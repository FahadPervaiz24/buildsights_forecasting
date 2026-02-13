# Buildsights Forecasting v1

Clean rebuild workspace.

## Raw ingest from API

Fetch raw permit datasets directly from NYC Open Data API and save to Parquet.

```bash
cd Buildsights_Forecasting_v1
python3 scripts/data_processing/ingest_permits_api_to_parquet.py --dataset-id ipu4-2q9a
```

`ipu4-2q9a` ingest includes all dataset columns and explicitly includes:
- `permit_si_no`
- `gis_latitude`
- `gis_longitude`

For DOB NOW permits:

```bash
python3 scripts/data_processing/ingest_permits_api_to_parquet.py --dataset-id rbx6-tga4
```

`rbx6-tga4` ingest includes all dataset columns and explicitly includes:
- `job_filing_number`
- `issued_date`
- `latitude`
- `longitude`

Optional test run (first page only):

```bash
python3 scripts/data_processing/ingest_permits_api_to_parquet.py --dataset-id ipu4-2q9a --max-pages 1 --limit 10000
```
