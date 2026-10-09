"""
输出文件命名
============
统一「本地模板 / GordenPPTSkill / 讯飞智文」三条渲染链路的产物命名，
避免同名课题互相覆盖。

修复的缺陷
----------
原实现三条链路一律用「{标题}.{ext}」落盘，而 OUTPUT_DIR 是全局共享目录，于是：

  ① 两位老师先后生成同名课题 → 后者的文件直接覆盖前者；
  ② 前者任务的 filepath 仍指向该路径 → 点下载拿到的是后者的内容（跨用户串档，且不报错）；
  ③ skill 引擎的临时 edits.json 也按标题命名，并发生成时会互相踩踏。

命名规则
--------
    文件名 = 「{标题}__{uid}.{ext}」     # uid 传 task_id

  - 不同任务 → uid 不同 → 永不互相覆盖；
  - 同一任务重复导出 → uid 相同 → 路径稳定，与「/refine 复用 task_id」的设计一致，
    下载地址不变、完成即覆盖为新版；
  - uid 为空 → 退化为原「{标题}.{ext}」，保持向后兼容（如命令行直接调用）。
"""

import os
import re

from config import OUTPUT_DIR

# 文件名字符白名单限制：Windows 不允许 < > : " / \ | ? *
_ILLEGAL_CHARS = re.compile(r'[<>:"/\\|?*]')

# 标题截断长度：Windows 传统路径上限 260 字符，过长的课题名会直接保存失败
_MAX_STEM_LEN = 80


def safe_stem(title, fallback: str = "未命名") -> str:
    """把任意标题清洗为可用作文件名的片段：去非法字符、去首尾空白与点号、截断、兜底。"""
    stem = _ILLEGAL_CHARS.sub("_", str(title or ""))
    stem = stem.strip().strip(".").strip()
    stem = stem[:_MAX_STEM_LEN].strip().strip(".")
    return stem or fallback


def unique_output_path(title, ext: str, uid: str = "", fallback: str = "未命名"):
    """返回 (绝对路径, 文件名)。uid 非空时拼入文件名，保证跨任务不冲突。"""
    stem = safe_stem(title, fallback)
    if uid:
        stem = f"{stem}__{uid}"
    filename = f"{stem}.{str(ext).lstrip('.')}"
    return os.path.join(OUTPUT_DIR, filename), filename
