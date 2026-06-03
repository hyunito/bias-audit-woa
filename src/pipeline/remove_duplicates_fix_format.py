import pandas as pd
from src.pipeline.handle_missing_data import process_missing_data
from src.pipeline.tracker_setup import tracker

@tracker.track("Remove Duplicates")
def remove_duplicates(df):
    """
    Remove exact duplicated rows from the dataset.
    """
    df = df.copy()
    df = df.drop_duplicates()
    return df

@tracker.track("Fix Format")
def fix_format(df):    
    """
    Type cast certain columns and fix formatting like number commas and typos.
    """
    print("fix_format started")
    
    numeric_cols = ['age', 'fnlwgt', 'education-num', 'capital-gain', 'capital-lose', 'hours-per-week']
    for col in numeric_cols:
        if col in df.columns:
            if df[col].dtype == 'object':
                df[col] = df[col].apply(lambda x: str(x).replace(',', '') if pd.notnull(x) else x)
            df[col] = pd.to_numeric(df[col], errors='coerce').astype('Int64')

    cat_cols = ['workclass', 'education', 'marital-status', 'occupation', 'relationship', 'race', 'sex', 'native-country', 'income']
    for col in cat_cols:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: str(x).strip() if pd.notnull(x) else x)
            df[col] = df[col].replace('nan', pd.NA)

    if 'workclass' in df.columns:
        df['workclass'] = df['workclass'].replace({'privat': 'Private', 'state gov': 'State-gov'})
    
    if 'education' in df.columns:
        df['education'] = df['education'].str.capitalize()
        
    if 'marital-status' in df.columns:
        df['marital-status'] = df['marital-status'].str.capitalize()
    
    if 'relationship' in df.columns:
        df['relationship'] = df['relationship'].str.capitalize()
        
    if 'race' in df.columns:
        df['race'] = df['race'].replace({'wht': 'White', 'blk': 'Black'})
        
    if 'sex' in df.columns:
        df['sex'] = df['sex'].str.capitalize()
        df['sex'] = df['sex'].replace({'m': 'Male', 'M': 'Male', 'f': 'Female', 'F': 'Female', 'fem': 'Female'})
        
    if 'native-country' in df.columns:
        df['native-country'] = df['native-country'].replace({'USA': 'United-States', 'US': 'United-States', 'united-states': 'United-States'})
        
    return df

def process_format_and_duplicates(df):
    """Entry point for this pipeline stage."""
    print("\nStep 1: Removing duplicates and fixing format...")
    df = remove_duplicates(df)
    df = fix_format(df)
    print(f"Shape after step 1: {df.shape}")
    
    
    return process_missing_data(df)
