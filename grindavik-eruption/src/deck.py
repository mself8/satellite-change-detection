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
# 시립대(UOS) 공식 템플릿(UOS_PTformat_B) 아이덴티티 적용, 16:9 유지
# — UOS Blue #004094 + 베이지 #ECEAE6, 좌측 세로바, 우상단 로고, 흰 바탕 챕터
PRIMARY = RGBColor(0x00, 0x40, 0x94)   # UOS Blue (크롬·표 헤더·구조 강조)
ACCENT = RGBColor(0x0E, 0x7C, 0x7B)    # 딥틸 (방법 강조 — 본문 전용)
ACCENT2 = RGBColor(0xD9, 0x53, 0x2B)   # 라바 (핵심 결과 강조 — 본문 전용)
LIGHT = RGBColor(0xEC, 0xEA, 0xE6)     # UOS 베이지 (배너·표 줄무늬)
GREY = RGBColor(0x7B, 0x88, 0x94)
DARK = RGBColor(0x1B, 0x24, 0x30)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
HAIR = RGBColor(0xDE, 0xE5, 0xEB)      # 헤어라인
SUB1 = RGBColor(0xC9, 0xD7, 0xEA)      # UOS Blue 배경 보조텍스트
LOGO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "uos_logo.png")

FOOTER = "변화탐지"   # 빌더가 content.META["footer"]로 덮어씀


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


def poly(slide, pts, color):
    """자유형 다각형 (UOS 템플릿 사다리꼴 재현). pts: [(x,y), ...] EMU(Length)."""
    fb = slide.shapes.build_freeform(int(pts[0][0]), int(pts[0][1]), scale=1.0)
    fb.add_line_segments([(int(x), int(y)) for x, y in pts[1:]], close=True)
    sp = fb.convert_to_shape()
    sp.fill.solid(); sp.fill.fore_color.rgb = color
    sp.line.fill.background(); sp.shadow.inherit = False
    return sp


def trapbar(slide, x, y, w, h, color, topnip=0.021, botlift=0.02):
    """UOS 좌측 세로바 — 위 모서리 topnip, 아래 변이 우상향 botlift 잘린 사다리꼴."""
    x, y, w, h = int(x), int(y), int(w), int(h)
    return poly(slide, [(x, y), (x + int(w * (1 - topnip)), y),
                        (x + w, y + int(h * (1 - botlift))), (x, y + h)], color)


def textbox(slide, x, y, w, h, anchor=MSO_ANCHOR.TOP):
    tb = slide.shapes.add_textbox(x, y, w, h); tf = tb.text_frame
    tf.word_wrap = True; tf.vertical_anchor = anchor
    return tb, tf


def notes(slide, text):
    slide.notes_slide.notes_text_frame.text = text


def title_slide(prs, title, subtitle, course, team, date, present_no):
    s = _blank(prs)
    # UOS 표지(템플릿 충실): 메인 패널은 하단이 대각으로 잘린 오각형 + 우하단 경사 조각
    poly(s, [(0, 0), (Inches(10.84), 0), (Inches(10.84), Inches(5.60)), (0, SH)], PRIMARY)
    poly(s, [(Inches(13.333), Inches(5.84)), (Inches(13.333), Inches(7.5)),
             (Inches(10.68), Inches(7.5)), (Inches(10.68), Inches(6.40))], PRIMARY)
    s.shapes.add_picture(LOGO, Inches(11.95), Inches(0.35), Inches(1.0), Inches(1.0))
    rect(s, Inches(0.9), Inches(4.45), Inches(2.2), Inches(0.05), WHITE)
    _, tf = textbox(s, Inches(0.9), Inches(1.5), Inches(9.3), Inches(2.6))
    _set(tf.paragraphs[0], title, 32, WHITE, bold=True)
    p = tf.add_paragraph(); _set(p, subtitle, 18, SUB1); p.space_before = Pt(14)
    _, tf2 = textbox(s, Inches(0.9), Inches(4.8), Inches(9.3), Inches(2.2))
    _set(tf2.paragraphs[0], course, 15, SUB1)
    for line in [f"발표 순서 {present_no}번    |    팀원: {team}"]:
        p = tf2.add_paragraph(); _set(p, line, 15, SUB1); p.space_before = Pt(8)
    _, tf3 = textbox(s, Inches(11.0), Inches(6.85), Inches(2.0), Inches(0.4))
    _set(tf3.paragraphs[0], date, 13, WHITE, bold=True, align=PP_ALIGN.RIGHT)
    return s


def toc_slide(prs, sections):
    s = _blank(prs)
    trapbar(s, 0, 0, Inches(0.45), Inches(4.15), PRIMARY)
    s.shapes.add_picture(LOGO, Inches(12.30), Inches(0.30), Inches(0.75), Inches(0.75))
    _, tf = textbox(s, Inches(0.95), Inches(0.62), Inches(8), Inches(0.6))
    _set(tf.paragraphs[0], "목차", 24, DARK, bold=True)
    _, tfe = textbox(s, Inches(0.95), Inches(1.18), Inches(8), Inches(0.4))
    _set(tfe.paragraphs[0], "Table of Contents", 12.5, PRIMARY, bold=True)
    y = 2.05
    for no, title in sections:
        rect(s, Inches(1.0), Inches(y), Inches(0.52), Inches(0.52), PRIMARY)
        _, tn = textbox(s, Inches(1.0), Inches(y), Inches(0.52), Inches(0.52), MSO_ANCHOR.MIDDLE)
        _set(tn.paragraphs[0], f"{no:02d}", 15, WHITE, bold=True, align=PP_ALIGN.CENTER)
        _, tt = textbox(s, Inches(1.78), Inches(y), Inches(9.5), Inches(0.52), MSO_ANCHOR.MIDDLE)
        _set(tt.paragraphs[0], title, 18, DARK, bold=True)
        y += 0.92
    return s


def section_slide(prs, no, title):
    s = _blank(prs)
    # UOS 챕터: 흰 바탕 + 좌측 블루 사다리꼴 바 + 로고 (템플릿 충실 — 하단 라인 없음)
    trapbar(s, 0, 0, Inches(0.45), Inches(4.15), PRIMARY)
    s.shapes.add_picture(LOGO, Inches(12.30), Inches(0.30), Inches(0.75), Inches(0.75))
    _, tf = textbox(s, Inches(0.95), Inches(2.55), Inches(10), Inches(0.8))
    _set(tf.paragraphs[0], f"{no:02d}", 50, PRIMARY, bold=True)
    _, tf2 = textbox(s, Inches(0.95), Inches(3.65), Inches(11.5), Inches(1.0))
    _set(tf2.paragraphs[0], title, 30, DARK, bold=True)
    return s


def end_slide(prs, team, present_no, course):
    s = _blank(prs)
    s.shapes.add_picture(LOGO, Inches(6.17), Inches(1.65), Inches(1.0), Inches(1.0))
    rect(s, 0, Inches(7.38), SW, Inches(0.12), PRIMARY)
    _, tf = textbox(s, Inches(0), Inches(3.1), SW, Inches(0.9))
    _set(tf.paragraphs[0], "감사합니다  ·  Q & A", 30, PRIMARY, bold=True, align=PP_ALIGN.CENTER)
    _, tf2 = textbox(s, Inches(0), Inches(4.4), SW, Inches(1.3))
    _set(tf2.paragraphs[0], f"{team}   |   발표 {present_no}번", 15, DARK, align=PP_ALIGN.CENTER)
    p = tf2.add_paragraph(); _set(p, course, 12.5, GREY, align=PP_ALIGN.CENTER); p.space_before = Pt(8)
    return s


def content_head(prs, kicker, title):
    s = _blank(prs)
    # UOS 본문 헤더: 화면 좌단 사다리꼴 미니바(템플릿 slide4) + 블루 키커 + 잉크 타이틀 + 로고
    trapbar(s, 0, 0, Inches(0.15), Inches(1.05), PRIMARY, topnip=0, botlift=0.023)
    _, tfk = textbox(s, Inches(0.42), Inches(0.13), Inches(11), Inches(0.4))
    _set(tfk.paragraphs[0], kicker, 13, PRIMARY, bold=True)
    _, tft = textbox(s, Inches(0.42), Inches(0.45), Inches(11.8), Inches(0.66))
    _set(tft.paragraphs[0], title, 24, DARK, bold=True)
    s.shapes.add_picture(LOGO, Inches(12.55), Inches(0.22), Inches(0.62), Inches(0.62))
    rect(s, 0, Inches(1.18), SW, Inches(0.012), HAIR)
    rect(s, Inches(0.42), Inches(1.155), Inches(2.0), Inches(0.05), PRIMARY)
    return s


def footer(slide, page):
    _, tf = textbox(slide, Inches(0.4), Inches(7.05), Inches(8), Inches(0.4))
    _set(tf.paragraphs[0], FOOTER, 9, GREY)
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
        _set(p, bullet + text, size - level * 1.2, color, bold=bold)
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
