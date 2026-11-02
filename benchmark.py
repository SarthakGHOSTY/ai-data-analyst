import numbers
import sys
import time

import pandas as pd

from utils.cleaner import drop_duplicates, infer_types
from utils.db import run_query
from utils.loader import load_data
from utils.pipeline import answer_question

DATA_PATH = "data/Online_Retail.csv"

# (question, trusted SQL that gives the correct answer)
CASES = [
    ("What was the highest monthly revenue?",
     "SELECT MAX(r) FROM (SELECT SUM(Quantity * UnitPrice) AS r FROM data GROUP BY DATE_TRUNC('month', InvoiceDate))"),
    ("What is the average order value per invoice?",
     "SELECT AVG(t) FROM (SELECT SUM(Quantity * UnitPrice) AS t FROM data GROUP BY InvoiceNo)"),
    ("What was the total revenue in December 2010?",
     "SELECT SUM(Quantity * UnitPrice) FROM data WHERE InvoiceDate >= '2010-12-01' AND InvoiceDate < '2011-01-01'"),
    ("How many invoices were cancelled?",
     "SELECT COUNT(DISTINCT InvoiceNo) FROM data WHERE InvoiceNo LIKE 'C%'"),
    ("What is the total revenue excluding the United Kingdom?",
     "SELECT SUM(Quantity * UnitPrice) FROM data WHERE Country <> 'United Kingdom'"),
    ("Who are the top 3 customers by total spend?",
     "SELECT CustomerID FROM data WHERE CustomerID IS NOT NULL GROUP BY CustomerID ORDER BY SUM(Quantity * UnitPrice) DESC LIMIT 3"),
    ("How many customers placed more than 10 orders?",
     "SELECT COUNT(*) FROM (SELECT CustomerID FROM data WHERE CustomerID IS NOT NULL GROUP BY CustomerID HAVING COUNT(DISTINCT InvoiceNo) > 10)"),
    ("What percentage of revenue comes from the United Kingdom?",
     "SELECT 100.0 * SUM(CASE WHEN Country = 'United Kingdom' THEN Quantity * UnitPrice END) / SUM(Quantity * UnitPrice) FROM data"),
    ("Which product has the highest total revenue?",
     "SELECT Description FROM data GROUP BY Description ORDER BY SUM(Quantity * UnitPrice) DESC LIMIT 1"),
    ("What is the median quantity per row?",
     "SELECT MEDIAN(Quantity) FROM data"),
    ("How many rows have a missing description?",
     "SELECT COUNT(*) FROM data WHERE Description IS NULL"),
    ("How many custmers are there from France?",
     "SELECT COUNT(DISTINCT CustomerID) FROM data WHERE Country = 'France'"),
]


def norm_col(series):
    values = []
    for v in series.tolist():
        if pd.isna(v):
            values.append(None)
        elif isinstance(v, numbers.Number):
            values.append(round(float(v), 2))
        else:
            values.append(str(v))
    return values


def results_match(truth, got):
    if truth.shape[0] != got.shape[0]:
        return False
    got_cols = [norm_col(got[c]) for c in got.columns]
    return all(norm_col(truth[c]) in got_cols for c in truth.columns)


def main():
    with open(DATA_PATH, "rb") as f:
        df = load_data(f)
    df, _ = infer_types(df)
    df, _ = drop_duplicates(df)

    rows = []
    for question, truth_sql in CASES:
        truth = run_query(df, truth_sql)
        start = time.perf_counter()
        try:
            out = answer_question(question, df)
        except Exception as e:
            out = {"sql": "", "df": None, "error": str(e), "attempts": []}
        seconds = time.perf_counter() - start
        passed = out["error"] is None and results_match(truth, out["df"])
        rows.append({
            "question": question,
            "passed": passed,
            "attempts": len(out["attempts"]),
            "seconds": round(seconds, 1),
            "error": out["error"] or "",
            "generated_sql": " ".join(out["sql"].split()),
        })
        print("PASS" if passed else "FAIL", f"{seconds:4.1f}s", question)
        time.sleep(1)

    report = pd.DataFrame(rows)
    report.to_csv("benchmark_results.csv", index=False)
    total = len(report)
    correct = int(report["passed"].sum())
    print(f"\nAccuracy: {correct}/{total} = {correct / total:.0%}")
    print(f"Average time: {report['seconds'].mean():.1f}s")
    print("Details saved to benchmark_results.csv")


if __name__ == "__main__":
    main()