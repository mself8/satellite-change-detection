# -*- coding: utf-8 -*-
"""Modified U-Net(3-encoder 회귀) 결과 figure — fig16.
(a) 예측 용암도 맵  (b) 타깃 vs 예측 산점도(R, held-out; 교수님 Fig.8b 대응)  (c) 학습곡선+성능."""
import warnings; warnings.filterwarnings("ignore")
import os, sys, json, numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from common import DATA, FIG, read_tif, target_grid, get_stats
import viz
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
KF, KB = viz.KFONT, viz.KFONT_B
plt.rcParams["savefig.dpi"] = 200

tr, W, H, b = target_grid(); EXT = [b[0], b[2], b[1], b[3]]
S = get_stats(); HIS = json.load(open(f"{DATA}/dl3_history.json"))
s25 = read_tif(f"{DATA}/s2_2025.tif")[0]; tc = viz.truecolor(s25)
pred = read_tif(f"{DATA}/dl3_degree.tif")[0]
tgt = read_tif(f"{DATA}/lava_degree.tif")[0]
land = read_tif(f"{DATA}/land.tif")[0] > 0.5
te_col = int(S.get("dl3_test_col", int(0.70*W)))

fig, ax = plt.subplots(1, 3, figsize=(21, 7.4))

# (a) 예측 용암도
ax[0].imshow(tc, extent=EXT, origin="upper")
pm = np.where(land & (pred > 0.1), pred, np.nan)
im = ax[0].imshow(pm, extent=EXT, origin="upper", cmap="inferno", vmin=0, vmax=1, alpha=0.85)
viz.add_graticule(ax[0], EXT, n=3, color="white", label_color="black", alpha=0.5)
viz.add_north_arrow(ax[0], color="white"); viz.add_scalebar(ax[0], EXT, length_km=2)
ax[0].set_aspect("equal"); ax[0].set_title("(a) 예측 용암 변화강도 (3-encoder Modified U-Net)", fontproperties=KB, fontsize=13)
cb = fig.colorbar(im, ax=ax[0], shrink=0.6, pad=0.02); cb.set_label("용암도 (0~1)", fontproperties=KF)

# (b) 타깃 vs 예측 산점도 (held-out) — 교수님 Fig.8b 대응
reg = land & (np.arange(W)[None, :] >= te_col) & np.isfinite(pred)
xt = tgt[reg]; yp = pred[reg]
rs = np.random.RandomState(0); idx = rs.choice(xt.size, min(6000, xt.size), replace=False)
ax[1].scatter(xt[idx], yp[idx], s=5, alpha=0.25, color="#2c7fb8", edgecolors="none")
ax[1].plot([0, 1], [0, 1], "--", color="0.4", lw=1.2)
ax[1].set_xlim(0, 1.05); ax[1].set_ylim(0, 1.05); ax[1].set_aspect("equal")
ax[1].set_xlabel("타깃 용암도 (GT)", fontproperties=KF); ax[1].set_ylabel("예측 용암도", fontproperties=KF)
ax[1].text(0.04, 0.96, f"Pearson R = {S['dl3_r_test']:.3f}\nMAE = {S['dl3_mae_test']:.3f}\nRMSE = {S['dl3_rmse_test']:.3f}",
           transform=ax[1].transAxes, va="top", ha="left", fontproperties=KB, fontsize=12,
           bbox=dict(boxstyle="round", fc="white", alpha=0.85))
ax[1].set_title("(b) 타깃 vs 예측 (held-out 픽셀별)", fontproperties=KB, fontsize=13); ax[1].grid(alpha=0.3)

# (c) 학습곡선 — 원자료(연한 선)+7ep 이동평균(굵은 선): 발표 가독성, 원자료도 정직하게 유지
ep = HIS["epoch"]
def smooth(v, k=7):
    v = np.asarray(v, float); kern = np.ones(k)
    return np.convolve(v, kern, "same") / np.convolve(np.ones_like(v), kern, "same")
ax[2].plot(ep, HIS["loss"], lw=0.9, color="#c0392b", alpha=0.28)
ax[2].plot(ep, HIS["test_mae"], lw=0.9, color="#2ca25f", alpha=0.28)
ax[2].plot(ep, smooth(HIS["loss"]), lw=2.4, color="#c0392b", label="학습 손실 (MAE)")
ax[2].plot(ep, smooth(HIS["test_mae"]), lw=2.4, color="#2ca25f", label="검증 MAE (held-out)")
ax[2].set_xlabel("epoch", fontproperties=KF); ax[2].set_ylabel("MAE", fontproperties=KF)
ax[2].legend(prop=KF, fontsize=10, title="굵은 선 = 7ep 이동평균 · 연한 선 = 원자료",
             title_fontproperties=KF); ax[2].grid(alpha=0.3); ax[2].set_axisbelow(True)
ax[2].set_title("(c) 학습곡선 (MAE 손실)", fontproperties=KB, fontsize=13)
ax[2].text(0.5, -0.18,
           f"held-out 분할(임계0.5): IoU {S['dl3_iou_test']:.2f}·F1 {S['dl3_f1_test']:.2f}  ·  DL3 용암 {S['dl3_area_km2']:.0f} km² (합의 {S['lava_km2']:.0f})\n"
           f"3-encoder {S['dl3_cins']}({sum(S['dl3_cins'])}ch) · {S['dl3_params_m']}M · NAdam·MAE·ReLU출력 · {S['dl3_epochs']}ep  (이어루 외 2022 구조 준수)",
           transform=ax[2].transAxes, ha="center", va="top", fontproperties=KF, fontsize=9.5, color="#555")

fig.suptitle("그림 16. Modified U-Net 3-encoder 확장 (이어루 외 2022 기반) — 용암 변화강도 회귀", fontproperties=KB, fontsize=16)
fig.tight_layout(rect=[0, 0.02, 1, 0.95])
fig.savefig(f"{FIG}/fig16_modunet.png", bbox_inches="tight"); plt.close(fig)
print("fig16_modunet 저장:", f"{FIG}/fig16_modunet.png")
