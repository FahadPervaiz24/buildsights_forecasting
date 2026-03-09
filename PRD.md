# BuildSights Forecasting v1 — PRD Checklist

## Product Objective
- Build a forecasting system for NYC permit counts where **district-level forecasting is the baseline track** and **cluster-wise aggregated forecasting is the primary modeling track**.
- Ensure clustering outputs are interpretable and reproducible enough to support regime-aware forecasting features.

## Phase 1 — Data Ingestion and Unified Feature Base
- [x] Ingest DOB Permit Issuance (`ipu4-2q9a`) to parquet
- [x] Ingest DOB NOW Build Permits (`rbx6-tga4`) to parquet
- [x] Validate source schema availability for key date/geospatial fields
- [x] Build canonical unified table `data/processed/permits_unified.parquet`
- [x] Run cross-system overlap diagnostic (geo + time collision check)
- [ ] Record dataset metadata snapshot (row counts, source update timestamps, schema hash)
- [ ] Formalize collision handling policy (tag/drop/retain)

## Phase 2 — Spatial Attribution and District Baseline Track
- [x] Load NYC Community District geometry (`nycd_25d`)
- [x] Spatially attribute permits to district/borough boundaries
- [x] Write district-attributed unified output
- [x] Build monthly district time series for baseline forecasting
- [x] Run district baselines (MA12 + SARIMA workflow currently in repo)
- [ ] Persist district baseline metrics table (`data/processed/metrics_district_baselines.parquet`)
- [ ] Lock district baseline split protocol (rolling origin vs fixed holdout)

## Phase 3 — Raw-Point Clustering and Cluster Assignment
- [x] Run raw-permit point clustering with adaptive borough-wise HDBSCAN
- [x] Export permit-level cluster assignments (`cluster_id_raw`, `cluster_id_visual`, `cluster_id_final`)
- [x] Add visual-cluster cap to reduce over-granularity for maps
- [x] Add post-assignment pass to map residual noise points to nearest visual cluster
- [ ] Add cluster quality table (coverage, silhouette proxy, cluster size distribution, assignment distance quantiles)
- [ ] Add versioned clustering config snapshot (all hyperparameters + run timestamp)

## Phase 4 — Cluster-Wise Forecasting Dataset (Primary Track)
- [ ] Build monthly permit counts aggregated by `cluster_id_final`
- [ ] Add cluster-level temporal features (lags, rolling means, seasonal flags, trend indicators)
- [ ] Add cluster composition features (permit mix, source mix, cost stats) using leakage-safe lagging
- [ ] Persist modeling table `data/processed/monthly_permits_by_cluster_modeling.parquet`
- [ ] Add train/validation/test split logic for cluster panel forecasting

## Phase 5 — Forecasting Models and Evaluation
- [ ] Train baseline cluster-wise models (MA12 / SARIMA-style) as first benchmark
- [ ] Train pooled panel model across clusters (with cluster ID effects/features)
- [ ] Compare against district baseline on common metrics (MAE, sMAPE, weighted variants)
- [ ] Select primary objective metric and secondary diagnostics
- [ ] Produce model comparison table with both district and cluster tracks

## Phase 6 — Cluster Interpretation and Explainability
- [ ] Create cluster profile table (top permit types, cost profile, volatility, seasonality)
- [ ] Compute cluster-vs-city lift metrics for categorical distributions
- [ ] Identify distinguishing features per cluster for interpretation/report narrative
- [ ] Validate that cluster definitions are behaviorally meaningful (not only geometric artifacts)

## Phase 7 — Visualization and Reporting
- [x] Monthly volume plot from unified dataset
- [x] Animation for staged clustering process
- [x] Raw/visual-cap/final cluster maps
- [ ] Add cluster-wise time-series diagnostics (top-N clusters by volume)
- [ ] Add forecast-vs-actual plots for both district and cluster tracks
- [ ] Update report with final model choice, tradeoffs, and interpretation findings

## Phase 8 — Reproducibility and Handoff
- [ ] Write exact runbook with command order and expected outputs
- [ ] Add data and script folder documentation completeness checks
- [ ] Add environment/dependency spec for clean reruns
- [ ] Finalize handoff package (README + PRD + report + metrics artifacts)
