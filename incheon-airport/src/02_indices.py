"""분광지수(NDVI·NDBI·MNDWI) 및 차분영상 계산·저장.

밴드순: 0=Blue 1=Green 2=Red 3=NIR 4=SWIR1(B11) 5=SWIR2(B12)
"""
import warnings; warnings.filterwarnings("ignore")
import os, sys, numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from common import DATA, read_tif, write_tif, target_grid

transform, W, H, bounds = target_grid()
B, G, R, NIR, SW1, SW2 = 0, 1, 2, 3, 4, 5


def indices(stack):
    g, r, nir, sw1 = stack[G], stack[R], stack[NIR], stack[SW1]
    eps = 1e-6
    ndvi = (nir - r) / (nir + r + eps)
    ndbi = (sw1 - nir) / (sw1 + nir + eps)
    mndwi = (g - sw1) / (g + sw1 + eps)
    return ndvi, ndbi, mndwi


s17, _ = read_tif(os.path.join(DATA, "s2_2017.tif"))
s25, _ = read_tif(os.path.join(DATA, "s2_2025.tif"))
ndvi17, ndbi17, mndwi17 = indices(s17)
ndvi25, ndbi25, mndwi25 = indices(s25)

# 마스크: 물(MNDWI>0), 두 해 모두 육지인 안정육지
water17 = mndwi17 > 0.0
water25 = mndwi25 > 0.0
land_stable = (~water17) & (~water25)
write_tif(os.path.join(DATA, "land_stable.tif"), land_stable.astype("float32"), transform, nodata=0)

# 저장 (지수 + 차분)
for name, arr in [
    ("ndvi_2017", ndvi17), ("ndvi_2025", ndvi25),
    ("ndbi_2017", ndbi17), ("ndbi_2025", ndbi25),
    ("mndwi_2017", mndwi17), ("mndwi_2025", mndwi25),
    ("d_ndvi", ndvi25 - ndvi17), ("d_ndbi", ndbi25 - ndbi17),
    ("d_mndwi", mndwi25 - mndwi17),
]:
    write_tif(os.path.join(DATA, name + ".tif"), arr.astype("float32"), transform)

# 요약 통계
def summ(a, m):
    v = a[m]
    return f"mean={np.nanmean(v):+.3f} std={np.nanstd(v):.3f}"

print(f"연구 프레임: {W}x{H}px @10m = {W*H*100/1e6:.1f} km²")
print(f"안정육지 화소: {land_stable.sum():,} ({land_stable.mean()*100:.1f}%)")
print("\n[안정육지 기준]")
print(f"NDVI  2017 {summ(ndvi17,land_stable)} | 2025 {summ(ndvi25,land_stable)} "
      f"| Δ평균 {np.nanmean((ndvi25-ndvi17)[land_stable]):+.3f}")
print(f"NDBI  2017 {summ(ndbi17,land_stable)} | 2025 {summ(ndbi25,land_stable)} "
      f"| Δ평균 {np.nanmean((ndbi25-ndbi17)[land_stable]):+.3f}")
print("\n[물 면적] 2017 {:.2f} km² → 2025 {:.2f} km² (Δ{:+.2f})".format(
    water17.sum()*1e-4, water25.sum()*1e-4, (water25.sum()-water17.sum())*1e-4))
print("육지→물/물→육지 전이: 물→육 {:.2f} km², 육→물 {:.2f} km²".format(
    (water17 & ~water25).sum()*1e-4, (~water17 & water25).sum()*1e-4))

# 변화 강도 임계(차분 표준화) 미리보기
for nm, d in [("ΔNDVI", ndvi25-ndvi17), ("ΔNDBI", ndbi25-ndbi17)]:
    dd = d[land_stable]
    inc = (dd > 0.1).mean()*100; dec = (dd < -0.1).mean()*100
    print(f"{nm}: 증가(>+0.1) {inc:.1f}% / 감소(<-0.1) {dec:.1f}%  (안정육지)")
print("\n지수·차분 저장 완료.")
