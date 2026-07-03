# -*- coding: utf-8 -*-
"""딥러닝 — 광학+SAR 융합 U-Net 신규 용암 분할 (교수님 백두산 광학+SAR DL 융합 응용).

· 입력(융합): S2 2025 6밴드 + ΔNDVI·ΔNBR + S1 VV/VH·ΔVV + SAR 유효마스크 (14채널)
· 라벨: 다중센서 합의 용암(consensus==1)을 약지도(pseudo-label)로 사용
· 순환논리 방지: 장면을 좌/우로 공간분할 → 안 본 영역(test)에서 IoU/F1 평가
· 가치: ①공간 일반화 입증 ②SAR 결측(27%) 영역까지 용암맵 보완 ③매끄러운 확률맵
출력: data/dl_lava_{prob,mask}.tif, figures/fig13_dl.png, stats.json 갱신
"""
import warnings; warnings.filterwarnings("ignore")
import os, sys, json, numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from common import DATA, FIG, read_tif, write_tif, target_grid, get_stats, put_stats
import torch, torch.nn as nn, torch.nn.functional as F

torch.manual_seed(0); np.random.seed(0)
tr, W, H, b = target_grid(); PX = 100/1e6
B, G, R, NIR, SW1, SW2 = range(6)
DEV = "cpu"; torch.set_num_threads(min(32, os.cpu_count() or 4))

# ---- 채널 구성 (광학+SAR 융합) ----
s25, _ = read_tif(f"{DATA}/s2_2025.tif")
nd23, _ = read_tif(f"{DATA}/ndvi_2023.tif"); nd25, _ = read_tif(f"{DATA}/ndvi_2025.tif")
dN, _ = read_tif(f"{DATA}/d_ndvi.tif"); dB, _ = read_tif(f"{DATA}/d_nbr.tif")
s1, _ = read_tif(f"{DATA}/s1_2025.tif"); vv, vh = s1[0], s1[1]
dvv, _ = read_tif(f"{DATA}/d_vv.tif")
land, _ = read_tif(f"{DATA}/land.tif"); land = land > 0.5
code, _ = read_tif(f"{DATA}/consensus_lava.tif")
sar_ok = np.isfinite(vv) & np.isfinite(dvv)

chans = [s25[B], s25[G], s25[R], s25[NIR], s25[SW1], s25[SW2],   # 광학 2025
         nd23, nd25, dN, dB,                                      # 광학 전후 변화
         np.where(sar_ok, vv, 0), np.where(sar_ok, vh, 0), np.where(sar_ok, dvv, 0),  # SAR
         sar_ok.astype("float32")]                                # SAR 유효 채널
NAMES = ["B","G","R","NIR","SW1","SW2","NDVI23","NDVI25","dNDVI","dNBR","VV","VH","dVV","SARok"]
X = np.stack([np.nan_to_num(c.astype("float32")) for c in chans], 0)   # (C,H,W)
C = X.shape[0]
# 채널별 정규화 (육지 기준 z-score; SARok 채널 제외)
for i in range(C):
    if NAMES[i] == "SARok": continue
    m = X[i][land]; mu, sd = float(np.nanmean(m)), float(np.nanstd(m)+1e-6)
    X[i] = (X[i]-mu)/sd
Y = (code == 1).astype("float32")            # 라벨: 합의 용암
M = land.astype("float32")                    # 손실 마스크: 육지

# ---- 공간 분할 (좌=train, 우=test, 가운데 버퍼) ----
tr_end = int(0.60*W); te_start = int(0.70*W)
print(f"채널 {C}개, 육지 {land.sum()*PX:.0f}km², 용암라벨 {Y[land].mean()*100:.1f}% | split: train col<{tr_end}, test col>={te_start}")

P, S = 128, 64
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
print(f"패치(128/stride64): train {len(tr_p)}, test {len(te_p)}")

def batch(ps, idx):
    xs, ys, ms = [], [], []
    for k in idx:
        r, c = ps[k]
        xs.append(X[:, r:r+P, c:c+P]); ys.append(Y[r:r+P, c:c+P]); ms.append(M[r:r+P, c:c+P])
    return (torch.tensor(np.stack(xs)), torch.tensor(np.stack(ys))[:, None], torch.tensor(np.stack(ms))[:, None])

# ---- U-Net (소형) ----
def cbr(i, o): return nn.Sequential(nn.Conv2d(i, o, 3, padding=1), nn.BatchNorm2d(o), nn.ReLU(True),
                                    nn.Conv2d(o, o, 3, padding=1), nn.BatchNorm2d(o), nn.ReLU(True))
class UNet(nn.Module):
    def __init__(s, c, base=32):
        super().__init__()
        s.e1=cbr(c,base); s.e2=cbr(base,base*2); s.e3=cbr(base*2,base*4); s.b=cbr(base*4,base*8)
        s.pool=nn.MaxPool2d(2)
        s.u3=nn.ConvTranspose2d(base*8,base*4,2,2); s.d3=cbr(base*8,base*4)
        s.u2=nn.ConvTranspose2d(base*4,base*2,2,2); s.d2=cbr(base*4,base*2)
        s.u1=nn.ConvTranspose2d(base*2,base,2,2);   s.d1=cbr(base*2,base)
        s.out=nn.Conv2d(base,1,1)
    def forward(s,x):
        e1=s.e1(x); e2=s.e2(s.pool(e1)); e3=s.e3(s.pool(e2)); b=s.b(s.pool(e3))
        d=s.d3(torch.cat([s.u3(b),e3],1)); d=s.d2(torch.cat([s.u2(d),e2],1)); d=s.d1(torch.cat([s.u1(d),e1],1))
        return s.out(d)
net = UNet(C).to(DEV)
opt = torch.optim.Adam(net.parameters(), 1e-3)
pos = max(Y[land].mean(), 1e-3); pw = torch.tensor([min((1-pos)/pos, 8.0)])
print(f"모델 파라미터 {sum(p.numel() for p in net.parameters())/1e3:.0f}k, pos_weight {pw.item():.1f}")

def loss_fn(logit, y, m):
    bce = F.binary_cross_entropy_with_logits(logit, y, reduction="none", pos_weight=pw)
    bce = (bce*m).sum()/(m.sum()+1)
    p = torch.sigmoid(logit)
    dice = 1 - (2*(p*y*m).sum()+1)/((p*m).sum()+(y*m).sum()+1)
    return bce+dice

@torch.no_grad()
def eval_iou(ps):
    net.eval(); I=U=0.0
    for s0 in range(0, len(ps), 8):
        xb, yb, mb = batch(ps, range(s0, min(s0+8, len(ps))))
        pr = (torch.sigmoid(net(xb)) > 0.5).float()*mb; yb = yb*mb
        I += (pr*yb).sum().item(); U += ((pr+yb) >= 1).float().sum().item()
    return I/(U+1)

# 학습곡선용: 학습패치 고정 부분집합(독립 RNG — 학습 permutation 스트림 불변)
_rs = np.random.RandomState(1)
tr_sub = [tr_p[i] for i in _rs.choice(len(tr_p), min(64, len(tr_p)), replace=False)]
hist = {"epoch": [], "loss": [], "train_iou": [], "test_iou": []}
EP = 45
print("학습 시작...")
for ep in range(1, EP+1):
    net.train(); order = np.random.permutation(len(tr_p)); tot = 0.0; nb = 0
    for s0 in range(0, len(order), 8):
        xb, yb, mb = batch(tr_p, order[s0:s0+8])
        opt.zero_grad(); l = loss_fn(net(xb), yb, mb); l.backward(); opt.step(); tot += l.item(); nb += 1
    tl = tot/max(1, nb); tri = eval_iou(tr_sub); ti = eval_iou(te_p)
    hist["epoch"].append(ep); hist["loss"].append(round(tl, 4))
    hist["train_iou"].append(round(tri, 4)); hist["test_iou"].append(round(ti, 4))
    if ep % 5 == 0 or ep == 1:
        print(f"  ep{ep:02d} loss {tl:.3f}  train IoU {tri:.3f}  test IoU {ti:.3f}")

# ---- 전 장면 예측 (overlap 평균) ----
net.eval(); prob = np.zeros((H, W), "float32"); cnt = np.zeros((H, W), "float32")
with torch.no_grad():
    for r in range(0, H-P+1, S) or [0]:
        for c in range(0, W-P+1, S):
            x = torch.tensor(X[None, :, r:r+P, c:c+P])
            prob[r:r+P, c:c+P] += torch.sigmoid(net(x))[0, 0].numpy(); cnt[r:r+P, c:c+P] += 1
    # 우측/하단 가장자리 보정
    for r in [H-P]:
        for c in range(0, W-P+1, S):
            x = torch.tensor(X[None, :, r:r+P, c:c+P]); prob[r:r+P, c:c+P] += torch.sigmoid(net(x))[0,0].numpy(); cnt[r:r+P, c:c+P]+=1
    for c in [W-P]:
        for r in range(0, H-P+1, S):
            x = torch.tensor(X[None, :, r:r+P, c:c+P]); prob[r:r+P, c:c+P] += torch.sigmoid(net(x))[0,0].numpy(); cnt[r:r+P, c:c+P]+=1
prob = np.where(cnt > 0, prob/np.maximum(cnt, 1), 0)
prob[~land] = np.nan
mask = (prob > 0.5) & land
write_tif(f"{DATA}/dl_lava_prob.tif", prob.astype("float32"), tr)
write_tif(f"{DATA}/dl_lava_mask.tif", mask.astype("float32"), tr, nodata=0)

# ---- 평가 (test 영역, 육지) ----
test_reg = land & (np.arange(W)[None, :] >= te_start)
def metrics(reg):
    yt = (code == 1) & reg; yp = mask & reg
    tp = (yt & yp).sum(); fp = (~yt & yp).sum(); fn = (yt & ~yp).sum()
    iou = tp/(tp+fp+fn+1e-9); prec = tp/(tp+fp+1e-9); rec = tp/(tp+fn+1e-9)
    return iou, prec, rec, 2*prec*rec/(prec+rec+1e-9)
iou, prec, rec, f1 = metrics(test_reg)
iou_all, prec_all, rec_all, f1_all = metrics(land)
train_reg = land & (np.arange(W)[None, :] < tr_end)
iou_tr, prec_tr, rec_tr, f1_tr = metrics(train_reg)
# 임계값 독립 지표 (held-out): ROC-AUC · PR-AUC
from sklearn.metrics import roc_auc_score, average_precision_score
_sel = test_reg & np.isfinite(prob); _yt = (code == 1)[_sel].astype(int); _pp = prob[_sel]
auc = float(roc_auc_score(_yt, _pp)) if _yt.min() != _yt.max() else float("nan")
ap = float(average_precision_score(_yt, _pp)) if _yt.min() != _yt.max() else float("nan")
# SAR 결측부 보완: 합의 불가했던 곳에서 DL이 찾은 용암
gap = land & (~sar_ok)
dl_gap = (mask & gap).sum()*PX
print(f"\n[학습영역]      IoU {iou_tr:.3f}  P {prec_tr:.3f}  R {rec_tr:.3f}  F1 {f1_tr:.3f}  (패치 {len(tr_p)})")
print(f"[검증 held-out] IoU {iou:.3f}  P {prec:.3f}  R {rec:.3f}  F1 {f1:.3f}  (패치 {len(te_p)})  AUC {auc:.3f}  PR-AUC {ap:.3f}")
print(f"[전체]          IoU {iou_all:.3f}  F1 {f1_all:.3f}  | DL 용암 {mask.sum()*PX:.1f}km² (합의 {get_stats()['lava_km2']:.1f})")
print(f"[SAR 결측부 보완]  결측영역 {gap.sum()*PX:.1f}km² 중 DL 용암 {dl_gap:.2f}km² (규칙기반은 산정 불가)")

json.dump(hist, open(f"{DATA}/dl_history.json", "w"))
put_stats(dl_iou_test=round(float(iou),3), dl_f1_test=round(float(f1),3), dl_prec_test=round(float(prec),3),
          dl_rec_test=round(float(rec),3), dl_iou_all=round(float(iou_all),3), dl_f1_all=round(float(f1_all),3),
          dl_prec_all=round(float(prec_all),3), dl_rec_all=round(float(rec_all),3),
          dl_iou_train=round(float(iou_tr),3), dl_prec_train=round(float(prec_tr),3),
          dl_rec_train=round(float(rec_tr),3), dl_f1_train=round(float(f1_tr),3),
          dl_auc_test=round(auc,3), dl_ap_test=round(ap,3),
          dl_train_patches=len(tr_p), dl_test_patches=len(te_p),
          dl_lava_km2=round(float(mask.sum()*PX),2), dl_sargap_km2=round(float(dl_gap),2),
          dl_epochs=EP, dl_channels=C, dl_test_col=te_start)
print("\nDL 산출물 저장: dl_lava_prob.tif / dl_lava_mask.tif / dl_history.json")
