# -*- coding: utf-8 -*-
"""딥러닝 학습곡선 + 검증 성능표 — fig14_dl_curve.png
(a) 손실곡선  (b) IoU 학습 vs 검증(과적합 점검)  (c) 학습/검증/전체 성능표 + AUC·PR-AUC."""
import warnings; warnings.filterwarnings("ignore")
import os, sys, json, numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from common import DATA, FIG, get_stats
import viz
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
KF, KB = viz.KFONT, viz.KFONT_B
plt.rcParams["savefig.dpi"] = 200

H = json.load(open(f"{DATA}/dl_history.json")); S = get_stats()
ep, loss, tri, tei = H["epoch"], H["loss"], H["train_iou"], H["test_iou"]
best = int(np.argmax(tei))

fig = plt.figure(figsize=(15, 9))
gs = fig.add_gridspec(2, 2, height_ratios=[1.25, 0.9], hspace=0.34, wspace=0.22)

# (a) 손실곡선
axL = fig.add_subplot(gs[0, 0])
axL.plot(ep, loss, "-o", color="#c0392b", ms=3.5, lw=1.8)
axL.set_xlabel("epoch", fontproperties=KF); axL.set_ylabel("loss (BCE+Dice)", fontproperties=KF)
axL.set_title("(a) 학습 손실곡선", fontproperties=KB, fontsize=13)
axL.grid(alpha=0.3); axL.set_axisbelow(True)

# (b) IoU 학습 vs 검증
axI = fig.add_subplot(gs[0, 1])
axI.plot(ep, tri, "-o", color="#4c72b0", ms=3.5, lw=1.8, label="학습영역 IoU")
axI.plot(ep, tei, "-o", color="#2ca25f", ms=3.5, lw=1.8, label="검증(held-out) IoU")
axI.axvline(ep[best], color="0.55", ls="--", lw=1)
axI.annotate(f"best {tei[best]:.2f} @ep{ep[best]}", (ep[best], tei[best]),
             xytext=(6, -26), textcoords="offset points", fontproperties=KF, fontsize=9, color="#1b5e20")
axI.set_ylim(0.5, 1.0); axI.set_xlabel("epoch", fontproperties=KF); axI.set_ylabel("IoU", fontproperties=KF)
axI.set_title("(b) IoU 곡선 — 학습영역 vs 검증영역", fontproperties=KB, fontsize=13)
axI.legend(prop=KF, fontsize=10, loc="lower right"); axI.grid(alpha=0.3); axI.set_axisbelow(True)
axI.text(0.03, 0.97, "검증>학습: 주 용암체가 검증영역에 위치 → 과적합 아님",
         transform=axI.transAxes, fontproperties=KF, fontsize=8.5, color="#555", va="top")

# (c) 성능표
axT = fig.add_subplot(gs[1, :]); axT.axis("off")
axT.set_title("(c) 공간분할(held-out) 검증 성능표", fontproperties=KB, fontsize=13, y=1.0)
cols = ["영역", "패치수", "IoU", "정밀도", "재현율", "F1"]
rows = [
    ["학습 (train)",    f"{S['dl_train_patches']}", f"{S['dl_iou_train']:.2f}", f"{S['dl_prec_train']:.2f}", f"{S['dl_rec_train']:.2f}", f"{S['dl_f1_train']:.2f}"],
    ["검증 (held-out)", f"{S['dl_test_patches']}",  f"{S['dl_iou_test']:.2f}",  f"{S['dl_prec_test']:.2f}",  f"{S['dl_rec_test']:.2f}",  f"{S['dl_f1_test']:.2f}"],
    ["전체 장면",       "-",                          f"{S['dl_iou_all']:.2f}",   f"{S['dl_prec_all']:.2f}",   f"{S['dl_rec_all']:.2f}",   f"{S['dl_f1_all']:.2f}"],
]
tbl = axT.table(cellText=rows, colLabels=cols, cellLoc="center", bbox=[0.12, 0.34, 0.76, 0.58])
tbl.auto_set_font_size(False); tbl.set_fontsize(11)
for (r, c), cell in tbl.get_celld().items():
    cell.set_edgecolor("white"); cell.set_linewidth(1.2)
    if r == 0:
        cell.set_facecolor("#2E6E8E"); cell.set_text_props(color="white", fontproperties=KB)
    else:
        cell.set_text_props(fontproperties=(KB if c == 0 else KF))
        if rows[r-1][0].startswith("검증"): cell.set_facecolor("#e3f1e6")
        elif r % 2 == 0: cell.set_facecolor("#f3f6f8")
auc = S.get("dl_auc_test", float("nan")); ap = S.get("dl_ap_test", float("nan"))
axT.text(0.5, 0.18,
         f"라벨 = 다중센서 합의(약지도)   ·   검증 ROC-AUC {auc:.3f} · PR-AUC {ap:.3f}   ·   "
         f"DL 용암 {S['dl_lava_km2']:.0f} km² ≈ 합의 {S['lava_km2']:.0f} km²",
         transform=axT.transAxes, ha="center", va="top", fontproperties=KB, fontsize=10.5, color="#222")
axT.text(0.5, 0.07,
         f"입력 {S['dl_channels']}채널(광학+SAR) · U-Net 1.9M · {S['dl_epochs']} epoch · 손실 BCE+Dice · 임계 0.5"
         "   |   검증은 학습에 안 쓴 우측(held-out) 영역",
         transform=axT.transAxes, ha="center", va="top", fontproperties=KF, fontsize=9.5, color="#666")

fig.suptitle("그림 14. 딥러닝(광학+SAR U-Net) — 학습곡선과 검증 성능", fontproperties=KB, fontsize=16)
fig.tight_layout(rect=[0, 0.01, 1, 0.95])
fig.savefig(f"{FIG}/fig14_dl_curve.png", bbox_inches="tight"); plt.close(fig)
print("fig14_dl_curve 저장:", f"{FIG}/fig14_dl_curve.png")
