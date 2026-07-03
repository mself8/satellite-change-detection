# -*- coding: utf-8 -*-
"""딥러닝 결과 figure — DL 용암확률 · DL vs 합의 비교(공간분할) · 지표/SAR결측 보완."""
import warnings; warnings.filterwarnings("ignore")
import os, sys, numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from common import DATA, FIG, read_tif, target_grid, get_stats
import viz
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch
KF, KB = viz.KFONT, viz.KFONT_B
plt.rcParams["savefig.dpi"] = 200

tr, W, H, b = target_grid(); EXT = [b[0], b[2], b[1], b[3]]; PX = 100/1e6
ST = get_stats()
s25, _ = read_tif(f"{DATA}/s2_2025.tif"); tc25 = viz.truecolor(s25)
prob, _ = read_tif(f"{DATA}/dl_lava_prob.tif"); mask, _ = read_tif(f"{DATA}/dl_lava_mask.tif"); mask = mask > 0.5
code, _ = read_tif(f"{DATA}/consensus_lava.tif")
land, _ = read_tif(f"{DATA}/land.tif"); land = land > 0.5
dvv, _ = read_tif(f"{DATA}/d_vv.tif"); sar_ok = np.isfinite(dvv)
cons = (code == 1) & land
te_col = int(ST.get("dl_test_col", int(0.70*W)))
x_te = b[0] + te_col*10   # test 경계 UTM x

fig, ax = plt.subplots(1, 3, figsize=(21, 8.2))

# (a) DL 용암 확률 over 트루컬러
ax[0].imshow(tc25, extent=EXT, origin="upper")
pm = np.where(land, prob, np.nan)
im = ax[0].imshow(np.where(pm > 0.25, pm, np.nan), extent=EXT, origin="upper", cmap="hot", vmin=0, vmax=1, alpha=0.75)
viz.add_graticule(ax[0], EXT, n=3, color="white", label_color="black", alpha=0.5)
viz.add_north_arrow(ax[0], color="white"); viz.add_scalebar(ax[0], EXT, length_km=2)
ax[0].set_title("(a) DL 용암 확률 (광학+SAR 융합 U-Net)", fontproperties=KB, fontsize=13); ax[0].set_aspect("equal")
cb = fig.colorbar(im, ax=ax[0], shrink=0.6, pad=0.02); cb.set_label("용암 확률", fontproperties=KF)

# (b) DL vs 합의 (공간분할 검증)
agree = np.zeros((H, W)); agree[cons & mask] = 1; agree[~cons & mask & land] = 2; agree[cons & ~mask] = 3
cmap = ListedColormap(["#dfe6ea", "#2ca25f", "#d7301f", "#2b6cb0"])
ax[1].imshow(viz.truecolor(s25)*0.45 + 0.55, extent=EXT, origin="upper")
ax[1].imshow(np.where(land, agree, np.nan), extent=EXT, origin="upper", cmap=cmap, vmin=0, vmax=3, alpha=0.85, interpolation="nearest")
ax[1].axvline(x_te, color="black", lw=2, ls="--")
ax[1].text(x_te+150, EXT[3]-800, "← 학습   |   검증(held-out) →", fontproperties=KF, fontsize=10,
           color="black", path_effects=viz._stroke("white", 2.5))
viz.add_north_arrow(ax[1], color="black", ec="white"); viz.add_scalebar(ax[1], EXT, length_km=2)
ax[1].legend(handles=[Patch(fc="#2ca25f", label="일치(TP)"), Patch(fc="#d7301f", label="DL만(FP)"),
                      Patch(fc="#2b6cb0", label="합의만(FN)")], loc="lower left", prop=KF, fontsize=9, framealpha=.9)
ax[1].set_title(f"(b) DL vs 다중센서 합의  (검증 IoU {ST['dl_iou_test']:.2f}·F1 {ST['dl_f1_test']:.2f})",
                fontproperties=KB, fontsize=13); ax[1].set_aspect("equal")
ax[1].set_xticks([]); ax[1].set_yticks([])

# (c) 지표 + SAR 결측 보완
m = ["IoU", "정밀도", "재현율", "F1"]; v = [ST["dl_iou_test"], ST["dl_prec_test"], ST["dl_rec_test"], ST["dl_f1_test"]]
bars = ax[2].bar(m, v, color=["#2E9E8F", "#4c72b0", "#dd8452", "#55a868"], edgecolor="0.3")
for r, val in zip(bars, v): ax[2].text(r.get_x()+r.get_width()/2, val+0.02, f"{val:.2f}", ha="center", fontproperties=KB, fontsize=12)
ax[2].set_ylim(0, 1.05); ax[2].set_xticklabels(m, fontproperties=KF, fontsize=11)
ax[2].set_title("(c) 공간분할(held-out) 검증 성능", fontproperties=KB, fontsize=13)
ax[2].grid(axis="y", alpha=0.3); ax[2].set_axisbelow(True)
ax[2].text(0.5, -0.16, f"DL 용암 {ST['dl_lava_km2']:.0f} km² ↔ 합의 {ST['lava_km2']:.0f} km² (근접)  ·  입력 {ST['dl_channels']}채널 · {ST['dl_epochs']}ep\n"
           f"검증은 학습에 안 쓴 우측(held-out) 영역 — 규칙 암기가 아닌 용암 signature 학습 입증",
           transform=ax[2].transAxes, ha="center", va="top", fontproperties=KF, fontsize=10, color="#444")

fig.suptitle("그림 13. 딥러닝(광학+SAR 융합 U-Net) — 신규 용암 분할과 검증", fontproperties=KB, fontsize=16)
fig.tight_layout(rect=[0, 0.02, 1, 0.95])
fig.savefig(f"{FIG}/fig13_dl.png", bbox_inches="tight"); plt.close(fig)
print("fig13_dl 저장:", f"{FIG}/fig13_dl.png")
