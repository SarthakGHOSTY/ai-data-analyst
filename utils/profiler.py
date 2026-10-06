import pandas as pd


def summary_metrics(df: pd.DataFrame) -> dict:
    return {
        "Rows": df.shape[0],
        "Columns": df.shape[1],
        "Missing values": int(df.isna().sum().sum()),
        "Duplicate rows": int(df.duplicated().sum()),
    }


def column_profile(df: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame({
        "dtype": df.dtypes.astype(str),
        "missing": df.isna().sum(),
        "missing_%": (df.isna().mean() * 100).round(1),
        "unique": df.nunique(),
    })