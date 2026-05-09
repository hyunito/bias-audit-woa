import pandas as pd
import numpy as np
import os

def make_dirty():
    np.random.seed(42)
    file_path = 'data/raw/adult_data.csv'
    
    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found.")
        return
        
    df = pd.read_csv(file_path, skipinitialspace=True)
    n = len(df)
    
    #age column
    df.loc[np.random.choice(n, int(n*0.05), replace=False), 'age'] = np.nan
    df.loc[np.random.choice(n, int(n*0.01), replace=False), 'age'] = 999
    df.loc[np.random.choice(n, int(n*0.01), replace=False), 'age'] = -5
    
    #workclass column
    df['workclass'] = df['workclass'].astype(str)
    private_idx = df[df['workclass'] == 'Private'].index
    if len(private_idx) > 0:
        df.loc[np.random.choice(private_idx, int(len(private_idx)*0.05), replace=False), 'workclass'] = 'privat'
    stategov_idx = df[df['workclass'] == 'State-gov'].index
    if len(stategov_idx) > 0:
        df.loc[np.random.choice(stategov_idx, int(len(stategov_idx)*0.05), replace=False), 'workclass'] = 'state gov'
    df.loc[np.random.choice(n, int(n*0.05), replace=False), 'workclass'] = np.nan
    
    #education column
    df['education'] = df['education'].astype(str)
    idx = np.random.choice(n, int(n*0.1), replace=False)
    df.loc[idx, 'education'] = df.loc[idx, 'education'].str.lower()
    idx = np.random.choice(n, int(n*0.1), replace=False)
    df.loc[idx, 'education'] = df.loc[idx, 'education'].str.upper()
    
    #education-num column
    df.loc[np.random.choice(n, int(n*0.05), replace=False), 'education-num'] = np.nan
    
    #marital-status column
    df['marital-status'] = df['marital-status'].astype(str)
    df.loc[np.random.choice(n, int(n*0.03), replace=False), 'marital-status'] = 'Married'
    df.loc[np.random.choice(n, int(n*0.03), replace=False), 'marital-status'] = 'Never Married'
    
    #occupation column
    df.loc[np.random.choice(n, int(n*0.05), replace=False), 'occupation'] = np.nan
    df.loc[np.random.choice(n, int(n*0.02), replace=False), 'occupation'] = 'Unknown'
    
    df['relationship'] = df['relationship'].astype(str)
    idx = np.random.choice(n, int(n*0.1), replace=False)
    df.loc[idx, 'relationship'] = df.loc[idx, 'relationship'].str.lower()
    
    #race column
    df['race'] = df['race'].astype(str)
    white_idx = df[df['race'] == 'White'].index
    if len(white_idx) > 0:
        df.loc[np.random.choice(white_idx, int(len(white_idx)*0.05), replace=False), 'race'] = 'wht'
    black_idx = df[df['race'] == 'Black'].index
    if len(black_idx) > 0:
        df.loc[np.random.choice(black_idx, int(len(black_idx)*0.05), replace=False), 'race'] = 'blk'
    
    #sex column
    df['sex'] = df['sex'].astype(str)
    male_idx = df[df['sex'] == 'Male'].index
    if len(male_idx) > 0:
        df.loc[np.random.choice(male_idx, int(len(male_idx)*0.05), replace=False), 'sex'] = 'male'
        df.loc[np.random.choice(male_idx, int(len(male_idx)*0.05), replace=False), 'sex'] = 'm'
        df.loc[np.random.choice(male_idx, int(len(male_idx)*0.05), replace=False), 'sex'] = 'M'
    female_idx = df[df['sex'] == 'Female'].index
    if len(female_idx) > 0:
        df.loc[np.random.choice(female_idx, int(len(female_idx)*0.05), replace=False), 'sex'] = 'F'
        df.loc[np.random.choice(female_idx, int(len(female_idx)*0.05), replace=False), 'sex'] = 'fem'
    
    #capital-gain column
    df.loc[np.random.choice(n, int(n*0.02), replace=False), 'capital-gain'] = -5000
    df.loc[np.random.choice(n, int(n*0.01), replace=False), 'capital-gain'] = 9999999
    
    #capital-lose column
    df.loc[np.random.choice(n, int(n*0.02), replace=False), 'capital-lose'] = -100
    
    #hours-per-week column
    df.loc[np.random.choice(n, int(n*0.02), replace=False), 'hours-per-week'] = 200
    df.loc[np.random.choice(n, int(n*0.01), replace=False), 'hours-per-week'] = -10
    df.loc[np.random.choice(n, int(n*0.05), replace=False), 'hours-per-week'] = np.nan
    
    #native-country column
    df['native-country'] = df['native-country'].astype(str)
    usa_idx = df[df['native-country'] == 'United-States'].index
    if len(usa_idx) > 0:
        df.loc[np.random.choice(usa_idx, int(len(usa_idx)*0.05), replace=False), 'native-country'] = 'USA'
        df.loc[np.random.choice(usa_idx, int(len(usa_idx)*0.05), replace=False), 'native-country'] = 'US'
        df.loc[np.random.choice(usa_idx, int(len(usa_idx)*0.05), replace=False), 'native-country'] = 'united-states'
    
    
    #duplicates = df.sample(n=int(n*0.05), replace=True)
    #df = pd.concat([df, duplicates], ignore_index=True)
    
    
    df.to_csv('data/raw/adult_data_dirty.csv', index=False)
    print(f"Successfully injected noise and anomalies into data/raw/adult_data_dirty.csv")

if __name__ == '__main__':
    make_dirty()
