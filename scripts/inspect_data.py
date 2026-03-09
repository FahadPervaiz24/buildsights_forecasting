import pandas as pd


df = pd.read_parquet("data/processed/permits_unified.parquet")
#print(df.columns)
#"""
types =  df["estimated_job_cost"]
#types = types.drop_duplicates()
types = types.dropna()
print(types.mean()) #"""
