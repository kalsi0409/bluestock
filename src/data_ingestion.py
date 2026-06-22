import os
import glob
import pandas as pd

def profile_and_load_datasets(data_folder="data/raw"):
    csv_files = glob.glob(os.path.join(data_folder, "*.csv"))
    datasets = {}
    
    if not csv_files:
        print(f"⚠️ No CSV assets found in '{data_folder}' yet.")
        return datasets

    print("=== STARTING DATASET PROFILING ===")
    for file_path in csv_files:
        file_name = os.path.basename(file_path)
        try:
            df = pd.read_csv(file_path, low_memory=False)
            datasets[file_name] = df
            print(f"\nAsset: {file_name} | Shape: {df.shape}")
            print(df.dtypes.to_string())
            print("-" * 40)
        except Exception as e:
            print(f"❌ Error reading {file_name}: {e}")
    return datasets

if __name__ == "__main__":
    profile_and_load_datasets()