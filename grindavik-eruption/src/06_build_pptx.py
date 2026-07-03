# -*- coding: utf-8 -*-
"""발표자료(PPTX) 조립 — content.SLIDES 사양을 렌더."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from common import OUT, FIG
import deck as D
import content as C
from pptx.util import Inches, Pt

D.FOOTER = C.META["footer"]
COL = {"dark": D.DARK, "primary": D.PRIMARY, "accent": D.ACCENT, "accent2": D.ACCENT2, "grey": D.GREY}
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
        D.notes(s, f"발표 시작. 아이슬란드 Grindavík–Sundhnúkur 분화(2023→2025) 전후를 광학·SAR·지표온도 "
                   f"3센서·{C.NM}기법으로 변화탐지. 핵심: 단일 광학지수는 이끼 위상/테프라로 과대추정되며, "
                   f"다중센서 합의로 신규 용암 약 {C.LAVA:.0f}km²를 견고하게 산정.")
    elif t == "toc":
        secs = [(s2["no"], s2["title"]) for s2 in C.SLIDES if s2["type"] == "section"]
        s = D.toc_slide(prs, secs)
        add_footer(s); D.notes(s, sp["note"])
    elif t == "section":
        s = D.section_slide(prs, sp["no"], sp["title"]); add_footer(s)
    elif t == "end":
        s = D.end_slide(prs, C.META["team"], C.META["present_no"], C.META["course"])
        D.notes(s, sp["note"])
    elif t == "content":
        s = D.content_head(prs, sp["kicker"], sp["title"])
        side = sp.get("img_side")
        y = 1.45
        if sp.get("pretext"):
            _, tf = D.textbox(s, Inches(0.55), Inches(y), Inches(12.2), Inches(0.5))
            D._set(tf.paragraphs[0], sp["pretext"], 15, D.PRIMARY, bold=True); y += 0.62
        if side == "full":
            D.img_fit(s, F(sp["image"]), Inches(0.5), Inches(y), Inches(12.3), Inches(4.7 if sp.get("banner") else 5.3))
        elif side == "left":
            D.img_fit(s, F(sp["image"]), Inches(0.35), Inches(1.35), Inches(8.9), Inches(5.45))
            D.bullets(s, conv_bullets(sp["bullets"]), Inches(9.35), Inches(1.6), Inches(3.75), Inches(5.1), size=15, gap=8)
        else:
            if sp.get("table"):
                tbl = sp["table"]; th = 0.46 * len(tbl)
                tw = 7.4 if sp.get("bullets") else 11.7
                D.table(s, tbl, Inches(0.55), Inches(y), Inches(tw), Inches(th), sizes=13.5, col_w=sp.get("table_col_w"))
                if sp.get("bullets"):
                    D.bullets(s, conv_bullets(sp["bullets"]), Inches(8.25), Inches(y), Inches(4.85), Inches(5.0), size=15, gap=7)
                if sp.get("subtext"):
                    _, tf = D.textbox(s, Inches(0.6), Inches(y + th + 0.25), Inches(12), Inches(0.5))
                    D._set(tf.paragraphs[0], sp["subtext"], 14, D.GREY)
            elif sp.get("bullets"):
                # 래핑 포함 줄 수로 자동 축소(긴 불릿이 많으면 dense) — 푸터 침범 방지
                blts = sp["bullets"]
                lines = sum(max(1, -(-len(t[0]) // (62 - t[1] * 6))) for t in blts)
                sz, gp = (15, 6) if (len(blts) > 9 or lines > 11) else (17, 9)
                D.bullets(s, conv_bullets(blts), Inches(0.6), Inches(y), Inches(12.3), Inches(5.2), size=sz, gap=gp)
        if sp.get("software"):
            D.rect(s, Inches(0.55), Inches(6.45), Inches(12.23), Inches(0.5), D.LIGHT)
            D.rect(s, Inches(0.55), Inches(6.45), Inches(0.1), Inches(0.5), D.PRIMARY)
            _, tf = D.textbox(s, Inches(0.78), Inches(6.5), Inches(11.9), Inches(0.42))
            D._set(tf.paragraphs[0], sp["software"], 12.5, D.PRIMARY, bold=True)
        if sp.get("banner"):
            by = 5.95 if side == "full" else 6.05
            D.rect(s, Inches(0.7), Inches(by), Inches(11.9), Inches(0.85), D.LIGHT)
            D.rect(s, Inches(0.7), Inches(by), Inches(0.12), Inches(0.85), D.PRIMARY)
            _, tf = D.textbox(s, Inches(0.95), Inches(by + 0.05), Inches(11.5), Inches(0.75))
            D._set(tf.paragraphs[0], sp["banner"], 15, D.DARK, bold=True)
        add_footer(s); D.notes(s, sp["note"])

out = f"{OUT}/아이슬란드_화산_변화탐지_발표.pptx"
prs.save(out)
print(f"PPTX 저장: {out}  ({len(prs.slides._sldIdLst)} slides)")
