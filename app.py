import pandas as pd
import streamlit as st

st.title("AI-Powered Data Analyst")

file = st.file_uploader("Upload a CSV or Excel file", type=["csv", "xlsx"])

if file:
    if file.name.endswith(".csv"):
        try:
            df = pd.read_csv(file)
        except UnicodeDecodeError:
            file.seek(0)
            df = pd.read_csv(file, encoding="latin-1")
    else:
        df = pd.read_excel(file)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Rows", df.shape[0])
    c2.metric("Columns", df.shape[1])
    c3.metric("Missing values", int(df.isna().sum().sum()))
    c4.metric("Duplicate rows", int(df.duplicated().sum()))

    st.subheader("Preview")
    st.dataframe(df.head())

    st.subheader("Column profile")
    profile = pd.DataFrame({
        "dtype": df.dtypes.astype(str),
        "missing": df.isna().sum(),
        "missing_%": (df.isna().mean() * 100).round(1),
        "unique": df.nunique(),
    })
    st.dataframe(profile)

    st.subheader("Summary statistics")
    st.dataframe(df.describe())