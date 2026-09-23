# Data Quality Report: Hospital Analytics

**Source:** `Hospital Analytics.xlsx`, sheet *Data Before Cleaning*. It has 248 rows and 10 columns, with Arabic headers and values.
**Output:** `Cleaned_Hospital_Data.csv` (247 rows, 34 columns), plus the *Clean Data* sheet in `Hospital_Analytics_Clean.xlsx`.
**Script:** `clean_and_validate.py`. Every check below is re-run from the raw file, and each count is logged to `cleaning_log.json`.

## Summary

At first glance the file looks clean: it has **no blank cells**, the categories are spelled consistently, and every age is in a valid range.
The problems are hidden in values that *look* valid:

| # | Issue | Rows | Action |
|---|---|---:|---|
| 1 | Exact duplicate row (Excel row 23 repeats row 22) | 1 | Removed |
| 2 | Discharge date **before** admission date | 29 (11.7%) | Dates swapped; `Date_Corrected = TRUE` |
| 3 | Placeholder bills: **999** (×100) and **3852** (×95) | 195 (79%) | `Bill` set to blank; original kept in `Bill_Raw`; `Bill_Status` flag |
| 4 | Stays longer than 14 days for a minor condition (cold, flu, migraine, allergy) | 17 | Kept; `Review_Flag` |
| 5 | Unusual age for the diagnosis (stroke under 18, hypertension under 12) | 7 | Kept; `Review_Flag` |
| 6 | Very long stays (over 17 days, the IQR upper fence) | 18 | Kept; `LOS_Outlier` flag |
| 7 | Recorded gender disagrees with the first name | 131 (53%) | Reported only; cannot be corrected |
| 8 | Names are not unique: the same name appears with different ages and genders | 64 names | `Patient_ID` created per admission |

## 1. Missing values

No blank cells in any column, even after converting every column to its proper type. The real missing data is hidden in the bill column
as placeholder values (section 4).

## 2. Duplicates

One row is an exact copy of the row before it: same patient, dates, bill and every other field (Excel rows 22 and 23). The second copy was removed.
Duplicates were checked on all columns. Names alone cannot identify duplicates, because different people share a name (section 7).

## 3. Data types and date logic

- Types enforced: Age and Bill as whole numbers, both dates as dates (time part removed), and all text trimmed.
- **29 rows had the discharge date 1–5 days before the admission date.** Gaps of 1–5 days are the same size as normal stays (median 4 days),
  so this is a data-entry error where the two dates were typed into the wrong fields, not random bad values. The dates were swapped. Deleting these
  rows instead would have lost 12% of the data. The flag `Date_Corrected` lets anyone exclude them.
- After the swap, one stay runs from 31 Dec 2022 to 3 Jan 2023. It was kept. The 12-month charts count it under December.
- No same-day discharges. Length of stay is now 1–30 days for every row.

## 4. The bill column

| Evidence | Placeholder bills (999 / 3852) | Genuine bills |
|---|---|---|
| Count | 100 + 95 | 52 |
| Distinct values | 2 | 51 |
| Relationship with length of stay | none: the same value for 1-day and 30-day stays | **r = 0.64** (longer stay → higher bill) |
| Spread across diagnoses and severities | appears in all of them | varies |

Two values repeated 195 times across every diagnosis, severity, doctor and stay length cannot be real charges. `999` is a common "unknown" code,
and `3852` behaves the same way. **Decision:** set them to blank rather than impute. Imputing would mean inventing 79% of bills from 21%. Worse,
the genuine bills come almost only from short stays (94% are 7 days or less, and the longest is 12 days), so any imputation would have to guess
the price of 15–30-day stays with no data. Finance KPIs therefore use the 52 genuine bills and say so. The low **billing completeness (21%)** is
itself a finding for management.

## 5. Standardising values

- The categories were already consistent: 2 genders, 10 diagnoses, 7 doctors, 3 insurance types and 3 severity levels, with no spelling variants.
- Arabic labels were mapped to English (`Gender`, `Diagnosis`, `Doctor`, `Insurance`, `Severity`). The original Arabic stays in `*_AR` columns.
- `Severity` is an ordered category (Low < Medium < High) so it sorts correctly.

## 6. Unusual values: flagged, not deleted

- **Long-stay outliers:** 18 stays are above the IQR fence (Q3 + 1.5×IQR = 17 days). Long stays really happen and they drive bed demand,
  so deleting them would understate the workload. They are flagged in `LOS_Outlier`.
- **Minor condition, very long stay:** 17 cold, flu, migraine or allergy admissions lasted 15–28 days. That is clinically unusual. It could be a
  coding error, a missed diagnosis, or a patient who could not be discharged. These rows are flagged for review (listed on the dashboard).
- **Unusual age for the diagnosis:** a 12-year-old with a stroke, and six children aged 1–9 with hypertension. These are rare but possible, so they
  are flagged, not changed.
- Ages range from 1 to 90 and genuine bills from 503 to 6,763. No negative or zero values.

## 7. Consistency limits (cannot be fixed from this file)

- **Gender vs name:** the recorded gender disagrees with a clearly gendered first name (for example ياسمين recorded as *Male*, or يوسف as *Female*)
  in **131 of 247 rows (53%)**, which is what you would expect from random assignment. It is not possible to tell whether the name or the gender is
  wrong, so gender was left as recorded. The dashboard warns against drawing conclusions from gender.
- **No patient ID:** 75 names cover 247 admissions, and the same name comes with different ages and genders, so a name is not a person.
  `Patient_ID` (P0001…) was added as the admission key. **Readmission rate cannot be measured** until the source system records a real patient ID.

## 8. Calculated columns added

`Patient_ID`, `Length_of_Stay`, `Age_Group`, `Stay_Band`, `Long_Stay` (over 7 days), `LOS_Outlier`, `Diagnosis_Group`, `Admission_Month` / `_Month_Name` / `_Quarter` /
`_Weekday`, `Is_Weekend` (Friday–Saturday), `Is_Uninsured`, `High_Severity`, `Bill`, `Bill_Status`, `Bill_Per_Day`, `Date_Corrected`, `Review_Flag`.
Full definitions are on the *Data Dictionary* sheet of `Hospital_Analytics_Clean.xlsx`.

## Data quality scorecard (after cleaning)

| Dimension | Status |
|---|---|
| Completeness | Good for every field except Bill (21% genuine) |
| Uniqueness | Good: 0 duplicates, `Patient_ID` unique |
| Validity | Good: all dates in order, ages 1–90, stays 1–30 days |
| Consistency | Weak: gender vs name (53% mismatch); severity doesn't match stay length (see KEY_INSIGHTS.md) |
| Accuracy | 24 rows flagged for clinical review |
