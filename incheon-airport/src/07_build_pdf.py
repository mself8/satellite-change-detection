# -*- coding: utf-8 -*-
"""발표자료(PDF) 조립 — content.SLIDES를 matplotlib으로 16:9 페이지 렌더.

libreoffice 변환이 불가한 환경이라 NanumGothic을 임베드한 PDF를 직접 생성.
"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from common import OUT, FIG
import content as C
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Rectangle, FancyBboxPatch
import matplotlib.font_manager as fm
import matplotlib.image as mpimg

FP = "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"
FPB = "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf"
fm.fontManager.addfont(FP); fm.fontManager.addfont(FPB)
matplotlib.rcParams["font.family"] = "NanumGothic"
KF = fm.FontProperties(fname=FP); KB = fm.FontProperties(fname=FPB)

PRIMARY = "#143D59"; ACCENT = "#2E9E8F"; ACCENT2 = "#E8893A"
LIGHT = "#EEF3F5"; GREY = "#5A5A5A"; DARK = "#202A30"; WHITE = "#FFFFFF"
COL = {"dark": DARK, "primary": PRIMARY, "accent": ACCENT, "accent2": ACCENT2, "grey": GREY}
F = lambda n: f"{FIG}/{n}"
W, H = 13.333, 7.5


def newpage(pdf, facecolor=WHITE):
    fig = plt.figure(figsize=(W, H), dpi=200); fig.patch.set_facecolor(facecolor)
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, W); ax.set_ylim(0, H)
    ax.axis("off"); ax.invert_yaxis()
    return fig, ax


def txt(ax, x, y, s, size, color=DARK, bold=False, ha="left", va="top", wrap=True):
    ax.text(x, y, s, fontsize=size, color=color, ha=ha, va=va,
            fontproperties=(KB if bold else KF), wrap=wrap, zorder=5)


def rrect(ax, x, y, w, h, color, alpha=1.0):
    ax.add_patch(Rectangle((x, y), w, h, color=color, alpha=alpha, zorder=1))


def head(ax, kicker, title):
    rrect(ax, 0, 0, W, 1.15, PRIMARY)
    rrect(ax, 0, 1.15, W, 0.06, ACCENT)
    txt(ax, 0.55, 0.34, kicker, 11.5, ACCENT, bold=True)
    txt(ax, 0.55, 0.62, title, 20, WHITE, bold=True)


def footer(ax, page):
    txt(ax, 0.4, 7.24, C.META["footer"], 8.5, GREY)
    txt(ax, 12.9, 7.24, str(page), 9, GREY, ha="right")


def draw_bullets(ax, blts, x, y, size=14, gap=0.34, maxw=60):
    import textwrap
    cy = y
    for (text, lv, ck, bold) in blts:
        color = COL.get(ck, DARK)
        marker = "■ " if lv == 0 else ("·  " if lv == 1 else "-  ")
        indent = x + lv * 0.42
        sz = size - lv * 1.2
        wrapped = textwrap.wrap(text, width=int(maxw - lv * 6)) or [text]
        for i, line in enumerate(wrapped):
            prefix = marker if i == 0 else "    "
            txt(ax, indent, cy, prefix + line, sz, color, bold=bold)
            cy += gap * (0.82 if i > 0 else 1.0)
        cy += gap * 0.28
    return cy


def img_on(ax, path, x, y, w, h):
    im = mpimg.imread(path); ih, iw = im.shape[:2]; ar = iw / ih; bar = w / h
    if ar > bar:
        nw = w; nh = w / ar
    else:
        nh = h; nw = h * ar
    nx = x + (w - nw) / 2; ny = y + (h - nh) / 2
    iax = ax.figure.add_axes([nx / W, 1 - (ny + nh) / H, nw / W, nh / H])
    iax.imshow(im); iax.axis("off")


def draw_table(ax, data, x, y, w, rowh=0.42, col_w=None, size=12):
    rows, cols = len(data), len(data[0])
    if col_w is None: col_w = [1] * cols
    tot = sum(col_w); cw = [w * c / tot for c in col_w]
    for i, row in enumerate(data):
        ry = y + i * rowh
        cx = x
        for j, val in enumerate(row):
            if i == 0:
                rrect(ax, cx, ry, cw[j], rowh, PRIMARY)
            else:
                rrect(ax, cx, ry, cw[j], rowh, LIGHT if i % 2 else WHITE)
            ax.add_patch(Rectangle((cx, ry), cw[j], rowh, fill=False, ec="#CCCCCC", lw=0.5, zorder=2))
            txt(ax, cx + 0.1, ry + rowh / 2, str(val), size,
                WHITE if i == 0 else DARK, bold=(i == 0), va="center")
            cx += cw[j]
    return y + rows * rowh


def banner(ax, text, y=6.0):
    rrect(ax, 0.7, y, 11.93, 0.85, LIGHT)
    rrect(ax, 0.7, y, 0.12, 0.85, ACCENT)
    txt(ax, 1.0, y + 0.43, text, 13.5, PRIMARY, bold=True, va="center")


def render(pdf, sp, page):
    t = sp["type"]
    if t == "title":
        fig, ax = newpage(pdf, PRIMARY)
        rrect(ax, 0, 4.45, W, 0.09, ACCENT); rrect(ax, 0, 0, 0.16, H, ACCENT)
        for i, ln in enumerate(C.META["title"].split("\n")):
            txt(ax, 0.9, 1.7 + i * 0.62, ln, 30, WHITE, bold=True)
        txt(ax, 0.9, 3.5, C.META["subtitle"], 18, "#BFE3DC")
        txt(ax, 0.9, 5.0, C.META["course"], 14.5, "#D9E2E8")
        txt(ax, 0.9, 5.5, f"발표 순서 {C.META['present_no']}번    |    팀원: {C.META['team']}", 14.5, "#D9E2E8")
        txt(ax, 0.9, 6.0, C.META["date"], 14.5, "#D9E2E8")
    elif t == "section":
        fig, ax = newpage(pdf, PRIMARY)
        rrect(ax, 0.9, 2.7, 1.5, 1.5, ACCENT)
        txt(ax, 1.65, 3.45, f"{sp['no']:02d}", 40, WHITE, bold=True, ha="center", va="center")
        txt(ax, 2.7, 3.45, sp["title"], 28, WHITE, bold=True, va="center")
        footer(ax, page)
    elif t == "end":
        fig, ax = newpage(pdf, PRIMARY)
        rrect(ax, 0, 3.5, W, 0.08, ACCENT)
        txt(ax, W / 2, 2.7, "감사합니다  ·  Q & A", 32, WHITE, bold=True, ha="center", va="center")
        txt(ax, W / 2, 4.3, f"{C.META['team']}   |   발표 {C.META['present_no']}번", 16, "#D9E2E8", ha="center")
        txt(ax, W / 2, 4.8, C.META["course"], 13, "#BFE3DC", ha="center")
    elif t == "content":
        fig, ax = newpage(pdf)
        head(ax, sp["kicker"], sp["title"])
        side = sp.get("img_side"); y = 1.55
        if sp.get("pretext"):
            txt(ax, 0.55, y, sp["pretext"], 14, PRIMARY, bold=True); y += 0.6
        if side == "full":
            img_on(ax, F(sp["image"]), 0.5, 1.4, 12.3, 4.55 if sp.get("banner") else 5.3)
        elif side == "left":
            img_on(ax, F(sp["image"]), 0.3, 1.4, 8.85, 5.4)
            draw_bullets(ax, sp["bullets"], 9.4, 1.85, size=13, gap=0.33, maxw=26)
        else:
            if sp.get("table"):
                tw = 7.3 if sp.get("bullets") else 11.5
                yend = draw_table(ax, sp["table"], 0.55, y, tw, col_w=sp.get("table_col_w"), size=12.5)
                if sp.get("bullets"):
                    draw_bullets(ax, sp["bullets"], 8.2, y + 0.1, size=13, gap=0.33, maxw=34)
                if sp.get("subtext"):
                    txt(ax, 0.6, yend + 0.3, sp["subtext"], 13, GREY)
            elif sp.get("bullets"):
                draw_bullets(ax, sp["bullets"], 0.6, y, size=15, gap=0.42, maxw=72)
        if sp.get("software"):
            rrect(ax, 0.55, 6.42, 12.23, 0.5, LIGHT)
            rrect(ax, 0.55, 6.42, 0.1, 0.5, ACCENT)
            txt(ax, 0.78, 6.67, sp["software"], 11, PRIMARY, bold=True, va="center")
        if sp.get("banner"):
            banner(ax, sp["banner"], y=5.98)
        footer(ax, page)
    pdf.savefig(fig); plt.close(fig)


out = f"{OUT}/인천공항_변화탐지_발표.pdf"
page = 0
with PdfPages(out) as pdf:
    for sp in C.SLIDES:
        if sp["type"] in ("section", "content"):
            page += 1
        render(pdf, sp, page)
print(f"PDF 저장: {out}  ({len(C.SLIDES)} pages, HAS_LST={C.HAS_LST})")
