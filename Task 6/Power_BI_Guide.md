# Power BI Guide - rebuild `Weather_Dashboard.html` as a native Power BI report

`Weather_Dashboard.html` (Plotly, works offline) is the delivered interactive dashboard. If the submission must be a Power BI file, this guide
reproduces it in about 20 minutes from `Cleaned_Weather.csv` (3,271 rows, 51 columns). No `.pbix` is included - it has to be authored in Power BI Desktop.

## 1. Load and type the data

1. Home -> Get Data -> Text/CSV -> `Cleaned_Weather.csv` -> Transform Data.
2. Types: `Date` = Date; `Year`, `Month`, `Quarter`, `DayOfYear`, `IsRainDay`, `RainToday_Flag`, `RainTomorrow_Flag`, `IsAnomaly` = Whole number;
   temperatures, `Rainfall`, `Sunshine`, `Evaporation`, `Pressure*`, `*_Z` = Decimal number; `Season`, `MonthName`, `YearMonth`, `WindGustDir`, `WindDir*`,
   `RainCategory`, `HeatCategory`, `GustCategory`, `AnomalyType` = Text.
3. **Leave the blanks alone.** `WindGustSpeed`, `WindGustDir` (first 957 days) and `Cloud9am`, `Cloud3pm` (520 days) are empty on purpose - the source held
   constant placeholders there (see `DATA_QUALITY_REPORT.md`). Power BI treats them as null and averages skip them, which is the correct behaviour.
4. Close & Apply.

## 2. Sort orders (so charts do not sort alphabetically)

Modeling -> New column, then Column tools -> Sort by column:

```DAX
MonthSort  = MONTH ( 'Cleaned_Weather'[Date] )                 // sort MonthName by MonthSort
SeasonSort = SWITCH ( 'Cleaned_Weather'[Season], "Summer", 1, "Autumn", 2, "Winter", 3, "Spring", 4 )   // sort Season by SeasonSort
DirSort    = SWITCH ( 'Cleaned_Weather'[WindGustDir], "N",1,"NNE",2,"NE",3,"ENE",4,"E",5,"ESE",6,"SE",7,"SSE",8,"S",9,"SSW",10,"SW",11,"WSW",12,"W",13,"WNW",14,"NW",15,"NNW",16 )
```

Also create a **Date table** (`Calendar = CALENDAR ( DATE(2008,2,1), DATE(2017,6,25) )`), relate `Calendar[Date]` to `Cleaned_Weather[Date]`, and use it on time axes.
Months with no data (Apr 2011, Dec 2012, Feb 2013) will then show as gaps, not zeros.

## 3. Measures

```DAX
Days            = COUNTROWS ( Cleaned_Weather )
Avg Max Temp    = AVERAGE ( Cleaned_Weather[MaxTemp] )
Avg Min Temp    = AVERAGE ( Cleaned_Weather[MinTemp] )
Avg Humidity 3pm = AVERAGE ( Cleaned_Weather[Humidity3pm] )
Avg Gust        = AVERAGE ( Cleaned_Weather[WindGustSpeed] )
Total Rainfall  = SUM ( Cleaned_Weather[Rainfall] )
Rain Day %      = DIVIDE ( SUM ( Cleaned_Weather[IsRainDay] ), [Days] )
Hot Days 30     = CALCULATE ( [Days], Cleaned_Weather[MaxTemp] >= 30 )
Extreme Heat 35 = CALCULATE ( [Days], Cleaned_Weather[MaxTemp] >= 35 )
Heavy Rain Days = CALCULATE ( [Days], Cleaned_Weather[Rainfall] > 25 )
Heavy Rain Share of Total = DIVIDE ( CALCULATE ( [Total Rainfall], Cleaned_Weather[Rainfall] > 25 ), [Total Rainfall] )
Anomaly Days    = SUM ( Cleaned_Weather[IsAnomaly] )
Anomaly %       = DIVIDE ( [Anomaly Days], [Days] )
Rain Tomorrow % = DIVIDE ( SUM ( Cleaned_Weather[RainTomorrow_Flag] ), [Days] )
Rain Tomorrow % | Rain Today = CALCULATE ( [Rain Tomorrow %], Cleaned_Weather[RainToday_Flag] = 1 )
Rain Tomorrow % | Dry Today  = CALCULATE ( [Rain Tomorrow %], Cleaned_Weather[RainToday_Flag] = 0 )
Max Temp Anomaly (vs same month) =
    VAR m = SELECTEDVALUE ( Cleaned_Weather[Month] )
    RETURN [Avg Max Temp] - CALCULATE ( [Avg Max Temp], ALL ( Cleaned_Weather ), Cleaned_Weather[Month] = m )
```

## 4. Report page (mirrors the HTML)

| Visual | Fields |
|---|---|
| 8 KPI cards | Avg Max Temp, Avg Min Temp, Avg Humidity 3pm, Avg Gust, Total Rainfall, Rain Day %, Hot Days 30, Anomaly Days |
| Line chart "Monthly max/min" | Calendar[Date] (month level) x Avg Max Temp, Avg Min Temp |
| Clustered column "Seasonal cycle" | MonthName (sorted) x Avg Max Temp, Avg Min Temp |
| Box plot / candlestick alternative | Season x MaxTemp (use the *Box and Whisker* custom visual, or a column chart of Avg Max Temp by Season) |
| Matrix heat map | Rows `Year`, columns `MonthName`, values `Max Temp Anomaly (vs same month)` with diverging conditional formatting (blue - grey - orange, centre 0) |
| Column chart "Rain by month" | MonthName x Rain Day % |
| Clustered column "Rain intensity" | `RainCategory` x `Days`, plus % of total rainfall |
| Filled/Radar "Wind rose" | `WindGustDir` (sorted by DirSort) x Days - use the *Radar* visual or a column chart |
| Bar chart "Rain days by gust direction" | `WindGustDir` x Rain Day %  (sort descending) |
| Line chart "Daily max temp" | Calendar[Date] x MaxTemp; add a second series filtered to `AnomalyType` contains "Heat" for the red markers |
| Table "Most unusual days" | Date, AnomalyType, MaxTemp, Rainfall, WindGustSpeed, WindGustDir - filter `IsAnomaly` = 1 |
| Slicers | Year, Season (tiles), plus cross-filtering from the wind and month charts (Power BI does this by default) |

Add a text box with the two data caveats from `KEY_INSIGHTS.md` (single unnamed location; placeholder blocks removed) on the page.
