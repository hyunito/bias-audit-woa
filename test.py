import pandas as pd

raw_data_path = 'data/raw/adult_data_dirty.csv'
print(f"Loading raw data from {raw_data_path}...")
df = pd.read_csv(raw_data_path)

print(df['workclass'].unique())