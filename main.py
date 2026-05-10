import os
import pandas as pd
from src.pipeline.remove_duplicates_fix_format import remove_duplicates
from src.pipeline.handle_missing_data import handle_missing
from src.pipeline.outlier_remover import outlier_demographics

def run_pipeline():

    print("Starting Data Pipeline...")

    raw_data_path = 'data/raw/adult_data_dirty.csv'
    print(f"Loading raw data from {raw_data_path}...")
    df = pd.read_csv(raw_data_path)
    print(f"Initial Shape: {df.shape}")
    print("\nStep 1: Removing duplicates and fixing format...")
    df = remove_duplicates(df)
    print(f"Shape after step 1: {df.shape}")
    
    print("\nStep 2: Handling missing data...")
    df = handle_missing(df)
    print(f"Shape after step 2: {df.shape}")
    
    print("\nStep 3: Removing outliers...")
    df = outlier_demographics(df)
    print(f"Shape after step 3: {df.shape}")
    
    print("\nSaving cleaned dataset...")
    os.makedirs('data/cleaned', exist_ok=True)
    output_path = 'data/cleaned/adult_data_cleaned.csv'
    df.to_csv(output_path, index=False)
        
    print(f"\nPipeline execution completed successfully! Cleaned dataset saved to {output_path}")

if __name__ == "__main__":
    run_pipeline()
