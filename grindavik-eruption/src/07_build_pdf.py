# -*- coding: utf-8 -*-
"""발표자료(PDF) 조립 — content.SLIDES를 matplotlib으로 16:9 페이지 렌더.

libreoffice 변환 불가 환경이라 NanumGothic 임베드 PDF를 직접 생성.
"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from common import OUT, FIG
import content as C
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Rectangle, Polygon
import matplotlib.font_manager as fm
import matplotlib.image as mpimg

FP = "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"
FPB = "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf"
fm.fontManager.addfont(FP); fm.fontManager.addfont(FPB)
matplotlib.rcParams["font.family"] = "NanumGothic"
KF = fm.FontProperties(fname=FP); KB = fm.FontProperties(fname=FPB)

# 시립대(UOS) 템플릿(UOS_PTformat_B) 아이덴티티, 16:9 유지 (deck.py와 동일 팔레트)
PRIMARY = "#004094"; ACCENT = "#0E7C7B"; ACCENT2 = "#D9532B"
LIGHT = "#ECEAE6"; GREY = "#7B8894"; DARK = "#1B2430"; WHITE = "#FFFFFF"
HAIR = "#DEE5EB"; SUB1 = "#C9D7EA"
COL = {"dark": DARK, "primary": PRIMARY, "accent": ACCENT, "accent2": ACCENT2, "grey": GREY}
LOGO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "uos_logo.png")
F = lambda n: f"{FIG}/{n}"
W, H = 13.333, 7.5


def newpage(facecolor=WHITE):
    fig = plt.figure(figsize=(W, H), dpi=200); fig.patch.set_facecolor(facecolor)
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, W); ax.set_ylim(0, H)
    ax.axis("off"); ax.invert_yaxis()
    return fig, ax


def txt(ax, x, y, s, size, color=DARK, bold=False, ha="left", va="top", wrap=True):
    ax.text(x, y, s, fontsize=size, color=color, ha=ha, va=va,
            fontproperties=(KB if bold else KF), wrap=wrap, zorder=5)


def rrect(ax, x, y, w, h, color, alpha=1.0):
    ax.add_patch(Rectangle((x, y), w, h, color=color, alpha=alpha, zorder=1))


def trapbar(ax, x, y, w, h, color=None, topnip=0.021, botlift=0.02):
    """UOS 좌측 세로바 — 위 모서리·아래 변이 비스듬한 사다리꼴 (템플릿 충실)."""
    ax.add_patch(Polygon([(x, y), (x + w * (1 - topnip), y),
                          (x + w, y + h * (1 - botlift)), (x, y + h)],
                         color=color or PRIMARY, zorder=1))


def head(ax, kicker, title):
    trapbar(ax, 0, 0, 0.15, 1.05, PRIMARY, topnip=0, botlift=0.023)
    txt(ax, 0.42, 0.21, kicker, 12.5, PRIMARY, bold=True)
    txt(ax, 0.42, 0.52, title, 22, DARK, bold=True)
    img_on(ax, LOGO, 12.55, 0.22, 0.62, 0.62)
    rrect(ax, 0, 1.18, W, 0.012, HAIR)
    rrect(ax, 0.42, 1.155, 2.0, 0.05, PRIMARY)


def footer(ax, page):
    txt(ax, 0.4, 7.24, C.META["footer"], 8.5, GREY)
    txt(ax, 12.9, 7.24, str(page), 9, GREY, ha="right")


def draw_bullets(ax, blts, x, y, size=14, gap=0.34, maxw=60):
    import textwrap
    cy = y
    for (text, lv, ck, bold) in blts:
        color = COL.get(ck, DARK)
        marker = "■ " if lv == 0 else ("·  " if lv == 1 else "-  ")
        indent = x + lv * 0.42; sz = size - lv * 1.0
        wrapped = textwrap.wrap(text, width=int(maxw - lv * 6)) or [text]
        for i, line in enumerate(wrapped):
            prefix = marker if i == 0 else "    "
            txt(ax, indent, cy, prefix + line, sz, color, bold=bold)
            cy += gap * (0.82 if i > 0 else 1.0)
        cy += gap * 0.28
    return cy


def img_on(ax, path, x, y, w, h):
    im = mpimg.imread(path); ih, iw = im.shape[:2]; ar = iw / ih; bar = w / h
    if ar > bar: nw = w; nh = w / ar
    else: nh = h; nw = h * ar
    nx = x + (w - nw) / 2; ny = y + (h - nh) / 2
    iax = ax.figure.add_axes([nx / W, 1 - (ny + nh) / H, nw / W, nh / H])
    iax.imshow(im); iax.axis("off")


def draw_table(ax, data, x, y, w, rowh=0.42, col_w=None, size=12):
    rows, cols = len(data), len(data[0])
    if col_w is None: col_w = [1] * cols
    tot = sum(col_w); cw = [w * c / tot for c in col_w]
    for i, row in enumerate(data):
        ry = y + i * rowh; cx = x
        for j, val in enumerate(row):
            rrect(ax, cx, ry, cw[j], rowh, PRIMARY if i == 0 else (LIGHT if i % 2 else WHITE))
            ax.add_patch(Rectangle((cx, ry), cw[j], rowh, fill=False, ec="#CCCCCC", lw=0.5, zorder=2))
            txt(ax, cx + 0.1, ry + rowh / 2, str(val), size, WHITE if i == 0 else DARK, bold=(i == 0), va="center")
            cx += cw[j]
    return y + rows * rowh


def banner(ax, text, y=6.0):
    rrect(ax, 0.7, y, 11.93, 0.85, LIGHT); rrect(ax, 0.7, y, 0.12, 0.85, PRIMARY)
    size = 14 if len(text) <= 60 else (13 if len(text) <= 70 else 12)  # 길면 자동 축소(오버플로 방지)
    txt(ax, 1.0, y + 0.43, text, size, DARK, bold=True, va="center")


def render(pdf, sp, page):
    t = sp["type"]
    if t == "title":
        fig, ax = newpage()
        # UOS 표지(템플릿 충실): 메인 패널은 하단이 대각으로 잘린 오각형 + 우하단 경사 조각
        ax.add_patch(Polygon([(0, 0), (10.84, 0), (10.84, 5.60), (0, H)], color=PRIMARY, zorder=1))
        ax.add_patch(Polygon([(13.333, 5.84), (13.333, 7.5), (10.68, 7.5), (10.68, 6.40)],
                             color=PRIMARY, zorder=1))
        img_on(ax, LOGO, 11.95, 0.35, 1.0, 1.0)
        rrect(ax, 0.9, 4.45, 2.2, 0.05, WHITE)
        for i, ln in enumerate(C.META["title"].split("\n")):
            txt(ax, 0.9, 1.7 + i * 0.62, ln, 27, WHITE, bold=True)
        txt(ax, 0.9, 3.6, C.META["subtitle"], 16.5, SUB1)
        txt(ax, 0.9, 5.0, C.META["course"], 14.5, SUB1)
        txt(ax, 0.9, 5.5, f"발표 순서 {C.META['present_no']}번    |    팀원: {C.META['team']}", 14.5, SUB1)
        txt(ax, 12.95, 7.0, C.META["date"], 12.5, WHITE, bold=True, ha="right")
    elif t == "toc":
        fig, ax = newpage()
        trapbar(ax, 0, 0, 0.45, 4.15)
        img_on(ax, LOGO, 12.30, 0.30, 0.75, 0.75)
        txt(ax, 0.95, 0.62, "목차", 22, DARK, bold=True)
        txt(ax, 0.95, 1.22, "Table of Contents", 12, PRIMARY, bold=True)
        yy = 2.05
        for s2 in C.SLIDES:
            if s2["type"] != "section": continue
            rrect(ax, 1.0, yy, 0.52, 0.52, PRIMARY)
            txt(ax, 1.26, yy + 0.26, f"{s2['no']:02d}", 14, WHITE, bold=True, ha="center", va="center")
            txt(ax, 1.78, yy + 0.26, s2["title"], 17, DARK, bold=True, va="center")
            yy += 0.92
        footer(ax, page)
    elif t == "section":
        fig, ax = newpage()
        # UOS 챕터: 흰 바탕 + 좌측 블루 사다리꼴 바 + 로고 (템플릿 충실 — 하단 라인 없음)
        trapbar(ax, 0, 0, 0.45, 4.15)
        img_on(ax, LOGO, 12.30, 0.30, 0.75, 0.75)
        txt(ax, 0.95, 2.55, f"{sp['no']:02d}", 46, PRIMARY, bold=True)
        txt(ax, 0.95, 3.80, sp["title"], 28, DARK, bold=True)
        footer(ax, page)
    elif t == "end":
        fig, ax = newpage()
        img_on(ax, LOGO, (W - 1.0) / 2, 1.65, 1.0, 1.0)
        rrect(ax, 0, 7.38, W, 0.12, PRIMARY)
        txt(ax, W / 2, 3.6, "감사합니다  ·  Q & A", 30, PRIMARY, bold=True, ha="center", va="center")
        txt(ax, W / 2, 4.5, f"{C.META['team']}   |   발표 {C.META['present_no']}번", 15, DARK, ha="center")
        txt(ax, W / 2, 5.0, C.META["course"], 12.5, GREY, ha="center")
    elif t == "content":
        fig, ax = newpage()
        head(ax, sp["kicker"], sp["title"]); side = sp.get("img_side"); y = 1.55
        if sp.get("pretext"):
            txt(ax, 0.55, y, sp["pretext"], 14, PRIMARY, bold=True); y += 0.55
        if side == "full":
            img_on(ax, F(sp["image"]), 0.5, 1.4, 12.3, 4.55 if sp.get("banner") else 5.3)
        elif side == "left":
            img_on(ax, F(sp["image"]), 0.3, 1.4, 8.85, 5.4)
            draw_bullets(ax, sp["bullets"], 9.4, 1.8, size=14.5, gap=0.355, maxw=23)
        else:
            if sp.get("table"):
                tw = 7.3 if sp.get("bullets") else 11.5
                yend = draw_table(ax, sp["table"], 0.55, y, tw, col_w=sp.get("table_col_w"), size=13.5)
                if sp.get("bullets"):
                    draw_bullets(ax, sp["bullets"], 8.2, y + 0.1, size=14, gap=0.35, maxw=31)
                if sp.get("subtext"):
                    txt(ax, 0.6, yend + 0.3, sp["subtext"], 13.5, GREY)
            elif sp.get("bullets"):
                # 래핑 포함 줄 수로 자동 축소(긴 불릿이 많으면 dense) — 푸터 침범 방지
                blts = sp["bullets"]
                lines = sum(max(1, -(-len(t[0]) // (58 - t[1] * 6))) for t in blts)
                sz, gp, mw = (14.5, 0.36, 74) if (len(blts) > 9 or lines > 11) else (16.5, 0.44, 64)
                draw_bullets(ax, blts, 0.6, y, size=sz, gap=gp, maxw=mw)
        if sp.get("software"):
            rrect(ax, 0.55, 6.42, 12.23, 0.5, LIGHT); rrect(ax, 0.55, 6.42, 0.1, 0.5, PRIMARY)
            txt(ax, 0.78, 6.67, sp["software"], 11.5, PRIMARY, bold=True, va="center")
        if sp.get("banner"):
            banner(ax, sp["banner"], y=5.98)
        footer(ax, page)
    pdf.savefig(fig); plt.close(fig)


out = f"{OUT}/아이슬란드_화산_변화탐지_발표.pdf"
page = 0
with PdfPages(out) as pdf:
    for sp in C.SLIDES:
        if sp["type"] in ("toc", "section", "content"):
            page += 1
        render(pdf, sp, page)
print(f"PDF 저장: {out}  ({len(C.SLIDES)} pages)")
