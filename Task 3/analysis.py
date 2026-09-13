"""
Task 3 - HR Employee Attrition: Analysis

Runs the analysis the task asks for directly against Cleaned_HR_Attrition.csv:
  1. Headcount by department / job role
  2. Salary vs experience vs performance
  3. Satisfaction levels (overall + split by attrition)
  4. Attrition and its drivers (OverTime, JobSatisfaction, WorkLifeBalance, ...)

Prints a readable report to stdout (redirected to analysis_output.txt) and
also dumps the key numbers to analysis_summary.json so the dashboard/report
builders don't have to recompute anything.
"""

import json
import pandas as pd

pd.set_option("display.width", 120)
pd.set_option("display.max_columns", 20)

df = pd.read_csv("Cleaned_HR_Attrition.csv")
N = len(df)
attr_rate = df["AttritionFlag"].mean() * 100

summary = {}

def hr(title):
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)

# ---------------------------------------------------------------- overview
hr("0. OVERVIEW")
print(f"Total employees: {N}")
print(f"Overall attrition rate: {attr_rate:.1f}%  ({df['AttritionFlag'].sum()} left / {N - df['AttritionFlag'].sum()} stayed)")
summary["overview"] = {"n_employees": N, "attrition_rate_pct": round(attr_rate, 2)}

# ---------------------------------------------------------------- 1. dept & role
hr("1. HEADCOUNT & ATTRITION BY DEPARTMENT")
dept = df.groupby("Department").agg(Headcount=("EmployeeNumber", "count"),
                                     AttritionRate=("AttritionFlag", "mean"),
                                     AvgIncome=("MonthlyIncome", "mean")).round(2)
dept["AttritionRate"] = (dept["AttritionRate"] * 100).round(1)
print(dept.sort_values("Headcount", ascending=False))
summary["by_department"] = dept.reset_index().to_dict(orient="records")

hr("1b. HEADCOUNT & ATTRITION BY JOB ROLE")
role = df.groupby("JobRole").agg(Headcount=("EmployeeNumber", "count"),
                                  AttritionRate=("AttritionFlag", "mean"),
                                  AvgIncome=("MonthlyIncome", "mean")).round(2)
role["AttritionRate"] = (role["AttritionRate"] * 100).round(1)
role = role.sort_values("AttritionRate", ascending=False)
print(role)
summary["by_job_role"] = role.reset_index().to_dict(orient="records")

# ---------------------------------------------------------------- 2. salary/exp/perf
hr("2. SALARY BY JOB LEVEL")
lvl = df.groupby("JobLevel").agg(Headcount=("EmployeeNumber", "count"),
                                  AvgIncome=("MonthlyIncome", "mean"),
                                  AvgTotalYears=("TotalWorkingYears", "mean")).round(0)
print(lvl)
summary["by_job_level"] = lvl.reset_index().to_dict(orient="records")

hr("2b. SALARY vs EXPERIENCE (correlation)")
corr_income_exp = df["MonthlyIncome"].corr(df["TotalWorkingYears"])
corr_income_age = df["MonthlyIncome"].corr(df["Age"])
print(f"Correlation MonthlyIncome vs TotalWorkingYears: {corr_income_exp:.2f}")
print(f"Correlation MonthlyIncome vs Age: {corr_income_age:.2f}")
summary["correlations"] = {"income_vs_experience": round(corr_income_exp, 3),
                            "income_vs_age": round(corr_income_age, 3)}

hr("2c. PERFORMANCE RATING DISTRIBUTION & SALARY HIKE")
perf = df.groupby("PerformanceRating").agg(Headcount=("EmployeeNumber", "count"),
                                            AvgSalaryHike=("PercentSalaryHike", "mean"),
                                            AvgIncome=("MonthlyIncome", "mean")).round(1)
print(perf)
summary["by_performance_rating"] = perf.reset_index().to_dict(orient="records")

# ---------------------------------------------------------------- 3. satisfaction
hr("3. SATISFACTION LEVELS (overall averages, scale 1-4)")
sat_cols = ["JobSatisfaction", "EnvironmentSatisfaction", "RelationshipSatisfaction", "WorkLifeBalance"]
sat_overall = df[sat_cols].mean().round(2)
print(sat_overall)
summary["satisfaction_overall"] = sat_overall.to_dict()

hr("3b. SATISFACTION LEVELS SPLIT BY ATTRITION")
sat_by_attr = df.groupby("Attrition")[sat_cols].mean().round(2)
print(sat_by_attr)
summary["satisfaction_by_attrition"] = sat_by_attr.reset_index().to_dict(orient="records")

# ---------------------------------------------------------------- 4. attrition drivers
hr("4. ATTRITION RATE BY OVERTIME")
ot = df.groupby("OverTime")["AttritionFlag"].agg(["count", "mean"])
ot["mean"] = (ot["mean"] * 100).round(1)
print(ot.rename(columns={"count": "Headcount", "mean": "AttritionRate%"}))
summary["attrition_by_overtime"] = ot.reset_index().rename(
    columns={"count": "Headcount", "mean": "AttritionRatePct"}).to_dict(orient="records")

hr("4b. ATTRITION RATE BY JOB SATISFACTION LEVEL (1=Low .. 4=Very High)")
js = df.groupby("JobSatisfaction")["AttritionFlag"].agg(["count", "mean"])
js["mean"] = (js["mean"] * 100).round(1)
print(js.rename(columns={"count": "Headcount", "mean": "AttritionRate%"}))
summary["attrition_by_job_satisfaction"] = js.reset_index().rename(
    columns={"count": "Headcount", "mean": "AttritionRatePct"}).to_dict(orient="records")

hr("4c. ATTRITION RATE BY WORK-LIFE BALANCE (1=Bad .. 4=Best)")
wlb = df.groupby("WorkLifeBalance")["AttritionFlag"].agg(["count", "mean"])
wlb["mean"] = (wlb["mean"] * 100).round(1)
print(wlb.rename(columns={"count": "Headcount", "mean": "AttritionRate%"}))
summary["attrition_by_worklife_balance"] = wlb.reset_index().rename(
    columns={"count": "Headcount", "mean": "AttritionRatePct"}).to_dict(orient="records")

hr("4d. ATTRITION RATE BY BUSINESS TRAVEL")
bt = df.groupby("BusinessTravel")["AttritionFlag"].agg(["count", "mean"])
bt["mean"] = (bt["mean"] * 100).round(1)
print(bt.rename(columns={"count": "Headcount", "mean": "AttritionRate%"}))
summary["attrition_by_business_travel"] = bt.reset_index().rename(
    columns={"count": "Headcount", "mean": "AttritionRatePct"}).to_dict(orient="records")

hr("4e. ATTRITION RATE BY MARITAL STATUS")
ms = df.groupby("MaritalStatus")["AttritionFlag"].agg(["count", "mean"])
ms["mean"] = (ms["mean"] * 100).round(1)
print(ms.rename(columns={"count": "Headcount", "mean": "AttritionRate%"}))
summary["attrition_by_marital_status"] = ms.reset_index().rename(
    columns={"count": "Headcount", "mean": "AttritionRatePct"}).to_dict(orient="records")

hr("4f. ATTRITION RATE BY AGE GROUP")
ag = df.groupby("AgeGroup", observed=True)["AttritionFlag"].agg(["count", "mean"])
ag["mean"] = (ag["mean"] * 100).round(1)
print(ag.rename(columns={"count": "Headcount", "mean": "AttritionRate%"}))
summary["attrition_by_age_group"] = ag.reset_index().rename(
    columns={"count": "Headcount", "mean": "AttritionRatePct"}).to_dict(orient="records")

hr("4g. ATTRITION RATE BY TENURE BAND")
tb = df.groupby("TenureBand", observed=True)["AttritionFlag"].agg(["count", "mean"])
tb["mean"] = (tb["mean"] * 100).round(1)
print(tb.rename(columns={"count": "Headcount", "mean": "AttritionRate%"}))
summary["attrition_by_tenure_band"] = tb.reset_index().rename(
    columns={"count": "Headcount", "mean": "AttritionRatePct"}).to_dict(orient="records")

hr("4h. AVERAGE MONTHLY INCOME: STAYED vs LEFT")
inc_attr = df.groupby("Attrition")["MonthlyIncome"].mean().round(0)
print(inc_attr)
summary["income_by_attrition"] = inc_attr.to_dict()

hr("4i. DISTANCE FROM HOME: STAYED vs LEFT")
dist_attr = df.groupby("Attrition")["DistanceFromHome"].mean().round(1)
print(dist_attr)
summary["distance_by_attrition"] = dist_attr.to_dict()

with open("analysis_summary.json", "w", encoding="utf-8") as f:
    json.dump(summary, f, indent=2, default=str)

print("\nSaved -> analysis_summary.json")
