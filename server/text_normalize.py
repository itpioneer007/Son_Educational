"""正文文本规整：把大模型偶发输出的 LaTeX 数学式降级为 Unicode 纯文本，
并把题目选项的行首缩进补齐到 Markdown 嵌套列表要求的列位。

为什么需要
----------
本项目没有数学公式引擎（前端 marked、导出侧自研 HTML/DOCX 渲染都是纯文本
渲染器），LaTeX 一旦进入正文会出现两种坏结果：

- 前端 marked 会把 ``\\(`` 的反斜杠当作转义吃掉：``\frac{1}{x}`` 显示成
  ``frac{1}{x}``（内容被破坏），``\\(x^2\\)`` 显示成 ``(x^2)``；
- 导出 HTML / DOCX 里 LaTeX 原样保留，``\\[ ... \\]`` 这种块级公式还会被
  当成三行普通段落输出。

面向中小学教师的场景，用 Unicode 符号（x²、√、±、≤、≠、Δ）表达完全够用，
因此在**正文落盘前**统一降级一次，保证「右侧预览 = 导出结果」且正文不含反斜杠。

缩进规整则是另一类兜底：Markdown 有序列表的嵌套要求子项缩进 ≥ 题干内容列
（``1. `` → 3 空格），大模型常只给 0~1 空格，导致前端 marked 把每个选项拆成
独立顶层列表（右侧预览散成一片）。提示词里已要求 3 空格，但模型并不稳定遵守，
故在落盘前按题干宽度统一补齐。
"""

import re

__all__ = ["normalize_math", "normalize_md_indent"]

# 上标 / 下标可映射字符
_SUP_KEYS = set("0123456789+-=()n")
_SUB_KEYS = set("0123456789+-=n")
_SUP = str.maketrans("0123456789+-=()n", "⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁼⁽⁾ⁿ")
_SUB = str.maketrans("0123456789+-=n", "₀₁₂₃₄₅₆₇₈₉₊₋₌ₙ")

# 命令 → Unicode 符号
_SYMBOLS = {
    r"\pm": "±", r"\mp": "∓",
    r"\times": "×", r"\div": "÷", r"\cdot": "·", r"\ast": "∗",
    r"\leq": "≤", r"\le": "≤", r"\geq": "≥", r"\ge": "≥",
    r"\neq": "≠", r"\ne": "≠", r"\approx": "≈", r"\equiv": "≡",
    r"\sim": "∽", r"\cong": "≌", r"\propto": "∝",
    r"\infty": "∞", r"\angle": "∠", r"\perp": "⊥", r"\parallel": "∥",
    r"\in": "∈", r"\notin": "∉", r"\ni": "∋",
    r"\subset": "⊂", r"\subseteq": "⊆", r"\supset": "⊃", r"\supseteq": "⊇",
    r"\cup": "∪", r"\cap": "∩", r"\emptyset": "∅", r"\varnothing": "∅",
    r"\alpha": "α", r"\beta": "β", r"\gamma": "γ", r"\delta": "δ",
    r"\epsilon": "ε", r"\varepsilon": "ε", r"\zeta": "ζ", r"\eta": "η",
    r"\theta": "θ", r"\iota": "ι", r"\kappa": "κ", r"\lambda": "λ",
    r"\mu": "μ", r"\nu": "ν", r"\xi": "ξ", r"\pi": "π", r"\rho": "ρ", r"\sigma": "σ",
    r"\tau": "τ", r"\upsilon": "υ", r"\phi": "φ", r"\varphi": "φ",
    r"\chi": "χ", r"\psi": "ψ", r"\omega": "ω",
    r"\Gamma": "Γ", r"\Delta": "Δ", r"\Theta": "Θ", r"\Lambda": "Λ",
    r"\Xi": "Ξ", r"\Pi": "Π", r"\Sigma": "Σ", r"\Phi": "Φ",
    r"\Psi": "Ψ", r"\Omega": "Ω",
    r"\rightarrow": "→", r"\to": "→", r"\Rightarrow": "⇒",
    r"\leftarrow": "←", r"\Leftarrow": "⇐",
    r"\leftrightarrow": "↔", r"\Leftrightarrow": "⇔",
    r"\because": "∵", r"\therefore": "∴",
    r"\circ": "°", r"\degree": "°",
    r"\dots": "…", r"\ldots": "…", r"\cdots": "…", r"\vdots": "⋮", r"\ddots": "⋱",
    r"\quad": " ", r"\qquad": " ", r"\;": " ", r"\,": " ", r"\:": " ", r"\!": "",
}


def _apply_symbols(text: str) -> str:
    """替换 LaTeX 符号命令；字母命令需带词边界，避免 `\\le` 吃掉 `\\leq`。"""
    for key, val in _SYMBOLS.items():
        if not key[-1].isalpha():
            text = text.replace(key, val)
    for key in sorted((k for k in _SYMBOLS if k[-1].isalpha()), key=len, reverse=True):
        # LaTeX 里命令后的空格只是命令结束符，转成 Unicode 后属多余，一并吞掉
        # （只吃水平空白，避免把换行合并）。`m\leq 2` → `m≤2`、`\pi r^2` → `πr²`
        text = re.sub(
            re.escape(key) + r"(?![a-zA-Z])[ \t]*",
            lambda _m, v=_SYMBOLS[key]: v,
            text,
        )
    return text


# 数学函数名：LaTeX 里是命令（`\cos`），纯文本里是一段普通字母，但前面的变量与它
# 之间是隐含相乘 —— 直接删反斜杠会把 `F\cos\theta` 粘成难以阅读的 `Fcosθ`。
# 这里显式识别函数名，前面是字母/数字/右括号时补一个空格还原相乘关系。
_FUNCS = (
    "arcsin arccos arctan sinh cosh tanh "
    "sin cos tan cot sec csc "
    "log ln lg lim max min exp det gcd sup inf deg"
).split()
_FUNC_RE = re.compile(r"\\(" + "|".join(_FUNCS) + r")(?![a-zA-Z])")
_PRECEDING_ATOM = re.compile(r"[0-9A-Za-z)\]⁰¹²³⁴⁵⁶⁷⁸⁹₀₁₂₃₄₅₆₇₈₉]")
# 修饰命令（矢量/上划线/帽子…）：只保留被修饰的内容，避免命令名残留进正文
_ACCENT_RE = re.compile(
    r"\\(?:vec|bar|hat|tilde|dot|ddot|overline|underline|widehat|widetilde)"
    r"\s*\{([^{}]*)\}"
)


def _func_sub(m: "re.Match") -> str:
    name = m.group(1)
    prev = m.string[m.start() - 1] if m.start() > 0 else ""
    if prev and _PRECEDING_ATOM.match(prev):
        return " " + name
    return name


# 分数命令：分子/分母允许再套一层花括号，覆盖 \frac{\sqrt{2}}{2} 这类写法
_NEST = r"(?:[^{}]|\{[^{}]*\})*"
_FRAC_RE = re.compile(
    r"\\(?:dfrac|tfrac|frac)\s*\{(" + _NEST + r")\}\s*\{(" + _NEST + r")\}"
)


def _frac(m: "re.Match") -> str:
    """`\\frac{a}{b}` → `a/b`；分子分母含运算时补括号以免歧义。"""
    num, den = m.group(1).strip(), m.group(2).strip()
    if re.search(r"[+\-*/=]", num):
        num = f"({num})"
    if re.search(r"[+\-*/=]", den):
        den = f"({den})"
    return f"{num}/{den}"


def _sup(m: "re.Match") -> str:
    body = m.group(1) if m.group(1) is not None else m.group(2)
    if body and all(c in _SUP_KEYS for c in body):
        return body.translate(_SUP)
    return f"^({body})"


def _sub(m: "re.Match") -> str:
    body = m.group(1) if m.group(1) is not None else m.group(2)
    if body and all(c in _SUB_KEYS for c in body):
        return body.translate(_SUB)
    return f"_({body})"


def normalize_math(text: str) -> str:
    """把 LaTeX 数学式降级为 Unicode 纯文本；无 LaTeX 时原样返回。"""
    if not text:
        return text or ""
    s = text

    # ① 公式定界符：块级转段落间隔，行内直接去掉
    s = re.sub(r"\\\[|\\\]", "\n", s)
    s = re.sub(r"\\\(|\\\)", "", s)
    s = s.replace("$$", "").replace("$", "")

    # ② 尺寸/定界命令与结构命令
    # 分数允许分子/分母再套一层花括号（如 \frac{\sqrt{2}}{2}）
    s = re.sub(r"\\(?:left|right|bigl|bigr|Bigl|Bigr|bigg|Bigg)(?![a-zA-Z])", "", s)
    s = _FRAC_RE.sub(_frac, s)
    s = re.sub(
        r"\\sqrt\s*\[([^\]]*)\]\s*\{([^{}]*)\}",
        lambda m: f"{m.group(1)}√({m.group(2)})",
        s,
    )
    s = re.sub(r"\\sqrt\s*\{([^{}]*)\}", lambda m: f"√({m.group(1)})", s)
    s = re.sub(
        r"\\(?:text|textrm|mathrm|mathbf|mathit|mathsf|operatorname)\s*\{([^{}]*)\}",
        r"\1",
        s,
    )
    # 度数 `30^\circ`：`^\circ` 不是上标，直接整体换成度符号，避免留下孤立的 `^`
    s = re.sub(r"\^\s*\\circ(?![a-zA-Z])", "°", s)
    # 矢量/上划线/帽子等修饰命令：只保留被修饰内容，别让命令名残留进正文
    s = _ACCENT_RE.sub(r"\1", s)

    # ③ 上下标
    # 下标要求前面不是下划线/反斜杠：填空题的连续下划线（____）不能当作下标
    s = re.sub(r"\^\{([^{}]*)\}|\^(\w)", _sup, s)
    s = re.sub(r"_\{([^{}]*)\}|(?<![_\\])_([A-Za-z0-9])", _sub, s)

    # ④ 符号命令 + 数学函数名（函数名前面的变量补空格还原隐含相乘）
    s = _apply_symbols(s)
    s = _FUNC_RE.sub(_func_sub, s)

    # ⑤ 兜底：不留任何反斜杠（纯文本正文里它已无意义，且会被前端 marked 吃掉）
    s = s.replace("\\", "")

    # ⑥ 收尾：合并多余空格与空行
    # 只合并「行内」连续空白（前面有非空白字符），绝不能碰行首缩进 —— 题目选项
    # 依赖 ``1. `` 后 3 空格缩进才能被 marked 认作嵌套列表，一旦压平就会被拆成
    # 独立顶层列表，右侧预览散成一片。
    s = re.sub(r"(?<=\S)[ \t]{2,}", " ", s)
    s = re.sub(r"[ \t]+\n", "\n", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s


# 顶层题干：``1. `` / ``1、`` / ``1)``（行首无缩进）
_Q_LINE_RE = re.compile(r"^(\d{1,3})[.、)]\s+\S")
# 题干下的列表子项（选项 / ``- 答案`` / ``- 解析``）
_SUB_ITEM_RE = re.compile(r"^[-*+]\s+\S")
_HEADING_RE = re.compile(r"^#{1,6}\s")


def normalize_md_indent(md: str) -> str:
    """把题干下的选项/答案等列表子项统一缩进到所属题干的正文列。

    仅调整「行首缩进」，不改动正文内容；遇到空行或新标题即结束当前题干上下文，
    因此不会误伤正文里本就存在的顶层无序列表。无题干上下文时原样返回。
    """
    if not md:
        return md or ""
    out = []
    child_col = 0
    for raw in md.split("\n"):
        line = raw.rstrip()
        stripped = line.lstrip()
        if not stripped:
            child_col = 0
            out.append("")
            continue
        if _HEADING_RE.match(stripped):
            child_col = 0
            out.append(stripped)
            continue
        # 顶层题干（本身未缩进）→ 记住它要求的子项缩进列
        m_q = _Q_LINE_RE.match(stripped)
        if m_q and line == stripped:
            child_col = len(m_q.group(1)) + 2  # ``1.`` + 1 空格 → 内容列 3
            out.append(stripped)
            continue
        # 题干下的列表子项 → 提到题干正文列，供 marked 正确嵌套
        if child_col and _SUB_ITEM_RE.match(stripped):
            out.append(" " * child_col + stripped)
            continue
        out.append(line)
    return "\n".join(out)
