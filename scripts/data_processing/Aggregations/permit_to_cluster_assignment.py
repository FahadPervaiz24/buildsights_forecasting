import pandas as pd
import geopandas as gpd
import numpy as np
from sklearn.neighbors import NearestNeighbors

df = pd.read_parquet("data/processed/permits_unified.parquet")
centers = gpd.read_file("data/processed/cluster_centroids.geojson")

# Keep rows with valid lat/lon
mask = df["latitude"].notna() & df["longitude"].notna()
work = df.loc[mask].copy()

# Points -> projected CRS for distance in feet
pts = gpd.GeoDataFrame(
    work,
    geometry=gpd.points_from_xy(work["longitude"], work["latitude"]),
    crs="EPSG:4326",
).to_crs("EPSG:2263")

centers = centers.to_crs("EPSG:2263")

# Nearest centroid assignment
pt_xy = np.column_stack([pts.geometry.x.values, pts.geometry.y.values]).astype(np.float64)
ct_xy = np.column_stack([centers.geometry.x.values, centers.geometry.y.values]).astype(np.float64)

nn = NearestNeighbors(n_neighbors=1, algorithm="ball_tree")
nn.fit(ct_xy)

dist, idx = nn.kneighbors(pt_xy)
assigned_cluster = centers["cluster_id_final"].to_numpy()[idx[:, 0]]

# Write back to original df
df["cluster_id_final"] = pd.NA
df["cluster_assignment_dist_ft"] = pd.NA
df.loc[mask, "cluster_id_final"] = assigned_cluster
df.loc[mask, "cluster_assignment_dist_ft"] = dist[:, 0]
print(df.shape,df.head())
print(df.columns)
df.to_parquet("data/processed/full_permits_by_cluster.parquet")