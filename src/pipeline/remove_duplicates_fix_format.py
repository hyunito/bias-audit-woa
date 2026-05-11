import pandas as pd
from src.pipeline.tracker_setup import tracker

@tracker.track("Remove Duplicates")
def remove_duplicates(df):
    """
    Remove exact duplicated rows from the dataset.
    """
    df = df.copy()
    df = df.drop_duplicates()

    return fix_format(df)

def fix_format(df):    
    """
    Type cast certain columns and fix formatting like number commas and typos.
    """
    print("fix_format started")
    # 2. Fix number formats with commas and type cast
    numeric_cols = ['age', 'fnlwgt', 'education-num', 'capital-gain', 'capital-lose', 'hours-per-week']
    for col in numeric_cols:
        if col in df.columns:
            if df[col].dtype == 'object':
                df[col] = df[col].apply(lambda x: str(x).replace(',', '') if pd.notnull(x) else x)
            # Cast to numeric, coerce errors to NaN, then cast to nullable Integer
            df[col] = pd.to_numeric(df[col], errors='coerce').astype('Int64')

    # 3. Type cast categorical columns to string and fix typos
    cat_cols = ['workclass', 'education', 'marital-status', 'occupation', 'relationship', 'race', 'sex', 'native-country', 'income']
    for col in cat_cols:
        if col in df.columns:
            # Cast to string only if not null, and strip whitespaces
            df[col] = df[col].apply(lambda x: str(x).strip() if pd.notnull(x) else x)
            # Remove any artificial 'nan' strings resulting from astype/str conversion
            df[col] = df[col].replace('nan', pd.NA)

    # Dictionary for known typos injected or present in the dirty data
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
        df['sex'] = df['sex'].replace({'m': 'Male', 'M': 'Male', 'f': 'Female', 'F': 'Female', 'fem': 'Female'})
        
    if 'native-country' in df.columns:
        df['native-country'] = df['native-country'].replace({'USA': 'United-States', 'US': 'United-States', 'united-states': 'United-States'})
        
    return df
