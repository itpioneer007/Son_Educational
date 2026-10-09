# -*- coding: utf-8 -*-
"""
讯飞智文 PPT 生成客户端
=======================
两段式流程的第二段：DeepSeek 已产出大纲 → 交给讯飞智文出稿。

采用官方「流程二：通过大纲生成 PPT」：
    1. build_xf_outline()  DeepSeek 大纲 → 讯飞 OutlineVo 结构
    2. create_ppt_task()   POST /api/ppt/v2/createPptByOutline  → sid
    3. wait_for_ppt()      GET  /api/ppt/v2/progress            → pptUrl
    4. _download()         把 pptUrl 下载成本地 pptx

对外暴露 generate_pptx(outline, output_path)，供 spark_ppt.adapter 自动发现。
任何异常都向上抛出，由 adapter 捕获后回退本地模板渲染。
"""

import base64
import hashlib
import hmac
import json
import os
import sys
import time

import requests

_API_BASE = "https://zwapi.xfyun.cn/api/ppt/v2"
_MAX_CHAPTERS = 10    # 官方限制：一级大纲不超过 10 个
_MAX_QUERY_LEN = 8000  # 官方限制：query 不超过 8000 字


# ════════════════════════════════════════════════════════════════
# 鉴权
# ════════════════════════════════════════════════════════════════

def _signature(app_id: str, api_secret: str, timestamp: int) -> str:
    """官方签名算法：HMAC-SHA1(md5(appId + timestamp), apiSecret) → Base64"""
    auth = hashlib.md5(f"{app_id}{timestamp}".encode("utf-8")).hexdigest()
    digest = hmac.new(
        api_secret.encode("utf-8"), auth.encode("utf-8"), hashlib.sha1
    ).digest()
    return base64.b64encode(digest).decode("utf-8")


def _headers(app_id: str, api_secret: str) -> dict:
    timestamp = int(time.time())
    return {
        "appId": app_id,
        "timestamp": str(timestamp),
        "signature": _signature(app_id, api_secret, timestamp),
        "Content-Type": "application/json; charset=utf-8",
    }


def _load_config():
    """读取 config/spark_config.py。"""
    config_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config")
    if config_dir not in sys.path:
        sys.path.insert(0, config_dir)
    import spark_config
    return spark_config


# ════════════════════════════════════════════════════════════════
# 模板列表查询
# ════════════════════════════════════════════════════════════════

def _extract_preview(item: dict) -> str:
    """detailImage 是 JSON 字符串，内含各页封面图；取标题封面图作预览。"""
    detail = item.get("detailImage")
    if isinstance(detail, str) and detail.strip():
        try:
            images = json.loads(detail)
        except ValueError:
            images = None
        if isinstance(images, dict):
            for key in ("titleCoverImage", "titleCoverImageLarge",
                        "catalogueCoverImage", "contentCoverImage"):
                if images.get(key):
                    return images[key]
    return item.get("thumbnail") or item.get("coverUrl") or item.get("preview") or ""


def _normalize_templates(data) -> list:
    """解析讯飞模板列表响应。

    真实结构：data = {total: N, records: [{templateIndexId, style, color,
    industry, pageCount, payType, detailImage(JSON字符串)}]}
    同时兼容 data 为 list / {templates:[...]} / {list:[...]} 的形态。
    """
    if isinstance(data, dict):
        items = data.get("records") or data.get("templates") or data.get("list") or []
    elif isinstance(data, list):
        items = data
    else:
        items = []

    result = []
    for item in items:
        if not isinstance(item, dict):
            continue
        template_id = (
            item.get("templateIndexId") or item.get("templateId")
            or item.get("template_id") or item.get("id") or item.get("key")
        )
        if not template_id:
            continue
        style = str(item.get("style") or "").strip()
        color = str(item.get("color") or "").strip()
        name = (
            item.get("name") or item.get("title")
            or " · ".join(p for p in (style, color) if p)
            or str(template_id)
        )
        result.append({
            "id": str(template_id),
            "name": name,
            "preview": _extract_preview(item),
            "style": style,
            "color": color,
            "industry": str(item.get("industry") or "").strip(),
        })
    return result


# 模板列表缓存：上游按页拉取耗时明显，进程内缓存一段时间，避免每次进市场都重拉
_TEMPLATE_CACHE: dict = {}
_TEMPLATE_CACHE_TTL = 30 * 60  # 秒
_TEMPLATE_PAGE_SIZE = 50       # 每页条数（上游上限）
_TEMPLATE_MAX_PAGES = 2        # 抓取前 2 页，约 100 个模板

# 讯飞模板接口的正确用法：分页参数必须放在 JSON Body 里（放 query string 会被忽略，
# 导致每次只返回固定的一批）。用 body 传 pageNum/pageSize 才能翻页取到更多模板。
def _fetch_template_page(app_id: str, api_secret: str, pay_type: str, page_num: int) -> dict:
    resp = requests.post(
        f"{_API_BASE}/template/list",
        json={"payType": pay_type, "pageNum": page_num, "pageSize": _TEMPLATE_PAGE_SIZE},
        headers=_headers(app_id, api_secret),
        timeout=30,
    )
    resp.raise_for_status()
    payload = resp.json()
    if payload.get("code") != 0:
        raise RuntimeError(
            f"查询讯飞模板失败: code={payload.get('code')} desc={payload.get('desc')}"
        )
    return payload.get("data")


def get_templates(pay_type: str = "not_free") -> dict:
    """查询讯飞 PPT 模板列表（分页抓取 + 去重 + 进程内缓存）。

    返回 {"total": 真实条数, "templates": [{id, name, preview, style, color, industry}]}
    """
    cached = _TEMPLATE_CACHE.get(pay_type)
    if cached and time.time() - cached["ts"] < _TEMPLATE_CACHE_TTL:
        return {"total": len(cached["templates"]), "templates": cached["templates"]}

    cfg = _load_config()
    if not cfg.APP_ID or not cfg.API_SECRET:
        raise RuntimeError("未配置讯飞凭据，无法查询模板列表")

    unique, seen = [], set()
    for page_num in range(1, _TEMPLATE_MAX_PAGES + 1):
        data = _fetch_template_page(cfg.APP_ID, cfg.API_SECRET, pay_type, page_num)
        for t in _normalize_templates(data):
            if t["id"] in seen:
                continue
            seen.add(t["id"])
            unique.append(t)

    _TEMPLATE_CACHE[pay_type] = {"ts": time.time(), "templates": unique}
    return {"total": len(unique), "templates": unique}


# ════════════════════════════════════════════════════════════════
# 大纲转换：DeepSeek 结构 → 讯飞 OutlineVo
# ════════════════════════════════════════════════════════════════

def build_query(content: dict) -> str:
    """把各页要点拼成 query 文本——讯飞大纲只承载标题层级，
    正文细节需靠 query 一并传入。"""
    lines = []
    for slide in content.get("slides") or []:
        title = str(slide.get("title") or "").strip()
        bullets = [str(b).strip() for b in (slide.get("content") or []) if str(b).strip()]
        if title and bullets:
            lines.append(f"{title}：" + "；".join(bullets))
        elif title:
            lines.append(title)
    return "\n".join(lines)[:_MAX_QUERY_LEN]


def build_xf_outline(content: dict) -> dict:
    """DeepSeek 大纲 → 讯飞 OutlineVo。

    映射规则：
      - title 页        → 跳过（封面由 title / subTitle 承载）
      - section 页      → 一级大纲 chapters[].chapterTitle
      - content 等页    → 归属到当前章节的 chapterContents[].chapterTitle
      - 无 section 时   → 兜底建一个章节承载全部内容页
    """
    chapters = []
    current = None

    for slide in content.get("slides") or []:
        slide_type = str(slide.get("type") or "").lower()
        title = str(slide.get("title") or "").strip()
        if not title or slide_type == "title":
            continue

        if slide_type == "section":
            current = {"chapterTitle": title, "chapterContents": []}
            chapters.append(current)
            continue

        if current is None:
            current = {
                "chapterTitle": str(content.get("title") or "主要内容").strip(),
                "chapterContents": [],
            }
            chapters.append(current)

        current["chapterContents"].append({"chapterTitle": title})

    # 官方限制一级大纲 ≤10：保留前 9 个，其余子项并入第 10 个
    if len(chapters) > _MAX_CHAPTERS:
        kept = chapters[:_MAX_CHAPTERS - 1]
        overflow_contents = []
        for chapter in chapters[_MAX_CHAPTERS - 1:]:
            overflow_contents.extend(chapter.get("chapterContents") or [])
        kept.append({
            "chapterTitle": chapters[_MAX_CHAPTERS - 1]["chapterTitle"],
            "chapterContents": overflow_contents,
        })
        chapters = kept

    return {
        "title": str(content.get("title") or "教学课件").strip(),
        "subTitle": str(content.get("subtitle") or "").strip(),
        "chapters": chapters,
        "end": "",
    }


# ════════════════════════════════════════════════════════════════
# 讯飞接口调用
# ════════════════════════════════════════════════════════════════

def create_ppt_task(app_id: str, api_secret: str, *, query: str, outline: dict,
                    cfg, template_id: str, is_card_note: bool, is_figure: bool) -> str:
    """创建 PPT 生成任务，返回 sid。"""
    body = {
        "query": query,
        "outline": outline,
        "templateId": template_id,
        "author": cfg.AUTHOR,
        "isCardNote": is_card_note,
        "search": False,
        "isFigure": is_figure,
        "aiImage": cfg.AI_IMAGE,
    }
    resp = requests.post(
        f"{_API_BASE}/createPptByOutline",
        json=body,
        headers=_headers(app_id, api_secret),
        timeout=30,
    )
    resp.raise_for_status()
    payload = resp.json()
    if payload.get("code") != 0:
        raise RuntimeError(
            f"创建讯飞 PPT 任务失败: code={payload.get('code')} desc={payload.get('desc')}"
        )
    sid = (payload.get("data") or {}).get("sid")
    if not sid:
        raise RuntimeError(f"创建讯飞 PPT 任务未返回 sid: {payload}")
    return sid


def wait_for_ppt(app_id: str, api_secret: str, sid: str, cfg) -> str:
    """轮询进度直到产出 pptUrl；超时或失败抛异常。"""
    deadline = time.time() + cfg.TIMEOUT_SECONDS
    while time.time() < deadline:
        resp = requests.get(
            f"{_API_BASE}/progress",
            params={"sid": sid},
            headers=_headers(app_id, api_secret),
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json().get("data") or {}

        if data.get("errMsg"):
            raise RuntimeError(f"讯飞生成失败: {data['errMsg']}")

        ppt_url = data.get("pptUrl")
        if ppt_url:
            return ppt_url

        time.sleep(cfg.POLL_INTERVAL)

    raise TimeoutError(f"讯飞 PPT 生成超时（{cfg.TIMEOUT_SECONDS}s），sid={sid}")


def _download(url: str, dest_path: str):
    """把讯飞返回的下载链接落盘为本地 pptx。"""
    resp = requests.get(url, timeout=120, stream=True)
    resp.raise_for_status()
    with open(dest_path, "wb") as fh:
        for chunk in resp.iter_content(chunk_size=8192):
            if chunk:
                fh.write(chunk)


# ════════════════════════════════════════════════════════════════
# 对 adapter 暴露的入口
# ════════════════════════════════════════════════════════════════

def _to_bool(value, default: bool) -> bool:
    """FormData 传来的布尔是字符串，这里统一归一化。"""
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in ("true", "1", "yes", "on")


def generate_pptx(outline: dict, output_path: str, options: dict = None) -> str:
    """按 DeepSeek 大纲调用讯飞智文生成 pptx，返回本地文件路径。

    options 可覆盖默认配置：sparkTemplateId / isCardNote / isFigure
    """
    cfg = _load_config()
    options = options or {}
    if not cfg.APP_ID or not cfg.API_SECRET:
        raise RuntimeError(
            "未配置讯飞凭据：请在 server/spark_ppt/config/spark_config.py "
            "中填写 APP_ID 与 API_SECRET"
        )

    template_id = str(options.get("sparkTemplateId") or "").strip() or cfg.TEMPLATE_ID
    is_card_note = _to_bool(options.get("isCardNote"), cfg.IS_CARD_NOTE)
    is_figure = _to_bool(options.get("isFigure"), cfg.IS_FIGURE)

    query = build_query(outline)
    xf_outline = build_xf_outline(outline)

    sid = create_ppt_task(
        cfg.APP_ID, cfg.API_SECRET,
        query=query, outline=xf_outline, cfg=cfg,
        template_id=template_id, is_card_note=is_card_note, is_figure=is_figure,
    )
    ppt_url = wait_for_ppt(cfg.APP_ID, cfg.API_SECRET, sid, cfg)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    _download(ppt_url, output_path)
    return output_path