# Task 6 - Data Quality Report

Source: `Weather_Data.csv` - 3,271 daily weather observations, 22 columns. Output: `Cleaned_Weather.csv` (3,271 rows, 51 columns).

## Bottom line

The raw file has **0 missing values, 0 duplicate rows, 0 duplicate dates and no impossible values** - but that is misleading, because the gaps were **already filled with constants** before the file was published. Two blocks were detected and blanked (see the table): wind gust speed/direction for **957 days** (Feb 2008 - Oct 2010) and cloud cover for **520 days** (Dec 2010 - Jun 2012). Left in, they would have made westerly winds look dominant (and gust-based 'anomalies' impossible in 2008-10). **No rows were dropped and no other value was changed or imputed.** Wind-gust analysis therefore covers 2,314 days and cloud analysis 2,751 days.

## Limitations that affect the analysis (read these first)

1. **No location field.** The brief asks about 'different cities and countries', but the file has no city, station or country column - it is one unnamed location. Comparing locations is therefore not possible and no location comparison is fabricated. The analysis compares **time periods** (year, season, month) and **wind-direction sectors** instead.
2. **Location is inferred, not stated.** The hottest day is 18 Jan 2013 at 45.8°C, which matches the Bureau of Meteorology's record for Sydney (Observatory Hill, 45.8°C, 18 Jan 2013), and the seasons are southern-hemisphere (hottest Dec-Feb). It is treated as **a single Australian (apparently Sydney) station**; seasons are labelled accordingly. Confirm with the data provider before quoting the city name.
3. **Uneven coverage.** 162 calendar days are missing, including 3 whole months (Apr 2011, Dec 2012, Feb 2013); Oct 2010 (18/31 days), Aug 2012 (24/31 days) are only partly covered. 2008 has no January and 2017 stops on 25 June. Because of this, annual rainfall *totals* are not comparable between years (2010-2013 are all incomplete) - the analysis uses percentages and per-day averages, and treats 2008 and 2017 as partial years. Monthly and seasonal averages use observed days only.
4. **Only ~9 years of data.** Any trend is a short-record observation, not a climate-change conclusion.

## Validation checks

| Check | Result | Action |
|---|---|---|
| Rows x columns | 3,271 x 22 | None needed |
| Missing values (all columns) | 0 (but see the constant-value blocks below - missing readings were pre-filled) | See below |
| Fully duplicated rows | 0 | None needed |
| Date format | m/d/yyyy (e.g. 2/1/2008 = 1 Feb 2008); parsed with explicit format, 0 failures | Converted to a real date; stored ISO yyyy-mm-dd |
| Duplicate dates | 0 | None needed |
| Chronological order | Yes | None needed |
| Calendar coverage | 01 Feb 2008 -> 25 Jun 2017: 3,271 of 3,433 days present, 162 missing. Longest gap: 31 days (01 Dec 2012 - 31 Dec 2012) | Kept as-is (no interpolation). Monthly/annual means use observed days only |
| Months with no data at all | 3: Apr 2011, Dec 2012, Feb 2013 | Left blank in charts (never filled with zero or interpolated); they are excluded from monthly/seasonal averages |
| Months with < 80% of days | Oct 2010 (18/31 days), Aug 2012 (24/31 days) | Kept; monthly totals for these months are understated |
| Partial years | 2008 starts 1 Feb (333 days, no January); 2017 ends 25 Jun (175 days) | Full-year comparisons are unreliable (see limitation 3); rates per day/percentages are used instead of totals |
| Wind-direction labels | 16 compass points in each of the 3 direction columns, no typos/variants | Whitespace-trimmed |
| Constant-value blocks (placeholder fill) - wind gust | 957 days (29.3%), 01 Feb 2008 - 04 Oct 2010: WindGustSpeed = 41 km/h and WindGustDir = W on every single day. Real gusts vary from day to day; the next-longest run of the same (speed, direction) pair anywhere else in the file is only a few days | Set WindGustSpeed and WindGustDir to missing for these days (flag `WindGust_Placeholder`); rows kept |
| Constant-value blocks (placeholder fill) - cloud cover | 520 days (15.9%), 24 Dec 2010 - 30 Jun 2012: Cloud9am = 5 and Cloud3pm = 4 on every single day | Set Cloud9am and Cloud3pm to missing for these days (flag `Cloud_Placeholder`); rows kept |
| Same scan on all other columns | Longest identical run: WindDir9am 16, WindDir3pm 9, WindSpeed9am 8, WindSpeed3pm 7 days (rainfall excluded: 0.0 mm can legitimately repeat) | None - no other placeholder blocks found |
| MinTemp > MaxTemp | 0 rows | None needed |
| Temp9am / Temp3pm above MaxTemp | 0 rows | None needed |
| Temp9am / Temp3pm below MinTemp | Temp9am: 0 rows; Temp3pm: 35 rows (1.1%) | Kept - physically possible (cold front / rainy afternoon cooler than the overnight minimum), flagged in `Temp3pm_BelowMin` |
| RainToday vs Rainfall | RainToday = 'Yes' <=> Rainfall > 1 mm holds for 3,271/3,271 rows (100%). The >= 1 mm rule would break 37 rows - all 37 days with exactly 1.0 mm are 'No' | Not an error: this is the dataset's rain-day definition. Adopted as `IsRainDay` |
| RainTomorrow vs next day's RainToday | Agree on 100.0% of 3,225 consecutive-day pairs | None needed - the label is internally consistent |
| Wind gust below a 9am/3pm wind speed | 0 rows | Kept - gust is the day's peak so this should not happen, but the gaps are tiny; noted only |
| Sunshine = 0 hours | 181 days (5.5%); 66% of them are rain days, mean 3pm cloud (where recorded) = 7.7/8 | Kept - consistent with overcast/rainy days, not a missing-value placeholder |
| Cloud cover above 8 oktas | Cloud9am: 1 row(s) at 9 (code for 'sky obscured'); Cloud3pm max = 8 | Kept - 9 is a valid BOM code; treated as 8 only if averaged (not used in KPIs) |
| Humidity outside 0-100 % | 0 rows | None needed |
| Value ranges plausible | MinTemp 4.3..27.6; MaxTemp 11.7..45.8; Pressure9am 986.7..1039; Pressure3pm 989.8..1036.7; WindGustSpeed 17..96; Rainfall 0..119.4 | None needed |
| Location / country columns | NONE - the file has no city, station or country field, so it covers a single unnamed location | Cross-location comparison is impossible. Location context is inferred, not given (see limitation 2 above) |

## Engineered columns

| Column | Definition |
|---|---|
| Year, Month, MonthName, Quarter, YearMonth, DayOfYear | Calendar parts of `Date` |
| Season | Southern-hemisphere meteorological season: Summer = Dec-Feb, Autumn = Mar-May, Winter = Jun-Aug, Spring = Sep-Nov |
| MeanTemp | (MinTemp + MaxTemp) / 2 |
| TempRange | MaxTemp - MinTemp (diurnal range) |
| TempChange_9to3, HumidityDrop_9to3, PressureChange_9to3 | 3pm value vs 9am value (humidity: 9am - 3pm) |
| AvgWindSpeed | Mean of WindSpeed9am and WindSpeed3pm |
| RainToday_Flag, RainTomorrow_Flag | 1/0 versions of the Yes/No columns |
| IsRainDay | 1 when Rainfall > 1 mm (the dataset's own rain-day rule) |
| RainCategory | Dry (<=1 mm), Light (1-10), Moderate (10-25), Heavy (25-50), Very heavy (>50) mm |
| HeatCategory | Mild (<20 °C), Warm (20-30), Hot (30-35), Extreme heat (>=35) by MaxTemp |
| GustCategory | Light (<30 km/h), Moderate (30-50), Strong (50-70), Gale-force (>=70) |
| Temp3pm_BelowMin | 1 when the 3pm temperature was below that day's minimum |
| WindGust_Placeholder, Cloud_Placeholder | 1 on days whose gust / cloud values were a constant placeholder and were set to missing |
| MaxTemp_Z, MinTemp_Z, Humidity3pm_Z, WindGustSpeed_Z, Pressure9am_Z | z-score versus the same calendar month across all years (removes seasonality) |
| AnomalyType, IsAnomaly | Flag when any |z| >= 3, or wet-day rainfall > Q3 + 3xIQR (53.4 mm) |

## Unusual-value screening

- **Statistical anomalies flagged: 90 days (2.8%).** By type: Extreme rain 31, Heat 28, Extreme gust 14, Very dry 9, Warm night 7, Low pressure 6, Cold night 3, High pressure 2, Cold 1.
- Rainfall is heavily right-skewed (median 0 mm, mean 3.34 mm), so a z-score is inappropriate for it; extreme rain uses a Tukey far-out fence on wet-day rainfall instead (53.4 mm; wet-day Q1 3.0, Q3 15.6).
- Tukey 1.5xIQR whisker counts (informational only - outliers are **retained**, they are real weather):

| Variable | Outside whiskers | Lower fence | Upper fence |
|---|---:|---:|---:|
| MinTemp | 0 | -0.7 | 30.5 |
| MaxTemp | 31 | 10.0 | 35.6 |
| Rainfall | 603 | -2.1 | 3.5 |
| WindGustSpeed | 50 | 5.5 | 73.5 |
| WindSpeed9am | 24 | -2.5 | 33.5 |
| WindSpeed3pm | 60 | 1.5 | 37.5 |
| Humidity9am | 12 | 25.0 | 113.0 |
| Humidity3pm | 19 | 14.0 | 94.0 |
| Pressure9am | 24 | 999.6 | 1037.2 |
| Pressure3pm | 20 | 997.0 | 1035.0 |
| Temp9am | 2 | 2.0 | 33.5 |
| Temp3pm | 25 | 9.2 | 33.7 |

Outliers were not removed: the extremes (heatwaves, storms) are exactly what this analysis is meant to find.
