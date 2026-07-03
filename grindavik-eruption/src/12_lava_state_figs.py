# -*- coding: utf-8 -*-
"""잔열 상태 분류 발표 figure — lava_state_real_data_v2.ipynb 산출물의 덱 스타일 렌더링.
· 입력: data/lava_state.tif (0=냉각, 1=잔열, 2=SAR결측), data/lava_state_stats.json
· 출력: figures/fig17_lava_state.png (지도 2패널), figures/fig18_lava_state_eval.png (평가 4패널)
선행: 노트북(캐시 모드) 실행으로 입력 두 파일 생성.
"""
import warnings; warnings.filterwarnings("ignore")
import os, sys, json, numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from common import DATA, FIG, read_tif, target_grid
import viz
from pyproj import Transformer
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch
KF, KB = viz.KFONT, viz.KFONT_B
plt.rcParams["savefig.dpi"] = 200

tr, W, H, b = target_grid(); EXT = [b[0], b[2], b[1], b[3]]
with open(f"{DATA}/lava_state_stats.json", encoding="utf-8") as f:
    S = json.load(f)

s25, _ = read_tif(f"{DATA}/s2_2025.tif"); tc25 = viz.truecolor(s25)
state, _ = read_tif(f"{DATA}/lava_state.tif"); state = np.where(state < -1, np.nan, state)
anom, _ = read_tif(f"{DATA}/lst_anom.tif")
lava = (read_tif(f"{DATA}/consensus_lava.tif")[0] == 1)

ap = S["area_pred"]; al_ = S["area_label"]

# ---- fig17: (a) 잔열 상태 분류  (b) 라벨 근거 ΔLST′ ----
def base(ax, dim=1.0):
    ax.imshow(tc25*dim + (1-dim)*0.15, extent=EXT, origin="upper"); ax.set_aspect("equal")
    viz.add_graticule(ax, EXT, n=3, color="white", label_color="black", alpha=0.5)
    viz.add_north_arrow(ax, color="white"); viz.add_scalebar(ax, EXT, length_km=2)

def mark(ax, x, y, name, dx=120, dy=120):
    ax.scatter([x], [y], s=70, marker="o", facecolor="white", edgecolor="black", lw=1.5, zorder=6)
    ax.text(x+dx, y+dy, name, fontproperties=KF, fontsize=10, color="black",
            path_effects=viz._stroke("white", 2.5), zorder=6)

T = Transformer.from_crs(4326, 32627, always_xy=True)
ASSETS = {"그린다비크 읍": (-22.437, 63.836), "Svartsengi 발전소": (-22.451, 63.881),
          "Sundhnúkur 분화구열": (-22.375, 63.892)}
OFF = {"그린다비크 읍": (200, -550), "Svartsengi 발전소": (-2600, 450), "Sundhnúkur 분화구열": (250, 250)}

fig, ax = plt.subplots(1, 2, figsize=(16, 8.2))

# (a) 분류 지도
base(ax[0])
for v, c, a in [(0, "#fdb863", 0.88), (1, "#d7191c", 0.92), (2, "#9e9e9e", 0.85)]:
    ax[0].imshow(np.where(state == v, 1.0, np.nan), extent=EXT, origin="upper",
                 cmap=ListedColormap([c]), alpha=a, vmin=1, vmax=1, interpolation="nearest")
for nm, (lon, lat) in ASSETS.items():
    x, y = T.transform(lon, lat); mark(ax[0], x, y, nm, *OFF[nm])
ax[0].legend(handles=[
    Patch(fc="#d7191c", label=f"잔열 (배경보다 따뜻)   {ap['hot']:.1f} km²"),
    Patch(fc="#fdb863", label=f"냉각 (배경 수준)   {ap['cold']:.1f} km²"),
    Patch(fc="#9e9e9e", label=f"SAR 결측   {ap['gap']:.1f} km²")],
    loc="lower left", prop=KF, fontsize=10, framealpha=.92)
ax[0].set_title("(a) 잔열 상태 분류 — 광학+SAR 딥러닝 (열은 라벨에만 사용)",
                fontproperties=KB, fontsize=13.5)

# (b) 라벨 근거
base(ax[1], dim=0.55)
im = ax[1].imshow(np.where(lava, anom, np.nan), extent=EXT, origin="upper",
                  cmap="inferno", vmin=0, vmax=7, interpolation="nearest", zorder=2)
cb = fig.colorbar(im, ax=ax[1], shrink=0.62, pad=0.02)
cb.set_label("ΔLST′ 상대승온 (°C)", fontproperties=KF, fontsize=10)
ax[1].text(0.035, 0.97,
           f"약지도 라벨 (합의 용암 {S['consensus_km2']:.1f} km² 내)\n"
           f"· 잔열: ΔLST′ ≥ {S['hot_thr']}°C   ({al_['hot']:.1f} km²)\n"
           f"· 냉각: ΔLST′ < {S['cold_thr']}°C   ({al_['cold']:.1f} km²)\n"
           f"· 모호구간 학습 제외   ({al_['ambig']:.1f} km²)",
           transform=ax[1].transAxes, va="top", ha="left", fontproperties=KF,
           fontsize=10.5, color="#222",
           bbox=dict(boxstyle="round,pad=0.5", fc="white", ec="#d7191c", alpha=0.93))
ax[1].set_title("(b) 라벨 근거 — Landsat ΔLST′ 상대승온", fontproperties=KB, fontsize=13.5)

fig.suptitle("그림 17. 합의 신규 용암의 잔열 상태 — \"얼마나 식었나\" (분출시기 분석과 보완)",
             fontproperties=KB, fontsize=16)
fig.tight_layout(rect=[0, 0.01, 1, 0.95])
fig.savefig(f"{FIG}/fig17_lava_state.png", bbox_inches="tight"); plt.close(fig)
print("저장:", f"{FIG}/fig17_lava_state.png")

# ---- fig18: 평가 4패널 ----
fig, ax = plt.subplots(2, 2, figsize=(14.5, 9))

# (a) 검증 정직성 — 같은 모델, 검증 설계만 변경
hon = sorted(S["honesty"].items())                       # ①②③ 순
met = [("bal_acc", "균형정확도"), ("f1_냉각", "F1(냉각)"), ("auc", "AUC")]
cols = ["#2e7d8f", "#e8a13a", "#c0392b"]
hx = np.arange(len(met))
for i, (name, r) in enumerate(hon):
    vals = [r[m] for m, _ in met]
    bb = ax[0, 0].bar(hx + i*0.27 - 0.27, vals, 0.26, color=cols[i],
                      label=name.split(" · ")[0].replace(" (보고)", "").replace(" (v1 분할방식)", "").replace(" (v1 누수 재현)", ""))
    for x_, v in zip(hx + i*0.27 - 0.27, vals):
        ax[0, 0].text(x_, v + 0.013, f"{v:.2f}", ha="center", fontsize=8.5, fontweight="bold")
ax[0, 0].set_xticks(hx); ax[0, 0].set_xticklabels([k for _, k in met], fontproperties=KF, fontsize=11)
ax[0, 0].axhline(0.5, ls=":", color="0.45", lw=1)
ax[0, 0].text(1.5, 0.515, "더미(전부 잔열)", fontproperties=KF, fontsize=8.5, color="0.35", ha="center")
ax[0, 0].set_ylim(0, 1.12); ax[0, 0].grid(alpha=0.3, axis="y")
ax[0, 0].legend(prop=KF, fontsize=9, loc="upper left")
ax[0, 0].set_title("(a) 검증 설계별 성능 — 랜덤분할·누수가 부풀리는 양",
                   fontproperties=KB, fontsize=12.5)

# (b) 모델 비교 (공간 블록 CV)
order = ["Logistic", "RandomForest", "MLP"]
auc_v = [S["cv_spatial"][m]["auc"] for m in order]
ba_v = [S["cv_spatial"][m]["bal_acc"] for m in order]
bx = np.arange(3)
ax[0, 1].bar(bx - 0.18, auc_v, 0.34, color="#2e7d8f", label="AUC")
ax[0, 1].bar(bx + 0.18, ba_v, 0.34, color="#6b8f71", label="균형정확도")
for x_, v in list(zip(bx - 0.18, auc_v)) + list(zip(bx + 0.18, ba_v)):
    ax[0, 1].text(x_, v + 0.012, f"{v:.3f}", ha="center", fontsize=9, fontweight="bold")
ax[0, 1].set_xticks(bx); ax[0, 1].set_xticklabels(["로지스틱", "랜덤포레스트", "MLP(딥러닝)"],
                                                  fontproperties=KF, fontsize=11)
ax[0, 1].axhline(0.5, ls=":", color="0.45", lw=1)
ax[0, 1].set_ylim(0.4, 1.08); ax[0, 1].grid(alpha=0.3, axis="y")
ax[0, 1].legend(prop=KF, fontsize=10)
ax[0, 1].set_title("(b) 모델 비교 — 공간 블록 5-fold CV", fontproperties=KB, fontsize=12.5)

# (c) 특징 중요도
imp = dict(sorted(S["importance"].items(), key=lambda kv: kv[1]))
ax[1, 0].barh(list(imp.keys()), list(imp.values()), color="#2e7d8f")
ax[1, 0].set_xlabel("AUC 하락량 (permutation)", fontproperties=KF, fontsize=10)
ax[1, 0].grid(alpha=0.3, axis="x")
ax[1, 0].set_title("(c) 특징 중요도 — LST 제외 후 무엇이 잔열을 설명하나",
                   fontproperties=KB, fontsize=12.5)

# (d) 면적 구성 — 라벨 vs 모델 예측
gx = np.arange(2)
ax[1, 1].bar(gx - 0.18, [al_["hot"], al_["cold"]], 0.34, color="#d7191c", label="라벨 (모호 제외)")
ax[1, 1].bar(gx + 0.18, [ap["hot"], ap["cold"]], 0.34, color="#f08c8c", label="모델 예측 (전체 적용)")
for x_, v in [(gx[0]-0.18, al_["hot"]), (gx[1]-0.18, al_["cold"]),
              (gx[0]+0.18, ap["hot"]), (gx[1]+0.18, ap["cold"])]:
    ax[1, 1].text(x_, v + 0.18, f"{v:.1f}", ha="center", fontsize=9.5, fontweight="bold")
ax[1, 1].set_xticks(gx); ax[1, 1].set_xticklabels(["잔열", "냉각"], fontproperties=KF, fontsize=11)
ax[1, 1].set_ylabel("km²", fontproperties=KF)
ax[1, 1].text(0.97, 0.95, f"합의 신규 용암 {S['consensus_km2']:.1f} km²\n"
                          f"(모호 {al_['ambig']:.1f} · SAR결측 {ap['gap']:.1f} km²)",
              transform=ax[1, 1].transAxes, ha="right", va="top", fontproperties=KF,
              fontsize=9.5, bbox=dict(boxstyle="round,pad=0.4", fc="#f5f5f5", ec="0.6"))
ax[1, 1].grid(alpha=0.3, axis="y"); ax[1, 1].legend(prop=KF, fontsize=9.5)
ax[1, 1].set_title("(d) 면적 구성 — 잔열이 지배적", fontproperties=KB, fontsize=12.5)

fig.suptitle("그림 18. 잔열 분류 평가 — 공간 블록 CV 기준 정직 보고 (광학+SAR 특징)",
             fontproperties=KB, fontsize=15.5)
fig.tight_layout(rect=[0, 0.01, 1, 0.95])
fig.savefig(f"{FIG}/fig18_lava_state_eval.png", bbox_inches="tight"); plt.close(fig)
print("저장:", f"{FIG}/fig18_lava_state_eval.png")
