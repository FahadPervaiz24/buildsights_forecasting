import pandas as pd


df = pd.read_parquet("data/processed/permits_unified.parquet")
print(df.groupby(["job_type"], dropna=False).size())
print("----------------",df.groupby(["work_type"], dropna=False).size())
