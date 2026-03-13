import pandas as pd;

df = pd.read_parquet("data/processed/permit_cluster_assignments.parquet")
#take data from permits

"""
df = df[["permit_id", "issued_date", "cluster_id_final"]].copy()
df["issued_date"] = df["issued_date"].dt.to_period("M")
df = df.groupby(["cluster_id_final", "issued_date"])["permit_id"].size().rename("permit_count").reset_index()
print(df.shape, df.iloc[1000:1050])
"""