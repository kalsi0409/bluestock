import pandas as pd
import numpy as np
from sqlalchemy import create_engine
import os
import glob

# Your local MySQL credentials
DB_URL = "mysql+pymysql://root:harshal0409@localhost:3306/bluestock_mf"
engine = create_engine(DB_URL)

def clean_and_load_dynamic_data():
    print("--- STARTING DAY 2 DYNAMIC INGESTION PIPELINE ---")
    
    raw_folder = "data/raw"
    file_pattern = os.path.join(raw_folder, "*_raw.csv")
    all_files = glob.glob(file_pattern)
    
    if not all_files:
        print(f"ERROR: No files ending in '_raw.csv' found in {raw_folder}!")
        return
        
    funds_list = []
    nav_history_list = []
    
    # Map of known scheme names to their AMFI codes just in case they aren't columns
    fallback_codes = {
        "hdfc_top_100_direct": "125497",
        "sbi_bluechip": "119551",
        "icici_bluechip": "120503",
        "nippon_large_cap": "118632",
        "axis_bluechip": "119092",
        "kotak_bluechip": "120841"
    }
    
    for file_path in all_files:
        filename = os.path.basename(file_path)
        clean_name = filename.replace('_raw.csv', '').lower()
        print(f"Reading and extraction processing: {filename}")
        
        df = pd.read_csv(file_path)
        
        # Standardize all column names to lowercase to prevent case issues
        df.columns = [str(col).strip().lower() for col in df.columns]
        
        # Check if basic 'nav' and 'date' columns exist
        if 'nav' not in df.columns or 'date' not in df.columns:
            print(f"WARNING: Skipping {filename} - missing mandatory 'nav' or 'date' columns. Found: {list(df.columns)}")
            continue
            
        # Determine the AMFI code dynamically
        detected_code = None
        if 'amfi_code' in df.columns:
            detected_code = str(df['amfi_code'].iloc[0]).strip()
        elif 'code' in df.columns:
            detected_code = str(df['code'].iloc[0]).strip()
        else:
            # Fallback to looking up by file name if column doesn't exist
            detected_code = fallback_codes.get(clean_name)
            
        if not detected_code or detected_code == 'nan':
            print(f"WARNING: Skipping {filename} - Could not resolve AMFI scheme code.")
            continue
            
        # Apply structured cleaning transformations
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        df['nav'] = pd.to_numeric(df['nav'], errors='coerce')
        df['amfi_code'] = detected_code
        
        df = df.dropna(subset=['date', 'nav'])
        df = df[df['nav'] > 0]
        
        if df.empty:
            print(f"WARNING: {filename} has no valid data rows after filtering.")
            continue
            
        # Extract scheme name presentation text
        display_name = filename.replace('_raw.csv', '').replace('_', ' ')
        
        funds_list.append({
            'amfi_code': detected_code,
            'scheme_name': display_name,
            'category': 'Equity - Large Cap', 
            'sub_category': 'Growth',
            'risk_grade': 'Very High'
        })
        
        # Keep only what our fact_nav table structures need
        nav_history_list.append(df[['amfi_code', 'date', 'nav']])
        
    if not nav_history_list:
        print("ERROR: No valid data objects were processed. Pipeline terminated.")
        return
        
    # 2. Upload to dim_fund
    df_dim_fund = pd.DataFrame(funds_list).drop_duplicates(subset=['amfi_code'])
    print(f"Uploading {len(df_dim_fund)} records to 'dim_fund' table...")
    df_dim_fund.to_sql('dim_fund', con=engine, if_exists='append', index=False)
    
    # 3. Aggregate, forward-fill, and upload to fact_nav
    df_fact_nav = pd.concat(nav_history_list, ignore_index=True)
    df_fact_nav.drop_duplicates(subset=['amfi_code', 'date'], inplace=True)
    
    df_fact_nav.sort_values(by=['amfi_code', 'date'], inplace=True)
    df_fact_nav = df_fact_nav.set_index('date').groupby('amfi_code').resample('D').ffill().reset_index()
    
    print(f"Uploading {len(df_fact_nav)} records into 'fact_nav'...")
    df_fact_nav.to_sql('fact_nav', con=engine, if_exists='append', index=False)
    
    print("SUCCESS: Dynamic database loading sequence successfully terminated!")

if __name__ == "__main__":
    clean_and_load_dynamic_data()