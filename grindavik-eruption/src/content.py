# -*- coding: utf-8 -*-
"""발표 슬라이드 사양 (단일 소스). PPTX·PDF 빌더가 공유.

내러티브: 아이슬란드 Grindavík–Sundhnúkur 분화(2023→2025)를 광학·SAR·지표온도
다중센서로 교차탐지. 단일 광학지수는 이끼 위상/테프라로 과대추정되며, 다중센서
합의로 신규 용암을 견고하게 산정한다 — 선행연구 이어루 외(2022) 백두산 광학+SAR 융합의 응용.
"""
import os
from common import get_stats

S = get_stats()
LAVA = S["lava_km2"]; OPT = S["lava_optonly_km2"]; BARE_INC = S["class_area"]["2025"][2]-S["class_area"]["2023"][2]
NM = 7
MLIST = "트루컬러·NDVI·분류·CVA·PCA·SAR·LST"
HAS_LST = True

META = dict(
    title="위성 다중센서 기반 아이슬란드\nGrindavík–Sundhnúkur 분화 변화탐지 (2023→2025)",
    subtitle="광학·SAR·지표온도 융합으로 신규 용암류를 견고하게 탐지",
    course="AI기반 원격탐사 · 기말 팀프로젝트",
    team="이승훈 · 정송윤 · 주서진", date="2026. 06.", present_no=12,
    footer="아이슬란드 Grindavík 분화 변화탐지  ·  발표 12번",
)


def b(text, level=0, color="dark", bold=False):
    return (text, level, color, bold)


SLIDES = [
    {"type": "title"},

    {"type": "toc",
     "note": "목차. 배경과 연구 질문, 연구지역·데이터, 다중센서 변화탐지 방법, 결과(합의 용암·딥러닝·"
             "위험도·웹맵 시연), 결론 순서로 진행한다."},

    {"type": "section", "no": 1, "title": "배경 및 필요성"},

    {"type": "content", "kicker": "1. 배경 및 필요성", "title": "Reykjanes 화산활동 재개와 변화 모니터링",
     "bullets": [
        b("아이슬란드 Reykjanes 반도: 약 800년 휴지 후 2021년부터 화산활동 재개"),
        b("Sundhnúkur 분화구열: 2023.12 분화 시작 → 2024–2025 다수 분화 반복", 1),
        b("용암류가 Grindavík(읍)·Svartsengi 지열발전·블루라군을 위협(주민 대피·방어벽)", 1),
        b("대규모 용암 분출은 토지피복·지형·열환경을 광범위·급격하게 변화시킴"),
        b("→ 신규 용암의 위치·면적을 객관적·정량적으로 파악할 필요", 1),
        b("위성 원격탐사: 접근위험 지역을 광역·주기·비접촉 관측 — 화산 모니터링에 최적"),
        b("수업·연구 연계: 다분광 + SAR + 열적외 다중센서 융합 (이어루 외 2022 백두산 광학+SAR 연구의 화산 응용)", 0, "accent", True),
     ],
     "note": "아이슬란드 Reykjanes 반도는 약 800년 만에 화산활동이 재개됐고, 2023년 12월 "
             "Sundhnúkur 분화구열에서 분화가 시작돼 2024–2025년 여러 차례 반복됐다. 용암이 그린다비크 마을과 "
             "Svartsengi 지열발전소, 블루라군을 위협해 대피와 방어벽 건설이 있었다. 이런 급격한 변화를 정량 "
             "파악하려면 위성 원격탐사가 효과적이고, 특히 이어루 외(2022) 백두산 연구처럼 광학+SAR+열 다중센서 융합을 적용했다."},

    {"type": "content", "kicker": "1. 배경 및 필요성", "title": "연구 목적과 핵심 질문",
     "bullets": [
        b("목적: 분화 전후(2023→2025) 신규 용암류를 다중센서 원격탐사로 탐지·정량화"),
        b("핵심 질문", 0, "primary", True),
        b("단일 광학지수(NDVI 등)만으로 아이슬란드 화산지대 변화를 신뢰성 있게 잴 수 있는가?", 1),
        b("이끼(moss)의 계절·수분 위상과 테프라(화산재) 교란을 어떻게 분리할 것인가?", 1),
        b("광학·SAR·열 센서는 같은 용암을 어떻게 다르게/일관되게 포착하는가?", 1),
        b(f"접근: {NM}개 기법({MLIST})을 교차 적용하고, 센서 간 '합의'로 견고 추정", 0, "accent2", True),
     ],
     "banner": f"핵심 결과 미리보기 — 단일기법은 무식생 +{BARE_INC:.0f} km²로 과대추정. 다중센서 합의 신규 용암은 {LAVA:.0f} km².  왜 차이가? 본 발표가 규명한다.",
     "note": "목적은 분화 전후 신규 용암을 다중센서로 탐지·정량화하는 것. 핵심 질문은 ①단일 광학지수로 "
             "충분한가 ②이끼 위상·테프라 교란을 어떻게 분리하나 ③광학·SAR·열이 어떻게 일관되나이다. "
             "결론부터: 단일기법은 무식생 34 km² 증가로 과대추정되지만, 센서 합의 용암은 약 21 km²다. 그 차이를 규명한다."},

    {"type": "section", "no": 2, "title": "연구지역 및 데이터"},

    {"type": "content", "kicker": "2. 연구지역 및 데이터", "title": "연구지역 — Grindavík·Svartsengi·Sundhnúkur",
     "image": "fig01_location.png", "img_side": "left",
     "bullets": [
        b("위치: 아이슬란드 남서부", 0, "primary", True),
        b("Reykjanes 반도", 1), b("레이캬비크 남서 ~40 km", 1),
        b("63.88°N, 22.44°W", 1),
        b("분석범위 약 200.9 km²", 0, "primary", True),
        b("(육지 ≈ 169, 수역 ≈ 32 km²)", 1),
        b("주요 지물", 0, "primary", True),
        b("Sundhnúkur 분화구열(분화중심)", 1),
        b("그린다비크 읍·블루라군", 1),
     ],
     "note": "연구지역은 아이슬란드 남서부 Reykjanes 반도, 레이캬비크 남서 약 40km다. 분석범위 약 "
             "201km²(육지 169, 수역 32). 중앙·북부의 검은 영역이 2023–2025 분화로 형성된 용암류이고, 남쪽 해안의 "
             "그린다비크 읍, 블루라군·Svartsengi가 인접한다. 모든 결과지도에 방위표·축척·격자를 넣었다."},

    {"type": "content", "kicker": "2. 연구지역 및 데이터", "title": "사용 데이터 — 광학·SAR·지표온도 다중센서",
     "table": [["센서/자료", "내용", "시기"],
               ["Sentinel-2 L2A (광학)", "지표반사율 6밴드 10m", "2023·2024·2025 (9월)"],
               ["Sentinel-1 RTC (SAR)", "C-band VV/VH 후방산란(dB)", "2023 vs 2025"],
               ["Landsat 8/9 C2L2", "지표온도(LST)", "2023 vs 2025"]],
     "table_col_w": [1.4, 1.7, 1.2],
     "bullets": [
        b("설계: 동일 계절(9월) 비교", 0, "accent", True),
        b("→ 식생 위상차 최소화", 1),
        b("전처리", 0, "primary", True),
        b("UTM 27N·10m 공통격자 정합", 1),
        b("SCL 구름마스킹, SAR dB변환", 1),
        b("Landsat QA 마스킹", 1),
        b("취득: STAC API (AWS·PC)", 0, "grey"),
     ],
     "note": "데이터는 세 종류다. Sentinel-2 광학(2023·2024·2025 9월), Sentinel-1 SAR(VV/VH, 2023 vs 2025), "
             "Landsat 지표온도(2023 vs 2025). 광학은 세 해 모두 9월로 계절효과를 줄였고, SAR·지표온도도 같은 "
             "여름철(무설기)로 맞춰 비교했다. UTM 27N 10m 격자로 정합, 구름은 SCL·QA로 마스킹, SAR은 dB로 변환했다. "
             "취득은 STAC API(AWS·Planetary Computer) 자동수집 — 수업 실습의 EarthExplorer와 같은 Landsat C2 L2 "
             "산출물을 코드로 받아 재현 가능하게 한 것이다."},

    {"type": "section", "no": 3, "title": "연구 방법"},

    {"type": "content", "kicker": "3. 연구 방법", "title": "분석 흐름과 다중센서 변화탐지 기법",
     "pretext": "흐름:  3센서 수집 → 정합·마스킹 → (광학)지수·분류·CVA·PCA + (SAR)후방산란차 + (열)LST이상 → 다중센서 합의",
     "table": [["분류", "방법", "탐지 대상"],
               ["광학 분광지수", "NDVI · NBR · 차분", "식생·이끼 소실 / 용암 매몰"],
               ["토지피복분류", "k-means + 전이행렬", "범주적 토지피복 전이"],
               ["고급 변화탐지", "CVA(6밴드) · PCA(차분)", "종합 변화강도 · 주 변화축"],
               ["SAR 후방산란", "ΔVV/VH (거친 a'a 용암↑)", "구름·주야 무관 표면 거칠기"],
               ["지표온도(LST)", "Landsat 상대 ΔLST 이상", "용암·지열 열적 신호"],
               ["다중센서 합의", "광학 ∧ (SAR↑ ∨ 열↑)", "견고한 신규 용암 (잡음 제거)"]],
     "table_col_w": [1.1, 1.9, 1.9],
     "software": "Python (rasterio · scikit-learn · NumPy · Matplotlib · pyproj)  ·  STAC API 자동수집  ·  수집~지도·인터랙티브 웹 전 과정 코드화(재현가능)",
     "note": "처리흐름은 3센서 수집-정합-분석-합의다. 광학에서 NDVI·NBR 차분, k-means 분류+전이, CVA, "
             "PCA를 수행하고, SAR에서 후방산란 변화(거친 용암은 산란↑), 열에서 상대 LST 이상을 본다. 마지막에 "
             "세 센서를 교차해 '합의'된 곳만 신규 용암으로 판정한다. 전 과정을 코드화해 재현 가능하다."},

    {"type": "content", "kicker": "3. 연구 방법", "title": "지수 정의와 다중센서 합의 원리",
     "bullets": [
        b("광학 지수 (정규화 차분)", 0, "primary", True),
        b("NDVI=(NIR-R)/(NIR+R) → 식생·이끼 활력", 1),
        b("NBR=(NIR-SWIR2)/(NIR+SWIR2) → 식생소실·용암 매몰", 1),
        b("변화탐지", 0, "primary", True),
        b("차분영상 · CVA(6밴드 벡터크기, Otsu) · 차분 PCA(주 변화축)", 1),
        b("SAR: 신규 a'a 용암은 표면이 거칠어 후방산란(VV) 증가", 1),
        b("LST: 촬영일 기상차는 상대이상(anomaly)으로 보정 → 토지피복 신호 분리", 1),
        b("다중센서 합의 = 광학(식생→저알베도 무식생) ∧ (SAR 산란↑ ∨ 열 승온↑)", 0, "accent2", True),
        b("→ 이끼 위상·단일센서 잡음을 상호검증으로 제거", 1, "accent"),
     ],
     "note": "광학지수는 NDVI(식생), NBR(소실·매몰)을 쓴다. 변화탐지는 차분·CVA·PCA로 본다. SAR은 "
             "신규 a'a 용암이 거칠어 후방산란이 증가하는 원리를 이용하고, LST는 촬영일 기상차를 상대이상으로 "
             "보정해 토지피복 신호만 남긴다. 핵심은 다중센서 합의 — 광학이 식생소실을 가리키고 동시에 SAR 산란↑ "
             "또는 열 승온↑이 나타나는 곳만 신규 용암으로 본다. 단일센서 잡음을 상호검증으로 제거한다."},

    {"type": "section", "no": 4, "title": "결과 분석"},

    {"type": "content", "kicker": "4. 결과 분석", "title": "트루컬러 — 분화 전·중·후",
     "image": "fig02_truecolor.png", "img_side": "full",
     "banner": "2023(전) 이끼·용암대지 → 2024(분화중) → 2025(후) 중앙·북부에 검은 신규 용암류 뚜렷",
     "note": "트루컬러 3시기. 2023년엔 이끼와 기존 용암대지였던 중앙·북부가 2025년엔 검은 신규 용암으로 "
             "덮였다. 2024년은 분화 진행 중 스냅샷이다. 육안으로도 용암 확장이 분명하다."},

    {"type": "content", "kicker": "4. 결과 분석", "title": "용암류 확대 — Sundhnúkur→Grindavík",
     "image": "fig03_zoom.png", "img_side": "left",
     "bullets": [
        b("상세 변화", 0, "primary", True),
        b("2023: 이끼·용암대지(밝음)", 1),
        b("2025: 검은 신규 용암류", 1),
        b("적색 = 다중센서 합의 용암", 0, "accent2", True),
        b("그린다비크 읍 북측까지 근접", 1),
        b("Svartsengi·블루라군 인접", 1),
     ],
     "note": "분화중심 확대. 2023년 밝은 이끼·용암대지가 2025년 검은 신규 용암으로 바뀌었고, 적색이 "
             "다중센서 합의 용암이다. 용암이 그린다비크 읍 북측, Svartsengi·블루라군 가까이까지 확장했다."},

    {"type": "content", "kicker": "4. 결과 분석", "title": "NDVI — 식생·이끼 소실 (단, 위상교란 주의)",
     "image": "fig04_ndvi.png", "img_side": "left",
     "bullets": [
        b("정량 결과 (육지)", 0, "primary", True),
        b(f"NDVI 0.40(’23)→0.37(’25)", 1),
        b("ΔNDVI 감소 21% > 증가 16%", 1),
        b("용암부에서 NDVI 급감(적색)", 1),
        b("주의: 2024년 0.29로 일시 저하", 0, "accent2", True),
        b("→ 이끼 위상·테프라 교란 존재", 1),
     ],
     "note": "NDVI는 육지평균 0.40→0.37로 소폭 감소, 용암부는 급감(적색)이다. 다만 2024년이 0.29로 더 "
             "낮았다가 2025년 회복한 패턴은 용암으로 설명되지 않는다 — 이끼의 계절·수분 위상과 테프라(화산재) "
             "교란 때문이다. 따라서 NDVI 단독으로는 용암을 과대·오판할 수 있어 SAR·열로 보완한다."},

    {"type": "content", "kicker": "4. 결과 분석", "title": "다중센서 변화 증거 — 광학·SAR·열의 일치",
     "image": "fig05_multisensor.png", "img_side": "full",
     "banner": f"같은 위치(중앙·북부)에서 광학 식생↓ · SAR 후방산란 +{S['sar_dvv_mean']:.1f}dB↑ · 열 상대승온↑ 이 동시 발생 → 신규 용암의 강한 증거",
     "note": "핵심 융합 그림. (a)광학 ΔNDVI 감소, (b)SAR ΔVV 증가(거친 용암), (c)열 상대 LST 이상 승온이 "
             "모두 중앙·북부 같은 위치를 가리킨다. 서로 독립적인 세 물리량이 일치하므로 그곳이 신규 용암이라는 "
             "증거가 매우 강하다. SAR 남서부 결측(궤도 커버)은 열·광학으로 보완한다."},

    {"type": "content", "kicker": "4. 결과 분석", "title": "다중센서 합의 신규 용암 (핵심 결과)",
     "image": "fig06_consensus.png", "img_side": "full",
     "banner": f"다중센서 합의 신규 용암 ≈ {LAVA:.0f} km² (중심 {S['lava_lat']:.2f}°N) · 광학단독 잡음 {OPT:.0f} km² 제거 · 합의부 ΔVV {S['lava_dvv']:+.1f}dB·ΔLST′ {S['lava_anom']:+.1f}°C",
     "note": "핵심 결과다. 광학∧(SAR↑∨열↑) 합의로 산정한 신규 용암은 약 21km²로, Sundhnúkur 분화구열 "
             "(63.9°N)을 중심으로 분포한다. 광학단독 4km²는 합의에서 빠진 위상 잡음이다. 우측 막대처럼 단일기법 "
             "(분류 무식생 +34, ΔNDVI 35km²)은 과대추정이고, 합의는 약 21km²로 견고하다."},

    {"type": "content", "kicker": "4. 결과 분석", "title": "토지피복 분류 — 무식생 급증",
     "image": "fig07_class.png", "img_side": "left",
     "bullets": [
        b("k-means 비지도 3클래스", 0, "primary", True),
        b("수역 / 식생·이끼 / 나지·용암", 1),
        b("두 해 공통 군집 → 직접 비교", 1),
        b(f"나지·용암 23→57 km² (+{BARE_INC:.0f})", 0, "accent2", True),
        b("식생·이끼 147→114 km²", 1),
        b("단, 위상으로 과대 — 합의로 보정", 1, "accent"),
     ],
     "note": "k-means로 수역·식생이끼·나지용암 3클래스 분류. 두 해 화소를 함께 학습해 직접 비교했다. "
             "나지·용암이 23→57km²로 +34 증가했지만, 이 중 상당부는 이끼 위상으로 나지처럼 분류된 과대분이다. "
             "그래서 다중센서 합의로 보정해 약 21km²를 신규 용암으로 본다."},

    {"type": "content", "kicker": "4. 결과 분석", "title": "무식생 급증의 분해 — 과대추정 vs 견고추정",
     "image": "fig08_class_stats.png", "img_side": "full",
     "banner": f"2025 '나지·용암' 57 km² 중 다중센서 합의 신규 용암은 {LAVA:.0f} km² — 나머지는 기존 용암대지·위상 잡음",
     "note": "좌측은 클래스 면적 변화, 우측 도넛은 2025년 나지·용암 57km²의 구성이다. 그중 다중센서 "
             "합의 신규 용암이 약 21km², 나머지는 기존 용암대지·나지와 위상 잡음이다. 단일 분류 수치를 그대로 "
             "쓰면 과대추정임을 보여준다."},

    {"type": "content", "kicker": "4. 결과 분석", "title": "CVA·PCA — 데이터 기반 변화 확인",
     "image": "fig09_cva_pca.png", "img_side": "left",
     "bullets": [
        b("CVA(6밴드 변화벡터)", 0, "primary", True),
        b(f"Otsu 임계, 변화 {S['cva_change_km2']:.0f} km²(육지 {S['cva_change_pct']}%)", 1),
        b("PCA(차분영상)", 0, "primary", True),
        b(f"PC1이 분산 {S['pca_var'][0]:.0f}% 설명", 1),
        b(f"PC1↔ΔNDVI 상관 {S['pca_pc1_dndvi_corr']:+.2f}", 1),
        b("→ 주 변화축 = 식생→용암", 0, "accent", True),
     ],
     "note": "CVA는 6밴드 변화를 벡터로 합쳐 강도를 보고, Otsu 임계로 약 31km²(육지 18%)가 변화로 잡혔다. "
             "차분영상 PCA는 제1성분이 분산 89%를 설명하며 ΔNDVI와 -0.70 상관 — 데이터가 스스로 지목한 최대 "
             "변화축이 '식생→용암'이다. 별개 기법들이 같은 결론을 준다."},

    {"type": "content", "kicker": "4. 결과 분석", "title": "지표온도(LST) — 용암·지열 열신호",
     "image": "fig10_lst.png", "img_side": "left",
     "bullets": [
        b("Landsat 8/9 지표온도", 0, "primary", True),
        b(f"육지평균 {S['lst_2023']:.0f}→{S['lst_2025']:.0f}°C", 1),
        b(f"→ 기상차(+{S['lst_bg']:.0f}°C) 탓 — 절대비교 불가", 1, "grey"),
        b("보정 적용 — 상대이상(ΔLST′ = ΔLST - 배경평균)", 0, "primary", True),
        b(f"2025 고온부 {S['hot_km2']:.1f} km², 최대 {S['hot_temp']:.0f}°C", 1),
        b("용암·Svartsengi 지열에 집중", 0, "accent", True),
     ],
     "note": "Landsat 지표온도. 육지평균이 15→19°C로 올랐지만 이는 두 촬영일 기상차(+4°C)가 크다 — "
             "단일영상 절대비교의 한계다. 그래서 상대이상으로 보정하면, 용암부와 Svartsengi 지열지대가 주변보다 "
             "뚜렷이 승온한다. 2025년 고온화소는 약 1.7km², 최대 27°C로 신규 용암·지열 신호와 일치한다."},

    {"type": "content", "kicker": "4. 결과 분석", "title": "식생지수 종합 — 시기 궤적·분포",
     "image": "fig11_summary.png", "img_side": "left",
     "bullets": [
        b("NDVI 궤적", 0, "primary", True),
        b("2024 분화중 일시 저하(테프라·위상)", 1),
        b("→ 영구 손실(용암)과 구분 필요", 1, "accent2"),
        b("분포 이동", 0, "primary", True),
        b("저NDVI(용암) 화소 증가", 1),
        b("다중센서로 영구 용암만 추출", 0, "accent", True),
     ],
     "note": "NDVI 궤적은 2024년에 일시 저하 후 2025년 부분 회복했다 — 분화 중 테프라·이끼 위상에 의한 "
             "가역 변화로, 용암에 의한 영구 손실과 구분해야 한다. 분포에서도 저NDVI 화소가 늘었다. 결국 가역 "
             "위상과 영구 용암을 가르려면 다중센서 합의가 필요하다는 점을 종합적으로 보여준다."},

    {"type": "content", "kicker": "4. 결과 분석", "title": "인터랙티브 변화탐지 웹맵 (시연)",
     "image": "fig12_webpreview.png", "img_side": "left",
     "bullets": [
        b("브라우저 기반 인터랙티브 지도", 0, "primary", True),
        b("지표별 2023 vs 2025 스와이프 비교(트루컬러·NDVI·SAR)", 1),
        b("지도 클릭 = 픽셀 판독(ΔNDVI·ΔVV·ΔLST)", 1),
        b("결과 레이어 토글: 합의용암·잔열·딥러닝", 1),
        b("위험도 연결선(발전소 14m)·지물·축척", 1),
        b("Leaflet 직접 구현(코드 생성)", 0, "accent", True),
        b("발표 중 실제 지도 시연", 0, "accent2", True),
     ],
     "note": "정적 그림을 넘어 인터랙티브 웹맵도 제작했다. 같은 지표의 2023과 2025를 스와이프로 "
             "나란히 비교하고, 지도를 아무 데나 클릭하면 그 지점의 광학·SAR·열 변화값과 합의 판정이 즉석에서 떠서 "
             "다중센서 합의를 직접 확인할 수 있다. 합의용암 레이어와 자산 위험도 연결선도 켤 수 있다. "
             "Leaflet으로 직접 구현했으며(web/index.html) 발표 때 실제 지도를 시연하겠다."},

    {"type": "section", "no": 5, "title": "결론"},

    {"type": "content", "kicker": "5. 결론", "title": "핵심 발견",
     "bullets": [
        b("발견 ① 분화 전후 신규 용암을 다중센서로 정량 탐지", 0, "accent2", True),
        b(f"다중센서 합의 신규 용암 ≈ {LAVA:.0f} km², Sundhnúkur(63.9°N) 중심", 1),
        b("광학(식생↓)·SAR(+2.7dB)·열(상대승온)이 동일 위치에서 일치", 1),
        b("발견 ② 단일 광학지수는 과대·오판 위험", 0, "primary", True),
        b(f"분류 무식생 +{BARE_INC:.0f} km², ΔNDVI 35 km²로 과대추정", 1),
        b("원인: 이끼(moss) 계절·수분 위상 + 분화중 테프라(2024 NDVI 일시 저하)", 1),
        b("발견 ③ 방법론적 교훈 — 다중센서 융합의 가치", 0, "primary", True),
        b("독립 물리량의 '합의'가 단일센서 잡음을 제거 → 견고한 탐지", 1),
        b("구름·주야 무관한 SAR + 열적 LST가 광학을 상호보완", 1),
     ],
     "note": "결론. ①분화 전후 신규 용암을 다중센서로 약 21km² 정량 탐지했고 광학·SAR·열이 같은 곳에서 "
             "일치한다. ②단일 광학지수는 무식생 34km²·ΔNDVI 35km²로 과대추정되는데, 원인은 이끼 위상과 분화중 "
             "테프라(2024 일시 저하)다. ③교훈은 독립 물리량의 합의가 잡음을 제거해 견고한 탐지를 준다는 것 — "
             "이어루 외(2022) 백두산 광학+SAR 융합과 같은 방향이다."},

    {"type": "content", "kicker": "5. 결론", "title": "한계와 종합 결론",
     "bullets": [
        b("연구의 한계", 0, "primary", True),
        b(f"Sentinel-1 SAR 남서부 결측(궤도 커버 {S['sar_valid_pct']}%) → 열·광학으로 보완", 1),
        b("단일시기 LST 절대비교 불가(기상차) → 상대이상으로 대응", 1),
        b("Landsat 100m 열해상도, 광학·검증표본의 분광혼동", 1),
        b("종합 결론", 0, "accent", True),
        b(f"Grindavík 분화 전후 신규 용암 ≈ {LAVA:.0f} km²를 {NM}기법·3센서로 교차검증", 1),
        b("단일지수 과대추정을 다중센서 합의로 견고화 — 화산 변화탐지에 융합 필수", 1),
        b("향후: InSAR 지표변형, 시계열(분화별) 추적, 고해상 열적외 융합", 1),
     ],
     "note": "한계는 SAR 남서부 결측(73% 커버), LST 단일시기 절대비교 불가, Landsat 열해상도 100m다. "
             "각각 열·광학 보완, 상대이상 보정으로 대응했다. 종합하면 Grindavík 분화 전후 신규 용암 약 21km²를 "
             "7기법·3센서로 교차검증했고, 단일지수 과대추정을 합의로 견고화했다. 향후 InSAR 지표변형과 분화별 "
             "시계열로 확장할 수 있다."},

    {"type": "end", "note": "질의응답. 예상질문 ①왜 합의가 분류보다 작나? → 이끼 위상으로 나지처럼 분류된 과대분을 "
        "SAR·열 불일치로 제거하기 때문. ②SAR 증가가 왜 용암? → 신규 a'a 용암은 표면이 거칠어 후방산란이 커진다. "
        "③LST 절대값이 올랐는데? → 촬영일 기상차로, 상대이상으로 보정해 용암·지열 신호만 본다. ④2024는 왜 NDVI가 "
        "더 낮나? → 분화중 테프라 낙하·이끼 수분위상의 일시·가역 저하."},
]

# 융합 U-Net(fig13·14)은 본편에서 제외 — Modified U-Net 슬라이드에 교차확인 한 줄로 흡수.
# (figures/fig13_dl.png·fig14_dl_curve.png은 질문 대비 백업으로 보관)

# Modified U-Net 슬라이드 (11_modified_unet.py 실행 후 stats에 dl3 지표 있으면 삽입)
if "dl3_r_test" in S:
    MOD_SLIDE = {
        "type": "content", "kicker": "4. 결과 분석", "title": "딥러닝 — Modified U-Net 3-encoder 확장 (이어루 외 2022 기반)",
        "image": "fig16_modunet.png", "img_side": "full",
        "banner": (f"held-out R {S['dl3_r_test']:.2f}·MAE {S['dl3_mae_test']:.3f} — 임계 0.5 분할 시 "
                   f"{S['dl3_area_km2']:.0f} km²로 합의({LAVA:.0f})에 근접 (IoU {S['dl3_iou_test']:.2f})"),
        "note": ("이어루 외(2022) 백두산 논문의 Modified U-Net(분리 인코더 회귀)을 그대로 따르되, 광학만 쓰던 인코더를 "
                 "가시광(R,G,B)·적외광학(NIR·SWIR·변화지수)·SAR 세 개로 확장했다. 얼음변화도(0~1) 대신 '용암 변화강도'(0~1)를 "
                 "회귀했고 손실 MAE·옵티마 NAdam·ReLU 출력으로 원 논문 설정을 따랐다(epoch·lr·batch는 CPU에 맞춰 조정). "
                 f"학습에 안 쓴 우측에서 타깃과 R {S['dl3_r_test']:.2f}로 일치했고, 임계 0.5로 자르면 {S['dl3_area_km2']:.0f} km²로 "
                 "합의(21)에 근접한다. 라벨은 다중센서 증거로 만든 연속 약지도다. 별도의 단일 인코더 광학+SAR 융합 "
                 f"U-Net(이진 분할)로도 held-out IoU {S['dl_iou_test']:.2f}·F1 {S['dl_f1_test']:.2f}을 얻어 "
                 "교차 확인했다(상세는 백업 fig13·14)."),
    }
    # GT(정답) 정의·목적 슬라이드
    GT_SLIDE = {
        "type": "content", "kicker": "4. 결과 분석", "title": "딥러닝 학습 설계 — GT(정답)는 무엇이고, 무엇을 알아내나",
        "bullets": [
            b("GT = 현장 실측이 아닌 물리 규칙 기반 '약지도(weak label)' — 선행연구(이어루 외 2022)와 동일한 설계", 0, "primary", True),
            b("선행연구: 물=1·얼음=0 앵커의 상대 분광반사도 규칙 → 얼음변화도(0~1)를 GT로 학습 (상관 0.9968)", 1),
            b("본 연구: 식생소실 ∧ SWIR 어두움 (+ SAR 거칠기↑ 가산) → 용암 변화강도(0~1) 연속 약지도", 1),
            b("GT가 입력에서 유도되는데 왜 배우나? — 탐지 결과의 단순 재현이 아니라", 0, "accent2", True),
            b(f"규칙 '지식'의 일반화: 학습에 없던 공간(우측 30%)에서 원시영상→용암도 재현 (R {S['dl3_r_test']:.2f})", 1),
            b("장면별 임계·앵커 수작업을 제거 — 새 영상·다른 분화에 재적용 가능한 자동 탐지기", 1),
            b("SAR 결측 구역도 광학 패턴만으로 보완 출력", 1, "accent"),
            b("학습 방식 — 입력은 128×128 패치(주변 공간 문맥 활용), 채점(손실)은 화소별 MAE", 0, "primary", True),
            b("패치는 좌측 60%에서만 추출해 학습, 우측 30%로 평가 — 공간 분리로 순환논리 방지 (선행연구는 장면 분할)", 1),
        ],
        "note": ("딥러닝의 정답(GT)부터 명확히 하면, 현장 실측이 없어 물리 규칙으로 만든 약지도다. "
                 "참조한 이어루 외(2022) 백두산 연구도 물=1, 얼음=0을 앵커로 한 상대 분광반사도 규칙으로 얼음변화도를 만들어 "
                 "GT로 썼고, 본 연구도 같은 설계다 — 용암 변화강도는 다중센서 규칙(식생소실∧SWIR어두움+SAR↑)에서 나온다. "
                 "'GT가 입력에서 계산되는데 왜 배우나'가 자연스러운 질문인데, 목적은 탐지의 재현이 아니라 일반화다. "
                 "규칙에는 장면별 임계·앵커 같은 수동 요소가 들어가는데, 학습된 모델은 그것 없이 원시 영상에서 바로 "
                 "용암도를 출력하고, 본 적 없는 공간(우측 30% held-out)에서 R 0.99로 재현하며, SAR이 결측인 곳도 광학 "
                 "패턴으로 보완한다. 학습은 128×128 화소 패치 단위다 — 패치째 입력돼 각 화소의 예측이 주변 공간 "
                 "문맥(용암류의 연속성, 경계 질감)을 반영하고, 채점은 화소별 MAE로 한다. 패치는 좌측 60%에서만 추출해 "
                 "학습하고 우측 30%에서 평가했다. 선행연구도 같은 구조로 83장면을 66/17로 나눠 새 날짜·다른 센서"
                 "(L5/7/8) 장면에서 검증했다 — 우리는 한 장면이라 날짜 대신 공간을 분리해 순환논리를 방지했다."),
    }
    # 구조도(fig19, TikZ — src/fig19_arch.tex에서 빌드)를 결과 앞에 함께 삽입
    ARCH_SLIDE = {
        "type": "content", "kicker": "4. 결과 분석", "title": "딥러닝 모델 구조 — 3-encoder Modified U-Net",
        "image": "fig19_arch.png", "img_side": "full",
        "banner": (f"센서 그룹별 분리 인코더(가시광·적외광학·SAR) → 병목 병합 → skip 결합 디코더 → "
                   f"용암 변화강도(0~1) 화소 회귀 — MAE 손실·NAdam, 파라미터 {S['dl3_params_m']:.0f}M"),
        "note": ("모델 구조다. 입력을 가시광 3밴드·적외광학 7밴드·SAR 4채널 세 그룹으로 나눠 각각 "
                 "독립 인코더에 넣는다 — 이어루 외(2022)의 분리 인코더(2-encoder) 설계를 다중센서 3-encoder로 "
                 "확장했다(주황이 확장 부분). 각 인코더는 Conv-BN-ReLU 2회+MaxPool을 3번 반복해 채널을 32→256으로 "
                 "키우고, 세 병목을 concat으로 융합한 뒤, 디코더가 up-conv 각 단마다 세 인코더의 skip을 전부 받아 "
                 "공간 해상도를 복원한다. 출력은 1×1 Conv+ReLU로 화소별 용암 변화강도(0~1)를 회귀하고, 타깃은 "
                 "다중센서 연속 약지도, 손실 MAE·옵티마 NAdam — 원 논문 설정을 따랐다."),
    }
    _im = next(i for i, s in enumerate(SLIDES) if s.get("type") == "section" and s.get("no") == 5)
    SLIDES[_im:_im] = [GT_SLIDE, ARCH_SLIDE, MOD_SLIDE]
    for _s in SLIDES:
        if _s.get("title", "").startswith("분석 흐름"):
            _s["table"].append(["딥러닝", "Modified U-Net 3-enc 회귀 (이어루 외 2022)", "용암 변화강도(합의 일반화)"])
        if _s.get("title") == "핵심 발견":
            _s["bullets"].append(b(f"딥러닝(Modified U-Net 3-enc 확장)이 합의를 일반화 — held-out R {S['dl3_r_test']:.2f}·IoU {S['dl3_iou_test']:.2f}", 1, "accent"))

# 위험도 슬라이드 (10_hazard.py 실행 후 stats에 생성시기/거리 있으면 삽입)
if "lava_new_km2" in S:
    HAZ_SLIDE = {
        "type": "content", "kicker": "4. 결과 분석", "title": "위험도 분석 — 용암 생성시기와 자산 근접도",
        "image": "fig15_hazard.png", "img_side": "full",
        "banner": (f"생성시기: 구 {S['lava_old_km2']:.0f} + 최신 {S['lava_new_km2']:.0f} km²(자산 쪽 전진)  ·  "
                   f"근접: Svartsengi 발전소 {S['dist_svartsengi_m']:.0f} m · 블루라군 {S['dist_bluelagoon_m']:.0f} m · "
                   f"그린다비크 {S['dist_grindavik_m']/1000:.1f} km"),
        "note": ("위험도 관점에서 두 가지를 분석했다. ① 생성시기 — 2025 합의용암을 2024년 SWIR 어두움으로 구/신 분리했다 "
                 "(용암 SWIR≈0.02로 이끼 0.18보다 압도적으로 어두워 이끼 위상 혼란에 안 속는다). 구 용암 17.2, 최신 용암 3.7 km²이며 "
                 "최신 용암이 자산(남서) 쪽으로 전진했다. ② 근접 위험도 — 용암이 Svartsengi 발전소 14 m, 블루라군 113 m까지 다가왔고 "
                 "그린다비크 읍은 2.4 km 떨어져 있다. 실제로 발전소·블루라군은 방어벽으로 지켜낸 지역이다."),
    }
    _ih = next(i for i, s in enumerate(SLIDES) if s.get("type") == "section" and s.get("no") == 5)
    SLIDES.insert(_ih, HAZ_SLIDE)
    for _s in SLIDES:
        if _s.get("title") == "핵심 발견":
            _s["bullets"].append(b(f"위험도 — 최신 용암이 자산으로 전진, Svartsengi {S['dist_svartsengi_m']:.0f} m·블루라군 {S['dist_bluelagoon_m']:.0f} m 근접", 1, "accent"))

# 잔열 상태 슬라이드 — 본편 제외(2026-06-12 팀 결정: 딥러닝은 Modified U-Net 한 축으로 단순화).
# fig17/18·lava_state.tif·웹맵 ◆잔열 레이어는 백업/시연용으로 보존. 복원하려면 플래그만 True.
INCLUDE_LAVA_STATE = False
_LSJ = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "lava_state_stats.json")
if INCLUDE_LAVA_STATE and os.path.exists(_LSJ):
    import json as _json
    with open(_LSJ, encoding="utf-8") as _f:
        LS = _json.load(_f)
    _auc = LS["cv_spatial"]["MLP"]["auc"]
    STATE_SLIDE = {
        "type": "content", "kicker": "4. 결과 분석", "title": "위험도 심화 — 합의 용암의 잔열 상태 (얼마나 식었나)",
        "image": "fig17_lava_state.png", "img_side": "full",
        "banner": (f"열(ΔLST 이상) 약지도 × 광학+SAR 학습 — 합의 {LAVA:.0f} km² 중 잔열 {LS['area_pred']['hot']:.0f} km² 잔존, "
                   f"500m 공간블록 검증 AUC {_auc:.2f} (열 없이도 구분)"),
        "note": ("위험도의 후속 질문 — '찾아낸 용암이 얼마나 식었나'. 두 영상 모두 분화 휴지기라 흐르는 용암은 없고"
                 "(>100°C 화소 0), 배경 대비 상대승온(ΔLST 이상)이 3.5°C 이상이면 잔열, 1.5°C 미만이면 냉각으로 약지도를 만들었다. "
                 "학습 특징에서는 열을 일부러 제외하고 광학+SAR만 썼는데(라벨 누수 방지), 500m 공간블록 교차검증 AUC "
                 f"{_auc:.2f}로 구분된다 — 가장 강한 단서는 SAR 거칠기 변화(ΔVV)다. 합의 {LAVA:.0f} km² 중 약 "
                 f"{LS['area_pred']['hot']:.0f} km²가 아직 따뜻하고, 앞 장의 생성시기와 합치면 '최신·온기 잔존' 구역이 자산 방향이라 "
                 "모니터링 우선순위의 근거가 된다. 모델·평가 상세는 백업(fig18)."),
    }
    _is = next(i for i, s in enumerate(SLIDES) if s.get("type") == "section" and s.get("no") == 5)
    SLIDES.insert(_is, STATE_SLIDE)
