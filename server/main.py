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
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from config import OUTPUT_DIR, DATA_DIR, TASKS_FILE, CONTENTS_DIR, HOST, PORT
from ai_service import (
    stream_ppt_content, stream_doc_content, stream_quiz_content, stream_exam_content,
    chat_with_qwen, chat_with_qwen_stream,
)
from file_generator import (
    generate_pptx_from_template,
    generate_docx_from_markdown, generate_quiz_html_from_markdown,
    generate_exam_html_from_markdown, parse_ppt_outline,
    get_template_list, pick_template,
)
from skill_ppt import (
    is_skill_template, generate_skill_pptx,
    get_template_list as get_skill_template_list,
)
from spark_ppt import generate_pptx_via_spark, get_templates as get_spark_templates

@asynccontextmanager
async def _lifespan(app: FastAPI):
    """启动时准备输出/数据目录并载入历史任务记录。

    替代已废弃的 @app.on_event("startup")：该钩子在未来 FastAPI 版本会被移除。
    """
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(CONTENTS_DIR, exist_ok=True)
    _load_tasks()
    yield


app = FastAPI(title="EduAI 课件生成 API", version="1.0.0", lifespan=_lifespan)

# CORS — 允许前端 dev server 跨域
# 原配置同时开了 allow_origins=["*"] 与 allow_credentials=True，二者互相矛盾：
# 按 CORS 规范，凭据模式下不允许把 Origin 回成通配符，浏览器会直接拒绝该响应，
# 这组配置实际不生效。改为环境变量驱动的显式白名单（默认覆盖 Vite dev server）。
_CORS_ORIGINS = [
    o.strip()
    for o in os.getenv(
        "CORS_ALLOW_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173,"
        "http://localhost:8000,http://127.0.0.1:8000",
    ).split(",")
    if o.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── 任务存储 ─────────────────────────────────────────────────
# 任务持久化到本地 JSON 文件，服务重启后记录不丢失，供管理后台统计
_tasks: dict[str, dict] = {}
# 写盘互斥锁。必须用 threading.Lock 而非 asyncio.Lock：_new_task / _update_task
# 既会从协程里调用，也会从同步路由（delete_task）里调用 —— 后者由 FastAPI
# 丢到线程池执行，asyncio.Lock 跨线程不起作用。
_tasks_lock = threading.Lock()

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
        return

    # 兼容旧数据：早期版本把正文直接存在 tasks.json 的 content_md 里，
    # 而新实现落盘会剥离该字段。若此处不迁出，老任务的正文会在下次重启后丢失。
    for tid, t in _tasks.items():
        md = t.get("content_md")
        if md and not os.path.exists(_content_path(tid)):
            _write_content(tid, md)


# ── 正文存储 ─────────────────────────────────────────────────
# 任务元数据存 tasks.json，正文 Markdown 按 task_id 单独落盘。
# 这样 tasks.json 只随任务条数线性增长，不会因为每篇教案/试卷的全文而膨胀；
# 正文则在真正需要时（查询任务 / 触发导出）再懒加载进内存。

def _content_path(task_id: str) -> str:
    return os.path.join(CONTENTS_DIR, f"{task_id}.md")


def _write_content(task_id: str, text: str):
    """写入（覆盖）任务正文"""
    try:
        os.makedirs(CONTENTS_DIR, exist_ok=True)
        with open(_content_path(task_id), "w", encoding="utf-8") as f:
            f.write(text or "")
    except OSError:
        pass


def _read_content(task_id: str) -> str:
    """读取任务正文；不存在或读取失败返回空串"""
    try:
        with open(_content_path(task_id), "r", encoding="utf-8") as f:
            return f.read()
    except OSError:
        return ""


def _delete_content(task_id: str):
    """删除任务正文（随任务一并清理）"""
    try:
        os.remove(_content_path(task_id))
    except OSError:
        pass


def _ensure_content(task: dict) -> str:
    """确保 task 的正文已载入内存，返回正文。

    内存里没有时（典型场景：服务重启后任务从 tasks.json 恢复）从
    data/contents/{task_id}.md 读回，使 GET /api/courseware/{id} 与导出
    流程都能拿到正文；启动时不预读，避免正文全量驻留内存。
    """
    md = task.get("content_md")
    if md:
        return md
    if not task.get("id"):
        return ""
    md = _read_content(task["id"])
    if md:
        task["content_md"] = md
    return md


def _save_tasks():
    """将任务记录落盘。

    正文不写入 tasks.json：一篇教案/试卷全文 3k–8k 字，若随任务一起落盘，
    该文件会无界膨胀（且启动时被整体读入内存）。正文另存
    data/contents/{task_id}.md，需要时用 _ensure_content() 懒加载。

    并发安全：加锁串行化写入；先写临时文件再 os.replace 原子替换，
    避免多个线程同时写、或进程在写一半时中断，导致 tasks.json 内容残缺
    （残留的半截 JSON 会让下次启动 _load_tasks 直接失败，任务记录全丢）。
    """
    with _tasks_lock:
        try:
            os.makedirs(DATA_DIR, exist_ok=True)
            snapshot = {tid: {**t, "content_md": None} for tid, t in _tasks.items()}
            tmp_path = TASKS_FILE + ".tmp"
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(snapshot, f, ensure_ascii=False, indent=2)
            os.replace(tmp_path, TASKS_FILE)
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
    if not _ensure_content(task):
        raise HTTPException(status_code=400, detail="内容尚未生成，无法导出")

    # 清空流式缓冲，避免导出时 SSE 重复推送正文
    _stream_text[task_id] = ""
    _update_task(
        task_id, status="exporting", progress=0,
        stage="正在排版导出…", filename=None, filepath=None, error=None,
    )
    asyncio.create_task(_run_export(task_id, dict(task.get("params") or {})))
    return {"taskId": task_id, "status": "exporting"}


def _render_local_ppt(content: dict, template_id: str, uid: str = ""):
    """本地模板渲染：skill 精品模版走保版式引擎，其余走通用模板。"""
    if template_id and is_skill_template(template_id):
        return generate_skill_pptx(content, template_id, uid=uid)
    return generate_pptx_from_template(content, template_id, uid)


async def _release_stream_buffer(task_id: str, delay: float = 3.0):
    """任务到达终态后释放流式缓冲区。

    不立即 pop：SSE 客户端每 0.15s 轮询一次缓冲区，若生成刚结束就清空，
    正在连接的客户端可能在最后一次轮询前取不到末尾增量，表现为正文尾部丢失。
    留一个短窗口再清理，避免正文在内存中长期以两份存在（_stream_text 与
    task["content_md"]）。

    若期间又开始了新一轮生成（/refine 复用同一 task_id），status 已回到
    processing，此时跳过清理，避免误删新一轮的缓冲。
    """
    await asyncio.sleep(delay)
    task = _tasks.get(task_id)
    if task is not None and task.get("status") not in ("ready", "completed", "failed"):
        return
    _stream_text.pop(task_id, None)


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

        text = _stream_text.get(task_id, "")
        # 正文落独立文件；tasks.json 里不再保存全文
        _write_content(task_id, text)
        _update_task(
            task_id,
            content_md=text,
            progress=100,
            status="ready",
            stage="内容已生成，可提出修改或导出",
        )
    except Exception as e:
        _update_task(task_id, status="failed", error=str(e),
                     stage=f"生成失败：{str(e)[:80]}")
    finally:
        # 无论成功还是失败都进入终态，安排释放流式缓冲，避免正文长期双份驻留内存
        asyncio.create_task(_release_stream_buffer(task_id))


async def _run_export(task_id: str, params: dict):
    """把用户确认后的 Markdown 内容渲染为最终文件（docx / html / pptx）。"""
    task = _tasks.get(task_id, {})
    md = _ensure_content(task)
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
                spark_result = await asyncio.to_thread(generate_pptx_via_spark, content, params, task_id)
                if spark_result:
                    filepath, filename = spark_result
                else:
                    # 讯飞不可用/失败 → 回退本地模板渲染，保证任务不中断
                    _update_task(task_id, stage="自动排版不可用，改用本地模版…")

            if not filepath:
                filepath, filename = await asyncio.to_thread(
                    _render_local_ppt, content, template_id, task_id
                )
        elif params.get("type") == "doc":
            _update_task(task_id, progress=60, stage="正在生成 Word 教案…")
            filepath, filename = await asyncio.to_thread(
                generate_docx_from_markdown, md, meta, task_id
            )
        elif params.get("type") == "exam":
            _update_task(task_id, progress=60, stage="正在生成试卷文件…")
            filepath, filename = await asyncio.to_thread(
                generate_exam_html_from_markdown, md, meta, task_id
            )
        else:
            _update_task(task_id, progress=60, stage="正在生成练习文件…")
            filepath, filename = await asyncio.to_thread(
                generate_quiz_html_from_markdown, md, meta, task_id
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
        # 按创建时间倒序。注意不能用 id 排序：id 是 uuid4 的随机前缀，
        # 按它排序会得到随机顺序，导致管理后台"最近任务"每次刷新都在跳。
        for t in sorted(
            _tasks.values(), key=lambda x: x.get("created_at", ""), reverse=True
        )
    ]


# ── API: 查询任务状态 ─────────────────────────────────────────

@app.get("/api/courseware/{task_id}")
def get_task(task_id: str):
    task = _tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    # 正文可能只在磁盘上（服务重启后），返回前按需载入
    _ensure_content(task)
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
    _delete_content(task_id)
    _save_tasks()
    return {"ok": True}


if __name__ == "__main__":
    import uvicorn

    # ws="none"：本项目只用 SSE（StreamingResponse）推送进度，不需要 WebSocket。
    # 且新版 uvicorn 的 WebSocket 实现要求 websockets>=14，而机器上是 websockets 10.4，
    # 不关掉会导致 worker 启动即 ImportError 崩溃。
    uvicorn.run("main:app", host=HOST, port=PORT, reload=True, ws="none")
