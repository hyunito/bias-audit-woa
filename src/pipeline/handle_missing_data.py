import pandas as pd
import numpy as np
from src.utils.provenance import tracker

@tracker.track('handle_missing_data', include_args=False)
def handle_missing(df):
    """
    Handle missing values in the dataset.
    Replaces all blanks or '?' with NA.
    """
    df = df.copy()
    
    # Replace all blanks or '?' with NA
    df = df.replace(r'^\s*$', np.nan, regex=True)
    df = df.replace('?', np.nan)
    # Replaces 'Unknown' injected by make_dirty with NA as well
    df = df.replace('Unknown', np.nan)
    return df

@tracker.track('remove_missing_rows', include_args=False)
def missing_rows(df):
    """
    Removes rows missing 3 or more columns.
    """
    # We require at least (total_cols - 5) valid values to keep a row
    thresh = len(df.columns) - 5
    df = df.dropna(thresh=thresh)
    return df

@tracker.track('remove_missing_target', include_args=False)
def remove_missing_target(df):
    """
    Removes rows where the target variable ('income') is missing.
    """
    # Remove rows where target variable ('income') is missing
    if 'income' in df.columns:
        df = df.dropna(subset=['income'])
    return df
