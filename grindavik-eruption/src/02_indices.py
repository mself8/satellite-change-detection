"""분광지수(NDVI·NBR·NDWI) 및 시기 차분 — Grindavík/Sundhnúkur 분화 변화탐지.

밴드순: 0=Blue 1=Green 2=Red 3=NIR 4=SWIR1(B11) 5=SWIR2(B12)
분화 전(2023-09)·중(2024-09)·후(2025-09) 3시기. 정량비교는 전(2023)↔후(2025) 중심.
용암은 무식생·저알베도·거친 표면 → NDVI↓, NBR↓, 알베도↓ 로 포착.
"""
import warnings; warnings.filterwarnings("ignore")
import os, sys, numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from common import DATA, read_tif, write_tif, target_grid, put_stats

transform, W, H, bounds = target_grid()
B, G, R, NIR, SW1, SW2 = range(6)
PX = 100/1e6  # km²/픽셀


def indices(s):
    g, r, nir, sw1, sw2 = s[G], s[R], s[NIR], s[SW1], s[SW2]
    eps = 1e-6
    ndvi = (nir - r) / (nir + r + eps)
    nbr = (nir - sw2) / (nir + sw2 + eps)          # 소실/연소(용암 매몰)지수: 식생·이끼 높음, 용암 낮음
    ndwi = (g - nir) / (g + nir + eps)             # 수체
    albedo = s[:4].mean(0)                          # 가시+NIR 밝기 (용암=저알베도)
    return ndvi, nbr, ndwi, albedo


S = {yr: read_tif(f"{DATA}/s2_{yr}.tif")[0] for yr in ("2023", "2024", "2025")}
IDX = {yr: indices(S[yr]) for yr in S}
ndvi23, nbr23, ndwi23, alb23 = IDX["2023"]
ndvi25, nbr25, ndwi25, alb25 = IDX["2025"]

# 마스크: 물(둘 중 한 해라도 수체) / 육지
water = (ndwi25 > 0.1) | (ndwi23 > 0.1)
land = ~water
write_tif(f"{DATA}/land.tif", land.astype("float32"), transform, nodata=0)

# 시기별 지수 + 전후 차분 저장
for yr in S:
    nd, nb, nw, al = IDX[yr]
    write_tif(f"{DATA}/ndvi_{yr}.tif", nd, transform)
    write_tif(f"{DATA}/nbr_{yr}.tif", nb, transform)
    write_tif(f"{DATA}/albedo_{yr}.tif", al, transform)
write_tif(f"{DATA}/d_ndvi.tif", (ndvi25 - ndvi23).astype("float32"), transform)
write_tif(f"{DATA}/d_nbr.tif", (nbr25 - nbr23).astype("float32"), transform)
write_tif(f"{DATA}/d_albedo.tif", (alb25 - alb23).astype("float32"), transform)

# ---- 통계 ----
print(f"프레임 {W}x{H}@10m = {W*H*PX:.1f} km²  | 육지 {land.sum()*PX:.1f}  물 {water.sum()*PX:.1f} km²")
ndvi_mean = {}
for yr in S:
    nd = IDX[yr][0]
    ndvi_mean[yr] = float(np.nanmean(nd[land]))
    print(f"NDVI {yr}: 육지평균 {ndvi_mean[yr]:+.3f}  식생화소(>0.3) {(nd[land]>0.3).mean()*100:.1f}%")
dN = ndvi25 - ndvi23
print(f"ΔNDVI(25-23) 육지: 감소(<-0.1) {(dN[land]<-0.1).mean()*100:.1f}%  증가(>0.1) {(dN[land]>0.1).mean()*100:.1f}%")

put_stats(
    frame_km2=round(W*H*PX, 1), land_km2=round(land.sum()*PX, 1), water_km2=round(water.sum()*PX, 1),
    ndvi_mean=ndvi_mean,
    ndvi_dec_pct=round((dN[land] < -0.1).mean()*100, 1),
    ndvi_inc_pct=round((dN[land] > 0.1).mean()*100, 1),
    dates={"2023": open(f"{DATA}/s2_2023.date").read().strip(),
           "2024": "2024-09-15",
           "2025": open(f"{DATA}/s2_2025.date").read().strip()},
)
print("지수·차분·마스크 저장 완료.")
