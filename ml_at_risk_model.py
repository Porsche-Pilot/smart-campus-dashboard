import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder

print("⏳ Loading data and engineering features...")

df = pd.read_csv("attendance_24_weeks.csv")
df = df.sort_values(by=["Student_ID","Course","Week"])

# Encode
le_day = LabelEncoder()
le_course = LabelEncoder()
le_time = LabelEncoder()

df["Day_enc"] = le_day.fit_transform(df["Day"])
df["Course_enc"] = le_course.fit_transform(df["Course"])
df["Time_enc"] = le_time.fit_transform(df["Time_Slot"])

# Features
df["past_avg"] = df.groupby(["Student_ID","Course"])["Attendance"].transform(lambda x: x.expanding().mean())
df["last5"] = df.groupby(["Student_ID","Course"])["Attendance"].transform(lambda x: x.rolling(5).mean())
df["last10"] = df.groupby(["Student_ID","Course"])["Attendance"].transform(lambda x: x.rolling(10).mean())

df.fillna(0, inplace=True)

# TRAIN REGRESSOR
features = ["past_avg","last5","last10","Week","Day_enc","Course_enc","Time_enc"]

X = df[features]
y = df["Attendance"]

print("🧠 Training AI Model (This takes just a moment)...")
model = RandomForestRegressor(n_estimators=50, n_jobs=-1, random_state=42)
model.fit(X, y)

# --- SUPER FAST VECTORIZED PREDICTION ---
print("⚡ Running batch predictions instantly...")
TOTAL_CLASSES = 140

# 1. Quickly calculate 'observed' and 'current_attended' for all groups at once
agg_df = df.groupby(["Student_ID", "Course"]).agg(
    observed=("Attendance", "size"),
    current_attended=("Attendance", "sum")
).reset_index()

# 2. Grab the very last row for every student-course combination instantly
last_rows_df = df.drop_duplicates(subset=["Student_ID", "Course"], keep="last")

# Merge them together so everything aligns perfectly
eval_df = pd.merge(agg_df, last_rows_df, on=["Student_ID", "Course"])

# 3. PREDICT ALL 35,000 AT ONCE (This is where the magic speed happens)
eval_df["pred_prob"] = model.predict(eval_df[features])

# 4. Instant Vectorized Math (No for-loops!)
eval_df["remaining"] = TOTAL_CLASSES - eval_df["observed"]
eval_df["future_attended"] = eval_df["pred_prob"] * eval_df["remaining"]
eval_df["final_attended"] = eval_df["current_attended"] + eval_df["future_attended"]

eval_df["Current_%"] = (eval_df["current_attended"] / eval_df["observed"]) * 100
eval_df["Predicted_Final_%"] = (eval_df["final_attended"] / TOTAL_CLASSES) * 100

# 5. Apply the Alert Status instantly across all rows
eval_df["Status"] = np.where(eval_df["Predicted_Final_%"] < 75.0, "⚠️ ALERT", "OK")

# 6. Format and Export
output_df = eval_df[["Student_ID", "Course", "Current_%", "Predicted_Final_%", "Status"]]
output_df = output_df.round({"Current_%": 2, "Predicted_Final_%": 2})

output_df.to_csv("FAST_predicted_attendance.csv", index=False)

print("✅ Super fast prediction done! Saved to 'FAST_predicted_attendance.csv'")