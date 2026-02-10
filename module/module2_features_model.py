import pandas as pd
import numpy as np

from tsfresh import extract_features
from tsfresh.utilities.dataframe_functions import impute
from prophet import Prophet

from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.cluster import DBSCAN

def run_modeling(df_clean: pd.DataFrame):
    """
    Module 2 Feature Extraction + Modeling:
    - TSFresh feature extraction
    - Prophet forecasting
    - Clustering (DBSCAN + PCA)
    Returns dict with:
      - features_df
      - prophet_forecasts
      - clustering_df
    """

    df = df_clean.copy()

    # Ensure Timestamp exists
    if "Timestamp" not in df.columns and "timestamp" in df.columns:
        df = df.rename(columns={"timestamp": "Timestamp"})

    df["Timestamp"] = pd.to_datetime(df["Timestamp"], errors="coerce")
    df = df.dropna(subset=["Timestamp"])

    # Person_ID support (single user)
    if "Person_ID" not in df.columns:
        df["Person_ID"] = "User_1"

    # Map metric names (safe)
    col_map = {}
    for col in df.columns:
        low = col.lower()
        if low in ["heart_rate", "heartrate", "hr"]:
            col_map[col] = "Heart_Rate"
        if low in ["sleep_duration", "sleep", "sleep_hours"]:
            col_map[col] = "Sleep_Duration"
        if low in ["daily_steps", "steps", "step_count"]:
            col_map[col] = "Daily_Steps"

    df = df.rename(columns=col_map)

    metrics = [m for m in ["Heart_Rate", "Sleep_Duration", "Daily_Steps"] if m in df.columns]
    if len(metrics) == 0:
        raise ValueError("No metric columns found (Heart_Rate / Sleep_Duration / Daily_Steps)")

    # Long format
    df_long = df.melt(
        id_vars=["Person_ID", "Timestamp"],
        value_vars=metrics,
        var_name="metric",
        value_name="value"
    )

    df_long["ts_id"] = df_long["Person_ID"].astype(str) + "_" + df_long["metric"]

    # TSFresh
    features = extract_features(
        df_long,
        column_id="ts_id",
        column_sort="Timestamp",
        column_value="value",
        n_jobs=0
    )
    impute(features)

    features["Person_ID"] = features.index.str.split("_").str[0]
    features["Metric"] = features.index.str.split("_").str[1]
    features_df = features.reset_index(drop=True)

    # Prophet forecasts
    prophet_forecasts = {}
    for m in metrics:
        temp = df[["Timestamp", m]].dropna()
        temp = temp.rename(columns={"Timestamp": "ds", m: "y"})

        #FIX (2 lines): Prophet requires unique ds timestamps
        temp = temp.sort_values("ds")
        temp = temp.drop_duplicates(subset=["ds"], keep="last")

        if len(temp) < 10:
            continue

        model = Prophet(daily_seasonality=True)
        model.fit(temp)
        forecast = model.predict(temp)
        prophet_forecasts[m] = forecast

    # Clustering (DBSCAN + PCA)
    feature_numeric = features_df.select_dtypes(include=[np.number])
    clustering_df = pd.DataFrame()

    if feature_numeric.shape[1] >= 2:
        scaler = StandardScaler()
        X = scaler.fit_transform(feature_numeric)

        pca = PCA(n_components=2)
        X_pca = pca.fit_transform(X)

        db = DBSCAN(eps=0.8, min_samples=2)
        labels = db.fit_predict(X_pca)

        clustering_df = pd.DataFrame({
            "pca1": X_pca[:, 0],
            "pca2": X_pca[:, 1],
            "cluster": labels
        })

    return {
        "features_df": features_df,
        "prophet_forecasts": prophet_forecasts,
        "clustering_df": clustering_df,
    }
