import os
import requests
import pandas as pd

RAW_DATA_DIR = "data/raw"
SCHEMES = {
    "125497": "HDFC_Top_100_Direct",
    "119551": "SBI_Bluechip",
    "120503": "ICICI_Bluechip",
    "118632": "Nippon_Large_Cap",
    "119092": "Axis_Bluechip",
    "120841": "Kotak_Bluechip"
}

def fetch_and_save_nav(scheme_code, scheme_name):
    url = f"https://api.mfapi.in/mf/{scheme_code}"
    print(f"Fetching: {scheme_name} ({scheme_code})...")
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        meta = data.get("meta", {})
        nav_list = data.get("data", [])
        
        if not nav_list:
            print(f"⚠️ No data found for {scheme_name}")
            return
            
        df = pd.DataFrame(nav_list)
        df["scheme_code"] = scheme_code
        df["scheme_name"] = meta.get("scheme_name", scheme_name)
        
        os.makedirs(RAW_DATA_DIR, exist_ok=True)
        output_file = os.path.join(RAW_DATA_DIR, f"{scheme_name}_raw.csv")
        df.to_csv(output_file, index=False)
        print(f"✅ Saved {len(df)} rows to {output_file}")
        
    except Exception as e:
        print(f"❌ Error fetching {scheme_code}: {e}")

if __name__ == "__main__":
    for code, name in SCHEMES.items():
        fetch_and_save_nav(code, name)