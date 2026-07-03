"""고급 변화탐지: 변화벡터분석(CVA) + 주성분분석(PCA) 기반 변화탐지."""
import warnings; warnings.filterwarnings("ignore")
import os, sys, numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from common import DATA, FIG, read_tif, write_tif, target_grid
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt

transform, W, H, bounds = target_grid()
ext = [bounds[0], bounds[2], bounds[1], bounds[3]]
B, G, R, NIR, SW1, SW2 = range(6)
s17, _ = read_tif(f"{DATA}/s2_2017.tif")
s25, _ = read_tif(f"{DATA}/s2_2025.tif")
land, _ = read_tif(f"{DATA}/land_stable.tif"); land = land > 0.5


def otsu(v, nbins=256):
    v = v[np.isfinite(v)]
    hist, edges = np.histogram(v, bins=nbins)
    p = hist / hist.sum(); w = np.cumsum(p); m = np.cumsum(p * (edges[:-1]))
    mt = m[-1]; denom = w * (1 - w)
    sb = np.where(denom > 0, (mt * w - m) ** 2 / np.where(denom == 0, 1, denom), 0)
    return edges[:-1][np.argmax(sb)]


# ---- CVA ----
X17 = np.stack([s17[b] for b in range(6)], -1).reshape(-1, 6)
X25 = np.stack([s25[b] for b in range(6)], -1).reshape(-1, 6)
Xall = np.vstack([X17, X25]); mu, sd = Xall.mean(0), Xall.std(0) + 1e-6
d = ((X25 - mu) / sd) - ((X17 - mu) / sd)           # 표준화 차분벡터
mag = np.sqrt((d ** 2).sum(1)).reshape(H, W)         # 변화강도
write_tif(f"{DATA}/cva_magnitude.tif", mag.astype("float32"), transform)
thr = otsu(mag[land])
changed = (mag > thr) & land
print(f"CVA: magnitude 평균 {mag[land].mean():.2f}, Otsu임계 {thr:.2f}")
print(f"  변화화소(안정육지): {changed.sum()*1e-4:.2f} km² ({changed[land].mean()*100:.1f}%)")

# 변화 유형 (ΔNDVI, ΔNDBI 부호)
ndvi17 = (s17[NIR]-s17[R])/(s17[NIR]+s17[R]+1e-6); ndvi25 = (s25[NIR]-s25[R])/(s25[NIR]+s25[R]+1e-6)
ndbi17 = (s17[SW1]-s17[NIR])/(s17[SW1]+s17[NIR]+1e-6); ndbi25 = (s25[SW1]-s25[NIR])/(s25[SW1]+s25[NIR]+1e-6)
dN = ndvi25-ndvi17; dB = ndbi25-ndbi17
ctype = np.zeros((H, W), np.uint8)        # 0 안정
ctype[changed & (dN > 0.1)] = 1           # 녹화
ctype[changed & (dN < -0.1)] = 2          # 식생감소(개발/제거)
ctype[changed & (ctype == 0)] = 3         # 기타 표면변화(나지↔포장 등)
write_tif(f"{DATA}/cva_type.tif", ctype.astype("float32"), transform, nodata=255)
for k, nm in [(1, "녹화"), (2, "식생감소(개발)"), (3, "기타 표면변화"), (0, "안정")]:
    print(f"  유형 {nm}: {(ctype==k)[land].sum()*1e-4:.2f} km²")

# ---- PCA 변화탐지 (차분영상 PCA) ----
# 표준화 차분밴드 d(N,6)의 PCA → PC1 = 주 변화축, PC2 = 2차 변화축
dl = d[land.ravel()]
Cd = np.cov(dl, rowvar=False)
val, vec = np.linalg.eigh(Cd); order = np.argsort(val)[::-1]
val, vec = val[order], vec[:, order]; ev = val / val.sum()
print(f"\n차분영상 PCA 분산설명: " + " ".join(f"PC{i+1} {ev[i]*100:.1f}%" for i in range(6)))
PCs = (d @ vec).reshape(H, W, 6)
pc1 = PCs[..., 0]; pc2 = PCs[..., 1]
if np.corrcoef(pc1[land], dN[land])[0, 1] < 0: pc1 = -pc1   # 식생증가가 +
write_tif(f"{DATA}/pca_change.tif", pc1.astype("float32"), transform)
write_tif(f"{DATA}/pca_change2.tif", pc2.astype("float32"), transform)
np.save(f"{DATA}/pca_var.npy", ev)
print(f"PC1↔ΔNDVI 상관 {np.corrcoef(pc1[land], dN[land])[0,1]:+.2f}, "
      f"PC2↔ΔNDBI 상관 {np.corrcoef(pc2[land], dB[land])[0,1]:+.2f}")
kpc = 0; pc_change = pc1

# 진단 figure
fig, ax = plt.subplots(1, 3, figsize=(20, 8))
im0 = ax[0].imshow(np.where(land, mag, np.nan), extent=ext, cmap="magma", vmax=np.nanpercentile(mag[land],98))
ax[0].set_title("CVA 변화강도"); plt.colorbar(im0, ax=ax[0], shrink=.6)
from matplotlib.colors import ListedColormap
cm = ListedColormap(["#eeeeee", "#3aa657", "#d9534f", "#f0c040"])
ax[1].imshow(np.where(land, ctype, np.nan), extent=ext, cmap=cm, vmin=0, vmax=3)
ax[1].set_title("CVA 변화유형(녹/적/황)")
vlim = np.nanpercentile(abs(pc_change[land]), 98)
im2 = ax[2].imshow(np.where(land, pc_change, np.nan), extent=ext, cmap="RdBu",
                   vmin=-vlim, vmax=vlim)
ax[2].set_title("PCA 변화성분(차분 PC1)"); plt.colorbar(im2, ax=ax[2], shrink=.6)
for a in ax: a.set_xticks([]); a.set_yticks([])
plt.tight_layout(); plt.savefig(f"{FIG}/_diag_advanced.png", dpi=85, bbox_inches="tight")
print("\n진단 저장: _diag_advanced.png")
