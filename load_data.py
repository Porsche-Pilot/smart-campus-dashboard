import pandas as pd
from sqlalchemy import create_engine
import os

engine = create_engine('sqlite:///smart_campus_intelligence.db')

def setup_database():
    # Make sure these exact file names are in your 'jaimahakal' folder
    files_to_store = {
        'attendance': 'attendance_24_weeks.csv',
        'wifi': 'semester_wifi_usage_24_weeks.csv',
        'electricity': 'semester_electricity_usage_24_weeks.csv',
        'mess': 'cleaned_mess_data.csv'  # This is the table it was missing!
    }

    print("--- Starting Data Ingestion into SQL ---")

    for table_name, file_path in files_to_store.items():
        if os.path.exists(file_path):
            print(f"Loading {file_path} into table '{table_name}'...")
            
            # Using chunksize so memory doesn't crash
            chunksize = 100000 
            first_chunk = True
            
            for chunk in pd.read_csv(file_path, chunksize=chunksize):
                mode = 'replace' if first_chunk else 'append'
                chunk.to_sql(table_name, engine, if_exists=mode, index=False)
                first_chunk = False
            
            print(f"✅ Successfully stored '{table_name}'")
        else:
            print(f"❌ ERROR: Cannot find {file_path}. Is it in the same folder?")

if __name__ == "__main__":
    setup_database()