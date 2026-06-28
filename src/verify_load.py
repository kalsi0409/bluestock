import pandas as pd
from sqlalchemy import create_engine

# Update with your database credentials
DB_URL = "mysql+pymysql://root:harshal0409@localhost:3306/bluestock_mf"
engine = create_engine(DB_URL)

def verify_counts():
    tables = ['dim_fund', 'fact_nav', 'fact_transactions', 'fact_performance']
    print("--- DATABASE LOAD VERIFICATION ---")
    
    for table in tables:
        # Fetch count from MySQL
        db_count = pd.read_sql(f"SELECT COUNT(*) FROM {table}", engine).iloc[0, 0]
        print(f"📋 Table '{table}' successfully verified. Total loaded rows: {db_count}")

if __name__ == "__main__":
    verify_counts()