# Forecasting Notes

## Issues
- Community district IDs which dont exist appear in BoroCD rows
- '164' with 1938 permits, '226' '227' and '228' with 532 permits, '355' with 905 permits, '480' '481' '482' '483' '484' with 2535 permits, and '595' with 190 permits 

## Progress
- Ingested historical permits (`ipu4-2q9a`) and DOB NOW permits (`rbx6-tga4`) to raw parquet.
- Built canonical unified schema in `data/processed/permits_unified.parquet`.
- Updated plots to use unified dataset and DOB NOW-aware timeline.
- Added spatial join script to attach `BoroCD` from NYCD polygons.
- Dupe check (geoLoc + time match) yields 1275 collisions. Negligible considering simultaneous issuance in large projects
- Zero records with NaN geolocation
- Aggregated monthly permit counts by `BoroCD` and month (ready to persist as `permits_by_district_month.parquet`).

## Next
- Re-run monthly baselines on unified data.
- Plot with geospatial features.
- Build features including geospatial location.
- Decide how to handle invalid/rare `BoroCD` values before modeling.






## Metric COMPS
-12 Month rolling avg: 
Avg VAL MAE: 30.8749
Avg VAL sMAPE: 0.1437
-ETS
MAE: 44.80715648338512 
sMAPE 0.25613349456018863
-ETS+MA12 50/50
MAE: 43.85294773562688 
sMAPE: 0.2504583795765319


