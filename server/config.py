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


# AI 配置 —— 两条调用通道（都是阿里云百炼 DashScope 的 OpenAI 兼容接口）
# 两条通道 Base URL 相同，区别只在「用哪个 Key / 哪个额度池」：
#   deepseek：DEEPSEEK_API_KEY + deepseek-v4.1-flash
#   qwen    ：QWEN_API_KEY + CONTENT_MODEL（默认 qwen3.8-max）
# 注册获取 Key: https://bailian.console.aliyun.com/
# ==================================================================
DEEPSEEK_API_KEY = _cred("DEEPSEEK_API_KEY")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL") or "https://dashscope.aliyuncs.com/compatible-mode/v1"
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL") or "deepseek-v4.1-flash"

# Qwen 通道 —— 同时用于「内容制作」与「教师 AI 助手对话」
QWEN_API_KEY = _cred("QWEN_API_KEY")
QWEN_BASE_URL = os.getenv("QWEN_BASE_URL") or "https://dashscope.aliyuncs.com/compatible-mode/v1"
QWEN_MODEL = os.getenv("QWEN_MODEL") or "qwen3.8-27b"  # AI 助手对话用（可用 qwen-plus / qwen-max 等）

# ── 内容制作通道（课件 / 教案 / 出题 / 试卷）──────────────────────
# 2026-10-19：DEEPSEEK_API_KEY 所在工作区的**免费额度耗尽**，DashScope 直接返回
#   403 {"code":"AllocationQuota.FreeTierOnly","message":"Free quota exhausted..."}
# 表现是四个内容制作角色全部生成失败，与代码无关。故默认改走 qwen 通道（实测可用）。
# 想切回 DeepSeek：CONTENT_PROVIDER=deepseek，或单独 PPT_PROVIDER=deepseek 只切一个角色。
# 每个角色仍可用 <ROLE>_MODEL 单独钉死模型，例如 PPT_MODEL=qwen3.8-max。
# ==================================================================
CONTENT_PROVIDER = (os.getenv("CONTENT_PROVIDER") or "qwen").lower()
CONTENT_MODEL = os.getenv("CONTENT_MODEL") or "qwen3.8-max"
# 主通道因「额度 / 鉴权 / 模型未开通」失败时，是否自动换另一条通道重试一次。
# auto=自动回退，off=不回退（直接报错）。
CONTENT_FALLBACK = (os.getenv("CONTENT_FALLBACK") or "auto").lower()


def _role_provider(role: str) -> str:
    return (os.getenv(f"{role}_PROVIDER") or CONTENT_PROVIDER).lower()


def _role_model(role: str, provider: str) -> str:
    explicit = os.getenv(f"{role}_MODEL")
    if explicit:
        return explicit
    return CONTENT_MODEL if provider == "qwen" else DEEPSEEK_MODEL


# 角色对应：PPT=课件制作 / DOC=教案编写 / QUIZ=课堂练习 / EXAM=试卷生成
PPT_PROVIDER, DOC_PROVIDER = _role_provider("PPT"), _role_provider("DOC")
QUIZ_PROVIDER, EXAM_PROVIDER = _role_provider("QUIZ"), _role_provider("EXAM")
PPT_MODEL = _role_model("PPT", PPT_PROVIDER)
DOC_MODEL = _role_model("DOC", DOC_PROVIDER)
QUIZ_MODEL = _role_model("QUIZ", QUIZ_PROVIDER)
EXAM_MODEL = _role_model("EXAM", EXAM_PROVIDER)

# 服务配置
HOST = "0.0.0.0"
PORT = 8000
BASE_DIR = os.path.dirname(__file__)
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
DATA_DIR = os.path.join(BASE_DIR, "data")
TASKS_FILE = os.path.join(DATA_DIR, "tasks.json")  # 任务记录（仅元数据）
CONTENTS_DIR = os.path.join(DATA_DIR, "contents")  # 正文 Markdown，按 task_id 单独存放
MAX_FILE_SIZE_MB = 50
