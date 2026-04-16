"""
=============================================================================
  ATTENDANCE PREDICTION MODEL — COMPLETE EVALUATION & METRICS REPORT
  Model : Random Forest Regressor
  Data  : attendance_24_weeks.csv  (24 weeks × students × courses)
=============================================================================
"""

import pandas as pd
import numpy as np
import time
import warnings
warnings.filterwarnings("ignore")

from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import (
    train_test_split, cross_val_score, KFold
)
from sklearn.metrics import (
    mean_absolute_error, mean_squared_error, r2_score,
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, classification_report
)

# ─────────────────────────────────────────────────────────────
# 1.  DATA LOADING & FEATURE ENGINEERING
# ─────────────────────────────────────────────────────────────
print("=" * 70)
print("  ATTENDANCE PREDICTION MODEL — FULL EVALUATION")
print("=" * 70)
print()

t0 = time.time()
print("⏳ [1/7] Loading data and engineering features …")

df = pd.read_csv("attendance_24_weeks.csv")
df = df.sort_values(by=["Student_ID", "Course", "Week"]).reset_index(drop=True)

# --- Label encoding ---
le_day    = LabelEncoder()
le_course = LabelEncoder()
le_time   = LabelEncoder()

df["Day_enc"]    = le_day.fit_transform(df["Day"])
df["Course_enc"] = le_course.fit_transform(df["Course"])
df["Time_enc"]   = le_time.fit_transform(df["Time_Slot"])

# --- Rolling / expanding features ---
df["past_avg"] = (
    df.groupby(["Student_ID", "Course"])["Attendance"]
      .transform(lambda x: x.expanding().mean())
)
df["last5"] = (
    df.groupby(["Student_ID", "Course"])["Attendance"]
      .transform(lambda x: x.rolling(5).mean())
)
df["last10"] = (
    df.groupby(["Student_ID", "Course"])["Attendance"]
      .transform(lambda x: x.rolling(10).mean())
)
df.fillna(0, inplace=True)

features = ["past_avg", "last5", "last10", "Week", "Day_enc", "Course_enc", "Time_enc"]

print(f"   ✅ Loaded {len(df):,} rows  |  {df['Student_ID'].nunique()} students  |  "
      f"{df['Course'].nunique()} courses  |  {df['Week'].nunique()} weeks")
print(f"   Features used: {features}")
print()

# ─────────────────────────────────────────────────────────────
# 2.  TRAIN / TEST SPLIT  (Temporal: first 20 weeks → train, last 4 → test)
# ─────────────────────────────────────────────────────────────
print("📊 [2/7] Splitting data (temporal split: Weeks 1-20 train, 21-24 test) …")

train_df = df[df["Week"] <= 20].copy()
test_df  = df[df["Week"] >  20].copy()

X_train = train_df[features]
y_train = train_df["Attendance"]
X_test  = test_df[features]
y_test  = test_df["Attendance"]

print(f"   Train set: {len(train_df):,} rows  (Weeks 1–20)")
print(f"   Test  set: {len(test_df):,} rows   (Weeks 21–24)")
print()

# ─────────────────────────────────────────────────────────────
# 3.  MODEL TRAINING
# ─────────────────────────────────────────────────────────────
print("🧠 [3/7] Training Random Forest Regressor …")

model = RandomForestRegressor(
    n_estimators=50,
    n_jobs=-1,
    random_state=42
)
model.fit(X_train, y_train)

y_pred = model.predict(X_test)
# Clip predictions to [0, 1] since attendance is binary
y_pred_clipped = np.clip(y_pred, 0, 1)

train_time = time.time() - t0
print(f"   ✅ Model trained in {train_time:.1f}s")
print()

# ─────────────────────────────────────────────────────────────
# 4.  REGRESSION METRICS  (raw probability-like prediction)
# ─────────────────────────────────────────────────────────────
print("=" * 70)
print("  📈  REGRESSION METRICS  (predicting attendance probability)")
print("=" * 70)

mae  = mean_absolute_error(y_test, y_pred_clipped)
mse  = mean_squared_error(y_test, y_pred_clipped)
rmse = np.sqrt(mse)
r2   = r2_score(y_test, y_pred_clipped)

# Mean Absolute Percentage Error (avoid /0 with a floor)
mape = np.mean(np.abs((y_test - y_pred_clipped) / np.where(y_test == 0, 1, y_test))) * 100

print(f"   MAE  (Mean Absolute Error)     : {mae:.4f}")
print(f"   MSE  (Mean Squared Error)      : {mse:.4f}")
print(f"   RMSE (Root Mean Squared Error)  : {rmse:.4f}")
print(f"   R²   (Coefficient of Determination) : {r2:.4f}")
print(f"   MAPE (Mean Abs % Error)         : {mape:.2f}%")
print()

# Interpretation helper
if r2 >= 0.8:
    print(f"   💡 Interpretation: R² = {r2:.4f}  →  Model explains {r2*100:.1f}% of variance (EXCELLENT)")
elif r2 >= 0.6:
    print(f"   💡 Interpretation: R² = {r2:.4f}  →  Model explains {r2*100:.1f}% of variance (GOOD)")
elif r2 >= 0.4:
    print(f"   💡 Interpretation: R² = {r2:.4f}  →  Model explains {r2*100:.1f}% of variance (MODERATE)")
else:
    print(f"   💡 Interpretation: R² = {r2:.4f}  →  Model explains {r2*100:.1f}% of variance (POOR)")
print()

# ─────────────────────────────────────────────────────────────
# 5.  CLASSIFICATION METRICS  (threshold = 0.5 → Present/Absent)
# ─────────────────────────────────────────────────────────────
print("=" * 70)
print("  🎯  CLASSIFICATION METRICS  (threshold = 0.5 → Present / Absent)")
print("=" * 70)

y_pred_binary = (y_pred_clipped >= 0.5).astype(int)

acc  = accuracy_score(y_test, y_pred_binary)
prec = precision_score(y_test, y_pred_binary, zero_division=0)
rec  = recall_score(y_test, y_pred_binary, zero_division=0)
f1   = f1_score(y_test, y_pred_binary, zero_division=0)

print(f"   Accuracy  : {acc:.4f}  ({acc*100:.2f}%)")
print(f"   Precision : {prec:.4f}")
print(f"   Recall    : {rec:.4f}")
print(f"   F1 Score  : {f1:.4f}")
print()

# Confusion Matrix
cm = confusion_matrix(y_test, y_pred_binary)
tn, fp, fn, tp = cm.ravel()
print("   Confusion Matrix:")
print(f"                    Predicted Absent    Predicted Present")
print(f"   Actual Absent      {tn:>10,}           {fp:>10,}")
print(f"   Actual Present     {fn:>10,}           {tp:>10,}")
print()
print(f"   True Negatives  (TN) : {tn:,}")
print(f"   False Positives (FP) : {fp:,}")
print(f"   False Negatives (FN) : {fn:,}")
print(f"   True Positives  (TP) : {tp:,}")
print()

# Specificity & Sensitivity
specificity = tn / (tn + fp) if (tn + fp) > 0 else 0
sensitivity = rec  # same as recall
print(f"   Sensitivity (Recall / TPR) : {sensitivity:.4f}")
print(f"   Specificity (TNR)          : {specificity:.4f}")
print()

# Full classification report
print("   Detailed Classification Report:")
print(classification_report(y_test, y_pred_binary,
                            target_names=["Absent (0)", "Present (1)"],
                            digits=4))
print()

# ─────────────────────────────────────────────────────────────
# 6.  CROSS-VALIDATION  (5-Fold on full data)
# ─────────────────────────────────────────────────────────────
print("=" * 70)
print("  🔄  5-FOLD CROSS-VALIDATION  (on full dataset)")
print("=" * 70)

# Use a sample if dataset is very large to keep CV fast
MAX_CV_ROWS = 500_000
if len(df) > MAX_CV_ROWS:
    print(f"   (Sampling {MAX_CV_ROWS:,} rows from {len(df):,} for faster CV …)")
    cv_df = df.sample(n=MAX_CV_ROWS, random_state=42)
else:
    cv_df = df

X_cv = cv_df[features]
y_cv = cv_df["Attendance"]

kfold = KFold(n_splits=5, shuffle=True, random_state=42)

cv_r2   = cross_val_score(model, X_cv, y_cv, cv=kfold, scoring="r2",                   n_jobs=-1)
cv_mae  = cross_val_score(model, X_cv, y_cv, cv=kfold, scoring="neg_mean_absolute_error", n_jobs=-1)
cv_rmse = cross_val_score(model, X_cv, y_cv, cv=kfold, scoring="neg_root_mean_squared_error", n_jobs=-1)

print(f"   R²   per fold : {np.round(cv_r2, 4)}")
print(f"   R²   mean±std : {cv_r2.mean():.4f} ± {cv_r2.std():.4f}")
print()
print(f"   MAE  per fold : {np.round(-cv_mae, 4)}")
print(f"   MAE  mean±std : {(-cv_mae).mean():.4f} ± {(-cv_mae).std():.4f}")
print()
print(f"   RMSE per fold : {np.round(-cv_rmse, 4)}")
print(f"   RMSE mean±std : {(-cv_rmse).mean():.4f} ± {(-cv_rmse).std():.4f}")
print()

# ─────────────────────────────────────────────────────────────
# 7.  FEATURE IMPORTANCE
# ─────────────────────────────────────────────────────────────
print("=" * 70)
print("  🏆  FEATURE IMPORTANCE  (Random Forest — Gini Impurity)")
print("=" * 70)

importances = model.feature_importances_
feat_imp = pd.DataFrame({
    "Feature":    features,
    "Importance": importances
}).sort_values("Importance", ascending=False)

for _, row in feat_imp.iterrows():
    bar = "█" * int(row["Importance"] * 50)
    print(f"   {row['Feature']:<12s}  {row['Importance']:.4f}  {bar}")
print()

# ─────────────────────────────────────────────────────────────
# 8.  RESIDUAL ANALYSIS
# ─────────────────────────────────────────────────────────────
print("=" * 70)
print("  📉  RESIDUAL ANALYSIS")
print("=" * 70)

residuals = y_test.values - y_pred_clipped
print(f"   Mean residual        : {residuals.mean():.6f}  (ideal = 0)")
print(f"   Std of residuals     : {residuals.std():.6f}")
print(f"   Median residual      : {np.median(residuals):.6f}")
print(f"   Max overestimate     : {residuals.min():.6f}  (most negative residual)")
print(f"   Max underestimate    : {residuals.max():.6f}  (most positive residual)")
print()

# ─────────────────────────────────────────────────────────────
# 9.  PER-COURSE EVALUATION
# ─────────────────────────────────────────────────────────────
print("=" * 70)
print("  📚  PER-COURSE BREAKDOWN")
print("=" * 70)

test_df = test_df.copy()
test_df["y_pred"] = y_pred_clipped
test_df["y_pred_binary"] = y_pred_binary

course_metrics = []
for course in sorted(test_df["Course"].unique()):
    mask = test_df["Course"] == course
    yt = test_df.loc[mask, "Attendance"]
    yp = test_df.loc[mask, "y_pred"]
    ypb = test_df.loc[mask, "y_pred_binary"]

    c_mae  = mean_absolute_error(yt, yp)
    c_rmse = np.sqrt(mean_squared_error(yt, yp))
    c_r2   = r2_score(yt, yp) if len(yt) > 1 else 0
    c_acc  = accuracy_score(yt, ypb)
    c_f1   = f1_score(yt, ypb, zero_division=0)

    course_metrics.append({
        "Course": course, "MAE": round(c_mae, 4), "RMSE": round(c_rmse, 4),
        "R2": round(c_r2, 4), "Accuracy": round(c_acc, 4), "F1": round(c_f1, 4),
        "Samples": len(yt)
    })

course_df = pd.DataFrame(course_metrics)
print(course_df.to_string(index=False))
print()

# ─────────────────────────────────────────────────────────────
# 10.  ALERT-LEVEL EVALUATION  (< 75% attendance prediction)
# ─────────────────────────────────────────────────────────────
print("=" * 70)
print("  ⚠️   ALERT THRESHOLD ANALYSIS  (Predicted Final % < 75)")
print("=" * 70)

TOTAL_CLASSES = 140

# Build the final prediction table (same logic as original script)
agg_df = df.groupby(["Student_ID", "Course"]).agg(
    observed=("Attendance", "size"),
    current_attended=("Attendance", "sum")
).reset_index()

last_rows = df.drop_duplicates(subset=["Student_ID", "Course"], keep="last")
eval_df = pd.merge(agg_df, last_rows, on=["Student_ID", "Course"])

eval_df["pred_prob"]       = model.predict(eval_df[features])
eval_df["remaining"]       = TOTAL_CLASSES - eval_df["observed"]
eval_df["future_attended"] = eval_df["pred_prob"] * eval_df["remaining"]
eval_df["final_attended"]  = eval_df["current_attended"] + eval_df["future_attended"]
eval_df["Current_%"]       = (eval_df["current_attended"] / eval_df["observed"]) * 100
eval_df["Predicted_Final_%"]= (eval_df["final_attended"] / TOTAL_CLASSES) * 100
eval_df["Status"]          = np.where(eval_df["Predicted_Final_%"] < 75.0, "ALERT", "OK")

total_pairs = len(eval_df)
alert_count = (eval_df["Status"] == "ALERT").sum()
ok_count    = (eval_df["Status"] == "OK").sum()

print(f"   Total student-course combinations : {total_pairs:,}")
print(f"   ⚠️  ALERT  (< 75% predicted)       : {alert_count:,}  ({alert_count/total_pairs*100:.1f}%)")
print(f"   ✅ OK      (≥ 75% predicted)       : {ok_count:,}    ({ok_count/total_pairs*100:.1f}%)")
print()
print(f"   Avg Current Attendance %     : {eval_df['Current_%'].mean():.2f}%")
print(f"   Avg Predicted Final %        : {eval_df['Predicted_Final_%'].mean():.2f}%")
print(f"   Std of Predicted Final %     : {eval_df['Predicted_Final_%'].std():.2f}%")
print()

# --- Alert distribution by course ---
alert_by_course = eval_df.groupby("Course")["Status"].apply(
    lambda x: (x == "ALERT").sum()
).reset_index(name="Alert_Count")
alert_by_course["Total"] = eval_df.groupby("Course")["Status"].count().values
alert_by_course["Alert_%"] = (alert_by_course["Alert_Count"] / alert_by_course["Total"] * 100).round(1)

print("   Alerts by Course:")
print(alert_by_course.to_string(index=False))
print()

# ─────────────────────────────────────────────────────────────
# 11.  MODEL HYPERPARAMETERS  (for report completeness)
# ─────────────────────────────────────────────────────────────
print("=" * 70)
print("  ⚙️   MODEL CONFIGURATION & HYPERPARAMETERS")
print("=" * 70)
print(f"   Algorithm             : Random Forest Regressor")
print(f"   n_estimators          : {model.n_estimators}")
print(f"   max_depth             : {model.max_depth}  (None = unlimited)")
print(f"   min_samples_split     : {model.min_samples_split}")
print(f"   min_samples_leaf      : {model.min_samples_leaf}")
print(f"   max_features          : {model.max_features}")
print(f"   random_state          : {model.random_state}")
print(f"   n_jobs                : {model.n_jobs}")
print(f"   Number of trees       : {len(model.estimators_)}")
print(f"   Total training time   : {train_time:.1f}s")
print()

# ─────────────────────────────────────────────────────────────
# 12.  LOGIC EXPLANATION  (printed summary)
# ─────────────────────────────────────────────────────────────
print("=" * 70)
print("  📝  MODEL LOGIC & APPROACH EXPLAINED")
print("=" * 70)
print("""
   PROBLEM:
   Predict whether a student will maintain ≥ 75% attendance by semester end,
   given 24 weeks of historical attendance data across multiple courses.

   APPROACH:
   1. Feature Engineering — For every student-course-week record, we compute:
        • past_avg  : Expanding (cumulative) mean of all past attendance (0/1)
        • last5     : Rolling mean over the last 5 class records
        • last10    : Rolling mean over the last 10 class records
        • Week      : Week number (temporal signal)
        • Day_enc   : Day-of-week encoded via LabelEncoder
        • Course_enc: Course label encoded
        • Time_enc  : Time slot encoded

   2. Model — Random Forest Regressor with 50 trees.
        • Each tree independently learns attendance probabilities.
        • The ensemble averages trees → smooth probability output in [0, 1].
        • This is preferred over a classifier here because the output
          probability is directly used to extrapolate future attendance %.

   3. Prediction Logic:
        • For each (Student, Course) pair:
            a)  Compute how many classes observed so far  (observed)
            b)  Compute how many the student attended      (current_attended)
            c)  Predict probability of attending each remaining class
            d)  future_attended = pred_prob × remaining_classes
            e)  final_attended  = current_attended + future_attended
            f)  Predicted_Final_% = final_attended / TOTAL_CLASSES × 100
        • If Predicted_Final_% < 75 → ⚠️ ALERT (student at risk)

   4. Why Random Forest?
        • Works well with tabular data
        • Handles non-linear feature interactions automatically
        • Robust to outliers and noise
        • Provides feature importance for interpretability
        • No need for feature scaling / normalization

   5. Limitations:
        • Rolling features (last5/last10) have NaN for early weeks → filled with 0
        • Assumes remaining classes follow the same pattern as recent history
        • Does not account for external factors (exams, holidays, etc.)
        • A classifier (e.g., XGBoost) could yield sharper binary decisions
""")

# ─────────────────────────────────────────────────────────────
# 13.  SAVE SUMMARY REPORT
# ─────────────────────────────────────────────────────────────
summary = {
    "Metric": [
        "MAE", "MSE", "RMSE", "R²", "MAPE (%)",
        "Accuracy", "Precision", "Recall", "F1 Score",
        "Specificity", "Sensitivity",
        "CV R² (mean)", "CV R² (std)",
        "CV MAE (mean)", "CV RMSE (mean)",
        "True Negatives", "False Positives", "False Negatives", "True Positives",
        "Alert Count", "OK Count", "Total Pairs"
    ],
    "Value": [
        round(mae, 4), round(mse, 4), round(rmse, 4), round(r2, 4), round(mape, 2),
        round(acc, 4), round(prec, 4), round(rec, 4), round(f1, 4),
        round(specificity, 4), round(sensitivity, 4),
        round(cv_r2.mean(), 4), round(cv_r2.std(), 4),
        round((-cv_mae).mean(), 4), round((-cv_rmse).mean(), 4),
        tn, fp, fn, tp,
        alert_count, ok_count, total_pairs
    ]
}

summary_df = pd.DataFrame(summary)
summary_df.to_csv("evaluation_metrics_report.csv", index=False)

# Also save feature importances
feat_imp.to_csv("feature_importances.csv", index=False)

# Also save per-course metrics
course_df.to_csv("per_course_metrics.csv", index=False)

elapsed = time.time() - t0
print("=" * 70)
print(f"  ✅  ALL DONE!  Total elapsed: {elapsed:.1f}s")
print("=" * 70)
print()
print("  Saved files:")
print("    → evaluation_metrics_report.csv   (all metrics in one table)")
print("    → feature_importances.csv         (feature importance scores)")
print("    → per_course_metrics.csv          (per-course breakdown)")
print("    → FAST_predicted_attendance.csv   (original predictions)")
print()