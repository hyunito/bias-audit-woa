import os
import pandas as pd
from src.pipeline.remove_duplicates_fix_format import clean_and_format
from src.pipeline.handle_missing_data import handle_missing
from src.pipeline.outlier_remover import outlier_demographics
from src.utils.provenance import tracker

def run_pipeline():
    print("="*50)
    print("Starting Data Pipeline...")
    print("="*50)
    raw_data_path = 'data/raw/adult_data_dirty.csv'
    print(f"Loading raw data from {raw_data_path}...")
    df = pd.read_csv(raw_data_path)
    print(f"Initial shape: {df.shape}")
    
    print("\nStep 1: Removing duplicates and fixing format...")
    df = clean_and_format(df)
    print(f"Shape after step 1: {df.shape}")
    
    print("\nStep 2: Handling missing data...")
    df = handle_missing(df)
    print(f"Shape after step 2: {df.shape}")
    
    print("\nStep 3: Removing outliers...")
    df = outlier_demographics(df, cat_threshold=0.15)
    print(f"Shape after step 3: {df.shape}")
    
    print("\nSaving cleaned dataset...")
    os.makedirs('data/cleaned', exist_ok=True)
    output_path = 'data/cleaned/adult_data_cleaned.csv'
    df.to_csv(output_path, index=False)
    
    tracker.save_logs()
        
    print(f"\nPipeline execution completed successfully! Cleaned dataset saved to {output_path}")

if __name__ == "__main__":
    run_pipeline()
