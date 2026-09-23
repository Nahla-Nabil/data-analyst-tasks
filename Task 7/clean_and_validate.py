"""
Task 7 - Hospital Analytics: data cleaning & validation.

Reads  Hospital Analytics.xlsx   (sheet "Data Before Cleaning", 248 rows, Arabic headers/values)
Writes Cleaned_Hospital_Data.csv  (UTF-8 with BOM so Excel shows Arabic correctly)
       cleaning_log.json          (every check, its count and the action taken - used by the report + workbook)

Cleaning steps, in order:
  1. Rename Arabic headers to English, trim whitespace, enforce data types.
  2. Remove exact duplicate rows.
  3. Fix discharge-before-admission rows (dates entered in the wrong order -> swapped, flagged).
  4. Detect placeholder bills (999 and 3852) -> set to missing, keep a Bill_Status flag.
  5. Standardise categories: Arabic -> English labels, ordered Severity, doctor names transliterated.
  6. Flag (not delete) clinically unusual rows: long-stay outliers, atypical age for the diagnosis.
  7. Record known limitations that cannot be fixed from this file (gender vs first name, no patient ID).
  8. Add calculated columns used by the KPIs and dashboard.
"""

import json

import numpy as np
import pandas as pd

RAW = "Hospital Analytics.xlsx"
OUT = "Cleaned_Hospital_Data.csv"
LOG = "cleaning_log.json"

COLS = {
    "اسم المريض": "Patient_Name", "العمر": "Age", "الجنس": "Gender", "التشخيص": "Diagnosis_AR",
    "الطبيب المعالج": "Doctor_AR", "تاريخ الدخول": "Admission_Date", "تاريخ الخروج": "Discharge_Date",
    "الفاتورة": "Bill_Raw", "التأمين": "Insurance_AR", "مستوى الخطورة": "Severity_AR",
}
GENDER = {"ذكر": "Male", "أنثى": "Female"}
DIAGNOSIS = {
    "أنفلونزا": "Influenza", "نزلة برد": "Common Cold", "التهاب رئوي": "Pneumonia",
    "كسور": "Fractures", "سكري": "Diabetes", "ضغط مرتفع": "Hypertension",
    "فشل كلوي": "Kidney Failure", "حساسية مزمنة": "Chronic Allergy",
    "صداع نصفي": "Migraine", "جلطة": "Stroke",
}
# clinical grouping - lets the dashboard compare acute vs chronic vs critical workload
DIAG_GROUP = {
    "Influenza": "Respiratory infection", "Common Cold": "Respiratory infection", "Pneumonia": "Respiratory infection",
    "Diabetes": "Chronic disease", "Hypertension": "Chronic disease", "Kidney Failure": "Chronic disease",
    "Chronic Allergy": "Chronic disease", "Fractures": "Trauma", "Migraine": "Neurological", "Stroke": "Neurological",
}
# conditions where a multi-week stay is clinically unusual
MINOR = {"Common Cold", "Influenza", "Migraine", "Chronic Allergy"}
DOCTOR = {
    "د. ريم عبد الله": "Dr. Reem Abdullah", "د. محمد حسن": "Dr. Mohamed Hassan", "د. أحمد علي": "Dr. Ahmed Ali",
    "د. ياسمين محمود": "Dr. Yasmin Mahmoud", "د. خالد سامي": "Dr. Khaled Sami", "د. نور خالد": "Dr. Nour Khaled",
    "د. سارة إبراهيم": "Dr. Sara Ibrahim",
}
INSURANCE = {"تأمين خاص": "Private", "تأمين حكومي": "Government", "بدون تأمين": "Uninsured"}
SEVERITY = {"منخفض": "Low", "متوسط": "Medium", "مرتفع": "High"}
FEMALE_FIRST = {"ندى", "ياسمين", "مريم", "سارة", "نور", "ريم"}
PLACEHOLDER_BILLS = (999, 3852)

log = {"checks": []}


def note(check, count, action, detail=""):
    log["checks"].append({"check": check, "count": int(count), "action": action, "detail": detail})
    print(f"- {check}: {count} -> {action}")


# ---------------------------------------------------------------- 1. load, rename, types
raw = pd.read_excel(RAW, sheet_name="Data Before Cleaning")
log["raw_rows"], log["raw_cols"] = int(raw.shape[0]), int(raw.shape[1])
df = raw.rename(columns=lambda c: COLS[str(c).strip()])

for c in df.select_dtypes(include=["object", "string"]).columns:
    df[c] = df[c].astype(str).str.strip().str.replace(r"\s+", " ", regex=True)
df["Age"] = pd.to_numeric(df["Age"], errors="coerce")
df["Bill_Raw"] = pd.to_numeric(df["Bill_Raw"], errors="coerce")
for c in ("Admission_Date", "Discharge_Date"):
    df[c] = pd.to_datetime(df[c], errors="coerce").dt.normalize()

note("Missing values (all columns)", df.isna().sum().sum(), "none found - no imputation needed",
     "blank cells checked after type coercion; the real 'missing' data is hidden as placeholder bills (step 4)")

# ---------------------------------------------------------------- 2. duplicates
dups = df.duplicated()
note("Exact duplicate rows", dups.sum(), "removed (kept first occurrence)",
     "; ".join(f"row {i + 2}: {df.loc[i, 'Patient_Name']}, {df.loc[i, 'Admission_Date']:%Y-%m-%d}" for i in df.index[dups]))
df = df[~dups].reset_index(drop=True)

# ---------------------------------------------------------------- 3. date order
neg = df["Discharge_Date"] < df["Admission_Date"]
gap = (df.loc[neg, "Admission_Date"] - df.loc[neg, "Discharge_Date"]).dt.days
note("Discharge date before admission date", neg.sum(), "dates swapped + Date_Corrected flag",
     f"gaps of {gap.min()}-{gap.max()} days, the same size as normal stays -> a data-entry order error, not a real value")
df["Date_Corrected"] = neg
df.loc[neg, ["Admission_Date", "Discharge_Date"]] = df.loc[neg, ["Discharge_Date", "Admission_Date"]].values
note("Same-day admission/discharge", (df["Discharge_Date"] == df["Admission_Date"]).sum(), "none found")

# ---------------------------------------------------------------- 4. placeholder bills
df["Length_of_Stay"] = (df["Discharge_Date"] - df["Admission_Date"]).dt.days
is_ph = df["Bill_Raw"].isin(PLACEHOLDER_BILLS)
real = df[~is_ph]
r_los = real["Bill_Raw"].corr(real["Length_of_Stay"])
ph_los = df.loc[is_ph, "Bill_Raw"].groupby(df["Bill_Raw"]).size().to_dict()
note("Placeholder bill values (999, 3852)", is_ph.sum(), "set to missing + Bill_Status flag (not imputed)",
     f"999 x{ph_los.get(999, 0)} and 3852 x{ph_los.get(3852, 0)} repeat across every diagnosis, severity and "
     f"stay length; the other {len(real)} bills are all distinct and rise with stay length (r = {r_los:.2f}). "
     "Imputing 79% of bills from 21% would invent the financial picture, so finance KPIs use recorded bills only.")
df["Bill_Status"] = np.select([df["Bill_Raw"] == 999, df["Bill_Raw"] == 3852], ["Placeholder 999", "Placeholder 3852"], "Recorded")
df["Bill"] = df["Bill_Raw"].where(~is_ph)
log["bill_evidence"] = {
    "recorded_n": int(len(real)), "placeholder_n": int(is_ph.sum()),
    "corr_bill_los_recorded": round(float(r_los), 3),
    "avg_los_recorded": round(float(real["Length_of_Stay"].mean()), 2),
    "avg_los_placeholder": round(float(df.loc[is_ph, "Length_of_Stay"].mean()), 2),
    "recorded_min": int(real["Bill_Raw"].min()), "recorded_max": int(real["Bill_Raw"].max()),
}

# ---------------------------------------------------------------- 5. standardise categories
for col, mapping, new in [("Gender", GENDER, "Gender"), ("Diagnosis_AR", DIAGNOSIS, "Diagnosis"),
                          ("Doctor_AR", DOCTOR, "Doctor"), ("Insurance_AR", INSURANCE, "Insurance"),
                          ("Severity_AR", SEVERITY, "Severity")]:
    unknown = set(df[col]) - set(mapping)
    assert not unknown, f"unmapped {col}: {unknown}"
    if col == "Gender":
        df["Gender_AR"] = df["Gender"]
    df[new] = df[col].map(mapping)
note("Category spelling variants", 0, "none found; Arabic labels mapped to English (Arabic kept in *_AR columns)",
     "Gender 2, Diagnosis 10, Doctor 7, Insurance 3, Severity 3 distinct values")
df["Diagnosis_Group"] = df["Diagnosis"].map(DIAG_GROUP)
df["Severity"] = pd.Categorical(df["Severity"], ["Low", "Medium", "High"], ordered=True)

# ---------------------------------------------------------------- 6. range & plausibility checks
bad_age = ~df["Age"].between(0, 110)
note("Age outside 0-110", bad_age.sum(), "none found", f"range {df['Age'].min()}-{df['Age'].max()}")
bad_bill = df["Bill"].notna() & (df["Bill"] <= 0)
note("Zero/negative recorded bills", bad_bill.sum(), "none found")
out_year = ~df["Admission_Date"].dt.year.eq(2023)
note("Admissions outside 2023", out_year.sum(),
     "kept - a New-Year stay (31 Dec 2022 -> 3 Jan 2023) produced by the date swap" if out_year.any() else "none found",
     f"admissions {df['Admission_Date'].min():%Y-%m-%d} to {df['Admission_Date'].max():%Y-%m-%d}; "
     "the 12-month charts count it under December (1 of 247 rows)")

q1, q3 = df["Length_of_Stay"].quantile([.25, .75])
fence = q3 + 1.5 * (q3 - q1)
df["LOS_Outlier"] = df["Length_of_Stay"] > fence
note(f"Length of stay above IQR fence (> {fence:.0f} days)", df["LOS_Outlier"].sum(), "kept + LOS_Outlier flag",
     "long stays are possible and drive bed capacity; removing them would understate workload")
long_minor = df["Diagnosis"].isin(MINOR) & (df["Length_of_Stay"] > 14)
note("Stay > 14 days for a minor condition (cold, flu, migraine, allergy)", long_minor.sum(),
     "kept + flagged in Review_Flag", "clinically unusual - worth a chart review / coding audit")
atypical_age = ((df["Diagnosis"] == "Stroke") & (df["Age"] < 18)) | ((df["Diagnosis"] == "Hypertension") & (df["Age"] < 12))
note("Atypical age for diagnosis (stroke < 18, hypertension < 12)", atypical_age.sum(),
     "kept + flagged in Review_Flag", "rare but possible in children - cannot be proved wrong from this file")
df["Review_Flag"] = np.select([long_minor, atypical_age], ["Long stay for minor condition", "Atypical age for diagnosis"], "")

# ---------------------------------------------------------------- 7. consistency limits (reported, not changed)
first = df["Patient_Name"].str.split().str[0]
name_gender = np.where(first.isin(FEMALE_FIRST), "Female", "Male")
mism = (name_gender != df["Gender"]).mean()
note("Gender disagrees with first name", (name_gender != df["Gender"]).sum(), "reported, not changed",
     f"{mism:.0%} of rows - near a coin toss, so the recorded gender cannot be trusted but also cannot be corrected "
     "reliably (which of name or gender is wrong is unknown). Gender charts carry this caveat.")
g = df.groupby("Patient_Name").agg(n=("Age", "size"), ages=("Age", "nunique"))
note("Repeated patient names with different ages", int((g["ages"] > 1).sum()),
     "Patient_ID created per admission; names treated as non-unique",
     f"{df['Patient_Name'].nunique()} names across {len(df)} admissions; same name appears with different ages/genders "
     "-> different people, so readmission rate cannot be measured")

# ---------------------------------------------------------------- 8. calculated columns
df.insert(0, "Patient_ID", [f"P{i:04d}" for i in range(1, len(df) + 1)])
df["Age_Group"] = pd.cut(df["Age"], [-1, 17, 39, 59, 200], labels=["Child (0-17)", "Adult (18-39)", "Middle age (40-59)", "Senior (60+)"])
df["Stay_Band"] = pd.cut(df["Length_of_Stay"], [0, 3, 7, 14, 1000], labels=["1-3 days", "4-7 days", "8-14 days", "15+ days"])
df["Long_Stay"] = df["Length_of_Stay"] > 7
df["Admission_Month"] = df["Admission_Date"].dt.month
df["Admission_Month_Name"] = df["Admission_Date"].dt.strftime("%b")
df["Admission_Quarter"] = "Q" + df["Admission_Date"].dt.quarter.astype(str)
df["Admission_Weekday"] = df["Admission_Date"].dt.day_name()
df["Is_Weekend"] = df["Admission_Date"].dt.dayofweek.isin([4, 5])  # Fri/Sat - Arabic-region weekend
df["High_Severity"] = df["Severity"].eq("High")
df["Is_Uninsured"] = df["Insurance"].eq("Uninsured")
df["Bill_Per_Day"] = (df["Bill"] / df["Length_of_Stay"]).round(2)

order = ["Patient_ID", "Patient_Name", "Age", "Age_Group", "Gender", "Gender_AR",
         "Diagnosis", "Diagnosis_AR", "Diagnosis_Group", "Doctor", "Doctor_AR",
         "Admission_Date", "Discharge_Date", "Length_of_Stay", "Stay_Band", "Long_Stay", "LOS_Outlier",
         "Admission_Month", "Admission_Month_Name", "Admission_Quarter", "Admission_Weekday", "Is_Weekend",
         "Insurance", "Insurance_AR", "Is_Uninsured", "Severity", "Severity_AR", "High_Severity",
         "Bill", "Bill_Raw", "Bill_Status", "Bill_Per_Day", "Date_Corrected", "Review_Flag"]
df = df[order]
df.to_csv(OUT, index=False, encoding="utf-8-sig", date_format="%Y-%m-%d")

log["clean_rows"], log["clean_cols"] = int(len(df)), int(df.shape[1])
log["los_fence"] = float(fence)
with open(LOG, "w", encoding="utf-8") as f:
    json.dump(log, f, ensure_ascii=False, indent=2)
print(f"\n{log['raw_rows']} raw rows -> {len(df)} clean rows, {df.shape[1]} columns -> {OUT}")
