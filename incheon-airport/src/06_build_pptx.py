# -*- coding: utf-8 -*-
"""발표자료(PPTX) 조립 — content.SLIDES 사양을 렌더."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from common import OUT, FIG
import deck as D
import content as C
from pptx.util import Inches, Pt

COL = {"dark": D.DARK, "primary": D.PRIMARY, "accent": D.ACCENT,
       "accent2": D.ACCENT2, "grey": D.GREY}
F = lambda n: f"{FIG}/{n}"


def conv_bullets(blts):
    return [(t, lv, COL.get(ck, D.DARK), bd) for (t, lv, ck, bd) in blts]


prs = D.new_prs()
page = [0]


def add_footer(s):
    page[0] += 1; D.footer(s, page[0])


for sp in C.SLIDES:
    t = sp["type"]
    if t == "title":
        s = D.title_slide(prs, C.META["title"], C.META["subtitle"], C.META["course"],
                          C.META["team"], C.META["date"], C.META["present_no"])
        D.notes(s, f"발표 시작(약 12분). 인천공항 4단계 확장 전후를 Sentinel-2와 {C.NM}개 기법으로 변화탐지. "
                   "핵심: 통념(확장=식생감소)과 달리 녹화가 우세, 다중기법 교차분석의 필요성.")
    elif t == "section":
        s = D.section_slide(prs, sp["no"], sp["title"]); add_footer(s)
    elif t == "end":
        s = D.section_slide(prs, 99, "감사합니다  ·  Q & A")
        _, tf = D.textbox(s, Inches(2.7), Inches(4.4), Inches(9.5), Inches(1.5))
        D._set(tf.paragraphs[0], f"{C.META['team']}   |   발표 {C.META['present_no']}번", 16, D.WHITE)
        p = tf.add_paragraph(); D._set(p, C.META["course"], 13, D.RGBColor(0xBF, 0xE3, 0xDC))
        D.notes(s, sp["note"])
    elif t == "content":
        s = D.content_head(prs, sp["kicker"], sp["title"])
        side = sp.get("img_side")
        y = 1.45
        if sp.get("pretext"):
            _, tf = D.textbox(s, Inches(0.55), Inches(y), Inches(12.2), Inches(0.5))
            D._set(tf.paragraphs[0], sp["pretext"], 14, D.PRIMARY, bold=True); y += 0.65
        if side == "full":
            D.img_fit(s, F(sp["image"]), Inches(0.5), Inches(y), Inches(12.3), Inches(4.7 if sp.get("banner") else 5.3))
        elif side == "left":
            D.img_fit(s, F(sp["image"]), Inches(0.35), Inches(1.35), Inches(8.9), Inches(5.45))
            D.bullets(s, conv_bullets(sp["bullets"]), Inches(9.35), Inches(1.65), Inches(3.7), Inches(5.0), size=13.5, gap=8)
        else:
            if sp.get("table"):
                tbl = sp["table"]; th = 0.42 * len(tbl)
                tw = 7.4 if sp.get("bullets") else 11.7
                D.table(s, tbl, Inches(0.55), Inches(y), Inches(tw), Inches(th),
                        sizes=12.5, col_w=sp.get("table_col_w"))
                if sp.get("bullets"):
                    D.bullets(s, conv_bullets(sp["bullets"]), Inches(8.25), Inches(y), Inches(4.8), Inches(5.0), size=13.5, gap=7)
                if sp.get("subtext"):
                    _, tf = D.textbox(s, Inches(0.6), Inches(y + th + 0.25), Inches(12), Inches(0.5))
                    D._set(tf.paragraphs[0], sp["subtext"], 13, D.GREY)
            elif sp.get("bullets"):
                D.bullets(s, conv_bullets(sp["bullets"]), Inches(0.6), Inches(y), Inches(12.3), Inches(5.2), size=15.5, gap=9)
        if sp.get("software"):
            D.rect(s, Inches(0.55), Inches(6.45), Inches(12.23), Inches(0.5), D.LIGHT)
            D.rect(s, Inches(0.55), Inches(6.45), Inches(0.1), Inches(0.5), D.ACCENT)
            _, tf = D.textbox(s, Inches(0.78), Inches(6.5), Inches(11.9), Inches(0.42))
            D._set(tf.paragraphs[0], sp["software"], 11.5, D.PRIMARY, bold=True)
        if sp.get("banner"):
            by = 5.95 if side == "full" else 6.05
            D.rect(s, Inches(0.7), Inches(by), Inches(11.9), Inches(0.85), D.LIGHT)
            _, tf = D.textbox(s, Inches(0.95), Inches(by + 0.07), Inches(11.5), Inches(0.7))
            D._set(tf.paragraphs[0], sp["banner"], 14, D.PRIMARY, bold=True)
        add_footer(s); D.notes(s, sp["note"])

out = f"{OUT}/인천공항_변화탐지_발표.pptx"
prs.save(out)
print(f"PPTX 저장: {out}  ({len(prs.slides._sldIdLst)} slides, HAS_LST={C.HAS_LST})")
