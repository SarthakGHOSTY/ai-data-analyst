import streamlit as st

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

    st.subheader("Summary statistics")
    st.dataframe(df.describe())