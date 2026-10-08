import os

# AI 配置 —— 内容生成模型（课件 / 教案 / 出题 / 试卷）
# 统一走阿里云百炼 DashScope 的 deepseek-v4.1-flash（OpenAI 兼容接口）
# 注册获取 Key: https://bailian.console.aliyun.com/
# ==================================================================
# 优先级：环境变量 > 下方硬编码（方便本地开发）
# ==================================================================
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY") or "sk-ws-H.PHIXRLM.Deyh.MEUCIQChtnF3RkQKwBpfK7tQUDShC9-lAnXdSTQmY-VX9to3ZgIgWctnL6q5cmxjHzXzx1jckMFEw9rDkR0EdXs2RUeXWr4"

DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL") or "https://dashscope.aliyuncs.com/compatible-mode/v1"
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL") or "deepseek-v4.1-flash"

# ── 四大内容制作角色的独立模型配置 ────────────────────────────────
# 每个内容制作角色由「特定 LLM 模型」驱动，默认复用上方内容生成模型，
# 后续可单独将某个角色替换为其他 LLM（改环境变量或下方模型名即可）。
# 角色对应：PPT_MODEL=课件制作 / DOC_MODEL=教案编写 / QUIZ_MODEL=课堂练习 / EXAM_MODEL=试卷生成
# ==================================================================
PPT_MODEL = os.getenv("PPT_MODEL") or DEEPSEEK_MODEL
DOC_MODEL = os.getenv("DOC_MODEL") or DEEPSEEK_MODEL
QUIZ_MODEL = os.getenv("QUIZ_MODEL") or DEEPSEEK_MODEL
EXAM_MODEL = os.getenv("EXAM_MODEL") or DEEPSEEK_MODEL

# Qwen 对话配置 —— 阿里云百炼 DashScope（OpenAI 兼容接口）
# 用于「知课 AI 备课助手」对话；课件/教案/出题/试卷仍走 DeepSeek
# 注册获取 Key: https://bailian.console.aliyun.com/
# ==================================================================
# 优先级：环境变量 > 下方硬编码（方便本地开发）
# ==================================================================
QWEN_API_KEY = os.getenv("QWEN_API_KEY") or "sk-ws-H.EYLDXPX.uTtl.MEYCIQCDdcBAkELSb4AjzM5gIFXIydrgZVLDMFMWbtBUJ4918AIhAKAVh7wpX4DmX0gPcp2bIMc31SgGGT78xCkCRlyUb6TE"
QWEN_BASE_URL = os.getenv("QWEN_BASE_URL") or "https://dashscope.aliyuncs.com/compatible-mode/v1"
QWEN_MODEL = os.getenv("QWEN_MODEL") or "qwen3.8-27b"  # 可用 qwen-plus / qwen-max / qwen-turbo 等

# 服务配置
HOST = "0.0.0.0"
PORT = 8000
BASE_DIR = os.path.dirname(__file__)
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
DATA_DIR = os.path.join(BASE_DIR, "data")
TASKS_FILE = os.path.join(DATA_DIR, "tasks.json")  # 任务记录持久化文件
MAX_FILE_SIZE_MB = 50
