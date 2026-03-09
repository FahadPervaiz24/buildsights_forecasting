# Data Folder Guide

This folder stores raw source datasets and processed modeling/clustering outputs used by the forecasting and spatial analysis pipelines.

## `raw/`
- `raw/dob_historical.parquet`: Raw DOB Permit Issuance records ingested from NYC Open Data (`ipu4-2q9a`).
- `raw/dob_now.parquet`: Raw DOB NOW Build permit records ingested from NYC Open Data (`rbx6-tga4`).
- `raw/district_spatial.zip`: Archived spatial boundary package used for district-level spatial joins.
- `raw/nycd_25d/nycd.shp`: NYC Community District polygon geometry used to assign permits to districts/boroughs.
- `raw/nycd_25d/nycd.shx`: Shapefile index companion for `nycd.shp`.
- `raw/nycd_25d/nycd.dbf`: Attribute table companion for `nycd.shp`.
- `raw/nycd_25d/nycd.prj`: Projection metadata companion for `nycd.shp`.
- `raw/nycd_25d/nycd.shp.xml`: Metadata XML companion for `nycd.shp`.

## `processed/`
- `processed/permits_unified.parquet`: Canonical merged permit table built from historical + DOB NOW datasets.
- `processed/permits_unified_with_district.parquet`: Unified permit table with community district (`BoroCD`) attached via spatial join.
- `processed/permit_cluster_assignments.parquet`: Permit-level raw/visual/final cluster labels and assignment diagnostics from HDBSCAN.
- `processed/cell_cluster_map.csv`: Legacy grid-cell-to-cluster mapping from earlier cell-based clustering workflow.
- `processed/aggregated_on_districts/permits_unified_with_district.parquet`: District-attributed unified permits used for district-level aggregation/modeling.
- `processed/aggregated_on_districts/monthly_permits_by_district.parquet`: Monthly permit counts by district for full coverage.
- `processed/aggregated_on_districts/monthly_permits_by_district_modeling.parquet`: Filtered monthly district series used for baseline forecasting experiments.
