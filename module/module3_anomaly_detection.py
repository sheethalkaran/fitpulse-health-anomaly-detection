import pandas as pd
import numpy as np

def detect_anomalies(df_input: pd.DataFrame) -> pd.DataFrame:
    df = df_input.copy()

    # Ensure Timestamp
    if "Timestamp" not in df.columns and "timestamp" in df.columns:
        df = df.rename(columns={"timestamp": "Timestamp"})

    df["Timestamp"] = pd.to_datetime(df["Timestamp"], errors="coerce")
    df = df.dropna(subset=["Timestamp"])
    df = df.sort_values("Timestamp").reset_index(drop=True)

    # Ensure Person_ID
    if "Person_ID" not in df.columns:
        df["Person_ID"] = "User_1"

    features = ["Heart_Rate", "Daily_Steps", "Sleep_Duration"]
    features = [c for c in features if c in df.columns]

    #Baseline + Residual Anomaly
    for col in features:
        df[f"{col}_baseline"] = (
            df.groupby("Person_ID")[col]
              .rolling(window=24, min_periods=1)
              .mean()
              .reset_index(level=0, drop=True)
        )

        df[f"{col}_residual"] = df[col] - df[f"{col}_baseline"]

        std = (
            df.groupby("Person_ID")[f"{col}_residual"]
              .transform("std")
              .replace(0, np.nan)
        )

        df[f"{col}_residual_anomaly"] = np.abs(df[f"{col}_residual"]) > (3 * std)

    #Rule Based
    if "Heart_Rate" in df.columns:
        df["Heart_Rate_rule_anomaly"] = (df["Heart_Rate"] < 50) | (df["Heart_Rate"] > 100)
    else:
        df["Heart_Rate_rule_anomaly"] = False

    if "Daily_Steps" in df.columns:
        df["Daily_Steps_rule_anomaly"] = (df["Daily_Steps"] < 2000) | (df["Daily_Steps"] > 15000)
    else:
        df["Daily_Steps_rule_anomaly"] = False

    if "Sleep_Duration" in df.columns:
        df["Sleep_Duration_rule_anomaly"] = (df["Sleep_Duration"] < 5) | (df["Sleep_Duration"] > 9)
    else:
        df["Sleep_Duration_rule_anomaly"] = False

    #Final anomaly flags
    if "Heart_Rate_residual_anomaly" in df.columns:
        df["Heart_Rate_anomaly"] = df["Heart_Rate_residual_anomaly"] | df["Heart_Rate_rule_anomaly"]
    else:
        df["Heart_Rate_anomaly"] = df["Heart_Rate_rule_anomaly"]

    if "Daily_Steps_residual_anomaly" in df.columns:
        df["Daily_Steps_anomaly"] = df["Daily_Steps_residual_anomaly"] | df["Daily_Steps_rule_anomaly"]
    else:
        df["Daily_Steps_anomaly"] = df["Daily_Steps_rule_anomaly"]

    if "Sleep_Duration_residual_anomaly" in df.columns:
        df["Sleep_Duration_anomaly"] = df["Sleep_Duration_residual_anomaly"] | df["Sleep_Duration_rule_anomaly"]
    else:
        df["Sleep_Duration_anomaly"] = df["Sleep_Duration_rule_anomaly"]

    # optional combined anomaly
    df["anomaly"] = (
        df["Heart_Rate_anomaly"].astype(int)
        + df["Daily_Steps_anomaly"].astype(int)
        + df["Sleep_Duration_anomaly"].astype(int)
    )
    df["anomaly"] = (df["anomaly"] > 0).astype(int)

    return df
