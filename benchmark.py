import numbers
import time

import pandas as pd

from utils.cleaner import drop_duplicates, infer_types
from utils.db import run_query
from utils.loader import load_data
from utils.pipeline import answer_question

RETAIL = [
    ("How many rows are in the data?",
     "SELECT COUNT(*) FROM data"),
    ("How many unique customers are there?",
     "SELECT COUNT(DISTINCT CustomerID) FROM data"),
    ("How many different countries are there?",
     "SELECT COUNT(DISTINCT Country) FROM data"),
    ("How many unique invoices are there?",
     "SELECT COUNT(DISTINCT InvoiceNo) FROM data"),
    ("How many different products (stock codes) are there?",
     "SELECT COUNT(DISTINCT StockCode) FROM data"),
    ("What is the total revenue?",
     "SELECT SUM(Quantity * UnitPrice) FROM data"),
    ("What is the average unit price?",
     "SELECT AVG(UnitPrice) FROM data"),
    ("How many rows have a negative quantity?",
     "SELECT COUNT(*) FROM data WHERE Quantity < 0"),
    ("Which country has the highest revenue?",
     "SELECT Country FROM data GROUP BY Country ORDER BY SUM(Quantity * UnitPrice) DESC LIMIT 1"),
    ("Sabse zyada revenue kis country se aaya?",
     "SELECT Country FROM data GROUP BY Country ORDER BY SUM(Quantity * UnitPrice) DESC LIMIT 1"),
    ("Which country has the most unique customers?",
     "SELECT Country FROM data GROUP BY Country ORDER BY COUNT(DISTINCT CustomerID) DESC LIMIT 1"),
    ("How many unique invoices came from Germany?",
     "SELECT COUNT(DISTINCT InvoiceNo) FROM data WHERE Country = 'Germany'"),
    ("What are the top 5 products by quantity sold?",
     "SELECT Description FROM data GROUP BY Description ORDER BY SUM(Quantity) DESC LIMIT 5"),
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

TELCO = [
    ("How many customers churned?",
     "SELECT COUNT(*) FROM data WHERE Churn = 'Yes'"),
    ("What is the churn rate as a percentage?",
     "SELECT 100.0 * SUM(CASE WHEN Churn = 'Yes' THEN 1 ELSE 0 END) / COUNT(*) FROM data"),
    ("Which contract type has the highest churn rate?",
     "SELECT Contract FROM data GROUP BY Contract ORDER BY AVG(CASE WHEN Churn = 'Yes' THEN 1.0 ELSE 0 END) DESC LIMIT 1"),
    ("What is the average monthly charge for customers who churned?",
     "SELECT AVG(MonthlyCharges) FROM data WHERE Churn = 'Yes'"),
    ("How many senior citizens are there?",
     "SELECT COUNT(*) FROM data WHERE SeniorCitizen = 1"),
    ("What is the average tenure in months?",
     "SELECT AVG(tenure) FROM data"),
    ("How many customers have fiber optic internet?",
     "SELECT COUNT(*) FROM data WHERE InternetService = 'Fiber optic'"),
    ("Which payment method is the most common?",
     "SELECT PaymentMethod FROM data GROUP BY PaymentMethod ORDER BY COUNT(*) DESC LIMIT 1"),
    ("What percentage of customers have no internet service?",
     "SELECT 100.0 * SUM(CASE WHEN InternetService = 'No' THEN 1 ELSE 0 END) / COUNT(*) FROM data"),
    ("How many customers have a missing TotalCharges?",
     "SELECT COUNT(*) FROM data WHERE TotalCharges IS NULL"),
    ("What is the average monthly charge for month-to-month customers?",
     "SELECT AVG(MonthlyCharges) FROM data WHERE Contract = 'Month-to-month'"),
    ("How many customers use electronic check?",
     "SELECT COUNT(*) FROM data WHERE PaymentMethod = 'Electronic check'"),
]

TELCO_DISGUISED = [
    ("How many customers left?",
     "SELECT COUNT(*) FROM data WHERE left_flag = 1"),
    ("What is the average monthly fee?",
     "SELECT AVG(monthly_fee) FROM data"),
    ("What is the average months active for customers who left?",
     "SELECT AVG(months_active) FROM data WHERE left_flag = 1"),
    ("How many customers are on the 2Y term?",
     "SELECT COUNT(*) FROM data WHERE term = '2Y'"),
    ("Which term has the highest share of customers who left?",
     "SELECT term FROM data GROUP BY term ORDER BY AVG(left_flag) DESC LIMIT 1"),
    ("How many customers pay by E-CHK?",
     "SELECT COUNT(*) FROM data WHERE pay_mode = 'E-CHK'"),
    ("What is the total lifetime fee?",
     "SELECT SUM(lifetime_fee) FROM data"),
    ("How many customers are seniors?",
     "SELECT COUNT(*) FROM data WHERE is_senior = 1"),
    ("How many customers are on plan F?",
     "SELECT COUNT(*) FROM data WHERE net_plan = 'F'"),
    ("What is the average monthly fee for customers on plan F?",
     "SELECT AVG(monthly_fee) FROM data WHERE net_plan = 'F'"),
    ("Which pay mode is the most common?",
     "SELECT pay_mode FROM data GROUP BY pay_mode ORDER BY COUNT(*) DESC LIMIT 1"),
    ("How many customers have no lifetime fee recorded?",
     "SELECT COUNT(*) FROM data WHERE lifetime_fee IS NULL"),
]

DATASETS = [
    ("Online Retail", "data/Online_Retail.csv", RETAIL),
    ("Telco Churn", "data/WA_Fn-UseC_-Telco-Customer-Churn.csv", TELCO),
    ("Telco Disguised", "data/telco_disguised.csv", TELCO_DISGUISED),
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


def load_clean(path):
    with open(path, "rb") as f:
        df = load_data(f)
    df, _ = infer_types(df)
    df, _ = drop_duplicates(df)
    return df


def main():
    rows = []
    for name, path, cases in DATASETS:
        print(f"\n== {name} ==")
        df = load_clean(path)
        for question, truth_sql in cases:
            truth = run_query(df, truth_sql)
            start = time.perf_counter()
            try:
                out = answer_question(question, df)
            except Exception as e:
                out = {"sql": "", "df": None, "error": str(e), "attempts": []}
            seconds = time.perf_counter() - start
            passed = out["error"] is None and results_match(truth, out["df"])
            rows.append({
                "dataset": name,
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
    print()
    for name, group in report.groupby("dataset", sort=False):
        print(f"{name}: {int(group['passed'].sum())}/{len(group)} = {group['passed'].mean():.0%}")
    print(f"Overall: {int(report['passed'].sum())}/{len(report)} = {report['passed'].mean():.0%}")
    print(f"Average time: {report['seconds'].mean():.1f}s")
    print("Details saved to benchmark_results.csv")


if __name__ == "__main__":
    main()