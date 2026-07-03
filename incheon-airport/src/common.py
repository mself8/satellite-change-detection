"""공통 설정 · 그리드 · 원격 COG 윈도우 읽기 헬퍼.

인천국제공항 4단계 확장사업 전후(2017 vs 2025) 변화탐지 프로젝트.
모든 래스터를 동일한 UTM 52N · 10m 그리드로 정렬하여 저장한다.
"""
import os
import numpy as np
import rasterio
from rasterio.warp import transform_bounds, reproject, Resampling
from rasterio.transform import from_origin
from rasterio.windows import from_bounds as win_from_bounds

ROOT = "/workspace/원격탐사/project"
DATA = os.path.join(ROOT, "data")
FIG = os.path.join(ROOT, "figures")
OUT = os.path.join(ROOT, "outputs")
for d in (DATA, FIG, OUT):
    os.makedirs(d, exist_ok=True)

STAC_URL = "https://earth-search.aws.element84.com/v1"

# 다운로드 범위(경위도). 공항 핵심부 + 약간의 맥락 여백.
DOWNLOAD_BBOX = [126.395, 37.415, 126.495, 37.525]   # [W, S, E, N]
DST_CRS = "EPSG:32652"   # WGS84 / UTM zone 52N (인천 = zone 52)
RES = 10.0               # m

# Sentinel-2 L2A 장면 (MGRS 52SBG, 운량 0%, 같은 날짜 10/28)
S2_DATES = {"2017": "2017-10-28", "2025": "2025-10-28"}
S2_TILE = "MGRS-52SBG"

# Sentinel-2 자산 키 (earth-search v1)
S2_ASSETS = {
    "blue": "blue", "green": "green", "red": "red",
    "nir": "nir", "swir16": "swir16", "swir22": "swir22",
}
S2_SCL = "scl"

# Landsat C2L2 후보 (지표온도). S2와 ±1일 정렬 우선.
LS_DATES = {"2017": "2017-10-29", "2025": "2025-10-27"}

# C2L2 ST_B10 스케일 (Kelvin)
LST_SCALE, LST_OFFSET = 0.00341802, 149.0


def target_grid():
    """UTM 52N · 10m 공통 타깃 그리드를 반환."""
    l, b, r, t = transform_bounds("EPSG:4326", DST_CRS, *DOWNLOAD_BBOX)
    l = np.floor(l / RES) * RES
    b = np.floor(b / RES) * RES
    r = np.ceil(r / RES) * RES
    t = np.ceil(t / RES) * RES
    w = int(round((r - l) / RES))
    h = int(round((t - b) / RES))
    transform = from_origin(l, t, RES, RES)
    return transform, w, h, (l, b, r, t)


def _env():
    return rasterio.Env(
        GDAL_HTTP_MULTIPLEX="YES",
        GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR",
        CPL_VSIL_CURL_ALLOWED_EXTENSIONS=".tif,.TIF",
        GDAL_HTTP_MAX_RETRY="5", GDAL_HTTP_RETRY_DELAY="1",
        VSI_CACHE="TRUE",
    )


def fetch(url, transform, w, h, resampling=Resampling.bilinear, band=1):
    """원격 COG에서 AOI 윈도우만 읽어 타깃 그리드로 재투영."""
    l = transform.c
    t = transform.f
    r = l + w * RES
    b = t - h * RES
    with _env(), rasterio.open(url) as src:
        sb = transform_bounds(DST_CRS, src.crs, l, b, r, t)
        win = win_from_bounds(*sb, transform=src.transform)
        win = win.round_offsets(op="floor").round_lengths(op="ceil")
        pad = 6
        win = rasterio.windows.Window(win.col_off - pad, win.row_off - pad,
                                      win.width + 2 * pad, win.height + 2 * pad)
        arr = src.read(band, window=win, boundless=True,
                       fill_value=0).astype("float32")
        wt = src.window_transform(win)
        dst = np.zeros((h, w), dtype="float32")
        reproject(arr, dst, src_transform=wt, src_crs=src.crs,
                  dst_transform=transform, dst_crs=DST_CRS,
                  resampling=resampling, src_nodata=0, dst_nodata=0)
    return dst


def write_tif(path, arr, transform, crs=DST_CRS, nodata=np.nan):
    """단일/다중 밴드 배열을 GeoTIFF로 저장. arr: (H,W) 또는 (B,H,W)."""
    if arr.ndim == 2:
        arr = arr[None]
    count, h, w = arr.shape
    with rasterio.open(path, "w", driver="GTiff", height=h, width=w,
                       count=count, dtype="float32", crs=crs,
                       transform=transform, nodata=nodata,
                       compress="deflate", predictor=2) as dst:
        dst.write(arr.astype("float32"))


def read_tif(path):
    with rasterio.open(path) as src:
        arr = src.read().astype("float32")
        prof = src.profile
    return (arr[0] if arr.shape[0] == 1 else arr), prof
