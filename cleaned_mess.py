import pandas as pd
import sqlite3
import os

print("Loading raw dataset...")
df = pd.read_csv("mess_dataset_matrix.csv")

# 1. Melt the dataframe from wide to long format
id_vars = ["Student_ID", "Meal"]
date_cols = [col for col in df.columns if col not in id_vars]

df_long = pd.melt(df, id_vars=id_vars, value_vars=date_cols, var_name="Date", value_name="Raw_Value")

# 2. Extract Status and Scan_Time
# '1_HH:MM' means Present (1). '0' means Absent (0).
df_long['Status'] = df_long['Raw_Value'].apply(lambda x: 1 if str(x).startswith('1') else 0)
df_long['Scan_Time'] = df_long['Raw_Value'].apply(lambda x: str(x).split('_')[1] if str(x).startswith('1_') else None)

# Drop the raw, noisy column
df_long.drop(columns=['Raw_Value'], inplace=True)

# 3. Clean up and format data types
df_long['Date'] = pd.to_datetime(df_long['Date'])
df_long['Student_ID'] = df_long['Student_ID'].astype(str)

print("Cleaning complete. Here is a preview:")
print(df_long.head())

# 4. Save to CSV for Business Intelligence tools (Power BI / Tableau)
cleaned_csv_path = "cleaned_mess_data.csv"
df_long.to_csv(cleaned_csv_path, index=False)
print(f"\nSaved CSV to: {cleaned_csv_path}")

# 5. Structure and store efficiently using SQL (SQLite)
db_path = "campus_mess.db"

# Remove existing DB if you are re-running the script
if os.path.exists(db_path):
    os.remove(db_path)

conn = sqlite3.connect(db_path)
df_long.to_sql("mess_logs", conn, if_exists="replace", index=False)
conn.close()
print(f"Saved SQLite database to: {db_path}")