# -*- coding: utf-8 -*-
"""교수님 Modified U-Net(2-encoder 회귀) 구조를 다중센서로 확장한 3-encoder 버전.

· 구조(교수님 충실): 분리 인코더 → 각 인코더 skip을 디코더에 concat → ReLU 출력 회귀
  - Enc1 가시광(R,G,B) / Enc2 적외광학(NIR,SWIR1,SWIR2,NDVI23,NDVI25,ΔNDVI,ΔNBR) / Enc3 SAR(VV,VH,ΔVV,유효)
· 손실 MAE · 옵티마 NAdam · 출력 ReLU (교수님 Table.4와 동일 계열; epoch/lr/batch는 CPU에 맞춰 조정)
· 타깃 T(0~1): 연속 '용암 변화강도' = mean(식생소실, SWIR어두움, SAR증가) — 임계 0.5 → 합의 21km²에 근접
· 순환논리 방지: 좌/우 공간분할, held-out에서 회귀(MAE·RMSE·R) + 임계 분할(IoU·F1) 평가
출력: data/lava_degree.tif(타깃), data/dl3_degree.tif(예측), dl3_history.json, figures/fig16_*, stats 갱신
사용: python 11_modified_unet.py [EPOCHS]
"""
import warnings; warnings.filterwarnings("ignore")
import os, sys, json, numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from common import DATA, read_tif, write_tif, target_grid, get_stats, put_stats
import torch, torch.nn as nn, torch.nn.functional as F

torch.manual_seed(0); np.random.seed(0)
tr, W, H, b = target_grid(); PX = 100/1e6
DEV = "cpu"; torch.set_num_threads(min(40, os.cpu_count() or 4))
EP = int(sys.argv[1]) if len(sys.argv) > 1 else 60

# ---------- 입력 로드 ----------
s25 = read_tif(f"{DATA}/s2_2025.tif")[0]
s1 = read_tif(f"{DATA}/s1_2025.tif")[0]
nd23 = read_tif(f"{DATA}/ndvi_2023.tif")[0]; nd25 = read_tif(f"{DATA}/ndvi_2025.tif")[0]
dN = read_tif(f"{DATA}/d_ndvi.tif")[0]; dB = read_tif(f"{DATA}/d_nbr.tif")[0]
dvv = read_tif(f"{DATA}/d_vv.tif")[0]
land = read_tif(f"{DATA}/land.tif")[0] > 0.5
code = read_tif(f"{DATA}/consensus_lava.tif")[0]
sw1 = s25[4]; sar_ok = np.isfinite(dvv)

# ---------- 연속 타깃 T (용암 변화강도 0~1) ----------
oc = np.clip((nd23 - nd25)/0.4, 0, 1)                # 식생/이끼 소실 (ΔNDVI 0.4 → 1)
dk = np.clip((0.10 - sw1)/0.08, 0, 1)                # SWIR 어두워짐 (이끼0.10→용암0.02)
opt = np.minimum(oc, dk)                             # 광학 AND: 식생소실 ∧ 어두움 (둘 다 필요)
sar_up = np.clip(np.nan_to_num(dvv)/4.0, 0, 1)       # 후방산란 증가 (a'a 거칠기, 보정)
T = np.where(sar_ok, np.clip(opt + 0.25*sar_up, 0, 1), opt)
T = np.where(land, T, 0).astype("float32")
write_tif(f"{DATA}/lava_degree.tif", T, tr, nodata=0)
print(f"타깃 T: 임계0.5 면적 {(T>0.5)[land].sum()*PX:.2f} km² (합의 {get_stats()['lava_km2']:.1f}) | "
      f"육지 평균 {T[land].mean():.3f}")

# ---------- 3그룹 입력 (인코더별), 육지 z-score ----------
def stack(chs, skip_last=False):
    X = np.stack([np.nan_to_num(c.astype("float32")) for c in chs], 0)
    for i in range(X.shape[0]):
        if skip_last and i == X.shape[0]-1: continue
        m = X[i][land]; mu, sd = float(m.mean()), float(m.std()+1e-6); X[i] = (X[i]-mu)/sd
    return X
GX = [stack([s25[0], s25[1], s25[2]]),                                  # 가시광 (3)
      stack([s25[3], s25[4], s25[5], nd23, nd25, dN, dB]),              # 적외광학+변화 (7)
      stack([s1[0], s1[1], np.nan_to_num(dvv), sar_ok.astype("float32")], skip_last=True)]  # SAR (4)
CINS = [g.shape[0] for g in GX]
Y = T; M = land.astype("float32")
print("인코더 입력 채널:", CINS, "| 합", sum(CINS))

# ---------- 공간분할 + 패치 ----------
tr_end = int(0.60*W); te_start = int(0.70*W); P, S = 128, 64
def patches(region):
    out = []
    for r in range(0, H-P+1, S):
        for c in range(0, W-P+1, S):
            if region == "train" and c+P > tr_end: continue
            if region == "test" and c < te_start: continue
            if land[r:r+P, c:c+P].mean() < 0.1: continue
            out.append((r, c))
    return out
tr_p, te_p = patches("train"), patches("test")
print(f"패치(128/64): train {len(tr_p)}, test {len(te_p)} | split col<{tr_end}/>={te_start}")

def batch(ps, idx):
    xs = [[], [], []]; ys = []; ms = []
    for k in idx:
        r, c = ps[k]
        for g in range(3): xs[g].append(GX[g][:, r:r+P, c:c+P])
        ys.append(Y[r:r+P, c:c+P]); ms.append(M[r:r+P, c:c+P])
    X = [torch.tensor(np.stack(x)) for x in xs]
    return X, torch.tensor(np.stack(ys))[:, None], torch.tensor(np.stack(ms))[:, None]

# ---------- 3-encoder Modified U-Net ----------
def cbr(i, o): return nn.Sequential(nn.Conv2d(i, o, 3, padding=1), nn.BatchNorm2d(o), nn.ReLU(True),
                                    nn.Conv2d(o, o, 3, padding=1), nn.BatchNorm2d(o), nn.ReLU(True))
class Enc(nn.Module):
    def __init__(s, cin, base=32):
        super().__init__(); s.e1=cbr(cin,base); s.e2=cbr(base,base*2); s.e3=cbr(base*2,base*4)
        s.b=cbr(base*4,base*8); s.pool=nn.MaxPool2d(2)
    def forward(s, x):
        e1=s.e1(x); e2=s.e2(s.pool(e1)); e3=s.e3(s.pool(e2)); bo=s.b(s.pool(e3)); return e1,e2,e3,bo
class ModUNet(nn.Module):
    def __init__(s, cins, base=32):
        super().__init__(); K=len(cins); s.encs=nn.ModuleList([Enc(c, base) for c in cins])
        s.fuse=cbr(base*8*K, base*8)
        s.u3=nn.ConvTranspose2d(base*8,base*4,2,2); s.d3=cbr(base*4 + base*4*K, base*4)
        s.u2=nn.ConvTranspose2d(base*4,base*2,2,2); s.d2=cbr(base*2 + base*2*K, base*2)
        s.u1=nn.ConvTranspose2d(base*2,base,2,2);   s.d1=cbr(base + base*K, base)
        s.out=nn.Conv2d(base,1,1)
    def forward(s, xs):
        o=[e(x) for e,x in zip(s.encs, xs)]
        e1=[t[0] for t in o]; e2=[t[1] for t in o]; e3=[t[2] for t in o]; bo=[t[3] for t in o]
        d=s.fuse(torch.cat(bo,1))
        d=s.d3(torch.cat([s.u3(d)]+e3,1)); d=s.d2(torch.cat([s.u2(d)]+e2,1)); d=s.d1(torch.cat([s.u1(d)]+e1,1))
        return F.relu(s.out(d))   # ReLU 출력 (교수님과 동일)
net = ModUNet(CINS).to(DEV)
opt = torch.optim.NAdam(net.parameters(), lr=1e-3)   # 옵티마 NAdam (교수님과 동일 계열)
print(f"모델 파라미터 {sum(p.numel() for p in net.parameters())/1e6:.2f}M | EP {EP} | NAdam lr1e-3 · MAE")

def mae_loss(pred, y, m): return (torch.abs(pred-y)*m).sum()/(m.sum()+1)

@torch.no_grad()
def eval_reg(ps):
    net.eval(); se=ae=nn_=0.0
    for s0 in range(0, len(ps), 8):
        xb, yb, mb = batch(ps, range(s0, min(s0+8, len(ps))))
        pr=net(xb)*mb; yy=yb*mb
        ae += torch.abs(pr-yy).sum().item(); se += ((pr-yy)**2).sum().item(); nn_ += mb.sum().item()
    return ae/(nn_+1), (se/(nn_+1))**0.5

# ---------- 학습 ----------
hist = {"epoch": [], "loss": [], "test_mae": []}
print("학습 시작...")
for ep in range(1, EP+1):
    net.train(); order = np.random.permutation(len(tr_p)); tot=0.0; nb=0
    for s0 in range(0, len(order), 8):
        xb, yb, mb = batch(tr_p, order[s0:s0+8])
        opt.zero_grad(); l = mae_loss(net(xb), yb, mb); l.backward(); opt.step(); tot += l.item(); nb += 1
    tl = tot/max(1, nb); tmae, _ = eval_reg(te_p)
    hist["epoch"].append(ep); hist["loss"].append(round(tl, 4)); hist["test_mae"].append(round(tmae, 4))
    if ep % 5 == 0 or ep == 1: print(f"  ep{ep:02d} loss {tl:.4f}  test MAE {tmae:.4f}")

# ---------- 전 장면 예측 ----------
net.eval(); pred = np.zeros((H, W), "float32"); cnt = np.zeros((H, W), "float32")
with torch.no_grad():
    rs = list(range(0, H-P+1, S)) + [H-P]; cs = list(range(0, W-P+1, S)) + [W-P]
    for r in rs:
        for c in cs:
            xb = [torch.tensor(g[None, :, r:r+P, c:c+P]) for g in GX]
            pred[r:r+P, c:c+P] += net(xb)[0, 0].numpy(); cnt[r:r+P, c:c+P] += 1
pred = np.where(cnt > 0, pred/np.maximum(cnt, 1), 0); pred[~land] = np.nan
write_tif(f"{DATA}/dl3_degree.tif", pred.astype("float32"), tr, nodata=0)

# ---------- 평가 ----------
test_reg = land & (np.arange(W)[None, :] >= te_start)
def reg_m(reg):
    yt=Y[reg]; yp=np.nan_to_num(pred)[reg]
    return float(np.abs(yp-yt).mean()), float(np.sqrt(((yp-yt)**2).mean())), float(np.corrcoef(yp, yt)[0,1])
def seg_m(reg, thr=0.5):
    yt=(code==1)&reg; yp=(np.nan_to_num(pred)>thr)&reg
    tp=(yt&yp).sum(); fp=(~yt&yp).sum(); fn=(yt&~yp).sum()
    iou=tp/(tp+fp+fn+1e-9); pr=tp/(tp+fp+1e-9); rc=tp/(tp+fn+1e-9)
    return iou, pr, rc, 2*pr*rc/(pr+rc+1e-9)
mae_t, rmse_t, r_t = reg_m(test_reg)
iou_t, prec_t, rec_t, f1_t = seg_m(test_reg)
area = (np.nan_to_num(pred) > 0.5)[land].sum()*PX
print(f"\n[held-out 회귀]  MAE {mae_t:.4f}  RMSE {rmse_t:.4f}  Pearson R {r_t:.4f}")
print(f"[held-out 분할(임계0.5)]  IoU {iou_t:.3f}  P {prec_t:.3f}  R {rec_t:.3f}  F1 {f1_t:.3f}")
print(f"[전체] DL3 용암 {area:.2f} km² (합의 {get_stats()['lava_km2']:.1f})")

json.dump(hist, open(f"{DATA}/dl3_history.json", "w"))
put_stats(dl3_mae_test=round(mae_t, 4), dl3_rmse_test=round(rmse_t, 4), dl3_r_test=round(r_t, 4),
          dl3_iou_test=round(iou_t, 3), dl3_f1_test=round(f1_t, 3), dl3_prec_test=round(prec_t, 3),
          dl3_rec_test=round(rec_t, 3), dl3_area_km2=round(float(area), 2),
          dl3_params_m=round(sum(p.numel() for p in net.parameters())/1e6, 2),
          dl3_epochs=EP, dl3_cins=CINS, dl3_test_col=te_start)
print("\nDL3 산출물 저장: lava_degree.tif / dl3_degree.tif / dl3_history.json")
