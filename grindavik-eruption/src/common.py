"""공통 설정·그리드·원격 COG 읽기 — 아이슬란드 Grindavík 화산 변화탐지.

Sentinel-2(광학) 3시기 + Sentinel-1 RTC(SAR) + Landsat(지표온도)를
동일 UTM 27N · 10m 격자로 정렬. 교수님(이어루) 백두산 광학+SAR 연구 응용.
"""
import os
import json
import numpy as np
import rasterio
from rasterio.warp import transform_bounds, reproject, Resampling
from rasterio.transform import from_origin
from rasterio.windows import from_bounds as win_from_bounds

ROOT = "/workspace/원격탐사/project_iceland"
DATA = os.path.join(ROOT, "data"); FIG = os.path.join(ROOT, "figures")
OUT = os.path.join(ROOT, "outputs"); WEB = os.path.join(ROOT, "web")
for d in (DATA, FIG, OUT, WEB):
    os.makedirs(d, exist_ok=True)

STAC_AWS = "https://earth-search.aws.element84.com/v1"
STAC_PC = "https://planetarycomputer.microsoft.com/api/stac/v1"

# Grindavík / Sundhnúkur 분화구열 / 블루라군·Svartsengi 포함
DOWNLOAD_BBOX = [-22.55, 63.815, -22.28, 63.945]   # W,S,E,N
DST_CRS = "EPSG:32627"   # UTM 27N (아이슬란드 남서부)
RES = 10.0

# Sentinel-2 L2A 3시기 (운량 0%) — 분화 전→중→후
S2_DATES = {"2023": "2023-08-13", "2024": "2024-09-15", "2025": "2025-06-13"}
S2_ASSETS = {"blue":"blue","green":"green","red":"red","nir":"nir","swir16":"swir16","swir22":"swir22"}
S2_SCL = "scl"

# Sentinel-1 RTC (PC, IW VV/VH) 전/후 — 시점은 다운로드 시 자동탐색
S1_PERIODS = {"2023": "2023-06-01/2023-09-30", "2025": "2025-05-01/2025-07-31"}
# Landsat C2L2 지표온도 전/후
LS_PERIODS = {"2023": "2023-06-01/2023-09-15", "2025": "2025-05-01/2025-08-31"}
LST_SCALE, LST_OFFSET = 0.00341802, 149.0


def target_grid():
    l, b, r, t = transform_bounds("EPSG:4326", DST_CRS, *DOWNLOAD_BBOX)
    l = np.floor(l/RES)*RES; b = np.floor(b/RES)*RES
    r = np.ceil(r/RES)*RES; t = np.ceil(t/RES)*RES
    w = int(round((r-l)/RES)); h = int(round((t-b)/RES))
    return from_origin(l, t, RES, RES), w, h, (l, b, r, t)


def _env():
    return rasterio.Env(GDAL_HTTP_MULTIPLEX="YES", GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR",
                        CPL_VSIL_CURL_ALLOWED_EXTENSIONS=".tif,.tiff,.TIF,.TIFF",
                        GDAL_HTTP_MAX_RETRY="5", GDAL_HTTP_RETRY_DELAY="1", VSI_CACHE="TRUE")


def fetch(url, transform, w, h, resampling=Resampling.bilinear, band=1):
    l, t = transform.c, transform.f; r = l + w*RES; b = t - h*RES
    with _env(), rasterio.open(url) as src:
        sb = transform_bounds(DST_CRS, src.crs, l, b, r, t)
        win = win_from_bounds(*sb, transform=src.transform).round_offsets(op="floor").round_lengths(op="ceil")
        pad = 6
        win = rasterio.windows.Window(win.col_off-pad, win.row_off-pad, win.width+2*pad, win.height+2*pad)
        arr = src.read(band, window=win, boundless=True, fill_value=0).astype("float32")
        wt = src.window_transform(win)
        dst = np.zeros((h, w), "float32")
        reproject(arr, dst, src_transform=wt, src_crs=src.crs, dst_transform=transform,
                  dst_crs=DST_CRS, resampling=resampling, src_nodata=0, dst_nodata=0)
    return dst


def write_tif(path, arr, transform, crs=DST_CRS, nodata=np.nan):
    if arr.ndim == 2: arr = arr[None]
    c, h, w = arr.shape
    with rasterio.open(path, "w", driver="GTiff", height=h, width=w, count=c, dtype="float32",
                       crs=crs, transform=transform, nodata=nodata, compress="deflate", predictor=2) as d:
        d.write(arr.astype("float32"))


def read_tif(path):
    with rasterio.open(path) as src:
        a = src.read().astype("float32"); p = src.profile
    return (a[0] if a.shape[0] == 1 else a), p


STATS = os.path.join(DATA, "stats.json")


def put_stats(**kw):
    """분석 수치를 stats.json에 누적 저장 (content.py·figures가 공유하는 단일 소스)."""
    d = {}
    if os.path.exists(STATS):
        with open(STATS, encoding="utf-8") as f: d = json.load(f)
    d.update(kw)
    with open(STATS, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    return d


def get_stats():
    with open(STATS, encoding="utf-8") as f: return json.load(f)
