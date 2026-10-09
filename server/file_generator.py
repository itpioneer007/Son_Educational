"""
文件生成器 — 将 AI 生成的结构化内容渲染为 PPTX / DOCX / HTML 文件
支持多套模板配色，自动根据学科匹配主题风格。
支持基于 public/ppts 目录下的预置 PPTX 模版进行内容填充。
"""

import os
import re
import json
import html
import shutil
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from docx import Document
from docx.shared import Pt as DocxPt, RGBColor as DocxRGB, Inches as DocxInches, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_ALIGN_VERTICAL
from docx.enum.style import WD_STYLE_TYPE
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

from config import OUTPUT_DIR

# ════════════════════════════════════════════════════════════════
# PPT 模版映射配置
# ════════════════════════════════════════════════════════════════

# 项目 public/ppts 目录路径
_PPT_TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "public", "ppts")
_TEMPLATE_MAPPING_FILE = os.path.join(_PPT_TEMPLATES_DIR, "template_mapping.json")

# 加载模版映射配置
_template_config = {}
try:
    if os.path.exists(_TEMPLATE_MAPPING_FILE):
        with open(_TEMPLATE_MAPPING_FILE, "r", encoding="utf-8") as f:
            _template_config = json.load(f)
except Exception:
    pass

# 模版 ID → 文件名映射
TEMPLATE_ID_MAP = {}
TEMPLATE_LIST = []
for _t in _template_config.get("templates", []):
    TEMPLATE_ID_MAP[_t["id"]] = _t["file"]
    TEMPLATE_LIST.append({
        "id": _t["id"],
        "name": _t["name"],
        "description": _t["description"],
        "subjects": _t.get("subjects", []),
        "preview": _t.get("preview", ""),
    })

# 学科 → 模版 ID 映射
SUBJECT_TEMPLATE_MAP = _template_config.get("subjectTemplateMap", {})
DEFAULT_TEMPLATE_ID = _template_config.get("defaultTemplate", "first_class")

# 确保模版文件存在
def _get_template_path(template_id):
    """获取模版文件的完整路径，不存在则返回 None"""
    filename = TEMPLATE_ID_MAP.get(template_id)
    if not filename:
        return None
    path = os.path.join(_PPT_TEMPLATES_DIR, filename)
    return path if os.path.exists(path) else None


def get_template_list():
    """返回可用模版列表（供 API 使用）"""
    available = []
    for t in TEMPLATE_LIST:
        if _get_template_path(t["id"]):
            available.append(t)
    return available


def pick_template(subject="", template_id=""):
    """根据学科或显式指定选择模版 ID"""
    # 显式指定优先
    if template_id and template_id in TEMPLATE_ID_MAP and _get_template_path(template_id):
        return template_id
    # 根据学科自动匹配
    if subject:
        for keyword, tid in SUBJECT_TEMPLATE_MAP.items():
            if keyword in subject:
                if _get_template_path(tid):
                    return tid
    # 返回默认模版
    if _get_template_path(DEFAULT_TEMPLATE_ID):
        return DEFAULT_TEMPLATE_ID
    # 兜底：返回第一个可用模版
    for t in TEMPLATE_LIST:
        if _get_template_path(t["id"]):
            return t["id"]
    return None

# ════════════════════════════════════════════════════════════════
# 多模板配色方案
# ════════════════════════════════════════════════════════════════

THEMES = {
    "blue": {
        "name": "深海蓝",
        "primary": RGBColor(0x1A, 0x36, 0x5D),      # 藏蓝
        "secondary": RGBColor(0x2B, 0x6C, 0xB0),     # 中蓝
        "accent": RGBColor(0x0E, 0xA5, 0xE9),        # 天蓝
        "accent_light": RGBColor(0xE0, 0xF2, 0xFE),   # 浅蓝底
        "bg": RGBColor(0xF8, 0xFA, 0xFC),            # 浅灰
        "text": RGBColor(0x1E, 0x29, 0x3B),          # 深灰
        "text_light": RGBColor(0x94, 0xA3, 0xB8),    # 浅灰字
        "white": RGBColor(0xFF, 0xFF, 0xFF),
        "dark_bg": RGBColor(0x0F, 0x20, 0x3A),       # 深色背景
        "card_bg": RGBColor(0xF1, 0xF5, 0xF9),
        "divider": RGBColor(0xE2, 0xE8, 0xF0),
    },
    "green": {
        "name": "青松绿",
        "primary": RGBColor(0x14, 0x52, 0x2D),
        "secondary": RGBColor(0x16, 0xA3, 0x4A),
        "accent": RGBColor(0x34, 0xD3, 0x99),
        "accent_light": RGBColor(0xD1, 0xFA, 0xE5),
        "bg": RGBColor(0xF8, 0xFA, 0xFC),
        "text": RGBColor(0x1E, 0x29, 0x3B),
        "text_light": RGBColor(0x94, 0xA3, 0xB8),
        "white": RGBColor(0xFF, 0xFF, 0xFF),
        "dark_bg": RGBColor(0x0A, 0x2E, 0x1A),
        "card_bg": RGBColor(0xF1, 0xF5, 0xF9),
        "divider": RGBColor(0xE2, 0xE8, 0xF0),
    },
    "warm": {
        "name": "暖阳橙",
        "primary": RGBColor(0x7C, 0x2D, 0x12),
        "secondary": RGBColor(0xC2, 0x41, 0x0C),
        "accent": RGBColor(0xF5, 0x9E, 0x0B),
        "accent_light": RGBColor(0xFE, 0xF3, 0xC7),
        "bg": RGBColor(0xFC, 0xFB, 0xF8),
        "text": RGBColor(0x1E, 0x29, 0x3B),
        "text_light": RGBColor(0xA8, 0xA2, 0x9E),
        "white": RGBColor(0xFF, 0xFF, 0xFF),
        "dark_bg": RGBColor(0x45, 0x1A, 0x0A),
        "card_bg": RGBColor(0xF5, 0xF0, 0xEB),
        "divider": RGBColor(0xE7, 0xE0, 0xDA),
    },
    "violet": {
        "name": "紫罗兰",
        "primary": RGBColor(0x4C, 0x1D, 0x95),
        "secondary": RGBColor(0x7C, 0x3A, 0xED),
        "accent": RGBColor(0xA7, 0x8B, 0xFA),
        "accent_light": RGBColor(0xED, 0xE9, 0xFE),
        "bg": RGBColor(0xF8, 0xFA, 0xFC),
        "text": RGBColor(0x1E, 0x29, 0x3B),
        "text_light": RGBColor(0x94, 0xA3, 0xB8),
        "white": RGBColor(0xFF, 0xFF, 0xFF),
        "dark_bg": RGBColor(0x2E, 0x10, 0x65),
        "card_bg": RGBColor(0xF5, 0xF3, 0xFF),
        "divider": RGBColor(0xE2, 0xE8, 0xF0),
    },
    "teal": {
        "name": "湖水青",
        "primary": RGBColor(0x13, 0x49, 0x4A),
        "secondary": RGBColor(0x0D, 0x94, 0x88),
        "accent": RGBColor(0x5E, 0xEA, 0xD4),
        "accent_light": RGBColor(0xCC, 0xFB, 0xF1),
        "bg": RGBColor(0xF8, 0xFA, 0xFC),
        "text": RGBColor(0x1E, 0x29, 0x3B),
        "text_light": RGBColor(0x94, 0xA3, 0xB8),
        "white": RGBColor(0xFF, 0xFF, 0xFF),
        "dark_bg": RGBColor(0x0C, 0x2D, 0x2E),
        "card_bg": RGBColor(0xF0, 0xFD, 0xFA),
        "divider": RGBColor(0xE2, 0xE8, 0xF0),
    },
}

# 自动根据学科匹配主题
SUBJECT_THEME_MAP = {
    "物理": "blue", "化学": "blue", "数学": "blue", "科学": "blue",
    "生物": "green", "地理": "teal", "自然": "green",
    "语文": "warm", "历史": "warm", "政治": "warm", "道德": "warm", "社会": "warm",
    "英语": "violet", "美术": "violet", "音乐": "violet", "艺术": "violet",
}
DEFAULT_THEME = "blue"


def _pick_theme(subject: str = "", style: str = "") -> dict:
    """根据学科自动选择配色主题"""
    if not subject:
        return THEMES[DEFAULT_THEME]
    for keyword, theme_name in SUBJECT_THEME_MAP.items():
        if keyword in subject:
            return THEMES.get(theme_name, THEMES[DEFAULT_THEME])
    return THEMES[DEFAULT_THEME]


# ════════════════════════════════════════════════════════════════
# PPTX 工具函数
# ════════════════════════════════════════════════════════════════

def _set_slide_bg(slide, color: RGBColor):
    """设置幻灯片纯色背景"""
    background = slide.background
    fill = background.fill
    fill.solid()
    fill.fore_color.rgb = color


def _add_text_box(slide, left, top, width, height, text, font_size=18,
                  bold=False, color=None, alignment=PP_ALIGN.LEFT,
                  font_name=None, line_spacing=None):
    """在幻灯片上添加文本框"""
    txBox = slide.shapes.add_textbox(
        Inches(left), Inches(top), Inches(width), Inches(height)
    )
    tf = txBox.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = text
    p.font.size = Pt(font_size)
    p.font.bold = bold
    p.font.color.rgb = color or THEMES[DEFAULT_THEME]["text"]
    p.alignment = alignment
    if font_name:
        p.font.name = font_name
    if line_spacing:
        p.line_spacing = Pt(line_spacing)
    return txBox


def _add_bullet_list(slide, left, top, width, height, items,
                     font_size=16, color=None, bullet_char="▸", line_spacing=1.4):
    """添加带符号的要点列表"""
    txBox = slide.shapes.add_textbox(
        Inches(left), Inches(top), Inches(width), Inches(height)
    )
    tf = txBox.text_frame
    tf.word_wrap = True

    bullet_color = color or THEMES[DEFAULT_THEME]["text"]
    for i, item in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = f"{bullet_char}  {item}"
        p.font.size = Pt(font_size)
        p.font.color.rgb = bullet_color
        p.space_after = Pt(font_size * 0.4)
        if line_spacing:
            p.line_spacing = Pt(font_size * line_spacing)
    return txBox


def _add_accent_bar(slide, theme, top=0, height=0.08):
    """在幻灯片顶部添加装饰条"""
    bar = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE,
        Inches(0), Inches(top), Inches(13.333), Inches(height)
    )
    bar.fill.solid()
    bar.fill.fore_color.rgb = theme["secondary"]
    bar.line.fill.background()
    return bar


def _add_page_number(slide, page_num, total, theme):
    """添加页码"""
    _add_text_box(
        slide, 11.5, 7.0, 1.5, 0.4,
        f"{page_num} / {total}",
        font_size=9, color=theme["text_light"],
        alignment=PP_ALIGN.RIGHT
    )


def _add_decorative_shape(slide, left, top, width, height, color, shape_type=MSO_SHAPE.RECTANGLE):
    """添加装饰形状"""
    shape = slide.shapes.add_shape(
        shape_type, Inches(left), Inches(top), Inches(width), Inches(height)
    )
    shape.fill.solid()
    shape.fill.fore_color.rgb = color
    shape.line.fill.background()
    return shape


# ════════════════════════════════════════════════════════════════
# PPTX 幻灯片布局
# ════════════════════════════════════════════════════════════════

def _make_title_slide(slide, slide_data, theme, page_num, total):
    """封面页 - 全幅深色背景 + 装饰几何元素 + 居中大标题"""
    title = slide_data.get("title", "")
    content = slide_data.get("content", [])
    subtitle = "\n".join(content) if isinstance(content, list) else str(content) if content else ""

    # 深色背景
    _set_slide_bg(slide, theme["dark_bg"])

    # 装饰元素：右上角大圆
    _add_decorative_shape(
        slide, 9.5, -1.2, 5.5, 5.5,
        RGBColor(
            min(theme["secondary"][0] + 30, 255),
            min(theme["secondary"][1] + 30, 255),
            min(theme["secondary"][2] + 30, 255)
        ),
        MSO_SHAPE.OVAL
    )
    # 装饰元素：左下角小圆
    _add_decorative_shape(
        slide, -1.0, 5.5, 3.0, 3.0,
        theme["secondary"],
        MSO_SHAPE.OVAL
    )

    # 顶部细装饰线
    _add_accent_bar(slide, theme, top=0, height=0.04)

    # 主标题区域 - 大号居中
    _add_text_box(
        slide, 1.5, 1.8, 10.3, 1.8, title,
        font_size=44, bold=True, color=theme["white"],
        alignment=PP_ALIGN.CENTER
    )

    # 副标题
    if subtitle:
        _add_text_box(
            slide, 1.5, 3.8, 10.3, 1.2, subtitle,
            font_size=20, color=theme["accent"],
            alignment=PP_ALIGN.CENTER
        )

    # 底部装饰线 + 学科标签
    _add_text_box(
        slide, 4.5, 5.5, 4.3, 0.3,
        "━" * 26,
        font_size=12, color=theme["accent"],
        alignment=PP_ALIGN.CENTER
    )

    # 页码
    _add_page_number(slide, page_num, total, theme)


def _make_content_slide(slide, slide_data, theme, page_num, total):
    """标准内容页 - 顶部色条 + 标题 + 要点列表 + 页码"""
    slide_title = slide_data.get("title", "")
    slide_content = slide_data.get("content", [])

    # 浅色背景
    _set_slide_bg(slide, theme["bg"])

    # 顶部粗装饰条
    _add_accent_bar(slide, theme, top=0, height=0.06)

    # 左侧色块装饰
    _add_decorative_shape(
        slide, 0, 0.06, 0.12, 1.2, theme["secondary"]
    )

    # 标题 - 带底部细线
    _add_text_box(
        slide, 0.8, 0.3, 11.7, 0.7, slide_title,
        font_size=28, bold=True, color=theme["primary"]
    )
    # 标题下划线
    _add_decorative_shape(
        slide, 0.8, 1.05, 2.5, 0.04, theme["accent"]
    )

    # 要点内容
    if slide_content:
        _add_bullet_list(
            slide, 1.0, 1.5, 11.5, 5.0,
            slide_content,
            font_size=18, color=theme["text"],
            bullet_char="▸"
        )

    # 页码
    _add_page_number(slide, page_num, total, theme)


def _make_comparison_slide(slide, slide_data, theme, page_num, total):
    """对比布局页 - 左右分栏 + 中间分隔"""
    slide_title = slide_data.get("title", "")
    slide_content = slide_data.get("content", [])

    _set_slide_bg(slide, theme["bg"])
    _add_accent_bar(slide, theme, top=0, height=0.06)
    _add_decorative_shape(slide, 0, 0.06, 0.12, 1.2, theme["secondary"])

    _add_text_box(
        slide, 0.8, 0.3, 11.7, 0.7, slide_title,
        font_size=28, bold=True, color=theme["primary"]
    )
    _add_decorative_shape(slide, 0.8, 1.05, 2.5, 0.04, theme["accent"])

    if len(slide_content) >= 2:
        mid = len(slide_content) // 2
        left_items = slide_content[:mid]
        right_items = slide_content[mid:]

        # 左侧卡片背景
        _add_decorative_shape(
            slide, 0.8, 1.5, 5.5, 5.0, theme["card_bg"]
        )
        # 右侧卡片背景
        _add_decorative_shape(
            slide, 7.0, 1.5, 5.5, 5.0, theme["card_bg"]
        )

        _add_bullet_list(slide, 1.0, 1.6, 5.0, 4.8, left_items,
                         font_size=15, color=theme["text"])
        _add_bullet_list(slide, 7.2, 1.6, 5.0, 4.8, right_items,
                         font_size=15, color=theme["text"])

    _add_page_number(slide, page_num, total, theme)


def _make_summary_slide(slide, slide_data, theme, page_num, total):
    """总结页 - 浅色背景 + 居中标题 + 要点"""
    slide_title = slide_data.get("title", "")
    slide_content = slide_data.get("content", [])

    _set_slide_bg(slide, theme["accent_light"])

    # 装饰顶条
    _add_accent_bar(slide, theme, top=0, height=0.06)

    _add_text_box(
        slide, 1.0, 0.5, 11.3, 0.8, slide_title,
        font_size=30, bold=True, color=theme["primary"],
        alignment=PP_ALIGN.CENTER
    )

    # 标题下装饰线
    _add_text_box(
        slide, 5.0, 1.3, 3.3, 0.2,
        "━" * 18,
        font_size=12, color=theme["accent"],
        alignment=PP_ALIGN.CENTER
    )

    if slide_content:
        _add_bullet_list(
            slide, 2.5, 1.8, 8.3, 4.5, slide_content,
            font_size=20, color=theme["text"],
            bullet_char="✦"
        )

    _add_page_number(slide, page_num, total, theme)


def _make_section_slide(slide, slide_data, theme, page_num, total):
    """章节分隔页 - 深色横条 + 大章节号"""
    slide_title = slide_data.get("title", "")

    _set_slide_bg(slide, theme["bg"])

    # 全宽色条
    _add_decorative_shape(
        slide, 0, 2.5, 13.333, 2.5, theme["primary"]
    )

    # 章节标题
    _add_text_box(
        slide, 1.0, 2.8, 11.3, 1.5, slide_title,
        font_size=36, bold=True, color=theme["white"],
        alignment=PP_ALIGN.CENTER
    )

    _add_page_number(slide, page_num, total, theme)


# 布局分发映射
SLIDE_BUILDERS = {
    "title": _make_title_slide,
    "content": _make_content_slide,
    "comparison": _make_comparison_slide,
    "summary": _make_summary_slide,
    "section": _make_section_slide,
}


# ════════════════════════════════════════════════════════════════
# PPTX 生成主函数
# ════════════════════════════════════════════════════════════════

def _remove_all_slides(prs):
    """移除 Presentation 中的所有幻灯片，保留母版/主题"""
    xml_slides = prs.slides._sldIdLst
    slides_to_remove = list(xml_slides)
    for sld_id_elem in slides_to_remove:
        rId = sld_id_elem.get(
            '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id'
        )
        if rId:
            try:
                prs.part.drop_rel(rId)
            except Exception:
                pass
        xml_slides.remove(sld_id_elem)


def generate_pptx_from_template(content: dict, template_id: str = "") -> tuple:
    """
    基于 public/ppts 目录下的预置 PPTX 模版生成课件。
    打开模版文件，移除原有幻灯片，保留模版的主题/母版设计，
    然后用 AI 生成的内容重新填充幻灯片。
    
    Args:
        content: AI 生成的课件内容
        template_id: 模版 ID（如 spring/first_class/chinese_style 等），
                     为空时自动根据学科匹配
    
    Returns:
        (filepath, filename) 元组
    """
    subject = content.get("subject", "")
    tid = pick_template(subject, template_id)
    template_path = _get_template_path(tid)
    
    if not template_path:
        # 模版不可用，回退到内置主题生成
        print(f"[PPT] 模版 '{tid}' 不可用，回退到内置主题生成")
        return generate_pptx(content)
    
    template_name = TEMPLATE_ID_MAP.get(tid, tid)
    print(f"[PPT] 使用模版: {template_name} → {template_path}")
    
    # 打开模版文件
    prs = Presentation(template_path)
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    
    # 移除模版中原有的幻灯片，保留主题/母版设计
    _remove_all_slides(prs)
    
    # 从内容生成新幻灯片（使用模版的主题）
    style = content.get("style", "")
    theme = _pick_theme(subject, style)
    slides_data = content.get("slides", [])
    total = len(slides_data)
    
    # 尝试使用模版的空白布局（默认第 7 个，索引 6）
    try:
        blank_layout = prs.slide_layouts[6]
    except IndexError:
        blank_layout = prs.slide_layouts[0]
    
    for idx, slide_data in enumerate(slides_data):
        slide_type = slide_data.get("type", "content")
        slide_notes = slide_data.get("notes", "")
        
        slide = prs.slides.add_slide(blank_layout)
        
        builder = SLIDE_BUILDERS.get(slide_type, _make_content_slide)
        builder(slide, slide_data, theme, idx + 1, total)
        
        if slide_notes:
            try:
                notes_slide = slide.notes_slide
                notes_slide.notes_text_frame.text = slide_notes
            except Exception:
                pass
    
    # 保存
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    safe_title = re.sub(r'[<>:"/\\|?*]', '_', content.get('title', '课件'))
    filename = f"{safe_title}.pptx"
    filepath = os.path.join(OUTPUT_DIR, filename)
    prs.save(filepath)
    
    tmpl_info = next((t for t in TEMPLATE_LIST if t["id"] == tid), None)
    tmpl_display = tmpl_info["name"] if tmpl_info else template_name
    print(f"[PPT] 模版「{tmpl_display}」+ 主题「{theme['name']}」→ {filepath}")
    return filepath, filename


def generate_pptx(content: dict) -> tuple:
    """根据 AI 生成的内容创建 PPTX 文件，自动匹配学科主题"""
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)

    subject = content.get("subject", "")
    style = content.get("style", "")
    theme = _pick_theme(subject, style)
    slides_data = content.get("slides", [])
    total = len(slides_data)

    for idx, slide_data in enumerate(slides_data):
        slide_type = slide_data.get("type", "content")
        slide_notes = slide_data.get("notes", "")

        # 使用空白布局
        slide = prs.slides.add_slide(prs.slide_layouts[6])

        # 调用对应的布局构建器
        builder = SLIDE_BUILDERS.get(slide_type, _make_content_slide)
        builder(slide, slide_data, theme, idx + 1, total)

        # 备注
        if slide_notes:
            try:
                notes_slide = slide.notes_slide
                notes_slide.notes_text_frame.text = slide_notes
            except Exception:
                pass

    # 保存
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    safe_title = re.sub(r'[<>:"/\\|?*]', '_', content.get('title', '课件'))
    filename = f"{safe_title}.pptx"
    filepath = os.path.join(OUTPUT_DIR, filename)
    prs.save(filepath)
    print(f"[PPT] 使用主题: {theme['name']} → {filepath}")
    return filepath, filename


# ════════════════════════════════════════════════════════════════
# DOCX 生成 - 结构化教案
# ════════════════════════════════════════════════════════════════

# 教案标准配色（专业沉稳）
_DOC_PRIMARY   = "1A365D"   # 深蓝 —— 一级标题、主题色
_DOC_SECONDARY = "2B6CB0"   # 中蓝 —— 二级标题 / 目标维度强调
_DOC_ACCENT    = "0E7490"   # 重点强调色
_DOC_LIGHT_BG  = "EAF2FB"   # 一级标题浅色色块
_DOC_TABLE_BG  = "F1F5F9"   # 基本信息表标签底色
_DOC_BODY      = "334155"   # 正文深灰
_DOC_MUTED     = "64748B"   # 次要说明文字

# 匹配「知识与技能 / 过程与方法 / 情感态度（与价值观）」等目标维度前缀
_MATCH_GOAL_DIMENSION = re.compile(
    r'^\s*(?:\d+[\.、]\s*)?(知识与技能|过程与方法|情感态度与价值观|情感态度价值观|情感态度)'
)

def _set_cn_font(run, size=11, bold=False, italic=False, color=_DOC_BODY, name="Microsoft YaHei"):
    """统一设置 run 的字体（含中文字体 eastAsia），保证中文渲染一致。"""
    run.font.size = DocxPt(size)
    run.font.bold = bold
    run.font.italic = italic
    run.font.color.rgb = DocxRGB.from_string(color)
    run.font.name = name
    run._element.get_or_add_rPr().rFonts.set(qn('w:eastAsia'), name)


def _shade_paragraph(p, fill=_DOC_LIGHT_BG):
    """为段落添加背景色块（色块标注效果）。"""
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), fill)
    p._p.get_or_add_pPr().append(shd)


def _left_bar(p, color=_DOC_PRIMARY, sz=30):
    """为段落添加左侧粗竖条（重点强调效果）。"""
    pPr = p._p.get_or_add_pPr()
    pbdr = OxmlElement('w:pBdr')
    left = OxmlElement('w:left')
    left.set(qn('w:val'), 'single')
    left.set(qn('w:sz'), str(sz))
    left.set(qn('w:space'), '4')
    left.set(qn('w:color'), color)
    pbdr.append(left)
    pPr.append(pbdr)


def _add_heading(doc, text, level=1):
    """添加统一层级样式标题：一级=深蓝色块+左竖条，二级=◆中蓝加粗，三级=重点加大。"""
    p = doc.add_paragraph()
    pf = p.paragraph_format
    if level <= 1:
        pf.space_before = DocxPt(16)
        pf.space_after = DocxPt(8)
        pf.left_indent = Cm(0.1)
        _shade_paragraph(p, _DOC_LIGHT_BG)
        _left_bar(p, _DOC_PRIMARY, 30)
        _set_cn_font(p.add_run("    " + text), size=16, bold=True, color=_DOC_PRIMARY, name="黑体")
    elif level == 2:
        pf.space_before = DocxPt(10)
        pf.space_after = DocxPt(6)
        pf.left_indent = Cm(0.5)
        _set_cn_font(p.add_run("◆ " + text), size=14, bold=True, color=_DOC_SECONDARY, name="微软雅黑")
    else:
        pf.space_before = DocxPt(6)
        pf.space_after = DocxPt(4)
        pf.left_indent = Cm(0.8)
        _set_cn_font(p.add_run(text), size=12, bold=True, color=_DOC_ACCENT)
    return p


def _fill_info_cell(cell, text, is_label):
    """填充基本信息表单元格：标签单元格浅灰底 + 深蓝加粗，值单元格居中。"""
    p = cell.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT if is_label else WD_ALIGN_PARAGRAPH.CENTER
    pf = p.paragraph_format
    pf.space_before = DocxPt(2)
    pf.space_after = DocxPt(2)
    if is_label:
        _shade_paragraph(p, _DOC_TABLE_BG)
        _set_cn_font(p.add_run(text), size=11, bold=True, color=_DOC_PRIMARY)
    else:
        _set_cn_font(p.add_run(text or "—"), size=11, color=_DOC_BODY)
    cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER


def _add_info_table(doc, items):
    """生成「课程基本信息」区域：2×N 的规范边框表格，标签/值交错排列。"""
    table = doc.add_table(rows=0, cols=4)
    table.style = 'Table Grid'
    table.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for start in range(0, len(items), 2):
        row = table.add_row()
        for gi, (label, value) in enumerate(items[start:start + 2]):
            li = gi * 2
            _fill_info_cell(row.cells[li], label, True)
            _fill_info_cell(row.cells[li + 1], value, False)
    # 设定列宽
    widths = [Cm(2.4), Cm(4.6), Cm(2.4), Cm(4.6)]
    for r in table.rows:
        for ci, w in enumerate(widths):
            r.cells[ci].width = w
    return table


def generate_docx(content: dict) -> tuple:
    """生成美观、结构规范的教案 DOCX 文件（三层次标题 + 专业排版样式）"""
    doc = Document()

    # 页面设置
    section = doc.sections[0]
    section.top_margin = Cm(2.4)
    section.bottom_margin = Cm(2.4)
    section.left_margin = Cm(2.6)
    section.right_margin = Cm(2.6)

    # 默认正文样式
    normal = doc.styles['Normal']
    normal.font.name = 'Microsoft YaHei'
    normal.font.size = DocxPt(11)
    normal.paragraph_format.line_spacing = 1.5
    normal.paragraph_format.space_after = DocxPt(4)
    normal.element.rPr.rFonts.set(qn('w:eastAsia'), 'Microsoft YaHei')

    # ── ① 标题区 ──
    title_text = content.get("title", "教案")
    title_para = doc.add_paragraph()
    title_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title_para.paragraph_format.space_before = DocxPt(12)
    title_para.paragraph_format.space_after = DocxPt(6)
    _set_cn_font(title_para.add_run(title_text), size=26, bold=True, color=_DOC_PRIMARY, name="黑体")

    # 子题（学科 · 年级）
    subtitle = " · ".join(x for x in [content.get("subject", ""), content.get("grade", "")] if x)
    if subtitle:
        sub_para = doc.add_paragraph()
        sub_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        sub_para.paragraph_format.space_after = DocxPt(6)
        _set_cn_font(sub_para.add_run(subtitle), size=13, color=_DOC_MUTED)

    # 装饰分割线
    div_para = doc.add_paragraph()
    div_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    div_para.paragraph_format.space_after = DocxPt(12)
    _set_cn_font(div_para.add_run("─" * 46), size=10, color="CBD5E1")

    # ── ② 课程基本信息表 ──
    info_items = [
        ("学科", content.get("subject", "")),
        ("年级", content.get("grade", "")),
        ("课时", content.get("duration", "1课时")),
        ("教学风格", content.get("style", "—")),
    ]
    _add_info_table(doc, info_items)
    doc.add_paragraph(style='Normal')

    # ── ③ 教学目标 ──
    teaching_goals = content.get("teachingGoals", "")
    if teaching_goals:
        _add_heading(doc, "教学目标", level=1)
        goal_list = [g.strip() for g in teaching_goals.replace("；", ";").split(";") if g.strip()]
        for g in goal_list:
            # 识别并加粗「知识与技能/过程与方法/情感态度」等目标维度前缀
            dim = _MATCH_GOAL_DIMENSION.match(g)
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Cm(0.8)
            p.paragraph_format.space_after = DocxPt(4)
            _set_cn_font(p.add_run("✦ "), size=11, bold=True, color=_DOC_ACCENT)
            if dim:
                _set_cn_font(p.add_run(dim.group(1)), size=11, bold=True, color=_DOC_SECONDARY)
                _set_cn_font(p.add_run(g[dim.end():]), size=11, color=_DOC_BODY)
            else:
                _set_cn_font(p.add_run(g), size=11, color=_DOC_BODY)

    # ── ④ 教学重难点分析 ──
    key_points = content.get("keyPoints", "")
    if key_points:
        _add_heading(doc, "教学重难点分析", level=1)
        pts = [t.strip() for t in key_points.replace("；", ";").split(";") if t.strip()]
        for i, pt in enumerate(pts, 1):
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Cm(0.8)
            p.paragraph_format.space_after = DocxPt(4)
            _set_cn_font(p.add_run(f"{i}. "), size=11, bold=True, color=_DOC_ACCENT)
            _set_cn_font(p.add_run(pt), size=11, color=_DOC_BODY)

    # ── ⑤ 教学过程设计 ──
    sections = content.get("sections", [])
    if sections:
        _add_heading(doc, "教学过程设计", level=1)
        for i, section_item in enumerate(sections, 1):
            heading = section_item.get("heading", f"环节 {i}")
            _add_heading(doc, heading, level=2)
            for item in section_item.get("content", []):
                p = doc.add_paragraph()
                p.paragraph_format.left_indent = Cm(1.2)
                p.paragraph_format.space_after = DocxPt(3)
                _set_cn_font(p.add_run("▸ "), size=11, color="94A3B8")
                _set_cn_font(p.add_run(item), size=11, color=_DOC_BODY)

    # ── ⑥ 教学反思 ──
    _add_heading(doc, "教学反思", level=1)
    note_p = doc.add_paragraph()
    note_p.paragraph_format.left_indent = Cm(0.8)
    note_p.paragraph_format.space_after = DocxPt(6)
    _set_cn_font(
        note_p.add_run("（此部分建议课后填写，围绕目标达成、互动效果与改进方向进行反思）"),
        size=10, italic=True, color="94A3B8",
    )
    for tip in ["本节课教学目标的达成情况：", "学生参与度与互动效果：", "需要改进或调整的环节："]:
        p = doc.add_paragraph()
        p.paragraph_format.left_indent = Cm(1.0)
        p.paragraph_format.space_after = DocxPt(2)
        _set_cn_font(p.add_run(tip), size=11, color=_DOC_MUTED)

    # 保存
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    safe_title = re.sub(r'[<>:"/\\|?*]', '_', content.get('title', '教案'))
    filename = f"{safe_title}.docx"
    filepath = os.path.join(OUTPUT_DIR, filename)
    doc.save(filepath)
    print(f"[DOC] 已生成: {filepath}")
    return filepath, filename


# ════════════════════════════════════════════════════════════════
# HTML 题目生成 - 强化样式
# ════════════════════════════════════════════════════════════════

def generate_quiz_html(content: dict) -> tuple:
    """生成精美教学题 HTML 页面"""
    title = content.get('title', '练习题')
    question_count = len(content.get('questions', []))

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: system-ui, "PingFang SC", "Microsoft YaHei", sans-serif;
    max-width: 860px;
    margin: 0 auto;
    padding: 48px 24px;
    color: #1E293B;
    background: #F7F5F2;
  }}
  .header {{
    text-align: center;
    margin-bottom: 48px;
    padding-bottom: 32px;
    border-bottom: 2px solid #E2E8F0;
  }}
  .header h1 {{
    font-size: 2rem;
    font-weight: 800;
    color: #1A365D;
    letter-spacing: -0.02em;
    margin-bottom: 8px;
  }}
  .header .meta {{
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 16px;
    color: #64748B;
    font-size: 0.9rem;
  }}
  .header .count {{
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 4px 12px;
    background: #F1F5F9;
    border-radius: 20px;
    font-weight: 600;
    font-size: 0.85rem;
  }}
  .question {{
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 12px;
    padding: 24px 28px;
    margin-bottom: 20px;
    box-shadow: 0 1px 2px rgba(0,0,0,0.04);
    transition: box-shadow 0.2s;
  }}
  .question:hover {{
    box-shadow: 0 4px 12px rgba(0,0,0,0.06);
  }}
  .q-header {{
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 16px;
  }}
  .q-num {{
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 32px;
    height: 32px;
    background: #2B6CB0;
    color: #FFF;
    border-radius: 8px;
    font-size: 0.85rem;
    font-weight: 700;
    flex-shrink: 0;
  }}
  .q-type {{
    padding: 3px 10px;
    border-radius: 6px;
    font-size: 0.75rem;
    font-weight: 700;
    letter-spacing: 0.02em;
  }}
  .q-type.choice {{ background: #DBEAFE; color: #1E40AF; }}
  .q-type.fill   {{ background: #D1FAE5; color: #065F46; }}
  .q-type.essay  {{ background: #EDE9FE; color: #5B21B6; }}
  .q-text {{
    font-size: 1rem;
    font-weight: 600;
    line-height: 1.7;
    margin-bottom: 12px;
    color: #1E293B;
  }}
  .options {{
    margin: 8px 0 16px 20px;
  }}
  .options p {{
    padding: 6px 0;
    font-size: 0.95rem;
    color: #475569;
  }}
  .answer-area {{
    margin-top: 16px;
  }}
  .show-btn {{
    padding: 6px 16px;
    background: #2B6CB0;
    color: #FFF;
    border: none;
    border-radius: 6px;
    cursor: pointer;
    font-size: 0.8rem;
    font-weight: 600;
    transition: background 0.2s;
  }}
  .show-btn:hover {{ background: #1E4F82; }}
  .answer-box {{
    display: none;
    margin-top: 12px;
    padding: 14px 18px;
    background: #F0FDF4;
    border-radius: 10px;
    border-left: 3px solid #10B981;
  }}
  .answer-box strong {{
    color: #065F46;
    font-size: 0.9rem;
  }}
  .answer-box .analysis {{
    margin-top: 6px;
    color: #64748B;
    font-size: 0.85rem;
    line-height: 1.6;
  }}
  .footer {{
    text-align: center;
    margin-top: 48px;
    padding-top: 24px;
    border-top: 1px solid #E2E8F0;
    color: #94A3B8;
    font-size: 0.8rem;
  }}
  @media print {{
    body {{ background: #FFF; }}
    .question {{ box-shadow: none; border: 1px solid #E2E8F0; page-break-inside: avoid; }}
    .show-btn {{ display: none; }}
    .answer-box {{ display: block !important; }}
  }}
</style>
</head>
<body>
<div class="header">
  <h1>{title}</h1>
  <div class="meta">
    <span class="count">共 {question_count} 题</span>
  </div>
</div>
"""

    for i, q in enumerate(content.get("questions", []), 1):
        q_type_key = q.get("type", "choice")
        q_type_cn = {"choice": "选择题", "fill": "填空题", "essay": "简答题"}.get(q_type_key, "其他")
        q_type_class = {"choice": "choice", "fill": "fill", "essay": "essay"}.get(q_type_key, "choice")

        html += f'''<div class="question">
  <div class="q-header">
    <span class="q-num">{i}</span>
    <span class="q-type {q_type_class}">{q_type_cn}</span>
  </div>
  <div class="q-text">{q["question"]}</div>
'''

        if q.get("options"):
            html += '  <div class="options">\n'
            for opt in q["options"]:
                html += f'    <p>{opt}</p>\n'
            html += '  </div>\n'

        html += f'''  <div class="answer-area">
    <button class="show-btn" onclick="var box=this.nextElementSibling;box.style.display='block';this.style.display='none'">显示答案</button>
    <div class="answer-box">
      <strong>答案：{q["answer"]}</strong>
      <div class="analysis">解析：{q.get("analysis", "暂无解析")}</div>
    </div>
  </div>
</div>
'''

    html += '''<div class="footer">
  <p>知启灵枢 · AI 智能出题 · 仅供教学参考</p>
</div>
</body></html>'''

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    safe_title = re.sub(r'[<>:"/\\|?*]', '_', title)
    filename = f"{safe_title}.html"
    filepath = os.path.join(OUTPUT_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[HTML] 已生成: {filepath}")
    return filepath, filename


def generate_exam_html(content: dict) -> tuple:
    """生成试卷 HTML 页面，含选择题/填空题/解答题"""
    title = content.get("title", "综合试卷")
    subject = content.get("subject", "")
    grade = content.get("grade", "")
    total = content.get("total_score", 100)
    duration = content.get("duration", "90分钟")
    sections = content.get("sections", [])
    answer_key = content.get("answer_key", "")

    # 计算总题数
    total_questions = sum(s.get("count", 0) for s in sections)

    sections_html = ""
    section_letters = "一二三四五六七八九十"
    for si, sec in enumerate(sections):
        stype = sec.get("type", "选择题")
        count = sec.get("count", 0)
        score_per = sec.get("score_per", 0)
        subtotal = sec.get("subtotal", count * score_per)
        questions = sec.get("questions", [])

        q_html = ""
        for qi, q in enumerate(questions, 1):
            q_content = q.get("content", "")
            q_options = q.get("options", [])
            q_diff = q.get("difficulty", "")

            opts_html = ""
            for opt in q_options:
                opts_html += f'<p style="margin:4px 0 4px 20px">{opt}</p>'

            q_html += f'''<div class="question-item">
  <div class="q-row">
    <span class="q-num">{qi}.</span>
    <span class="q-text">{q_content}</span>
    {f'<span class="q-blank"></span>' if stype == "填空题" and not q_options else ''}
    {f'<span class="q-diff {q_diff}">{"⚪" if q_diff == "基础" else "🔵" if q_diff == "中等" else "🔴"}</span>' if q_diff else ''}
  </div>
  {f'<div class="q-opts">{opts_html}</div>' if opts_html else ''}
</div>'''

        sections_html += f'''<div class="section">
  <div class="section-header">
    <span class="section-title">{section_letters[si] if si < len(section_letters) else si + 1}、{stype}</span>
    <span class="section-meta">共 {count} 题 · 每题 {score_per} 分 · 小计 {subtotal} 分</span>
  </div>
  <div class="section-body">
    {q_html}
  </div>
</div>'''

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: "PingFang SC", "Microsoft YaHei", system-ui, sans-serif;
    max-width: 900px;
    margin: 0 auto;
    padding: 40px 32px;
    color: #1E293B;
    background: #F7F5F2;
  }}
  .paper-header {{
    text-align: center;
    margin-bottom: 40px;
    padding-bottom: 28px;
    border-bottom: 3px double #CBD5E1;
  }}
  .paper-header h1 {{ font-size: 1.8rem; font-weight: 800; letter-spacing: 2px; color: #0F172A; }}
  .paper-header .meta {{ margin-top: 12px; display: flex; justify-content: center; gap: 32px; font-size: 0.9rem; color: #64748B; }}
  .paper-header .meta span {{ white-space: nowrap; }}
  .section {{
    margin-bottom: 36px;
    page-break-inside: avoid;
  }}
  .section-header {{
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    padding-bottom: 10px;
    margin-bottom: 16px;
    border-bottom: 2px solid #E2E8F0;
  }}
  .section-title {{ font-size: 1.1rem; font-weight: 700; color: #0F172A; }}
  .section-meta {{ font-size: 0.8rem; color: #6B7280; }}
  .question-item {{
    padding: 12px 0;
    border-bottom: 1px solid #F1F5F9;
  }}
  .question-item:last-child {{ border-bottom: none; }}
  .q-row {{ display: flex; align-items: flex-start; gap: 8px; line-height: 1.7; }}
  .q-num {{ font-weight: 600; color: #475569; min-width: 28px; }}
  .q-text {{ flex: 1; }}
  .q-blank {{
    display: inline-block;
    min-width: 80px;
    border-bottom: 2px solid #94A3B8;
    margin: 0 4px;
  }}
  .q-opts {{ margin-top: 4px; font-size: 0.9rem; color: #334155; }}
  .q-diff {{ margin-left: auto; font-size: 0.7rem; }}
  .answer-key {{
    margin-top: 48px;
    padding: 24px;
    background: #F8FAFC;
    border: 1px solid #E2E8F0;
    border-radius: 12px;
    white-space: pre-wrap;
    line-height: 1.8;
    font-size: 0.88rem;
    color: #1E293B;
  }}
  .answer-key h3 {{ font-size: 1rem; margin-bottom: 12px; }}
  @media print {{
    body {{ background: #FFF; padding: 20px; }}
    .question-item {{ page-break-inside: avoid; }}
    .section {{ page-break-inside: avoid; }}
  }}
  @media (max-width: 600px) {{
    body {{ padding: 16px; }}
    .paper-header .meta {{ flex-direction: column; gap: 4px; }}
    .section-header {{ flex-direction: column; gap: 4px; }}
  }}
</style>
</head>
<body>
<div class="paper-header">
  <h1>{title}</h1>
  <div class="meta">
    <span>学科：{subject}</span>
    <span>年级：{grade}</span>
    <span>总分：{total} 分</span>
    <span>时长：{duration}</span>
    <span>题量：共 {total_questions} 题</span>
  </div>
</div>

{sections_html}

{f'<div class="answer-key"><h3>📋 参考答案与评分标准</h3>{answer_key}</div>' if answer_key else ''}

<div style="text-align:center;margin-top:40px;padding-top:20px;border-top:1px solid #E2E8F0;color:#94A3B8;font-size:0.8rem;">
  <p>知启灵枢 · AI 智能组卷 · 仅供教学参考</p>
</div>
</body>
</html>"""

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    safe_title = re.sub(r'[<>:"/\\|?*]', '_', title)
    filename = f"{safe_title}.html"
    filepath = os.path.join(OUTPUT_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[HTML Exam] 已生成: {filepath}")
    return filepath, filename


# ════════════════════════════════════════════════════════════════
# Markdown 渲染 —— 右侧面板所见即导出所得
# ════════════════════════════════════════════════════════════════

def _strip_md_inline(text: str) -> str:
    """去除行内 Markdown 标记（加粗/斜体/行内代码），用于纯文本渲染。"""
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text or "")
    text = re.sub(r'(?<!\*)\*(?!\s)(.+?)(?<!\s)\*(?!\*)', r'\1', text)
    text = re.sub(r'`(.+?)`', r'\1', text)
    return text.strip()


def _parse_markdown_blocks(md: str) -> list:
    """把 Markdown 解析为渲染友好的块列表。

    支持：一级~六级标题、无序列表(-/*/+)、有序列表(1./1、)、普通段落。
    """
    blocks = []
    lines = (md or "").replace("\r\n", "\n").split("\n")
    i, n = 0, len(lines)
    while i < n:
        line = lines[i].strip()
        i += 1
        if not line:
            continue
        heading = re.match(r'^(#{1,6})\s+(.*)$', line)
        if heading:
            blocks.append((f"h{len(heading.group(1))}", heading.group(2).strip()))
            continue
        if re.match(r'^[-*+]\s+', line):
            items = [re.sub(r'^[-*+]\s+', '', line).strip()]
            while i < n and re.match(r'^\s*[-*+]\s+', lines[i]):
                items.append(re.sub(r'^\s*[-*+]\s+', '', lines[i]).strip())
                i += 1
            blocks.append(("ul", items))
            continue
        num = re.match(r'^(\d+)[.、)]\s+(.*)$', line)
        if num:
            items = [num.group(2).strip()]
            while i < n:
                nxt = re.match(r'^\s*(\d+)[.、)]\s+(.*)$', lines[i])
                if not nxt:
                    break
                items.append(nxt.group(2).strip())
                i += 1
            blocks.append(("ol", items))
            continue
        blocks.append(("p", line))
    return blocks


def _first_heading(md: str, fallback: str) -> str:
    """取 Markdown 首个一级标题作为标题；没有则用 fallback。"""
    for line in (md or "").replace("\r\n", "\n").split("\n"):
        m = re.match(r'^#\s+(.*)$', line.strip())
        if m:
            return _strip_md_inline(m.group(1))
    return fallback


def _strip_first_heading_line(md: str) -> str:
    """去掉正文中首个一级标题行（标题已在页头单独渲染）。"""
    lines = (md or "").replace("\r\n", "\n").split("\n")
    out, removed = [], False
    for line in lines:
        if not removed and re.match(r'^#\s+', line.strip()):
            removed = True
            continue
        out.append(line)
    return "\n".join(out)


def generate_docx_from_markdown(md: str, meta: dict) -> tuple:
    """把确认后的 Markdown 教案渲染为 DOCX（所见即所得）。"""
    doc = Document()
    section = doc.sections[0]
    section.top_margin = Cm(2.4)
    section.bottom_margin = Cm(2.4)
    section.left_margin = Cm(2.6)
    section.right_margin = Cm(2.6)

    normal = doc.styles['Normal']
    normal.font.name = 'Microsoft YaHei'
    normal.font.size = DocxPt(11)
    normal.paragraph_format.line_spacing = 1.5
    normal.paragraph_format.space_after = DocxPt(4)
    normal.element.rPr.rFonts.set(qn('w:eastAsia'), 'Microsoft YaHei')

    # ① 标题区
    title_text = _first_heading(md, meta.get("topic") or "教案")
    title_para = doc.add_paragraph()
    title_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title_para.paragraph_format.space_before = DocxPt(12)
    title_para.paragraph_format.space_after = DocxPt(6)
    _set_cn_font(title_para.add_run(title_text), size=26, bold=True,
                 color=_DOC_PRIMARY, name="黑体")

    subtitle = " · ".join(x for x in [meta.get("subject", ""), meta.get("grade", "")] if x)
    if subtitle:
        sub_para = doc.add_paragraph()
        sub_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        sub_para.paragraph_format.space_after = DocxPt(6)
        _set_cn_font(sub_para.add_run(subtitle), size=13, color=_DOC_MUTED)

    div_para = doc.add_paragraph()
    div_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    div_para.paragraph_format.space_after = DocxPt(12)
    _set_cn_font(div_para.add_run("─" * 46), size=10, color="CBD5E1")

    # ② 课程基本信息表（取自任务参数，保证准确）
    _add_info_table(doc, [
        ("学科", meta.get("subject", "")),
        ("年级", meta.get("grade", "")),
        ("课时", meta.get("duration", "1课时")),
        ("教学风格", meta.get("style", "—")),
    ])
    doc.add_paragraph(style='Normal')

    # ③ 正文：按 Markdown 层级渲染（一级栏目→深蓝色块标题，环节→◆标题）
    for kind, payload in _parse_markdown_blocks(md):
        if kind == "h1":
            if payload == title_text:
                continue  # 标题已在页头渲染
            _add_heading(doc, _strip_md_inline(payload), 1)
        elif kind == "h2":
            _add_heading(doc, _strip_md_inline(payload), 1)
        elif kind in ("h3", "h4"):
            _add_heading(doc, _strip_md_inline(payload), 2)
        elif kind in ("h5", "h6"):
            _add_heading(doc, _strip_md_inline(payload), 3)
        elif kind == "ul":
            for item in payload:
                p = doc.add_paragraph()
                p.paragraph_format.left_indent = Cm(1.0)
                p.paragraph_format.space_after = DocxPt(3)
                _set_cn_font(p.add_run("▸ "), size=11, color="94A3B8")
                _set_cn_font(p.add_run(_strip_md_inline(item)), size=11, color=_DOC_BODY)
        elif kind == "ol":
            for idx, item in enumerate(payload, 1):
                p = doc.add_paragraph()
                p.paragraph_format.left_indent = Cm(1.0)
                p.paragraph_format.space_after = DocxPt(3)
                _set_cn_font(p.add_run(f"{idx}. "), size=11, bold=True, color=_DOC_ACCENT)
                _set_cn_font(p.add_run(_strip_md_inline(item)), size=11, color=_DOC_BODY)
        else:
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Cm(0.5)
            p.paragraph_format.space_after = DocxPt(4)
            _set_cn_font(p.add_run(_strip_md_inline(payload)), size=11, color=_DOC_BODY)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    safe_title = re.sub(r'[<>:"/\\|?*]', '_', title_text)
    filename = f"{safe_title}.docx"
    filepath = os.path.join(OUTPUT_DIR, filename)
    doc.save(filepath)
    print(f"[DOC] 已生成: {filepath}")
    return filepath, filename


# HTML 文档外壳（练习题 / 试卷共用）：浅色纸张风，便于阅读与打印
_HTML_MD_CSS = """
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    font-family: system-ui, "PingFang SC", "Microsoft YaHei", sans-serif;
    max-width: 860px; margin: 0 auto; padding: 48px 28px 64px;
    color: #1E293B; background: #F7F5F2; line-height: 1.8;
  }
  .header { text-align: center; margin-bottom: 36px; padding-bottom: 24px;
    border-bottom: 2px solid #E2E8F0; }
  .header h1 { font-size: 1.9rem; font-weight: 800; color: #1A365D;
    letter-spacing: -0.02em; margin-bottom: 10px; }
  .header .meta { display: flex; flex-wrap: wrap; align-items: center;
    justify-content: center; gap: 10px 18px; color: #64748B; font-size: 0.9rem; }
  .header .meta span { padding: 3px 12px; background: #F1F5F9; border-radius: 20px; }
  .doc { background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px;
    padding: 32px 34px; box-shadow: 0 1px 2px rgba(0,0,0,0.04); }
  .doc h1 { font-size: 1.5rem; color: #1A365D; margin: 30px 0 14px;
    padding-bottom: 8px; border-bottom: 2px solid #EAF2FB; }
  .doc h2 { font-size: 1.25rem; color: #1A365D; margin: 28px 0 12px;
    padding: 8px 12px; background: #EAF2FB; border-left: 4px solid #1A365D;
    border-radius: 4px; }
  .doc h3 { font-size: 1.08rem; color: #2B6CB0; margin: 20px 0 10px; }
  .doc h4, .doc h5, .doc h6 { font-size: 1rem; color: #0E7490; margin: 16px 0 8px; }
  .doc p { margin: 8px 0; color: #334155; }
  .doc ul, .doc ol { margin: 8px 0 8px 24px; color: #334155; }
  .doc li { margin: 5px 0; }
  strong { color: #1A365D; }
  .footer { text-align: center; margin-top: 40px; padding-top: 20px;
    border-top: 1px solid #E2E8F0; color: #94A3B8; font-size: 0.8rem; }
  @media print { body { background: #fff; padding: 0; } .doc { border: none; box-shadow: none; } }
"""


def _html_inline(text: str) -> str:
    """转义后保留加粗标记。"""
    text = html.escape(_strip_md_inline(text))
    return text


def _markdown_to_html(md: str) -> str:
    """Markdown 块 → HTML（标题 / 列表 / 段落）。"""
    parts = []
    for kind, payload in _parse_markdown_blocks(md):
        if kind.startswith("h"):
            lvl = kind[1]
            parts.append(f"<h{lvl}>{_html_inline(payload)}</h{lvl}>")
        elif kind == "ul":
            items = "".join(f"<li>{_html_inline(x)}</li>" for x in payload)
            parts.append(f"<ul>{items}</ul>")
        elif kind == "ol":
            items = "".join(f"<li>{_html_inline(x)}</li>" for x in payload)
            parts.append(f"<ol>{items}</ol>")
        else:
            parts.append(f"<p>{_html_inline(payload)}</p>")
    return "\n".join(parts)


def _render_markdown_html(md: str, meta: dict, kind: str) -> tuple:
    """通用：Markdown → 独立 HTML 文件（练习题 / 试卷）。"""
    default_title = "试卷" if kind == "exam" else "练习题"
    title = _first_heading(md, meta.get("topic") or default_title)
    body = _markdown_to_html(_strip_first_heading_line(md))

    bits = []
    if meta.get("subject"):
        bits.append(f"学科：{meta['subject']}")
    if meta.get("grade"):
        bits.append(f"年级：{meta['grade']}")
    if kind == "exam" and meta.get("totalScore"):
        bits.append(f"总分：{meta['totalScore']} 分")
    if meta.get("duration"):
        bits.append(f"时长：{meta['duration']}")
    meta_html = "".join(f"<span>{html.escape(b)}</span>" for b in bits)

    footer = ("知启灵枢 · AI 智能组卷 · 仅供教学参考" if kind == "exam"
              else "知启灵枢 · AI 智能出题 · 仅供教学参考")

    doc = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html.escape(title)}</title>
<style>{_HTML_MD_CSS}</style>
</head>
<body>
<div class="header">
  <h1>{html.escape(title)}</h1>
  <div class="meta">{meta_html}</div>
</div>

<div class="doc">
{body}
</div>

<div class="footer"><p>{footer}</p></div>
</body>
</html>"""

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    safe_title = re.sub(r'[<>:"/\\|?*]', '_', title)
    filename = f"{safe_title}.html"
    filepath = os.path.join(OUTPUT_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(doc)
    print(f"[HTML] 已生成: {filepath}")
    return filepath, filename


def generate_quiz_html_from_markdown(md: str, meta: dict) -> tuple:
    """把确认后的 Markdown 练习题渲染为 HTML。"""
    return _render_markdown_html(md, meta, "quiz")


def generate_exam_html_from_markdown(md: str, meta: dict) -> tuple:
    """把确认后的 Markdown 试卷渲染为 HTML。"""
    return _render_markdown_html(md, meta, "exam")


def parse_ppt_outline(md: str, meta: dict = None) -> dict:
    """把 Markdown 课件大纲解析为 PPT 渲染器所需的 content 结构。

    规则：# → 封面标题；## → 章节分隔页；### → 内容页；- → 内容页要点。
    """
    meta = meta or {}
    lines = (md or "").replace("\r\n", "\n").split("\n")
    title = ""
    slides = []
    current = None
    for raw in lines:
        line = raw.strip()
        if not line:
            continue
        h = re.match(r'^(#{1,3})\s+(.*)$', line)
        if h:
            level, text = len(h.group(1)), _strip_md_inline(h.group(2))
            if level == 1:
                title = title or text
            elif level == 2:
                slides.append({"type": "section", "title": text, "content": []})
                current = None
            else:
                current = {"type": "content", "title": text, "content": []}
                slides.append(current)
            continue
        bullet = re.match(r'^[-*+]\s+(.*)$', line)
        item = _strip_md_inline(bullet.group(1) if bullet else line)
        if current is None:
            current = {"type": "content", "title": "内容", "content": []}
            slides.append(current)
        current["content"].append(item)

    title = title or meta.get("topic") or "教学课件"
    cover_meta = " · ".join(x for x in [meta.get("subject", ""), meta.get("grade", "")] if x)
    slides.insert(0, {
        "type": "title",
        "title": title,
        "content": [cover_meta] if cover_meta else [],
    })
    return {"title": title, "subtitle": "", "slides": slides}


# ════════════════════════════════════════════════════════════════
# 测试入口
# ════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    test = {
        "title": "牛顿第二定律",
        "subject": "物理",
        "grade": "高一",
        "duration": "45分钟",
        "slides": [
            {"type": "title", "title": "牛顿第二定律",
             "content": ["高中物理 · 必修一", "F = ma"], "notes": ""},
            {"type": "section", "title": "第一部分：知识回顾",
             "content": [], "notes": ""},
            {"type": "content", "title": "复习回顾",
             "content": ["力的概念与表示方法", "牛顿第一定律（惯性定律）", "加速度的定义与物理意义"],
             "notes": ""},
            {"type": "content", "title": "实验探究",
             "content": ["控制变量法：分别探究 F 与 m 的影响",
              "质量一定时：加速度与合外力成正比 a ∝ F",
              "合外力一定时：加速度与质量成反比 a ∝ 1/m"],
             "notes": "重点讲解实验设计"},
            {"type": "content", "title": "牛顿第二定律公式",
             "content": ["表达式：F = ma", "F — 合外力（单位：N）",
              "m — 质量（单位：kg）", "a — 加速度（单位：m/s²）"],
             "notes": ""},
            {"type": "comparison", "title": "典型例题对比",
             "content": ["已知 F=10N, m=2kg → a=5m/s²",
              "已知 a=3m/s², m=4kg → F=12N",
              "水平面光滑，F=15N, m=3kg → a=5m/s²",
              "斜面 θ=30°, m=2kg → a=4.9m/s²"],
             "notes": ""},
            {"type": "summary", "title": "本节课总结",
             "content": ["牛顿第二定律：F = ma",
              "矢量性：a 与 F 方向始终相同",
              "瞬时性：F 变化则 a 瞬时变化",
              "独立性：各分力产生的加速度独立叠加"],
             "notes": ""},
        ],
    }

    print("=" * 60)
    print("  知启灵枢 · 文件生成器测试")
    print("=" * 60)

    path, name = generate_pptx(test)
    print(f"  PPT  → {path}")

    # 测试 DOCX
    doc_test = {
        "title": "牛顿第二定律教案",
        "subject": "物理",
        "grade": "高一",
        "duration": "45分钟",
        "teachingGoals": "理解牛顿第二定律的内容与公式；掌握F=ma的应用方法；培养科学探究精神",
        "keyPoints": "牛顿第二定律的公式推导；加速度与力、质量的关系",
        "sections": [
            {"heading": "导入新课", "content": ["回顾牛顿第一定律", "提问：力与加速度的关系？"]},
            {"heading": "新课讲授", "content": ["实验演示：控制变量法", "推导公式 F=ma", "讲解各物理量含义"]},
            {"heading": "巩固练习", "content": ["例题1：已知力求加速度", "例题2：已知加速度求力"]},
        ],
    }
    dpath, dname = generate_docx(doc_test)
    print(f"  DOC → {dpath}")

    # 测试 HTML
    quiz_test = {
        "title": "牛顿第二定律练习",
        "questions": [
            {"type": "choice", "question": "牛顿第二定律的表达式是？",
             "options": ["A. F = mv", "B. F = ma", "C. F = m/a", "D. F = a/m"],
             "answer": "B", "analysis": "牛顿第二定律表明合外力等于质量乘以加速度。"},
            {"type": "fill", "question": "质量为2kg的物体受到10N合外力，加速度为___ m/s²",
             "options": [], "answer": "5", "analysis": "由 F=ma 得 a=F/m=10/2=5 m/s²"},
            {"type": "essay", "question": "请简述牛顿第二定律中'矢量性'的含义。",
             "options": [], "answer": "加速度方向与合外力方向始终相同",
             "analysis": "F=ma是矢量等式，a的方向由F决定。"},
        ],
    }
    qpath, qname = generate_quiz_html(quiz_test)
    print(f"  HTML→ {qpath}")
    print("=" * 60)
    print("  全部生成完成！")
