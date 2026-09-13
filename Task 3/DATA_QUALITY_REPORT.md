# Data Quality Report — HR Employee Attrition

Source file: `WA_Fn-UseC_-HR-Employee-Attrition.csv`
Raw shape: **1470 rows x 35 columns**

## 1. Duplicates
- Fully duplicated rows: **0**
- Duplicate `EmployeeNumber` values: **0**

## 2. Missing values
- No missing values in any column.

## 3. Constant columns (no analytical value)
- `EmployeeCount` = `1` for all 1470 rows -> dropped
- `Over18` = `Y` for all 1470 rows -> dropped
- `StandardHours` = `80` for all 1470 rows -> dropped

## 4. Range / consistency checks
- Age outside 18-65: OK
- EnvironmentSatisfaction outside 1-4 scale: OK
- JobInvolvement outside 1-4 scale: OK
- JobSatisfaction outside 1-4 scale: OK
- RelationshipSatisfaction outside 1-4 scale: OK
- WorkLifeBalance outside 1-4 scale: OK
- PerformanceRating outside 1-4 scale: OK
- MonthlyIncome <= 0: OK
- YearsAtCompany > TotalWorkingYears (impossible): OK
- YearsInCurrentRole > YearsAtCompany (impossible): OK
- YearsWithCurrManager > YearsAtCompany (impossible): OK

## 5. Data types
- All numeric columns loaded as int64, all categorical columns as object/string — no dtype coercion needed.

## 6. Actions taken
- Dropped 0 exact duplicate row(s).
- Dropped 3 constant column(s): `EmployeeCount`, `Over18`, `StandardHours`.
- Added engineered columns for analysis: `AttritionFlag`, `IncomeBand`, `AgeGroup`, `TenureBand`.
- Final cleaned shape: **1470 rows x 36 columns** -> `Cleaned_HR_Attrition.csv`

## Conclusion
This dataset arrived in good shape: no missing values, no duplicate rows, and no logically impossible values were found. The only real cleaning step was removing 4 constant/no-signal columns (`EmployeeCount`, `Over18`, `StandardHours`, `StandardHours`-like) that carry no analytical value, and adding a few grouped/derived columns to make the Power BI dashboard and charts easier to build (age bands, income bands, tenure bands, a numeric Attrition flag).