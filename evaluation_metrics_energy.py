"""
=============================================================================
  WIFI & ELECTRICITY USAGE PREDICTION — COMPLETE EVALUATION & METRICS REPORT
  Model : XGBoost (Gradient Boosted Trees)
  Data  : semester_wifi_usage_24_weeks.csv & semester_electricity_usage_24_weeks.csv
=============================================================================
"""

import pandas as pd
import numpy as np
import time
import warnings
import os

warnings.filterwarnings("ignore")

from xgboost import XGBRegressor
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import (
    mean_absolute_error, mean_squared_error, r2_score
)

# ──────────────────────────────────────────────────────────────
# CONFIG & HELPER FUNCTIONS (From Original Code)
# ──────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ELEC_FILE = os.path.join(BASE_DIR, "semester_electricity_usage_24_weeks.csv")
WIFI_FILE = os.path.join(BASE_DIR, "semester_wifi_usage_24_weeks.csv")

DAY_ORDER = {"Mon": 0, "Tue": 1, "Wed": 2, "Thu": 3, "Fri": 4, "Sat": 5, "Sun": 6}
PERIOD_MAP = {"Normal": 0, "Mid-Sem": 1, "Exam": 2, "Post-Exam": 3}

def mean_absolute_percentage_error(y_true, y_pred):
    # Avoid division by zero
    y_true_safe = np.where(y_true == 0, 1e-6, y_true)
    return np.mean(np.abs((y_true - y_pred) / y_true_safe)) * 100

def add_time_features(df):
    """Add cyclical time features and encodings."""
    df = df.copy()
    df["hour_sin"] = np.sin(2 * np.pi * df["Hour"] / 24)
    df["hour_cos"] = np.cos(2 * np.pi * df["Hour"] / 24)
    df["day_num"] = df["Day"].map(DAY_ORDER)
    df["day_sin"] = np.sin(2 * np.pi * df["day_num"] / 7)
    df["day_cos"] = np.cos(2 * np.pi * df["day_num"] / 7)
    df["period_encoded"] = df["Period_Type"].map(PERIOD_MAP)
    df["is_weekend"] = (df["day_num"] >= 5).astype(int)
    df["time_idx"] = (df["Week"] - 1) * 168 + df["day_num"] * 24 + df["Hour"]
    return df

def add_lag_features(df, target_col, group_cols=None):
    """Add lag features: same hour last week, 2 weeks ago, and rolling mean."""
    df = df.copy()
    df = df.sort_values(["Week", "day_num", "Hour"])

    if group_cols:
        group = df.groupby(group_cols)
    else:
        group = df

    if group_cols:
        df["lag_1w"] = group[target_col].shift(168)
        df["lag_2w"] = group[target_col].shift(336)
        df["lag_3w"] = group[target_col].shift(504)
        df["rolling_mean_4w"] = group[target_col].transform(
            lambda x: x.shift(168).rolling(window=4, min_periods=1).mean()
        )
    else:
        df["lag_1w"] = df[target_col].shift(168)
        df["lag_2w"] = df[target_col].shift(336)
        df["lag_3w"] = df[target_col].shift(504)
        df["rolling_mean_4w"] = (
            df[target_col].shift(168).rolling(window=4, min_periods=1).mean()
        )
    return df

# ──────────────────────────────────────────────────────────────
# EVALUATION WRAPPER FUNCTION
# ──────────────────────────────────────────────────────────────
def evaluate_time_series_model(df, target_col, feature_cols, model_params, name="MODEL"):
    print("=" * 70)
    print(f"  {name.upper()} — FULL EVALUATION")
    print("=" * 70)
    
    # Drop rows with NaN lags (first 3 weeks)
    train_df = df.dropna(subset=["lag_1w", "lag_2w", "lag_3w"]).copy()
    print(f"  ✅ Data prepared. Total usable samples: {len(train_df):,}")
    
    # ─── Temporal Split (First 17 Weeks vs Last 4 Weeks out of usable 21) ───
    # Since weeks 1-3 are dropped (NaN lags), train starts from Week 4.
    # Let's say Week 21-24 is test, Week <= 20 is train.
    test_weeks = [21, 22, 23, 24]
    
    train_split = train_df[~train_df["Week"].isin(test_weeks)].copy()
    test_split  = train_df[train_df["Week"].isin(test_weeks)].copy()
    
    X_train, y_train = train_split[feature_cols], train_split[target_col]
    X_test, y_test   = test_split[feature_cols], test_split[target_col]
    
    print(f"  📊 Temporal Split:")
    print(f"     Train : {len(X_train):,} rows (Weeks {train_split['Week'].min()}–{train_split['Week'].max()})")
    print(f"     Test  : {len(X_test):,} rows (Weeks {test_split['Week'].min()}–{test_split['Week'].max()})")
    print()
    
    # ─── Model Training ───
    print("  🧠 Training XGBoost Regressor …")
    t0 = time.time()
    
    model = XGBRegressor(**model_params)
    model.fit(X_train, y_train)
    
    y_pred = model.predict(X_test)
    y_pred = np.clip(y_pred, 0, None)  # Ensure no negative predictions
    
    train_time = time.time() - t0
    print(f"     ✅ Model trained in {train_time:.1f}s")
    print()
    
    # ─── Regression Metrics ───
    mae  = mean_absolute_error(y_test, y_pred)
    mse  = mean_squared_error(y_test, y_pred)
    rmse = np.sqrt(mse)
    r2   = r2_score(y_test, y_pred)
    mape = mean_absolute_percentage_error(y_test, y_pred)
    
    print("  📈 REGRESSION METRICS (Temporal Test Set):")
    print(f"     MAE   (Mean Absolute Error)     : {mae:.4f}")
    print(f"     MSE   (Mean Squared Error)      : {mse:.4f}")
    print(f"     RMSE  (Root Mean Squared Error) : {rmse:.4f}")
    print(f"     R²    (Coeff of Determination)  : {r2:.4f}")
    print(f"     MAPE  (Mean Abs Pct Error)      : {mape:.2f}%")
    print()
    
    # ─── TimeSeriesSplit Cross Validation ───
    print("  🔄 3-FOLD TIME SERIES CROSS-VALIDATION (on all usable data):")
    tscv = TimeSeriesSplit(n_splits=3)
    X_all, y_all = train_df[feature_cols], train_df[target_col]
    
    cv_rmse, cv_r2, cv_mae = [], [], []
    for fold, (t_idx, v_idx) in enumerate(tscv.split(X_all), 1):
        # We can use a faster evaluation for CV if needed, but XGBoost is fast
        cv_model = XGBRegressor(**model_params)
        cv_model.fit(X_all.iloc[t_idx], y_all.iloc[t_idx])
        y_cv_pred = cv_model.predict(X_all.iloc[v_idx])
        y_cv_pred = np.clip(y_cv_pred, 0, None)
        
        cv_rmse.append(np.sqrt(mean_squared_error(y_all.iloc[v_idx], y_cv_pred)))
        cv_r2.append(r2_score(y_all.iloc[v_idx], y_cv_pred))
        cv_mae.append(mean_absolute_error(y_all.iloc[v_idx], y_cv_pred))
        print(f"     Fold {fold}: RMSE={cv_rmse[-1]:.4f}, R²={cv_r2[-1]:.4f}, MAE={cv_mae[-1]:.4f}")
        
    print(f"     ---")
    print(f"     Avg RMSE: {np.mean(cv_rmse):.4f} ± {np.std(cv_rmse):.4f}")
    print(f"     Avg R²  : {np.mean(cv_r2):.4f} ± {np.std(cv_r2):.4f}")
    print(f"     Avg MAE : {np.mean(cv_mae):.4f} ± {np.std(cv_mae):.4f}")
    print()

    # ─── Feature Importances ───
    print("  🏆 FEATURE IMPORTANCE (Trained Model based on gain):")
    importances = model.feature_importances_
    feat_imp_df = pd.DataFrame({
        "Feature": feature_cols,
        "Importance": importances
    }).sort_values("Importance", ascending=False)
    
    for _, row in feat_imp_df.iterrows():
        bar = "█" * int(row["Importance"] * 50)
        print(f"     {row['Feature']:<16s}  {row['Importance']:.4f}  {bar}")
    print()
    
    # ─── Residual Analysis ───
    print("  📉 RESIDUAL ANALYSIS:")
    residuals = y_test.values - y_pred
    print(f"     Mean residual     : {residuals.mean():.4f} (ideal = 0)")
    print(f"     Std of residuals  : {residuals.std():.4f}")
    print(f"     Max overestimate  : {residuals.min():.4f} (most negative)")
    print(f"     Max underestimate : {residuals.max():.4f} (most positive)")
    print()
    
    summary = {
        "Target": [target_col],
        "MAE": [round(mae, 4)],
        "RMSE": [round(rmse, 4)],
        "R2": [round(r2, 4)],
        "MAPE (%)": [round(mape, 2)],
        "CV RMSE": [round(np.mean(cv_rmse), 4)],
        "CV R2": [round(np.mean(cv_r2), 4)]
    }
    
    return pd.DataFrame(summary), feat_imp_df

# ──────────────────────────────────────────────────────────────
# MAIN PIPELINE 
# ──────────────────────────────────────────────────────────────
def main():
    print("╔═══════════════════════════════════════════════════════════╗")
    print("║  USAGE MODEL EVALUATION PIPELINE                         ║")
    print("║  Algorithm: XGBoost (Gradient Boosted Trees)             ║")
    print("╚═══════════════════════════════════════════════════════════╝\n")

    summary_tables = []
    
    # ─── 1. Evaluate WiFi ───
    df_wifi = pd.read_csv(WIFI_FILE)
    df_wifi = add_time_features(df_wifi)
    df_wifi = df_wifi.sort_values("time_idx").reset_index(drop=True)
    df_wifi = add_lag_features(df_wifi, "Wifi_Usage_MB")
    
    wifi_features = [
        "Week", "Hour", "hour_sin", "hour_cos", "day_num", "day_sin", "day_cos",
        "period_encoded", "is_weekend", "lag_1w", "lag_2w", "lag_3w", "rolling_mean_4w"
    ]
    
    wifi_params = {
        "n_estimators": 300,
        "max_depth": 6,
        "learning_rate": 0.05,
        "subsample": 0.8,
        "colsample_bytree": 0.8,
        "random_state": 42,
        "verbosity": 0,
    }
    
    wifi_summary, wifi_feat_imp = evaluate_time_series_model(
        df=df_wifi, target_col="Wifi_Usage_MB", feature_cols=wifi_features, 
        model_params=wifi_params, name="Wifi Prediction Model"
    )
    summary_tables.append(wifi_summary)
    
    wifi_feat_imp.to_csv("usage_wifi_feature_importances.csv", index=False)
    
    # ─── 2. Evaluate Electricity ───
    df_elec = pd.read_csv(ELEC_FILE)
    df_elec = add_time_features(df_elec)
    df_elec = df_elec.sort_values(["Building", "time_idx"]).reset_index(drop=True)
    
    buildings = df_elec["Building"].unique()
    building_map = {b: i for i, b in enumerate(buildings)}
    df_elec["building_encoded"] = df_elec["Building"].map(building_map)
    df_elec = add_lag_features(df_elec, "Electricity_Usage_kWh", group_cols=["Building"])
    
    elec_features = [
        "Week", "Hour", "hour_sin", "hour_cos", "day_num", "day_sin", "day_cos",
        "period_encoded", "is_weekend", "building_encoded",
        "lag_1w", "lag_2w", "lag_3w", "rolling_mean_4w"
    ]
    
    elec_params = {
        "n_estimators": 500,
        "max_depth": 7,
        "learning_rate": 0.05,
        "subsample": 0.8,
        "colsample_bytree": 0.8,
        "reg_alpha": 0.1,
        "reg_lambda": 1.0,
        "random_state": 42,
        "verbosity": 0,
    }
    
    elec_summary, elec_feat_imp = evaluate_time_series_model(
        df=df_elec, target_col="Electricity_Usage_kWh", feature_cols=elec_features, 
        model_params=elec_params, name="Electricity Prediction Model"
    )
    summary_tables.append(elec_summary)
    elec_feat_imp.to_csv("usage_electricity_feature_importances.csv", index=False)
    
    # ─── 3. Save Summary ───
    final_summary = pd.concat(summary_tables, ignore_index=True)
    final_summary.to_csv("usage_evaluation_metrics_report.csv", index=False)
    
    print("=" * 70)
    print("  ✅  ALL DONE!")
    print("=" * 70)
    print()
    print("  Saved files:")
    print("    → usage_evaluation_metrics_report.csv           (metrics summary)")
    print("    → usage_wifi_feature_importances.csv            (WiFi feat importance)")
    print("    → usage_electricity_feature_importances.csv     (Elec feat importance)")
    print()

if __name__ == "__main__":
    main()