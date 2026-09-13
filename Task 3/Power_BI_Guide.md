# Power BI Dashboard — Build Guide

**Data source:** `Cleaned_HR_Attrition.csv` (1,470 rows, 36 columns — already cleaned, banded columns included: `AgeGroup`, `IncomeBand`, `TenureBand`, `AttritionFlag`).

This guide reproduces `HR_Attrition_Dashboard.html` as a native Power BI report with drill-down/cross-filter behavior that the static HTML can't give you. Steps take ~15–20 minutes in Power BI Desktop.

## 1. Load & type the data

1. Home → Get Data → Text/CSV → select `Cleaned_HR_Attrition.csv` → Load.
2. In Power Query (Transform Data), set data types:
   - `Attrition`, `Department`, `JobRole`, `OverTime`, `BusinessTravel`, `MaritalStatus`, `Gender`, `EducationField`, `AgeGroup`, `IncomeBand`, `TenureBand` → **Text (categorical)**
   - `Age`, `MonthlyIncome`, `DailyRate`, `HourlyRate`, `MonthlyRate`, `DistanceFromHome`, `PercentSalaryHike`, `TotalWorkingYears`, `YearsAtCompany`, `YearsInCurrentRole`, `YearsSinceLastPromotion`, `YearsWithCurrManager`, `NumCompaniesWorked`, `TrainingTimesLastYear` → **Whole Number**
   - `EnvironmentSatisfaction`, `JobInvolvement`, `JobSatisfaction`, `RelationshipSatisfaction`, `WorkLifeBalance`, `PerformanceRating`, `JobLevel`, `StockOptionLevel`, `AttritionFlag` → **Whole Number**
3. Close & Apply.

## 2. Sort orders for banded columns (so charts don't sort alphabetically)

Create a sort-index column for each band (Modeling → New Column), then set "Sort by Column" (Column tools → Sort by Column) on the text column:

```DAX
AgeGroupSort =
SWITCH('Cleaned_HR_Attrition'[AgeGroup], "18-25",1, "26-35",2, "36-45",3, "46-55",4, "56-60",5)
```

```DAX
TenureBandSort =
SWITCH('Cleaned_HR_Attrition'[TenureBand], "0-2 yrs",1, "3-5 yrs",2, "6-10 yrs",3, "11-20 yrs",4, "20+ yrs",5)
```

After creating each: click the `AgeGroup` column in the Fields list → **Column tools** tab → **Sort by Column** → pick `AgeGroupSort`. Repeat for `TenureBand` with `TenureBandSort`.

## 3. DAX measures

Create these one at a time (Modeling → New Measure):

```DAX
Total Employees = COUNTROWS('Cleaned_HR_Attrition')

Employees Left = CALCULATE([Total Employees], 'Cleaned_HR_Attrition'[Attrition] = "Yes")

Attrition Rate = DIVIDE([Employees Left], [Total Employees])

Avg Monthly Income = AVERAGE('Cleaned_HR_Attrition'[MonthlyIncome])

Avg Job Satisfaction = AVERAGE('Cleaned_HR_Attrition'[JobSatisfaction])

Avg Tenure Years = AVERAGE('Cleaned_HR_Attrition'[YearsAtCompany])

Pct Overtime = DIVIDE(
    CALCULATE([Total Employees], 'Cleaned_HR_Attrition'[OverTime] = "Yes"),
    [Total Employees]
)

Avg Salary Hike % = AVERAGE('Cleaned_HR_Attrition'[PercentSalaryHike])
```

**Important:** after creating `Attrition Rate` and `Pct Overtime`, select each in the Fields list → **Measure tools** tab → **Format** = `Percentage`, 1 decimal.

## 4. Report layout (2 pages)

### Page 1 — Overview
- **KPI cards** (Card visual, one per measure): Total Employees, Attrition Rate, Avg Monthly Income, Avg Job Satisfaction, Pct Overtime, Avg Tenure Years.
- **Donut chart**: Legend = `Department`, Values = Total Employees.
- **Clustered bar**: Axis = `Department`, Values = Attrition Rate.
- **Clustered bar**: Axis = `JobRole`, Values = Attrition Rate, sorted descending — this is the sharpest chart in the report (Sales Representative at ~40% vs Research Director at ~2%).
- **Column chart**: Axis = `JobLevel`, Values = Avg Monthly Income.
- Add a **slicer** for `Department` and one for `Attrition` so every visual on the page cross-filters.

### Page 2 — Attrition Drivers
- **Column chart**: Axis = `OverTime`, Values = Attrition Rate (the single strongest driver: ~30.5% vs ~10.4%).
- **Column chart**: Axis = `JobSatisfaction`, Values = Attrition Rate.
- **Column chart**: Axis = `WorkLifeBalance`, Values = Attrition Rate.
- **Bar chart**: Axis = `BusinessTravel`, Values = Attrition Rate.
- **Bar chart**: Axis = `MaritalStatus`, Values = Attrition Rate.
- **Column chart**: Axis = `AgeGroup` (sorted via `AgeGroupSort`), Values = Attrition Rate.
- **Column chart**: Axis = `TenureBand` (sorted via `TenureBandSort`), Values = Attrition Rate.
- **Clustered column**: Axis = `Attrition`, Values = `JobSatisfaction`, `EnvironmentSatisfaction`, `RelationshipSatisfaction`, `WorkLifeBalance` (add all four as separate value fields, they'll average automatically) — shows the satisfaction gap between people who stayed vs. left.
- Add a **text box** with the headline insight: *"Overtime workers leave at ~3x the rate of everyone else — 30.5% vs 10.4%."*

### Formatting to match the theme used across submissions
- Report theme: single accent blue (`#2E75B6`), white cards, light-blue page background (`#EEF4FB`).
- All attrition-rate visuals formatted as percentage, 1 decimal.
- Enable **Data labels** on every bar/column chart.

## 5. Save / export
- File → Save As → `HR_Attrition_Dashboard.pbix`, saved inside this Task 3 folder.
- Optional: File → Export → Export to PDF for a static copy.
- Add the `.pbix` (and PDF if made) into `NahlaNabil.zip` before submitting.

---
*Every number in this guide (attrition rates, averages) was computed from the actual cleaned dataset — see `analysis_output.txt` to double-check any figure while you build.*
