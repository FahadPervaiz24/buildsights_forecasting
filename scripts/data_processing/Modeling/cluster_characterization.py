import pandas as pd
import numpy as np

df = pd.read_parquet("data/processed/full_permits_by_cluster.parquet")


clusters = df["cluster_id_final"].unique()

# quick cleanup 
df = df.dropna(subset=["cluster_id_final", "issued_date"]).copy()
df["cluster_id_final"] = df["cluster_id_final"].astype("Int64")
df["issued_date"] = pd.to_datetime(df["issued_date"], errors="coerce")

#next steps:
# - get core cluster stats first (num permits, num bins, maybe permits/bin)
# - work_type is messy rn (codes + names), need one mapping table 
# - then do % mix by cluster vs whole city mix
# - lifts: if plumbing is 2x city avg in a cluster, that is real signal
# - add monthly behavior: mean/std/cv by cluster to differentiate stable vs volatile clusters

