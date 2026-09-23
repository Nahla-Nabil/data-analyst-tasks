"""
Task 7 - Hospital Analytics: measures, KPIs, summary tables and statistical checks.

Reads  Cleaned_Hospital_Data.csv
Writes analysis_summary.json  (every KPI + table - feeds the workbook, dashboard and KEY_INSIGHTS.md)
       analysis_output.txt    (human-readable printout of the same)

Each KPI answers one management question:
  volume      -> Total Admissions, Avg Daily Census, Peak Census       (how busy are we?)
  efficiency  -> ALOS, Median LOS, Bed-Days, Long-Stay Rate            (how well do we use beds?)
  acuity      -> High-Severity Share, Senior Share                     (how sick / how old are patients?)
  finance     -> Uninsured Rate, Avg Recorded Bill, Cost per Day,
                 Billing Completeness                                   (is revenue at risk / recorded?)
  quality     -> Date-Correction Rate, Review-Flag Rate                (can we trust the records?)
"""

import json
import sys

import pandas as pd
from scipy import stats

IN_CSV = "Cleaned_Hospital_Data.csv"
OUT_JSON = "analysis_summary.json"
OUT_TXT = "analysis_output.txt"
L = "Length_of_Stay"

df = pd.read_csv(IN_CSV, parse_dates=["Admission_Date", "Discharge_Date"])
lines = []


def out(s=""):
    lines.append(str(s))


# ------------------------------------------------------------------ daily census (patients in a bed each night)
days = pd.date_range(df["Admission_Date"].min(), df["Discharge_Date"].max() - pd.Timedelta(days=1))
census = pd.Series([int(((df["Admission_Date"] <= d) & (df["Discharge_Date"] > d)).sum()) for d in days], index=days)
census_2023 = census[census.index.year == 2023]

# ------------------------------------------------------------------ headline KPIs
rec = df[df["Bill"].notna()]
kpi = {
    "total_admissions": len(df),
    "unique_names": int(df["Patient_Name"].nunique()),
    "alos": round(df[L].mean(), 2),
    "median_los": float(df[L].median()),
    "total_bed_days": int(df[L].sum()),
    "long_stay_rate": round(df["Long_Stay"].mean(), 4),
    "stays_15plus": int((df[L] >= 15).sum()),
    "bed_days_15plus_share": round(df.loc[df[L] >= 15, L].sum() / df[L].sum(), 4),
    "avg_daily_census": round(census_2023.mean(), 2),
    "peak_census": int(census.max()),
    "peak_census_date": f"{census.idxmax():%Y-%m-%d}",
    "high_severity_share": round(df["High_Severity"].mean(), 4),
    "senior_share": round((df["Age"] >= 60).mean(), 4),
    "avg_age": round(df["Age"].mean(), 1),
    "uninsured_rate": round(df["Is_Uninsured"].mean(), 4),
    "billing_completeness": round(len(rec) / len(df), 4),
    "recorded_bills": len(rec),
    "avg_recorded_bill": round(rec["Bill"].mean(), 0),
    "median_bill_per_day": round(rec["Bill_Per_Day"].median(), 0),
    "total_recorded_billing": int(rec["Bill"].sum()),
    "date_correction_rate": round(df["Date_Corrected"].mean(), 4),
    "review_flag_rate": round(df["Review_Flag"].notna().mean(), 4),
    "admissions_per_doctor": round(len(df) / df["Doctor"].nunique(), 1),
}


# ------------------------------------------------------------------ summary tables
def summary(by, order=None):
    g = df.groupby(by, observed=True).agg(
        Admissions=(L, "size"), ALOS=(L, "mean"), Bed_Days=(L, "sum"),
        Long_Stay_Rate=("Long_Stay", "mean"), High_Severity_Share=("High_Severity", "mean"),
        Uninsured_Rate=("Is_Uninsured", "mean"), Avg_Age=("Age", "mean"),
        Recorded_Bills=("Bill", "count"), Avg_Recorded_Bill=("Bill", "mean"),
        Review_Flags=("Review_Flag", "count"),
    )
    g["Admission_Share"] = g["Admissions"] / len(df)
    g["Bed_Day_Share"] = g["Bed_Days"] / df[L].sum()
    g = g.reindex(order) if order else g.sort_values("Admissions", ascending=False)
    return g.round(4).reset_index()


MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
WEEKDAYS = ["Saturday", "Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
tables = {
    "diagnosis": summary("Diagnosis"),
    "diagnosis_group": summary("Diagnosis_Group"),
    "doctor": summary("Doctor"),
    "insurance": summary("Insurance", ["Private", "Government", "Uninsured"]),
    "severity": summary("Severity", ["Low", "Medium", "High"]),
    "age_group": summary("Age_Group", ["Child (0-17)", "Adult (18-39)", "Middle age (40-59)", "Senior (60+)"]),
    "gender": summary("Gender"),
    "month": summary("Admission_Month_Name", MONTHS),
    "quarter": summary("Admission_Quarter", ["Q1", "Q2", "Q3", "Q4"]),
    "weekday": summary("Admission_Weekday", WEEKDAYS),
    "stay_band": summary("Stay_Band", ["1-3 days", "4-7 days", "8-14 days", "15+ days"]),
}
sev_by_dx = pd.crosstab(df["Diagnosis"], df["Severity"])[["Low", "Medium", "High"]]
monthly_census = census_2023.groupby(census_2023.index.month).mean().round(2)

# ------------------------------------------------------------------ statistical checks (do the gaps mean anything?)
tests = {}
for g in ["Severity", "Diagnosis", "Doctor", "Insurance", "Age_Group", "Gender"]:
    tests[f"LOS by {g} (Kruskal-Wallis)"] = stats.kruskal(*[x[L] for _, x in df.groupby(g)]).pvalue
for a, b in [("Diagnosis", "Severity"), ("Doctor", "Severity"), ("Insurance", "Severity"), ("Insurance", "Age_Group")]:
    tests[f"{a} vs {b} (chi-square)"] = stats.chi2_contingency(pd.crosstab(df[a], df[b]))[1]
rho_age, p_age = stats.spearmanr(df["Age"], df[L])
rho_bill, p_bill = stats.spearmanr(rec["Bill"], rec[L])
tests["Age vs LOS (Spearman)"] = p_age
tests["Recorded bill vs LOS (Spearman)"] = p_bill
corr = {"age_los_rho": round(rho_age, 3), "bill_los_rho": round(rho_bill, 3)}

# ------------------------------------------------------------------ focused findings
long15 = df[df[L] >= 15]
findings = {
    "minor_in_15plus": int(long15["Review_Flag"].eq("Long stay for minor condition").sum()),
    "long15_recorded_bills": int(long15["Bill"].notna().sum()),
    "senior_bed_day_share": round(df.loc[df["Age"] >= 60, L].sum() / df[L].sum(), 4),
    "top2_doctor_admission_share": None, "top2_doctor_bed_day_share": None,
    "cold_alos": round(df.loc[df["Diagnosis"] == "Common Cold", L].mean(), 2),
    "stroke_alos": round(df.loc[df["Diagnosis"] == "Stroke", L].mean(), 2),
    "pneumonia_high_share": round(df.loc[df["Diagnosis"] == "Pneumonia", "High_Severity"].mean(), 4),
    "alos_high": round(df.loc[df["Severity"] == "High", L].mean(), 2),
    "alos_low": round(df.loc[df["Severity"] == "Low", L].mean(), 2),
    "friday_admissions": int((df["Admission_Weekday"] == "Friday").sum()),
    "tue_wed_admissions": int(df["Admission_Weekday"].isin(["Tuesday", "Wednesday"]).sum()),
    "recorded_bill_short_stay_share": round((rec[L] <= 7).mean(), 4),
}
doc = tables["doctor"].sort_values("ALOS", ascending=False)
top2 = doc.head(2)
findings["top2_doctors"] = top2["Doctor"].tolist()
findings["top2_doctor_admission_share"] = round(top2["Admissions"].sum() / len(df), 4)
findings["top2_doctor_bed_day_share"] = round(top2["Bed_Days"].sum() / df[L].sum(), 4)

# ------------------------------------------------------------------ print + save
out("=== HEADLINE KPIs ===")
for k, v in kpi.items():
    out(f"{k:28s} {v}")
for name, t in tables.items():
    out(f"\n=== BY {name.upper()} ===")
    out(t.to_string(index=False))
out("\n=== SEVERITY MIX BY DIAGNOSIS (counts) ===")
out(sev_by_dx.to_string())
out("\n=== AVG DAILY CENSUS BY MONTH (2023) ===")
out(monthly_census.to_string())
out("\n=== STATISTICAL TESTS (p-values; < 0.05 = real difference) ===")
for k, v in tests.items():
    out(f"{k:45s} p = {v:.3f}")
out(f"\nSpearman rho: age~LOS {corr['age_los_rho']}, recorded bill~LOS {corr['bill_los_rho']}")
out("\n=== FOCUSED FINDINGS ===")
for k, v in findings.items():
    out(f"{k:36s} {v}")

text = "\n".join(lines)
with open(OUT_TXT, "w", encoding="utf-8") as f:
    f.write(text)
sys.stdout.reconfigure(encoding="utf-8")
print(text)


def jsonable(t):
    return json.loads(t.to_json(orient="records"))


summary_json = {
    "kpi": kpi, "tables": {k: jsonable(v) for k, v in tables.items()},
    "severity_by_diagnosis": {"index": sev_by_dx.index.tolist(), "columns": sev_by_dx.columns.tolist(), "data": sev_by_dx.values.tolist()},
    "monthly_census": {int(k): float(v) for k, v in monthly_census.items()},
    "daily_census": {"dates": [f"{d:%Y-%m-%d}" for d in census.index], "values": census.tolist()},
    "tests": {k: round(float(v), 4) for k, v in tests.items()}, "corr": corr, "findings": findings,
}
with open(OUT_JSON, "w", encoding="utf-8") as f:
    json.dump(summary_json, f, ensure_ascii=False, indent=1, default=float)
