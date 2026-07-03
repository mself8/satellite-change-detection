"""비지도 토지피복 분류(k-means, 3클래스) + 식생→무식생 전이.

클래스: 수역 / 식생·이끼 / 나지·용암.  (광학만으로 신규용암↔구용암 분리는 신뢰도 낮아
신규 용암 판정은 04에서 다중센서 합의로 수행. 여기서는 범주적 토지피복 전이를 정량화.)
"""
import warnings; warnings.filterwarnings("ignore")
import os, sys, numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from common import DATA, FIG, read_tif, write_tif, target_grid, put_stats
from sklearn.cluster import MiniBatchKMeans
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap

rng = np.random.RandomState(42)
transform, W, H, bounds = target_grid()
ext = [bounds[0], bounds[2], bounds[1], bounds[3]]
B, G, R, NIR, SW1, SW2 = range(6)
K = 12
PX = 100/1e6
CLASSES = ["수역", "식생·이끼", "나지·용암"]            # 0,1,2
CMAP = ListedColormap(["#2c7fb8", "#41ab5d", "#8c6d4f"])

s23, _ = read_tif(f"{DATA}/s2_2023.tif")
s25, _ = read_tif(f"{DATA}/s2_2025.tif")


def feats(s):
    g, r, nir, sw1 = s[G], s[R], s[NIR], s[SW1]
    ndvi = (nir - r) / (nir + r + 1e-6)
    ndwi = (g - nir) / (g + nir + 1e-6)
    X = np.stack([s[B], s[G], s[R], s[NIR], s[SW1], s[SW2], ndvi, ndwi], -1)
    return X.reshape(-1, X.shape[-1])


X23, X25 = feats(s23), feats(s25)
Xall = np.vstack([X23, X25]); mu, sd = Xall.mean(0), Xall.std(0) + 1e-6
idx = rng.choice(Xall.shape[0], size=150000, replace=False)
km = MiniBatchKMeans(n_clusters=K, random_state=42, n_init=10, batch_size=10000)
km.fit(((Xall - mu) / sd)[idx])
lab23 = km.predict((X23 - mu) / sd).reshape(H, W)
lab25 = km.predict((X25 - mu) / sd).reshape(H, W)
cen = km.cluster_centers_ * sd + mu


def to_class(c):
    ndvi, ndwi, nir = c[6], c[7], c[3]
    if ndwi > 0.15 and nir < 0.18: return 0   # 수역
    if ndvi > 0.30:                return 1   # 식생·이끼
    return 2                                  # 나지·용암


lut = np.array([to_class(cen[c]) for c in range(K)])
cls23 = lut[lab23].astype("float32"); cls25 = lut[lab25].astype("float32")
write_tif(f"{DATA}/class_2023.tif", cls23, transform, nodata=255)
write_tif(f"{DATA}/class_2025.tif", cls25, transform, nodata=255)

a23 = np.array([(cls23 == k).sum() for k in range(3)]) * PX
a25 = np.array([(cls25 == k).sum() for k in range(3)]) * PX
np.save(f"{DATA}/class_area.npy", np.vstack([a23, a25]))
print("3클래스 면적(km²):")
for k in range(3):
    print(f"  {CLASSES[k]:>9} {a23[k]:6.2f} → {a25[k]:6.2f}  ({a25[k]-a23[k]:+.2f})")

# 육지 식생↔무식생 전이 (용암 매몰 = 식생→무식생)
land, _ = read_tif(f"{DATA}/land.tif"); land = land > 0.5
veg23 = (cls23 == 1) & land; veg25 = (cls25 == 1) & land
nv23 = (cls23 != 1) & land; nv25 = (cls25 != 1) & land
T = np.array([[(veg23 & veg25).sum(), (veg23 & nv25).sum()],
              [(nv23 & veg25).sum(), (nv23 & nv25).sum()]]) * PX
np.save(f"{DATA}/land_transition.npy", T)
print("\n[육지 식생↔무식생 전이 km²] (행2023→열2025)")
print(f"  식생 '23   식생'25 {T[0,0]:7.2f}  무식생'25 {T[0,1]:7.2f}")
print(f"  무식생'23  식생'25 {T[1,0]:7.2f}  무식생'25 {T[1,1]:7.2f}")
print(f"  ▶ 식생→무식생(용암·소실): {T[0,1]:.2f} km²   무식생→식생(회복·위상): {T[1,0]:.2f} km²")

put_stats(
    class_area={"2023": [round(x, 2) for x in a23], "2025": [round(x, 2) for x in a25]},
    veg_to_bare=round(float(T[0, 1]), 2), bare_to_veg=round(float(T[1, 0]), 2),
    veg_area={"2023": round(float(a23[1]), 2), "2025": round(float(a25[1]), 2)},
)

fig, ax = plt.subplots(1, 2, figsize=(15, 8))
ax[0].imshow(cls23, extent=ext, cmap=CMAP, vmin=0, vmax=2); ax[0].set_title("2023 분류")
ax[1].imshow(cls25, extent=ext, cmap=CMAP, vmin=0, vmax=2); ax[1].set_title("2025 분류")
for a in ax: a.set_xticks([]); a.set_yticks([])
plt.tight_layout(); plt.savefig(f"{FIG}/_diag_class.png", dpi=80, bbox_inches="tight")
print("\n검증맵 저장: _diag_class.png")
