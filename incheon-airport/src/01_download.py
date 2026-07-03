"""Sentinel-2 반사율 6밴드 + SCL, Landsat 지표온도(LST)를 AOI로 클립 저장."""
import warnings; warnings.filterwarnings("ignore")
import os, sys, numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from common import (STAC_URL, DOWNLOAD_BBOX, DST_CRS, S2_DATES, S2_TILE,
                    S2_ASSETS, S2_SCL, LS_DATES, LST_SCALE, LST_OFFSET,
                    DATA, target_grid, fetch, write_tif)
from pystac_client import Client
from rasterio.warp import Resampling

cat = Client.open(STAC_URL)
transform, W, H, bounds = target_grid()
print(f"타깃 그리드: {W}x{H} px @10m, UTM52N, bounds={[round(x) for x in bounds]}")


def s2_item(date):
    s = cat.search(collections=["sentinel-2-l2a"], bbox=DOWNLOAD_BBOX,
                   datetime=f"{date}/{date}", query={"grid:code": {"eq": S2_TILE}})
    return list(s.items())[0]


def landsat_item(date):
    s = cat.search(collections=["landsat-c2-l2"], bbox=DOWNLOAD_BBOX,
                   datetime=f"{date}/{date}",
                   query={"platform": {"in": ["landsat-8", "landsat-9"]}})
    return list(s.items())[0]


# ---- Sentinel-2 ----
band_order = ["blue", "green", "red", "nir", "swir16", "swir22"]
for yr, date in S2_DATES.items():
    it = s2_item(date)
    print(f"\n[S2 {yr}] {it.id}  cloud={it.properties['eo:cloud_cover']:.1f}")
    bands = []
    for b in band_order:
        url = it.assets[S2_ASSETS[b]].href
        arr = fetch(url, transform, W, H, Resampling.bilinear)
        bands.append(arr / 10000.0)   # L2A 반사율 스케일
        print(f"   {b:7s} ok  range=[{np.nanmin(arr/10000):.2f},{np.nanmax(arr/10000):.2f}]")
    stack = np.stack(bands)
    write_tif(os.path.join(DATA, f"s2_{yr}.tif"), stack, transform)
    # SCL (장면분류: 구름/그림자 마스킹용), 최근접
    scl = fetch(it.assets[S2_SCL].href, transform, W, H, Resampling.nearest)
    write_tif(os.path.join(DATA, f"scl_{yr}.tif"), scl, transform, nodata=0)
    print(f"   -> s2_{yr}.tif (밴드순: {band_order}), scl_{yr}.tif")

# ---- Landsat 지표온도 ----
for yr, date in LS_DATES.items():
    it = landsat_item(date)
    print(f"\n[LST {yr}] {it.id}  cloud={it.properties['eo:cloud_cover']:.1f}")
    st = fetch(it.assets["lwir11"].href, transform, W, H, Resampling.bilinear)
    qa = fetch(it.assets["qa_pixel"].href, transform, W, H, Resampling.nearest)
    lst_c = st * LST_SCALE + LST_OFFSET - 273.15
    qa_i = qa.astype(np.uint16)
    cloud = ((qa_i >> 3) & 1).astype(bool)        # cloud
    shadow = ((qa_i >> 4) & 1).astype(bool)       # cloud shadow
    dilated = ((qa_i >> 1) & 1).astype(bool)      # dilated cloud
    lst_c[(st == 0) | cloud | shadow | dilated] = np.nan
    write_tif(os.path.join(DATA, f"lst_{yr}.tif"), lst_c, transform)
    valid = np.isfinite(lst_c)
    print(f"   유효 {valid.mean()*100:.1f}%  LST mean={np.nanmean(lst_c):.1f}°C "
          f"[{np.nanmin(lst_c):.1f},{np.nanmax(lst_c):.1f}]")

print("\n다운로드 완료.")
