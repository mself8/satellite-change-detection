# Satellite Change Detection — Two Course Projects

Team final projects from *AI-Based Remote Sensing* (University of Seoul, Spring 2026): two end-to-end satellite change-detection studies, from STAC data acquisition to presentation decks and an interactive web map.

Detailed write-ups live in each project folder (in Korean); this page summarizes both in English.

## 1. Grindavík–Sundhnúkur eruption lava mapping (2023 → 2025) — [`grindavik-eruption/`](grindavik-eruption/)

Robust mapping of the new lava flows from the Sundhnúkur fissure eruptions near Grindavík, Iceland, by requiring **multi-sensor consensus**: Sentinel-2 optical (vegetation loss), Sentinel-1 SAR (ΔVV +2.7 dB), and Landsat land-surface-temperature anomaly (+3.9 °C) must agree per pixel.

- **Consensus new lava ≈ 21 km²** (UTM 27N, 10 m grid, AOI ≈ 201 km²)
- Single-sensor optical methods **overestimate** (+33–35 km²): moss phenology and tephra disturb NDVI — the temporary 2024 NDVI drop demonstrates it — and the consensus rule removes ~4 km² of that noise
- Also included: k-means land-cover transitions, CVA/PCA change analysis, a hazard map, **two deep-learning experiments** (incl. a Modified U-Net following the instructor's published Mt. Paektu optical+SAR fusion research), residual-heat ("lava state") classification of the fresh lava field, and an **interactive before/after web map** — open [`grindavik-eruption/web/index.html`](grindavik-eruption/web/) in a browser (Leaflet bundled; only basemap tiles need internet)

## 2. Incheon International Airport Phase-4 expansion (2017 → 2025) — [`incheon-airport/`](incheon-airport/)

Quantitative before/after analysis of the airport's Phase-4 construction using a **same-calendar-date** Sentinel-2 pair (Oct 28, 0 % cloud, seasonal effects cancelled) and six change-detection techniques (spectral indices, k-means transition matrices, CVA, PCA, Landsat LST).

- Counter-intuitive headline: vegetation on stable land **increased by +8.8 km²** — the 2017 baseline was peak-construction bare ground and post-completion landscaping followed; genuinely new impervious surface is local (3.0 km²)
- A cross-sensor check (2025 S2B vs S2C, identical NDVI 0.392) confirms the vegetation gain is real, not sensor drift

## Data

Raster inputs (`*.tif`) are **not committed** (size). Each project re-fetches them from open STAC endpoints: AWS earth-search for Sentinel-2 (no auth) and Microsoft Planetary Computer for Sentinel-1 RTC and Landsat C2L2. Committed instead: all result figures, derived statistics (JSON), the presentation decks (PDF), and the web map — so the results are browsable without downloading anything.

## Credit

Course team projects (presentation team #12, three members), presented June 2026.
