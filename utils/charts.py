import pandas as pd
import plotly.express as px

TIME_HINTS = ("date", "month", "year", "week", "day", "time")


def suggest_chart(df: pd.DataFrame):
    if df is None or df.shape[0] < 2 or df.shape[1] < 2:
        return None
    x = df.columns[0]
    numeric = [c for c in df.columns[1:] if pd.api.types.is_numeric_dtype(df[c])]
    if not numeric:
        return None
    is_time = pd.api.types.is_datetime64_any_dtype(df[x]) or any(
        hint in str(x).lower() for hint in TIME_HINTS
    )
    return ("line" if is_time else "bar"), x, numeric[0]


def make_chart(df: pd.DataFrame, kind: str, x: str, y: str):
    data = df.head(30) if kind == "bar" else df
    if kind == "line":
        return px.line(data, x=x, y=y, markers=True)
    return px.bar(data, x=x, y=y)