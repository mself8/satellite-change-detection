"""Landsat 지표온도(LST)를 Planetary Computer에서 자동 재시도로 확보.

PC STAC API가 간헐적 504를 내므로, item-by-id 직접 조회 + 장기 재시도.
PC 복구 시 lst_2017.tif / lst_2025.tif 생성. 멱등(이미 있으면 건너뜀).
"""
import warnings; warnings.filterwarnings("ignore")
import os, sys, time, json
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np, requests, rasterio
import planetary_computer as pc
from rasterio.warp import Resampling
from common import DATA, LST_SCALE, LST_OFFSET, target_grid, fetch, write_tif

PC = "https://planetarycomputer.microsoft.com/api/stac/v1"
CANDIDATES = {
    "2017": ["LC08_L2SP_116034_20171029_02_T1",
             "LC08_L2SP_116034_20171130_02_T1",
             "LC08_L2SP_116034_20171114_02_T1"],
    "2025": ["LC09_L2SP_116034_20251027_02_T1",
             "LC09_L2SP_116034_20251112_02_T1",
             "LC08_L2SP_116034_20251104_02_T1"],
}
transform, W, H, _ = target_grid()


def get_item(item_id):
    r = requests.get(f"{PC}/collections/landsat-c2-l2/items/{item_id}", timeout=60)
    r.raise_for_status()
    return r.json()


def process(yr):
    out = os.path.join(DATA, f"lst_{yr}.tif")
    if os.path.exists(out):
        print(f"[{yr}] 이미 존재, 건너뜀"); return True
    for cid in CANDIDATES[yr]:
        try:
            item = get_item(cid)
            st_href = pc.sign(item["assets"]["lwir11"]["href"])
            qa_href = pc.sign(item["assets"]["qa_pixel"]["href"])
            st = fetch(st_href, transform, W, H, Resampling.bilinear)
            qa = fetch(qa_href, transform, W, H, Resampling.nearest)
            lst = st * LST_SCALE + LST_OFFSET - 273.15
            qa_i = qa.astype(np.uint16)
            bad = (st == 0)
            for bit in (1, 3, 4):  # dilated, cloud, shadow
                bad |= ((qa_i >> bit) & 1).astype(bool)
            lst[bad] = np.nan
            write_tif(out, lst, transform)
            print(f"[{yr}] OK {cid} cloud={item['properties'].get('eo:cloud_cover'):.1f} "
                  f"유효{np.isfinite(lst).mean()*100:.0f}% mean={np.nanmean(lst):.1f}°C")
            return True
        except Exception as e:
            print(f"[{yr}] {cid} 실패: {str(e)[:70]}")
    return False


def main():
    attempts = int(os.environ.get("LST_ATTEMPTS", "60"))
    for k in range(attempts):
        done = all(os.path.exists(os.path.join(DATA, f"lst_{y}.tif"))
                   or process(y) for y in ("2017", "2025"))
        if done:
            print("LST 완료."); return 0
        print(f"... 시도 {k+1}/{attempts} 실패, 60s 후 재시도 (PC 복구 대기)")
        time.sleep(60)
    print("LST 미완료(PC 장기 장애)."); return 1


if __name__ == "__main__":
    sys.exit(main())
