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
        if nums.notna().sum() == filled:
            df[col] = nums
            changes.append(f"{col}: text -> number")
            continue

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            dates = pd.to_datetime(s, errors="coerce")
        if dates.notna().sum() == filled:
            df[col] = dates
            changes.append(f"{col}: text -> date")
    return df, changes


def drop_duplicates(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    before = len(df)
    df = df.drop_duplicates()
    return df, before - len(df)


def fix_options(series: pd.Series) -> list[str]:
    if pd.api.types.is_datetime64_any_dtype(series):
        return ["keep", "drop rows"]
    if pd.api.types.is_numeric_dtype(series):
        return ["keep", "drop rows", "fill median", "fill mean"]
    return ["keep", "drop rows", "fill most common", "fill 'Unknown'"]


def handle_missing(df: pd.DataFrame, strategies: dict) -> tuple[pd.DataFrame, list[str]]:
    df = df.copy()
    log = []
    for col, strategy in strategies.items():
        n = int(df[col].isna().sum())
        if n == 0 or strategy == "keep":
            continue
        if strategy == "drop rows":
            df = df[df[col].notna()]
        elif strategy == "fill median":
            df[col] = df[col].fillna(df[col].median())
        elif strategy == "fill mean":
            df[col] = df[col].fillna(df[col].mean())
        elif strategy == "fill most common":
            mode = df[col].mode()
            if mode.empty:
                continue
            df[col] = df[col].fillna(mode.iloc[0])
        elif strategy == "fill 'Unknown'":
            df[col] = df[col].fillna("Unknown")
        log.append(f"{col}: {strategy} ({n} missing)")
    return df, log