import pandas as pd
import streamlit as st

from utils.charts import make_chart, suggest_chart
from utils.cleaner import (
    detect_outliers,
    drop_duplicates,
    fix_options,
    handle_missing,
    handle_outliers,
    infer_types,
)
from utils.db import run_query
from utils.llm import explain_result
from utils.loader import load_data
from utils.pipeline import answer_question
from utils.profiler import column_profile, summary_metrics
from utils.validator import validate_sql


def date_note(df):
    parts = []
    for c in df.select_dtypes("datetime").columns:
        parts.append(f"{c} runs from {df[c].min():%Y-%m-%d} to {df[c].max():%Y-%m-%d}")
    return "; ".join(parts)


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
    cleaned, extra_dupes = drop_duplicates(cleaned)
    if extra_dupes:
        st.write(f"**Duplicates created by outlier capping, removed:** {extra_dupes}")

    st.header("Cleaning report")
    report = pd.DataFrame({"before": summary_metrics(df), "after": summary_metrics(cleaned)})
    st.dataframe(report)

    st.subheader("Column profile after cleaning")
    st.dataframe(column_profile(cleaned))

    st.subheader("Summary statistics after cleaning")
    st.dataframe(cleaned.describe())

    st.download_button(
        "Download cleaned CSV",
        cleaned.to_csv(index=False).encode("utf-8"),
        "cleaned_data.csv",
        "text/csv",
    )

    st.header("SQL playground")
    sql = st.text_area("SQL (table name: data)", "SELECT * FROM data LIMIT 5")
    if st.button("Run query"):
        ok, checked = validate_sql(sql)
        if not ok:
            st.error(f"Blocked: {checked}")
        else:
            try:
                res = run_query(cleaned, checked)
                st.dataframe(res)
                pick = suggest_chart(res)
                if pick:
                    kind, x, y = pick
                    st.plotly_chart(make_chart(res, kind, x, y), key="playground_chart")
            except Exception as e:
                st.error(str(e))

    st.header("Ask a question")
    history = st.session_state.setdefault("history", [])
    question = st.text_input("Ask about your data in plain English")
    if st.button("Ask"):
        if not question:
            st.warning("Type a question first.")
        else:
            with st.spinner("Thinking..."):
                try:
                    out = answer_question(question, cleaned)
                except Exception as e:
                    st.error(str(e))
                    st.stop()
            out.update(question=question, file=file.name, insight=None)
            history.append(out)

    if history and st.button("Clear history"):
        history.clear()
        st.rerun()

    for idx in reversed(range(len(history))):
        item = history[idx]
        if item["file"] != file.name:
            continue
        with st.container(border=True):
            st.markdown(f"**Q: {item['question']}**")
            st.code(item["sql"], language="sql")
            if len(item["attempts"]) > 1:
                st.caption(f"Needed {len(item['attempts'])} attempts to get a working query.")
            if item["error"]:
                st.error(item["error"])
                continue
            result = item["df"].head(1000)
            st.dataframe(result)
            pick = suggest_chart(result)
            if pick:
                kind, x, y = pick
                st.plotly_chart(make_chart(result, kind, x, y), key=f"chart_{idx}")
            if st.button("Explain this result", key=f"explain_{idx}"):
                with st.spinner("Writing insight..."):
                    try:
                        item["insight"] = explain_result(
                            item["question"], item["sql"], result, date_note(cleaned)
                        )
                    except Exception as e:
                        st.error(str(e))
            if item["insight"]:
                st.info(item["insight"].replace("$", "\\$"))