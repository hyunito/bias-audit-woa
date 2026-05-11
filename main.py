import os
import pandas as pd
from src.pipeline.tracker_setup import tracker
from src.pipeline.remove_duplicates_fix_format import process_format_and_duplicates

def run_pipeline():

    print("Starting Data Pipeline...")

    raw_data_path = 'data/raw/adult_data_dirty.csv'
    print(f"Loading raw data from {raw_data_path}...")
    df = pd.read_csv(raw_data_path)
    print(f"Initial Shape: {df.shape}")
    print("\nExecuting Pipeline Chain...")
    df = process_format_and_duplicates(df)

    
    print("\nSaving cleaned dataset...")
    os.makedirs('data/cleaned', exist_ok=True)
    output_path = 'data/cleaned/adult_data_cleaned.csv'
    df.to_csv(output_path, index=False)
    
    tracker.export_to_json(filepath="data/provenance/provenance_metadata.json")
        
    print(f"\nPipeline execution completed successfully! Cleaned dataset saved to {output_path}")

if __name__ == "__main__":
    run_pipeline()
