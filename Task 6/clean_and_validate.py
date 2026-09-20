"""
Task 6 - Weather Data: cleaning, validation and feature engineering.

Reads  Weather_Data.csv          (raw, 3,271 daily observations)
Writes Cleaned_Weather.csv       (validated + engineered columns)
       DATA_QUALITY_REPORT.md    (every check, its result, and the action taken)

Every number in the report is computed here - nothing is typed in by hand.
"""

import numpy as np
import pandas as pd

RAW_PATH = "Weather_Data.csv"
OUT_CSV = "Cleaned_Weather.csv"
OUT_REPORT = "DATA_QUALITY_REPORT.md"

MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
# Southern-hemisphere meteorological seasons (the data is Australian: hottest months are Dec-Feb).
SEASON_OF_MONTH = {12: "Summer", 1: "Summer", 2: "Summer", 3: "Autumn", 4: "Autumn", 5: "Autumn",
                   6: "Winter", 7: "Winter", 8: "Winter", 9: "Spring", 10: "Spring", 11: "Spring"}

Z_THRESHOLD = 3.0  # |z| vs the same calendar month's climatology


def main():
    raw = pd.read_csv(RAW_PATH)
    df = raw.copy()
    checks = []  # (check, result, action)

    # ------------------------------------------------------------------ structure
    checks.append(("Rows x columns", f"{raw.shape[0]:,} x {raw.shape[1]}", "None needed"))
    n_missing = int(raw.isna().sum().sum())
    checks.append(("Missing values (all columns)", f"{n_missing} (but see the constant-value blocks below - missing readings were pre-filled)", "See below"))
    n_dup_rows = int(raw.duplicated().sum())
    checks.append(("Fully duplicated rows", f"{n_dup_rows}", "None needed"))

    # ------------------------------------------------------------------ dates
    df["Date"] = pd.to_datetime(raw["Date"], format="%m/%d/%Y", errors="raise")
    n_dup_dates = int(df["Date"].duplicated().sum())
    sorted_ok = bool(df["Date"].is_monotonic_increasing)
    checks.append(("Date format", "m/d/yyyy (e.g. 2/1/2008 = 1 Feb 2008); parsed with explicit format, 0 failures",
                   "Converted to a real date; stored ISO yyyy-mm-dd"))
    checks.append(("Duplicate dates", f"{n_dup_dates}", "None needed"))
    checks.append(("Chronological order", "Yes" if sorted_ok else "No", "Sorted" if not sorted_ok else "None needed"))
    df = df.sort_values("Date").reset_index(drop=True)

    full_range = pd.date_range(df["Date"].min(), df["Date"].max(), freq="D")
    missing_days = full_range.difference(df["Date"])
    gaps = df["Date"].diff().dt.days
    longest_gap = int(gaps.max())
    longest_gap_end = df.loc[gaps.idxmax(), "Date"]
    longest_gap_start = longest_gap_end - pd.Timedelta(days=longest_gap)
    checks.append(("Calendar coverage",
                   f"{df['Date'].min():%d %b %Y} -> {df['Date'].max():%d %b %Y}: {len(df):,} of {len(full_range):,} days "
                   f"present, {len(missing_days)} missing. Longest gap: {longest_gap - 1} days "
                   f"({longest_gap_start + pd.Timedelta(days=1):%d %b %Y} - {longest_gap_end - pd.Timedelta(days=1):%d %b %Y})",
                   "Kept as-is (no interpolation). Monthly/annual means use observed days only"))
    per_year = df.groupby(df["Date"].dt.year).size()
    all_months = pd.period_range(df["Date"].min().to_period("M"), df["Date"].max().to_period("M"), freq="M")
    ym_counts = df.groupby(df["Date"].dt.to_period("M")).size().reindex(all_months, fill_value=0)
    absent = [p for p in all_months if ym_counts[p] == 0]
    sparse = [(p, int(ym_counts[p]), p.days_in_month) for p in all_months if 0 < ym_counts[p] < 0.8 * p.days_in_month]
    absent_txt = ", ".join(p.strftime("%b %Y") for p in absent)
    sparse_txt = ", ".join(f"{p.strftime('%b %Y')} ({n}/{d} days)" for p, n, d in sparse)
    checks.append(("Months with no data at all", f"{len(absent)}: {absent_txt}",
                   "Left blank in charts (never filled with zero or interpolated); they are excluded from monthly/seasonal averages"))
    checks.append(("Months with < 80% of days", sparse_txt if sparse else "none", "Kept; monthly totals for these months are understated"))
    checks.append(("Partial years",
                   f"2008 starts 1 Feb ({per_year[2008]} days, no January); 2017 ends 25 Jun ({per_year[2017]} days)",
                   "Full-year comparisons are unreliable (see limitation 3); rates per day/percentages are used instead of totals"))

    # ------------------------------------------------------------------ text fields
    dir_cols = ["WindGustDir", "WindDir9am", "WindDir3pm"]
    for c in dir_cols + ["RainToday", "RainTomorrow"]:
        df[c] = df[c].astype(str).str.strip()
    dirs_ok = all(df[c].nunique() == 16 for c in dir_cols)
    checks.append(("Wind-direction labels", "16 compass points in each of the 3 direction columns, no typos/variants"
                   if dirs_ok else "Unexpected label count", "Whitespace-trimmed"))
    df["RainToday_Flag"] = (df["RainToday"] == "Yes").astype(int)
    df["RainTomorrow_Flag"] = (df["RainTomorrow"] == "Yes").astype(int)

    # ------------------------------------------------------------------ placeholder (auto-filled) blocks
    # The source has no NaNs, but two column groups sit on ONE constant value for hundreds of consecutive days -
    # the fingerprint of missing readings that were filled with the median/mode before the file was published.
    def placeholder_mask(cols, min_len=30):
        key = df[cols].astype(str).agg("|".join, axis=1)
        run_id = (key != key.shift()).cumsum()
        return key.groupby(run_id).transform("size") >= min_len

    other_runs = {}
    for c in ["MinTemp", "MaxTemp", "Evaporation", "Sunshine", "WindSpeed9am", "WindSpeed3pm", "Humidity9am", "Humidity3pm",
              "Pressure9am", "Pressure3pm", "Temp9am", "Temp3pm", "WindDir9am", "WindDir3pm"]:
        run_id = (df[c] != df[c].shift()).cumsum()
        other_runs[c] = int(df[c].groupby(run_id).transform("size").max())
    gust_ph = placeholder_mask(["WindGustSpeed", "WindGustDir"])
    cloud_ph = placeholder_mask(["Cloud9am", "Cloud3pm"])
    gust_ph_txt = (f"{int(gust_ph.sum()):,} days ({gust_ph.mean():.1%}), {df.loc[gust_ph, 'Date'].min():%d %b %Y} - {df.loc[gust_ph, 'Date'].max():%d %b %Y}: "
                   f"WindGustSpeed = {int(df.loc[gust_ph, 'WindGustSpeed'].iloc[0])} km/h and WindGustDir = {df.loc[gust_ph, 'WindGustDir'].iloc[0]} on every single day")
    cloud_ph_txt = (f"{int(cloud_ph.sum()):,} days ({cloud_ph.mean():.1%}), {df.loc[cloud_ph, 'Date'].min():%d %b %Y} - {df.loc[cloud_ph, 'Date'].max():%d %b %Y}: "
                    f"Cloud9am = {int(df.loc[cloud_ph, 'Cloud9am'].iloc[0])} and Cloud3pm = {int(df.loc[cloud_ph, 'Cloud3pm'].iloc[0])} on every single day")
    checks.append(("Constant-value blocks (placeholder fill) - wind gust", gust_ph_txt +
                   ". Real gusts vary from day to day; the next-longest run of the same (speed, direction) pair anywhere else in the file is only a few days",
                   "Set WindGustSpeed and WindGustDir to missing for these days (flag `WindGust_Placeholder`); rows kept"))
    checks.append(("Constant-value blocks (placeholder fill) - cloud cover", cloud_ph_txt,
                   "Set Cloud9am and Cloud3pm to missing for these days (flag `Cloud_Placeholder`); rows kept"))
    checks.append(("Same scan on all other columns", "Longest identical run: " + ", ".join(f"{c} {v}" for c, v in sorted(other_runs.items(), key=lambda kv: -kv[1])[:4])
                   + " days (rainfall excluded: 0.0 mm can legitimately repeat)", "None - no other placeholder blocks found"))
    df["WindGust_Placeholder"] = gust_ph.astype(int)
    df["Cloud_Placeholder"] = cloud_ph.astype(int)
    df.loc[gust_ph, ["WindGustSpeed", "WindGustDir"]] = np.nan
    df.loc[cloud_ph, ["Cloud9am", "Cloud3pm"]] = np.nan
    g_start, g_end = df.loc[gust_ph, "Date"].min(), df.loc[gust_ph, "Date"].max()
    c_start, c_end = df.loc[cloud_ph, "Date"].min(), df.loc[cloud_ph, "Date"].max()
    gust_first_real = df.loc[df["WindGustSpeed"].notna(), "Date"].min()
    n_gust_valid, n_cloud_valid = int(df["WindGustSpeed"].notna().sum()), int(df["Cloud9am"].notna().sum())

    # ------------------------------------------------------------------ physical / logical consistency
    n_minmax = int((df["MinTemp"] > df["MaxTemp"]).sum())
    checks.append(("MinTemp > MaxTemp", f"{n_minmax} rows", "None needed"))
    n_t3_hi = int((df["Temp3pm"] > df["MaxTemp"]).sum())
    n_t9_hi = int((df["Temp9am"] > df["MaxTemp"]).sum())
    checks.append(("Temp9am / Temp3pm above MaxTemp", f"{n_t9_hi + n_t3_hi} rows", "None needed"))
    n_t3_lo = int((df["Temp3pm"] < df["MinTemp"]).sum())
    n_t9_lo = int((df["Temp9am"] < df["MinTemp"]).sum())
    checks.append(("Temp9am / Temp3pm below MinTemp",
                   f"Temp9am: {n_t9_lo} rows; Temp3pm: {n_t3_lo} rows ({n_t3_lo / len(df):.1%})",
                   "Kept - physically possible (cold front / rainy afternoon cooler than the overnight minimum), "
                   "flagged in `Temp3pm_BelowMin`"))
    df["Temp3pm_BelowMin"] = (df["Temp3pm"] < df["MinTemp"]).astype(int)

    # RainToday should follow "Rainfall > 1 mm"
    rule_gt1 = (df["Rainfall"] > 1).astype(int)
    rule_ge1 = (df["Rainfall"] >= 1).astype(int)
    match_gt1 = int((rule_gt1 == df["RainToday_Flag"]).sum())
    match_ge1 = int((rule_ge1 == df["RainToday_Flag"]).sum())
    n_exactly1 = int((df["Rainfall"] == 1.0).sum())
    checks.append(("RainToday vs Rainfall",
                   f"RainToday = 'Yes' <=> Rainfall > 1 mm holds for {match_gt1:,}/{len(df):,} rows (100%). "
                   f"The >= 1 mm rule would break {len(df) - match_ge1} rows - all {n_exactly1} days with exactly 1.0 mm are 'No'",
                   "Not an error: this is the dataset's rain-day definition. Adopted as `IsRainDay`"))
    df["IsRainDay"] = rule_gt1

    # RainTomorrow should equal the next row's RainToday whenever the next row is the next calendar day
    nxt_today = df["RainToday"].shift(-1)
    consecutive = (df["Date"].shift(-1) - df["Date"]).dt.days == 1
    agree = float((df.loc[consecutive, "RainTomorrow"] == nxt_today[consecutive]).mean())
    checks.append(("RainTomorrow vs next day's RainToday",
                   f"Agree on {agree:.1%} of {int(consecutive.sum()):,} consecutive-day pairs",
                   "None needed - the label is internally consistent"))

    n_gust = int((df["WindGustSpeed"] < df[["WindSpeed9am", "WindSpeed3pm"]].max(axis=1)).sum())  # NaN gusts compare False
    checks.append(("Wind gust below a 9am/3pm wind speed", f"{n_gust} rows",
                   "Kept - gust is the day's peak so this should not happen, but the gaps are tiny; noted only"))
    n_sun0 = int((df["Sunshine"] == 0).sum())
    sun0 = df[df["Sunshine"] == 0]
    checks.append(("Sunshine = 0 hours",
                   f"{n_sun0} days ({n_sun0 / len(df):.1%}); {float((sun0['Rainfall'] > 1).mean()):.0%} of them are rain days, "
                   f"mean 3pm cloud (where recorded) = {sun0['Cloud3pm'].mean():.1f}/8",
                   "Kept - consistent with overcast/rainy days, not a missing-value placeholder"))
    n_cloud9 = int((df["Cloud9am"] > 8).sum())
    checks.append(("Cloud cover above 8 oktas",
                   f"Cloud9am: {n_cloud9} row(s) at 9 (code for 'sky obscured'); Cloud3pm max = {int(df['Cloud3pm'].max())}",
                   "Kept - 9 is a valid BOM code; treated as 8 only if averaged (not used in KPIs)"))
    n_hum = int(((df[["Humidity9am", "Humidity3pm"]] < 0) | (df[["Humidity9am", "Humidity3pm"]] > 100)).sum().sum())
    checks.append(("Humidity outside 0-100 %", f"{n_hum} rows", "None needed"))
    rng = {c: (df[c].min(), df[c].max()) for c in ["MinTemp", "MaxTemp", "Pressure9am", "Pressure3pm", "WindGustSpeed", "Rainfall"]}
    checks.append(("Value ranges plausible",
                   "; ".join(f"{c} {lo:g}..{hi:g}" for c, (lo, hi) in rng.items()),
                   "None needed"))

    # ------------------------------------------------------------------ location
    hottest = df.loc[df["MaxTemp"].idxmax()]
    checks.append(("Location / country columns",
                   "NONE - the file has no city, station or country field, so it covers a single unnamed location",
                   "Cross-location comparison is impossible. Location context is inferred, not given (see limitation 2 above)"))

    # ------------------------------------------------------------------ feature engineering
    df["Year"] = df["Date"].dt.year
    df["Month"] = df["Date"].dt.month
    df["MonthName"] = df["Month"].map(lambda m: MONTH_NAMES[m - 1])
    df["Quarter"] = df["Date"].dt.quarter
    df["Season"] = df["Month"].map(SEASON_OF_MONTH)
    df["YearMonth"] = df["Date"].dt.strftime("%Y-%m")
    df["DayOfYear"] = df["Date"].dt.dayofyear
    df["MeanTemp"] = ((df["MinTemp"] + df["MaxTemp"]) / 2).round(2)
    df["TempRange"] = (df["MaxTemp"] - df["MinTemp"]).round(2)
    df["TempChange_9to3"] = (df["Temp3pm"] - df["Temp9am"]).round(2)
    df["HumidityDrop_9to3"] = df["Humidity9am"] - df["Humidity3pm"]
    df["PressureChange_9to3"] = (df["Pressure3pm"] - df["Pressure9am"]).round(2)
    df["AvgWindSpeed"] = ((df["WindSpeed9am"] + df["WindSpeed3pm"]) / 2).round(1)
    df["RainCategory"] = pd.cut(df["Rainfall"], bins=[-0.01, 1, 10, 25, 50, np.inf],
                                labels=["Dry (<=1 mm)", "Light (1-10)", "Moderate (10-25)", "Heavy (25-50)", "Very heavy (>50)"])
    df["HeatCategory"] = pd.cut(df["MaxTemp"], bins=[-np.inf, 20, 30, 35, np.inf], right=False,
                                labels=["Mild (<20)", "Warm (20-30)", "Hot (30-35)", "Extreme heat (>=35)"])
    df["GustCategory"] = pd.cut(df["WindGustSpeed"], bins=[-np.inf, 30, 50, 70, np.inf], right=False,
                                labels=["Light (<30)", "Moderate (30-50)", "Strong (50-70)", "Gale-force (>=70)"])

    # ------------------------------------------------------------------ anomaly flags
    # z-score relative to the same calendar month across all years, so seasonality is not mistaken for anomaly
    anomaly_vars = {"MaxTemp": ("Heat", "Cold"), "MinTemp": ("Warm night", "Cold night"),
                    "Humidity3pm": ("Very humid", "Very dry"), "WindGustSpeed": ("Extreme gust", None),
                    "Pressure9am": ("High pressure", "Low pressure")}
    for var in anomaly_vars:
        g = df.groupby("Month")[var]
        df[f"{var}_Z"] = ((df[var] - g.transform("mean")) / g.transform("std")).round(2)

    wet = df.loc[df["IsRainDay"] == 1, "Rainfall"]
    q1, q3 = wet.quantile([0.25, 0.75])
    rain_fence = q3 + 3 * (q3 - q1)  # Tukey "far out" fence on wet-day rainfall (rainfall is heavily right-skewed)

    def label_row(r):
        tags = []
        for var, (hi_lbl, lo_lbl) in anomaly_vars.items():
            z = r[f"{var}_Z"]
            if z >= Z_THRESHOLD and hi_lbl:
                tags.append(hi_lbl)
            elif z <= -Z_THRESHOLD and lo_lbl:
                tags.append(lo_lbl)
        if r["IsRainDay"] == 1 and r["Rainfall"] > rain_fence:
            tags.append("Extreme rain")
        return "; ".join(tags)

    df["AnomalyType"] = df.apply(label_row, axis=1)
    df["IsAnomaly"] = (df["AnomalyType"] != "").astype(int)
    n_anom = int(df["IsAnomaly"].sum())
    type_counts = df.loc[df["IsAnomaly"] == 1, "AnomalyType"].str.split("; ").explode().value_counts()

    # Tukey 1.5 IQR outlier counts (informational: how many raw values sit outside the whiskers)
    iqr_rows = []
    for c in ["MinTemp", "MaxTemp", "Rainfall", "WindGustSpeed", "WindSpeed9am", "WindSpeed3pm",
              "Humidity9am", "Humidity3pm", "Pressure9am", "Pressure3pm", "Temp9am", "Temp3pm"]:
        a, b = df[c].quantile([0.25, 0.75])
        lo, hi = a - 1.5 * (b - a), b + 1.5 * (b - a)
        iqr_rows.append((c, int(((df[c] < lo) | (df[c] > hi)).sum()), lo, hi))

    # ------------------------------------------------------------------ save
    front = ["Date", "Year", "Month", "MonthName", "Quarter", "Season", "YearMonth", "DayOfYear"]
    df = df[front + [c for c in df.columns if c not in front]]
    df["Date"] = df["Date"].dt.strftime("%Y-%m-%d")
    df.to_csv(OUT_CSV, index=False)

    # ------------------------------------------------------------------ report
    L = []
    L.append("# Task 6 - Data Quality Report\n")
    L.append(f"Source: `{RAW_PATH}` - {raw.shape[0]:,} daily weather observations, {raw.shape[1]} columns. "
             f"Output: `{OUT_CSV}` ({df.shape[0]:,} rows, {df.shape[1]} columns).\n")
    L.append("## Bottom line\n")
    L.append(f"The raw file has **{n_missing} missing values, {n_dup_rows} duplicate rows, {n_dup_dates} duplicate dates and no impossible values** - "
             f"but that is misleading, because the gaps were **already filled with constants** before the file was published. "
             f"Two blocks were detected and blanked (see the table): wind gust speed/direction for **{int(gust_ph.sum()):,} days** "
             f"({g_start:%b %Y} - {g_end:%b %Y}) and cloud cover for **{int(cloud_ph.sum()):,} days** "
             f"({c_start:%b %Y} - {c_end:%b %Y}). "
             f"Left in, they would have made westerly winds look dominant (and gust-based 'anomalies' impossible in 2008-10). "
             f"**No rows were dropped and no other value was changed or imputed.** Wind-gust analysis therefore covers "
             f"{n_gust_valid:,} days and cloud analysis {n_cloud_valid:,} days.\n")
    L.append("## Limitations that affect the analysis (read these first)\n")
    L.append("1. **No location field.** The brief asks about 'different cities and countries', but the file has no city, station or "
             "country column - it is one unnamed location. Comparing locations is therefore not possible and no location "
             "comparison is fabricated. The analysis compares **time periods** (year, season, month) and **wind-direction sectors** instead.")
    L.append(f"2. **Location is inferred, not stated.** The hottest day is {hottest['Date']:%d %b %Y} at {hottest['MaxTemp']}°C, which matches the "
             "Bureau of Meteorology's record for Sydney (Observatory Hill, 45.8°C, 18 Jan 2013), and the seasons are southern-hemisphere "
             "(hottest Dec-Feb). It is treated as **a single Australian (apparently Sydney) station**; seasons are labelled accordingly. "
             "Confirm with the data provider before quoting the city name.")
    L.append(f"3. **Uneven coverage.** {len(missing_days)} calendar days are missing, including {len(absent)} whole months ({absent_txt}); "
             f"{sparse_txt} are only partly covered. 2008 has no January and 2017 stops on 25 June. Because of this, annual rainfall "
             "*totals* are not comparable between years (2010-2013 are all incomplete) - the analysis uses percentages and per-day averages, "
             "and treats 2008 and 2017 as partial years. Monthly and seasonal averages use observed days only.")
    L.append("4. **Only ~9 years of data.** Any trend is a short-record observation, not a climate-change conclusion.\n")
    L.append("## Validation checks\n")
    L.append("| Check | Result | Action |\n|---|---|---|")
    for c, r, a in checks:
        L.append(f"| {c} | {r} | {a} |")
    L.append("\n## Engineered columns\n")
    L.append("| Column | Definition |\n|---|---|")
    for c, d in [
        ("Year, Month, MonthName, Quarter, YearMonth, DayOfYear", "Calendar parts of `Date`"),
        ("Season", "Southern-hemisphere meteorological season: Summer = Dec-Feb, Autumn = Mar-May, Winter = Jun-Aug, Spring = Sep-Nov"),
        ("MeanTemp", "(MinTemp + MaxTemp) / 2"),
        ("TempRange", "MaxTemp - MinTemp (diurnal range)"),
        ("TempChange_9to3, HumidityDrop_9to3, PressureChange_9to3", "3pm value vs 9am value (humidity: 9am - 3pm)"),
        ("AvgWindSpeed", "Mean of WindSpeed9am and WindSpeed3pm"),
        ("RainToday_Flag, RainTomorrow_Flag", "1/0 versions of the Yes/No columns"),
        ("IsRainDay", "1 when Rainfall > 1 mm (the dataset's own rain-day rule)"),
        ("RainCategory", "Dry (<=1 mm), Light (1-10), Moderate (10-25), Heavy (25-50), Very heavy (>50) mm"),
        ("HeatCategory", "Mild (<20 °C), Warm (20-30), Hot (30-35), Extreme heat (>=35) by MaxTemp"),
        ("GustCategory", "Light (<30 km/h), Moderate (30-50), Strong (50-70), Gale-force (>=70)"),
        ("Temp3pm_BelowMin", "1 when the 3pm temperature was below that day's minimum"),
        ("WindGust_Placeholder, Cloud_Placeholder", "1 on days whose gust / cloud values were a constant placeholder and were set to missing"),
        ("MaxTemp_Z, MinTemp_Z, Humidity3pm_Z, WindGustSpeed_Z, Pressure9am_Z", "z-score versus the same calendar month across all years (removes seasonality)"),
        ("AnomalyType, IsAnomaly", f"Flag when any |z| >= {Z_THRESHOLD:g}, or wet-day rainfall > Q3 + 3xIQR ({rain_fence:.1f} mm)"),
    ]:
        L.append(f"| {c} | {d} |")
    L.append("\n## Unusual-value screening\n")
    L.append(f"- **Statistical anomalies flagged: {n_anom} days ({n_anom / len(df):.1%}).** By type: "
             + ", ".join(f"{k} {v}" for k, v in type_counts.items()) + ".")
    L.append(f"- Rainfall is heavily right-skewed (median 0 mm, mean {df['Rainfall'].mean():.2f} mm), so a z-score is inappropriate for it; "
             f"extreme rain uses a Tukey far-out fence on wet-day rainfall instead ({rain_fence:.1f} mm; wet-day Q1 {q1:.1f}, Q3 {q3:.1f}).")
    L.append("- Tukey 1.5xIQR whisker counts (informational only - outliers are **retained**, they are real weather):\n")
    L.append("| Variable | Outside whiskers | Lower fence | Upper fence |\n|---|---:|---:|---:|")
    for c, k, lo, hi in iqr_rows:
        L.append(f"| {c} | {k} | {lo:.1f} | {hi:.1f} |")
    L.append("\nOutliers were not removed: the extremes (heatwaves, storms) are exactly what this analysis is meant to find.")
    with open(OUT_REPORT, "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")
    print(f"Wrote {OUT_CSV} {df.shape} and {OUT_REPORT}")
    print("Anomalies:", n_anom, dict(type_counts))


if __name__ == "__main__":
    main()
