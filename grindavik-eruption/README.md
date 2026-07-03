# 아이슬란드 Grindavík–Sundhnúkur 분화 변화탐지 (2023→2025)

위성 **다중센서(광학·SAR·지표온도) 변화탐지**로 신규 용암류를 견고하게 탐지하는
AI기반 원격탐사(서울시립대) 기말 팀프로젝트. 이어루 교수님의 백두산 광학+SAR 융합 연구를 응용.

## 핵심 결과
- **다중센서 합의 신규 용암 ≈ 21 km²** (Sundhnúkur 분화구열, 63.9°N 중심)
- 광학(식생↓)·SAR(ΔVV +2.7 dB)·열(상대승온 +3.9°C)이 **같은 위치에서 일치**
- 단일 광학기법은 무식생 +33 km²·ΔNDVI 35 km²로 **과대추정** — 이끼(moss) 위상·테프라 교란 때문
  (2024년 NDVI 일시 저하가 그 증거). 다중센서 합의로 위상 잡음 ~4 km² 제거.

## 데이터 (UTM 27N · 10 m, AOI ≈ 201 km²)
| 센서 | 자료 | 시기 |
|---|---|---|
| Sentinel-2 L2A (광학) | 지표반사율 6밴드 | 2023-09-21 · 2024-09-15 · 2025-09-18 |
| Sentinel-1 RTC (SAR) | VV/VH 후방산란(dB) | 2023 vs 2025 (커버 73%) |
| Landsat 8/9 C2L2 | 지표온도(LST) | 2023 vs 2025 |

취득: STAC API (S2=AWS earth-search 무인증, S1·Landsat=Planetary Computer).

> **참고**: 원본·중간 래스터(`data/*.tif`)는 용량 문제로 레포에 포함하지 않았습니다.
> `src/01_download.py`부터 순서대로 실행하면 재생성됩니다. 통계(`data/*.json`)·
> `figures/`·`web/`은 포함되어 있어 **데이터 없이도 결과 열람이 가능**합니다.

## 파이프라인 (src/, 순서대로 실행)
```bash
PY=python3
$PY src/01_download.py     # S2·S1·Landsat 다운로드 (STAC → data/*.tif)
$PY src/01b_select_s2.py   # 2023·2025 S2 저운량·전커버 장면 재선택
$PY src/02_indices.py      # NDVI·NBR·NDWI·알베도 + 전후 차분, 마스크, stats.json
$PY src/03_classify.py     # k-means 3클래스(수역/식생이끼/나지용암) + 전이
$PY src/04_advanced.py     # CVA·PCA·SAR ΔVV·LST 이상 + ★다중센서 합의 용암
$PY src/05_figures.py      # 발표 figure 11종 (방위표·축척·격자 포함)
$PY src/06_build_pptx.py   # 발표자료 PPTX
$PY src/07_build_pdf.py    # 발표자료 PDF (NanumGothic 임베드)
$PY src/08_web.py          # ★ 인터랙티브 웹맵 (web/index.html)
```
- 공유 모듈: `common.py`(격자·COG·stats), `viz.py`(지도 카토그래피), `deck.py`(pptx),
  `content.py`(슬라이드 단일 소스 — 제목·팀·발표번호 여기서 수정).
- 분석 수치는 `data/stats.json`에 누적 저장되어 figures·content가 공유.

## 산출물 (outputs/, web/, lava_state/)
- `outputs/아이슬란드_화산_변화탐지_발표.pdf` (26쪽 · 발표노트 포함 PPTX 원본은 용량상 미포함)
- `web/index.html` — **인터랙티브 변화탐지 웹맵**
- `lava_state/` — 후속 실험: 합의 용암 영역의 **잔열 상태 분류(v2)** 노트북
  (`lava_state_real_data_v2.ipynb`) + 결과 맵·평가·민감도·피처중요도 그림

### 웹맵 사용
`web/index.html`을 브라우저로 열면 됨 (베이스맵 타일만 인터넷 필요, Leaflet은 `web/lib/`에 동봉).
- 분화 **전(2023) ↔ 후(2025) 스와이프** 슬라이더
- 위성영상 위 **다중센서 오버레이 토글**: 광학 ΔNDVI · SAR ΔVV · 열 ΔLST 이상 · 지표온도 · ★합의용암 · 위색합성·2024
- 주요 지물 팝업, 오버레이 투명도, 축척

## 환경 메모
- 한글 폰트: `/usr/share/fonts/truetype/nanum/NanumGothic*.ttf` (matplotlib·pptx 임베드)
- libreoffice가 이 환경에서 OOXML 변환 불가 → PDF는 matplotlib로 직접 생성
- 발표자료 텍스트에 U+2212(−) 대신 ASCII '-' 사용 (NanumGothic 글리프 누락 회피)

## 한계 (정직 보고)
- SAR 남서부 결측(상대궤도 커버 73%) → 열·광학으로 보완
- 단일시기 LST 절대비교 불가(촬영일 기상차 +4°C) → 상대이상(anomaly)으로 대응
- Landsat 열해상도 100 m, 비지도분류 검증표본 부재
