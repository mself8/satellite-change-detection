"""지도 시각화 공통 모듈: 한글폰트, 경위도 그래티큘, north arrow, scale bar.

평가표 필수요건: 모든 결과맵에 north arrow · scale bar · grid 포함.
데이터는 UTM 52N(m). 그래티큘은 경위도 선을 UTM로 변환해 정확히 그린다.
"""
import numpy as np
import matplotlib as mpl
mpl.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from matplotlib.patches import FancyArrow, Rectangle
from matplotlib.offsetbox import AnchoredOffsetbox, TextArea, VPacker, DrawingArea
from pyproj import Transformer

# ---- 한글 폰트 ----
_FONT = "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"
_FONT_B = "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf"
for f in (_FONT, _FONT_B):
    fm.fontManager.addfont(f)
mpl.rcParams["font.family"] = "NanumGothic"
mpl.rcParams["axes.unicode_minus"] = False
mpl.rcParams["font.size"] = 11
mpl.rcParams["figure.dpi"] = 120
KFONT = fm.FontProperties(fname=_FONT)
KFONT_B = fm.FontProperties(fname=_FONT_B)

DST_CRS = "EPSG:32652"
_to_ll = Transformer.from_crs(DST_CRS, "EPSG:4326", always_xy=True)
_to_utm = Transformer.from_crs("EPSG:4326", DST_CRS, always_xy=True)


def stretch(arr, p=(2, 98)):
    lo, hi = np.nanpercentile(arr, p)
    return np.clip((arr - lo) / (hi - lo + 1e-9), 0, 1)


def truecolor(stack, p=(2, 98), gamma=1.25, bands=(2, 1, 0)):
    """stack: (6,H,W) [B,G,R,NIR,SWIR1,SWIR2] -> RGB 0..1."""
    rgb = np.stack([stack[b] for b in bands], -1)
    out = np.zeros_like(rgb)
    for i in range(3):
        out[..., i] = stretch(rgb[..., i], p)
    return np.clip(out ** (1 / gamma), 0, 1)


def falsecolor(stack, p=(2, 98), gamma=1.2):
    """NIR-R-G 위색 합성(식생=적색). bands NIR,R,G = 3,2,1."""
    return truecolor(stack, p, gamma, bands=(3, 2, 1))


def _nice_step(span, target_n):
    raw = span / target_n
    for s in (0.005, 0.01, 0.02, 0.025, 0.05, 0.1, 0.2):
        if s >= raw:
            return s
    return 0.5


def add_graticule(ax, ext, n=4, color="white", alpha=0.45, lw=0.6,
                  label_color="black", fontsize=8):
    """경위도 그래티큘 + 가장자리 눈금라벨. ext=[xmin,xmax,ymin,ymax] UTM(m)."""
    xmin, xmax, ymin, ymax = ext
    cx = [xmin, xmin, xmax, xmax]; cy = [ymin, ymax, ymin, ymax]
    lons, lats = _to_ll.transform(cx, cy)
    lon0, lon1 = min(lons), max(lons)
    lat0, lat1 = min(lats), max(lats)
    dlon = _nice_step(lon1 - lon0, n)
    dlat = _nice_step(lat1 - lat0, n)
    lon_ticks = np.arange(np.ceil(lon0 / dlon) * dlon, lon1, dlon)
    lat_ticks = np.arange(np.ceil(lat0 / dlat) * dlat, lat1, dlat)

    samp_lat = np.linspace(lat0 - dlat, lat1 + dlat, 80)
    xt_pos, xt_lab = [], []
    for lo in lon_ticks:
        xs, ys = _to_utm.transform(np.full_like(samp_lat, lo), samp_lat)
        ax.plot(xs, ys, color=color, alpha=alpha, lw=lw, ls=":", zorder=5)
        if ys.min() <= ymin <= ys.max():
            xt_pos.append(np.interp(ymin, ys, xs))
            xt_lab.append(f"{lo:.2f}°E")
    samp_lon = np.linspace(lon0 - dlon, lon1 + dlon, 80)
    yt_pos, yt_lab = [], []
    for la in lat_ticks:
        xs, ys = _to_utm.transform(samp_lon, np.full_like(samp_lon, la))
        ax.plot(xs, ys, color=color, alpha=alpha, lw=lw, ls=":", zorder=5)
        if xs.min() <= xmin <= xs.max():
            yt_pos.append(np.interp(xmin, xs, ys))
            yt_lab.append(f"{la:.2f}°N")
    ax.set_xticks(xt_pos); ax.set_xticklabels(xt_lab, fontsize=fontsize, color=label_color)
    ax.set_yticks(yt_pos); ax.set_yticklabels(yt_lab, fontsize=fontsize, color=label_color)
    ax.set_xlim(xmin, xmax); ax.set_ylim(ymin, ymax)
    ax.tick_params(length=3, color=label_color)


def add_north_arrow(ax, x=0.94, y=0.94, size=0.07, color="white", ec="black"):
    """우상단 N 화살표 (axes 좌표)."""
    ax.annotate("", xy=(x, y), xytext=(x, y - size),
                xycoords="axes fraction",
                arrowprops=dict(facecolor=color, edgecolor=ec, width=4.5,
                                headwidth=12, headlength=10, lw=1.0), zorder=10)
    ax.text(x, y + 0.012, "N", transform=ax.transAxes, ha="center", va="bottom",
            fontsize=12, fontweight="bold", color=color,
            path_effects=_stroke(ec), zorder=11)


def _stroke(color="black", lw=2):
    import matplotlib.patheffects as pe
    return [pe.withStroke(linewidth=lw, foreground=color)]


def add_scalebar(ax, ext, length_km=2.0, loc="lower right", color="white",
                 ec="black", fontsize=8.5, height_frac=0.012, pad_frac=0.04):
    """분할형 축척 막대 (검정/흰색 교차). 데이터좌표(m) 기준."""
    xmin, xmax, ymin, ymax = ext
    L = length_km * 1000.0
    seg = L / 2.0
    h = (ymax - ymin) * height_frac
    px = (xmax - xmin) * pad_frac
    py = (ymax - ymin) * pad_frac
    if "right" in loc:
        x0 = xmax - px - L
    else:
        x0 = xmin + px
    y0 = ymin + py
    fills = [color, ec]
    for i in range(2):
        ax.add_patch(Rectangle((x0 + i * seg, y0), seg, h, facecolor=fills[i],
                               edgecolor=ec, lw=0.8, zorder=10))
    for i, val in enumerate([0, seg / 1000, L / 1000]):
        lab = f"{val:g}"
        ax.text(x0 + i * seg, y0 + h * 1.5, lab, ha="center", va="bottom",
                fontsize=fontsize, color=ec, fontweight="bold",
                path_effects=_stroke("white", 1.5), zorder=11)
    ax.text(x0 + L, y0 + h * 1.5, "km", ha="left", va="bottom", fontsize=fontsize,
            color=ec, fontweight="bold", path_effects=_stroke("white", 1.5), zorder=11)


def finalize(ax, ext, title=None, sb_km=2.0, sb_loc="lower right",
             grat_color="white", grat_label="black", na_color="white"):
    """지도 1장 마무리: 그래티큘 + N + 축척 + 제목."""
    add_graticule(ax, ext, color=grat_color, label_color=grat_label)
    add_north_arrow(ax, color=na_color)
    add_scalebar(ax, ext, length_km=sb_km, loc=sb_loc)
    if title:
        ax.set_title(title, fontproperties=KFONT_B, fontsize=13, pad=8)
    ax.set_aspect("equal")


def map_panel(ax, data, ext, cmap, vmin, vmax, title=None, cbar=False,
              cbar_label=None, sb_km=2.0, sb_loc="lower right",
              grat_color="0.25", grat_label="black", na_color="black",
              under=None, n_grat=4):
    """연속형 데이터 지도 패널 + (옵션)컬러바 + 필수 카토그래피.

    under: 배경 이미지(RGB) 먼저 깔고 그 위에 data를 반투명 없이 덮을 때 사용.
    """
    if under is not None:
        ax.imshow(under, extent=ext, origin="upper", zorder=0)
    im = ax.imshow(data, extent=ext, origin="upper", cmap=cmap, vmin=vmin,
                   vmax=vmax, zorder=1)
    add_graticule(ax, ext, n=n_grat, color=grat_color, label_color=grat_label,
                  alpha=0.5)
    add_north_arrow(ax, color=na_color, ec="white")
    add_scalebar(ax, ext, length_km=sb_km, loc=sb_loc, color="white", ec="black")
    if title:
        ax.set_title(title, fontproperties=KFONT_B, fontsize=13, pad=7)
    ax.set_aspect("equal")
    if cbar:
        cb = ax.figure.colorbar(im, ax=ax, shrink=0.62, pad=0.02)
        if cbar_label:
            cb.set_label(cbar_label, fontproperties=KFONT, fontsize=9)
        cb.ax.tick_params(labelsize=8)
    return im


def discrete_panel(ax, data, ext, cmap, n, labels, title=None, sb_km=2.0,
                   sb_loc="lower right", legend=True, na_color="black",
                   grat_color="0.25"):
    """범주형(분류) 지도 패널 + 범례 + 카토그래피."""
    im = ax.imshow(data, extent=ext, origin="upper", cmap=cmap, vmin=0,
                   vmax=n - 1, interpolation="nearest", zorder=1)
    add_graticule(ax, ext, color=grat_color, label_color="black", alpha=0.5)
    add_north_arrow(ax, color=na_color, ec="white")
    add_scalebar(ax, ext, length_km=sb_km, loc=sb_loc, color="white", ec="black")
    if title:
        ax.set_title(title, fontproperties=KFONT_B, fontsize=13, pad=7)
    ax.set_aspect("equal")
    if legend:
        from matplotlib.patches import Patch
        cols = [cmap(i / max(n - 1, 1)) for i in range(n)]
        handles = [Patch(facecolor=cols[i], edgecolor="0.3", label=labels[i])
                   for i in range(n)]
        ax.legend(handles=handles, loc="lower left", fontsize=9, framealpha=0.9,
                  prop=KFONT, handlelength=1.2, borderpad=0.6)
    return im


if __name__ == "__main__":
    # 데모: 그래티큘/축척/화살표 점검
    import sys, os
    sys.path.insert(0, os.path.dirname(__file__))
    from common import read_tif, DATA, target_grid
    tr, W, H, b = target_grid()
    ext = [b[0], b[2], b[1], b[3]]
    a, _ = read_tif(os.path.join(DATA, "s2_2025.tif"))
    fig, ax = plt.subplots(figsize=(8, 9))
    ax.imshow(truecolor(a), extent=ext, origin="upper")
    finalize(ax, ext, "데모: 2025-10-28 트루컬러", sb_km=2.0)
    fig.savefig(os.path.join(os.path.dirname(DATA), "figures", "_viz_demo.png"),
                dpi=110, bbox_inches="tight")
    print("saved _viz_demo.png")
