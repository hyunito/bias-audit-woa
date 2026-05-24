import pandas as pd

raw_data_path = 'ACSIncome_2018_US.csv'
print(f"Loading raw data from {raw_data_path}...")
df = pd.read_csv(raw_data_path)

print(df.shape)