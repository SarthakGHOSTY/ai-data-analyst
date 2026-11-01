import os
import time

import pandas as pd
from dotenv import load_dotenv
from google import genai
from google.genai import errors

load_dotenv()
MODEL = "gemini-3.8-flash"


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
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    for attempt in range(retries):
        try:
            return client.models.generate_content(model=MODEL, contents=prompt).text
        except errors.APIError as e:
            if e.code in (429, 500, 503, 504) and attempt < retries - 1:
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