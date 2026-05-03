import pandas as pd
from clean import clean_demographics
from clean import clean_df

# Outlier Detection method used:
    #age --> Interquartile Range (IQR); any age that falls below the lower bound or above the upper bound is mathematically flagged as an outlier.
    #sex, race, marital-status --> Removes categories appearing less than the others (e.g. only appears 1%).


def outlier_demographics(df, cat_threshold=0.01):
    df_cleaned = df.copy(clean_demographics)

    # --- 1. NUMERICAL OUTLIERS (age) ---
    def num_outlier(df):
        df_cleaned = df.copy(clean_demographics)
        if 'age' in df_cleaned.columns:
            Q1 = df_cleaned['age'].quantile(0.25)
            Q3 = df_cleaned['age'].quantile(0.75)
            IQR = Q3 - Q1
            
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            # Keep only rows within the IQR bounds
            df_cleaned = df_cleaned[(df_cleaned['age'] >= lower_bound) & (df_cleaned['age'] <= upper_bound)]
        return df_cleaned

    # --- 2. CATEGORICAL OUTLIERS (sex, race, marital-status) ---
    def cat_outlier(df):
        df_cleaned = df.copy(clean_demographics)
        categorical_cols = ['sex', 'race', 'marital-status']
        
        for col in categorical_cols:
            if col in df_cleaned.columns:
                # Calculate the percentage frequency of each category
                frequencies = df_cleaned[col].value_counts(normalize=True)
                
                # Identify labels that fall below the threshold
                rare_labels = frequencies[frequencies < cat_threshold].index.tolist()
                
                # Remove rows that contain those rare labels
                if rare_labels:
                    df_cleaned = df_cleaned[~df_cleaned[col].isin(rare_labels)]
        return df_cleaned

    df_cleaned = num_outlier(df)
    df_cleaned = cat_outlier(df)

    return df_cleaned


df = pd.DataFrame(clean_df)
      
cleaned_df = outlier_demographics(df, cat_threshold=0.15)    #value is 0.15/15% because sample data is small
    
print("\nCleaned Dataset (Outliers Removed):")
print(cleaned_df)