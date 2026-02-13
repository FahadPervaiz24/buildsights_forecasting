# Buildsights Forecasting v1

Forecasting workspace for NYC DOB permits. Data is pulled from NYC Open Data, normalized into a unified schema, and modeled as monthly district-level time series.

## Data Sources
- **DOB Permit Issuance** (`ipu4-2q9a`) — historical permits
- **DOB NOW: Build – Approved Permits** (`rbx6-tga4`) — permits issued through DOB NOW (post‑2016)

## Pipeline (Quickstart)
1. **Ingest raw datasets (API → parquet)**
```bash
cd Buildsights_Forecasting_v1
python3 scripts/data_processing/ingest_permits_api_to_parquet.py --dataset-id ipu4-2q9a
python3 scripts/data_processing/ingest_dob_now_api_to_parquet.py
```

2. **Build unified schema**
```bash
python3 scripts/data_processing/build_unified_permits.py
```

3. **Attach community districts (BoroCD) via spatial join**
```bash
python3 scripts/data_processing/spatial_border_ingest.py
```

4. **Aggregate monthly counts by district**
```bash
python3 scripts/data_processing/build_monthly_permits_by_district.py
```

5. **Run baselines**
```bash
python3 scripts/monthly_mean_baseline.py
python3 scripts/monthly_model_compare.py
```

6. **Plot monthly volume**
```bash
python3 scripts/visualization/plot_permits_overview.py
```

## Key Outputs
- `data/raw/dob_historical.parquet`
- `data/raw/dob_now.parquet`
- `data/processed/permits_unified.parquet`
- `data/processed/permits_unified_with_district.parquet`
- `data/processed/monthly_permits_by_district.parquet`
- `data/processed/monthly_permits_by_district_modeling.parquet`

## Notes
- Mixed date formats are normalized in scripts; use `issued_date` for modeling.
- Geo fields are used only for spatial joins; raw data stays in `data/raw/`.
