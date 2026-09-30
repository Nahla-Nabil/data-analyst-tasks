# Power BI Guide: the customer dashboard in Power BI

## 0. The report: `Customer_Dashboard.pbix` (source project: `PowerBI/Customer_Dashboard.pbip`)

`Customer_Dashboard.pbix` is the finished report, with the data included (196 KB). Double-click it to open it in Power BI Desktop.
It was saved from the project described below.

`build_powerbi.py` generates a complete Power BI project (PBIP):
- a Power Query load of `Cleaned_Customers.csv`
- a `Calendar` table and a small `Field Quality` helper table
- 30 DAX measures
- a 5-page report: **Overview, Customers & Categories, Ratings, Data Quality, Insights**, with 6 synced drop-down slicers (Year, Gender, Age group, Category, Order size, Rating), 12 KPI cards, the charts and a category scorecard

The project was opened in Power BI Desktop (2.157) and refreshed with no load errors. Every KPI was then checked against the Python analysis by querying the model with DAX (section 4).
Screenshots of all five pages are in `screenshots/powerbi_*.png`.

**To create the `.pbix` from the project (about 30 seconds):**
1. Double-click `PowerBI/Customer_Dashboard.pbip`. It opens in Power BI Desktop.
2. Click **Refresh now** on the yellow bar. The project stores no data, so this loads the CSV.
3. **File → Save as → Browse this device**. Set *Save as type* to **Power BI file (\*.pbix)**, and save as `Customer_Dashboard.pbix` in `Task 9`.

The CSV path is written into the query as an absolute path (`C:\Users\nahla\Desktop\VOLTIX\Task 9\Cleaned_Customers.csv`). If the folder moves,
rerun `python build_powerbi.py`, or edit the path under Transform data → Source.

## 1. Model

| Table | Source | Purpose |
|---|---|---|
| `Customers` | Power Query: `Cleaned_Customers.csv`. Blanks become null, then types are set (Age, Year, Month_Num, Weekday_Num, Rating as whole numbers; Purchase_Amount as a decimal; Purchase_Date as a date) | One row per customer / purchase |
| `Calendar` | DAX: `ADDCOLUMNS ( CALENDAR ( DATE(2022,10,27), DATE(2025,7,23) ), "Year", ..., "Month_Num", ..., "Month", ..., "Year_Month", ... )` | Year slicer, days of data per month |
| `Field Quality` | Power Query `#table`: 7 fields × 3 statuses (Usable / Blank / Invalid) | Axis and legend for the data-quality chart (not related to other tables) |

Relationship: `Customers[Purchase_Date]` (many) → `Calendar[Date]` (one), single direction. The Year slicer uses `Calendar[Year]`, so it also limits the days used by
*Purchases per 30 Days*. Purchases with an invalid date (blank `Purchase_Date`) drop out as soon as a year is selected, the same behaviour as in the HTML dashboard.

Sort orders are built in Power Query, not as DAX columns (a DAX sort column derived from its own target is circular):
`AgeSort` for Age_Group, `BandSort` for Spend_Band, and `RatingBandSort` for Rating_Band (Dissatisfied → Neutral → Satisfied → No rating).
`Month_Name` is sorted by `Month_Num`, `Weekday` by `Weekday_Num`, `Calendar[Month]` by `Calendar[Month_Num]`, and `Field` / `Status` by their sort columns.

## 2. Measures

```DAX
Customers            = COUNTROWS ( Customers )
Revenue              = SUM ( Customers[Purchase_Amount] )                       // recorded amounts only
Priced Orders        = COUNT ( Customers[Purchase_Amount] )
AOV                  = AVERAGE ( Customers[Purchase_Amount] )
Median Order         = MEDIAN ( Customers[Purchase_Amount] )
Valid Ratings        = COUNT ( Customers[Rating] )                              // '10' and blanks were removed in cleaning
Rated                = VAR r = [Valid Ratings] RETURN IF ( r > 0, r )           // blank instead of 0 hides "No rating" in stacked bars
Avg Rating           = AVERAGE ( Customers[Rating] )
Satisfied %          = DIVIDE ( CALCULATE ( [Valid Ratings], Customers[Rating] >= 4 ), [Valid Ratings] )
Dissatisfied %       = DIVIDE ( CALCULATE ( [Valid Ratings], Customers[Rating] <= 2 ), [Valid Ratings] )
Net Satisfaction     = [Satisfied %] - [Dissatisfied %]
Rating Share         = VAR r = [Valid Ratings] RETURN IF ( r > 0, DIVIDE ( r, CALCULATE ( [Valid Ratings], ALLSELECTED ( Customers[Stars] ) ) ) )
Complete Records %   = DIVIDE ( CALCULATE ( [Customers], Customers[Complete_Record] = "Yes" ), [Customers] )
Usable Age %         = DIVIDE ( CALCULATE ( [Customers], Customers[Age_Status] = "Valid" ), [Customers] )
Customers with Age   = CALCULATE ( [Customers], Customers[Age_Status] = "Valid" )
Customer Share       = DIVIDE ( [Customers], CALCULATE ( [Customers], ALLSELECTED ( Customers ) ) )
Order Share          = DIVIDE ( [Priced Orders], CALCULATE ( [Priced Orders], ALLSELECTED ( Customers ) ) )
Revenue Share        = DIVIDE ( [Revenue], CALCULATE ( [Revenue], ALLSELECTED ( Customers ) ) )
Big Ticket Revenue % = DIVIDE ( CALCULATE ( [Revenue], Customers[Spend_Band] = "$750+" ), [Revenue] )
Unassigned Revenue % = DIVIDE ( CALCULATE ( [Revenue], Customers[Product_Category] = "Unknown" ), [Revenue] )

// Trend: only the 32 complete months (Oct 2022 and Jul 2025 are partial)
Full Months          = CALCULATE ( DISTINCTCOUNT ( 'Calendar'[Year_Month] ),
                           KEEPFILTERS ( 'Calendar'[Year_Month] >= "2022-11" && 'Calendar'[Year_Month] <= "2025-06" ) )
Purchases per Month  = DIVIDE ( CALCULATE ( [Customers], Customers[Full_Month] = "Yes" ), [Full Months] )
Revenue per Month    = DIVIDE ( CALCULATE ( [Revenue], Customers[Full_Month] = "Yes" ), [Full Months] )
Full-Month Revenue   = CALCULATE ( [Revenue], Customers[Full_Month] = "Yes" )
Full-Month Purchases = CALCULATE ( [Customers], Customers[Full_Month] = "Yes" )
Dated Purchases      = CALCULATE ( [Customers], Customers[Date_Status] = "Valid" )

// Seasonality: fair across months that occur in 2 or 3 years of the data window
Days of Data          = COUNTROWS ( 'Calendar' )
Purchases per 30 Days = DIVIDE ( [Customers], [Days of Data] ) * 30
H1 Revenue            = CALCULATE ( [Revenue], KEEPFILTERS ( 'Calendar'[Month_Num] IN { 1, 2, 3, 4, 5, 6 } ) )

// Data quality: one measure behind the 100% stacked bar (Field on the axis, Status in the legend)
Quality Rows =
VAR k = SELECTEDVALUE ( 'Field Quality'[Field] ) & "|" & SELECTEDVALUE ( 'Field Quality'[Status] )
RETURN SWITCH ( k,
    "Age|Usable",   CALCULATE ( [Customers], Customers[Age_Status] = "Valid" ),
    "Age|Blank",    CALCULATE ( [Customers], Customers[Age_Status] = "Missing" ),
    "Age|Invalid",  CALCULATE ( [Customers], Customers[Age_Status] IN { "Placeholder -1", "Placeholder 200" } ),
    ...                                                     // 16 combinations in total (see build_powerbi.py)
)
```

## 3. Report pages

| Page | Contents |
|---|---|
| **Overview** | 8 KPI cards · revenue per full month · revenue by category · % of orders vs % of revenue by order size · January–June revenue by year · purchases per 30 days by calendar month |
| **Customers & Categories** | Customers by age group (real ages only) · customers by gender · AOV by category · category scorecard (table) · purchases by weekday |
| **Ratings** | Rating distribution (1–5 stars) · rating mix (100% stacked: dissatisfied / neutral / satisfied) by category, by age group and by order size |
| **Data Quality** | Usable / blank / invalid values per field · 4 data-quality cards · age and rating values as recorded · cleaning decisions |
| **Insights** | Key findings and recommendations |

Colours match the HTML dashboard: main series `#2A78D6`, second series `#EB6834`, "Unknown" grey `#B9B7AE`, dissatisfied red `#E34948`, and satisfied blue `#2A78D6`.
Neutral uses a darker grey (`#8F8D85`), because Power BI always draws the labels inside stacked segments in white.

## 4. Check your numbers

With no filters, the cards must show: Customers **2,100** · Recorded revenue **$1.02M** · Avg order value **$510** · Purchases / month **59.9** · Avg rating **3.03** ·
Satisfied **39.3%** · Dissatisfied **38.7%** · Complete records **9.7%**.

Verified with DAX queries against the model (via the local Analysis Services instance that Power BI Desktop runs):
- Revenue **1,021,324.45**; January–June revenue **170,729.69 / 173,010.29 / 168,515.75** (2023 / 2024 / 2025)
- All 12 *Purchases per 30 Days* values and all 16 *Quality Rows* values match `analysis_output.txt`
- Year = 2024 → Purchases per Month **62.7** over **12** full months; Clothing + Female → **142** customers, AOV **$566**, rating **3.02**, the same as the HTML dashboard

Two DAX pitfalls were found and fixed during this check:
1. `Full Months` first filtered `'Calendar'[Date]`. Filtering the date column that is used in a relationship clears **all** filters on the Calendar table,
   so the Year slicer was ignored (2024 showed 23.5 purchases per month over 32 months). Filtering the text column `Year_Month` keeps the slicer.
2. `H1 Revenue` first used `'Calendar'[Month_Num] <= 6`. DAX treats a blank as 0, so the 118 purchases with an invalid date passed the test and appeared
   as a *(Blank)* year. `IN { 1, 2, 3, 4, 5, 6 }` excludes blanks.
