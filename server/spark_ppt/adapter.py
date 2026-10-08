"""
spark_ppt.adapter — 讯飞星火（讯飞智文）PPT 生成适配层

职责：把 DeepSeek 生成好的 PPT 大纲交给 spark_ppt/ 下你自己放置的讯飞脚本，
      回收生成的 pptx 路径并返回给上层。

与本地渲染引擎的边界
--------------------
- 本适配层只负责「调用你的脚本 + 回收产物」，不做任何 PPT 排版
- 任何异常都在这里被吞掉并返回 None，上层 main.py 据此回退本地模板渲染
"""

import os
import sys
import re
import importlib
import traceback

_PKG_DIR = os.path.dirname(os.path.abspath(__file__))
_SERVER_DIR = os.path.dirname(_PKG_DIR)
_CONFIG_DIR = os.path.join(_PKG_DIR, "config")
_PKG_NAME = os.path.basename(_PKG_DIR)

# 扫描时排除的自身模块
_SELF_MODULES = {"__init__", "adapter"}

# 兼容的入口函数名（按顺序匹配第一个可调用的）
_ENTRY_NAMES = ("generate_pptx", "create_pptx")


def _ensure_importable():
    """把 server / spark_ppt / spark_ppt.config 加入 sys.path，
    使你的脚本能直接 import config/ 下的配置模块。"""
    for path in (_SERVER_DIR, _PKG_DIR, _CONFIG_DIR):
        if path not in sys.path:
            sys.path.insert(0, path)


def _find_entry():
    """扫描 spark_ppt/ 下的脚本，返回符合契约的入口函数；找不到返回 None。"""
    try:
        filenames = sorted(os.listdir(_PKG_DIR))
    except OSError:
        return None

    for fname in filenames:
        if not fname.endswith(".py") or fname.startswith("_"):
            continue
        mod_name = fname[:-3]
        if mod_name in _SELF_MODULES:
            continue
        try:
            module = importlib.import_module(f"{_PKG_NAME}.{mod_name}")
        except Exception:
            print(f"[SPARK] 导入脚本 {fname} 失败:")
            traceback.print_exc()
            continue
        for entry_name in _ENTRY_NAMES:
            func = getattr(module, entry_name, None)
            if callable(func):
                return func
    return None


def _build_output_path(outline: dict) -> str:
    """按课件标题在 OUTPUT_DIR 下生成一个不冲突的 pptx 输出路径。"""
    from config import OUTPUT_DIR

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    title = str(outline.get("title") or "课件")
    safe_title = re.sub(r'[<>:"/\\|?*]', "_", title).strip() or "课件"
    return os.path.join(OUTPUT_DIR, f"{safe_title}_讯飞.pptx")


def generate_pptx_via_spark(outline: dict, params: dict = None):
    """调用讯飞 PPT 脚本生成课件。

    参数:
        outline: DeepSeek 生成的 PPT 大纲（含 title / slides 等字段）
        params:  任务原始参数（学科、年级、模版等），透传给脚本备用

    返回:
        成功 -> (filepath, filename)
        失败 -> None（上层据此回退本地模板渲染）
    """
    _ensure_importable()

    entry = _find_entry()
    if entry is None:
        print("[SPARK] 未在 spark_ppt/ 下找到入口函数（generate_pptx / create_pptx），跳过讯飞生成")
        return None

    output_path = _build_output_path(outline)
    try:
        result = entry(outline, output_path)

        # 兼容返回 str 路径 或 (路径, 文件名)
        if isinstance(result, (tuple, list)):
            result_path = result[0] if result else None
        else:
            result_path = result
        # 脚本没返回路径时，认为它写到了约定路径
        filepath = result_path or output_path

        if not os.path.exists(filepath):
            print(f"[SPARK] 脚本未产出文件，期望路径: {filepath}")
            return None

        print(f"[SPARK] 已生成: {filepath}")
        return filepath, os.path.basename(filepath)

    except Exception:
        print("[SPARK] 讯飞 PPT 生成失败，将回退本地模板渲染:")
        traceback.print_exc()
        return None