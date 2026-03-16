import pandas as pd;

df = pd.read_parquet("data/processed/full_permits_by_cluster.parquet")

"""
Null Val tests: 
print("Total Records: ", len(df))
print("NaN Records: ")
for c in ['source_system', 'permit_id', 'issued_date', 'filing_date',
       'expiration_date', 'permit_status', 'job_type', 'work_type', 'borough',
       'bin', 'block', 'lot', 'zip_code', 'latitude', 'longitude',
       'community_board', 'council_district', 'census_tract', 'nta',
       'estimated_job_cost', 'cluster_id_final', 'cluster_assignment_dist_ft']:
       print(c, ": ", df[df[c].isna()].shape[0])

Results:

Total Records:  4876612
NaN Records: 
source_system :  0
permit_id :  212
issued_date :  21120
filing_date :  891850
expiration_date :  13059
permit_status :  11228
job_type :  891849
work_type :  722391
borough :  0
bin :  0
block :  498
lot :  649
zip_code :  4741
latitude :  23529
longitude :  23529
community_board :  13371
council_district :  23529
census_tract :  23529
nta :  23529
estimated_job_cost :  3984764
cluster_id_final :  23529
cluster_assignment_dist_ft :  23529

"""
#Modeling set's creation requires removal of rows whos cluster_id_final and issued_date
#are missing, implicitly handling lat/long as well
#df = df[["permit_id", "issued_date", "cluster_id_final"]].copy()

df = df.dropna(subset=["issued_date", "cluster_id_final"])
df["cluster_id_final"] = df["cluster_id_final"].astype("Int64")

df["issued_date"] = df["issued_date"].dt.to_period("M")
df = df.groupby(["cluster_id_final", "issued_date"])["permit_id"].size().rename("permit_count").reset_index()
print(df.iloc[10500:10550], df.shape, df.columns)

df = df.sort_values(["issued_date"])
print(df.iloc[10500:10550])
