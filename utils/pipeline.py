import pandas as pd

from utils.db import run_query
from utils.llm import fix_sql, generate_sql
from utils.validator import validate_sql


def answer_question(question: str, df: pd.DataFrame, max_retries: int = 2) -> dict:
    attempts = []
    sql = generate_sql(question, df)
    for attempt in range(max_retries + 1):
        ok, result = validate_sql(sql)
        if not ok:
            error = f"Blocked: {result}"
            attempts.append((sql, error))
            return {"sql": sql, "df": None, "error": error, "attempts": attempts}
        try:
            out = run_query(df, result)
            attempts.append((result, None))
            return {"sql": result, "df": out, "error": None, "attempts": attempts}
        except Exception as e:
            attempts.append((result, str(e)))
            if attempt == max_retries:
                return {"sql": result, "df": None, "error": str(e), "attempts": attempts}
            sql = fix_sql(question, df, result, str(e))