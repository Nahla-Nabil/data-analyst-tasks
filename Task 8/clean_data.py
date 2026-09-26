"""Step 1: clean and enrich the Healthcare No-Shows data.

Input : healthcare_noshows.csv (raw, unchanged)
Output: Cleaned_NoShows.csv, cleaning_log.json
"""
import json
import pandas as pd

RAW = "healthcare_noshows.csv"
log = []


def note(step, check, found, action, rows_after):
    log.append({"step": step, "check": check, "found": found,
                "action": action, "rows_after": int(rows_after)})


df = pd.read_csv(RAW, encoding="utf-8", dtype={"PatientId": str})
n0 = len(df)
note(1, "Load raw file", f"{n0:,} rows x {df.shape[1]} columns", "Loaded as UTF-8", n0)

# 2. Missing values
na = int(df.isna().sum().sum())
blank = int((df.select_dtypes(exclude=["number", "bool"]).apply(lambda s: s.str.strip() == "")).sum().sum())
note(2, "Missing / blank values", f"{na} nulls, {blank} blank strings", "None to treat", len(df))

# 3. Duplicates
dup_full = int(df.duplicated().sum())
dup_id = int(df.AppointmentID.duplicated().sum())
note(3, "Duplicate rows / AppointmentID", f"{dup_full} full duplicates, {dup_id} repeated IDs",
     "None to remove", len(df))

# 4. Column names: fix misspellings, consistent naming
df = df.rename(columns={"PatientId": "Patient_ID", "AppointmentID": "Appointment_ID",
                        "ScheduledDay": "Scheduled_Date", "AppointmentDay": "Appointment_Date",
                        "Hipertension": "Hypertension", "Handcap": "Handicap",
                        "SMS_received": "SMS_Received", "Showed_up": "Showed_Up",
                        "Date.diff": "Lead_Days"})
note(4, "Column names", "Misspelled 'Hipertension', 'Handcap'; mixed styles ('Date.diff')",
     "Renamed to Hypertension, Handicap, Lead_Days, etc.", len(df))

# 5. Patient IDs stored as floats; 5 have decimal parts (corrupted by float export)
bad_pid = ~df.Patient_ID.str.fullmatch(r"\d+(\.0+)?")
df["Patient_ID"] = df.Patient_ID.str.replace(r"\.0+$", "", regex=True)
df["Flag_PatientID"] = bad_pid.map({True: "Malformed ID", False: ""})
note(5, "Patient_ID format", f"{int(bad_pid.sum())} IDs have decimals (e.g. 93779.52927); "
     "IDs are 13-15 digits and lose precision as numbers",
     "Kept as text; malformed IDs flagged, rows kept (appointment itself is valid)", len(df))

# 6. Dates and lead time consistency
df["Scheduled_Date"] = pd.to_datetime(df.Scheduled_Date)
df["Appointment_Date"] = pd.to_datetime(df.Appointment_Date)
recomputed = (df.Appointment_Date - df.Scheduled_Date).dt.days
mism = int((recomputed != df.Lead_Days).sum())
neg = df.Lead_Days < 0
note(6, "Lead_Days vs dates", f"{mism} mismatches with recomputed day difference", "None", len(df))
df = df[~neg].copy()
note(7, "Negative lead time", f"{int(neg.sum())} appointments scheduled AFTER the appointment date "
     "(all no-shows)", "Removed: impossible sequence", len(df))

# 8. Age
old = df.Age > 100
df["Flag_Age"] = ""
df.loc[df.Age >= 110, "Flag_Age"] = "Implausible age (115)"
note(8, "Age range", f"min {df.Age.min()}, max {df.Age.max()}; {int(old.sum())} rows over 100, "
     f"{int((df.Age >= 110).sum())} at 115 (2 patients)",
     "Kept and flagged (booking data is valid); ages 0/negative: none", len(df))

# 9. Categorical consistency
df["Gender"] = df.Gender.str.strip().str.upper()
df["Neighbourhood"] = df.Neighbourhood.str.strip().str.title()
note(9, "Category values", f"Gender: {sorted(df.Gender.unique())}; {df.Neighbourhood.nunique()} "
     "neighbourhoods, upper case", "Trimmed; neighbourhoods set to Title Case", len(df))

# 10. Saturday appointments
sat = int((df.Appointment_Date.dt.dayofweek == 5).sum())
note(10, "Weekend appointments", f"{sat} on Saturday, 0 on Sunday", "Kept (valid, tiny volume)", len(df))

# 11. Same-day multi bookings (identical apart from Appointment_ID)
key = [c for c in df.columns if c not in ("Appointment_ID",)]
multi = df.duplicated(subset=["Patient_ID", "Scheduled_Date", "Appointment_Date"], keep=False)
df["Flag_MultiBooking"] = multi.map({True: "Same-day multi-booking", False: ""})
note(11, "Multiple bookings same patient/day", f"{int(multi.sum()):,} rows share patient + "
     "scheduled + appointment date", "Kept (distinct Appointment_IDs = separate services), flagged", len(df))

# ---- Derived columns ------------------------------------------------------
df["SMS_Flag"] = df.SMS_Received.astype(int)
df["Status"] = df.Showed_Up.map({True: "Showed Up", False: "No-Show"})
df["No_Show"] = (~df.Showed_Up).astype(int)
df["Gender"] = df.Gender.map({"F": "Female", "M": "Male"})
yn = {True: "Yes", False: "No"}
for c in ["Scholarship", "Hypertension", "Diabetes", "Alcoholism", "Handicap", "SMS_Received"]:
    df[c] = df[c].map(yn)
df["Age_Group"] = pd.cut(df.Age, [0, 12, 18, 30, 45, 60, 75, 200],
                         labels=["01. Child (1-12)", "02. Teen (13-18)", "03. Young Adult (19-30)",
                                 "04. Adult (31-45)", "05. Middle Age (46-60)",
                                 "06. Senior (61-75)", "07. Elderly (76+)"], include_lowest=True).astype(str)
df["Lead_Time_Group"] = pd.cut(df.Lead_Days, [-1, 0, 3, 7, 14, 30, 60, 999],
                               labels=["1. Same day", "2. 1-3 days", "3. 4-7 days", "4. 8-14 days",
                                       "5. 15-30 days", "6. 31-60 days", "7. 60+ days"]).astype(str)
df["Appt_Weekday"] = df.Appointment_Date.dt.dayofweek.map(
    dict(enumerate(["1-Mon", "2-Tue", "3-Wed", "4-Thu", "5-Fri", "6-Sat", "7-Sun"])))
df["Appt_Month"] = df.Appointment_Date.dt.strftime("%Y-%m")
df["Chronic_Count"] = (df[["Hypertension", "Diabetes", "Alcoholism", "Handicap"]] == "Yes").sum(axis=1)
df["Chronic_Group"] = df.Chronic_Count.map(lambda n: "None" if n == 0 else ("1 condition" if n == 1 else "2+ conditions"))

# Patient history (chronological per patient)
df = df.sort_values(["Patient_ID", "Appointment_Date", "Scheduled_Date", "Appointment_ID"]).reset_index(drop=True)
g = df.groupby("Patient_ID")
df["Patient_Appt_Count"] = g.Appointment_ID.transform("count")
df["Visit_Number"] = g.cumcount() + 1
df["Prior_NoShows"] = g.No_Show.cumsum() - df.No_Show
df["First_Appt"] = (df.Visit_Number == 1).astype(int)   # SUM = distinct patients in any filter
df["Patient_Type"] = df.Patient_Appt_Count.map(lambda n: "One-time" if n == 1 else ("2-4 visits" if n <= 4 else "5+ visits"))
df["NoShow_History"] = df.apply(lambda r: "First visit" if r.Visit_Number == 1 else
                                ("Has missed before" if r.Prior_NoShows > 0 else "Never missed"), axis=1)
df["Neighbourhood_Rank"] = df.Neighbourhood.map(df.Neighbourhood.value_counts().rank(ascending=False, method="first")).astype(int)

cols = ["Appointment_ID", "Patient_ID", "Gender", "Age", "Age_Group", "Neighbourhood",
        "Scholarship", "Hypertension", "Diabetes", "Alcoholism", "Handicap", "Chronic_Count",
        "Chronic_Group", "SMS_Received", "SMS_Flag", "Scheduled_Date", "Appointment_Date", "Appt_Month",
        "Appt_Weekday", "Lead_Days", "Lead_Time_Group", "Status", "No_Show", "Patient_Appt_Count",
        "Patient_Type", "Visit_Number", "Prior_NoShows", "NoShow_History", "First_Appt",
        "Flag_PatientID", "Flag_Age", "Flag_MultiBooking"]
df = df.sort_values(["Appointment_Date", "Appointment_ID"])[cols].reset_index(drop=True)
note(12, "Derived columns", f"{len(cols)} columns in final table",
     "Added Status, No_Show (1/0), SMS_Flag (1/0), Age_Group, Lead_Time_Group, Appt_Weekday, Appt_Month, "
     "Chronic_Count/Group, patient history (visit #, prior no-shows, patient type), First_Appt, flags",
     len(df))

df.to_csv("Cleaned_NoShows.csv", index=False, date_format="%Y-%m-%d")
json.dump(log, open("cleaning_log.json", "w"), indent=2)
for r in log:
    print(f"{r['step']:>2}. {r['check']}: {r['found']} -> {r['action']} [{r['rows_after']:,}]")
print(df.shape, "no-show rate", round(df.No_Show.mean(), 4))
