import duckdb
import pandas as pd


def run_query(df: pd.DataFrame, sql: str) -> pd.DataFrame:
    con = duckdb.connect()
    con.register("data", df)
    con.execute("SET enable_external_access = false")
    try:
        return con.execute(sql).df()
    finally:
        con.close()