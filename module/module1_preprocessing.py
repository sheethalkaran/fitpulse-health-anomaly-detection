import pandas as pd
import numpy as np

def preprocess_data(df_raw: pd.DataFrame, resample_rule: str = "1H") -> pd.DataFrame:
    """
    Module 1 Preprocessing:
    - Detect timestamp column
    - Convert to datetime
    - Sort
    - Resample numeric cols
    - Fill missing
    """

    df = df_raw.copy()

    # Detect timestamp column
    timestamp_col = None
    for col in df.columns:
        if any(x in str(col).lower() for x in ["timestamp", "time", "date"]):
            timestamp_col = col
            break

    if timestamp_col is None:
        raise ValueError("No timestamp column found")

    # Standardize timestamp
    df = df.rename(columns={timestamp_col: "Timestamp"})
    df["Timestamp"] = pd.to_datetime(df["Timestamp"], errors="coerce")
    df = df.dropna(subset=["Timestamp"]).sort_values("Timestamp")
    df = df.set_index("Timestamp")

    # Resample numeric columns
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    if len(numeric_cols) == 0:
        raise ValueError("No numeric columns found in dataset")

    numeric_df = df[numeric_cols].resample(resample_rule).mean()
    numeric_df = numeric_df.replace([np.inf, -np.inf], np.nan)
    numeric_df = numeric_df.fillna(method="ffill").fillna(0)
    numeric_df = numeric_df.reset_index()

    return numeric_df
