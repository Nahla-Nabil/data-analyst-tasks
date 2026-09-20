# Task 6 - Key Insights: Weather & Climate Patterns

Dataset: 3,271 daily observations, 2008-02-01 to 2017-06-25 (cleaned file `Cleaned_Weather.csv`).

## Read this first - what the data can and cannot support

- **One location, not many.** The file has no city/country column, so the brief's 'across different cities and countries' cannot be answered; nothing is invented. Patterns are compared across **time (year, season, month)** and **wind direction**. The record looks like Sydney, Australia (the 45.8 °C maximum on 18 Jan 2013 matches Sydney Observatory Hill's official record), but the file does not say so - confirm before quoting a city.
- **Two blocks of the source were placeholders, not measurements**: wind gust speed/direction were a constant 41 km/h / W for the first 957 days (Feb 2008 - Oct 2010) and cloud cover a constant 5 / 4 for 520 days (Dec 2010 - Jun 2012). They were blanked. Left in, they would have made westerlies look like 44 % of all days (among real readings it is 20.2 %) and hidden the S/SE-wind rain pattern below. Wind-gust findings therefore cover 2,314 days (from 2010-10).
- **Gaps**: Apr 2011, Dec 2012 and Feb 2013 are missing entirely, 2008 has no January and 2017 stops on 25 Jun, so annual rainfall totals are not comparable; per-day rates and percentages are used.
- **Nine years is short.** Nothing here is a climate-change conclusion.

## The KPIs that matter

Chosen because each answers a different question a weather platform's users ask, and each can be tracked by period:

| KPI | Value (full record) | Why it matters |
|---|---|---|
| Average max / min temperature | 23.0 °C / 14.9 °C | Baseline comfort and the seasonal cycle; also the anchor for anomaly detection |
| Hot days (max >= 30 °C) / extreme heat days (>= 35 °C) | 187 (5.7 %) / 36 (1.1 %) | Health and fire-risk alerts - counts extremes that averages hide |
| Average 3pm humidity | 54.7 % | One of the strongest next-day rain signals in this data (with sunshine and cloud cover) |
| Rain days (> 1 mm) % | 26.0 % | How often it rains, independent of how much |
| Heavy-rain days (> 25 mm) and their share of rain | 122 days (3.7 %) carry 49.5 % of all rain | Flood risk - totals and averages hide this concentration |
| Average peak gust / days with gusts >= 70 km/h | 41.7 km/h / 86 days | Wind-safety alerts (gust data from Oct 2010) |
| Anomalous days | 90 (2.8 %) | Unusual-event monitor: z-score of 3 or more vs the same calendar month, or extreme rain |
| P(rain tomorrow given rain today) vs given dry today | 51.6 % vs 17.0 % | Persistence - a rain day roughly triples tomorrow's chance |

## 1. Temperature

| Season | Avg max °C | Avg min °C | Days |
|---|---|---|---|
| Summer | 26.8 | 19.7 | 772 |
| Autumn | 23.5 | 15.4 | 885 |
| Winter | 18.6 | 9.8 | 835 |
| Spring | 23.4 | 14.9 | 779 |

- **Seasonal cycle:** monthly average maximum ranges from 18.0 °C (July) to 27.5 °C (January); overnight minimums range from 9.0 °C to 20.3 °C.
- **Diurnal range** averages 8.1 °C, widest in winter (8.8 °C) and narrowest in summer (7.0 °C). 3pm is on average 3.7 °C warmer than 9am.
- **Extreme heat is a summer (and spring) phenomenon with dry air:** of 36 days at or above 35 °C, 26 were in summer, 9 in spring, 1 in autumn and none in winter; their average 3pm humidity was only 30.2 % (52.8 % of them below 25 %) - the fire-weather signature.

## 2. Humidity

- Mornings are more humid than afternoons in every month; on average humidity falls 13.5 points between 9am and 3pm.
- Humidity is highest in summer/autumn (3pm: 59 % / 56 %) and lowest in winter and spring (51 % / 52 %).
- On rain days 3pm humidity averages 64.2 % vs 51.4 % on dry days, sunshine 4.8 h vs 8.0 h, and max temperature 21.6 °C vs 23.5 °C - rainy days are cloudier, stickier and about 2 °C cooler.

## 3. Wind

- **Direction is a strong rain signal; speed is not.** Gusts from the S/SE sector (ESE, SE, SSE, S, SSW, SW) occur on 35.8 % of days but come with rain on **40.3 %** of them, versus **17.8 %** for all other directions; those days carried 59.7 % of all rainfall. Rank correlation between gust speed and rainfall is only 0.10.
- The wettest directions are SE (53 % rain days), ESE (43 % rain days), SW (42 % rain days), SSW (40 % rain days); the driest are NNW (14 %), N (13 %), NNE (10 %) (directions with at least 30 days).
- The most common single gust direction is W (20.2 % of days) and it is mostly dry (19.0 % rain days).
- **Spring is the windiest season** (mean gust 44.3 km/h; 33 of the 86 days with gusts >= 70 km/h). Summer is close (43.3 km/h); autumn is calmest (38.9 km/h).
- Strongest gusts: 96 km/h on 2014-06-28 (W), 96 km/h on 2016-06-05 (ENE), 94 km/h on 2011-05-30 (ESE), 94 km/h on 2013-08-12 (W).

## 4. Rainfall

- **No dry season:** rain days are 23-27 % of days in every season. By daily average the wettest months are June (5.9 mm/day) and April (5.26); the driest is September (1.73). December's average uses 8 years because Dec 2012 is missing.
- **Rain arrives in a few big events:**

| Rain class | Days | % of days |
|---|---|---|
| Dry (<=1 mm) | 2,422 | 74.0 % |
| Light (1-10) | 537 | 16.4 % |
| Moderate (10-25) | 190 | 5.8 % |
| Heavy (25-50) | 87 | 2.7 % |
| Very heavy (>50) | 35 | 1.1 % |

  Days over 25 mm are 3.7 % of the record but deliver **49.5 % of all rain**; the wettest 1 % of days alone deliver 22.2 %.
- Wettest days: 119.4 mm on 2015-04-21, 109.4 mm on 2012-03-08, 105.8 mm on 2015-04-22, 99.4 mm on 2011-03-20. Largest two-day total: **225.2 mm** starting 2015-04-21.
- **Persistence:** the chance of rain tomorrow is 51.6 % after a rain day and 17.0 % after a dry day (overall 26.0 %).
- **3pm humidity is a strong early-warning signal:**

| 3pm humidity | Days | Rain today | Rain tomorrow |
|---|---|---|---|
| < 40 % | 619 | 10 % | 6 % |
| 40-55 % | 914 | 17 % | 12 % |
| 55-70 % | 1216 | 27 % | 27 % |
| 70-85 % | 368 | 49 % | 64 % |
| 85 %+ | 154 | 82 % | 95 % |

  The one-line rule *'3pm humidity >= 70 % -> rain tomorrow'* is right 81.3 % of the time (precision 72.8 %, recall 44.8 %; it flags 16.0 % of days). For comparison, 'tomorrow = today' scores 74.9 % and always guessing dry scores 74.0 %. Sunshine (rank corr -0.51) and 3pm cloud (0.46) carry similar signal; **9am pressure carries almost none** (-0.04).

## 5. Unusual patterns

- **90 anomalous days (2.8 %):** Extreme rain 31, Heat 28, Extreme gust 14, Very dry 9, Warm night 7, Low pressure 6, Cold night 3, High pressure 2, Cold 1. Definition: |z| >= 3 against the same calendar month (so normal seasonality is not flagged), or wet-day rainfall above the Tukey far-out fence. Gust anomalies can only exist from Oct 2010.
- **Hottest / most extreme:** 2013-01-18 45.8 °C (z = 4.78); 2011-02-05 41.5 °C (z = 4.59); 2015-03-01 36.4 °C (z = 4.29); 2015-11-20 40.9 °C (z = 4.13). The 45.8 °C on 18 Jan 2013 came with 14 % afternoon humidity and a 78 km/h gust.
- **10 compound days** had two or more flags at once - two families stand out: (1) hot + very dry + gusty heatwave days (e.g. 2013-01-08, 2013-01-18, 2015-11-20) and (2) extreme-rain + extreme-gust storms (21-22 Apr 2015, 4-5 Jun 2016, with gusts of 72-96 km/h and 64-119 mm a day).
- **Warmest months relative to normal:** 2013-09 (+2.44 °C), 2016-12 (+2.3 °C), 2013-10 (+2.15 °C), 2017-01 (+2.15 °C). **Coolest:** 2011-12 (-2.7 °C), 2009-10 (-2.22 °C), 2008-02 (-2.13 °C).
- Anomaly flags per season are similar (summer 25, autumn 25, winter 24, spring 16) - but the *type* differs: heat flags are mostly summer/spring (20 of 28) while extreme-rain flags are mostly winter/autumn (22 of 31).

## 6. Change over time

| Year | Avg max °C | Avg min °C | Rain days % | Rain mm/day | Days >= 30 °C |
|---|---|---|---|---|---|
| 2009 | 22.9 | 15.1 | 24 | 2.66 | 21 |
| 2010 | 22.6 | 15.1 | 26 | 3.29 | 17 |
| 2011 | 22.5 | 14.7 | 27 | 3.49 | 23 |
| 2012 | 22.4 | 14.1 | 26 | 3.45 | 9 |
| 2013 | 23.5 | 14.7 | 21 | 3.50 | 19 |
| 2014 | 23.4 | 15.1 | 26 | 2.48 | 16 |
| 2015 | 23.1 | 14.9 | 27 | 3.70 | 21 |
| 2016 | 23.9 | 15.4 | 24 | 3.67 | 27 |

(2009-2016 only; per-day rates because 2010-2013 have missing months.)

- **Temperatures step up around 2013.** Comparing 2008-12 with 2013-17 month by month, maximums are about **+1.0 °C** higher after 2012; the yearly anomaly was between -0.5 and -0.1 °C in 2009-12 and rose to +0.8 °C in 2013 and +0.8 °C in 2016. Days at or above 35 °C: 10 in 2009-12 (1,346 observed days) vs 18 in 2013-16 (1,417 days).
- **Do not over-read it.** A straight-line fit gives +1.68 °C per decade, far too steep to be a climate trend; it is a short record dominated by a cool 2008-12 and a hot 2013 (the Bureau of Meteorology lists 2013 as Sydney's warmest year on record). Rainfall shows no significant change (p = 0.335). The honest statement is: *this station was about 1 °C warmer in 2013-17 than in 2008-12; nine years cannot say whether that persists.*

## Recommendations for the platform

1. **Use 3pm humidity (with cloud/sunshine) in the short-term rain alert** - it beats persistence and pressure by a wide margin; treat >= 70 % as 'rain likely tomorrow' and >= 85 % as 'very likely'.
2. **Add wind direction to rain warnings:** S/SE gusts (ESE-SW) more than double the chance of rain (40 % vs 18 %).
3. **Alert on extremes, not averages:** heat >= 35 °C with humidity under 25 % (fire weather) and rain > 25 mm (about 4 % of days, half of all rain).
4. **Automate anomaly flags with month-relative z-scores** (|z| >= 3) so seasonality is not mistaken for unusual weather; surface compound events.
5. **Fix the data feed:** stop filling missing readings with constants (gust and cloud lost 29 % and 16 % of days to placeholders) - publish real nulls - and add a location/station field so cities and countries can be compared.
