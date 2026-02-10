import streamlit as st
import pandas as pd

from module.module1_preprocessing import preprocess_data
from module.module2_features_model import run_modeling
from module.module3_anomaly_detection import detect_anomalies


@st.cache_data
def run_pipeline(df_raw: pd.DataFrame, resample_rule: str = "1H"):

    df0 = df_raw.copy()

    anomaly_cols = [
        "Heart_Rate_anomaly",
        "Daily_Steps_anomaly",
        "Sleep_Duration_anomaly"
    ]

    if all(col in df0.columns for col in anomaly_cols):
        # Ensure timestamp naming
        if "Timestamp" not in df0.columns and "timestamp" in df0.columns:
            df0 = df0.rename(columns={"timestamp": "Timestamp"})

        # Convert Timestamp properly
        if "Timestamp" in df0.columns:
            df0["Timestamp"] = pd.to_datetime(df0["Timestamp"], errors="coerce")
            df0 = df0.dropna(subset=["Timestamp"]).sort_values("Timestamp")

        #Module2 still can run on it (for insights)
        module2_out = run_modeling(df0)

        return df0, module2_out

    #Otherwise run full pipeline (raw file case)
    df_clean = preprocess_data(df0, resample_rule=resample_rule)

    # Safety: remove duplicate timestamps (Prophet fix)
    if "Timestamp" in df_clean.columns:
        df_clean["Timestamp"] = pd.to_datetime(df_clean["Timestamp"], errors="coerce")
        df_clean = df_clean.dropna(subset=["Timestamp"])
        df_clean = df_clean.sort_values("Timestamp")
        df_clean = df_clean.drop_duplicates(subset=["Timestamp"], keep="last")

    module2_out = run_modeling(df_clean)
    df_final = detect_anomalies(df_clean)

    return df_final, module2_out


#Alias (so app.py doesn't break)
run_full_pipeline = run_pipeline
