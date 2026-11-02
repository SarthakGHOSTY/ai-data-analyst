import os
import time

import pandas as pd
from dotenv import load_dotenv
from groq import APIConnectionError, APIStatusError, Groq

load_dotenv(override=True)
MODEL = "openai/gpt-oss-120b"


def build_prompt(question: str, df: pd.DataFrame) -> str:
    schema = "\n".join(f"- {c} ({t})" for c, t in df.dtypes.astype(str).items())
    sample = df.head(3).to_csv(index=False)
    return f"""You are a data analyst who writes DuckDB SQL.
Table name: data

Columns:
{schema}

Sample rows (CSV):
{sample}
Rules:
- Return exactly one SELECT query and nothing else (no explanation, no markdown).
- Use only the table "data" and the columns listed above.
- Wrap column names in double quotes if they contain spaces.
- Give every calculated column a short readable alias, like AS total_revenue.

Question: {question}
SQL:"""


def clean_sql(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`").strip()
        if text.lower().startswith("sql"):
            text = text[3:]
    return text.strip().rstrip(";").strip()


def call_llm(prompt: str, retries: int = 3) -> str:
    client = Groq(api_key=os.environ["GROQ_API_KEY"])
    for attempt in range(retries):
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
            )
            return response.choices[0].message.content or ""
        except APIStatusError as e:
            if e.status_code in (429, 500, 502, 503, 504) and attempt < retries - 1:
                time.sleep(2 * (attempt + 1))
                continue
            raise
        except APIConnectionError:
            if attempt < retries - 1:
                time.sleep(2 * (attempt + 1))
                continue
            raise


def generate_sql(question: str, df: pd.DataFrame) -> str:
    return clean_sql(call_llm(build_prompt(question, df)))


def fix_sql(question: str, df: pd.DataFrame, bad_sql: str, error: str) -> str:
    base = build_prompt(question, df).rsplit("SQL:", 1)[0]
    prompt = (
        f"{base}Your previous query:\n{bad_sql}\n\n"
        f"failed with this error:\n{error}\n\n"
        "Write a corrected query that follows the same rules.\nSQL:"
    )
    return clean_sql(call_llm(prompt))


def build_insight_prompt(question: str, sql: str, result: pd.DataFrame) -> str:
    table = result.head(20).to_csv(index=False)
    return f"""You are a data analyst explaining a query result to a non-technical user.

Question: {question}
SQL used: {sql}
Result (first rows, CSV):
{table}
Write 2-3 short sentences in plain English: the direct answer, then one notable
pattern or caveat. Use only numbers shown in the result. Do not invent causes."""


def explain_result(question: str, sql: str, result: pd.DataFrame) -> str:
    return call_llm(build_insight_prompt(question, sql, result)).strip()