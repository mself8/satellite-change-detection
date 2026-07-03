"""고급·다중센서 변화탐지: CVA + PCA(광학) + SAR 후방산란 변화 + LST 이상 + 다중센서 합의 용암.

핵심 산출물 = '다중센서 합의 신규 용암' 마스크:
  광학(식생→저알베도·무식생) ∧ ( SAR 후방산란↑  ∨  열적 상대승온↑ )
단일 광학지수는 아이슬란드 이끼 위상/테프라로 교란되므로, 광학·SAR·열의 교차합의로 견고화.
교수님(이어루) 백두산 광학+SAR 융합 연구의 응용.
"""
import warnings; warnings.filterwarnings("ignore")
import os, sys, numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from common import DATA, FIG, read_tif, write_tif, target_grid, put_stats
from pyproj import Transformer
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap

transform, W, H, bounds = target_grid()
ext = [bounds[0], bounds[2], bounds[1], bounds[3]]
B, G, R, NIR, SW1, SW2 = range(6); PX = 100/1e6
to_ll = Transformer.from_crs("EPSG:32627", "EPSG:4326", always_xy=True)

s23, _ = read_tif(f"{DATA}/s2_2023.tif"); s25, _ = read_tif(f"{DATA}/s2_2025.tif")
land, _ = read_tif(f"{DATA}/land.tif"); land = land > 0.5
ndvi23 = (s23[NIR]-s23[R])/(s23[NIR]+s23[R]+1e-6)
ndvi25 = (s25[NIR]-s25[R])/(s25[NIR]+s25[R]+1e-6)
alb25 = s25[:4].mean(0)
dN = ndvi25 - ndvi23


def otsu(v, nbins=256):
    v = v[np.isfinite(v)]; hist, edges = np.histogram(v, bins=nbins)
    p = hist/hist.sum(); w = np.cumsum(p); m = np.cumsum(p*edges[:-1]); mt = m[-1]
    denom = w*(1-w); sb = np.where(denom > 0, (mt*w-m)**2/np.where(denom == 0, 1, denom), 0)
    return edges[:-1][np.argmax(sb)]


# ---- CVA (6밴드 표준화 변화벡터) ----
X23 = np.stack([s23[b] for b in range(6)], -1).reshape(-1, 6)
X25 = np.stack([s25[b] for b in range(6)], -1).reshape(-1, 6)
Xall = np.vstack([X23, X25]); mu, sd = Xall.mean(0), Xall.std(0)+1e-6
d = ((X25-mu)/sd) - ((X23-mu)/sd)
mag = np.sqrt((d**2).sum(1)).reshape(H, W)
write_tif(f"{DATA}/cva_magnitude.tif", mag.astype("float32"), transform)
thr = otsu(mag[land]); changed = (mag > thr) & land
print(f"CVA: 평균강도 {mag[land].mean():.2f}, Otsu {thr:.2f}, 변화 {changed.sum()*PX:.1f} km² (육지 {changed[land].mean()*100:.0f}%)")

# ---- PCA (차분영상) ----
dl = d[land.ravel()]; Cd = np.cov(dl, rowvar=False)
val, vec = np.linalg.eigh(Cd); order = np.argsort(val)[::-1]; val, vec = val[order], vec[:, order]
ev = val/val.sum(); PCs = (d @ vec).reshape(H, W, 6); pc1 = PCs[..., 0]
if np.corrcoef(pc1[land], dN[land])[0, 1] > 0: pc1 = -pc1   # 용암(식생감소)이 +가 되도록
write_tif(f"{DATA}/pca_change.tif", pc1.astype("float32"), transform)
np.save(f"{DATA}/pca_var.npy", ev)
print(f"PCA 분산설명: " + " ".join(f"PC{i+1} {ev[i]*100:.0f}%" for i in range(4)))

# ---- SAR 후방산란 변화 (VV/VH dB) ----
s1a, _ = read_tif(f"{DATA}/s1_2023.tif"); s1b, _ = read_tif(f"{DATA}/s1_2025.tif")
dvv = s1b[0]-s1a[0]; dvh = s1b[1]-s1a[1]; sar_ok = np.isfinite(dvv)
write_tif(f"{DATA}/d_vv.tif", dvv.astype("float32"), transform)
lm = land & sar_ok
print(f"SAR: 유효 {sar_ok[land].mean()*100:.0f}%  ΔVV 평균 {np.nanmean(dvv[lm]):+.2f}dB  |ΔVV|>2 {(np.abs(dvv[lm])>2).mean()*100:.0f}%")

# ---- LST 이상(상대온도) ----
l23, _ = read_tif(f"{DATA}/lst_2023.tif"); l25, _ = read_tif(f"{DATA}/lst_2025.tif")
dL = l25 - l23; lf = land & np.isfinite(dL)
dL_bg = float(np.nanmean(dL[lf]))                 # 촬영일 기상차(배경)
anom = dL - dL_bg                                  # 상대 승온(토지피복 신호)
write_tif(f"{DATA}/lst_anom.tif", np.where(np.isfinite(dL), anom, np.nan).astype("float32"), transform)
hot = land & (l25 > np.nanpercentile(l25[land], 99))
print(f"LST: 육지평균 {np.nanmean(l23[land]):.1f}→{np.nanmean(l25[land]):.1f}°C (배경Δ{dL_bg:+.1f}) | "
      f"2025 고온화소(>99%) {hot.sum()*PX:.2f}km² 평균{np.nanmean(l25[hot]):.1f}°C")

# ---- 다중센서 합의 신규 용암 ----
opt = land & (ndvi23 > 0.25) & (ndvi25 < 0.18) & (alb25 < np.nanpercentile(alb25[land], 40))
sar = land & sar_ok & (dvv > 1.5)
thrm = lf & (anom > 2.0)
consensus = opt & (sar | thrm)
opt_only = opt & ~(sar | thrm)
code = np.where(consensus, 1, np.where(opt_only, 2, 0)).astype("float32")
write_tif(f"{DATA}/consensus_lava.tif", code, transform, nodata=255)

ys, xs = np.where(consensus)
ux = bounds[0]+(xs+0.5)*10; uy = bounds[3]-(ys+0.5)*10
lon, lat = to_ll.transform(ux, uy)
print(f"\n[다중센서 합의 신규 용암] {consensus.sum()*PX:.2f} km²  (광학단독 잡음 {opt_only.sum()*PX:.2f} km²)")
print(f"  중심 ≈ ({np.median(lat):.3f}°N, {abs(np.median(lon)):.3f}°W)  위도 {lat.min():.3f}~{lat.max():.3f}")
print(f"  합의용암 내: ΔVV {np.nanmean(dvv[consensus & sar_ok]):+.2f}dB,  ΔLST이상 {np.nanmean(anom[consensus & np.isfinite(anom)]):+.1f}°C")

put_stats(
    cva_change_km2=round(float(changed.sum()*PX), 1), cva_change_pct=round(float(changed[land].mean()*100)),
    pca_var=[round(float(x*100), 1) for x in ev[:6]],
    pca_pc1_dndvi_corr=round(float(np.corrcoef(pc1[land], dN[land])[0, 1]), 2),
    sar_valid_pct=round(float(sar_ok[land].mean()*100)), sar_dvv_mean=round(float(np.nanmean(dvv[lm])), 2),
    lst_2023=round(float(np.nanmean(l23[land])), 1), lst_2025=round(float(np.nanmean(l25[land])), 1),
    lst_bg=round(dL_bg, 1), hot_km2=round(float(hot.sum()*PX), 2), hot_temp=round(float(np.nanmean(l25[hot])), 1),
    lava_km2=round(float(consensus.sum()*PX), 2), lava_optonly_km2=round(float(opt_only.sum()*PX), 2),
    lava_dvv=round(float(np.nanmean(dvv[consensus & sar_ok])), 2),
    lava_anom=round(float(np.nanmean(anom[consensus & np.isfinite(anom)])), 1),
    lava_lat=round(float(np.median(lat)), 3), lava_lon=round(float(abs(np.median(lon))), 3),
)

# 진단 figure
fig, ax = plt.subplots(1, 3, figsize=(21, 7))
im0 = ax[0].imshow(np.where(land, mag, np.nan), extent=ext, cmap="magma", vmax=np.nanpercentile(mag[land], 98))
ax[0].set_title("CVA 강도"); plt.colorbar(im0, ax=ax[0], shrink=.6)
im1 = ax[1].imshow(np.where(lm, dvv, np.nan), extent=ext, cmap="RdBu_r", vmin=-4, vmax=4)
ax[1].set_title("ΔVV (SAR dB)"); plt.colorbar(im1, ax=ax[1], shrink=.6)
cm = ListedColormap(["#d9d9d9", "#d7301f", "#fdcc8a"])
ax[2].imshow(np.where(land, code, np.nan), extent=ext, cmap=cm, vmin=0, vmax=2)
ax[2].set_title("합의 용암(적)/광학단독(주)")
for a in ax: a.set_xticks([]); a.set_yticks([])
plt.tight_layout(); plt.savefig(f"{FIG}/_diag_advanced.png", dpi=80, bbox_inches="tight")
print("진단 저장: _diag_advanced.png")
