# Power BI Guide: the hospital dashboard in Power BI

## 0. Ready-made report: `Hospital_Dashboard.pbix` (and its source project `PowerBI/Hospital_Dashboard.pbip`)

`Hospital_Dashboard.pbix` is the finished Power BI report with the data included. Double-click it to open it in Power BI Desktop.
It was saved from the project described below.

`build_powerbi.py` generates a complete Power BI project (PBIP). It has the Power Query load of the CSV, a Calendar table, 22 DAX measures,
sort orders, and a 5-page report: **Overview, Case Mix & LOS, Doctors & Billing, Clinical Review, Insights**. The report has 6 synced drop-down
slicers, 8 KPI cards, the charts, a severity matrix, a doctor scorecard and the review table. It was opened in Power BI Desktop (2.157)
and refreshed; the numbers match the HTML dashboard. Screenshots are in `screenshots/powerbi_*.png`.

**To regenerate the `.pbix` from the project (about 30 seconds):**
1. Double-click `PowerBI/Hospital_Dashboard.pbip`. It opens in Power BI Desktop.
2. Click **Refresh now** on the yellow bar. The project stores no data, so it loads the CSV.
3. **File → Save as → Browse this device**. Set *Save as type* to **Power BI file (\*.pbix)** and save as `Hospital_Dashboard.pbix` in `Task 7`.

The CSV path is written into the query as an absolute path (`C:\Users\nahla\Desktop\VOLTIX\Task 7\Cleaned_Hospital_Data.csv`). If the folder moves,
rerun `python build_powerbi.py`, or edit it under Transform data → Source.

The rest of this guide explains the model, so it can also be rebuilt by hand.

## 1. Load the data

1. Home → Get Data → Text/CSV → `Cleaned_Hospital_Data.csv` (UTF-8) → **Transform Data**.
2. Set types:
   - Date: `Admission_Date`, `Discharge_Date`
   - Whole number: `Age`, `Length_of_Stay`, `Admission_Month`, `Bill`, `Bill_Raw`
   - Decimal: `Bill_Per_Day`
   - True/False: `Long_Stay`, `LOS_Outlier`, `Is_Weekend`, `Is_Uninsured`, `High_Severity`, `Date_Corrected`
   - Text: everything else
3. Leave `Bill` blank where it is blank. Those rows held the placeholders 999/3852, and averages must skip them.
4. Rename the table to `Admissions` → Close & Apply.

## 2. Date table and sort orders

```DAX
Calendar = ADDCOLUMNS ( CALENDAR ( DATE ( 2022, 12, 31 ), DATE ( 2024, 1, 14 ) ),
    "Month", FORMAT ( [Date], "MMM" ), "MonthNo", MONTH ( [Date] ), "Weekday", FORMAT ( [Date], "ddd" ),
    "WeekdaySort", MOD ( WEEKDAY ( [Date] ) , 7 ) )          // Sat = 0 ... Fri = 6
```
Relate `Calendar[Date]` 1→* `Admissions[Admission_Date]` (active). Then set sort orders (Column tools → Sort by column):

```DAX
SeveritySort = SWITCH ( Admissions[Severity], "Low", 1, "Medium", 2, "High", 3 )
AgeSort      = SWITCH ( Admissions[Age_Group], "Child (0-17)", 1, "Adult (18-39)", 2, "Middle age (40-59)", 3, "Senior (60+)", 4 )
StaySort     = SWITCH ( Admissions[Stay_Band], "1-3 days", 1, "4-7 days", 2, "8-14 days", 3, "15+ days", 4 )
```
Sort `Calendar[Month]` by `MonthNo`, and `Calendar[Weekday]` by `WeekdaySort`.

## 3. Calculated columns (only if you start from the raw Excel file)

The cleaned CSV already contains them. If you work from `Hospital Analytics.xlsx` instead, apply the same cleaning:

```DAX
Length_of_Stay = ABS ( DATEDIFF ( Raw[Admission], Raw[Discharge], DAY ) )     // reversed dates -> swap
Bill_Clean     = IF ( Raw[Bill] IN { 999, 3852 }, BLANK (), Raw[Bill] )
Long_Stay      = Raw[Length_of_Stay] > 7
Age_Group      = SWITCH ( TRUE (), Raw[Age] <= 17, "Child (0-17)", Raw[Age] <= 39, "Adult (18-39)",
                                   Raw[Age] <= 59, "Middle age (40-59)", "Senior (60+)" )
```

## 4. Measures (Home → New measure; put them in a `_Measures` table)

```DAX
Admissions            = COUNTROWS ( Admissions )
Bed Days              = SUM ( Admissions[Length_of_Stay] )
ALOS                  = AVERAGE ( Admissions[Length_of_Stay] )
Median LOS            = MEDIAN ( Admissions[Length_of_Stay] )
Long Stay Rate        = DIVIDE ( CALCULATE ( [Admissions], Admissions[Long_Stay] = TRUE () ), [Admissions] )
Bed Days 15+ Share    = DIVIDE ( CALCULATE ( [Bed Days], Admissions[Length_of_Stay] >= 15 ), [Bed Days] )
High Severity Share   = DIVIDE ( CALCULATE ( [Admissions], Admissions[Severity] = "High" ), [Admissions] )
Senior Share          = DIVIDE ( CALCULATE ( [Admissions], Admissions[Age] >= 60 ), [Admissions] )
Uninsured Rate        = DIVIDE ( CALCULATE ( [Admissions], Admissions[Insurance] = "Uninsured" ), [Admissions] )
Billing Completeness  = DIVIDE ( COUNT ( Admissions[Bill] ), [Admissions] )
Avg Genuine Bill      = AVERAGE ( Admissions[Bill] )
Median Bill per Day   = MEDIAN ( Admissions[Bill_Per_Day] )
Date Correction Rate  = DIVIDE ( CALCULATE ( [Admissions], Admissions[Date_Corrected] = TRUE () ), [Admissions] )
Review Flag Rate      = DIVIDE ( CALCULATE ( [Admissions], Admissions[Review_Flag] <> BLANK () ), [Admissions] )
Admission Share       = DIVIDE ( [Admissions], CALCULATE ( [Admissions], ALLSELECTED ( Admissions ) ) )
Bed Day Share         = DIVIDE ( [Bed Days], CALCULATE ( [Bed Days], ALLSELECTED ( Admissions ) ) )
ALOS vs Hospital      = [ALOS] - CALCULATE ( [ALOS], ALL ( Admissions ) )

// Daily census: patients in a bed on each Calendar date (use on a line chart with Calendar[Date] on the axis)
Census =
VAR d = MAX ( Calendar[Date] )
RETURN CALCULATE ( [Admissions],
    REMOVEFILTERS ( Calendar ),                                      // ignore the Date relationship
    Admissions[Admission_Date] <= d, Admissions[Discharge_Date] > d )
Peak Census = MAXX ( VALUES ( Calendar[Date] ), [Census] )
Avg Census  = AVERAGEX ( FILTER ( VALUES ( Calendar[Date] ), YEAR ( Calendar[Date] ) = 2023 ), [Census] )
```
Formats: rates as % with 1 decimal, ALOS with 1 decimal, bills as whole numbers with a thousands separator.

## 5. Report layout (one page, 16:9)

| Area | Visual | Fields |
|---|---|---|
| Top row | **Slicers**: Month (between), Doctor, Diagnosis, Insurance, Severity, Age_Group, Gender (dropdown) | Calendar[Month], Admissions[...] |
| KPI row | 8 **Cards**: Admissions, ALOS (subtitle Median LOS), Bed Days, Long Stay Rate, Peak Census, High Severity Share, Uninsured Rate, Billing Completeness | measures |
| Demand | Clustered column: Admissions by Calendar[Month] · Column: Admissions by Weekday · Line: Census by Calendar[Date] (+ constant line = Avg Census) | |
| Capacity | Clustered column: Admission Share and Bed Day Share by Stay_Band | |
| Case mix | Bar: Admissions by Diagnosis · Bar: ALOS by Diagnosis (+ average line from the Analytics pane) · **Matrix**: Diagnosis × Severity, values = Admissions shown as % of row total, background colour scale | |
| LOS drivers | Column: ALOS by Age_Group · Column: ALOS by Severity · Column: Admissions by Length_of_Stay (conditional colour: Long_Stay) | |
| Doctors | Bar: ALOS by Doctor (+ average line) · **Table** scorecard: Doctor, Admissions, Admission Share, Bed Day Share, ALOS, Long Stay Rate, High Severity Share | |
| Billing | 100% stacked bar: Admissions by Bill_Status · Scatter: Bill vs Length_of_Stay (Bill not blank) with a trend line | |
| Review | Table: Patient_ID, Review_Flag, Diagnosis, Age, Length_of_Stay, Severity, Doctor (visual filter: Review_Flag is not blank) | |

Interactivity: Format → Edit interactions → keep **Filter** (not Highlight) from the slicers, and **Highlight** between the bar charts, so that clicking a
diagnosis or doctor cross-filters the page just like the HTML dashboard.

Colours (to match the HTML version): main series `#2A78D6`, second series `#EB6834`, dimmed/unselected `#CFD8E3`,
age/severity ramp `#86B6EF → #3987E5 → #1C5CAB → #0D366B`, placeholder bills greys `#B9B7AE` / `#8F8D85`.

## 6. Check your numbers

With no filters, the cards must show: Admissions **247** · ALOS **6.3** · Bed Days **1,547** · Long Stay Rate **25.5%** · Peak Census **13** ·
High Severity **36.0%** · Uninsured **29.1%** · Billing Completeness **21.1%** (Avg Genuine Bill **2,945**).
