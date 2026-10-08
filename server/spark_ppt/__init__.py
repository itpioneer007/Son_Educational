"""
讯飞星火（讯飞智文）PPT 生成接入包
==================================
两段式 PPT 生成流程的第二段：

    DeepSeek 生成 PPT 大纲(JSON)  →  本包调用讯飞 PPT 模型出稿

目录约定
--------
spark_ppt/
├── __init__.py       ← 本文件
├── adapter.py        ← 适配层：把大纲喂给你的脚本，并回收 pptx 路径
├── config/           ← 放讯飞配置（AppID / APIKey / APISecret 等）
└── <你的脚本>.py      ← 放你的讯飞 PPT 生成脚本

接入契约
--------
把你的脚本放进 spark_ppt/ 后，让脚本暴露以下入口函数即可（二选一）：

    def generate_pptx(outline: dict, output_path: str, options: dict = None) -> str:
        '''outline:      DeepSeek 生成的 PPT 大纲，结构见 ai_service.PPT_SYSTEM_PROMPT
           output_path:  期望输出 pptx 的绝对路径
           options:      可选覆盖参数，如
                         {"sparkTemplateId": "...", "isCardNote": "true", "isFigure": "true"}
           返回值:        实际生成的 pptx 路径(str)，也兼容返回 (路径, 文件名)

        注：也兼容只接收两个参数 (outline, output_path) 的旧签名，adapter 会自动识别。

config/ 目录会自动加入 sys.path，脚本内可直接 import 配置模块读取密钥。

失败处理：脚本缺失、入口函数不存在或调用抛异常时，
generate_pptx_via_spark() 返回 None，由 main.py 回退到本地模板渲染。
"""

from .adapter import generate_pptx_via_spark
from .xf_ppt_client import get_templates

__all__ = ["generate_pptx_via_spark", "get_templates"]