"""2023·2025 S2를 AOI 전체 커버 + 저운량 장면으로 재선택·저장."""
import warnings; warnings.filterwarnings("ignore")
import os, sys, numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from common import STAC_AWS, DOWNLOAD_BBOX, DATA, S2_ASSETS, S2_SCL, target_grid, fetch, write_tif
from pystac_client import Client
from rasterio.warp import Resampling

aws = Client.open(STAC_AWS); tr, W, H, b = target_grid()
border = ["blue","green","red","nir","swir16","swir22"]

def pick(yr, dr):
    its = sorted(aws.search(collections=["sentinel-2-l2a"], bbox=DOWNLOAD_BBOX, datetime=dr,
                 query={"eo:cloud_cover":{"lt":25}}, max_items=60).items(),
                 key=lambda x: x.properties['eo:cloud_cover'])
    for it in its:
        red = fetch(it.assets["red"].href, tr, W, H, Resampling.nearest)
        cov = (red > 0).mean()
        if cov < 0.985:
            continue
        scl = fetch(it.assets[S2_SCL].href, tr, W, H, Resampling.nearest)
        cloud = np.isin(scl, [3,8,9,10]).mean()
        print(f"  {it.properties['datetime'][:10]} cov={cov*100:.0f}% AOI구름={cloud*100:.1f}% (tile cloud {it.properties['eo:cloud_cover']:.1f})")
        if cloud < 0.05:
            return it
    return None

for yr, dr in [("2023","2023-05-15/2023-09-30"), ("2025","2025-04-15/2025-09-30")]:
    print(f"[{yr}] 후보 검사:")
    it = pick(yr, dr)
    if not it:
        print(f"  적합 장면 못찾음"); continue
    print(f"→ 선택 {it.id}")
    bands = [fetch(it.assets[S2_ASSETS[k]].href, tr, W, H, Resampling.bilinear)/10000.0 for k in border]
    write_tif(f"{DATA}/s2_{yr}.tif", np.stack(bands), tr)
    scl = fetch(it.assets[S2_SCL].href, tr, W, H, Resampling.nearest)
    write_tif(f"{DATA}/scl_{yr}.tif", scl, tr, nodata=0)
    # 실제 사용 날짜 기록
    with open(f"{DATA}/s2_{yr}.date","w") as f: f.write(it.properties['datetime'][:10])
    print(f"   저장 s2_{yr}.tif ({it.properties['datetime'][:10]})")
print("완료")
