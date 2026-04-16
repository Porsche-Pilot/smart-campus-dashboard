# ==============================
# 1. IMPORT
# ==============================
import pandas as pd
import numpy as np

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score


# ==============================
# 2. LOAD DATA
# ==============================
df = pd.read_csv("cleaned_mess_data.csv")

df.columns = df.columns.str.strip()

# Rename
df.rename(columns={
    'Student_ID': 'student_id',
    'Meal': 'meal',
    'Date': 'date',
    'Scan_Time': 'time'
}, inplace=True)


# ==============================
# 3. CREATE DATETIME (FIXED)
# ==============================
df['datetime'] = pd.to_datetime(df['date'] + ' ' + df['time'], errors='coerce')

# Remove bad rows
df.dropna(subset=['datetime'], inplace=True)

df['day_of_week'] = df['datetime'].dt.dayofweek


# ==============================
# 4. FILTER VALID ENTRIES
# ==============================
# If Status column exists (like Present/Absent)
if 'Status' in df.columns:
    df = df[df['Status'] == 1]


# ==============================
# 5. AGGREGATE DEMAND
# ==============================
demand = df.groupby(['date','meal','day_of_week']).size().reset_index(name='students_count')

demand = demand.sort_values(by=['meal','date']).reset_index(drop=True)


# ==============================
# 6. FEATURE ENGINEERING
# ==============================
demand['prev_day'] = demand.groupby('meal')['students_count'].shift(1)
demand['prev2_day'] = demand.groupby('meal')['students_count'].shift(2)

demand['rolling_avg'] = demand.groupby('meal')['students_count'] \
    .rolling(3).mean().reset_index(0, drop=True)

demand['trend'] = demand['prev_day'] - demand['prev2_day']


# ==============================
# 7. TARGET
# ==============================
demand['target'] = demand.groupby('meal')['students_count'].shift(-1)

# 🔥 IMPORTANT: DO NOT DROP ALL DATA
demand = demand.dropna()

print("Remaining rows after preprocessing:", len(demand))


# ==============================
# 8. SAFETY CHECK
# ==============================
if len(demand) < 10:
    print("⚠️ Not enough data for ML. Using simple average instead.")
    
    avg = demand.groupby('meal')['students_count'].mean()
    print("\nAverage demand:\n", avg)
    
    exit()


# ==============================
# 9. TRAIN MODEL
# ==============================
X = demand[['students_count','prev_day','prev2_day','rolling_avg','trend','day_of_week']]
y = demand['target']

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

model = RandomForestRegressor(n_estimators=100)
model.fit(X_train, y_train)


# ==============================
# 10. EVALUATION
# ==============================
y_pred = model.predict(X_test)

print("\nEvaluation:\n")
print("MAE:", mean_absolute_error(y_test, y_pred))
print("R2 Score:", r2_score(y_test, y_pred))


# ==============================
# 11. OUTPUT & SAVE TO CSV
# ==============================
demand['predicted_students'] = np.round(model.predict(X)).astype(int) 

print("\nSample Predictions:\n")
print(demand[['date','meal','students_count','predicted_students']].head())

# --> UPDATED FILE NAME HERE <--
output_filename = "predicted_messhrs.csv"
demand.to_csv(output_filename, index=False)

print(f"\n✅ SUCCESS: Predictive procurement data saved to '{output_filename}'")