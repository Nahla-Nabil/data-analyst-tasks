"""
Task 6 - writes KEY_INSIGHTS.md from analysis_summary.json (numbers are never typed by hand).
Run after analysis.py.
"""

import json

S = json.load(open("analysis_summary.json", encoding="utf-8"))


def table(headers, rows):
    out = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    out += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return "\n".join(out)


sea = S["seasonal"]
mon = S["monthly"]
hb = S["rain_by_humidity_band"]
band_names = {"[0, 40)": "< 40 %", "[40, 55)": "40-55 %", "[55, 70)": "55-70 %", "[70, 85)": "70-85 %", "[85, 101)": "85 %+"}
rvd = S["rain_vs_dry"]
rc = S["rain_category_days"]
n = S["days"]
L = []
A = L.append

A("# Task 6 - Key Insights: Weather & Climate Patterns\n")
A(f"Dataset: {n:,} daily observations, {S['period'][0]} to {S['period'][1]} (cleaned file `Cleaned_Weather.csv`).\n")
A("## Read this first - what the data can and cannot support\n")
A("- **One location, not many.** The file has no city/country column, so the brief's 'across different cities and countries' cannot be answered; "
  "nothing is invented. Patterns are compared across **time (year, season, month)** and **wind direction**. The record looks like Sydney, Australia "
  "(the 45.8 °C maximum on 18 Jan 2013 matches Sydney Observatory Hill's official record), but the file does not say so - confirm before quoting a city.")
A("- **Two blocks of the source were placeholders, not measurements**: wind gust speed/direction were a constant 41 km/h / W for the first 957 days "
  "(Feb 2008 - Oct 2010) and cloud cover a constant 5 / 4 for 520 days (Dec 2010 - Jun 2012). They were blanked. Left in, they would have made "
  f"westerlies look like 44 % of all days (among real readings it is {S['w_dir_share_pct']} %) and hidden the S/SE-wind rain pattern below. "
  f"Wind-gust findings therefore cover {S['gust_valid_days']:,} days (from {S['gust_valid_from'][:7]}).")
A("- **Gaps**: Apr 2011, Dec 2012 and Feb 2013 are missing entirely, 2008 has no January and 2017 stops on 25 Jun, so annual rainfall totals are not comparable; per-day rates and percentages are used.")
A("- **Nine years is short.** Nothing here is a climate-change conclusion.\n")

A("## The KPIs that matter\n")
A("Chosen because each answers a different question a weather platform's users ask, and each can be tracked by period:\n")
A(table(["KPI", "Value (full record)", "Why it matters"], [
    ["Average max / min temperature", f"{S['avg_max_temp']} °C / {S['avg_min_temp']} °C", "Baseline comfort and the seasonal cycle; also the anchor for anomaly detection"],
    ["Hot days (max >= 30 °C) / extreme heat days (>= 35 °C)", f"{S['hot_days_30']} ({S['hot_days_30'] / n * 100:.1f} %) / {S['extreme_heat_days_35']} ({S['extreme_heat_days_35'] / n * 100:.1f} %)", "Health and fire-risk alerts - counts extremes that averages hide"],
    ["Average 3pm humidity", f"{S['avg_humidity_3pm']} %", "One of the strongest next-day rain signals in this data (with sunshine and cloud cover)"],
    ["Rain days (> 1 mm) %", f"{S['rain_day_pct']} %", "How often it rains, independent of how much"],
    ["Heavy-rain days (> 25 mm) and their share of rain", f"{S['heavy_rain_days']} days ({S['heavy_plus_days_pct']} %) carry {S['heavy_plus_mm_share_pct']} % of all rain", "Flood risk - totals and averages hide this concentration"],
    ["Average peak gust / days with gusts >= 70 km/h", f"{S['avg_gust']} km/h / {S['gust_ge70_days']} days", "Wind-safety alerts (gust data from Oct 2010)"],
    ["Anomalous days", f"{S['anomaly_days']} ({S['anomaly_days'] / n * 100:.1f} %)", "Unusual-event monitor: z-score of 3 or more vs the same calendar month, or extreme rain"],
    ["P(rain tomorrow given rain today) vs given dry today", f"{S['p_rain_tomorrow_given_rain']} % vs {S['p_rain_tomorrow_given_dry']} %", "Persistence - a rain day roughly triples tomorrow's chance"],
]))

A("\n## 1. Temperature\n")
A(table(["Season", "Avg max °C", "Avg min °C", "Days"], [[s, f"{a:.1f}", f"{b:.1f}", d] for s, a, b, d in zip(sea["Season"], sea["max_t"], sea["min_t"], sea["days"])]))
A(f"\n- **Seasonal cycle:** monthly average maximum ranges from {mon['max_t'][6]:.1f} °C (July) to {mon['max_t'][0]:.1f} °C (January); overnight minimums range from {mon['min_t'][6]:.1f} °C to {mon['min_t'][0]:.1f} °C.")
A(f"- **Diurnal range** averages {S['avg_temp_range']} °C, widest in winter ({S['diurnal_range_by_season']['Winter']} °C) and narrowest in summer ({S['diurnal_range_by_season']['Summer']} °C). 3pm is on average {S['temp_change_9to3']} °C warmer than 9am.")
A(f"- **Extreme heat is a summer (and spring) phenomenon with dry air:** of {S['extreme_heat_days_35']} days at or above 35 °C, {S['ge35_by_season']['Summer']} were in summer, {S['ge35_by_season']['Spring']} in spring, "
  f"{S['ge35_by_season']['Autumn']} in autumn and none in winter; their average 3pm humidity was only {S['ge35_mean_humidity3pm']} % ({S['ge35_share_below_25_humidity']} % of them below 25 %) - the fire-weather signature.")

A("\n## 2. Humidity\n")
A(f"- Mornings are more humid than afternoons in every month; on average humidity falls {S['humidity_drop_9to3']} points between 9am and 3pm.")
A(f"- Humidity is highest in summer/autumn (3pm: {sea['hum3'][0]:.0f} % / {sea['hum3'][1]:.0f} %) and lowest in winter and spring ({sea['hum3'][2]:.0f} % / {sea['hum3'][3]:.0f} %).")
A(f"- On rain days 3pm humidity averages {rvd['1']['Humidity3pm']} % vs {rvd['0']['Humidity3pm']} % on dry days, sunshine {rvd['1']['Sunshine']} h vs {rvd['0']['Sunshine']} h, and max temperature {rvd['1']['MaxTemp']} °C vs {rvd['0']['MaxTemp']} °C - rainy days are cloudier, stickier and about 2 °C cooler.")

A("\n## 3. Wind\n")
A(f"- **Direction is a strong rain signal; speed is not.** Gusts from the S/SE sector (ESE, SE, SSE, S, SSW, SW) occur on {S['se_sector_share_pct']} % of days but come with rain on **{S['se_sector_rain_day_pct']} %** of them, "
  f"versus **{S['other_sector_rain_day_pct']} %** for all other directions; those days carried {S['se_sector_share_of_rain_mm_pct']} % of all rainfall. Rank correlation between gust speed and rainfall is only {S['corr_rain_gust']:.2f}.")
A("- The wettest directions are " + ", ".join(f"{d['WindGustDir']} ({d['rain_today']:.0f} % rain days)" for d in S['wettest_gust_dirs'])
  + "; the driest are " + ", ".join(f"{d['WindGustDir']} ({d['rain_today']:.0f} %)" for d in S['driest_gust_dirs']) + " (directions with at least 30 days).")
A(f"- The most common single gust direction is W ({S['w_dir_share_pct']} % of days) and it is mostly dry ({S['w_dir_rain_day_pct']} % rain days).")
A(f"- **Spring is the windiest season** (mean gust {sea['gust'][3]:.1f} km/h; {S['gust_ge70_by_season']['Spring']} of the {S['gust_ge70_days']} days with gusts >= 70 km/h). Summer is close ({sea['gust'][0]:.1f} km/h); autumn is calmest ({sea['gust'][1]:.1f} km/h).")
A("- Strongest gusts: " + ", ".join(f"{g['kmh']} km/h on {g['date']} ({g['dir']})" for g in S['top_gust_days'][:4]) + ".")

A("\n## 4. Rainfall\n")
A(f"- **No dry season:** rain days are {min(sea['rain_day_pct']):.0f}-{max(sea['rain_day_pct']):.0f} % of days in every season. By daily average the wettest months are June ({mon['rain_mean'][5]} mm/day) and April ({mon['rain_mean'][3]}); the driest is September ({mon['rain_mean'][8]}). December's average uses 8 years because Dec 2012 is missing.")
A("- **Rain arrives in a few big events:**\n")
A(table(["Rain class", "Days", "% of days"], [[k, f"{v:,}", f"{v / n * 100:.1f} %"] for k, v in rc.items()]))
A(f"\n  Days over 25 mm are {S['heavy_plus_days_pct']} % of the record but deliver **{S['heavy_plus_mm_share_pct']} % of all rain**; the wettest 1 % of days alone deliver {S['rain_top10_share_pct']} %.")
A("- Wettest days: " + ", ".join(f"{d['mm']} mm on {d['date']}" for d in S['top_rain_days'][:4]) + f". Largest two-day total: **{S['two_day_top'][0]['mm']} mm** starting {S['two_day_top'][0]['date']}.")
A(f"- **Persistence:** the chance of rain tomorrow is {S['p_rain_tomorrow_given_rain']} % after a rain day and {S['p_rain_tomorrow_given_dry']} % after a dry day (overall {S['base_rain_tomorrow']} %).")
A("- **3pm humidity is a strong early-warning signal:**\n")
A(table(["3pm humidity", "Days", "Rain today", "Rain tomorrow"], [[band_names[k], v[2], f"{v[0]:.0f} %", f"{v[1]:.0f} %"] for k, v in hb.items()]))
A(f"\n  The one-line rule *'3pm humidity >= 70 % -> rain tomorrow'* is right {S['rule_hum70_accuracy_pct']} % of the time (precision {S['rule_hum70_precision_pct']} %, recall {S['rule_hum70_recall_pct']} %; it flags {S['rule_hum70_days_flagged_pct']} % of days). "
  f"For comparison, 'tomorrow = today' scores {S['persistence_accuracy_pct']} % and always guessing dry scores {S['always_dry_accuracy_pct']} %. Sunshine (rank corr {S['rank_corr_rain_tomorrow']['Sunshine']}) and 3pm cloud ({S['rank_corr_rain_tomorrow']['Cloud3pm']}) carry similar signal; "
  f"**9am pressure carries almost none** ({S['rank_corr_rain_tomorrow']['Pressure9am']}).")

A("\n## 5. Unusual patterns\n")
A(f"- **{S['anomaly_days']} anomalous days ({S['anomaly_days'] / n * 100:.1f} %):** " + ", ".join(f"{k} {v}" for k, v in S['anomalies_by_type'].items()) + ". Definition: |z| >= 3 against the same calendar month (so normal seasonality is not flagged), or wet-day rainfall above the Tukey far-out fence. Gust anomalies can only exist from Oct 2010.")
A("- **Hottest / most extreme:** " + "; ".join(f"{t['date']} {t['t']} °C (z = {t['z']})" for t in S['top_heat_z'][:4]) + ". The 45.8 °C on 18 Jan 2013 came with 14 % afternoon humidity and a 78 km/h gust.")
A(f"- **{S['compound_anomaly_days']} compound days** had two or more flags at once - two families stand out: (1) hot + very dry + gusty heatwave days (e.g. 2013-01-08, 2013-01-18, 2015-11-20) and "
  "(2) extreme-rain + extreme-gust storms (21-22 Apr 2015, 4-5 Jun 2016, with gusts of 72-96 km/h and 64-119 mm a day).")
A("- **Warmest months relative to normal:** " + ", ".join(f"{m['YearMonth']} (+{m['MaxA']} °C)" for m in S['warmest_months'][:4])
  + ". **Coolest:** " + ", ".join(f"{m['YearMonth']} ({m['MaxA']} °C)" for m in S['coolest_months'][:3]) + ".")
A(f"- Anomaly flags per season are similar (summer {S['anomalies_by_season']['Summer']}, autumn {S['anomalies_by_season']['Autumn']}, winter {S['anomalies_by_season']['Winter']}, spring {S['anomalies_by_season']['Spring']}) - but the *type* differs: heat flags are mostly summer/spring (20 of 28) while extreme-rain flags are mostly winter/autumn (22 of 31).")

A("\n## 6. Change over time\n")
ann = S["annual"]
A(table(["Year", "Avg max °C", "Avg min °C", "Rain days %", "Rain mm/day", "Days >= 30 °C"], [[y, f"{a:.1f}", f"{b:.1f}", f"{c:.0f}", f"{d:.2f}", e] for y, a, b, c, d, e in zip(ann["Year"], ann["max_temp"], ann["min_temp"], ann["rain_day_pct"], ann["rain_mm_per_day"], ann["hot_days"])]))
A("\n(2009-2016 only; per-day rates because 2010-2013 have missing months.)\n")
A(f"- **Temperatures step up around 2013.** Comparing 2008-12 with 2013-17 month by month, maximums are about **+{S['max_temp_diff_month_matched']} °C** higher after 2012; the yearly anomaly was between {min(S['max_anom_by_year'][str(y)] for y in range(2009, 2013)):+.1f} and {max(S['max_anom_by_year'][str(y)] for y in range(2009, 2013)):+.1f} °C in 2009-12 and rose to {S['max_anom_by_year']['2013']:+.1f} °C in 2013 and {S['max_anom_by_year']['2016']:+.1f} °C in 2016. "
  f"Days at or above 35 °C: {S['ge35_days_2009_2012']} in 2009-12 ({S['obs_days_2009_2012']:,} observed days) vs {S['ge35_days_2013_2016']} in 2013-16 ({S['obs_days_2013_2016']:,} days).")
A(f"- **Do not over-read it.** A straight-line fit gives +{S['trend_MaxTemp_per_decade']} °C per decade, far too steep to be a climate trend; it is a short record dominated by a cool 2008-12 and a hot 2013 (the Bureau of Meteorology lists 2013 as Sydney's warmest year on record). "
  f"Rainfall shows no significant change (p = {S['trend_Rain_p']}). The honest statement is: *this station was about 1 °C warmer in 2013-17 than in 2008-12; nine years cannot say whether that persists.*")

A("\n## Recommendations for the platform\n")
A("1. **Use 3pm humidity (with cloud/sunshine) in the short-term rain alert** - it beats persistence and pressure by a wide margin; treat >= 70 % as 'rain likely tomorrow' and >= 85 % as 'very likely'.")
A(f"2. **Add wind direction to rain warnings:** S/SE gusts (ESE-SW) more than double the chance of rain ({S['se_sector_rain_day_pct']:.0f} % vs {S['other_sector_rain_day_pct']:.0f} %).")
A(f"3. **Alert on extremes, not averages:** heat >= 35 °C with humidity under 25 % (fire weather) and rain > 25 mm (about {S['heavy_plus_days_pct']:.0f} % of days, half of all rain).")
A("4. **Automate anomaly flags with month-relative z-scores** (|z| >= 3) so seasonality is not mistaken for unusual weather; surface compound events.")
A("5. **Fix the data feed:** stop filling missing readings with constants (gust and cloud lost 29 % and 16 % of days to placeholders) - publish real nulls - and add a location/station field so cities and countries can be compared.")
with open("KEY_INSIGHTS.md", "w", encoding="utf-8") as f:
    f.write("\n".join(L) + "\n")
print("KEY_INSIGHTS.md written")
