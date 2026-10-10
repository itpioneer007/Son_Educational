import os
import importlib.util

# ==================================================================
# 凭据读取优先级：环境变量 > server/config.local.py（不入库）> 空值
# ==================================================================
# 仓库内不保存任何 API Key。本地开发请在 server/ 下新建 config.local.py：
#     DEEPSEEK_API_KEY = "sk-..."
#     QWEN_API_KEY     = "sk-..."
# 该文件已被 .gitignore 忽略（「API Key 配置（含敏感信息）」段）。
# 部署环境请改用环境变量注入，两种方式任选其一。
# ==================================================================
# 注意：文件名是 config.local.py（与 .gitignore 条目一致），模块名含点号，
# 无法用 import config_local 导入，因此这里按文件路径显式加载。
_LOCAL_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.local.py")


def _load_local():
    """加载同目录下不入库的 config.local.py；文件不存在或读取失败时返回 None。"""
    if not os.path.exists(_LOCAL_FILE):
        return None
    spec = importlib.util.spec_from_file_location("config_local", _LOCAL_FILE)
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception:
        return None
    return module


_local = _load_local()


def _cred(name: str, default: str = "") -> str:
    """凭据取值：环境变量 > config.local.py > 默认值。"""
    value = os.getenv(name)
    if value:
        return value
    if _local is not None:
        value = getattr(_local, name, None)
        if value:
            return value
    return default


# AI 配置 —— 内容生成模型（课件 / 教案 / 出题 / 试卷）
# 统一走阿里云百炼 DashScope 的 deepseek-v4.1-flash（OpenAI 兼容接口）
# 注册获取 Key: https://bailian.console.aliyun.com/
# ==================================================================
DEEPSEEK_API_KEY = _cred("DEEPSEEK_API_KEY")

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
# 用于「知启灵枢 教师 AI 助手」对话；课件/教案/出题/试卷仍走 DeepSeek
# 注册获取 Key: https://bailian.console.aliyun.com/
# 凭据读取方式同上：环境变量 > server/config.local.py
# ==================================================================
QWEN_API_KEY = _cred("QWEN_API_KEY")
QWEN_BASE_URL = os.getenv("QWEN_BASE_URL") or "https://dashscope.aliyuncs.com/compatible-mode/v1"
QWEN_MODEL = os.getenv("QWEN_MODEL") or "qwen3.8-27b"  # 可用 qwen-plus / qwen-max / qwen-turbo 等

# 服务配置
HOST = "0.0.0.0"
PORT = 8000
BASE_DIR = os.path.dirname(__file__)
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
DATA_DIR = os.path.join(BASE_DIR, "data")
TASKS_FILE = os.path.join(DATA_DIR, "tasks.json")  # 任务记录（仅元数据）
CONTENTS_DIR = os.path.join(DATA_DIR, "contents")  # 正文 Markdown，按 task_id 单独存放
MAX_FILE_SIZE_MB = 50
