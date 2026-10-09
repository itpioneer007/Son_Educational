"""
skill_ppt.py — GordenPPTSkill 精品模板生成引擎

将 AI 生成的教学课件大纲（title + slides + teachingGoals/keyPoints）
自动映射到 GordenPPTSkill 内置模板的固定页面/文字槽位上，生成 edits.json，
再调用 build_pptx.py 保版式输出最终 PPTX。

与 file_generator.generate_pptx_from_template 的区别：
- 旧引擎：删除模板所有页后手动重绘布局（不保留模板排版）
- 本引擎：只往模板固定槽位填写文字，100% 保留模板的版式/配色/字体
"""

import os
import re
import sys
import json
import subprocess

# ════════════════════════════════════════════════════════════════
# 路径配置
# ════════════════════════════════════════════════════════════════

# GordenPPTSkill 根目录（与本文件同级的 .trae/skills/GordenPPTSkill）
_SKILL_ROOT = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    ".trae", "skills", "GordenPPTSkill",
)
_TEMPLATES_DIR = os.path.join(_SKILL_ROOT, "templates")
_BUILD_SCRIPT = os.path.join(_SKILL_ROOT, "scripts", "build_pptx.py")

# ════════════════════════════════════════════════════════════════
# Skill 模板注册表
# ════════════════════════════════════════════════════════════════
# 只登记适配教学场景、且已确认版式结构的模板。
# 每套模板映射到具体的学科关键词，供自动匹配与前端展示。

SKILL_TEMPLATES = {
    # slug: {name, 适用学科关键词, 默认封面策略(标题字数上限等)}
    "cute-orange-class": {
        "name": "橙色可爱卡通（小学/幼儿）",
        "subjects": ["语文", "数学", "英语", "小学", "幼儿", "拼音", "道德", "科学", "美术", "音乐", "体育", "班会"],
        "short_title": 8,   # 封面主标题建议字数上限
        "desc": "暖橙卡通手绘风格，3只小宠物，活泼童趣，适合小学/幼儿园/亲子课堂。",
    },
}

# 供 file_generator / main 判断一个 template id 是否走 skill 引擎
SKILL_TEMPLATE_SLUGS = set(SKILL_TEMPLATES.keys())

# 输出目录（与 file_generator 共用 config.OUTPUT_DIR）
from config import OUTPUT_DIR


# ════════════════════════════════════════════════════════════════
# 工具函数
# ════════════════════════════════════════════════════════════════

def is_skill_template(template_id: str) -> bool:
    """判断 template_id 是否是 skill 引擎的模板 slug"""
    return template_id in SKILL_TEMPLATE_SLUGS


def get_template_list() -> list[dict]:
    """返回可用的 skill 模板列表（供前端展示/选择）"""
    result = []
    for slug, cfg in SKILL_TEMPLATES.items():
        if not os.path.exists(os.path.join(_TEMPLATES_DIR, slug, "template.pptx")):
            continue
        result.append({
            "id": slug,
            "name": cfg["name"],
            "description": cfg["desc"],
            "subjects": cfg["subjects"],
            "preview": f"/api/skill/templates/{slug}/preview",
            "engine": "skill",
        })
    return result


def _load_detail(slug: str) -> dict:
    """加载模板 detail.json"""
    detail_path = os.path.join(_TEMPLATES_DIR, slug, "detail.json")
    with open(detail_path, "r", encoding="utf-8") as f:
        return json.load(f)


def _template_path(slug: str) -> str:
    """模板 pptx 完整路径"""
    return os.path.join(_TEMPLATES_DIR, slug, "template.pptx")


def _clamp(text: str, max_chars: int | None) -> str:
    """按槽位容量截断到合理长度（剪到词尾，不硬截断加省略号）"""
    if not max_chars or max_chars <= 0:
        return text
    text = text.strip()
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rstrip("，。、；：,.;:")


# ════════════════════════════════════════════════════════════════
# 大纲 → edits.json 映射
# ════════════════════════════════════════════════════════════════

def _build_edits(detail: dict, content: dict, slug: str) -> dict:
    """把 AI 生成的课件内容映射到模板槽位，返回 edits.json 结构。

    核心策略：只选择与 AI 内容匹配的页面进行填充，避免留下带占位词的空白页。
    - 封面必有
    - 目录、章节扉页由 AI 的 section 数量决定
    - 内容页由 AI 的 content 块数量决定（按需挑选模板内容页）
    - 结束页必有
    """
    pages = detail.get("pages", [])
    # 按 slide_number 建索引，方便按角色取页
    by_num = {p["slide_number"]: p for p in pages}
    page_roles = detail.get("page_roles", {})

    # ── 从 AI 内容提取结构 ──
    title = (content.get("title") or "教学课件").strip()
    subtitle = content.get("subtitle") or ""
    subject = (content.get("subject") or "").strip()
    grade = (content.get("grade") or "").strip()

    ai_slides = content.get("slides", [])

    # 章节：用 AI 的 section 页
    sections = [s["title"] for s in ai_slides
                if s.get("type") == "section" and s.get("title")]

    # 内容块：收集所有 content/comparison 类页面
    content_blocks = [{
        "title": s["title"],
        "items": [x for x in (s.get("content") or [])
                  if x and not x.startswith("✦")],
    } for s in ai_slides
      if s.get("type") in ("content", "comparison") and s.get("title")]
    content_blocks = [b for b in content_blocks if b.get("title")]

    edits = []
    selected = []

    def slot_ids(page_num):
        """返回某页所有 editable 槽位 (slot_id, role, max_chars)"""
        pg = by_num.get(page_num)
        if not pg:
            return []
        return [(s["slot_id"], s.get("role", ""), s.get("max_chars"))
                for s in pg.get("text_slots", []) if s.get("editable", True)]

    # ── 封面 (cover) 必有 ──
    for pn in page_roles.get("cover", []):
        selected.append(pn)
        for sid, role, mc in slot_ids(pn):
            if "主标题" in role:
                edits.append({"slide": pn, "slot_id": sid,
                              "new_text": _clamp(title, mc)})
            elif "授课人" in role or "作者" in role:
                edits.append({"slide": pn, "slot_id": sid,
                              "new_text": "授课教师"})
            elif "副说明" in role or "副标题" in role:
                meta = f"{subject} · {grade}".strip(" ·")
                edits.append({"slide": pn, "slot_id": sid,
                              "new_text": _clamp(meta or subtitle or title, mc)})

    # 没有 section 时，章节目录退化为不生成（避免空白占位）
    divider_pages = page_roles.get("section_divider", [])
    agenda_pages = page_roles.get("agenda", [])
    content_pages = page_roles.get("content", [])

    if sections:
        # 章节扉页数量（用宿章节配额）
        n_sec = min(len(sections), len(divider_pages))
        # ── 目录 (agenda)：仅当章节数足以填满该目录页全部章节槽时才启用，
        #    否则保留即会留占位词，违背 skill 铁律 → 一律跳过目录页 ──
        for pn in agenda_pages:
            cap = sum(1 for _sid, role, _mc in slot_ids(pn)
                      if re.match(r"第 \d 章节标题", role))
            if len(sections) < cap:
                continue
            selected.append(pn)
            for sid, role, mc in slot_ids(pn):
                m = re.match(r"第 (\d) 章节标题", role)
                if m:
                    idx = int(m.group(1)) - 1
                    if idx < len(sections):
                        edits.append({"slide": pn, "slot_id": sid,
                                      "new_text": _clamp(sections[idx], mc)})
                elif "目" in role:
                    edits.append({"slide": pn, "slot_id": sid,
                                  "new_text": "目录"})

        # ── 章节扉页：每个 section 对应一张 ──
        for i, pn in enumerate(divider_pages[:n_sec]):
            selected.append(pn)
            for sid, role, mc in slot_ids(pn):
                if "标题" in role and "引言" not in role:
                    edits.append({"slide": pn, "slot_id": sid,
                                  "new_text": _clamp(sections[i], mc)})
                elif "引言" in role:
                    # 从该章节首块取首条为引言
                    intro = ""
                    if i < len(content_blocks):
                        items = content_blocks[i].get("items", [])
                        intro = items[0] if items else ""
                    edits.append({"slide": pn, "slot_id": sid,
                                  "new_text": _clamp(intro or sections[i], mc)})

    # ── 内容页：每个 content 块选一张模板内容页，按需挑选 ──
    for idx, block in enumerate(content_blocks):
        if idx >= len(content_pages):
            break
        pn = content_pages[idx]
        selected.append(pn)
        titles = []
        bodies = []
        for sid, role, mc in slot_ids(pn):
            if "标题" in role or "小标题" in role:
                titles.append((sid, mc))
            elif "正文" in role:
                bodies.append((sid, mc))

        item_pool = block.get("items", []) or []
        if titles:
            t0 = titles[0]
            edits.append({"slide": pn, "slot_id": t0[0],
                          "new_text": _clamp(block["title"], t0[1])})
            for extra_i, extra in enumerate(titles[1:], start=1):
                txt = item_pool[extra_i - 1] if len(item_pool) >= extra_i else ""
                edits.append({"slide": pn, "slot_id": extra[0],
                              "new_text": _clamp(txt, extra[1])})
        for bi, (sid, mc) in enumerate(bodies):
            txt = item_pool[len(titles) - 1 + bi] if len(item_pool) > (len(titles) - 1 + bi) else ""
            edits.append({"slide": pn, "slot_id": sid,
                          "new_text": _clamp(txt, mc)})

    # ── 结束页 (ending) 必有 ──
    for pn in page_roles.get("ending", []):
        selected.append(pn)
        for sid, role, mc in slot_ids(pn):
            if "主标" in role or "谢谢" in role:
                edits.append({"slide": pn, "slot_id": sid,
                              "new_text": "谢谢"})
            elif "副说明" in role:
                edits.append({"slide": pn, "slot_id": sid,
                              "new_text": _clamp("以上是本次课件内容，感谢观看", mc)})

    # 至少保留封面
    if not selected and page_roles.get("cover"):
        selected = list(page_roles["cover"])

    return {
        "template_slug": slug,
        "selected_slides": sorted(selected),
        "edits": [e for e in edits if e["new_text"]],
    }


# ════════════════════════════════════════════════════════════════
# 主入口：生成 skill 模板课件
# ════════════════════════════════════════════════════════════════

def generate_skill_pptx(content: dict, slug: str,
                        edits_input: dict | None = None) -> tuple:
    """
    基于 skill 模板生成课件 PPTX。

    Args:
        content: AI 生成的教学内容（含 title/slides/subject/grade 等）
        slug: skill 模板 slug（如 cute-orange-class）
        edits_input: 可选，调用方直接传入 edits.json（跳过自动映射）

    Returns:
        (filepath, filename)
    """
    slug = slug if slug in SKILL_TEMPLATES else "cute-orange-class"
    detail = _load_detail(slug)

    # 生成 edits.json
    if edits_input:
        edits_spec = edits_input
    else:
        edits_spec = _build_edits(detail, content, slug)

    if not edits_spec["edits"]:
        raise RuntimeError("未能从课件内容生成任何槽位填充")

    # 写 edits.json 到临时文件
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    safe_title = re.sub(r'[<>:"/\\|?*]', '_', content.get('title', '课件'))
    edits_path = os.path.join(OUTPUT_DIR, f"_skill_{safe_title}_edits.json")
    with open(edits_path, "w", encoding="utf-8") as f:
        json.dump(edits_spec, f, ensure_ascii=False, indent=2)

    # 输出 pptx
    filename = f"{safe_title}.pptx"
    output_path = os.path.join(OUTPUT_DIR, filename)

    # 调用 build_pptx.py 保版式生成
    detail_path = os.path.join(_TEMPLATES_DIR, slug, "detail.json")
    # 必须用当前解释器（sys.executable）。写死 "python" 在两种常见环境下会失败：
    # ① 机器上只有 py / python3 没有 python 别名；② 用 venv 但未激活，
    # 子进程落到系统 Python，缺失 python-pptx 依赖 → build_pptx.py 非零退出。
    cmd = [
        sys.executable, _BUILD_SCRIPT,
        _template_path(slug),
        edits_path,
        output_path,
        "--detail", detail_path,
    ]
    proc = subprocess.run(
        cmd, capture_output=True, text=True,
        encoding="utf-8", errors="replace",
    )
    if proc.returncode != 0:
        # 清理临时文件后抛出
        if os.path.exists(edits_path):
            os.remove(edits_path)
        raise RuntimeError(
            f"build_pptx.py 失败 (exit {proc.returncode}):\n{proc.stderr[-1500:]}"
        )

    # 清理临时 edits 文件
    if os.path.exists(edits_path):
        os.remove(edits_path)

    print(f"[SKILL-PPT] {slug} 生成: {output_path}")
    return output_path, filename


# ════════════════════════════════════════════════════════════════
# 测试入口
# ════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    test_content = {
        "title": "认识水果",
        "subject": "小学科学",
        "grade": "一年级",
        "subtitle": "一年级科学 · 第一单元",
        "slides": [
            {"type": "title", "title": "认识水果", "content": ["一年级科学"]},
            {"type": "section", "title": "一、常见水果",
             "content": [], "notes": ""},
            {"type": "content", "title": "苹果的营养",
             "content": ["富含维生素C", "帮助消化", "适合每天吃一个"]},
            {"type": "section", "title": "二、水果的颜色",
             "content": [], "notes": ""},
            {"type": "content", "title": "五颜六色的水果",
             "content": ["红色的苹果", "黄色的香蕉", "绿色的猕猴桃"]},
        ],
    }
    p, n = generate_skill_pptx(test_content, "cute-orange-class")
    print(f"生成成功: {p} / {n}")