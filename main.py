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
    
    df = process_format_and_duplicates(df)

    tracker.export_to_json(filepath="data/provenance/provenance_metadata.json")

if __name__ == "__main__":
    run_pipeline()
