import os
import sys
import pandas as pd
from src.utils.provenance import tracker

@tracker.track('num_outlier_removal', include_args=False)
def num_outlier(df):
    """Remove age outliers using Interquartile Range (IQR) method."""
    df_cleaned = df.copy()
    if 'age' in df_cleaned.columns:
        Q1 = df_cleaned['age'].quantile(0.25)
        Q3 = df_cleaned['age'].quantile(0.75)
        IQR = Q3 - Q1
        
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        
        # Identify outliers
        outliers = df_cleaned[(df_cleaned['age'] < lower_bound) | (df_cleaned['age'] > upper_bound)]
        for idx in outliers.index:
            tracker.log_row_change('num_outlier_removal', idx, 'age', df_cleaned.loc[idx, 'age'], 'removed')
        
        # Keep only rows within the IQR bounds
        df_cleaned = df_cleaned[(df_cleaned['age'] >= lower_bound) & (df_cleaned['age'] <= upper_bound)]
    return df_cleaned


@tracker.track('cat_outlier_removal', include_args=False)
def cat_outlier(df, cat_threshold=0.01):
    """Remove categorical outliers based on frequency threshold."""
    df_cleaned = df.copy()
    categorical_cols = ['sex', 'race', 'marital-status']
    
    for col in categorical_cols:
        if col in df_cleaned.columns:
            # Calculate the percentage frequency of each category
            frequencies = df_cleaned[col].value_counts(normalize=True)
            
            # Identify labels that fall below the threshold
            rare_labels = frequencies[frequencies < cat_threshold].index.tolist()
            
            # Identify rows to remove
            if rare_labels:
                to_remove = df_cleaned[df_cleaned[col].isin(rare_labels)]
                for idx in to_remove.index:
                    tracker.log_row_change('cat_outlier_removal', idx, col, df_cleaned.loc[idx, col], 'removed')
                
                # Remove rows that contain those rare labels
                df_cleaned = df_cleaned[~df_cleaned[col].isin(rare_labels)]
    return df_cleaned


@tracker.track('outlier_demographics', include_args=False)
def outlier_demographics(df, cat_threshold=0.01):
    """Remove both numerical and categorical outliers from demographics data."""
    df_cleaned = num_outlier(df)
    df_cleaned = cat_outlier(df_cleaned, cat_threshold)
    return df_cleaned


def run_outlier_removal():
    # Load the cleaned dataset from transformation.py
    df = pd.read_csv('data/cleaned/adult_data_cleaned.csv')
          
    cleaned_df = outlier_demographics(df, cat_threshold=0.15)    #value is 0.15/15% because sample data is small
        
    print("\nCleaned Dataset (Outliers Removed):")
    print(cleaned_df)

    # Save the final dataset
    os.makedirs('data/cleaned', exist_ok=True)
    cleaned_df.to_csv('data/cleaned/adult_data_final.csv', index=False)

    tracker.save_logs()
    
    return cleaned_df

if __name__ == "__main__":
    run_outlier_removal()