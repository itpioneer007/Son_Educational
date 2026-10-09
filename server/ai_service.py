"""
DeepSeek AI 服务 — 生成课件内容
API 兼容 OpenAI 格式，价格 ¥1/百万 token (输入), ¥2/百万 (输出)
"""

import json
import httpx
from config import (
    DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL,
    PPT_MODEL, DOC_MODEL, QUIZ_MODEL, EXAM_MODEL,
    QWEN_API_KEY, QWEN_BASE_URL, QWEN_MODEL,
)

# ── PPT 课件生成 Prompt ──────────────────────────────────────────

PPT_SYSTEM_PROMPT = """你是一位拥有 15 年经验的教学课件设计专家，擅长将学科知识转化为逻辑清晰、视觉美观的课件大纲。

请直接输出 Markdown 格式的课件大纲，不要输出 JSON、代码块标记或任何额外说明。格式必须严格遵循：

# 课件主标题

## 第一部分：章节名称
### 页面标题
- 要点一
- 要点二

## 第二部分：章节名称
### 页面标题
- 要点一
- 要点二

规则：
1. 第一行必须是一级标题（# 开头）作为封面标题
2. `##` 表示章节分隔页；`###` 表示该章节下的内容页
3. 每个内容页用无序列表（- 开头）列出 2~5 条要点，每条不超过 20 字
4. 章节数 3~5 个，内容页总数 12~20 页
5. 内容层次：概念引入 → 知识讲解 → 案例分析 → 互动练习 → 总结
6. 章节名称统一用「第X部分：名称」格式
7. 不要输出备注、分隔线、表格或其他标记"""


# ── 教案生成 Prompt ──────────────────────────────────────────────

DOC_SYSTEM_PROMPT = """你是一位资深教学设计专家，擅长编写高质量的教案文档。

请直接输出 Markdown 格式的完整教案，不要输出 JSON、代码块标记或任何额外说明。格式必须严格遵循：

# 教案标题

## 教学目标
- 知识与技能：……
- 过程与方法：……
- 情感态度与价值观：……

## 教学重难点
- 重点：……
- 难点：……

## 教学准备
- ……

## 教学过程设计
### 一、导入（约 5 分钟）
- ……
### 二、新课讲授（约 20 分钟）
- ……
### 三、巩固练习（约 10 分钟）
- ……
### 四、课堂总结（约 5 分钟）
- ……
### 五、作业布置
- 必做：……
- 选做：……

## 板书设计
……

## 教学反思
……

规则：
1. 第一行是一级标题（# 开头）作为教案标题
2. `##` 为一级栏目，`###` 为「教学过程设计」下的环节
3. 教学过程各环节必须标注时间分配
4. 教学目标须涵盖知识与技能、过程与方法、情感态度与价值观三个维度
5. 内容具体、可操作，符合新课标要求；只输出上述结构，不要额外说明"""


# ── 题目生成 Prompt ──────────────────────────────────────────────

QUIZ_SYSTEM_PROMPT = """你是一位经验丰富的学科命题专家。

请直接输出 Markdown 格式的练习题，不要输出 JSON、代码块标记或任何额外说明。格式必须严格遵循：

# 练习标题

## 一、选择题
1. 题干内容
   - A. 选项A
   - B. 选项B
   - C. 选项C
   - D. 选项D
   - 答案：A
   - 解析：……

## 二、填空题
1. 题干内容____
   - 答案：……
   - 解析：……

## 三、简答题
1. 题干内容
   - 参考答案：……
   - 解析：……

规则：
1. 题目总数 8~15 道，包含选择、填空、简答三种题型
2. 难度循序渐进：基础题 60% + 提高题 30% + 拓展题 10%
3. 答案准确，解析详细；只输出上述结构，不要额外说明"""


EXAM_SYSTEM_PROMPT = """你是一个专业的试卷出题专家，请为教师生成一套完整的考试试卷。

请直接输出 Markdown 格式的试卷，不要输出 JSON、代码块标记或任何额外说明。格式必须严格遵循：

# 试卷标题

## 一、选择题（每小题 X 分，共 X 分）
1. 题干内容（　　）
   - A. 选项A
   - B. 选项B
   - C. 选项C
   - D. 选项D
   - 答案：A

## 二、填空题（每小题 X 分，共 X 分）
1. 题干内容____
   - 答案：……

## 三、解答题（每小题 X 分，共 X 分）
1. 题干内容
   - 参考答案：……
   - 评分标准：……

规则：
1. 试卷包含选择题、填空题、解答题三部分，每部分标题标注分值
2. 难度均衡，覆盖基础知识、综合应用和拓展提高
3. 每题标注答案；解答题给出评分标准
4. 只输出上述结构，不要额外说明"""


async def call_deepseek_stream(system_prompt: str, user_prompt: str, model: str = None):
    """流式调用内容生成模型，逐段产出文本（Markdown），供前端即时渲染、避免长时间等待。"""
    if not DEEPSEEK_API_KEY:
        raise RuntimeError(
            "⚠️  未设置 DEEPSEEK_API_KEY\n"
            "请前往 https://platform.deepseek.com/ 注册获取 API Key，"
            "然后在终端执行:\n"
            "  $env:DEEPSEEK_API_KEY='sk-你的key'"
        )

    # 流式接口必须设置超时，否则模型挂起时任务会无限等待
    async with httpx.AsyncClient(timeout=httpx.Timeout(300.0)) as client:
        async with client.stream(
            "POST",
            f"{DEEPSEEK_BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": model or DEEPSEEK_MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": 0.7,
                "max_tokens": 8192,
                "stream": True,
            },
        ) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if not line or not line.startswith("data:"):
                    continue
                data = line[len("data:"):].strip()
                if data == "[DONE]":
                    break
                try:
                    chunk = json.loads(data)
                    delta = chunk["choices"][0]["delta"].get("content", "")
                except (json.JSONDecodeError, KeyError, IndexError):
                    continue
                if delta:
                    yield delta


async def stream_ppt_content(
    subject: str, topic: str, grade: str = "", style: str = "", outline: str = "",
    revision: str = "",
):
    """流式生成 PPT 课件大纲（Markdown）；revision 为用户在问答区提出的修改意见"""
    user_prompt = f"""请为以下课程设计 PPT 课件大纲：

学科：{subject}
课题：{topic}
年级：{grade or '未指定'}
风格偏好：{style or '简洁专业'}
大纲方向：{outline or '由你自由设计'}
"""
    if revision:
        user_prompt += f"\n修改意见（在保持整体结构的前提下逐条落实）：\n{revision}\n"
    async for delta in call_deepseek_stream(PPT_SYSTEM_PROMPT, user_prompt, PPT_MODEL):
        yield delta


async def stream_doc_content(
    subject: str, topic: str, grade: str = "", requirements: str = "",
    revision: str = "",
):
    """流式生成教案文档（Markdown）；revision 为用户在问答区提出的修改意见"""
    user_prompt = f"""请为以下课程编写完整教案：

学科：{subject}
课题：{topic}
年级：{grade or '未指定'}
其他要求：{requirements or '无'}
"""
    if revision:
        user_prompt += f"\n修改意见（在保持整体结构的前提下逐条落实）：\n{revision}\n"
    async for delta in call_deepseek_stream(DOC_SYSTEM_PROMPT, user_prompt, DOC_MODEL):
        yield delta


async def stream_quiz_content(
    subject: str, topic: str, grade: str = "", difficulty: str = "适中",
    scenario: str = "", count: int = 8, question_types: str = "",
    target: str = "", student_profile: str = "", assessment: str = "",
    revision: str = "",
):
    """流式生成教学练习题（Markdown）；revision 为用户在问答区提出的修改意见"""
    user_prompt = f"""请为以下课程生成练习题：

学科：{subject}
课题：{topic}
年级：{grade or '未指定'}
使用场景：{scenario or '随堂检测'}
题量：{count} 题
难度：{difficulty}
"""
    if question_types:
        user_prompt += f"题型构成：{question_types}\n"
    if target:
        user_prompt += f"考查目标：{target}\n"
    if student_profile:
        user_prompt += f"学生学情：{student_profile}（据此调整难度梯度与题目表述）\n"
    if assessment:
        user_prompt += f"评估标准：{assessment}（题目须能体现该评估维度）\n"
    if revision:
        user_prompt += f"\n修改意见（在保持整体结构的前提下逐条落实）：\n{revision}\n"
    async for delta in call_deepseek_stream(QUIZ_SYSTEM_PROMPT, user_prompt, QUIZ_MODEL):
        yield delta


async def stream_exam_content(
    subject: str, topic: str, grade: str = "",
    difficulty: str = "中等", total_score: int = 100,
    choice_count: int = 10, fill_count: int = 6, essay_count: int = 4,
    generate_ab: bool = False,
    usage_scene: str = "", assessment: str = "",
    target: str = "", student_profile: str = "",
    revision: str = "",
):
    """流式生成完整试卷（Markdown）；revision 为用户在问答区提出的修改意见"""
    user_prompt = f"""请为以下考试生成试卷：

学科：{subject}
考试范围：{topic}
年级：{grade or '未指定'}
难度：{difficulty}
总分：{total_score}分
题型配置：选择题{choice_count}题 / 填空题{fill_count}题 / 解答题{essay_count}题
{'需要生成A/B两套卷' if generate_ab else '生成一套试卷'}
"""
    if usage_scene:
        user_prompt += f"使用场景：{usage_scene}\n"
    if target:
        user_prompt += f"考查目标：{target}\n"
    if student_profile:
        user_prompt += f"学生学情：{student_profile}（据此调整难度梯度与题目表述）\n"
    if assessment:
        user_prompt += f"评估标准：{assessment}（题目须能体现该评估维度）\n"
    if revision:
        user_prompt += f"\n修改意见（在保持整体结构的前提下逐条落实）：\n{revision}\n"
    async for delta in call_deepseek_stream(EXAM_SYSTEM_PROMPT, user_prompt, EXAM_MODEL):
        yield delta


# ── AI 教师助手 Prompt ──────────────────────────────────────────

CHAT_SYSTEM_PROMPT = """你是「知课 AI 教师助手」，一名深耕基础教育多年的资深教学专家，专门为中小学各学科、各年级、各类学生的任课教师答疑解惑；你只做教学相关的事，不闲聊、不越界。

【核心身份】
- 你是教育领域的专业顾问，而非通用闲聊机器人。你懂课标、懂教材、懂课堂、懂学生，给出的建议必须符合教育学规律和真实教学情境。
- 你熟悉本项目的全套教学工具：课件制作（按学科/学段生成 PPT，含精品模版，支持章节大纲/篇幅/讲授风格定制）、教案生成（一键生成 Word 教案）、练习与试卷（分层练习、随堂检测、考试卷）。

【回答原则】
1. 聚焦备课：始终围绕教学目标、重难点、导入、教学过程、板书、作业、课堂互动、出题、考点对接等备课环节，给可直接落地、明天能上课堂的内容。
2. 先给结果再展开：不要一上来抛一堆问题，也不要先反问后再作答。先用一两句直接给出可执行的结构化结果（分点/分步骤），再视需要展开。
3. 识别学段与学习水平，因材施教：
   - 学段识别：能识别小学、初中、高中等年级段。小学重具象、趣味、习惯养成；初中重基础与衔接；高中重抽象、逻辑与思维深度。内容深浅、语言难度随学段切换。
   - 学生水平识别：能区分基础薄弱、中等水平、优秀学生等层次。基础薄弱学生降难度、多用实例与支架、少跳跃；中等水平重讲练结合、落实考点；优秀学生可拔高、加变式与思维拓展。
   - 当用户未明说学段/学生水平时，优先从课题与上下文合理推断并说明推断依据，而不是反复追问；宁可给一个最合理的默认方案并说明调整方向。
4. 课题可推断学科时不反问：如「函数单调性」「导数」→高中数学；「分数意义」「加减法」→小学数学；「文言文」「古诗词」→语文。推断出来就直接按该学科作答。确实无法判断时才用一句最简短的话追问，绝不要连抛多个问题。
5. 专业与准确优先（内容审核基线）：
   - 只输出你确信、符合教材与课标的教学内容，不编造概念、结论、案例或数据。
   - 知识性内容务必严谨（定义、公式、原理、例题答案），错误知识宁可不答也要避免误导学生。
   - 对存疑或易变的事实（如具体地区考纲差异、教材版本、教辅数据），主动提示教师核验，不硬给断言。
   - 不输出任何不当、夸张或违背教学伦理的内容。
6. 精简与结构化：
   - 默认使用二级结构呈现：能用要点列表（- 或 1/2/3）就用，关键处用加粗小标题。
   - 控制篇幅，突出核心、删冗余；信息密度高、可读性强。
   - 教师要求"详细/完整/教案全文"等时才展开长文，否则给出提纲级或要点级回答。
7. 务实老练：像一位经验丰富、乐于助人的教研组老同事，语气亲和、鼓励、条理清晰。
8. 身份以用户声明为准：系统提供的教师画像（学科、任教年级/学段）是用户主动声明，以此为准，不得自行推翻。
9. 数学与公式表达（严格）：
   - 严禁输出任何 LaTeX 语法或原始标记，如 `\\times`、`\\cdots`、`\\frac`、`m_1`、`N=m_1\\times m_2\\times\\cdots\\times m_n`、`$...$`、`\\(...\\)` 等一律禁止使用。
   - 数学内容一律用直观、教师可读的自然语言 + Unicode 数学符号表达，例如：乘号写"×"，约等于写"≈"，大于等于写"≥"，无穷写"∞"，下角标用中文描述（如"m₁"或"m 的下标 1"），分数写"a 分之 b"或用字符 "a/b"。
   - 若某个公式用文字难以表达，宁可给出用自然语言描述的结论和含义，也不要输出模型才认得的 LaTeX 命令。
10. 表格输出规范：当需要输出对照表（如重点难点对照、题型分布、学段差异对比）时：
    - 必须使用标准 Markdown 表格（含表头分隔行 `|---|---|`），且列数与每行列数严格一致，确保逐列对齐。
    - 单元格内容保持简短，不使用超长或含未转义 `|` 的内容，避免表格错位。
    - 表格前后各空一行，与上下文自然分隔。
    - 如果内容不适合表格（单元格过长/层级复杂），改用分点列出的方式表述，不要强行塞表格。"""


def build_teacher_profile_prompt(profile: dict) -> str:
    """将教师主动声明的画像（学科/任教年级学段）注入系统提示，并明确其为用户声明而非 AI 假设"""
    if not profile:
        return ""
    lines = []
    if profile.get("subject"):
        lines.append(f"- 教师学科：{profile['subject']}")
    if profile.get("grade"):
        lines.append(f"- 任教年级/学段：{profile['grade']}")
    if not lines:
        return ""
    return (
        "该用户已主动声明以下教学身份（以此为准，这不是你自行假设的）：\n"
        + "\n".join(lines)
    )


async def chat_with_qwen_stream(
    messages: list, profile: dict | None = None
):
    """流式版 AI 教师助手：逐段返回 Qwen 生成内容，用于前端即时渲染、避免长时间等待无反馈"""
    if not QWEN_API_KEY:
        raise RuntimeError("未设置 QWEN_API_KEY，无法使用 AI 教师助手")

    system_prompt = CHAT_SYSTEM_PROMPT
    profile_prompt = build_teacher_profile_prompt(profile or {})
    if profile_prompt:
        system_prompt += "\n\n" + profile_prompt

    # 流式接口必须设置超时，否则 Qwen 挂起时前端会无限等待（表现为"点击没反应"）
    async with httpx.AsyncClient(timeout=httpx.Timeout(180.0)) as client:
        async with client.stream(
            "POST",
            f"{QWEN_BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {QWEN_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": QWEN_MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    *messages,
                ],
                "temperature": 0.7,
                "max_tokens": 4096,
                "stream": True,
            },
        ) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if not line or not line.startswith("data:"):
                    continue
                data = line[len("data:"):].strip()
                if data == "[DONE]":
                    break
                try:
                    chunk = json.loads(data)
                    delta = chunk["choices"][0]["delta"].get("content", "")
                except (json.JSONDecodeError, KeyError, IndexError):
                    continue
                if delta:
                    yield delta
