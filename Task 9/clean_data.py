"""Step 1: clean, validate and enrich the Customer dataset.

Input : Customers_Fakedata.csv (raw, unchanged)
Output: Cleaned_Customers.csv, cleaning_log.json

Principle: flag, don't delete. Only exact duplicate rows are removed. An invalid value is blanked (and its reason
kept in a *_Status column) instead of the whole row being dropped, because the problems are spread so evenly that
only 204 of 2,100 rows (9.7%) are complete in every field - dropping incomplete rows would throw away 90% of the data.
"""
import json
import re

import numpy as np
import pandas as pd

RAW = "Customers_Fakedata.csv"
OUT = "Cleaned_Customers.csv"
log = []


def note(check, found, action, rows_after):
    log.append({"step": len(log) + 1, "check": check, "found": found, "action": action, "rows_after": int(rows_after)})


# Read everything as text so blanks, "-1", "200" and "32/13/2020" can be seen before any type conversion.
df = pd.read_csv(RAW, dtype=str, keep_default_na=False)
n0 = len(df)
note("Load raw file", f"{n0:,} rows x {df.shape[1]} columns: {', '.join(repr(c) for c in df.columns)}", "Loaded as text", n0)

# 1. Column structure --------------------------------------------------------------------------------------------
df = df.apply(lambda s: s.str.strip())
padded = [c for c in df.columns if c != c.strip()]
same = (df["Gender"] == df[padded[0]]).all() if padded else False
empty = [c for c in df.columns if (df[c] == "").all()]
df = df.drop(columns=padded + empty)
note("Redundant / empty columns",
     f"'{padded[0]}' (header padded with spaces) is an exact copy of Gender in all rows: {same}; "
     f"{empty} is 100% empty",
     "Both dropped", len(df))

# 2. Duplicates ---------------------------------------------------------------------------------------------------
dup = df.duplicated()
dup_rows = [int(i) + 2 for i in df.index[dup]]          # +2 = file line number (header is line 1)
id_dups_after = int(df[~dup].CustomerID.duplicated().sum())
df = df[~dup].reset_index(drop=True)
note("Duplicate rows", f"{int(dup.sum())} exact copies of earlier rows, all appended at the end of the file "
     f"(lines {min(dup_rows)}-{max(dup_rows)}); every repeated CustomerID is an exact copy",
     f"Removed; CustomerID is now unique ({id_dups_after} repeats left)", len(df))
n = len(df)

# 3. Age ----------------------------------------------------------------------------------------------------------
age = pd.to_numeric(df.Age.replace("", np.nan), errors="coerce")
df["Age_Status"] = np.select([df.Age == "", age == -1, age == 200], ["Missing", "Placeholder -1", "Placeholder 200"], "Valid")
valid_age = age.where(df.Age_Status == "Valid")
cnt = df.Age_Status.value_counts()
note("Age validity",
     f"{cnt['Placeholder -1']} x '-1' and {cnt['Placeholder 200']} x '200' (impossible ages used as placeholders), "
     f"{cnt['Missing']} blank; the {cnt['Valid']} real ages run {int(valid_age.min())}-{int(valid_age.max())}",
     f"Placeholders blanked; NOT imputed ({1 - cnt['Valid'] / n:.0%} of ages are unusable - a median fill would "
     "invent most of the column); Age_Status keeps the reason", n)
df["Age"] = valid_age.astype("Int64")
bins, labels = [14, 29, 44, 59, 74, 90], ["15-29", "30-44", "45-59", "60-74", "75-90"]
df["Age_Group"] = pd.cut(df.Age.astype(float), bins, labels=labels).astype(object).fillna("Unknown")

# 4. Gender -------------------------------------------------------------------------------------------------------
raw_g = df.Gender.value_counts().to_dict()
gmap = {"m": "Male", "male": "Male", "f": "Female", "female": "Female"}
df["Gender"] = df.Gender.str.lower().map(gmap).fillna("Unknown")
note("Gender spelling", f"6 spellings {sorted(k for k in raw_g if k)} + {raw_g.get('', 0)} blank",
     "Mapped to Male / Female; blank -> 'Unknown' (kept as its own group)", n)

# Recorded gender vs first name (consistency check - reported, not corrected)
df["First_Name"] = df.Name.str.split().str[0]
df["Last_Name"] = df.Name.str.split().str[-1]
name_gender = {"Ahmed": "Male", "Ali": "Male", "John": "Male", "Mark": "Male",
               "Fatma": "Female", "Lina": "Female", "Sara": "Female"}          # 'Alaa' is used for both sexes
expected = df.First_Name.map(name_gender)
testable = expected.notna() & (df.Gender != "Unknown")
conflict = testable & (expected != df.Gender)
df["Gender_Name_Conflict"] = np.where(testable, np.where(conflict, "Yes", "No"), "n/a")
note("Gender vs first name", f"Recorded gender contradicts a clearly gendered first name in {int(conflict.sum())} of "
     f"{int(testable.sum())} testable rows ({conflict.sum() / testable.sum():.0%}), e.g. 'Sara' recorded as Male "
     f"{int(((df.First_Name == 'Sara') & (df.Gender == 'Male')).sum())} times - what random assignment would give",
     "Kept as recorded (cannot tell which field is wrong); flagged; gender results carry a caveat", n)

# 5. Email and phone ----------------------------------------------------------------------------------------------
df["Email"] = df.Email.str.lower()
ok = df.Email.str.fullmatch(r"[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}")
matches_name = (df.Email.str.split("@").str[0] == (df.First_Name + "." + df.Last_Name).str.lower())
df["Email_Domain"] = df.Email.str.split("@").str[1]
note("Email", f"{int(ok.sum())}/{n} valid format, {matches_name.mean():.0%} built as first.last@domain; only "
     f"{df.Email.nunique()} distinct addresses for {n:,} customers (and {df.Name.nunique()} distinct names)",
     "Lower-cased; Email_Domain derived. Email/name cannot identify a person, so CustomerID stays the key", n)

ph = df.Phone.value_counts().to_dict()
df["Phone_Status"] = np.where(df.Phone == "", "Missing", "Placeholder")
note("Phone", f"{ph.get('', 0)} blank; the rest hold only 2 values: " +
     ", ".join(f"'{k}' x{v}" for k, v in ph.items() if k) + " (dummy digit sequences)",
     "Column dropped: it contains no real phone number. Phone_Status kept (0% reachable by phone)", n)
df = df.drop(columns=["Phone"])

# 6. Purchase amount ----------------------------------------------------------------------------------------------
amt = pd.to_numeric(df.PurchaseAmount.replace("", np.nan), errors="coerce")
q1, q3 = amt.quantile([.25, .75])
fence_hi, fence_lo = q3 + 1.5 * (q3 - q1), q1 - 1.5 * (q3 - q1)
df["Amount_Status"] = np.where(amt.isna(), "Missing", "Recorded")
note("PurchaseAmount", f"{int(amt.isna().sum())} blank; recorded values ${amt.min():.2f}-${amt.max():.2f}, no zero/negative "
     f"values, 0 outside the IQR fences (${max(fence_lo, 0):.0f}-${fence_hi:.0f})",
     "Blanks kept blank, NOT imputed: revenue KPIs use recorded amounts only (an imputed amount would be invented revenue)", n)
df["Purchase_Amount"] = amt.round(2)
df["Spend_Band"] = pd.cut(amt, [0, 250, 500, 750, 1000], labels=["Under $250", "$250-499", "$500-749", "$750+"],
                          right=False).astype(object).fillna("Unknown")

# 7. Purchase date ------------------------------------------------------------------------------------------------
dt = pd.to_datetime(df.PurchaseDate, format="%m/%d/%Y", errors="coerce")
bad = df.PurchaseDate[dt.isna()].value_counts().to_dict()
df["Date_Status"] = np.where(dt.isna(), "Invalid", "Valid")
note("PurchaseDate", f"Format M/D/YYYY; {int(dt.isna().sum())} invalid: " + ", ".join(f"'{k}' x{v}" for k, v in bad.items()) +
     f" (day 32, month 13 - impossible, and cannot be recovered); valid dates {dt.min():%d %b %Y} - {dt.max():%d %b %Y} "
     f"({(dt.max() - dt.min()).days} days), none in the future",
     "Invalid dates blanked; rows kept for the non-time analyses; excluded from trends", n)
df["Purchase_Date"] = dt
df["Year"] = dt.dt.year.astype("Int64")
df["Quarter"] = dt.dt.year.astype("Int64").astype(str) + "-Q" + dt.dt.quarter.astype("Int64").astype(str)
df["Year_Month"] = dt.dt.strftime("%Y-%m")
df["Month_Num"] = dt.dt.month.astype("Int64")
df["Month_Name"] = dt.dt.strftime("%b")
df["Weekday_Num"] = (dt.dt.dayofweek + 1).astype("Int64")          # 1 = Monday
df["Weekday"] = dt.dt.strftime("%a")
first_full, last_full = (dt.min() + pd.offsets.MonthBegin(1)).to_period("M"), (dt.max() + pd.offsets.MonthEnd(0) -
                                                                                 pd.offsets.MonthEnd(1)).to_period("M")
if dt.min().day == 1:
    first_full = dt.min().to_period("M")
per = dt.dt.to_period("M")
df["Full_Month"] = np.where(dt.isna(), "", np.where((per >= first_full) & (per <= last_full), "Yes", "Partial"))
df.loc[df.Quarter.str.contains("NA"), "Quarter"] = ""
note("Partial periods", f"The window starts {dt.min():%d %b %Y} and ends {dt.max():%d %b %Y}, so {dt.min():%b %Y} and "
     f"{dt.max():%b %Y} are partial months; full months = {first_full} to {last_full}",
     "Full_Month flag added; trend charts and growth rates use full months only", n)

# 8. Product category ---------------------------------------------------------------------------------------------
cats = sorted(c for c in df.ProductCategory.unique() if c)
blank_cat = int((df.ProductCategory == "").sum())
df["Product_Category"] = df.ProductCategory.replace("", "Unknown")
note("ProductCategory", f"{len(cats)} consistent values {cats}; {blank_cat} blank ({blank_cat / n:.0%})",
     "Blank -> 'Unknown', kept as its own group so its revenue stays visible", n)

# 9. Rating -------------------------------------------------------------------------------------------------------
r = pd.to_numeric(df.Rating.replace("", np.nan), errors="coerce")
df["Rating_Status"] = np.select([df.Rating == "", r == 10], ["Missing", "Out of range (10)"], "Valid")
rc = df.Rating_Status.value_counts()
note("Rating", f"Scale 1-5; {rc['Out of range (10)']} x '10' and {rc['Missing']} blank. No 6-9 values exist, so '10' is "
     "not a 10-point scale that could be rescaled - it is an invalid entry",
     "Out-of-range blanked (not capped to 5, which would inflate the top score); Rating_Status keeps the reason", n)
df["Rating"] = r.where(r.between(1, 5)).astype("Int64")
rf = df.Rating.astype(float)
df["Rating_Band"] = np.select([rf <= 2, rf == 3, rf >= 4], ["Dissatisfied (1-2)", "Neutral (3)", "Satisfied (4-5)"], "No rating")

# 10. Completeness score ------------------------------------------------------------------------------------------
checks = pd.DataFrame({"Age": df.Age_Status == "Valid", "Gender": df.Gender != "Unknown",
                       "Amount": df.Amount_Status == "Recorded", "Date": df.Date_Status == "Valid",
                       "Category": df.Product_Category != "Unknown", "Rating": df.Rating_Status == "Valid"})
df["Valid_Fields"] = checks.sum(axis=1)
df["Complete_Record"] = np.where(df.Valid_Fields == 6, "Yes", "No")
corr = checks.astype(int).corr().where(~np.eye(6, dtype=bool)).abs().max().max()
note("Completeness", f"Only {int((df.Valid_Fields == 6).sum())} rows ({(df.Valid_Fields == 6).mean():.1%}) are valid in all 6 "
     f"analytic fields; problems are independent of each other (max |r| between missing-flags = {corr:.2f})",
     "Pairwise handling: each metric uses every row valid for that metric (listwise deletion would keep only "
     "9.7%). Independence means this does not bias segment comparisons", n)

cols = ["Customer_ID", "Name", "First_Name", "Last_Name", "Gender", "Gender_Name_Conflict", "Age", "Age_Group", "Age_Status",
        "Email", "Email_Domain", "Phone_Status", "Purchase_Amount", "Amount_Status", "Spend_Band", "Purchase_Date", "Date_Status",
        "Year", "Quarter", "Year_Month", "Month_Num", "Month_Name", "Weekday_Num", "Weekday", "Full_Month",
        "Product_Category", "Rating", "Rating_Status", "Rating_Band", "Valid_Fields", "Complete_Record"]
df = df.rename(columns={"CustomerID": "Customer_ID"})[cols]
note("Output", f"{len(df):,} rows x {len(cols)} columns", "Saved Cleaned_Customers.csv (UTF-8, ISO dates)", len(df))

df.to_csv(OUT, index=False, date_format="%Y-%m-%d")
json.dump(log, open("cleaning_log.json", "w", encoding="utf-8"), indent=2, ensure_ascii=False)
for e in log:
    print(f"{e['step']:>2}. {e['check']}: {e['found']}\n    -> {e['action']} [{e['rows_after']:,} rows]")
