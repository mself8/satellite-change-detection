# -*- coding: utf-8 -*-
"""슬라이드급 결과 figure 생성. 모든 결과맵에 north arrow·scale bar·grid 포함."""
import warnings; warnings.filterwarnings("ignore")
import os, sys, numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from common import DATA, FIG, read_tif, target_grid
import viz
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, LinearSegmentedColormap
from matplotlib.patches import Rectangle, Patch, FancyArrowPatch
from matplotlib.font_manager import FontProperties
KF, KB = viz.KFONT, viz.KFONT_B
plt.rcParams["savefig.dpi"] = 200

tr, W, H, b = target_grid()
EXT = [b[0], b[2], b[1], b[3]]
B, G, R, NIR, SW1, SW2 = range(6)

# ---- load ----
s17, _ = read_tif(f"{DATA}/s2_2017.tif"); s25, _ = read_tif(f"{DATA}/s2_2025.tif")
ndvi17, _ = read_tif(f"{DATA}/ndvi_2017.tif"); ndvi25, _ = read_tif(f"{DATA}/ndvi_2025.tif")
ndbi17, _ = read_tif(f"{DATA}/ndbi_2017.tif"); ndbi25, _ = read_tif(f"{DATA}/ndbi_2025.tif")
mndwi17, _ = read_tif(f"{DATA}/mndwi_2017.tif"); mndwi25, _ = read_tif(f"{DATA}/mndwi_2025.tif")
dN, _ = read_tif(f"{DATA}/d_ndvi.tif"); dB, _ = read_tif(f"{DATA}/d_ndbi.tif")
cls17, _ = read_tif(f"{DATA}/class_2017.tif"); cls25, _ = read_tif(f"{DATA}/class_2025.tif")
mag, _ = read_tif(f"{DATA}/cva_magnitude.tif"); ctype, _ = read_tif(f"{DATA}/cva_type.tif")
pca1, _ = read_tif(f"{DATA}/pca_change.tif")
land, _ = read_tif(f"{DATA}/land_stable.tif"); land = land > 0.5
sea = (mndwi17 > 0.15) & (mndwi25 > 0.15)
tc17, tc25 = viz.truecolor(s17), viz.truecolor(s25)
M3 = np.load(f"{DATA}/change_matrix3.npy"); T = np.load(f"{DATA}/land_transition.npy")
area = np.load(f"{DATA}/class_area.npy"); pca_var = np.load(f"{DATA}/pca_var.npy")

# colormaps
CLS_CMAP = ListedColormap(["#1f6fb2", "#3aa657", "#cf9b6b"])
CLS_LAB = ["수역", "식생", "불투수·나지"]
NDVI_CMAP = LinearSegmentedColormap.from_list("ndvi", ["#8c510a", "#d8b365", "#f6e8c3", "#c7e9b4", "#41ab5d", "#005a32"])
masksea = lambda a: np.where(sea, np.nan, a)


def base(figsize):
    fig, ax = plt.subplots(1, len(figsize) if isinstance(figsize, list) else 1)
    return fig, ax

# ============ FIG 1: 위치/연구지역 ============
def fig_location():
    ctx = np.load(f"{DATA}/context_rgb.npy").transpose(1, 2, 0) / 255.0
    cl, cr, cb_, ct, sl, sr, sb_, st = np.load(f"{DATA}/context_meta.npy")
    fig = plt.figure(figsize=(15, 8.6))
    gs = fig.add_gridspec(1, 2, width_ratios=[1, 1.15], wspace=0.16)
    axc = fig.add_subplot(gs[0])
    axc.imshow(ctx ** 0.85, extent=[cl, cr, cb_, ct], origin="upper")
    axc.add_patch(Rectangle((sl, sb_), sr - sl, st - sb_, fill=False, ec="red", lw=2.4))
    axc.annotate("연구지역\n인천국제공항", xy=((sl+sr)/2, st), xytext=((sl+sr)/2, st+18000),
                 ha="center", color="white", fontproperties=KB, fontsize=12,
                 arrowprops=dict(arrowstyle="->", color="red", lw=1.8),
                 path_effects=viz._stroke("black", 2.5))
    viz.add_graticule(axc, [cl, cr, cb_, ct], n=4, color="white", label_color="black", alpha=0.4)
    viz.add_north_arrow(axc, color="white", ec="black")
    viz.add_scalebar(axc, [cl, cr, cb_, ct], length_km=20, loc="lower right")
    axc.set_title("광역 위치 (Sentinel-2, 수도권 서해안)", fontproperties=KB, fontsize=13)
    axc.set_aspect("equal")

    axm = fig.add_subplot(gs[1])
    axm.imshow(tc25, extent=EXT, origin="upper")
    viz.finalize(axm, EXT, "연구지역 상세 (2025-10-28 트루컬러)", sb_km=2, na_color="white")
    for (xy, txt) in [((273200, 4151600), "제2여객터미널\n(확장구역)"),
                      ((271400, 4148200), "제3·4활주로"),
                      ((274600, 4147600), "제1여객터미널"),
                      ((273000, 4154600), "공항신도시")]:
        axm.annotate(txt, xy=xy, fontproperties=KF, fontsize=9.5, color="white",
                     ha="center", path_effects=viz._stroke("black", 2.2))
    fig.suptitle("그림 1. 연구지역 — 인천국제공항 (영종도)", fontproperties=KB, fontsize=15, y=0.99)
    fig.savefig(f"{FIG}/fig01_location.png", bbox_inches="tight"); plt.close(fig)
    print("fig01_location")

# ============ FIG 2: 트루컬러 전후 + 확대 ============
def fig_truecolor():
    fig, ax = plt.subplots(1, 2, figsize=(15.5, 9.2))
    for a, tc, t in [(ax[0], tc17, "(a) 2017-10-28 (사업 착공기)"),
                     (ax[1], tc25, "(b) 2025-10-28 (사업 완료후)")]:
        a.imshow(tc, extent=EXT, origin="upper")
        viz.finalize(a, EXT, t, sb_km=2, na_color="white")
    # 확대 박스 표시
    for a in ax:
        a.add_patch(Rectangle((272400, 4150200), 3200, 3000, fill=False, ec="yellow", lw=1.8))
    fig.suptitle("그림 2. 트루컬러 합성영상 전후 비교 (B4·B3·B2)", fontproperties=KB, fontsize=15)
    fig.savefig(f"{FIG}/fig02_truecolor.png", bbox_inches="tight"); plt.close(fig)
    print("fig02_truecolor")

# ============ FIG 2b: 확대 비교 (제2터미널) ============
def fig_zoom():
    r0, r1, c0, c1 = 200, 620, 330, 760
    def px(r0, r1, c0, c1): return [b[0]+c0*10, b[0]+c1*10, b[3]-r1*10, b[3]-r0*10]
    e = px(r0, r1, c0, c1)
    fig, ax = plt.subplots(1, 2, figsize=(15, 7.6))
    ax[0].imshow(viz.truecolor(s17[:, r0:r1, c0:c1]), extent=e, origin="upper")
    ax[1].imshow(viz.truecolor(s25[:, r0:r1, c0:c1]), extent=e, origin="upper")
    for a, t in [(ax[0], "(a) 2017 — 공사중(나지)"), (ax[1], "(b) 2025 — 터미널·계류장 확장 완료")]:
        viz.finalize(a, e, t, sb_km=1, na_color="white")
    fig.suptitle("그림 3. 제2여객터미널 일원 확대 비교", fontproperties=KB, fontsize=15)
    fig.savefig(f"{FIG}/fig03_zoom.png", bbox_inches="tight"); plt.close(fig)
    print("fig03_zoom")

# ============ FIG 4: NDVI ============
def fig_ndvi():
    fig, ax = plt.subplots(1, 3, figsize=(20, 8))
    viz.map_panel(ax[0], masksea(ndvi17), EXT, NDVI_CMAP, -0.1, 0.8, "(a) NDVI 2017", True, "NDVI", n_grat=3)
    viz.map_panel(ax[1], masksea(ndvi25), EXT, NDVI_CMAP, -0.1, 0.8, "(b) NDVI 2025", True, "NDVI", n_grat=3)
    viz.map_panel(ax[2], np.where(land, dN, np.nan), EXT, "RdYlGn", -0.5, 0.5,
                  "(c) ΔNDVI (2025−2017)", True, "ΔNDVI", n_grat=3)
    fig.suptitle("그림 4. NDVI(식생지수) 분석 — 식생 증가 우세", fontproperties=KB, fontsize=15)
    fig.savefig(f"{FIG}/fig04_ndvi.png", bbox_inches="tight"); plt.close(fig)
    print("fig04_ndvi")

# ============ FIG 5: NDBI ============
def fig_ndbi():
    fig, ax = plt.subplots(1, 3, figsize=(20, 8))
    viz.map_panel(ax[0], masksea(ndbi17), EXT, "RdBu_r", -0.4, 0.4, "(a) NDBI 2017", True, "NDBI", n_grat=3)
    viz.map_panel(ax[1], masksea(ndbi25), EXT, "RdBu_r", -0.4, 0.4, "(b) NDBI 2025", True, "NDBI", n_grat=3)
    viz.map_panel(ax[2], np.where(land, dB, np.nan), EXT, "RdBu_r", -0.3, 0.3,
                  "(c) ΔNDBI (2025−2017)", True, "ΔNDBI", n_grat=3)
    fig.suptitle("그림 5. NDBI(건조·건폐지수) 분석 — 공사나지 감소 우세, 국지적 신규 불투수", fontproperties=KB, fontsize=15)
    fig.savefig(f"{FIG}/fig05_ndbi.png", bbox_inches="tight"); plt.close(fig)
    print("fig05_ndbi")

# ============ FIG 6: 분류 ============
def fig_class():
    fig, ax = plt.subplots(1, 2, figsize=(15, 9.2))
    viz.discrete_panel(ax[0], cls17, EXT, CLS_CMAP, 3, CLS_LAB, "(a) 2017 토지피복 분류", sb_km=2)
    viz.discrete_panel(ax[1], cls25, EXT, CLS_CMAP, 3, CLS_LAB, "(b) 2025 토지피복 분류", sb_km=2)
    fig.suptitle("그림 6. 토지피복 분류 (k-means 비지도분류, 3클래스)", fontproperties=KB, fontsize=15)
    fig.savefig(f"{FIG}/fig06_class.png", bbox_inches="tight"); plt.close(fig)
    print("fig06_class")

# ============ FIG 7: 분류 통계/전이 ============
def fig_class_stats():
    fig, ax = plt.subplots(1, 2, figsize=(15, 6.2))
    x = np.arange(3); w = 0.36
    cols = ["#1f6fb2", "#3aa657", "#cf9b6b"]
    ax[0].bar(x - w/2, area[0], w, label="2017", color=[c for c in cols], edgecolor="0.3", alpha=0.65)
    ax[0].bar(x + w/2, area[1], w, label="2025", color=[c for c in cols], edgecolor="0.3")
    for i in range(3):
        ax[0].text(x[i]-w/2, area[0][i]+0.4, f"{area[0][i]:.1f}", ha="center", fontsize=9, fontproperties=KF)
        ax[0].text(x[i]+w/2, area[1][i]+0.4, f"{area[1][i]:.1f}", ha="center", fontsize=9, fontproperties=KF)
    ax[0].set_xticks(x); ax[0].set_xticklabels(CLS_LAB, fontproperties=KF, fontsize=11)
    ax[0].set_ylabel("면적 (km²)", fontproperties=KF); ax[0].legend(prop=KF)
    ax[0].set_title("(a) 클래스별 면적 변화", fontproperties=KB, fontsize=13)
    ax[0].grid(axis="y", alpha=0.3)

    # 안정육지 식생전이 — 화살표 다이어그램
    ax[1].axis("off")
    ax[1].set_xlim(0, 10); ax[1].set_ylim(0, 10)
    ax[1].set_title("(b) 안정육지 식생 변화 (조위 영향 배제)", fontproperties=KB, fontsize=13)
    boxes = {"veg": (1.2, 6.5, "#3aa657", f"식생\n(2017)"), "nv": (1.2, 2.0, "#cf9b6b", f"비식생\n(2017)"),
             "veg2": (7.2, 6.5, "#3aa657", "식생\n(2025)"), "nv2": (7.2, 2.0, "#cf9b6b", "비식생\n(2025)")}
    for k, (xx, yy, c, t) in boxes.items():
        ax[1].add_patch(Rectangle((xx, yy), 1.7, 1.4, color=c, alpha=0.85, ec="0.3"))
        ax[1].text(xx+0.85, yy+0.7, t, ha="center", va="center", fontproperties=KF, fontsize=10, color="white")
    def arr(p, q, txt, col, off=0.0):
        a = FancyArrowPatch((p[0], p[1]), (q[0], q[1]), arrowstyle="-|>", mutation_scale=16,
                            lw=2.2, color=col, connectionstyle=f"arc3,rad={off}")
        ax[1].add_patch(a)
    arr((2.9, 7.2), (7.2, 7.2), "", "#3aa657")
    arr((2.9, 2.7), (7.2, 2.7), "", "#cf9b6b")
    arr((2.9, 2.4), (7.2, 6.7), "", "#1a7a1a", 0.18)   # 녹화
    arr((2.9, 6.3), (7.2, 2.9), "", "#b5651d", -0.18)  # 신규개발
    ax[1].text(5.0, 8.6, f"비식생→식생 (녹화): {T[1,0]:.1f} km²", ha="center", color="#1a7a1a", fontproperties=KB, fontsize=12)
    ax[1].text(5.0, 0.7, f"식생→비식생 (신규개발): {T[0,1]:.1f} km²", ha="center", color="#b5651d", fontproperties=KB, fontsize=12)
    ax[1].text(5.0, 4.7, f"순 식생 +{T[1,0]-T[0,1]:.1f} km²", ha="center", color="black", fontproperties=KB, fontsize=12.5)
    fig.suptitle("그림 7. 토지피복 정량 변화", fontproperties=KB, fontsize=15)
    fig.tight_layout(rect=[0,0,1,0.95]); fig.savefig(f"{FIG}/fig07_class_stats.png", bbox_inches="tight"); plt.close(fig)
    print("fig07_class_stats")

# ============ FIG 8: CVA ============
def fig_cva():
    fig, ax = plt.subplots(1, 2, figsize=(14.5, 9))
    viz.map_panel(ax[0], np.where(land, mag, np.nan), EXT, "magma", 0,
                  np.nanpercentile(mag[land], 98), "(a) CVA 변화강도(magnitude)", True, "변화강도", sb_km=2, na_color="white")
    cm = ListedColormap(["#3aa657", "#d9534f", "#f0c040"])
    typ = np.where(land & (ctype > 0), ctype - 1, np.nan)
    viz.discrete_panel(ax[1], typ, EXT, cm, 3, ["녹화", "식생감소(개발)", "기타 표면변화"],
                       "(b) CVA 변화유형", sb_km=2)
    fig.suptitle("그림 8. 변화벡터분석(CVA) — 변화 강도와 유형", fontproperties=KB, fontsize=15)
    fig.savefig(f"{FIG}/fig08_cva.png", bbox_inches="tight"); plt.close(fig)
    print("fig08_cva")

# ============ FIG 9: PCA ============
def fig_pca():
    fig, ax = plt.subplots(1, 2, figsize=(15, 8.4))
    vlim = np.nanpercentile(np.abs(pca1[land]), 98)
    viz.map_panel(ax[0], np.where(land, pca1, np.nan), EXT, "BrBG", -vlim, vlim,
                  "(a) 차분영상 PCA 제1성분 (주 변화축)", True, "PC1 점수", sb_km=2, na_color="black")
    ax[1].bar(np.arange(1, 7), pca_var[:6]*100, color="#4c72b0", edgecolor="0.3")
    for i, v in enumerate(pca_var[:6]*100):
        ax[1].text(i+1, v+0.8, f"{v:.1f}%", ha="center", fontproperties=KF, fontsize=9)
    ax[1].set_xlabel("주성분", fontproperties=KF); ax[1].set_ylabel("분산설명률 (%)", fontproperties=KF)
    ax[1].set_title("(b) 차분영상 PCA 분산설명", fontproperties=KB, fontsize=13)
    ax[1].grid(axis="y", alpha=0.3); ax[1].set_axisbelow(True)
    fig.suptitle("그림 9. 주성분분석(PCA) 기반 변화탐지", fontproperties=KB, fontsize=15)
    fig.tight_layout(rect=[0,0,1,0.95]); fig.savefig(f"{FIG}/fig09_pca.png", bbox_inches="tight"); plt.close(fig)
    print("fig09_pca")

# ============ FIG 10: 분포/방법비교 ============
def fig_summary():
    fig, ax = plt.subplots(1, 2, figsize=(15, 6))
    for a, d17, d25, ttl, xl in [(ax[0], ndvi17, ndvi25, "(a) NDVI 분포 (안정육지)", "NDVI"),
                                 (ax[1], ndbi17, ndbi25, "(b) NDBI 분포 (안정육지)", "NDBI")]:
        a.hist(d17[land], bins=80, alpha=0.55, label="2017", color="#b5651d", density=True)
        a.hist(d25[land], bins=80, alpha=0.55, label="2025", color="#3aa657", density=True)
        a.axvline(np.nanmean(d17[land]), color="#b5651d", ls="--", lw=1.5)
        a.axvline(np.nanmean(d25[land]), color="#1a7a1a", ls="--", lw=1.5)
        a.set_title(ttl, fontproperties=KB, fontsize=13); a.set_xlabel(xl, fontproperties=KF)
        a.set_ylabel("밀도", fontproperties=KF); a.legend(prop=KF); a.grid(alpha=0.3)
    fig.suptitle("그림 10. 분광지수 분포 변화 (정량 비교)", fontproperties=KB, fontsize=15)
    fig.tight_layout(rect=[0,0,1,0.94]); fig.savefig(f"{FIG}/fig10_summary.png", bbox_inches="tight"); plt.close(fig)
    print("fig10_summary")


if __name__ == "__main__":
    fig_location(); fig_truecolor(); fig_zoom(); fig_ndvi(); fig_ndbi()
    fig_class(); fig_class_stats(); fig_cva(); fig_pca(); fig_summary()
    print("\n모든 figure 생성 완료:", FIG)
