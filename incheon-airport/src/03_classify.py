"""비지도 토지피복 분류(k-means, 3 견고클래스) + 변화행렬.

광학 6밴드로는 포장면(불투수)과 나지의 분광분리가 신뢰도 낮아 두 클래스를
'불투수·나지'로 통합(견고한 3클래스: 수역/식생/불투수·나지).
서해안 조위차로 수역면적 비교는 조위 교란이 크므로, 토지변화 정량화는
'안정육지'(두 해 모두 육지) 화소에서 식생↔비식생 2클래스 전이로 수행.
"""
import warnings; warnings.filterwarnings("ignore")
import os, sys, numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from common import DATA, FIG, read_tif, write_tif, target_grid
from sklearn.cluster import MiniBatchKMeans
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
import viz

rng = np.random.RandomState(42)
transform, W, H, bounds = target_grid()
ext = [bounds[0], bounds[2], bounds[1], bounds[3]]
B, G, R, NIR, SW1, SW2 = range(6)
K = 12
CLASSES = ["수역", "식생", "불투수·나지"]       # 0,1,2
CMAP = ListedColormap(["#1f6fb2", "#3aa657", "#cf9b6b"])

s17, _ = read_tif(f"{DATA}/s2_2017.tif")
s25, _ = read_tif(f"{DATA}/s2_2025.tif")


def feats(s):
    g, r, nir, sw1 = s[G], s[R], s[NIR], s[SW1]
    ndvi = (nir - r) / (nir + r + 1e-6)
    mndwi = (g - sw1) / (g + sw1 + 1e-6)
    X = np.stack([s[B], s[G], s[R], s[NIR], s[SW1], s[SW2], ndvi, mndwi], -1)
    return X.reshape(-1, X.shape[-1])


X17 = feats(s17); X25 = feats(s25)
Xall = np.vstack([X17, X25]); mu, sd = Xall.mean(0), Xall.std(0) + 1e-6
idx = rng.choice(Xall.shape[0], size=150000, replace=False)
km = MiniBatchKMeans(n_clusters=K, random_state=42, n_init=10, batch_size=10000)
km.fit(((Xall - mu) / sd)[idx])
lab17 = km.predict((X17 - mu) / sd).reshape(H, W)
lab25 = km.predict((X25 - mu) / sd).reshape(H, W)
cen = km.cluster_centers_ * sd + mu


def to_class(c):
    ndvi, mndwi, nir = c[6], c[7], c[3]; bright = c[:6].mean()
    if mndwi > 0.15 and nir < 0.22:  return 0
    if bright < 0.10 and ndvi < 0.15: return 0
    if ndvi > 0.30:                   return 1
    return 2


lut = np.array([to_class(cen[c]) for c in range(K)])
cls17 = lut[lab17].astype("float32"); cls25 = lut[lab25].astype("float32")
write_tif(f"{DATA}/class_2017.tif", cls17, transform, nodata=255)
write_tif(f"{DATA}/class_2025.tif", cls25, transform, nodata=255)

px = 100 / 1e6
a17 = np.array([(cls17 == k).sum() for k in range(3)]) * px
a25 = np.array([(cls25 == k).sum() for k in range(3)]) * px
np.save(f"{DATA}/class_area.npy", np.vstack([a17, a25]))
print("3클래스 면적(km²):")
for k in range(3):
    print(f"  {CLASSES[k]:>10} {a17[k]:6.2f} → {a25[k]:6.2f}  ({a25[k]-a17[k]:+.2f})")

# 전이행렬 (전체프레임, 3x3) — 조위교란 포함, 참고용
M3 = np.zeros((3, 3)); f17 = cls17.ravel().astype(int); f25 = cls25.ravel().astype(int)
for i in range(3):
    for j in range(3):
        M3[i, j] = ((f17 == i) & (f25 == j)).sum() * px
np.save(f"{DATA}/change_matrix3.npy", M3)

# 안정육지 2클래스(식생/비식생) 전이 — 조위 무관, 핵심 정량
land, _ = read_tif(f"{DATA}/land_stable.tif"); land = land > 0.5
veg17 = (cls17 == 1) & land; veg25 = (cls25 == 1) & land
nonveg17 = (cls17 != 1) & land; nonveg25 = (cls25 != 1) & land
T = np.array([
    [(veg17 & veg25).sum(), (veg17 & nonveg25).sum()],
    [(nonveg17 & veg25).sum(), (nonveg17 & nonveg25).sum()],
]) * px
np.save(f"{DATA}/land_transition.npy", T)
print("\n[안정육지 식생↔비식생 전이, km²]  (행2017→열2025)")
print(f"             식생'25  비식생'25")
print(f"  식생 '17   {T[0,0]:7.2f} {T[0,1]:8.2f}")
print(f"  비식생'17  {T[1,0]:7.2f} {T[1,1]:8.2f}")
print(f"\n  ▶ 녹화(비식생→식생): {T[1,0]:.2f} km²  (공사완료+조경)")
print(f"  ▶ 신규개발(식생→비식생): {T[0,1]:.2f} km²  (확장 footprint)")
print(f"  ▶ 순 식생변화: {T[1,0]-T[0,1]:+.2f} km²")
print(f"  안정육지 총 {land.sum()*px:.1f} km² 중 변화 {(T[0,1]+T[1,0]):.2f} km² ({(T[0,1]+T[1,0])/(land.sum()*px)*100:.1f}%)")

fig, ax = plt.subplots(1, 2, figsize=(15, 9))
ax[0].imshow(cls17, extent=ext, cmap=CMAP, vmin=0, vmax=2); ax[0].set_title("2017 분류(3클래스)")
ax[1].imshow(cls25, extent=ext, cmap=CMAP, vmin=0, vmax=2); ax[1].set_title("2025 분류(3클래스)")
for a in ax: a.set_xticks([]); a.set_yticks([])
plt.tight_layout(); plt.savefig(f"{FIG}/_diag_class3.png", dpi=85, bbox_inches="tight")
print("\n검증맵 저장: _diag_class3.png")
