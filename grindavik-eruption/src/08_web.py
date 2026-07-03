# -*- coding: utf-8 -*-
"""인터랙티브 변화탐지 웹맵 생성 (Leaflet).

결과 래스터를 Web Mercator(3857)로 재투영→RGBA PNG로 export하고,
위성 베이스맵 위에 다음 기능을 가진 웹앱을 만든다(교수님이 좋아하시는 인터랙티브 시각화 강화):
  · 분화 전(2023)·중(2024)·후(2025) 원클릭 시점 전환 — 크로스페이드 + 자동재생(▶) + 단축키 0/1/2/3·P
  · 픽셀 인스펙터 — 지도 클릭 시 그 지점의 ΔNDVI·ΔVV·ΔLST′와 합의/잔열 판정을 팝업으로
  · 다중센서 분석 레이어 토글(★합의 용암, ◆잔열 상태, ◆U-Net 확률, ①②③ 센서별)
  · 위험도 연결선 — 주요 자산↔최근접 용암 거리(fig15와 동일 정의)
실행 후 web/index.html 을 브라우저로 열면 됨(베이스맵 타일만 인터넷 필요).
"""
import warnings; warnings.filterwarnings("ignore")
import os, sys, json, numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from common import DATA, WEB, read_tif, target_grid, get_stats
import viz
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
NDVI_CMAP = LinearSegmentedColormap.from_list("ndvi_bg",   # PDF fig04와 동일(갈색→초록)
    ["#8c510a", "#d8b365", "#f6e8c3", "#c7e9b4", "#41ab5d", "#005a32"])
from rasterio.warp import reproject, Resampling, transform_bounds
from rasterio.transform import from_bounds as t_from_bounds
from pyproj import Transformer
from PIL import Image

tr, W, H, b = target_grid()
UTM, WEBM = "EPSG:32627", "EPSG:3857"
ST = get_stats()
TILES = os.path.join(WEB, "tiles"); os.makedirs(TILES, exist_ok=True)
B, G, R, NIR, SW1, SW2 = range(6)

# Web Mercator 타깃 격자 + 위경도 바운드
db = transform_bounds(UTM, WEBM, b[0], b[1], b[2], b[3])           # (w,s,e,n) in 3857
OW, OH = W, H
dst_t = t_from_bounds(db[0], db[1], db[2], db[3], OW, OH)
llb = transform_bounds(WEBM, "EPSG:4326", *db)                     # (w,s,e,n) lon/lat
BOUNDS = [[llb[1], llb[0]], [llb[3], llb[2]]]                      # [[S,W],[N,E]]
CENTER = [(llb[1]+llb[3])/2, (llb[0]+llb[2])/2]


def warp(arr, resampling=Resampling.bilinear):
    dst = np.full((OH, OW), np.nan, "float32")
    reproject(arr.astype("float32"), dst, src_transform=tr, src_crs=UTM,
              dst_transform=dst_t, dst_crs=WEBM, resampling=resampling,
              src_nodata=np.nan, dst_nodata=np.nan)
    return dst


def save_rgba(rgba, name):
    Image.fromarray(rgba, "RGBA").save(os.path.join(TILES, name))
    return f"tiles/{name}"


def rgb_layer(tc, name, alpha=255):
    chans = [warp(tc[..., i]) for i in range(3)]
    rgb = np.clip(np.nan_to_num(np.stack(chans, -1)), 0, 1)
    valid = np.isfinite(chans[0]) & (np.stack(chans, -1).sum(-1) > 0.003)
    a = np.where(valid, alpha, 0).astype("uint8")
    return save_rgba(np.dstack([(rgb*255).astype("uint8"), a]), name)


def scalar_layer(arr, name, cmap, vmin, vmax, mask=None, alpha=235):
    w = warp(arr)
    m = np.isfinite(w)
    if mask is not None:
        m &= warp(mask.astype("float32"), Resampling.nearest) > 0.5
    norm = np.clip((w - vmin)/(vmax - vmin + 1e-9), 0, 1)
    rgba = (plt.get_cmap(cmap)(np.nan_to_num(norm))*255).astype("uint8")
    rgba[..., 3] = np.where(m, alpha, 0)
    return save_rgba(rgba, name)


def cat_layer(code, name, mapping):
    """mapping: {value: [r,g,b,a]}"""
    c = warp(code, Resampling.nearest)
    rgba = np.zeros((OH, OW, 4), "uint8")
    for v, col in mapping.items():
        rgba[np.round(c) == v] = col
    return save_rgba(rgba, name)


def stops(cmap, n=6):
    cm = plt.get_cmap(cmap)
    return ["#%02x%02x%02x" % tuple(int(x*255) for x in cm(i/(n-1))[:3]) for i in range(n)]


# ---- 데이터 로드 ----
s23, _ = read_tif(f"{DATA}/s2_2023.tif"); s24, _ = read_tif(f"{DATA}/s2_2024.tif"); s25, _ = read_tif(f"{DATA}/s2_2025.tif")
dN, _ = read_tif(f"{DATA}/d_ndvi.tif"); dvv, _ = read_tif(f"{DATA}/d_vv.tif")
lst25, _ = read_tif(f"{DATA}/lst_2025.tif"); anom, _ = read_tif(f"{DATA}/lst_anom.tif")
code, _ = read_tif(f"{DATA}/consensus_lava.tif")
land, _ = read_tif(f"{DATA}/land.tif"); land = land > 0.5

# 연도별 lens 원자료 (전/후 동일 스케일 스와이프용)
nd23, _ = read_tif(f"{DATA}/ndvi_2023.tif"); nd25, _ = read_tif(f"{DATA}/ndvi_2025.tif")
nb23, _ = read_tif(f"{DATA}/nbr_2023.tif");  nb25, _ = read_tif(f"{DATA}/nbr_2025.tif")
vv23 = read_tif(f"{DATA}/s1_2023.tif")[0][0]; vv25 = read_tif(f"{DATA}/s1_2025.tif")[0][0]   # band0 = VV
lt23, _ = read_tif(f"{DATA}/lst_2023.tif")
# LST는 절대비교 불가(전역 기상 오프셋) → 각 해 육지배경 대비 상대이상치로
la23 = lt23  - np.nanmean(np.where(land, lt23,  np.nan))
la25 = lst25 - np.nanmean(np.where(land, lst25, np.nan))

print("오버레이 export → web/tiles/ ...")
f_tc23 = rgb_layer(viz.truecolor(s23), "tc2023.png")
f_tc24 = rgb_layer(viz.truecolor(s24), "tc2024.png")
f_tc25 = rgb_layer(viz.truecolor(s25), "tc2025.png")
f_lava = cat_layer(code, "consensus.png", {1: [217, 26, 26, 205], 2: [250, 158, 51, 180]})

# ── 연도별 lens 타일 (전/후 동일 컬러스케일) ──
def lens_pair(a23, a25, base, cmap, vmin, vmax):
    return (scalar_layer(np.where(land, a23, np.nan), f"{base}_2023.png", cmap, vmin, vmax, mask=land),
            scalar_layer(np.where(land, a25, np.nan), f"{base}_2025.png", cmap, vmin, vmax, mask=land))
f_ndvi23, f_ndvi25 = lens_pair(nd23, nd25, "ndvi",   NDVI_CMAP, -0.1, 0.8)   # PDF fig04 동일 컬러맵·스케일
f_nbr23,  f_nbr25  = lens_pair(nb23, nb25, "nbr",    NDVI_CMAP, -0.1, 0.8)
f_vv23,   f_vv25   = lens_pair(vv23, vv25, "vv",     "viridis", -22, -3)
f_lst23,  f_lst25  = lens_pair(la23, la25, "lstrel", "RdBu_r",  -6,  6)
# 토지피복 분류(k-means 3클래스) — 식생→무식생(나지) 급증 (PDF fig07의 웹판)
cls23, _ = read_tif(f"{DATA}/class_2023.tif"); cls25, _ = read_tif(f"{DATA}/class_2025.tif")
CLSMAP = {0: [44, 127, 184, 225], 1: [65, 171, 93, 225], 2: [140, 109, 79, 235]}
f_cls23 = cat_layer(cls23, "class_2023.png", CLSMAP)
f_cls25 = cat_layer(cls25, "class_2025.png", CLSMAP)

# 잔열 상태 (노트북 v2 산출물; 없으면 생략) — fig15·17 팔레트(빨강=잔열, 연주황=냉각)
f_state, LS = None, None
if os.path.exists(f"{DATA}/lava_state.tif") and os.path.exists(f"{DATA}/lava_state_stats.json"):
    st_arr, _ = read_tif(f"{DATA}/lava_state.tif")
    st_arr = np.where(st_arr < -1, np.nan, st_arr)
    with open(f"{DATA}/lava_state_stats.json", encoding="utf-8") as f:
        LS = json.load(f)
    f_state = cat_layer(st_arr, "lava_state.png",
                        {1: [215, 25, 28, 205], 0: [253, 184, 99, 195], 2: [158, 158, 158, 150]})

f_dl = None
if os.path.exists(f"{DATA}/dl_lava_prob.tif"):
    dlp, _ = read_tif(f"{DATA}/dl_lava_prob.tif")
    f_dl = scalar_layer(np.where(land & (dlp > 0.2), dlp, np.nan), "dl_lava.png", "hot", 0, 1, mask=land)

# ---- 픽셀 인스펙터용 다운샘플 그리드 (web mercator, 1/4 해상도 ≈ 40m) ----
print("픽셀 인스펙터 데이터 export → web/pixdata.js ...")
DS = 4
NODATA = -99999

def pix(a, scale, resampling=Resampling.bilinear):
    w = warp(a, resampling)[::DS, ::DS]
    g = np.where(np.isfinite(w), np.round(w*scale), NODATA)
    return g.astype("int32"), w.shape

(_g_dn, (pH, pW)) = pix(np.where(land, dN, np.nan), 1000)
PIX = {
    "w": pW, "h": pH, "b": [round(v, 1) for v in db], "nd": NODATA,
    "layers": {
        "dndvi": _g_dn.ravel().tolist(),                                        # ×1000
        "dvv":   pix(np.where(land, dvv, np.nan), 100)[0].ravel().tolist(),     # ×100 (dB)
        "anom":  pix(np.where(land, anom, np.nan), 100)[0].ravel().tolist(),    # ×100 (°C)
        "code":  pix(code, 1, Resampling.nearest)[0].ravel().tolist(),          # 0/1/2
        "state": (pix(st_arr, 1, Resampling.nearest)[0].ravel().tolist()
                  if f_state else []),                                          # 0/1/2
    },
}

# ---- 위험도 연결선: 자산 ↔ 최근접 합의용암 (fig15와 동일 정의) ----
T = Transformer.from_crs(4326, 32627, always_xy=True)
Ti = Transformer.from_crs(32627, 4326, always_xy=True)
lava_m = (code == 1) & land
rr, cc = np.where(lava_m); xs_ = b[0]+(cc+0.5)*10.0; ys_ = b[3]-(rr+0.5)*10.0
HAZ = []
for nm, (lon, lat) in {"그린다비크 읍": (-22.437, 63.836), "Svartsengi 발전소": (-22.451, 63.881),
                       "블루라군": (-22.449, 63.880)}.items():
    ax_, ay_ = T.transform(lon, lat)
    d = np.hypot(xs_-ax_, ys_-ay_); k = int(d.argmin())
    nlon, nlat = Ti.transform(float(xs_[k]), float(ys_[k]))
    HAZ.append({"name": nm, "a": [lat, lon], "b": [round(nlat, 5), round(nlon, 5)],
                "d": int(round(float(d[k])))})
    print(f"  위험선 {nm}: {d[k]:.0f} m")

YEARS = [
    {"id": "tc2023", "name": "2023 분화 전", "file": f_tc23, "date": ST.get("dates", {}).get("2023", "2023-09")},
    {"id": "tc2024", "name": "2024 분화 중", "file": f_tc24, "date": ST.get("dates", {}).get("2024", "2024-09")},
    {"id": "tc2025", "name": "2025 분화 후", "file": f_tc25, "date": ST.get("dates", {}).get("2025", "2025-09")},
]
LENSES = [
    {"id": "tc", "name": "트루컬러", "before": f_tc23, "after": f_tc25,
     "legend": {"type": "text", "text": "가공 없는 광학 트루컬러 — 검은 신규 용암"}},
    {"id": "class", "name": "토지피복 분류", "before": f_cls23, "after": f_cls25,
     "legend": {"type": "cat", "items": [["#2c7fb8", "수역"], ["#41ab5d", "식생·이끼 (감소)"],
                ["#8c6d4f", f"나지·용암 ({ST['class_area']['2023'][2]:.0f}→{ST['class_area']['2025'][2]:.0f} km² 급증)"]]}},
    {"id": "ndvi", "name": "NDVI 식생지수", "before": f_ndvi23, "after": f_ndvi25,
     "legend": {"type": "grad", "stops": stops(NDVI_CMAP), "lo": "-0.1 (용암·나지)", "hi": "0.8 (식생)"}},
    {"id": "nbr", "name": "NBR 연소지수", "before": f_nbr23, "after": f_nbr25,
     "legend": {"type": "grad", "stops": stops(NDVI_CMAP), "lo": "-0.1", "hi": "0.8"}},
    {"id": "vv", "name": "SAR VV 후방산란", "before": f_vv23, "after": f_vv25,
     "legend": {"type": "grad", "stops": stops("viridis"), "lo": "-22 dB (매끈)", "hi": "-3 dB (거침·용암)"}},
    {"id": "lst", "name": "LST 상대이상치", "before": f_lst23, "after": f_lst25,
     "legend": {"type": "grad", "stops": stops("RdBu_r"), "lo": "-6°C", "hi": "+6°C (승온)"}},
]
OVERLAYS = [
    {"id": "consensus", "name": "★ 다중센서 합의 신규 용암", "file": f_lava, "on": True,
     "legend": {"type": "cat", "items": [["#d91a1a", f"합의 용암 {ST['lava_km2']:.0f} km²"],
                                          ["#fa9e33", f"광학단독(잡음) {ST['lava_optonly_km2']:.0f} km²"]]}},
]
if f_state:
    ap = LS["area_pred"]
    OVERLAYS.append({"id": "state", "name": "◆ 잔열 상태 (광학+SAR 딥러닝)", "file": f_state, "on": False,
                     "legend": {"type": "cat", "items": [
                         ["#d7191c", f"잔열(아직 따뜻) {ap['hot']:.1f} km²"],
                         ["#fdb863", f"냉각(배경 수준) {ap['cold']:.1f} km²"],
                         ["#9e9e9e", f"SAR 결측 {ap['gap']:.1f} km²"]]}})
if f_dl:
    OVERLAYS.append({"id": "dl", "name": "◆ 딥러닝 용암확률 (U-Net)", "file": f_dl, "on": False,
                     "legend": {"type": "grad", "stops": stops("hot"), "lo": "0", "hi": "1 (용암)"}})

_d = {h["name"]: h["d"] for h in HAZ}
MARKS = [
    {"name": "Sundhnúkur 분화구열", "lat": 63.892, "lon": -22.375, "desc": "2023–2025 분화 중심 (Sundhnúksgígar)"},
    {"name": "그린다비크 (읍)", "lat": 63.836, "lon": -22.437,
     "desc": f"용암 위협으로 주민 대피·방어벽 건설 · 최근접 용암 {_d['그린다비크 읍']/1000:.1f} km"},
    {"name": "블루라군·Svartsengi", "lat": 63.880, "lon": -22.449,
     "desc": f"지열발전소·관광지 · 최근접 용암 {_d['Svartsengi 발전소']} m"},
    {"name": "Þorbjörn", "lat": 63.861, "lon": -22.443, "desc": "지반융기 관측 화산"},
]

INDEX_HTML = r"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>아이슬란드 Grindavík 분화 — 위성 변화탐지</title>
<link rel="stylesheet" href="lib/leaflet.css"/>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.css"/>
<style>
  :root{
    --bg:#0a0f16; --panel:rgba(13,21,32,.80); --panel2:rgba(20,31,46,.72);
    --line:rgba(255,255,255,.10); --txt:#eaf1f6; --sub:#9bb0bd;
    --teal:#3ad0b8; --amber:#f4ad47; --lava:#ff3b2f; --danger:#ff5a5a;
    --shadow:0 8px 30px rgba(0,0,0,.45);
  }
  *{box-sizing:border-box}
  html,body{margin:0;height:100%;
    font-family:'Pretendard','Apple SD Gothic Neo','Malgun Gothic','Segoe UI',system-ui,sans-serif;
    background:var(--bg);color:var(--txt);-webkit-font-smoothing:antialiased}
  #map{position:absolute;inset:0;background:#070b11;cursor:crosshair}
  .card{position:absolute;z-index:1000;background:var(--panel);
    border:1px solid var(--line);border-radius:14px;box-shadow:var(--shadow);
    backdrop-filter:blur(10px) saturate(1.1);-webkit-backdrop-filter:blur(10px) saturate(1.1)}

  /* ── 컨트롤 패널 ── */
  #panel{top:16px;right:16px;width:264px;padding:4px 14px 12px;max-height:90%;overflow:auto}
  #panel::-webkit-scrollbar{width:7px}#panel::-webkit-scrollbar-thumb{background:rgba(255,255,255,.14);border-radius:4px}
  .sec{padding:11px 0;border-bottom:1px solid var(--line)}
  .sec:last-child{border-bottom:0}
  .sec h2{font-size:10.5px;margin:0 0 8px;color:var(--teal);text-transform:uppercase;letter-spacing:1.4px;font-weight:700}
  .sec h2 .q{color:var(--sub);text-transform:none;letter-spacing:0;font-weight:500;font-size:10.5px}
  label.row{display:flex;align-items:center;gap:9px;font-size:13px;margin:6px 0;cursor:pointer;color:#dce7ed}
  label.row:hover{color:#fff}
  label.row.lens{font-weight:600}
  input[type=checkbox],input[type=radio]{accent-color:var(--teal);width:15px;height:15px;cursor:pointer;flex:none}
  .star{color:var(--lava);font-weight:800}.diamond{color:var(--amber)}
  input[type=range]{width:100%;accent-color:var(--teal);cursor:pointer}
  .opval{float:right;font-size:11px;color:var(--sub)}

  /* ── 인트로 ── */
  #intro{position:absolute;inset:0;z-index:3000;display:flex;flex-direction:column;
    align-items:center;justify-content:center;text-align:center;cursor:pointer;
    background:radial-gradient(120% 90% at 50% 35%,rgba(12,20,32,.55),rgba(6,10,17,.92));
    transition:opacity .9s ease,visibility .9s}
  #intro.gone{opacity:0;visibility:hidden;pointer-events:none}
  #intro .eyebrow{font-size:13px;letter-spacing:5px;color:var(--teal);font-weight:700;text-transform:uppercase}
  #intro h1{margin:14px 24px 0;font-size:clamp(26px,4.4vw,52px);font-weight:800;line-height:1.15;
    letter-spacing:-.5px;text-shadow:0 3px 30px rgba(0,0,0,.6)}
  #intro p{margin:16px 24px 0;font-size:clamp(13px,1.5vw,16px);color:#c4d4dd;max-width:700px;line-height:1.6}
  #intro .go{margin-top:30px;font-size:12.5px;color:var(--sub);letter-spacing:.5px;
    border:1px solid var(--line);border-radius:30px;padding:9px 20px;background:rgba(255,255,255,.04)}
  #intro .go b{color:var(--teal)}

  /* ── 스와이프 ── */
  #swipe{position:absolute;top:0;bottom:0;z-index:600;pointer-events:none;transform:translateX(-50%)}
  #swipeLine{position:absolute;top:0;bottom:0;left:50%;width:2px;margin-left:-1px;
    background:rgba(255,255,255,.85);box-shadow:0 0 12px rgba(0,0,0,.6)}
  #swipeHandle{position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);
    width:42px;height:42px;border-radius:50%;background:rgba(13,21,32,.92);
    border:2px solid #fff;box-shadow:0 4px 16px rgba(0,0,0,.55);
    display:flex;align-items:center;justify-content:center;color:#fff;font-size:17px;
    cursor:ew-resize;pointer-events:auto;touch-action:none}
  #swipeHandle:hover{background:var(--teal);color:#06231f}
  #swPill{position:absolute;top:16px;left:50%;transform:translateX(-50%);display:flex;
    pointer-events:none;font-size:11.5px;font-weight:700;border-radius:8px;overflow:hidden;
    box-shadow:0 3px 12px rgba(0,0,0,.5);white-space:nowrap}
  #swPill span{padding:5px 11px;background:rgba(13,21,32,.9)}
  #swPill .b{color:#cfe0e6}#swPill .a{color:#ffb9b3;background:rgba(40,14,12,.9)}
  #lensTag{position:absolute;top:80px;left:11px;z-index:1000;font-size:12px;font-weight:700;
    padding:7px 12px;border-radius:9px}
  #lensTag b{color:var(--teal)}

  /* ── 범례 ── */
  #legend{bottom:18px;left:16px;max-width:290px;padding:12px 14px;font-size:12px;z-index:1000}
  #legend .lg{margin-bottom:10px}#legend .lg:last-child{margin-bottom:0}
  #legend .nm{font-weight:700;color:#fff;margin-bottom:4px;font-size:12px}
  #legend .bar{height:10px;border-radius:4px;margin:3px 0}
  #legend .mm{display:flex;justify-content:space-between;color:var(--sub);font-size:11px}
  #legend .sw{display:inline-block;width:12px;height:12px;border-radius:3px;margin-right:6px;vertical-align:-1px}

  /* ── 픽셀 판독 팝업 ── */
  .leaflet-popup-content-wrapper{background:var(--panel);color:var(--txt);border:1px solid var(--line);
    border-radius:12px;box-shadow:var(--shadow);backdrop-filter:blur(10px)}
  .leaflet-popup-tip{background:var(--panel)}
  .pxt{border-collapse:collapse;margin-top:4px;width:100%}
  .pxt td{padding:2px 8px;font-size:12px;border-bottom:1px solid var(--line)}
  .pxt td:first-child{color:var(--sub)}.pxt td:last-child{text-align:right;font-weight:700}
  .verdict{display:inline-block;margin-top:7px;padding:4px 10px;border-radius:7px;color:#fff;font-size:12px;font-weight:700}
  .hazlab{background:rgba(13,21,32,.92)!important;border:1px solid var(--line)!important;color:#ffb9b3!important;
    font-weight:700;font-size:11px;padding:2px 7px;border-radius:6px;box-shadow:0 2px 8px rgba(0,0,0,.5)}
  .hazlab::before{display:none!important}

  .credit{position:absolute;bottom:3px;right:8px;z-index:900;color:#7e93a0;font-size:10px}
  .leaflet-bar a{background:var(--panel2);color:var(--txt);border-color:var(--line)}
  .leaflet-bar a:hover{background:var(--teal);color:#06231f}
  #errbar{position:absolute;top:0;left:0;right:0;z-index:4000;background:#b00020;color:#fff;padding:8px 12px;font-size:13px;display:none}
  a{color:var(--teal)}
</style>
</head>
<body>
<div id="errbar"></div>
<div id="map"></div>

<div id="intro">
  <div class="eyebrow">Multi-sensor Change Detection · 2023 → 2025</div>
  <h1>아이슬란드 Grindavík–Sundhnúkur 분화</h1>
  <p>왼쪽 <b>비교 지표</b>를 고르고 가운데 손잡이를 끌면, 같은 지표의 <b>2023 ↔ 2025</b>가 동일 척도로 스와이프 비교된다
     (트루컬러·NDVI·NBR·SAR VV·LST). 지도를 클릭하면 그 지점의 센서값이 즉석 판독된다.</p>
  <div class="go">아무 곳이나 클릭하면 <b>지도로 진입</b>합니다</div>
</div>

<div id="lensTag" class="card">비교 지표 · <b id="lensName">트루컬러</b></div>

<div id="panel" class="card">
  <div class="sec">
    <h2>비교 지표 <span class="q">— 2023 ↔ 2025 스와이프</span></h2>
    <div id="lenslist"></div>
  </div>
  <div class="sec">
    <h2>결과 레이어</h2>
    <div id="ovlist"></div>
  </div>
  <div class="sec">
    <h2>베이스맵</h2>
    <label class="row"><input type="radio" name="base" value="dark" checked> 다크 카토그래피 (CARTO)</label>
    <label class="row"><input type="radio" name="base" value="sat"> 위성영상 (Esri)</label>
    <label class="row"><input type="radio" name="base" value="osm"> 일반지도 (OSM)</label>
  </div>
  <div class="sec">
    <h2>지물</h2>
    <label class="row"><input type="checkbox" id="marks" checked> 주요 지물·자산</label>
    <label class="row"><input type="checkbox" id="haz"> 위험도 연결선 (최근접 용암 거리)</label>
  </div>
  <div class="sec">
    <h2>결과 레이어 투명도 <span class="opval" id="opval">85%</span></h2>
    <input type="range" id="op" min="25" max="100" value="85">
  </div>
</div>

<div id="swipe">
  <div id="swPill"><span class="b">◀ 2023 분화 전</span><span class="a">2025 분화 후 ▶</span></div>
  <div id="swipeLine"></div>
  <div id="swipeHandle">⇄</div>
</div>

<div id="legend" class="card"></div>
<div class="credit">Sentinel-2/1 · Landsat 8/9 · STAC(AWS·PC) | Base © Esri / © OSM © CARTO | 클릭 = 픽셀 판독</div>

<script src="lib/leaflet.js"></script>
<script src="layers.js"></script>
<script src="pixdata.js"></script>
<script>
function showErr(m){var e=document.getElementById('errbar');if(e){e.style.display='block';e.textContent='⚠ '+m;}console.error(m);}
window.addEventListener('error',function(ev){showErr((ev.message||'오류')+' @'+String(ev.filename||'').split('/').pop()+':'+ev.lineno);});
try{
const Icon=L.icon({iconUrl:'lib/marker-icon.png',iconRetinaUrl:'lib/marker-icon-2x.png',
  shadowUrl:'lib/marker-shadow.png',iconSize:[25,41],iconAnchor:[12,41],popupAnchor:[1,-34],shadowSize:[41,41]});

const map=L.map('map',{zoomControl:true,attributionControl:false}).setView([64.9,-18.7],6);
L.control.scale({imperial:false,position:'bottomright'}).addTo(map);

// ── 베이스맵 ──
const bases={
  dark:L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',{subdomains:'abcd',maxZoom:19}),
  sat :L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',{maxZoom:19}),
  osm :L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:19})
};
let curBase=bases.dark.addTo(map);
document.querySelectorAll('input[name=base]').forEach(r=>r.addEventListener('change',e=>{
  map.removeLayer(curBase);curBase=bases[e.target.value].addTo(map);curBase.bringToBack();}));

// ── 전/후 패널(panes) — 같은 지표(lens)의 2023 vs 2025 ──
map.createPane('before');map.getPane('before').style.zIndex=300;
map.createPane('after'); map.getPane('after').style.zIndex=350;
let curLens=LENSES[0];
const beforeImg=L.imageOverlay(curLens.before,BOUNDS,{pane:'before',opacity:1}).addTo(map);
const afterImg =L.imageOverlay(curLens.after ,BOUNDS,{pane:'after' ,opacity:1}).addTo(map);
function setLens(id){curLens=LENSES.find(l=>l.id===id)||LENSES[0];
  beforeImg.setUrl(curLens.before);afterImg.setUrl(curLens.after);
  document.getElementById('lensName').textContent=curLens.name;buildLegend();}

// ── 결과 레이어 → '분화 후(2025)' 패널 위에 ──
let curOp=0.85;
const ov={};
OVERLAYS.forEach(o=>{ov[o.id]=L.imageOverlay(o.file,BOUNDS,{pane:'after',opacity:curOp});if(o.on)ov[o.id].addTo(map);});

// ── 스와이프 클립 ──
const swEl=document.getElementById('swipe');
let divRatio=0.5;
function clipAfter(){
  const size=map.getSize();if(!size.x)return;
  const dx=size.x*divRatio;
  const tl=map.containerPointToLayerPoint([0,0]);
  const br=map.containerPointToLayerPoint([size.x,size.y]);
  const cx=map.containerPointToLayerPoint([dx,0]).x;
  map.getPane('after').style.clip='rect('+tl.y+'px,'+br.x+'px,'+br.y+'px,'+cx+'px)';
  swEl.style.left=dx+'px';
}
map.on('move zoom zoomend zoomanim viewreset resize load',clipAfter);

// 손잡이 드래그
const handle=document.getElementById('swipeHandle');
function setRatio(clientX){const r=map.getContainer().getBoundingClientRect();
  divRatio=Math.max(0.02,Math.min(0.98,(clientX-r.left)/r.width));clipAfter();}
handle.addEventListener('pointerdown',e=>{e.preventDefault();map.dragging.disable();
  const mv=ev=>setRatio(ev.clientX);
  const up=()=>{map.dragging.enable();window.removeEventListener('pointermove',mv);window.removeEventListener('pointerup',up);};
  window.addEventListener('pointermove',mv);window.addEventListener('pointerup',up);});

// ── 마커 / 위험도 연결선 ──
const mlayer=L.layerGroup(MARKS.map(m=>L.marker([m.lat,m.lon],{icon:Icon}).bindPopup('<b>'+m.name+'</b><br>'+m.desc))).addTo(map);
const hlayer=L.layerGroup(HAZ.map(h=>{
  const col=h.d<200?'#ff4040':'#2fd07a';
  const line=L.polyline([h.a,h.b],{color:col,weight:3,dashArray:'7 6',opacity:.95});
  const mid=[(h.a[0]+h.b[0])/2,(h.a[1]+h.b[1])/2];
  const lab=L.tooltip({permanent:true,direction:'top',className:'hazlab',offset:[0,-2]})
    .setLatLng(mid).setContent(h.name+' '+(h.d<1000?h.d+' m':(h.d/1000).toFixed(1)+' km'));
  return L.layerGroup([line,lab]);
}));
document.getElementById('marks').addEventListener('change',e=>{e.target.checked?mlayer.addTo(map):map.removeLayer(mlayer);});
document.getElementById('haz').addEventListener('change',e=>{e.target.checked?hlayer.addTo(map):map.removeLayer(hlayer);});

// ── 비교 지표(lens) 라디오 ──
const lenslist=document.getElementById('lenslist');
LENSES.forEach((l,i)=>{
  const lab=document.createElement('label');lab.className='row lens';
  lab.innerHTML='<input type="radio" name="lens" value="'+l.id+'" '+(i===0?'checked':'')+'> '+l.name;
  lenslist.appendChild(lab);
  lab.querySelector('input').addEventListener('change',e=>{if(e.target.checked)setLens(l.id);});
});

// ── 결과 레이어 체크박스 ──
const ovlist=document.getElementById('ovlist');
OVERLAYS.forEach(o=>{
  const lab=document.createElement('label');lab.className='row';
  const nm=o.name.startsWith('★')?'<span class="star">★</span>'+o.name.slice(1)
          :o.name.startsWith('◆')?'<span class="diamond">◆</span>'+o.name.slice(1):o.name;
  lab.innerHTML='<input type="checkbox" id="ck_'+o.id+'" '+(o.on?'checked':'')+'> '+nm;
  ovlist.appendChild(lab);
  lab.querySelector('input').addEventListener('change',e=>{
    if(e.target.checked)ov[o.id].addTo(map);else map.removeLayer(ov[o.id]);buildLegend();});
});
const op=document.getElementById('op'),opval=document.getElementById('opval');
op.addEventListener('input',e=>{curOp=e.target.value/100;opval.textContent=e.target.value+'%';
  OVERLAYS.forEach(o=>ov[o.id].setOpacity(curOp));});

// ── 픽셀 인스펙터 (Δ값은 변화탐지 산출물 기준) ──
function merc(lat,lon){const R=6378137;return [R*lon*Math.PI/180,R*Math.log(Math.tan(Math.PI/4+lat*Math.PI/360))];}
function pxv(layer,lat,lon){const a=PX.layers[layer];if(!a||!a.length)return null;
  const m=merc(lat,lon);
  const c=Math.floor((m[0]-PX.b[0])/(PX.b[2]-PX.b[0])*PX.w);
  const r=Math.floor((PX.b[3]-m[1])/(PX.b[3]-PX.b[1])*PX.h);
  if(c<0||r<0||c>=PX.w||r>=PX.h)return null;const v=a[r*PX.w+c];return v===PX.nd?null:v;}
const fmt=(v,d,u)=>v===null?'—':(v>0?'+':'')+v.toFixed(d)+u;
map.on('click',e=>{
  const la=e.latlng.lat,lo=e.latlng.lng;
  const dn=pxv('dndvi',la,lo),dv=pxv('dvv',la,lo),an=pxv('anom',la,lo),cd=pxv('code',la,lo),st=pxv('state',la,lo);
  if(dn===null&&dv===null&&an===null)return;
  let verdict='변화 없음 / 비용암',vc='#5f7888';
  if(cd===1){verdict='다중센서 합의 용암';vc='#d91a1a';
    if(an!==null){const a2=an/100;if(a2>=3.5)verdict+=' · 잔열';else if(a2<1.5){verdict+=' · 냉각';vc='#b8722c';}else verdict+=' · 미온(모호)';}}
  else if(cd===2){verdict='광학단독 탐지 (잡음 가능)';vc='#e8862d';}
  const mdl=cd===1?(st===1?'잔열':st===0?'냉각':st===2?'SAR 결측':'—'):null;
  const html='<b>픽셀 판독</b> <span style="color:#7e93a0;font-size:11px">('+la.toFixed(4)+'°N, '+Math.abs(lo).toFixed(4)+'°W)</span>'+
    '<table class="pxt">'+
    '<tr><td>광학 ΔNDVI (23→25)</td><td>'+fmt(dn===null?null:dn/1000,2,'')+'</td></tr>'+
    '<tr><td>SAR ΔVV (23→25)</td><td>'+fmt(dv===null?null:dv/100,1,' dB')+'</td></tr>'+
    '<tr><td>열 ΔLST′ (배경보정)</td><td>'+fmt(an===null?null:an/100,1,' °C')+'</td></tr>'+
    (mdl?'<tr><td>모델 추정(광학+SAR)</td><td>'+mdl+'</td></tr>':'')+
    '</table><span class="verdict" style="background:'+vc+'">'+verdict+'</span>';
  L.popup({maxWidth:270}).setLatLng(e.latlng).setContent(html).openOn(map);
});

// ── 범례 (현재 지표 + 활성 결과 레이어) ──
function legendBlock(name,lg){
  let h='<div class="lg"><div class="nm">'+name.replace('★','★ ').replace('◆','◆ ')+'</div>';
  if(lg.type==='grad')h+='<div class="bar" style="background:linear-gradient(90deg,'+lg.stops.join(',')+')"></div><div class="mm"><span>'+lg.lo+'</span><span>'+lg.hi+'</span></div>';
  else if(lg.type==='cat')lg.items.forEach(it=>h+='<div><span class="sw" style="background:'+it[0]+'"></span>'+it[1]+'</div>');
  else if(lg.type==='text')h+='<div class="mm"><span>'+lg.text+'</span></div>';
  return h+'</div>';
}
function buildLegend(){
  const el=document.getElementById('legend');let h='';
  if(curLens&&curLens.legend)h+=legendBlock('지표 — '+curLens.name+' (2023↔2025)',curLens.legend);
  OVERLAYS.forEach(o=>{if(map.hasLayer(ov[o.id])&&o.legend)h+=legendBlock(o.name,o.legend);});
  el.innerHTML=h;el.style.display=h?'':'none';
}

// ── 인트로 → 진입 ──
const intro=document.getElementById('intro');let entered=false;
function enter(){if(entered)return;entered=true;
  map.flyToBounds(BOUNDS,{duration:2.6});
  map.once('moveend',()=>{clipAfter();});
  setTimeout(()=>intro.classList.add('gone'),700);
  setTimeout(clipAfter,3000);
}
intro.addEventListener('click',enter);
setTimeout(()=>{if(!entered)enter();},6000);

map.whenReady(()=>{divRatio=0.5;clipAfter();buildLegend();});
}catch(e){showErr('초기화 오류: '+e.message);}
</script>
</body>
</html>
"""

layers_js = (
    "// 자동 생성 (08_web.py)\n"
    f"const CENTER={json.dumps([round(c,4) for c in CENTER])};\n"
    f"const BOUNDS={json.dumps([[round(v,5) for v in BOUNDS[0]], [round(v,5) for v in BOUNDS[1]]])};\n"
    f"const YEARS={json.dumps(YEARS, ensure_ascii=False)};\n"
    f"const LENSES={json.dumps(LENSES, ensure_ascii=False)};\n"
    f"const OVERLAYS={json.dumps(OVERLAYS, ensure_ascii=False)};\n"
    f"const MARKS={json.dumps(MARKS, ensure_ascii=False)};\n"
    f"const HAZ={json.dumps(HAZ, ensure_ascii=False)};\n"
    f"const STATS={json.dumps(ST, ensure_ascii=False)};\n"
    f"const LSTATE={json.dumps(LS, ensure_ascii=False)};\n"
)
with open(os.path.join(WEB, "layers.js"), "w", encoding="utf-8") as f:
    f.write(layers_js)
with open(os.path.join(WEB, "pixdata.js"), "w", encoding="utf-8") as f:
    f.write("// 자동 생성 (08_web.py) — 픽셀 인스펙터용 1/4해상도 그리드 (3857)\n")
    f.write(f"const PX={json.dumps(PIX, separators=(',', ':'))};\n")
with open(os.path.join(WEB, "index.html"), "w", encoding="utf-8") as f:
    f.write(INDEX_HTML)
print(f"웹맵 생성 완료: {WEB}/index.html  (시점 {len(YEARS)} · 분석 레이어 {len(OVERLAYS)}종 · 위험선 {len(HAZ)})")
