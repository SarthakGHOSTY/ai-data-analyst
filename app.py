import streamlit as st

from utils.cleaner import (
    detect_outliers,
    drop_duplicates,
    fix_options,
    handle_missing,
    handle_outliers,
    infer_types,
)
from utils.loader import load_data
from utils.profiler import column_profile, summary_metrics

st.title("AI-Powered Data Analyst")

file = st.file_uploader("Upload a CSV or Excel file", type=["csv", "xlsx"])

if file:
    df = load_data(file)

    metrics = summary_metrics(df)
    cols = st.columns(len(metrics))
    for col, (label, value) in zip(cols, metrics.items()):
        col.metric(label, value)

    st.subheader("Preview")
    st.dataframe(df.head())

    st.subheader("Column profile")
    st.dataframe(column_profile(df))

    st.header("Cleaning")
    cleaned, type_changes = infer_types(df)
    cleaned, removed = drop_duplicates(cleaned)

    st.write("**Type changes:**", ", ".join(type_changes) or "none")
    st.write(f"**Duplicate rows removed:** {removed}")

    st.subheader("Column profile after cleaning")
    st.dataframe(column_profile(cleaned))

    st.subheader("Summary statistics after cleaning")
    st.dataframe(cleaned.describe())

    st.subheader("Missing values")
    strategies = {}
    for c in cleaned.columns:
        n = int(cleaned[c].isna().sum())
        if n:
            strategies[c] = st.selectbox(
                f"{c} ({n} missing)", fix_options(cleaned[c]), key=f"miss_{c}"
            )
    cleaned, fixes = handle_missing(cleaned, strategies)
    st.write("**Fixes applied:**", "; ".join(fixes) or "none")

    st.subheader("Column profile after cleaning")
    st.dataframe(column_profile(cleaned))

    st.subheader("Summary statistics after cleaning")
    st.dataframe(cleaned.describe())

    st.subheader("Outlier check (IQR method)")
    outliers = detect_outliers(cleaned)
    st.dataframe(outliers)

    out_strategies = {}
    for col in outliers.loc[outliers["outliers"] > 0, "column"]:
        out_strategies[col] = st.selectbox(
            f"{col} outliers", ["keep", "remove rows", "cap at bounds"], key=f"out_{col}"
        )
    cleaned, out_fixes = handle_outliers(cleaned, out_strategies)
    st.write("**Outlier fixes applied:**", "; ".join(out_fixes) or "none")