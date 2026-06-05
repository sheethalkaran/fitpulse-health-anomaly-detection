import pandas as pd
import numpy as np

def preprocess_data(df_raw: pd.DataFrame, resample_rule: str = "1h") -> pd.DataFrame:
    """
    Module 1 Preprocessing:
    - Detect timestamp column
    - Convert to datetime
    - Sort
    - Resample numeric cols (hourly by default)
    - Preserve non-numeric categorical columns (Person_ID, Weight_Category, etc.)
      via per-hour first-value and forward-fill
    - Fill missing values
    """

    df = df_raw.copy()

    # Convert Person_ID to string to avoid resampling numeric IDs as floats
    if "Person_ID" in df.columns:
        df["Person_ID"] = df["Person_ID"].astype(str)

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

    # Identify non-numeric (categorical/string) columns to preserve
    non_numeric_cols = [
        c for c in df.columns
        if c != "Timestamp" and not pd.api.types.is_numeric_dtype(df[c])
    ]

    # For each hour bin, take the first-occurring value for categorical columns
    meta_df = None
    if non_numeric_cols:
        df["_hour_bin"] = df["Timestamp"].dt.floor(resample_rule)
        meta_df = df.groupby("_hour_bin")[non_numeric_cols].first().reset_index()
        meta_df = meta_df.rename(columns={"_hour_bin": "Timestamp"})

    # Resample numeric columns
    df_indexed = df.set_index("Timestamp")
    numeric_cols = df_indexed.select_dtypes(include=[np.number]).columns
    if len(numeric_cols) == 0:
        raise ValueError("No numeric columns found in dataset")

    numeric_df = df_indexed[numeric_cols].resample(resample_rule).mean()
    numeric_df = numeric_df.replace([np.inf, -np.inf], np.nan)
    numeric_df = numeric_df.ffill().fillna(0)
    numeric_df = numeric_df.reset_index()

    # Merge back categorical columns
    if meta_df is not None and len(non_numeric_cols) > 0:
        numeric_df = numeric_df.merge(meta_df, on="Timestamp", how="left")
        for col in non_numeric_cols:
            if col in numeric_df.columns:
                numeric_df[col] = numeric_df[col].ffill()

    return numeric_df
