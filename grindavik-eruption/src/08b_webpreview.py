# -*- coding: utf-8 -*-
"""fig12_webpreview — 웹맵(08_web.py) UI 목업 프리뷰. 웹 기능 바꾸면 같이 재실행해 동기화."""
import warnings; warnings.filterwarnings("ignore")
import os, sys, json, numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from common import DATA, FIG, read_tif, target_grid, get_stats
import viz
from pyproj import Transformer
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
KF, KB = viz.KFONT, viz.KFONT_B
plt.rcParams["savefig.dpi"] = 200

tr, W, H, b = target_grid(); EXT = [b[0], b[2], b[1], b[3]]
ST = get_stats()
with open(f"{DATA}/lava_state_stats.json", encoding="utf-8") as f:
    LS = json.load(f)
ap = LS["area_pred"]

s25, _ = read_tif(f"{DATA}/s2_2025.tif"); tc25 = viz.truecolor(s25)
state, _ = read_tif(f"{DATA}/lava_state.tif"); state = np.where(state < -1, np.nan, state)
code, _ = read_tif(f"{DATA}/consensus_lava.tif")
land, _ = read_tif(f"{DATA}/land.tif"); land = land > 0.5

T = Transformer.from_crs(4326, 32627, always_xy=True)

# Svartsengi → 최근접 용암 (위험선)
lava_m = (code == 1) & land
rr, cc = np.where(lava_m); xs_ = b[0]+(cc+0.5)*10.0; ys_ = b[3]-(rr+0.5)*10.0
sx, sy = T.transform(-22.451, 63.881)
d = np.hypot(xs_-sx, ys_-sy); k = int(d.argmin())

fig, ax = plt.subplots(figsize=(9.6, 10.6))
ax.imshow(tc25, extent=EXT, origin="upper")
for v, c, a in [(0, "#fdb863", 0.88), (1, "#d7191c", 0.92), (2, "#9e9e9e", 0.8)]:
    ax.imshow(np.where(state == v, 1.0, np.nan), extent=EXT, origin="upper",
              cmap=ListedColormap([c]), alpha=a, vmin=1, vmax=1, interpolation="nearest")
viz.add_graticule(ax, EXT, n=3, color="white", label_color="black", alpha=0.5)
viz.add_north_arrow(ax, x=0.62, color="white"); viz.add_scalebar(ax, EXT, length_km=2)
ax.set_aspect("equal")

# 지물 + 위험선
for nm, lon, lat, dx, dy in [("Sundhnúkur 분화구열", -22.375, 63.892, 200, 250),
                             ("그린다비크", -22.437, 63.836, 200, -550)]:
    x, y = T.transform(lon, lat)
    ax.scatter([x], [y], s=60, facecolor="#ffd400", edgecolor="black", lw=1.4, zorder=6)
    ax.text(x+dx, y+dy, nm, fontproperties=KF, fontsize=9.5, color="white",
            path_effects=viz._stroke("black", 2.5), zorder=6)
ax.scatter([sx], [sy], s=60, facecolor="#ffd400", edgecolor="black", lw=1.4, zorder=6)
ax.plot([sx, xs_[k]], [sy, ys_[k]], color="#ff3030", lw=2.6, dashes=(5, 4), zorder=6)
ax.text(sx-150, sy+260, "Svartsengi 발전소 ── 최근접 용암 14 m", fontproperties=KF, fontsize=9.5,
        color="#ffd2d2", path_effects=viz._stroke("black", 2.5), zorder=7, ha="right")

CARD = dict(boxstyle="round,pad=0.62", fc="#143d59", ec="none", alpha=0.94)

# 타이틀 카드
ax.text(0.022, 0.982,
        "아이슬란드 Grindavík–Sundhnúkur 분화\n"
        "위성 다중센서(광학·SAR·열) 변화탐지 · 2023→2025\n"
        "시점 단축키 0·1·2·3 · P=재생 · 지도 클릭=픽셀 판독",
        transform=ax.transAxes, va="top", ha="left", fontproperties=KB, fontsize=10.5,
        color="white", bbox=CARD, linespacing=1.55, zorder=10)
ax.text(0.022, 0.872, f" 합의 신규 용암 ≈ {ST['lava_km2']:.0f} km² ",
        transform=ax.transAxes, va="top", ha="left", fontproperties=KB, fontsize=9.5,
        color="#06231f", bbox=dict(boxstyle="round,pad=0.42", fc="#2e9e8f", ec="none"), zorder=10)
ax.text(0.245, 0.872, f" 잔열 ≈ {ap['hot']:.0f} km² 잔존 ",
        transform=ax.transAxes, va="top", ha="left", fontproperties=KB, fontsize=9.5,
        color="#06231f", bbox=dict(boxstyle="round,pad=0.42", fc="#e8a13a", ec="none"), zorder=10)

# 우측 패널 카드 (컨트롤 목업)
panel = ("시점 — 광학 트루컬러\n"
         "  ○ 0  끄기 (베이스맵)\n"
         "  ○ 1  2023 분화 전   09-21\n"
         "  ○ 2  2024 분화 중   09-15\n"
         "  ● 3  2025 분화 후   09-18\n"
         "  ▶ 재생  전→중→후 자동\n"
         "──────────────\n"
         "분석 레이어\n"
         "  ● ★ 합의 신규 용암\n"
         "  ● ◆ 잔열 상태 (광학+SAR DL)\n"
         "  ○ ① ΔNDVI  ○ ② ΔVV\n"
         "  ○ ③ ΔLST 이상\n"
         "──────────────\n"
         "  ● 주요 지물  ● 위험도 연결선\n"
         "  투명도 ━━━━━●───")
ax.text(0.978, 0.982, panel, transform=ax.transAxes, va="top", ha="right",
        fontproperties=KF, fontsize=9, color="#eef3f5", bbox=CARD, linespacing=1.62, zorder=10)

# 클릭 팝업 목업 (용암 중심)
px, py = T.transform(-22.364, 63.895)
ax.scatter([px], [py], s=130, facecolor="none", edgecolor="white", lw=2.2, zorder=8)
ax.scatter([px], [py], s=12, facecolor="white", edgecolor="none", zorder=8)
pop = ("픽셀 판독  (63.8950°N, 22.3640°W)\n"
       "  광학 ΔNDVI        -0.39\n"
       "  SAR ΔVV          +2.7 dB\n"
       "  열 ΔLST          +7.1 °C\n"
       "  모델 추정(광학+SAR)  잔열")
bx, by = 0.052, 0.435
ax.annotate("", xy=(px, py), xytext=(bx+0.21, by-0.052), textcoords="axes fraction",
            arrowprops=dict(arrowstyle="-", color="white", lw=1.6), zorder=9)
ax.text(bx, by, pop, transform=ax.transAxes, va="top", ha="left", fontproperties=KF,
        fontsize=9.3, color="#1c2b33",
        bbox=dict(boxstyle="round,pad=0.55", fc="white", ec="#9fb6bd", lw=1), linespacing=1.6, zorder=10)
ax.text(bx+0.012, by-0.155, " 다중센서 합의 용암 · 잔열 ", transform=ax.transAxes, va="top",
        ha="left", fontproperties=KB, fontsize=9, color="white",
        bbox=dict(boxstyle="round,pad=0.38", fc="#d7191c", ec="none"), zorder=10)

# 범례 카드 (좌하단, 축척 위)
leg = ("범례\n"
       f"  잔열(따뜻) {ap['hot']:.1f} km²\n"
       f"  냉각(배경수준) {ap['cold']:.1f} km²\n"
       f"  SAR 결측 {ap['gap']:.1f} km²")
ax.text(0.022, 0.175, leg, transform=ax.transAxes, va="top", ha="left", fontproperties=KF,
        fontsize=8.8, color="#eef3f5", bbox=CARD, linespacing=1.55, zorder=10)
for i, c in enumerate(["#d7191c", "#fdb863", "#9e9e9e"]):
    ax.add_patch(plt.Rectangle((0.034, 0.175-0.043-i*0.0265), 0.016, 0.013,
                               transform=ax.transAxes, fc=c, ec="none", zorder=11))

ax.set_title("인터랙티브 웹맵 — 시점 전환 · 클릭 픽셀 판독 · 잔열/위험도 레이어 (시연)",
             fontproperties=KB, fontsize=13.5, pad=9)
fig.tight_layout()
fig.savefig(f"{FIG}/fig12_webpreview.png", bbox_inches="tight"); plt.close(fig)
print("저장:", f"{FIG}/fig12_webpreview.png")
