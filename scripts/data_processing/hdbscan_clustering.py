import pandas as pd
import geopandas as gpd
import numpy as np
import hdbscan
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from sklearn.cluster import KMeans
from sklearn.neighbors import NearestNeighbors


INPUT = "data/processed/permits_unified.parquet"
NYCD_SHAPEFILE = "data/raw/nycd_25d/nycd.shp"
YEARS_BACK = 10
K_SIZE = 18.0
MIN_CLUSTER_SIZE_FLOOR = 300
MIN_CLUSTER_SIZE_CEIL = 3000
MIN_SAMPLES_FLOOR = 5
MIN_SAMPLES_CEIL = 80
MIN_SAMPLES_RATIO = 0.015
TARGET_VISUAL_CLUSTERS = 150

OUTPUT_DENSITY = "scripts/visualization/output/raw_permits_density_hexbin.png"
OUTPUT_CLUSTERS = "scripts/visualization/output/hdbscan_clusters_raw_permits_visual_cap.png"
OUTPUT_ASSIGNMENTS = "data/processed/permit_cluster_assignments.parquet"


permits = pd.read_parquet(INPUT)
permits["issued_date"] = pd.to_datetime(permits["issued_date"], errors="coerce")

cutoff = pd.Timestamp.now() - pd.DateOffset(years=YEARS_BACK)
permits_recent = permits.loc[
    (permits["issued_date"] >= cutoff)
    & permits["latitude"].notna()
    & permits["longitude"].notna()
].copy()

if permits_recent.empty:
    raise RuntimeError("No valid permit points found after date/lat-lon filtering.")

gdf = gpd.GeoDataFrame(
    permits_recent,
    geometry=gpd.points_from_xy(permits_recent["longitude"], permits_recent["latitude"]),
    crs="EPSG:4326",
).to_crs("EPSG:2263")

# Build borough polygons from community-district shapes and attach borough id to each permit.
nycd = gpd.read_file(NYCD_SHAPEFILE).to_crs(gdf.crs)
nycd = nycd[["BoroCD", "geometry"]].copy()
nycd["BoroCD"] = pd.to_numeric(nycd["BoroCD"], errors="coerce")
nycd = nycd.dropna(subset=["BoroCD"]).copy()
nycd["boro_num"] = (nycd["BoroCD"].astype(int) // 100).astype(int)
nycd = nycd[nycd["boro_num"].between(1, 5)].copy()

borough_polys = nycd.dissolve(by="boro_num", as_index=False)[["boro_num", "geometry"]]
borough_polys["area_sq_km"] = borough_polys.geometry.area / 1_000_000.0

gdf = gpd.sjoin(gdf, borough_polys, how="left", predicate="within").drop(columns=["index_right"])
gdf = gdf.dropna(subset=["boro_num"]).copy()
gdf["boro_num"] = gdf["boro_num"].astype(int)

coords = np.column_stack([gdf.geometry.x.values, gdf.geometry.y.values]).astype(np.float64)

# Density preview from raw permit points (no cell aggregation)
fig, ax = plt.subplots(figsize=(10, 10))
hb = ax.hexbin(coords[:, 0], coords[:, 1], gridsize=180, bins="log", cmap="plasma", mincnt=1)
ax.set_title("Raw Permit Density (Hexbin, Log Scale)")
ax.axis("off")
fig.colorbar(hb, ax=ax, label="log10(N)")
plt.tight_layout()
plt.savefig(OUTPUT_DENSITY, dpi=300, bbox_inches="tight")
plt.close(fig)

# Adaptive borough-wise HDBSCAN
gdf["cluster_id_raw"] = -1
gdf["cluster_prob"] = 0.0

next_cluster_id = 0
borough_rows = []

for boro_num, g in gdf.groupby("boro_num"):
    area_sq_km = float(
        borough_polys.loc[borough_polys["boro_num"] == boro_num, "area_sq_km"].iloc[0]
    )
    n_points = len(g)
    permits_per_sq_km = n_points / max(area_sq_km, 1e-9)

    min_cluster_size = int(
        np.clip(round(K_SIZE * np.sqrt(permits_per_sq_km)), MIN_CLUSTER_SIZE_FLOOR, MIN_CLUSTER_SIZE_CEIL)
    )
    min_samples = int(
        np.clip(round(MIN_SAMPLES_RATIO * min_cluster_size), MIN_SAMPLES_FLOOR, MIN_SAMPLES_CEIL)
    )

    b_coords = np.column_stack([g.geometry.x.values, g.geometry.y.values]).astype(np.float64)
    labels = np.full(n_points, -1, dtype=int)
    probs = np.zeros(n_points, dtype=float)

    if n_points >= min_cluster_size:
        clusterer = hdbscan.HDBSCAN(
            min_cluster_size=min_cluster_size,
            min_samples=min_samples,
            metric="euclidean",
            cluster_selection_method="leaf",
            core_dist_n_jobs=-1,
            approx_min_span_tree=True,
        )
        local_labels = clusterer.fit_predict(b_coords)
        labels = local_labels.copy()
        probs = clusterer.probabilities_

        mask = labels != -1
        if mask.any():
            labels[mask] = labels[mask] + next_cluster_id
            next_cluster_id = int(labels[mask].max()) + 1

    gdf.loc[g.index, "cluster_id_raw"] = labels
    gdf.loc[g.index, "cluster_prob"] = probs

    borough_rows.append(
        {
            "boro_num": int(boro_num),
            "permits": n_points,
            "area_sq_km": area_sq_km,
            "permits_per_sq_km": permits_per_sq_km,
            "min_cluster_size": min_cluster_size,
            "min_samples": min_samples,
            "clusters": int(len(set(labels)) - (1 if -1 in labels else 0)),
            "noise_pct": float((labels == -1).mean() * 100.0),
        }
    )

labels_all = gdf["cluster_id_raw"].to_numpy(dtype=int)
print("permits clustered:", len(gdf))
print("Num clusters (excluding noise):", len(set(labels_all)) - (1 if -1 in labels_all else 0))
print("Noise permits:", (labels_all == -1).sum(), f"({(labels_all == -1).mean()*100:.2f}%)")

cluster_sizes = (
    pd.Series(labels_all).loc[lambda s: s != -1].value_counts().sort_values(ascending=False)
)
if not cluster_sizes.empty:
    print("Top 10 cluster sizes (permits):")
    print(cluster_sizes.head(10).to_string())

borough_summary = pd.DataFrame(borough_rows).sort_values("boro_num")
print("\nBorough adaptive params + outcomes:")
print(
    borough_summary[
        ["boro_num", "permits", "permits_per_sq_km", "min_cluster_size", "min_samples", "clusters", "noise_pct"]
    ].to_string(index=False, float_format=lambda x: f"{x:.2f}")
)

# Merge raw clusters to a capped set for visualization only.
raw_non_noise = sorted([cid for cid in gdf["cluster_id_raw"].unique() if cid != -1])
gdf["cluster_id_visual"] = -1
cluster_map = {}

if raw_non_noise:
    cluster_geo = (
        gdf[gdf["cluster_id_raw"] != -1]
        .groupby("cluster_id_raw")
        .agg(
            cx=("geometry", lambda s: s.x.mean()),
            cy=("geometry", lambda s: s.y.mean()),
            n=("cluster_id_raw", "size"),
        )
        .reset_index()
    )
    n_raw = len(cluster_geo)
    n_visual = min(TARGET_VISUAL_CLUSTERS, n_raw)

    if n_visual < n_raw:
        km = KMeans(n_clusters=n_visual, random_state=42, n_init=10)
        merged_labels = km.fit_predict(cluster_geo[["cx", "cy"]].to_numpy(), sample_weight=cluster_geo["n"].to_numpy())
        cluster_geo["cluster_id_visual"] = merged_labels.astype(int)
    else:
        cluster_geo["cluster_id_visual"] = np.arange(n_raw, dtype=int)

    cluster_map = dict(
        zip(cluster_geo["cluster_id_raw"].astype(int).tolist(), cluster_geo["cluster_id_visual"].astype(int).tolist())
    )
    gdf.loc[gdf["cluster_id_raw"] != -1, "cluster_id_visual"] = (
        gdf.loc[gdf["cluster_id_raw"] != -1, "cluster_id_raw"].map(cluster_map).astype(int)
    )

    print(
        f"\nVisual cluster cap: raw={n_raw} -> visual={gdf.loc[gdf['cluster_id_visual'] != -1, 'cluster_id_visual'].nunique()}"
    )

# Assign all remaining noise points to the nearest visual cluster centroid.
gdf["cluster_id_final"] = gdf["cluster_id_visual"]
gdf["cluster_assignment_dist_ft"] = np.nan

visual_non_noise_mask = gdf["cluster_id_visual"] != -1
noise_mask = gdf["cluster_id_visual"] == -1

if visual_non_noise_mask.any() and noise_mask.any():
    visual_centers = (
        gdf.loc[visual_non_noise_mask]
        .groupby("cluster_id_visual")
        .agg(
            cx=("geometry", lambda s: s.x.mean()),
            cy=("geometry", lambda s: s.y.mean()),
        )
        .reset_index()
    )

    nn = NearestNeighbors(n_neighbors=1, algorithm="ball_tree")
    nn.fit(visual_centers[["cx", "cy"]].to_numpy())

    noise_xy = np.column_stack(
        [
            gdf.loc[noise_mask, "geometry"].x.to_numpy(),
            gdf.loc[noise_mask, "geometry"].y.to_numpy(),
        ]
    ).astype(np.float64)
    dist, idx = nn.kneighbors(noise_xy)
    assigned_visual = visual_centers["cluster_id_visual"].to_numpy()[idx[:, 0]]

    gdf.loc[noise_mask, "cluster_id_final"] = assigned_visual.astype(int)
    gdf.loc[noise_mask, "cluster_assignment_dist_ft"] = dist[:, 0]

print(
    "Final noise after assignment:",
    int((gdf["cluster_id_final"] == -1).sum()),
)

# Cluster visualization
rng = np.random.default_rng(42)
unique_ids = sorted(gdf["cluster_id_final"].unique())
non_noise = [cid for cid in unique_ids if cid != -1]
color_map = {cid: mcolors.to_hex(rng.random(3)) for cid in non_noise}
color_map[-1] = "#9e9e9e"
gdf["plot_color"] = gdf["cluster_id_final"].map(color_map)

fig, ax = plt.subplots(figsize=(10, 10))
gdf.plot(ax=ax, color=gdf["plot_color"], markersize=0.7, linewidth=0)
ax.set_title("HDBSCAN Clusters on Raw Permit Points")
ax.axis("off")
plt.tight_layout()
plt.savefig(OUTPUT_CLUSTERS, dpi=300, bbox_inches="tight")
plt.close(fig)

# Export assignments (no noise reassignment)
assign_cols = [
    "permit_id",
    "issued_date",
    "latitude",
    "longitude",
    "cluster_id_raw",
    "cluster_id_visual",
    "cluster_id_final",
    "cluster_assignment_dist_ft",
    "cluster_prob",
]
gdf[assign_cols].to_parquet(OUTPUT_ASSIGNMENTS, index=False)

print("saved density:", OUTPUT_DENSITY)
print("saved clusters:", OUTPUT_CLUSTERS)
print("saved assignments:", OUTPUT_ASSIGNMENTS)
