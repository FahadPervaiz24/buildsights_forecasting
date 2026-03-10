# BuildSights Forecasting v1 — Requirement Checklist

## Product Objective
- Build a forecasting system for NYC permit counts where **district-level forecasting is the baseline track** and **cluster-wise aggregated forecasting is the primary modeling track**.
- Ensure clustering outputs are interpretable and reproducible enough to support regime-aware forecasting features.

## Phase 1 — Data Ingestion and Unified Feature Base
- [x] Ingest DOB Permit Issuance (`ipu4-2q9a`) to parquet via Socrata API
- [x] Ingest DOB NOW Build Permits (`rbx6-tga4`) to parquet via Socrata API
- [x] Check source schemas for required date and location fields
- [x] Build merged dataset `data/processed/permits_unified.parquet` combining historical and DOB NOW records
- [x] Run overlap checks to detect duplicate permits across the two systems
- [x] Define rules for how overlapping records are handled

## Phase 2 — Spatial Attribution and District Baseline Track
- [x] Load NYC Community District geometry (`nycd_25d`)
- [x] Assign permits to districts and boroughs using a spatial join
- [x] Save district-attributed permit dataset for modeling
- [x] Build monthly permit counts by district
- [x] Run baseline forecasting benchmarks (MA12 rolling baseline + SARIMA comparison)
- [ ] Finalize district baseline evaluation setup (rolling-origin vs fixed holdout)

## Phase 3 — Raw-Point Clustering and Cluster Assignment
- [x] Run borough-aware HDBSCAN clustering on raw permit point data
- [x] Export permit-level cluster assignments (`cluster_id_raw`, `cluster_id_visual`, `cluster_id_final`)
- [x] Add visual cluster cap to avoid over-fragmented map output
- [x] Reassign noise points to the nearest visual cluster
- [ ] Build cluster diagnostics summary (cluster sizes, coverage, assignment distances)
- [ ] Save clustering configuration (parameters + run metadata) for reproducibility

## Phase 4 — Cluster-Level Forecasting Dataset
- [ ] Build monthly permit counts grouped by `cluster_id_final`
- [ ] Add temporal modeling features (lags, rolling averages, seasonal flags)
- [ ] Save modeling dataset `monthly_permits_by_cluster_modeling.parquet`

## Phase 5 — Forecast Modeling and Evaluation
- [ ] Train baseline cluster-level forecasting models
- [ ] Compare cluster forecasts against district baselines using MAE and sMAPE
- [ ] Produce summary table comparing district vs cluster forecasting results

## Phase 6 — Cluster Interpretation and Analysis
- [ ] Build cluster summary tables (activity level, volatility, seasonality, permit mix)
- [ ] Identify characteristics that distinguish clusters for reporting

## Phase 7 — Visualization and Forecast Interface
- [x] Monthly permit volume diagnostics and trend plots
- [x] Animated visualization of clustering workflow
- [x] Raw / visual-cap / final cluster maps
- [ ] Generate cluster-level time series diagnostics for major clusters
- [ ] Export forecast outputs in map-ready format
- [ ] Implement interactive map visualization using deck.gl

## Phase 8 — Reproducibility and Handoff
- [ ] Write runbook describing the full pipeline and execution order
- [ ] Finalize repository documentation and environment setup
- [ ] Assemble final project package (README, PRD, report, model outputs)