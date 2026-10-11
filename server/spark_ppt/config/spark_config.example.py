# -*- coding: utf-8 -*-
"""讯飞智文（星火）PPT 能力配置示例。

用法：
    1. 复制本文件为同目录下的 spark_config.py
       （cp config/spark_config.example.py config/spark_config.py）
    2. 在讯飞开放平台控制台申请「讯飞智文」能力，把 APP_ID / API_SECRET 填进去
    3. spark_config.py 已被 .gitignore 忽略，凭据不会进入仓库

若不配置，平台仍可正常使用：PPT 会自动回退到本地内置模板渲染，
模板市场也会展示本地模板；只是没有「讯飞在线模板 + 自动配图」这类能力。

也可不建文件，直接用环境变量提供：
    SPARK_APP_ID / SPARK_API_SECRET / SPARK_TEMPLATE_ID ...
"""

# ── 必填：讯飞开放平台凭据 ──────────────────────────────────
APP_ID = ""
API_SECRET = ""

# ── 以下为可选默认值 ────────────────────────────────────────
# 默认模板 ID（留空则用讯飞侧默认模板）
TEMPLATE_ID = ""
# PPT 作者名
AUTHOR = "知启灵枢"
# AI 配图类型：normal（约 20% 正文配图）/ advanced（约 50%）
AI_IMAGE = "normal"
# 是否生成演讲备注 / 是否自动配图（true / false）
IS_CARD_NOTE = "true"
IS_FIGURE = "true"
# 轮询任务进度的超时与间隔（秒）
TIMEOUT_SECONDS = 300
POLL_INTERVAL = 3
