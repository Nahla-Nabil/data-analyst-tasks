# Tableau version of the Weather dashboard

`Weather_Dashboard.twbx` is a packaged Tableau workbook (workbook + data extract in one file). It opens in **Tableau Desktop or the free
Tableau Public Desktop** - double-click it. The data is `Weather.hyper` (3,271 rows, same content as `Cleaned_Weather.csv` plus three sort helper
columns); wind-gust and cloud placeholder blocks are real NULLs, as in the cleaned CSV.

## What is inside

| Dashboard | Sheets |
|---|---|
| **Overview** | 8 KPI tiles, key-insights text, monthly max/min temperature, seasonal cycle by month, max temperature by season |
| **Temperature and Humidity** | max-temperature anomaly heat map (month x year, vs that month's average), humidity by month, chance of rain by 3pm humidity band |
| **Wind and Rainfall** | gust-direction frequency, rain days by gust direction, wind speed by month, monthly rainfall, rain days by month, rain intensity |
| **Unusual Events** | daily max temperature (heat anomalies highlighted), daily rainfall (extreme days highlighted), anomalous days per year, table of the 90 anomalous days |

Every dashboard has **Year** and **Season** drop-down filters that apply to every sheet (the same filter is on all 24 sheets). Click-to-filter
actions are defined on the month, season and gust-direction charts (Overview and Wind and Rainfall).

Calculated fields (Data pane): Rain Day %, Rain Today %, Rain Tomorrow %, Hot Days (max >= 30C), Anomaly Days, Max Temp Anomaly (vs same month)
[`AVG([MaxTemp]) - AVG({FIXED [Month] : AVG([MaxTemp])})`], Share of Total Rainfall, Share of Days, 3pm Humidity Band, Rain Class,
Heat Anomaly?, Extreme Rain?, Is Anomaly?.

## What was checked, and what was not

Checked by opening the workbook in Tableau Public 2025.1 (log inspected, screenshots taken):
- loads with **no schema/format errors**; all 24 sheets and 4 dashboards exist;
- charts render from the real data; KPI values match the HTML dashboard (23.0 / 14.9 °C, 55 %, 41.7 km/h, 10,932 mm, 26.0 %);
- Year / Season drop-downs appear on every dashboard; the anomaly table is filtered to the 90 anomalous days; the timelines highlight anomalies.

**Not** tested by clicking: the filter actions and the drop-down filtering behaviour (they are defined in the file, but I did not drive the mouse
through them). If a click does not filter, use Dashboard > Actions to check the five "Filter n" actions.

## Known cosmetic limits

- Tableau's built-in **temperature palette** is used for the heat map: green = cooler than that month's usual, orange/red = hotter (no blue/red).
- The two-colour daily charts use Tableau's default blue/orange; the chart titles say which colour means what.
- Tableau has no polar chart, so the wind rose is a bar chart (gust direction frequency, sorted N to NNW).
- KPI tiles use Tableau's default font size. Tableau Public 2025.1 may show a harmless "Update Tableau" pop-up when it starts.

## Rebuild

```
pip install tableauhyperapi
python clean_and_validate.py && python analysis.py     # data + summary numbers
python build_tableau.py                                 # Cleaned_Weather.csv -> Weather.hyper
python build_twb.py                                     # -> Weather_Dashboard.twbx (the .twb XML is generated in Python)
```
