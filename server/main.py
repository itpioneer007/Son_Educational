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

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Query
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from config import OUTPUT_DIR, DATA_DIR, TASKS_FILE, HOST, PORT
from ai_service import (
    generate_ppt_content, generate_doc_content, generate_quiz_content, generate_exam_content,
    chat_with_qwen, chat_with_qwen_stream,
)
from file_generator import (
    generate_pptx, generate_pptx_from_template,
    generate_docx, generate_quiz_html, generate_exam_html,
    get_template_list, pick_template,
)
from skill_ppt import (
    is_skill_template, generate_skill_pptx,
    get_template_list as get_skill_template_list,
)
from spark_ppt import generate_pptx_via_spark

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
        "status": "queued",     # queued → processing → completed / failed
        "progress": 0,
        "stage": "等待处理",
        "filename": None,
        "filepath": None,
        "error": None,
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
    template: str = Form(""),       # PPT 模版 ID，为空时自动根据学科匹配
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
        "template": template,
    }

    # 后台异步执行
    asyncio.create_task(_run_generation(task_id, params))
    return {"taskId": task_id, "status": "queued"}


async def _run_generation(task_id: str, params: dict):
    """后台执行生成流程并逐步推送进度"""
    try:
        _update_task(task_id, status="processing", progress=0, stage="AI 正在构思课件结构...")
        await asyncio.sleep(0.3)

        # 1. AI 生成内容
        _update_task(task_id, progress=25, stage="调用 AI 生成课件内容...")
        if params["type"] == "ppt":
            content = await generate_ppt_content(
                params["subject"], params["topic"],
                params["grade"], params["style"], params["outline"],
            )
        elif params["type"] == "doc":
            content = await generate_doc_content(
                params["subject"], params["topic"],
                params["grade"], params["requirements"],
            )
        elif params["type"] == "exam":
            content = await generate_exam_content(
                params["subject"], params["topic"],
                grade=params["grade"], difficulty=params.get("difficulty", "中等"),
                total_score=int(params.get("totalScore", 100)),
                choice_count=int(params.get("choiceCount", 10)),
                fill_count=int(params.get("fillCount", 6)),
                essay_count=int(params.get("essayCount", 4)),
                generate_ab=params.get("generateAB", "false").lower() == "true",
            )
        else:
            content = await generate_quiz_content(
                params["subject"], params["topic"],
                params["grade"], params["difficulty"],
            )

        _update_task(task_id, progress=60, stage="正在渲染文件...")
        await asyncio.sleep(0.2)

        # 2. 渲染文件
        content["subject"] = params.get("subject", "")
        content["style"] = params.get("style", "")
        content["grade"] = params.get("grade", "")
        content["duration"] = params.get("duration", "45分钟")
        if params["type"] == "ppt":
            # 两段式流程：DeepSeek 已生成大纲(content)，此处交给讯飞 PPT 模型出稿
            template_id = params.get("template", "") or ""
            _update_task(task_id, progress=70, stage="正在调用讯飞 PPT 模型生成中...")
            # 讯飞脚本可能同步阻塞，放线程池执行避免卡住事件循环
            spark_result = await asyncio.to_thread(generate_pptx_via_spark, content, params)

            if spark_result:
                filepath, filename = spark_result
            else:
                # 讯飞不可用/失败 → 回退本地模板渲染，保证任务不中断
                _update_task(task_id, stage="讯飞生成不可用，回退本地模版渲染...")
                # skill 精品模版走保版式引擎
                if template_id and is_skill_template(template_id):
                    filepath, filename = generate_skill_pptx(content, template_id)
                else:
                    filepath, filename = generate_pptx_from_template(content, template_id)
        elif params["type"] == "doc":
            filepath, filename = generate_docx(content)
        elif params["type"] == "exam":
            filepath, filename = generate_exam_html(content)
        else:
            filepath, filename = generate_quiz_html(content)

        _update_task(task_id, progress=100, stage="生成完成",
                      status="completed", filename=filename, filepath=filepath)

    except Exception as e:
        _update_task(task_id, status="failed", error=str(e),
                      stage=f"生成失败: {str(e)[:80]}")


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
    """Server-Sent Events 实时推送生成进度"""
    async def event_generator():
        last_progress = -1
        while True:
            task = _tasks.get(task_id)
            if not task:
                yield f"event: error\ndata: {json.dumps({'message': '任务不存在'})}\n\n"
                break

            if task["progress"] != last_progress or task["status"] in ("completed", "failed"):
                data = json.dumps({
                    "status": task["status"],
                    "progress": task["progress"],
                    "stage": task["stage"],
                    "filename": task.get("filename"),
                    "error": task.get("error"),
                }, ensure_ascii=False)
                yield f"event: progress\ndata: {data}\n\n"
                last_progress = task["progress"]

            if task["status"] in ("completed", "failed"):
                break

            await asyncio.sleep(0.5)

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
    uvicorn.run("main:app", host=HOST, port=PORT, reload=True)
