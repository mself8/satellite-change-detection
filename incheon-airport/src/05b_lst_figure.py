# -*- coding: utf-8 -*-
"""LST(지표온도) figure — lst_*.tif 존재 시. (PC 복구 후 실행)

단일영상 절대 LST 비교는 촬영일 기상차 오프셋이 큼 → 의미있는 신호는
(1) 상대온도(anomaly) 변화, (2) 식생 vs 불투수 클래스별 온도대비(기상오프셋에 강건).
이후 06/07 재실행 시 LST 슬라이드 자동 포함.
"""
import warnings; warnings.filterwarnings("ignore")
import os, sys, numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from common import DATA, FIG, read_tif, target_grid
import viz
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt

if not (os.path.exists(f"{DATA}/lst_2017.tif") and os.path.exists(f"{DATA}/lst_2025.tif")):
    print("LST 데이터 없음 — 건너뜀"); sys.exit(0)

tr, W, H, b = target_grid(); EXT = [b[0], b[2], b[1], b[3]]
lst17, _ = read_tif(f"{DATA}/lst_2017.tif"); lst25, _ = read_tif(f"{DATA}/lst_2025.tif")
land, _ = read_tif(f"{DATA}/land_stable.tif"); land = land > 0.5
cls17, _ = read_tif(f"{DATA}/class_2017.tif"); cls25, _ = read_tif(f"{DATA}/class_2025.tif")
valid = land & np.isfinite(lst17) & np.isfinite(lst25)

m17, m25 = np.nanmean(lst17[valid]), np.nanmean(lst25[valid])
anom17 = lst17 - m17; anom25 = lst25 - m25
danom = np.where(valid, anom25 - anom17, np.nan)   # 상대온도 변화 (기상오프셋 제거)

# 클래스별 평균 LST (식생=1, 불투수·나지=2) — 절대값 기준, 연도내 대비
def cmean(lst, cls, k):
    m = valid & (cls == k); return np.nanmean(lst[m]) if m.sum() else np.nan
veg17, imp17 = cmean(lst17, cls17, 1), cmean(lst17, cls17, 2)
veg25, imp25 = cmean(lst25, cls25, 1), cmean(lst25, cls25, 2)
print(f"절대 LST 육지평균: 2017 {m17:.1f}°C, 2025 {m25:.1f}°C (Δ{m25-m17:+.1f}, 기상영향)")
print(f"클래스별 LST(불투수-식생 대비): 2017 {imp17-veg17:+.1f}°C, 2025 {imp25-veg25:+.1f}°C")
np.save(f"{DATA}/lst_classmean.npy", np.array([[veg17, imp17], [veg25, imp25]]))

fig, ax = plt.subplots(1, 3, figsize=(20, 8))
lo = np.nanpercentile(np.r_[lst17[valid], lst25[valid]], 2)
hi = np.nanpercentile(np.r_[lst17[valid], lst25[valid]], 98)
viz.map_panel(ax[0], np.where(land, lst17, np.nan), EXT, "inferno", lo, hi,
              f"(a) 지표온도 2017 (평균 {m17:.1f}°C)", True, "°C", n_grat=3, na_color="white")
viz.map_panel(ax[1], np.where(land, lst25, np.nan), EXT, "inferno", lo, hi,
              f"(b) 지표온도 2025 (평균 {m25:.1f}°C)", True, "°C", n_grat=3, na_color="white")
dv = np.nanpercentile(np.abs(danom[valid]), 98)
viz.map_panel(ax[2], danom, EXT, "coolwarm", -dv, dv,
              "(c) 상대온도 변화 Δanomaly", True, "상대 ΔT (°C)", n_grat=3)
fig.suptitle("그림 11. Landsat 지표온도(LST) — 열환경 (상대온도 기준)",
             fontproperties=viz.KFONT_B, fontsize=15)
fig.savefig(f"{FIG}/fig11_lst.png", bbox_inches="tight", dpi=200); plt.close(fig)
print("fig11_lst 생성 완료 → 06/07 재실행 시 LST 슬라이드 포함")
