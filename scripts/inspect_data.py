import pandas as pd


df = pd.read_parquet("data/processed/monthly_permits_by_district.parquet")
print(df.shape)
low_volume_districts = (
    df.groupby("BoroCD")["permit_count"]
      .sum()
      .loc[lambda s: s < 5000]
      .index
)

df_model = df[~df["BoroCD"].isin(low_volume_districts)].copy()

df_model.to_parquet(
    "data/processed/monthly_permits_by_district_modeling.parquet"
)
print(df_model.shape)