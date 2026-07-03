# -*- coding: utf-8 -*-
"""위험도 분석 — ① 용암 생성시기(recency) + ② 자산 근접 위험도.
· recency: 2025 합의용암을 2024 SWIR 어두움으로 구/신 분리 (용암 어두움이 이끼 위상에 안 속음)
· proximity: 그린다비크·Svartsengi·블루라군 → 최근접 용암 거리(m)
출력: data/lava_recency.tif, figures/fig15_hazard.png, stats.json 갱신
"""
import warnings; warnings.filterwarnings("ignore")
import os, sys, numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from common import DATA, FIG, read_tif, write_tif, target_grid, get_stats, put_stats
import viz
from pyproj import Transformer
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.patches import Patch
KF, KB = viz.KFONT, viz.KFONT_B
plt.rcParams["savefig.dpi"] = 200

tr, W, H, b = target_grid(); EXT = [b[0], b[2], b[1], b[3]]; PX = 100/1e6
THR = 0.06  # SWIR1 < THR => 용암처럼 어두움

s25, _ = read_tif(f"{DATA}/s2_2025.tif"); tc25 = viz.truecolor(s25)
sw24 = read_tif(f"{DATA}/s2_2024.tif")[0][4]
land = read_tif(f"{DATA}/land.tif")[0] > 0.5
code = read_tif(f"{DATA}/consensus_lava.tif")[0]
lava = (code == 1) & land

v24 = np.where(np.isfinite(sw24), sw24, 1.0)
old = lava & (v24 < THR)     # ~2024 생성 (구)
new = lava & (v24 >= THR)    # 2024->2025 생성 (최신)
old_km2, new_km2 = old.sum()*PX, new.sum()*PX
print(f"구용암(~2024) {old_km2:.2f} km2  |  최신용암(2024->2025) {new_km2:.2f} km2")

rec = np.zeros((H, W), "float32"); rec[old] = 1; rec[new] = 2
write_tif(f"{DATA}/lava_recency.tif", rec, tr, nodata=0)

# ② 근접 위험도
T = Transformer.from_crs(4326, 32627, always_xy=True)
ASSETS = {"그린다비크 읍": (-22.437, 63.836), "Svartsengi 발전소": (-22.451, 63.881),
          "블루라군": (-22.449, 63.880)}
rr, cc = np.where(lava); xs = b[0]+(cc+0.5)*10; ys = b[3]-(rr+0.5)*10
prox = {}
for nm, (lon, lat) in ASSETS.items():
    ax_, ay_ = T.transform(lon, lat)
    d = np.sqrt((xs-ax_)**2+(ys-ay_)**2); k = int(d.argmin())
    prox[nm] = {"asset": (ax_, ay_), "near": (float(xs[k]), float(ys[k])), "dist": float(d[k])}
    print(f"  {nm:16s}: {d[k]:6.0f} m")

put_stats(lava_old_km2=round(float(old_km2), 2), lava_new_km2=round(float(new_km2), 2),
          recency_swir_thr=THR,
          dist_grindavik_m=round(prox["그린다비크 읍"]["dist"]),
          dist_svartsengi_m=round(prox["Svartsengi 발전소"]["dist"]),
          dist_bluelagoon_m=round(prox["블루라군"]["dist"]))

# ---- figure: (a) 생성시기  (b) 근접 위험도 ----
def base(ax, dim=1.0):
    ax.imshow(tc25*dim + (1-dim), extent=EXT, origin="upper"); ax.set_aspect("equal")
    viz.add_graticule(ax, EXT, n=3, color="white", label_color="black", alpha=0.5)
    viz.add_north_arrow(ax, color="white"); viz.add_scalebar(ax, EXT, length_km=2)

def mark(ax, x, y, name, dx=120, dy=120):
    ax.scatter([x], [y], s=70, marker="o", facecolor="white", edgecolor="black", lw=1.5, zorder=6)
    ax.text(x+dx, y+dy, name, fontproperties=KF, fontsize=10, color="black",
            path_effects=viz._stroke("white", 2.5), zorder=6)

OFF = {"그린다비크 읍": (200, -550), "Svartsengi 발전소": (-2000, 450), "블루라군": (250, -650)}
o = np.where(old, 1.0, np.nan); n = np.where(new, 1.0, np.nan)
C_OLD = matplotlib.colors.ListedColormap(["#fdb863"]); C_NEW = matplotlib.colors.ListedColormap(["#d7191c"])
fig, ax = plt.subplots(1, 2, figsize=(16, 8.2))

# (a) 생성시기
base(ax[0])
ax[0].imshow(o, extent=EXT, origin="upper", cmap=C_OLD, alpha=0.85, vmin=1, vmax=1)
ax[0].imshow(n, extent=EXT, origin="upper", cmap=C_NEW, alpha=0.92, vmin=1, vmax=1)
for nm, p in prox.items():
    mark(ax[0], *p["asset"], nm, *OFF[nm])
ax[0].legend(handles=[Patch(fc="#fdb863", label=f"구 용암 (~2024)   {old_km2:.1f} km²"),
                      Patch(fc="#d7191c", label=f"최신 용암 (2024→2025)   {new_km2:.1f} km²")],
             loc="lower left", prop=KF, fontsize=10, framealpha=.92)
ax[0].set_title("(a) 용암 생성시기 — SWIR 기반 구/신 분리", fontproperties=KB, fontsize=14)

# (b) 근접 위험도
base(ax[1], dim=0.6)
ax[1].imshow(o, extent=EXT, origin="upper", cmap=C_OLD, alpha=0.5, vmin=1, vmax=1)
ax[1].imshow(n, extent=EXT, origin="upper", cmap=C_NEW, alpha=0.6, vmin=1, vmax=1)
for nm, p in prox.items():
    (axx, ayy), (nx, ny), d = p["asset"], p["near"], p["dist"]
    crit = d < 200
    ax[1].plot([axx, nx], [ayy, ny], color=("#d7191c" if crit else "#1a9850"), lw=2.4, zorder=5)
    mark(ax[1], axx, ayy, nm, *OFF[nm])
def km(d): return f"{d:.0f} m" if d < 1000 else f"{d/1000:.1f} km"
boxtxt = ("최근접 용암까지 거리\n"
          f"· Svartsengi 발전소  {km(prox['Svartsengi 발전소']['dist'])}  (위험)\n"
          f"· 블루라군  {km(prox['블루라군']['dist'])}  (위험)\n"
          f"· 그린다비크 읍  {km(prox['그린다비크 읍']['dist'])}")
ax[1].text(0.035, 0.97, boxtxt, transform=ax[1].transAxes, va="top", ha="left",
           fontproperties=KF, fontsize=11, color="#222",
           bbox=dict(boxstyle="round,pad=0.5", fc="white", ec="#d7191c", alpha=0.93))
ax[1].set_title("(b) 자산 근접 위험도 — 최근접 용암까지 거리", fontproperties=KB, fontsize=14)

fig.suptitle("그림 15. 위험도 분석 — 용암 생성시기와 자산 근접도", fontproperties=KB, fontsize=16)
fig.tight_layout(rect=[0, 0.01, 1, 0.95])
fig.savefig(f"{FIG}/fig15_hazard.png", bbox_inches="tight"); plt.close(fig)
print("fig15_hazard 저장:", f"{FIG}/fig15_hazard.png")
