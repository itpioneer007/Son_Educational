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

PPT_SYSTEM_PROMPT = """你是一位拥有 15 年经验的教学课件设计专家，擅长将学科知识转化为逻辑清晰、视觉美观的课件内容。

请严格按照以下 JSON 格式返回课件内容，不要包含任何额外文字或 markdown 标记：

```json
{
  "title": "课件主标题",
  "subtitle": "副标题（可选）",
  "style": "整体风格描述",
  "slides": [
    {
      "type": "title",
      "title": "封面标题",
      "content": ["学科·年级信息", "学校/教师信息"],
      "notes": "讲师备注"
    },
    {
      "type": "section",
      "title": "第一部分：章节标题",
      "content": [],
      "notes": ""
    },
    {
      "type": "content",
      "title": "知识点标题",
      "content": ["要点 1（每条不超过20字）", "要点 2", "要点 3"],
      "notes": "讲师备注"
    },
    {
      "type": "comparison",
      "title": "对比分析标题",
      "content": ["左边要点1", "左边要点2", "右边要点1", "右边要点2"],
      "notes": ""
    },
    {
      "type": "summary",
      "title": "本节课总结",
      "content": ["核心结论 1", "核心结论 2", "核心结论 3"],
      "notes": ""
    }
  ]
}
```

设计原则：
1. 每页 content 最多 5 个要点，每个要点不超过 20 字
2. 封面用 type:title，每部分开头用 type:section 做章节分隔页
3. 总幻灯片数量：12-20 页（含封面、章节分隔页、总结）
4. 内容层次：概念引入 → 知识讲解 → 案例分析 → 互动练习 → 总结
5. type 可选值：title, section, content, comparison, summary
6. 合理设计互动环节（提问、讨论、小练习）
7. 比较页（comparison）内容数量应为偶数，前一半放左边，后一半放右边
8. 总结页用 type:summary，要点前加 ✦ 符号自动渲染"""


# ── 教案生成 Prompt ──────────────────────────────────────────────

DOC_SYSTEM_PROMPT = """你是一位资深教学设计专家，擅长编写高质量的教案文档。

请严格按照以下 JSON 格式返回教案内容，不要包含任何额外文字：

```json
{
  "title": "教案标题",
  "subject": "学科",
  "grade": "年级",
  "duration": "课时时长",
  "teachingGoals": "教学目标1；教学目标2；教学目标3",
  "keyPoints": "重点1；重点2；难点1",
  "sections": [
    {
      "heading": "一、教学导入",
      "content": ["导入方式（3-5分钟）", "引发思考的问题"]
    },
    {
      "heading": "二、新课讲授",
      "content": ["知识点1讲解", "知识点2讲解", "演示/互动环节"]
    },
    {
      "heading": "三、巩固练习",
      "content": ["课堂练习1", "课堂练习2", "小组讨论"]
    },
    {
      "heading": "四、课堂总结",
      "content": ["核心知识回顾", "方法归纳"]
    },
    {
      "heading": "五、作业布置",
      "content": ["必做题", "选做题/拓展题"]
    }
  ]
}
```

设计原则：
1. sections 数量 5-8 个
2. teachingGoals 用半角分号分隔多条目标，keyPoints 用分号分隔重点和难点
3. 教学目标要符合新课标要求，涵盖知识与技能、过程与方法、情感态度价值观
4. 教学过程要详细、可操作，标注时间分配
5. 包含作业布置和板书设计要点"""


# ── 题目生成 Prompt ──────────────────────────────────────────────

QUIZ_SYSTEM_PROMPT = """你是一位经验丰富的学科命题专家。

请严格按照以下 JSON 格式返回题目内容：

```json
{
  "title": "练习标题",
  "questions": [
    {
      "type": "choice",
      "question": "题目内容",
      "options": ["A. 选项A", "B. 选项B", "C. 选项C", "D. 选项D"],
      "answer": "A",
      "analysis": "解析内容"
    },
    {
      "type": "fill",
      "question": "填空题内容____",
      "answer": "参考答案",
      "analysis": "解析内容"
    },
    {
      "type": "essay",
      "question": "简答题内容",
      "answer": "参考答案要点",
      "analysis": "评分标准"
    }
  ]
}
```

设计原则：
1. 题目总数 8-15 道，包含选择、填空、简答三种题型
2. 难度循序渐进：基础题 60% + 提高题 30% + 拓展题 10%
3. 答案准确，解析详细"""


async def call_deepseek(system_prompt: str, user_prompt: str, model: str = None) -> dict:
    """调用内容生成模型生成内容；model 用于按角色指定不同 LLM"""
    if not DEEPSEEK_API_KEY:
        raise RuntimeError(
            "⚠️  未设置 DEEPSEEK_API_KEY\n"
            "请前往 https://platform.deepseek.com/ 注册获取 API Key，"
            "然后在终端执行:\n"
            "  $env:DEEPSEEK_API_KEY='sk-你的key'"
        )

    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(
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
            },
        )
        resp.raise_for_status()
        data = resp.json()
        content = data["choices"][0]["message"]["content"]

    # 提取 JSON（AI 有时会包裹 markdown 代码块）
    content = content.strip()
    if content.startswith("```"):
        content = content.split("\n", 1)[-1]
        content = content.rsplit("```", 1)[0]
    return json.loads(content.strip())


async def generate_ppt_content(
    subject: str, topic: str, grade: str = "", style: str = "", outline: str = "",
    revision: str = "",
) -> dict:
    """生成 PPT 课件内容；revision 为用户在问答区提出的修改意见"""
    user_prompt = f"""请为以下课程设计 PPT 课件内容：

学科：{subject}
课题：{topic}
年级：{grade or '未指定'}
风格偏好：{style or '简洁专业'}
大纲方向：{outline or '由你自由设计'}
"""
    if revision:
        user_prompt += f"\n修改意见（在保持整体结构的前提下逐条落实）：\n{revision}\n"
    return await call_deepseek(PPT_SYSTEM_PROMPT, user_prompt, PPT_MODEL)


async def generate_doc_content(
    subject: str, topic: str, grade: str = "", requirements: str = "",
    revision: str = "",
) -> dict:
    """生成教案文档内容；revision 为用户在问答区提出的修改意见"""
    user_prompt = f"""请为以下课程编写完整教案：

学科：{subject}
课题：{topic}
年级：{grade or '未指定'}
其他要求：{requirements or '无'}
"""
    if revision:
        user_prompt += f"\n修改意见（在保持整体结构的前提下逐条落实）：\n{revision}\n"
    return await call_deepseek(DOC_SYSTEM_PROMPT, user_prompt, DOC_MODEL)


async def generate_quiz_content(
    subject: str, topic: str, grade: str = "", difficulty: str = "适中",
    scenario: str = "", count: int = 8, question_types: str = "",
    target: str = "", student_profile: str = "", assessment: str = "",
    revision: str = "",
) -> dict:
    """生成教学练习题；revision 为用户在问答区提出的修改意见"""
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
    return await call_deepseek(QUIZ_SYSTEM_PROMPT, user_prompt, QUIZ_MODEL)


async def generate_exam_content(
    subject: str, topic: str, grade: str = "",
    difficulty: str = "中等", total_score: int = 100,
    choice_count: int = 10, fill_count: int = 6, essay_count: int = 4,
    generate_ab: bool = False,
    usage_scene: str = "", assessment: str = "",
    target: str = "", student_profile: str = "",
    revision: str = "",
) -> dict:
    """生成完整试卷；revision 为用户在问答区提出的修改意见"""
    system_prompt = """你是一个专业的试卷出题专家。请为教师生成一套完整的考试试卷。

要求：
1. 试卷包含三部分：选择题、填空题、解答题
2. 题目难度均衡，覆盖基础知识、综合应用和拓展提高
3. 每道题标注分值
4. 提供参考答案和评分标准
5. 使用JSON格式返回，结构如下：
{
  "title": "试卷标题",
  "subject": "学科",
  "grade": "年级",
  "total_score": 100,
  "duration": "90分钟",
  "sections": [
    {
      "type": "选择题",
      "count": 10,
      "score_per": 3,
      "subtotal": 30,
      "questions": [
        {"id": 1, "content": "题目内容", "options": ["A. 选项A", "B. 选项B", "C. 选项C", "D. 选项D"], "answer": "A", "difficulty": "基础"}
      ]
    },
    {
      "type": "填空题",
      "count": 6,
      "score_per": 4,
      "subtotal": 24,
      "questions": [
        {"id": 1, "content": "题目内容____", "answer": "参考答案", "difficulty": "中等"}
      ]
    },
    {
      "type": "解答题",
      "count": 4,
      "score_per": 10,
      "subtotal": 40,
      "questions": [
        {"id": 1, "content": "题目内容", "answer": "参考答案要点", "difficulty": "提高", "scoring_criteria": "评分标准"}
      ]
    }
  ],
  "answer_key": "简要答案汇总"
}"""
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
    return await call_deepseek(system_prompt, user_prompt, EXAM_MODEL)


# ── AI 备课助手 Prompt ──────────────────────────────────────────

CHAT_SYSTEM_PROMPT = """你是「知课 AI 备课助手」，一名深耕基础教育多年的资深教学专家，服务对象是中小学各学科、各年级、各类学生的任课教师。

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
6. 精简与结构化（针对通用问答等自由提问）：
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

# 大功能定向指令（构思层）：每个功能为系统提示注入一段定向任务，配合前端子需求表单使用
FEATURE_PROMPTS = {
    "plan": """【当前任务：备课构思】请严格按用户给出的「课题、课型、教材版本、学生层次」构思教学方案。
课型决定整体结构：
- 新授课：概念引入→探究归纳→例题示范→练习巩固→小结
- 复习课：知识框架梳理→典型例题→易错点归纳→真题演练
- 习题讲评课：错因分析→方法归纳→变式训练→迁移应用
- 专题课：一题多解→多题一解→思想方法提炼→深度拓展
学生层次决定深度与节奏：重点班可拔高例题、加入拓展思考；普通班重基础落实、讲练并重；基础薄弱需降难度、多具象、衔接前置知识。
若用户勾选高考考点标注，则对每个知识点标注高考考频（高频/中频/低频）、常考题型与分值。
输出须包含：教学目标、教学重难点、课堂导入、教学环节流程（标注时间）、板书设计建议。结构清晰、可操作，便于教师审阅后据此生成课件。""",
    "lesson": """【当前任务：教案草稿】请严格按用户给出的「课题、课型、教材版本、学生层次、课时、教案详略」输出完整教案草稿。
教案详略决定详略程度：详案需精确到分钟、含过渡语与逐环节设计，适合公开课/检查；简案给出环节提纲与要点即可，适合日常使用。
结构须包含：教学目标（知识与技能、过程与方法、情感态度与价值观）、教学重难点、课时安排、教学准备、教学过程（导入→新授→巩固→总结，并标注时间）、板书设计、作业布置、教学反思要点。
若缺少学科、学段、教材版本等关键信息，优先从课题名称推断（如「函数的单调性」→高中数学），推断不出再简短追问；不确定的考点提示教师核验。""",
    "quiz": """【当前任务：出题草稿】请严格按用户给出的「课题、用途、题型分布、学生层次、难度、题量」设计分层练习草稿。
- 用途决定题型与配比：课堂练习题量适中重基础；课后作业分层梯度完整；周测/月考按考试标准配比并控制难度分布
- 题型分布按用户选择执行（高考标准≈选择+填空+解答题配比，或全选择/全解答）
- 学生层次决定分层比例：重点班提升/拓展题占多数；普通班基础/提升为主；基础薄弱以基础题为主、降低难度
按基础题/提升题/拓展题分层，每题附参考答案与考察点；若用户勾选高考考点标注，则每题标注对应高考考点与真题考法。""",
}


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


async def chat_with_qwen(
    messages: list, feature: str = "", profile: dict | None = None
) -> str:
    """AI 备课助手：调用 Qwen（百炼 OpenAI 兼容接口），支持大功能定向（ppt/lesson/quiz）与教师画像"""
    if not QWEN_API_KEY:
        raise RuntimeError("未设置 QWEN_API_KEY，无法使用 AI 备课助手")

    system_prompt = CHAT_SYSTEM_PROMPT
    profile_prompt = build_teacher_profile_prompt(profile or {})
    if profile_prompt:
        system_prompt += "\n\n" + profile_prompt
    feature_prompt = FEATURE_PROMPTS.get(feature or "", "")
    if feature_prompt:
        system_prompt += "\n\n" + feature_prompt

    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(
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
            },
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"].strip()


async def chat_with_qwen_stream(
    messages: list, feature: str = "", profile: dict | None = None
):
    """流式版 AI 备课助手：逐段返回 Qwen 生成内容，用于前端即时渲染、避免长时间等待无反馈"""
    if not QWEN_API_KEY:
        raise RuntimeError("未设置 QWEN_API_KEY，无法使用 AI 备课助手")

    system_prompt = CHAT_SYSTEM_PROMPT
    profile_prompt = build_teacher_profile_prompt(profile or {})
    if profile_prompt:
        system_prompt += "\n\n" + profile_prompt
    feature_prompt = FEATURE_PROMPTS.get(feature or "", "")
    if feature_prompt:
        system_prompt += "\n\n" + feature_prompt

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
