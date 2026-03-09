# Scripts Folder Guide

This folder contains data-engineering and modeling code for feature construction, forecasting baselines, unsupervised clustering, and model diagnostics.

## Top-level scripts
- `inspect_data.py`: Fast schema/output sanity-check utility used during feature pipeline iteration.
- `monthly_mean_baseline.py`: Univariate rolling-window baseline for monthly count forecasting with MAE/sMAPE evaluation.
- `monthly_model_compare.py`: District-level SARIMA baseline benchmarking for temporal model comparison.

## `data_processing/`
- `data_processing/ingest_permits_api_to_parquet.py`: Generic Socrata ingestion job for raw feature extraction to parquet.
- `data_processing/ingest_dob_now_api_to_parquet.py`: Source-specific ingestion job for DOB NOW Build permit records (`rbx6-tga4`).
- `data_processing/build_unified_permits.py`: Cross-source schema harmonization and canonical feature table construction.
- `data_processing/spatial_border_ingest.py`: Spatial feature attribution step that maps permits to district polygons.
- `data_processing/build_monthly_permits_by_district.py`: Time-series panel builder that creates district-by-month count targets.
- `data_processing/hdbscan_clustering.py`: Adaptive borough-wise HDBSCAN regime discovery on raw permit points with visual-cap and final assignment outputs.

## `visualization/`
- `visualization/plot_permits_overview.py`: Generates trend/seasonality diagnostics for monthly permit count behavior.
- `visualization/animate_hdbscan_process.py`: Animates staged cluster formation and assignment transitions for unsupervised model interpretation.

## `visualization/output/`
- `visualization/output/monthly_volume.png`: Monthly permit count plot with rolling average overlay.
- `visualization/output/month_of_year_profile.png`: Month-of-year seasonality profile chart.
- `visualization/output/geo_coverage_over_time.png`: Spatial/geographic coverage progression plot over time.
- `visualization/output/log_cell_density_map.png`: Legacy log-density map from cell-based clustering workflow.
- `visualization/output/hdbscan_clusters_filled.png`: Legacy filled-cluster map from earlier cell-based HDBSCAN workflow.
- `visualization/output/raw_permits_density_hexbin.png`: Log-density hexbin map from raw permit points.
- `visualization/output/hdbscan_clusters_raw_permits.png`: Raw HDBSCAN cluster map from raw permit points.
- `visualization/output/hdbscan_clusters_raw_permits_visual_cap.png`: Visual-cap merged cluster map used to reduce over-granularity.
- `visualization/output/hdbscan_process.gif`: Early animation output from prior clustering pipeline iteration.
- `visualization/output/hdbscan_process_improved.gif`: Improved animation output for the current raw-permit clustering workflow.

## Notes
- `__pycache__/` artifacts are runtime bytecode caches and are not source scripts.
- `.DS_Store` files are macOS Finder metadata and are not project logic.
