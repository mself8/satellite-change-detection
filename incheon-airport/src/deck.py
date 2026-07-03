# -*- coding: utf-8 -*-
"""python-pptx 슬라이드 빌더 헬퍼 (테마·텍스트·이미지·표·노트)."""
import os
from PIL import Image
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

SW, SH = Inches(13.333), Inches(7.5)
FONT = "나눔고딕"
PRIMARY = RGBColor(0x14, 0x3D, 0x59)   # 딥네이비
ACCENT = RGBColor(0x2E, 0x9E, 0x8F)    # 틸
ACCENT2 = RGBColor(0xE8, 0x8A, 0x3A)   # 오렌지(강조)
LIGHT = RGBColor(0xEE, 0xF3, 0xF5)
GREY = RGBColor(0x5A, 0x5A, 0x5A)
DARK = RGBColor(0x20, 0x2A, 0x30)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)


def new_prs():
    prs = Presentation(); prs.slide_width = SW; prs.slide_height = SH
    return prs


def _blank(prs):
    return prs.slides.add_slide(prs.slide_layouts[6])


def _set(tf_para, text, size, color, bold=False, font=FONT, align=None):
    tf_para.text = text
    for r in tf_para.runs:
        r.font.size = Pt(size); r.font.color.rgb = color
        r.font.bold = bold; r.font.name = font
    if align is not None:
        tf_para.alignment = align


def rect(slide, x, y, w, h, color, line=None):
    sp = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, y, w, h)
    sp.fill.solid(); sp.fill.fore_color.rgb = color
    if line is None:
        sp.line.fill.background()
    else:
        sp.line.color.rgb = line; sp.line.width = Pt(1)
    sp.shadow.inherit = False
    return sp


def textbox(slide, x, y, w, h, anchor=MSO_ANCHOR.TOP):
    tb = slide.shapes.add_textbox(x, y, w, h); tf = tb.text_frame
    tf.word_wrap = True; tf.vertical_anchor = anchor
    return tb, tf


def notes(slide, text):
    slide.notes_slide.notes_text_frame.text = text


def title_slide(prs, title, subtitle, course, team, date, present_no):
    s = _blank(prs)
    rect(s, 0, 0, SW, SH, PRIMARY)
    rect(s, 0, Inches(4.45), SW, Inches(0.09), ACCENT)
    rect(s, Inches(0.0), Inches(0.0), Inches(0.16), SH, ACCENT)
    _, tf = textbox(s, Inches(0.9), Inches(1.5), Inches(11.5), Inches(2.6))
    _set(tf.paragraphs[0], title, 33, WHITE, bold=True)
    p = tf.add_paragraph(); _set(p, subtitle, 19, RGBColor(0xBF, 0xE3, 0xDC)); p.space_before = Pt(14)
    _, tf2 = textbox(s, Inches(0.9), Inches(4.8), Inches(11.5), Inches(2.2))
    _set(tf2.paragraphs[0], course, 15, RGBColor(0xD9, 0xE2, 0xE8))
    for line in [f"발표 순서 {present_no}번    |    팀원: {team}", date]:
        p = tf2.add_paragraph(); _set(p, line, 15, RGBColor(0xD9, 0xE2, 0xE8)); p.space_before = Pt(8)
    return s


def section_slide(prs, no, title):
    s = _blank(prs)
    rect(s, 0, 0, SW, SH, PRIMARY)
    rect(s, Inches(0.9), Inches(2.7), Inches(1.5), Inches(1.5), ACCENT)
    _, tf = textbox(s, Inches(0.95), Inches(2.7), Inches(1.4), Inches(1.5), MSO_ANCHOR.MIDDLE)
    _set(tf.paragraphs[0], f"{no:02d}", 44, WHITE, bold=True, align=PP_ALIGN.CENTER)
    _, tf2 = textbox(s, Inches(2.7), Inches(2.7), Inches(9.5), Inches(1.5), MSO_ANCHOR.MIDDLE)
    _set(tf2.paragraphs[0], title, 30, WHITE, bold=True)
    return s


def content_head(prs, kicker, title):
    s = _blank(prs)
    rect(s, 0, 0, SW, Inches(1.15), PRIMARY)
    rect(s, 0, Inches(1.15), SW, Inches(0.06), ACCENT)
    _, tfk = textbox(s, Inches(0.55), Inches(0.16), Inches(11), Inches(0.4))
    _set(tfk.paragraphs[0], kicker, 12, ACCENT, bold=True)
    _, tft = textbox(s, Inches(0.55), Inches(0.46), Inches(12.2), Inches(0.66))
    _set(tft.paragraphs[0], title, 23, WHITE, bold=True)
    return s


def footer(slide, page):
    _, tf = textbox(slide, Inches(0.4), Inches(7.05), Inches(8), Inches(0.4))
    _set(tf.paragraphs[0], "인천국제공항 4단계 확장 변화탐지  ·  발표 12번", 9, GREY)
    _, tf2 = textbox(slide, Inches(12.2), Inches(7.05), Inches(0.9), Inches(0.4))
    _set(tf2.paragraphs[0], str(page), 10, GREY, align=PP_ALIGN.RIGHT)


def bullets(slide, items, x, y, w, h, size=15, gap=7):
    """items: list of (text, level, color?, bold?)."""
    tb, tf = textbox(slide, x, y, w, h)
    first = True
    for it in items:
        text, level = it[0], it[1]
        color = it[2] if len(it) > 2 and it[2] else DARK
        bold = it[3] if len(it) > 3 else False
        p = tf.paragraphs[0] if first else tf.add_paragraph(); first = False
        p.level = level
        bullet = "■ " if level == 0 else ("· " if level == 1 else "- ")
        _set(p, bullet + text, size - level * 1.5, color, bold=bold)
        p.space_after = Pt(gap)
    return tb


def img_fit(slide, path, x, y, w, h, center=True):
    iw, ih = Image.open(path).size
    ar = iw / ih; box_ar = w / h
    if ar > box_ar:
        nw = w; nh = int(w / ar)
    else:
        nh = h; nw = int(h * ar)
    nx = x + (w - nw) // 2 if center else x
    ny = y + (h - nh) // 2 if center else y
    return slide.shapes.add_picture(path, nx, ny, nw, nh)


def caption(slide, text, x, y, w):
    _, tf = textbox(slide, x, y, w, Inches(0.35))
    _set(tf.paragraphs[0], text, 10, GREY, align=PP_ALIGN.CENTER)


def table(slide, data, x, y, w, h, header=True, sizes=11, col_w=None):
    rows, cols = len(data), len(data[0])
    gt = slide.shapes.add_table(rows, cols, x, y, w, h).table
    if col_w:
        total = sum(col_w)
        for j, cw in enumerate(col_w):
            gt.columns[j].width = int(w * cw / total)
    for i, row in enumerate(data):
        for j, val in enumerate(row):
            c = gt.cell(i, j); c.text = str(val)
            c.margin_left = Inches(0.08); c.margin_right = Inches(0.06)
            c.margin_top = Inches(0.03); c.margin_bottom = Inches(0.03)
            c.vertical_anchor = MSO_ANCHOR.MIDDLE
            para = c.text_frame.paragraphs[0]
            for r in para.runs:
                r.font.size = Pt(sizes); r.font.name = FONT
                r.font.bold = (i == 0 and header)
                r.font.color.rgb = WHITE if (i == 0 and header) else DARK
            if i == 0 and header:
                c.fill.solid(); c.fill.fore_color.rgb = PRIMARY
            else:
                c.fill.solid(); c.fill.fore_color.rgb = LIGHT if i % 2 else WHITE
    return gt
