# BuildSights Forecasting v1 — PRD Checklist

## Phase 1 — Raw Ingest
- [x] Ingest DOB Permit Issuance (`ipu4-2q9a`) to parquet
- [x] Ingest DOB NOW Build Permits (`rbx6-tga4`) to parquet
- [x] Confirm schema fields for geolocation and dates
- [ ] Record dataset metadata snapshot (row counts, last updated, schema)
- [ ] Add light data quality checks (nulls, outliers, missing months)

## Phase 2 — Unified Schema
- [x] Build `permits_unified.parquet` with canonical fields
- [x] Run cross‑system collision check (geo+time)
- [ ] Decide collision policy (drop, keep, tag)
- [ ] Add source coverage summary (counts by year and source)

## Phase 3 — Spatial Join
- [x] Load NYC Community District polygons
- [x] Reproject polygons to EPSG:4326
- [x] Spatial join permits to polygons
- [x] Write `permits_unified_with_district.parquet`
- [ ] Decide how to handle invalid/rare `BoroCD` codes
- [ ] Validate spatial join coverage and error rate by borough

## Phase 4 — Aggregation
- [x] Build monthly district series with **year‑month** timestamps
- [x] Filter low‑volume districts for modeling
- [x] Write `monthly_permits_by_district_modeling.parquet`
- [ ] Add citywide and borough‑level aggregates

## Phase 5 — Baselines
- [x] MA12 baseline per district
- [x] ETS baseline per district
- [x] SARIMA baseline per district
- [ ] Decide final comparison metric (simple average vs weighted)
- [ ] Persist metrics table to `data/processed/metrics_baselines.parquet`

## Phase 6 — Visualization
- [x] Monthly volume plot from unified dataset
- [ ] Add district‑level seasonal plots (optional)
- [ ] Add diagnostics plot for source overlap (2016–2019)

## Phase 7 — Model Selection
- [ ] Pick winner baseline
- [ ] Define next model class (e.g., seasonal regression, ETS + exogenous)
- [ ] Decide evaluation split policy (rolling vs fixed holdout)

## Phase 8 — Output + Handoff
- [ ] Save final metrics table
- [ ] Document model choice + rationale in report
- [ ] Write reproducibility notes (exact commands + expected outputs)
