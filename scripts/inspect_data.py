import pandas as pd


df = pd.read_parquet("data/processed/permits_unified.parquet")
print(df.columns)
