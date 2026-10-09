"""
FastAPI 课件生成服务
====================
启动: uvicorn main:app --reload --port 8000
"""

import sys
import io

# 修复 Windows 中文编码问题
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

import json
import os
import uuid
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from config import OUTPUT_DIR, DATA_DIR, TASKS_FILE, HOST, PORT
from ai_service import (
    stream_ppt_content, stream_doc_content, stream_quiz_content, stream_exam_content,
    chat_with_qwen, chat_with_qwen_stream,
)
from file_generator import (
    generate_pptx, generate_pptx_from_template,
    generate_docx_from_markdown, generate_quiz_html_from_markdown,
    generate_exam_html_from_markdown, parse_ppt_outline,
    get_template_list, pick_template,
)
from skill_ppt import (
    is_skill_template, generate_skill_pptx,
    get_template_list as get_skill_template_list,
)
from spark_ppt import generate_pptx_via_spark, get_templates as get_spark_templates

app = FastAPI(title="EduAI 课件生成 API", version="1.0.0")

# CORS — 允许前端 dev server 跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── 任务存储 ─────────────────────────────────────────────────
# 任务持久化到本地 JSON 文件，服务重启后记录不丢失，供管理后台统计
_tasks: dict[str, dict] = {}
_tasks_lock = asyncio.Lock()

# 内容流式缓冲区：task_id → 已生成的 Markdown 文本。
# 只存在内存里（不落盘、不放进 _tasks），SSE 按游标增量推送给前端即时渲染。
_stream_text: dict[str, str] = {}


def _load_tasks():
    """启动时从磁盘加载历史任务记录"""
    global _tasks
    if not os.path.exists(TASKS_FILE):
        return
    try:
        with open(TASKS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            _tasks = data
    except (json.JSONDecodeError, OSError):
        # 损坏文件不阻塞启动，保留空内存态
        pass


def _save_tasks():
    """将任务记录落盘"""
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(TASKS_FILE, "w", encoding="utf-8") as f:
            json.dump(_tasks, f, ensure_ascii=False, indent=2)
    except OSError:
        pass


def _new_task(task_type: str, subject: str = "", topic: str = "", grade: str = "") -> str:
    task_id = uuid.uuid4().hex[:12]
    _tasks[task_id] = {
        "id": task_id,
        "type": task_type,      # ppt | doc | quiz | exam
        "subject": subject,     # 学科
        "topic": topic,         # 课题
        "grade": grade,         # 年级
        "status": "queued",     # queued → processing → ready（内容就绪，待导出）→ exporting → completed / failed
        "progress": 0,
        "stage": "等待处理",
        "content_md": None,     # AI 流式生成的 Markdown 正文（用户在右侧确认后据此导出）
        "filename": None,
        "filepath": None,
        "error": None,
        "params": None,      # 生成参数（供问答区提出修改意见后重跑使用）
        "revisions": [],     # 用户历次修改意见
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    _save_tasks()
    return task_id


def _update_task(task_id: str, **kwargs):
    if task_id in _tasks:
        _tasks[task_id].update(kwargs)
        _save_tasks()


# ── API: 提交生成任务 ─────────────────────────────────────────

@app.post("/api/courseware/create")
async def create_courseware(
    type: str = Form(...),          # ppt | doc | quiz | exam
    subject: str = Form(...),
    topic: str = Form(...),
    grade: str = Form(""),
    style: str = Form(""),
    outline: str = Form(""),
    requirements: str = Form(""),
    difficulty: str = Form("适中"),
    totalScore: str = Form("100"),
    choiceCount: str = Form("10"),
    fillCount: str = Form("6"),
    essayCount: str = Form("4"),
    generateAB: str = Form("false"),
    # 教学要素（分步向导采集的关键决策信息）
    duration: str = Form(""),
    studentProfile: str = Form(""),
    interactionDesign: str = Form(""),
    lessonFocus: str = Form(""),
    usageScene: str = Form(""),
    assessment: str = Form(""),
    target: str = Form(""),
    questionTypes: str = Form(""),
    scenario: str = Form(""),
    count: str = Form(""),
    template: str = Form(""),       # PPT 模版 ID，为空时自动根据学科匹配
    engine: str = Form("spark"),    # PPT 生成引擎：spark(讯飞智文) | local(本地模板)
    sparkTemplateId: str = Form(""),  # 讯飞模板 ID，为空用后端配置默认模板
    isCardNote: str = Form("true"),   # 讯飞：是否生成演讲备注
    isFigure: str = Form("true"),     # 讯飞：是否自动配图
    files: list[UploadFile] = File(default=[]),
):
    """
    提交课件生成任务
    - type: ppt | doc | quiz | exam
    - 文件可选，当前版本暂不处理文件内容（可后续扩展）
    """
    task_id = _new_task(type, subject, topic, grade)
    params = {
        "type": type,
        "subject": subject,
        "topic": topic,
        "grade": grade,
        "style": style,
        "outline": outline,
        "requirements": requirements,
        "difficulty": difficulty,
        "totalScore": totalScore,
        "choiceCount": choiceCount,
        "fillCount": fillCount,
        "essayCount": essayCount,
        "generateAB": generateAB,
        "duration": duration,
        "studentProfile": studentProfile,
        "interactionDesign": interactionDesign,
        "lessonFocus": lessonFocus,
        "usageScene": usageScene,
        "assessment": assessment,
        "target": target,
        "questionTypes": questionTypes,
        "scenario": scenario,
        "count": count,
        "template": template,
        "engine": engine,
        "sparkTemplateId": sparkTemplateId,
        "isCardNote": isCardNote,
        "isFigure": isFigure,
    }

    # 后台异步执行
    _update_task(task_id, params=params)
    asyncio.create_task(_run_generation(task_id, params))
    return {"taskId": task_id, "status": "queued"}


class RefineRequest(BaseModel):
    instruction: str  # 用户在问答区提出的修改意见


@app.post("/api/courseware/{task_id}/refine")
async def refine_courseware(task_id: str, req: RefineRequest):
    """按用户修改意见重跑生成：沿用原参数 + 累积修改意见，产出新版文件"""
    task = _tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    if task.get("status") == "processing":
        raise HTTPException(status_code=409, detail="当前正在生成中，请稍候再提修改")

    instruction = req.instruction.strip()
    if not instruction:
        raise HTTPException(status_code=400, detail="请填写修改意见")

    params = dict(task.get("params") or {})
    if not params:
        raise HTTPException(status_code=400, detail="该任务缺少生成参数，无法修改")

    revisions = list(task.get("revisions") or [])
    revisions.append(instruction)
    params["revision"] = "；".join(revisions)

    # 复用同一 task_id：下载地址不变，完成即覆盖为新版文件
    _stream_text[task_id] = ""
    _update_task(
        task_id,
        params=params,
        revisions=revisions,
        status="processing",
        progress=0,
        stage="正在按修改意见调整…",
        content_md=None,
        filename=None,
        filepath=None,
        error=None,
    )
    asyncio.create_task(_run_generation(task_id, params))
    return {"taskId": task_id, "status": "processing", "revisions": revisions}


# ── API: 导出最终内容 ─────────────────────────────────────────
# 内容生成（流式）与文件导出分离：用户先在右侧确认内容，满意后点击导出按钮，
# 后端才把 content_md 渲染成 docx / html / pptx 并置为可下载。

@app.post("/api/courseware/{task_id}/export")
async def export_courseware(task_id: str):
    task = _tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    if task.get("status") in ("processing", "exporting"):
        raise HTTPException(status_code=409, detail="当前正在处理中，请稍候")
    if not task.get("content_md"):
        raise HTTPException(status_code=400, detail="内容尚未生成，无法导出")

    # 清空流式缓冲，避免导出时 SSE 重复推送正文
    _stream_text[task_id] = ""
    _update_task(
        task_id, status="exporting", progress=0,
        stage="正在排版导出…", filename=None, filepath=None, error=None,
    )
    asyncio.create_task(_run_export(task_id, dict(task.get("params") or {})))
    return {"taskId": task_id, "status": "exporting"}


def _render_local_ppt(content: dict, template_id: str):
    """本地模板渲染：skill 精品模版走保版式引擎，其余走通用模板。"""
    if template_id and is_skill_template(template_id):
        return generate_skill_pptx(content, template_id)
    return generate_pptx_from_template(content, template_id)


async def _run_generation(task_id: str, params: dict):
    """后台流式生成正文（Markdown）：增量写入 _stream_text，完成后置为 ready 待导出。"""
    revision = params.get("revision", "")
    try:
        _update_task(task_id, status="processing", progress=5, stage="正在编写内容…")
        _stream_text[task_id] = ""

        if params["type"] == "ppt":
            stream = stream_ppt_content(
                params["subject"], params["topic"],
                params["grade"], params["style"], params["outline"], revision,
            )
        elif params["type"] == "doc":
            stream = stream_doc_content(
                params["subject"], params["topic"],
                params["grade"], params["requirements"], revision,
            )
        elif params["type"] == "exam":
            stream = stream_exam_content(
                params["subject"], params["topic"],
                grade=params["grade"], difficulty=params.get("difficulty", "中等"),
                total_score=int(params.get("totalScore", 100)),
                choice_count=int(params.get("choiceCount", 10)),
                fill_count=int(params.get("fillCount", 6)),
                essay_count=int(params.get("essayCount", 4)),
                generate_ab=params.get("generateAB", "false").lower() == "true",
                usage_scene=params.get("usageScene", ""),
                assessment=params.get("assessment", ""),
                target=params.get("target", ""),
                student_profile=params.get("studentProfile", ""),
                revision=revision,
            )
        else:
            stream = stream_quiz_content(
                params["subject"], params["topic"],
                params["grade"], params["difficulty"],
                scenario=params.get("scenario", ""),
                count=int(params.get("count") or 8),
                question_types=params.get("questionTypes", ""),
                target=params.get("target", ""),
                student_profile=params.get("studentProfile", ""),
                assessment=params.get("assessment", ""),
                revision=revision,
            )

        # 边生成边推进度（85% 封顶，剩余留给导出）；仅改内存、不逐次落盘
        async for delta in stream:
            _stream_text[task_id] = _stream_text.get(task_id, "") + delta
            task = _tasks.get(task_id)
            if task and task.get("progress", 5) < 85:
                task["progress"] = task["progress"] + 1

        _update_task(
            task_id,
            content_md=_stream_text.get(task_id, ""),
            progress=100,
            status="ready",
            stage="内容已生成，可提出修改或导出",
        )
    except Exception as e:
        _update_task(task_id, status="failed", error=str(e),
                     stage=f"生成失败：{str(e)[:80]}")


async def _run_export(task_id: str, params: dict):
    """把用户确认后的 Markdown 内容渲染为最终文件（docx / html / pptx）。"""
    task = _tasks.get(task_id, {})
    md = task.get("content_md") or ""
    meta = {
        "subject": params.get("subject", ""),
        "grade": params.get("grade", ""),
        "style": params.get("style", ""),
        "duration": params.get("duration", "45分钟"),
        "topic": params.get("topic", ""),
        "totalScore": params.get("totalScore", ""),
    }
    try:
        _update_task(task_id, status="exporting", progress=20, stage="正在排版…")
        await asyncio.sleep(0.1)

        if params.get("type") == "ppt":
            content = parse_ppt_outline(md, meta)
            content["subject"] = meta["subject"]
            content["style"] = meta["style"]
            template_id = params.get("template", "") or ""
            engine = (params.get("engine") or "spark").lower()
            filepath, filename = None, None

            if engine == "spark":
                _update_task(task_id, progress=50, stage="正在排版并自动配图…")
                # 讯飞脚本可能同步阻塞，放线程池执行避免卡住事件循环
                spark_result = await asyncio.to_thread(generate_pptx_via_spark, content, params)
                if spark_result:
                    filepath, filename = spark_result
                else:
                    # 讯飞不可用/失败 → 回退本地模板渲染，保证任务不中断
                    _update_task(task_id, stage="自动排版不可用，改用本地模版…")

            if not filepath:
                filepath, filename = await asyncio.to_thread(
                    _render_local_ppt, content, template_id
                )
        elif params.get("type") == "doc":
            _update_task(task_id, progress=60, stage="正在生成 Word 教案…")
            filepath, filename = await asyncio.to_thread(
                generate_docx_from_markdown, md, meta
            )
        elif params.get("type") == "exam":
            _update_task(task_id, progress=60, stage="正在生成试卷文件…")
            filepath, filename = await asyncio.to_thread(
                generate_exam_html_from_markdown, md, meta
            )
        else:
            _update_task(task_id, progress=60, stage="正在生成练习文件…")
            filepath, filename = await asyncio.to_thread(
                generate_quiz_html_from_markdown, md, meta
            )

        _update_task(task_id, progress=100, stage="导出完成",
                     status="completed", filename=filename, filepath=filepath)

    except Exception as e:
        _update_task(task_id, status="failed", error=str(e),
                     stage=f"导出失败：{str(e)[:80]}")


# ── API: 历史记录 ─────────────────────────────────────────────
# 注意：此路由必须定义在 /api/courseware/{task_id} 之前，
# 否则 FastAPI 会按顺序把 "list" 当作 task_id 匹配

@app.get("/api/courseware/list")
def list_tasks():
    return [
        {
            "id": t["id"],
            "type": t["type"],
            "subject": t.get("subject", ""),
            "topic": t.get("topic", ""),
            "grade": t.get("grade", ""),
            "status": t["status"],
            "progress": t.get("progress", 0),
            "stage": t["stage"],
            "filename": t.get("filename"),
            "error": t.get("error"),
            "created_at": t.get("created_at", ""),
        }
        for t in sorted(_tasks.values(), key=lambda x: x["id"], reverse=True)
    ]


# ── API: 查询任务状态 ─────────────────────────────────────────

@app.get("/api/courseware/{task_id}")
def get_task(task_id: str):
    task = _tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    return task


# ── API: SSE 进度流 ────────────────────────────────────────────

@app.get("/api/courseware/{task_id}/stream")
async def stream_progress(task_id: str):
    """Server-Sent Events：实时推送生成进度 + 正文增量（delta）"""
    async def event_generator():
        last_progress = -1
        cursor = 0  # 已推送的正文长度
        while True:
            task = _tasks.get(task_id)
            if not task:
                yield f"event: error\ndata: {json.dumps({'message': '任务不存在'})}\n\n"
                break

            # 1. 先推送正文增量，保证「ready」前的内容不丢
            buf = _stream_text.get(task_id, "")
            if len(buf) > cursor:
                chunk = buf[cursor:]
                cursor = len(buf)
                yield f"event: delta\ndata: {json.dumps({'text': chunk}, ensure_ascii=False)}\n\n"

            status = task["status"]
            terminal = status in ("ready", "completed", "failed")
            if task["progress"] != last_progress or terminal:
                data = json.dumps({
                    "status": status,
                    "progress": task["progress"],
                    "stage": task["stage"],
                    "filename": task.get("filename"),
                    "error": task.get("error"),
                }, ensure_ascii=False)
                yield f"event: progress\ndata: {data}\n\n"
                last_progress = task["progress"]

            if terminal:
                break

            await asyncio.sleep(0.15)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ── API: 文件下载 ─────────────────────────────────────────────

@app.get("/api/courseware/{task_id}/download")
def download_file(task_id: str):
    task = _tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    if task["status"] != "completed" or not task.get("filepath"):
        raise HTTPException(status_code=400, detail="文件尚未准备好")
    if not os.path.exists(task["filepath"]):
        raise HTTPException(status_code=404, detail="文件已被清理")

    return FileResponse(
        task["filepath"],
        filename=task["filename"],
        media_type="application/octet-stream",
    )


# ── API: AI 备课助手 ─────────────────────────────────────────

class ChatMessage(BaseModel):
    role: str  # user | assistant
    content: str


class TeacherProfile(BaseModel):
    subject: str = ""  # 教师学科
    grade: str = ""    # 任教年级/学段


class ChatRequest(BaseModel):
    messages: list[ChatMessage]
    feature: str = ""            # 大功能（构思层）：plan / lesson / quiz，空为通用问答
    profile: TeacherProfile | None = None  # 教师角色画像（可空）


@app.post("/api/chat")
async def chat_endpoint(req: ChatRequest):
    """AI 备课助手：按教师画像 + 大功能定向调用 Qwen，流式（SSE）返回，前端逐字渲染"""
    messages = [{"role": m.role, "content": m.content} for m in req.messages]
    profile = (
        {"subject": req.profile.subject, "grade": req.profile.grade}
        if req.profile
        else {}
    )

    async def event_stream():
        try:
            async for delta in chat_with_qwen_stream(
                messages, feature=req.feature, profile=profile
            ):
                yield f"data: {json.dumps({'content': delta}, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"
        except HTTPException:
            yield f"data: {json.dumps({'error': 'AI 备课助手服务异常'}, ensure_ascii=False)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


# ── API: PPT 模版列表 ─────────────────────────────────────────

@app.get("/api/templates")
def list_templates():
    """返回可用的 PPT 模版列表（含 GordenPPTSkill 精品模版）"""
    templates = get_template_list()
    # 合并 skill 精品模版，并标记引擎来源以便前端区分
    for t in get_skill_template_list():
        t["engine"] = "skill"
        templates.append(t)
    return {
        "templates": templates,
        "defaultTemplate": pick_template(),
    }


# ── API: 讯飞智文 PPT 模板列表 ─────────────────────────────────

@app.get("/api/spark/templates")
async def list_spark_templates():
    """返回讯飞智文模板列表。

    上游模板接口的分页参数必须放在 JSON Body 里，因此这里分页抓取多页并去重，
    一次性返回全部可用模板（约百个），total 为去重后的真实条数。失败（未配置凭据 /
    网络异常）时返回空列表 + error，不抛 500，以便前端优雅降级。
    """
    try:
        data = await asyncio.to_thread(get_spark_templates, "not_free")
        return {"templates": data.get("templates", []), "total": data.get("total", 0)}
    except Exception as e:
        return {"templates": [], "total": 0, "error": str(e)[:200]}


@app.get("/api/skill/templates/{slug}/preview")
def skill_template_preview(slug: str):
    """返回 skill 模版的预览图 preview.png"""
    from skill_ppt import _template_path as _sp
    import os as _os
    parent = _os.path.dirname(_sp(slug))
    p = _os.path.join(parent, "preview.png")
    if not _os.path.exists(p):
        raise HTTPException(status_code=404, detail="预览图不存在")
    return FileResponse(p, media_type="image/png")


# ── API: 删除任务 ─────────────────────────────────────────────

@app.delete("/api/courseware/{task_id}")
def delete_task(task_id: str):
    task = _tasks.pop(task_id, None)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    _stream_text.pop(task_id, None)
    # 清理文件
    fp = task.get("filepath")
    if fp and os.path.exists(fp):
        os.remove(fp)
    _save_tasks()
    return {"ok": True}


# ── 静态文件服务（预览输出目录） ──────────────────────────────

@app.on_event("startup")
def startup():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(DATA_DIR, exist_ok=True)
    # 加载历史任务记录，保证管理后台统计不丢失
    _load_tasks()


if __name__ == "__main__":
    import uvicorn

    # ws="none"：本项目只用 SSE（StreamingResponse）推送进度，不需要 WebSocket。
    # 且新版 uvicorn 的 WebSocket 实现要求 websockets>=14，而机器上是 websockets 10.4，
    # 不关掉会导致 worker 启动即 ImportError 崩溃。
    uvicorn.run("main:app", host=HOST, port=PORT, reload=True, ws="none")
