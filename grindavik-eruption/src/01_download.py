"""S2(광학 3시기) + S1 RTC(SAR 전/후) + Landsat(지표온도 전/후) 다운로드."""
import warnings; warnings.filterwarnings("ignore")
import os, sys, time, numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from common import (STAC_AWS, STAC_PC, DOWNLOAD_BBOX, DST_CRS, S2_DATES, S2_ASSETS, S2_SCL,
                    S1_PERIODS, LS_PERIODS, LST_SCALE, LST_OFFSET, DATA, target_grid, fetch, write_tif)
from pystac_client import Client
import planetary_computer as pc
from rasterio.warp import Resampling

aws = Client.open(STAC_AWS)
tr, W, H, bnds = target_grid()
print(f"그리드 {W}x{H}@10m UTM27N bounds={[round(x) for x in bnds]}")


def retry(fn, n=5, w=4):
    for i in range(n):
        try: return fn()
        except Exception as e:
            print(f"   retry{i}: {str(e)[:60]}"); time.sleep(w)
    return None

# ---- Sentinel-2 (AWS, 무인증) ----
border = ["blue","green","red","nir","swir16","swir22"]
for yr, date in S2_DATES.items():
    if os.path.exists(f"{DATA}/s2_{yr}.tif"):
        print(f"[S2 {yr}] 이미 있음, 건너뜀"); continue
    it = list(aws.search(collections=["sentinel-2-l2a"], bbox=DOWNLOAD_BBOX,
              datetime=f"{date}/{date}").items())[0]
    print(f"\n[S2 {yr}] {it.id} cloud={it.properties['eo:cloud_cover']:.1f}")
    bands = [fetch(it.assets[S2_ASSETS[b]].href, tr, W, H, Resampling.bilinear)/10000.0 for b in border]
    write_tif(f"{DATA}/s2_{yr}.tif", np.stack(bands), tr)
    scl = fetch(it.assets[S2_SCL].href, tr, W, H, Resampling.nearest)
    write_tif(f"{DATA}/scl_{yr}.tif", scl, tr, nodata=0)
    print(f"   저장 s2_{yr}.tif")

# ---- Sentinel-1 RTC (PC, IW VV/VH) — 전/후 동일 상대궤도 ----
pcat = Client.open(STAC_PC)
def s1_items(period):
    return retry(lambda: list(pcat.search(collections=["sentinel-1-rtc"], bbox=DOWNLOAD_BBOX,
        datetime=period, query={"sar:instrument_mode":{"eq":"IW"}}, max_items=30).items())) or []
s1 = {yr: s1_items(p) for yr, p in S1_PERIODS.items()}
def relorbs(items): return {it.properties.get("sat:relative_orbit") for it in items}
common = relorbs(s1["2023"]) & relorbs(s1["2025"])
print(f"\n[S1] 공통 상대궤도: {sorted(x for x in common if x)}")
ro = sorted(x for x in common if x)[0] if common else None
for yr in ("2023","2025"):
    cand = [it for it in s1[yr] if it.properties.get("sat:relative_orbit")==ro] or s1[yr]
    it = pc.sign(cand[0])
    print(f"[S1 {yr}] {it.id} orbit={it.properties.get('sat:relative_orbit')} {it.properties.get('sat:orbit_state')}")
    vv = retry(lambda: fetch(it.assets["vv"].href, tr, W, H, Resampling.bilinear))
    vh = retry(lambda: fetch(it.assets["vh"].href, tr, W, H, Resampling.bilinear))
    # dB 변환 (선형 RTC -> dB)
    vv_db = 10*np.log10(np.where(vv>0, vv, np.nan)); vh_db = 10*np.log10(np.where(vh>0, vh, np.nan))
    write_tif(f"{DATA}/s1_{yr}.tif", np.stack([vv_db, vh_db]), tr)
    print(f"   저장 s1_{yr}.tif VV dB[{np.nanpercentile(vv_db,2):.0f},{np.nanpercentile(vv_db,98):.0f}]")

# ---- Landsat 지표온도 (PC) ----
def ls_item(period):
    its = retry(lambda: list(pcat.search(collections=["landsat-c2-l2"], bbox=DOWNLOAD_BBOX, datetime=period,
        query={"platform":{"in":["landsat-8","landsat-9"]},"eo:cloud_cover":{"lt":30}}, max_items=30).items())) or []
    return sorted(its, key=lambda x:x.properties["eo:cloud_cover"])
for yr, p in LS_PERIODS.items():
    its = ls_item(p)
    if not its: print(f"[LST {yr}] 없음"); continue
    it = pc.sign(its[0])
    print(f"[LST {yr}] {it.id} cloud={it.properties['eo:cloud_cover']:.1f}")
    st = retry(lambda: fetch(it.assets["lwir11"].href, tr, W, H, Resampling.bilinear))
    qa = retry(lambda: fetch(it.assets["qa_pixel"].href, tr, W, H, Resampling.nearest))
    lst = st*LST_SCALE + LST_OFFSET - 273.15
    qi = qa.astype(np.uint16); bad = (st==0)
    for bit in (1,3,4): bad |= ((qi>>bit)&1).astype(bool)
    lst[bad] = np.nan
    write_tif(f"{DATA}/lst_{yr}.tif", lst, tr)
    print(f"   저장 lst_{yr}.tif 유효{np.isfinite(lst).mean()*100:.0f}% mean={np.nanmean(lst):.1f}°C")
print("\n다운로드 완료")
