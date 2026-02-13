import geopandas as gp
import pandas as pd

# Paths
POLY_PATH = "data/raw/nycd_25d/nycd.shp"
PERMITS_PATH = "data/processed/permits_unified.parquet"
OUTPUT_PATH = "data/processed/permits_unified_with_district.parquet"

# Load polygons and reproject to WGS84
polys = gp.read_file(POLY_PATH)
polys = polys.to_crs("EPSG:4326")
polys = polys[["BoroCD", "geometry"]].copy()

# Load permits (lat/lon in WGS84)
permits = pd.read_parquet(PERMITS_PATH)
permits = permits.copy()
permits = permits[permits["latitude"].notna() & permits["longitude"].notna()].copy()

# Build points GeoDataFrame
gdf = gp.GeoDataFrame(
    permits,
    geometry=gp.points_from_xy(permits["longitude"], permits["latitude"]),
    crs="EPSG:4326",
)

# Spatial join to assign community district
joined = gp.sjoin(gdf, polys, how="left", predicate="within")

# Write back to parquet (drop geometry/index columns)
out = joined.drop(columns=["geometry", "index_right"])
out.to_parquet(OUTPUT_PATH, index=False)

print("polygons:", polys.shape, "crs:", polys.crs)
print("permits with lat/lon:", len(permits))
print("joined rows:", len(out))
print("BoroCD nulls:", int(out["BoroCD"].isna().sum()))
print("output:", OUTPUT_PATH)
