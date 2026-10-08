import warnings

import pandas as pd


def infer_types(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    df = df.copy()
    changes = []
    for col in df.columns:
        if not pd.api.types.is_string_dtype(df[col]):
            continue
        s = df[col].astype("string").str.strip().replace("", pd.NA)
        filled = s.notna().sum()
        if filled == 0:
            continue

        nums = pd.to_numeric(s, errors="coerce")
        if nums.notna().sum() / filled > 0.95:
            df[col] = nums
            changes.append(f"{col}: text -> number")
            continue

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            dates = pd.to_datetime(s, errors="coerce")
        if dates.notna().sum() / filled > 0.95:
            df[col] = dates
            changes.append(f"{col}: text -> date")
    return df, changes


def drop_duplicates(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    before = len(df)
    df = df.drop_duplicates()
    return df, before - len(df)