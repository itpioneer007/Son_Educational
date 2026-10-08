import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from spark_ppt import generate_pptx_via_spark
from spark_ppt.xf_ppt_client import build_query, build_xf_outline

content = {
    "title": "牛顿第三定律",
    "subtitle": "高中物理 · 必修一",
    "slides": [
        {"type": "title", "title": "牛顿第三定律", "content": ["高中物理·必修一"]},
        {"type": "section", "title": "第一部分：概念引入", "content": []},
        {"type": "content", "title": "作用力与反作用力",
         "content": ["大小相等", "方向相反", "作用在不同物体上"]},
        {"type": "content", "title": "与平衡力的区别", "content": ["受力物体不同", "力的性质不同"]},
        {"type": "section", "title": "第二部分：规律应用", "content": []},
        {"type": "content", "title": "典型例题", "content": ["火箭升空", "走路时的摩擦力"]},
        {"type": "summary", "title": "课堂小结", "content": ["三同三不同"]},
    ],
}

print("=== 1. 讯飞 OutlineVo ===")
print(json.dumps(build_xf_outline(content), ensure_ascii=False, indent=2))

print("\n=== 2. query 文本 ===")
print(build_query(content))

print("\n=== 3. adapter 调用（凭据为空 -> 应回退返回 None）===")
print("RESULT:", generate_pptx_via_spark(content, {"subject": "物理"}))