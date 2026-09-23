# Tableau version of the hospital dashboard

`Hospital_Dashboard.twbx` is a packaged Tableau workbook, meaning the workbook and its data extract are in one file. It opens in Tableau Desktop or the
free **Tableau Public** (double-click it). The data is `Hospital.hyper`: the same 247 rows as `Cleaned_Hospital_Data.csv`, plus four sort-helper columns.
Placeholder bills are real NULLs, so every average skips them.

## What is inside

| Dashboard | Sheets |
|---|---|
| **Overview** | 8 KPI tiles, key-insights text, admissions by month, admissions by weekday, share of admissions vs share of bed-days by stay length, length-of-stay distribution (orange = over 7 days) |
| **Case Mix & Length of Stay** | admissions by diagnosis, ALOS by diagnosis, severity mix within each diagnosis (heat map, % of row), ALOS by age group, ALOS by severity, admissions by insurance |
| **Doctors & Billing** | ALOS by doctor, share of admissions vs bed-days by doctor, billing status (genuine vs placeholder bills), genuine bill vs length of stay |
| **Clinical Review** | the 24 records flagged during cleaning, with their length of stay |

**Interactivity**
- **Six drop-down filters** sit on every dashboard: Quarter, Doctor, Diagnosis, Insurance, Severity and Age group. Each one is attached to all 23
  sheets in one filter group, so a choice filters every KPI and chart.
- **Click-to-filter actions:** clicking a bar (month, weekday, diagnosis, age group, severity, insurance, doctor, billing status) filters the rest of that
  dashboard. Clicking it again clears the filter.

**Calculated fields:** Admissions, Long-Stay Rate, High-Severity Share, Uninsured Rate, Billing Completeness, Review Flags, Stay Class, plus shares that use
`EXCLUDE` LOD expressions so they respect the filters. For example, % of Bed-Days by stay band is
`SUM([Length_of_Stay]) / MIN({EXCLUDE [Stay_Band] : SUM([Length_of_Stay])})`.

## What was checked

I opened the workbook in Tableau Public 2025.1, inspected the log and took the screenshots in `screenshots/tableau_*.png`:
- It loads with no errors, and all 23 sheets and 4 dashboards render.
- The unfiltered KPIs match the HTML dashboard and the Excel workbook: 247 admissions, 6.3 days, 1,547 bed-days, 25.5%, 36.0%, 29.1%, 21.1% and 24 flagged records.
- **The shared filter was tested.** I built a copy with Doctor = Dr. Sara Ibrahim pre-selected. Every sheet then showed only her patients
  (24 admissions, ALOS 4.7), which matches the HTML dashboard (`screenshots/tableau_5_filter_test_dr_sara_ibrahim.png`).
- The click-to-filter actions are defined in the file, but I did not click through them with the mouse.

## Rebuild

```
pip install tableauhyperapi
python build_tableau.py      # Cleaned_Hospital_Data.csv -> Hospital.hyper
python build_twb.py          # -> Hospital_Dashboard.twbx (the .twb XML is generated in Python)
```
