# -*- coding: utf-8 -*-
"""슬라이드용 결과 figure 생성. 모든 결과맵에 north arrow·scale bar·grid 포함.

내러티브: 분화 전→후 용암류 확장을 광학·SAR·열 다중센서로 교차탐지.
핵심 figure = 다중센서 합의 신규 용암 (단일지수 과대추정 대비).
"""
import warnings; warnings.filterwarnings("ignore")
import os, sys, numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from common import DATA, FIG, read_tif, target_grid, get_stats
import viz
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, LinearSegmentedColormap
from matplotlib.patches import Rectangle, Patch
from pyproj import Transformer
KF, KB = viz.KFONT, viz.KFONT_B
plt.rcParams["savefig.dpi"] = 200

tr, W, H, b = target_grid()
EXT = [b[0], b[2], b[1], b[3]]
B, G, R, NIR, SW1, SW2 = range(6)
ST = get_stats()
TO_UTM = Transformer.from_crs("EPSG:4326", "EPSG:32627", always_xy=True)

# ---- load ----
s23, _ = read_tif(f"{DATA}/s2_2023.tif"); s24, _ = read_tif(f"{DATA}/s2_2024.tif"); s25, _ = read_tif(f"{DATA}/s2_2025.tif")
ndvi23, _ = read_tif(f"{DATA}/ndvi_2023.tif"); ndvi25, _ = read_tif(f"{DATA}/ndvi_2025.tif")
dN, _ = read_tif(f"{DATA}/d_ndvi.tif")
cls23, _ = read_tif(f"{DATA}/class_2023.tif"); cls25, _ = read_tif(f"{DATA}/class_2025.tif")
mag, _ = read_tif(f"{DATA}/cva_magnitude.tif"); pca1, _ = read_tif(f"{DATA}/pca_change.tif")
dvv, _ = read_tif(f"{DATA}/d_vv.tif"); anom, _ = read_tif(f"{DATA}/lst_anom.tif")
lst23, _ = read_tif(f"{DATA}/lst_2023.tif"); lst25, _ = read_tif(f"{DATA}/lst_2025.tif")
code, _ = read_tif(f"{DATA}/consensus_lava.tif")
land, _ = read_tif(f"{DATA}/land.tif"); land = land > 0.5
tc23, tc24, tc25 = viz.truecolor(s23), viz.truecolor(s24), viz.truecolor(s25)
fc25 = viz.falsecolor(s25)
area = np.array([ST["class_area"]["2023"], ST["class_area"]["2025"]])
pca_var = np.array(ST["pca_var"])

CLS_CMAP = ListedColormap(["#2c7fb8", "#41ab5d", "#8c6d4f"]); CLS_LAB = ["수역", "식생·이끼", "나지·용암"]
NDVI_CMAP = LinearSegmentedColormap.from_list("ndvi", ["#8c510a", "#d8b365", "#f6e8c3", "#c7e9b4", "#41ab5d", "#005a32"])
LMARKS = [("그린다비크(읍)", -22.437, 63.836), ("블루라군·Svartsengi", -22.449, 63.880),
          ("Sundhnúkur 분화구열", -22.375, 63.892), ("Þorbjörn", -22.443, 63.861)]


def marks(ax, names=None, color="white", fs=9.0, dy=7):
    for nm, lon, lat in LMARKS:
        if names is not None and nm not in names: continue
        x, y = TO_UTM.transform(lon, lat)
        if not (EXT[0] < x < EXT[1] and EXT[2] < y < EXT[3]): continue
        ax.plot(x, y, "o", ms=4.5, mfc="#ffd400", mec="black", mew=0.8, zorder=12)
        ax.annotate(nm, (x, y), xytext=(0, dy), textcoords="offset points", ha="center",
                    fontsize=fs, color=color, fontproperties=KF, zorder=13,
                    path_effects=viz._stroke("black", 2.2))


def lava_overlay(code):
    """합의용암=빨강, 광학단독=주황 의 반투명 RGBA."""
    ov = np.zeros((*code.shape, 4))
    ov[code == 1] = [0.85, 0.10, 0.10, 0.78]
    ov[code == 2] = [0.98, 0.62, 0.20, 0.70]
    return ov


# ===== FIG 1: 위치/연구지역 =====
def fig_location():
    fig, ax = plt.subplots(figsize=(12.5, 11))
    ax.imshow(tc25, extent=EXT, origin="upper")
    viz.finalize(ax, EXT, "연구지역 — Reykjanes 반도, 아이슬란드 남서부 (2025-09-18 트루컬러)", sb_km=2, na_color="white")
    marks(ax, fs=11, dy=9)
    # 분화구열 화살표 강조
    x, y = TO_UTM.transform(-22.375, 63.892)
    ax.annotate("2023–2025 분화 중심", xy=(x, y), xytext=(x-3600, y+1500), fontproperties=KB, fontsize=11,
                color="#ffd400", path_effects=viz._stroke("black", 3),
                arrowprops=dict(arrowstyle="->", color="#ffd400", lw=2))
    ax.text(0.015, 0.018, "위치 ≈ 63.88°N, 22.44°W  ·  레이캬비크 남서 ~40 km  ·  분석범위 약 13.6 × 14.8 km (200.9 km²)",
            transform=ax.transAxes, fontsize=9.5, color="white", fontproperties=KF,
            va="bottom", path_effects=viz._stroke("black", 2.5))
    fig.suptitle("그림 1. 연구지역 — Grindavík·Svartsengi·Sundhnúkur 일원", fontproperties=KB, fontsize=15, y=0.995)
    fig.savefig(f"{FIG}/fig01_location.png", bbox_inches="tight"); plt.close(fig); print("fig01_location")


# ===== FIG 2: 트루컬러 3시기 =====
def fig_truecolor():
    fig, ax = plt.subplots(1, 3, figsize=(21, 8.4))
    for a, tc, t in [(ax[0], tc23, "(a) 2023-09-21 — 분화 전"),
                     (ax[1], tc24, "(b) 2024-09-15 — 분화 중(syn-eruptive)"),
                     (ax[2], tc25, "(c) 2025-09-18 — 분화 후")]:
        a.imshow(tc, extent=EXT, origin="upper")
        viz.finalize(a, EXT, t, sb_km=2, na_color="white")
    marks(ax[2], names=["Sundhnúkur 분화구열", "그린다비크(읍)"], fs=8.5)
    fig.suptitle("그림 2. 트루컬러 합성 — 분화 전·중·후 (Sentinel-2, B4·B3·B2)", fontproperties=KB, fontsize=16, y=1.0)
    fig.savefig(f"{FIG}/fig02_truecolor.png", bbox_inches="tight"); plt.close(fig); print("fig02_truecolor")


# ===== FIG 3: 용암류 확대 (Sundhnúkur→Grindavík) =====
def fig_zoom():
    cx, cy = TO_UTM.transform(-22.41, 63.875)
    half = 4200
    e = [cx-half, cx+half, cy-half, cy+half]
    c0 = int((e[0]-b[0])/10); c1 = int((e[1]-b[0])/10)
    r0 = int((b[3]-e[3])/10); r1 = int((b[3]-e[2])/10)
    fig, ax = plt.subplots(1, 2, figsize=(15.5, 8.2))
    ax[0].imshow(viz.truecolor(s23[:, r0:r1, c0:c1]), extent=e, origin="upper")
    ax[1].imshow(viz.truecolor(s25[:, r0:r1, c0:c1]), extent=e, origin="upper")
    ax[1].imshow(lava_overlay(code[r0:r1, c0:c1]), extent=e, origin="upper")
    for a, t in [(ax[0], "(a) 2023 — 분화 전 (이끼·용암대지)"), (ax[1], "(b) 2025 — 신규 용암류(적색 합의영역)")]:
        viz.finalize(a, e, t, sb_km=1, na_color="white")
    marks(ax[1], names=["Sundhnúkur 분화구열", "그린다비크(읍)", "블루라군·Svartsengi"], fs=8.5)
    fig.suptitle("그림 3. Sundhnúkur–Grindavík 용암류 확대 비교", fontproperties=KB, fontsize=15)
    fig.savefig(f"{FIG}/fig03_zoom.png", bbox_inches="tight"); plt.close(fig); print("fig03_zoom")


# ===== FIG 4: NDVI (식생·이끼 소실) =====
def fig_ndvi():
    fig, ax = plt.subplots(1, 3, figsize=(21, 8))
    viz.map_panel(ax[0], np.where(land, ndvi23, np.nan), EXT, NDVI_CMAP, -0.1, 0.8, "(a) NDVI 2023(전)", True, "NDVI", n_grat=3)
    viz.map_panel(ax[1], np.where(land, ndvi25, np.nan), EXT, NDVI_CMAP, -0.1, 0.8, "(b) NDVI 2025(후)", True, "NDVI", n_grat=3)
    viz.map_panel(ax[2], np.where(land, dN, np.nan), EXT, "RdYlGn", -0.6, 0.6, "(c) ΔNDVI (2025-2023)", True, "ΔNDVI", n_grat=3)
    fig.suptitle("그림 4. NDVI 식생·이끼 변화 — 용암 매몰부 급감 (단, 이끼 위상교란 포함)", fontproperties=KB, fontsize=15)
    fig.savefig(f"{FIG}/fig04_ndvi.png", bbox_inches="tight"); plt.close(fig); print("fig04_ndvi")


# ===== FIG 5: 다중센서 증거 (광학·SAR·열) — 핵심 융합 =====
def fig_multisensor():
    fig, ax = plt.subplots(1, 3, figsize=(21, 8))
    viz.map_panel(ax[0], np.where(land, dN, np.nan), EXT, "RdYlGn", -0.6, 0.6,
                  "(a) 광학 ΔNDVI", True, "ΔNDVI", n_grat=3)
    viz.map_panel(ax[1], np.where(land, dvv, np.nan), EXT, "RdBu_r", -4, 4,
                  "(b) SAR ΔVV (후방산란, dB)", True, "ΔVV dB", na_color="black", n_grat=3)
    ax[1].text(0.20, 0.09, "S-1 궤도 결측\n(스와스 경계 · 커버 73%)", transform=ax[1].transAxes,
               ha="center", va="center", fontproperties=KF, fontsize=10.5, color="0.45", zorder=6)
    viz.map_panel(ax[2], np.where(land, anom, np.nan), EXT, "RdBu_r", -6, 6,
                  "(c) 열 ΔLST 이상(상대승온, °C)", True, "ΔLST′ °C", na_color="black", n_grat=3)
    fig.suptitle("그림 5. 다중센서 변화 증거 — 광학(식생↓)·SAR(거침↑)·열(승온↑)이 같은 위치를 지목",
                 fontproperties=KB, fontsize=15)
    fig.savefig(f"{FIG}/fig05_multisensor.png", bbox_inches="tight"); plt.close(fig); print("fig05_multisensor")


# ===== FIG 6: 다중센서 합의 신규 용암 (헤드라인) =====
def fig_consensus():
    fig, ax = plt.subplots(1, 2, figsize=(16, 8.6), gridspec_kw={"width_ratios": [1.25, 1]})
    a = ax[0]
    a.imshow(tc25, extent=EXT, origin="upper")
    a.imshow(lava_overlay(code), extent=EXT, origin="upper")
    viz.finalize(a, EXT, "합의 신규 용암(적) · 광학단독(주)", sb_km=2, na_color="white")
    marks(a, names=["Sundhnúkur 분화구열", "그린다비크(읍)", "블루라군·Svartsengi"], fs=8.5)
    a.legend(handles=[Patch(fc="#d91a1a", label=f"다중센서 합의 용암  {ST['lava_km2']:.1f} km²"),
                      Patch(fc="#fa9e33", label=f"광학단독(미합의·잡음)  {ST['lava_optonly_km2']:.1f} km²")],
             loc="lower left", prop=KF, fontsize=9, framealpha=0.9)
    # 우: 추정치 비교 막대 (과대추정 → 견고추정)
    a2 = ax[1]
    labels = ["분류:나지증가", "ΔNDVI 감소", "다중센서\n합의(견고)"]
    vals = [area[1][2]-area[0][2], ST["veg_to_bare"], ST["lava_km2"]]
    cols = ["#bdbdbd", "#bdbdbd", "#d91a1a"]
    bars = a2.bar(labels, vals, color=cols, edgecolor="0.3")
    for r, v in zip(bars, vals):
        a2.text(r.get_x()+r.get_width()/2, v+0.5, f"{v:.1f}", ha="center", fontproperties=KB, fontsize=12)
    a2.set_ylabel("면적 (km²)", fontproperties=KF)
    a2.set_title("단일기법 과대추정 vs 다중센서 견고추정", fontproperties=KB, fontsize=13)
    a2.set_xticklabels(labels, fontproperties=KF, fontsize=10.5)
    a2.grid(axis="y", alpha=0.3); a2.set_axisbelow(True)
    a2.text(0.5, 0.92, f"합의용암 내 ΔVV {ST['lava_dvv']:+.1f}dB · ΔLST′ {ST['lava_anom']:+.1f}°C\n중심 {ST['lava_lat']:.3f}°N",
            transform=a2.transAxes, ha="center", va="top", fontproperties=KF, fontsize=10, color="#555")
    fig.suptitle("그림 6. 다중센서 합의 신규 용암 — 견고한 용암 범위 산정", fontproperties=KB, fontsize=16)
    fig.tight_layout(rect=[0, 0, 1, 0.95]); fig.savefig(f"{FIG}/fig06_consensus.png", bbox_inches="tight"); plt.close(fig); print("fig06_consensus")


# ===== FIG 7: 분류 + 정량 =====
def fig_class():
    fig, ax = plt.subplots(1, 2, figsize=(15, 8.6))
    viz.discrete_panel(ax[0], cls23, EXT, CLS_CMAP, 3, CLS_LAB, "(a) 2023 토지피복", sb_km=2)
    viz.discrete_panel(ax[1], cls25, EXT, CLS_CMAP, 3, CLS_LAB, "(b) 2025 토지피복", sb_km=2)
    fig.suptitle("그림 7. 토지피복 분류 (k-means 비지도, 3클래스)", fontproperties=KB, fontsize=15)
    fig.savefig(f"{FIG}/fig07_class.png", bbox_inches="tight"); plt.close(fig); print("fig07_class")


def fig_class_stats():
    fig, ax = plt.subplots(1, 2, figsize=(15, 6.2))
    x = np.arange(3); w = 0.36; cols = ["#2c7fb8", "#41ab5d", "#8c6d4f"]
    ax[0].bar(x-w/2, area[0], w, color=cols, edgecolor="0.3", alpha=0.6, label="2023")
    ax[0].bar(x+w/2, area[1], w, color=cols, edgecolor="0.3", label="2025")
    for i in range(3):
        ax[0].text(x[i]-w/2, area[0][i]+1, f"{area[0][i]:.0f}", ha="center", fontsize=9, fontproperties=KF)
        ax[0].text(x[i]+w/2, area[1][i]+1, f"{area[1][i]:.0f}", ha="center", fontsize=9, fontproperties=KF)
    ax[0].set_xticks(x); ax[0].set_xticklabels(CLS_LAB, fontproperties=KF, fontsize=11)
    ax[0].set_ylabel("면적 (km²)", fontproperties=KF)
    handles = [Patch(fc=cols[i], label=CLS_LAB[i]) for i in range(3)] + \
              [Patch(fc="0.5", alpha=0.6, label="2023 (연한색)"), Patch(fc="0.5", label="2025 (진한색)")]
    ax[0].legend(handles=handles, prop=KF, fontsize=9, ncol=2)
    ax[0].set_title("(a) 클래스별 면적 변화", fontproperties=KB, fontsize=13); ax[0].grid(axis="y", alpha=0.3)
    # 도넛: 2025 무식생 구성 (합의용암 vs 기존나지/위상)
    lava = ST["lava_km2"]; bare25 = area[1][2]; other = max(bare25 - lava, 0)
    ax[1].pie([lava, other], labels=[f"신규 용암(합의)\n{lava:.0f} km²", f"기존 나지·용암대지·위상\n{other:.0f} km²"],
              colors=["#d91a1a", "#d9c7b0"], autopct="%1.0f%%", startangle=90,
              textprops={"fontproperties": KF, "fontsize": 10}, wedgeprops={"edgecolor": "white"})
    ax[1].set_title("(b) 2025 '나지·용암' 57 km²의 구성", fontproperties=KB, fontsize=13)
    fig.suptitle("그림 8. 토지피복 정량 변화 — 무식생 급증의 분해", fontproperties=KB, fontsize=15)
    fig.tight_layout(rect=[0, 0, 1, 0.94]); fig.savefig(f"{FIG}/fig08_class_stats.png", bbox_inches="tight"); plt.close(fig); print("fig08_class_stats")


# ===== FIG 9: CVA + PCA =====
def fig_cva_pca():
    fig, ax = plt.subplots(1, 2, figsize=(15.5, 8.4))
    viz.map_panel(ax[0], np.where(land, mag, np.nan), EXT, "magma", 0, np.nanpercentile(mag[land], 98),
                  "(a) CVA 변화강도 (6밴드)", True, "변화강도", sb_km=2, na_color="white")
    vlim = np.nanpercentile(np.abs(pca1[land]), 98)
    viz.map_panel(ax[1], np.where(land, pca1, np.nan), EXT, "RdBu_r", -vlim, vlim,
                  f"(b) 차분 PCA 제1성분 (분산 {pca_var[0]:.0f}%)", True, "PC1", sb_km=2, na_color="black")
    fig.suptitle("그림 9. 변화벡터분석(CVA)·주성분분석(PCA) — 데이터기반 주 변화축", fontproperties=KB, fontsize=15)
    fig.savefig(f"{FIG}/fig09_cva_pca.png", bbox_inches="tight"); plt.close(fig); print("fig09_cva_pca")


# ===== FIG 10: LST 열환경 =====
def fig_lst():
    fig, ax = plt.subplots(1, 3, figsize=(21, 8))
    vmin, vmax = 8, 26
    viz.map_panel(ax[0], np.where(land, lst23, np.nan), EXT, "inferno", vmin, vmax, "(a) LST 2023 (°C)", True, "°C", na_color="white", n_grat=3)
    viz.map_panel(ax[1], np.where(land, lst25, np.nan), EXT, "inferno", vmin, vmax, "(b) LST 2025 (°C)", True, "°C", na_color="white", n_grat=3)
    viz.map_panel(ax[2], np.where(land, anom, np.nan), EXT, "RdBu_r", -6, 6, "(c) 상대 ΔLST 이상(°C)", True, "ΔLST′", na_color="black", n_grat=3)
    fig.suptitle(f"그림 10. 지표온도(LST, Landsat 8/9) — 용암·지열 고온, 2025 최대 {ST['hot_temp']:.0f}°C ({ST['hot_km2']:.1f} km²)",
                 fontproperties=KB, fontsize=15)
    fig.savefig(f"{FIG}/fig10_lst.png", bbox_inches="tight"); plt.close(fig); print("fig10_lst")


# ===== FIG 11: NDVI 3시기 궤적 + 분포 =====
def fig_summary():
    fig, ax = plt.subplots(1, 2, figsize=(15, 6))
    yrs = ["2023", "2024", "2025"]; mns = [ST["ndvi_mean"][y] for y in yrs]
    ax[0].plot(yrs, mns, "-o", color="#2E9E8F", lw=2.5, ms=9)
    for xi, v in zip(yrs, mns): ax[0].text(xi, v+0.006, f"{v:.2f}", ha="center", fontproperties=KB, fontsize=11)
    ax[0].set_title("(a) 육지 NDVI 평균 궤적 — 2024 분화 중 저하", fontproperties=KB, fontsize=13)
    ax[0].set_ylabel("NDVI 육지 평균", fontproperties=KF); ax[0].grid(alpha=0.3); ax[0].set_ylim(0.25, 0.45)
    ax[0].annotate("분화 중 테프라·위상\n(일시 저하)", xy=("2024", mns[1]), xytext=(0.35, 0.30),
                   textcoords="axes fraction", fontproperties=KF, fontsize=9.5,
                   arrowprops=dict(arrowstyle="->", color="#888"))
    ax[1].hist(ndvi23[land], bins=80, alpha=0.55, label="2023(전)", color="#3aa657", density=True)
    ax[1].hist(ndvi25[land], bins=80, alpha=0.55, label="2025(후)", color="#b5651d", density=True)
    ax[1].axvline(0.18, color="k", ls="--", lw=1.2); ax[1].text(0.18, ax[1].get_ylim()[1]*0.9, " 무식생 임계", fontproperties=KF, fontsize=9)
    ax[1].set_title("(b) NDVI 분포 — 저NDVI(용암) 화소 증가", fontproperties=KB, fontsize=13)
    ax[1].set_xlabel("NDVI", fontproperties=KF); ax[1].set_ylabel("밀도", fontproperties=KF); ax[1].legend(prop=KF); ax[1].grid(alpha=0.3)
    fig.suptitle("그림 11. 식생지수 종합 — 시기 궤적과 분포 변화", fontproperties=KB, fontsize=15)
    fig.tight_layout(rect=[0, 0, 1, 0.94]); fig.savefig(f"{FIG}/fig11_summary.png", bbox_inches="tight"); plt.close(fig); print("fig11_summary")


if __name__ == "__main__":
    fig_location(); fig_truecolor(); fig_zoom(); fig_ndvi(); fig_multisensor()
    fig_consensus(); fig_class(); fig_class_stats(); fig_cva_pca(); fig_lst(); fig_summary()
    print("\n모든 figure 생성 완료:", FIG)
