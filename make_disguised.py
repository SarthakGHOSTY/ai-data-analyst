import pandas as pd

SRC = "data/WA_Fn-UseC_-Telco-Customer-Churn.csv"
OUT = "data/telco_disguised.csv"

df = pd.read_csv(SRC)
df = df.rename(columns={
    "customerID": "cid",
    "gender": "sex",
    "SeniorCitizen": "is_senior",
    "tenure": "months_active",
    "InternetService": "net_plan",
    "Contract": "term",
    "PaymentMethod": "pay_mode",
    "MonthlyCharges": "monthly_fee",
    "TotalCharges": "lifetime_fee",
    "Churn": "left_flag",
})
df = df[["cid", "sex", "is_senior", "months_active", "net_plan", "term",
         "pay_mode", "monthly_fee", "lifetime_fee", "left_flag"]]

df["net_plan"] = df["net_plan"].map({"DSL": "D", "Fiber optic": "F", "No": "N"})
df["term"] = df["term"].map({"Month-to-month": "M2M", "One year": "1Y", "Two year": "2Y"})
df["pay_mode"] = df["pay_mode"].map({
    "Electronic check": "E-CHK",
    "Mailed check": "M-CHK",
    "Bank transfer (automatic)": "BANK",
    "Credit card (automatic)": "CARD",
})
df["left_flag"] = df["left_flag"].map({"Yes": 1, "No": 0})

df.to_csv(OUT, index=False)
print("saved", OUT, df.shape)