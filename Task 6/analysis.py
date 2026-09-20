"""
Task 6 - Weather Data: exploratory analysis.

Reads  Cleaned_Weather.csv
Writes analysis_output.txt   (every table/number the insights are based on)
       analysis_summary.json (headline numbers, consumed by build_dashboard.py / KEY_INSIGHTS)
"""

import json

import numpy as np
import pandas as pd
from scipy import stats

IN_PATH = "Cleaned_Weather.csv"
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
SEASONS = ["Summer", "Autumn", "Winter", "Spring"]
FULL_YEARS = list(range(2009, 2017))  # 2008 has no Jan, 2017 ends 25 Jun; Apr 2011, Dec 2012 and Feb 2013 are missing entirely

out_lines = []


def emit(title, obj=None):
    out_lines.append(f"\n=== {title} ===")
    if obj is not None:
        out_lines.append(obj.to_string() if hasattr(obj, "to_string") else str(obj))


def main():
    df = pd.read_csv(IN_PATH, parse_dates=["Date"])
    S = {}  # summary json

    # ------------------------------------------------------------------ headline KPIs
    n = len(df)
    S["days"] = n
    S["period"] = [df["Date"].min().strftime("%Y-%m-%d"), df["Date"].max().strftime("%Y-%m-%d")]
    S["avg_max_temp"] = round(df["MaxTemp"].mean(), 1)
    S["avg_min_temp"] = round(df["MinTemp"].mean(), 1)
    S["avg_temp_range"] = round(df["TempRange"].mean(), 1)
    S["avg_humidity_9am"] = round(df["Humidity9am"].mean(), 1)
    S["avg_humidity_3pm"] = round(df["Humidity3pm"].mean(), 1)
    S["avg_gust"] = round(df["WindGustSpeed"].mean(), 1)
    S["avg_sunshine"] = round(df["Sunshine"].mean(), 1)
    S["rain_day_pct"] = round(df["IsRainDay"].mean() * 100, 1)
    S["mean_daily_rain"] = round(df["Rainfall"].mean(), 2)
    S["hot_days_30"] = int((df["MaxTemp"] >= 30).sum())
    S["extreme_heat_days_35"] = int((df["MaxTemp"] >= 35).sum())
    S["anomaly_days"] = int(df["IsAnomaly"].sum())
    emit("HEADLINE KPIs", pd.Series({k: v for k, v in S.items()}))

    # rainfall totals in comparable years only (full years, Dec 2012 gap noted)
    fy = df[df["Year"].isin(FULL_YEARS)]
    ann = fy.groupby("Year").agg(days=("Date", "size"), rain_mm_per_day=("Rainfall", "mean"), rain_day_pct=("IsRainDay", lambda v: v.mean() * 100),
                                 max_temp=("MaxTemp", "mean"), min_temp=("MinTemp", "mean"),
                                 hot_days=("MaxTemp", lambda s: int((s >= 30).sum())),
                                 humidity3=("Humidity3pm", "mean")).round(2)
    emit("ANNUAL SUMMARY (2009-2016; days = observed days; totals are NOT comparable because 2010-2013 have missing months, so per-day rates are shown)", ann)
    S["annual"] = ann.reset_index().to_dict(orient="list")

    # ------------------------------------------------------------------ seasonality
    mon = df.groupby("Month").agg(max_t=("MaxTemp", "mean"), min_t=("MinTemp", "mean"), hum3=("Humidity3pm", "mean"),
                                  gust=("WindGustSpeed", "mean"), rain_days=("IsRainDay", "mean"),
                                  rain_mean=("Rainfall", "mean"), sun=("Sunshine", "mean"), n=("Date", "size")).round(2)
    mon.index = MONTHS
    mon["rain_days"] = (mon["rain_days"] * 100).round(1)
    emit("MONTHLY CLIMATOLOGY", mon)
    S["hottest_month"] = mon["max_t"].idxmax()
    S["coolest_month"] = mon["max_t"].idxmin()
    S["hottest_month_val"] = float(mon["max_t"].max())
    S["coolest_month_val"] = float(mon["max_t"].min())
    S["wettest_month_by_rainmean"] = mon["rain_mean"].idxmax()
    S["driest_month_by_rainmean"] = mon["rain_mean"].idxmin()
    S["monthly"] = mon.reset_index().rename(columns={"index": "Month"}).to_dict(orient="list")

    sea = df.groupby("Season").agg(max_t=("MaxTemp", "mean"), min_t=("MinTemp", "mean"), hum3=("Humidity3pm", "mean"),
                                   gust=("WindGustSpeed", "mean"), rain_day_pct=("IsRainDay", "mean"),
                                   rain_mean=("Rainfall", "mean"), sun=("Sunshine", "mean"),
                                   days=("Date", "size")).reindex(SEASONS).round(2)
    sea["rain_day_pct"] = (sea["rain_day_pct"] * 100).round(1)
    emit("SEASONAL SUMMARY", sea)
    S["seasonal"] = sea.reset_index().to_dict(orient="list")
    S["seasonal_range_max_t"] = round(float(sea["max_t"].max() - sea["max_t"].min()), 1)

    # ------------------------------------------------------------------ temperature
    emit("MaxTemp distribution", df["MaxTemp"].describe().round(2))
    hot = df["HeatCategory"].value_counts(normalize=True).mul(100).round(1)
    emit("HeatCategory share %", hot)
    diurnal = df.groupby("Season")["TempRange"].mean().reindex(SEASONS).round(1)
    emit("Diurnal range by season", diurnal)
    S["diurnal_range_by_season"] = diurnal.to_dict()
    S["temp_change_9to3"] = round(df["TempChange_9to3"].mean(), 1)
    hd = df[df["MaxTemp"] >= 35]
    emit("Days >= 35C by year", hd.groupby("Year").size())
    S["days_ge35_by_year"] = {int(k): int(v) for k, v in hd.groupby("Year").size().items()}
    emit("Days >= 35C list", hd[["Date", "MaxTemp", "Humidity3pm", "WindGustSpeed", "WindGustDir"]].to_string(index=False))

    # ------------------------------------------------------------------ change over time (deseasonalised)
    df["MaxTemp_Anom"] = df["MaxTemp"] - df.groupby("Month")["MaxTemp"].transform("mean")
    df["MinTemp_Anom"] = df["MinTemp"] - df.groupby("Month")["MinTemp"].transform("mean")
    df["Rain_Anom"] = df["Rainfall"] - df.groupby("Month")["Rainfall"].transform("mean")
    ym = df.groupby("YearMonth").agg(MaxA=("MaxTemp_Anom", "mean"), MinA=("MinTemp_Anom", "mean"), RainA=("Rain_Anom", "mean"),
                                     Date=("Date", "min")).reset_index()
    ym["t"] = (ym["Date"] - ym["Date"].min()).dt.days / 365.25
    for v, label in [("MaxA", "MaxTemp"), ("MinA", "MinTemp")]:
        r = stats.linregress(ym["t"], ym[v])
        S[f"trend_{label}_per_decade"] = round(r.slope * 10, 2)
        S[f"trend_{label}_p"] = round(r.pvalue, 3)
        S[f"trend_{label}_r2"] = round(r.rvalue ** 2, 3)
    r = stats.linregress(ym["t"], ym["RainA"])
    S["trend_Rain_mm_per_day_per_decade"] = round(r.slope * 10, 2)
    S["trend_Rain_p"] = round(r.pvalue, 3)
    emit("TREND on monthly deseasonalised anomalies (linear, per decade)",
         pd.Series({k: S[k] for k in S if k.startswith("trend_")}))

    # like-for-like Feb 1 - Jun 25 window across all 10 years
    win = df[((df["Month"] >= 3) & (df["Month"] <= 5)) | ((df["Month"] == 2)) | ((df["Month"] == 6) & (df["Date"].dt.day <= 25))]
    win_year = win.groupby("Year").agg(max_t=("MaxTemp", "mean"), min_t=("MinTemp", "mean"), rain_mm=("Rainfall", "sum"),
                                       rain_days=("IsRainDay", "sum"), days=("Date", "size")).round(2)
    win_year["rain_mm_per_day"] = (win_year["rain_mm"] / win_year["days"]).round(2)
    emit("LIKE-FOR-LIKE Feb 1 - Jun 25 window by year (2011 lacks Apr, 2013 lacks Feb - compare the per-day columns, not totals)", win_year)
    S["window"] = win_year.reset_index().to_dict(orient="list")

    first, second = df[df["Year"] <= 2012], df[df["Year"] >= 2013]
    S["max_temp_2008_12"] = round(first["MaxTemp"].mean(), 2)
    S["max_temp_2013_17"] = round(second["MaxTemp"].mean(), 2)
    # month-matched comparison of the two halves (controls for the uneven months in 2008/2012/2017)
    mm = pd.DataFrame({"h1": first.groupby("Month")["MaxTemp"].mean(), "h2": second.groupby("Month")["MaxTemp"].mean()})
    S["max_temp_diff_month_matched"] = round(float((mm["h2"] - mm["h1"]).mean()), 2)
    t, p = stats.ttest_ind(second["MaxTemp_Anom"], first["MaxTemp_Anom"], equal_var=False)
    S["max_anom_2013_17_minus_2008_12"] = round(second["MaxTemp_Anom"].mean() - first["MaxTemp_Anom"].mean(), 2)
    S["max_anom_ttest_p"] = round(float(p), 4)
    emit("HALF-vs-HALF (2008-12 vs 2013-17) MaxTemp anomaly", pd.Series({
        "mean anomaly 2008-12": first["MaxTemp_Anom"].mean(), "mean anomaly 2013-17": second["MaxTemp_Anom"].mean(),
        "Welch p": p, "month-matched diff": S["max_temp_diff_month_matched"]}).round(3))

    # warmest / coolest single months (anomaly)
    top = ym.sort_values("MaxA", ascending=False).head(6)[["YearMonth", "MaxA", "MinA", "RainA"]].round(2)
    bot = ym.sort_values("MaxA").head(6)[["YearMonth", "MaxA", "MinA", "RainA"]].round(2)
    emit("WARMEST months by MaxTemp anomaly", top)
    emit("COOLEST months by MaxTemp anomaly", bot)
    S["warmest_months"] = top.to_dict(orient="records")
    S["coolest_months"] = bot.to_dict(orient="records")
    yr_anom = df.groupby("Year")["MaxTemp_Anom"].mean().round(2)
    emit("MaxTemp anomaly by year (vs same-month average; 2008/2017/2012 partial)", yr_anom)
    S["max_anom_by_year"] = {int(k): float(v) for k, v in yr_anom.items()}

    # ------------------------------------------------------------------ rainfall
    wet = df[df["IsRainDay"] == 1]
    S["wet_day_mean_mm"] = round(wet["Rainfall"].mean(), 1)
    S["wet_day_median_mm"] = round(wet["Rainfall"].median(), 1)
    S["rain_top10_share_pct"] = round(df["Rainfall"].nlargest(int(round(n * 0.01))).sum() / df["Rainfall"].sum() * 100, 1)
    S["rain_top1pct_days"] = int(round(n * 0.01))
    emit("Share of total rainfall from the wettest 1% of days (%)", S["rain_top10_share_pct"])
    rc = df["RainCategory"].value_counts().reindex(["Dry (<=1 mm)", "Light (1-10)", "Moderate (10-25)", "Heavy (25-50)", "Very heavy (>50)"])
    emit("Rain category days", pd.DataFrame({"days": rc, "pct": (rc / n * 100).round(1),
                                              "rain_mm": df.groupby("RainCategory", observed=True)["Rainfall"].sum().round(0)}))
    S["rain_category_days"] = {k: int(v) for k, v in rc.items()}
    top_rain = df.nlargest(10, "Rainfall")[["Date", "Rainfall", "Humidity3pm", "WindGustSpeed", "WindGustDir", "Pressure9am"]]
    emit("TOP 10 wettest days", top_rain.to_string(index=False))
    S["top_rain_days"] = [{"date": r.Date.strftime("%Y-%m-%d"), "mm": float(r.Rainfall)} for r in top_rain.itertuples()]
    ymr = df.groupby("YearMonth")["Rainfall"].sum().sort_values(ascending=False).head(5)
    emit("Wettest calendar months (total mm)", ymr)
    S["wettest_months"] = {k: round(float(v), 1) for k, v in ymr.items()}

    # persistence
    p_rr = df.loc[df["RainToday_Flag"] == 1, "RainTomorrow_Flag"].mean()
    p_dr = df.loc[df["RainToday_Flag"] == 0, "RainTomorrow_Flag"].mean()
    S["p_rain_tomorrow_given_rain"] = round(p_rr * 100, 1)
    S["p_rain_tomorrow_given_dry"] = round(p_dr * 100, 1)
    S["base_rain_tomorrow"] = round(df["RainTomorrow_Flag"].mean() * 100, 1)
    emit("Rain persistence", pd.Series({"P(rain tmrw | rain today) %": S["p_rain_tomorrow_given_rain"],
                                        "P(rain tmrw | dry today) %": S["p_rain_tomorrow_given_dry"],
                                        "P(rain tmrw) %": S["base_rain_tomorrow"]}))
    # naive persistence forecast accuracy (predict tomorrow = today)
    S["persistence_accuracy_pct"] = round((df["RainToday_Flag"] == df["RainTomorrow_Flag"]).mean() * 100, 1)
    S["always_dry_accuracy_pct"] = round((1 - df["RainTomorrow_Flag"].mean()) * 100, 1)

    # wet spells
    d = df.set_index("Date")["IsRainDay"].asfreq("D")
    spells, cur = [], 0
    for v in d:
        if v == 1:
            cur += 1
        else:
            if cur:
                spells.append(cur)
            cur = 0
    if cur:
        spells.append(cur)
    S["longest_wet_spell_days"] = int(max(spells))  # NB gaps in the record can join/split spells slightly

    # ------------------------------------------------------------------ wind
    # gust speed/direction were blanked for 2008-02..2010-10 (placeholder block) - wind stats use real readings only
    dv = df[df["WindGustDir"].notna()]
    nv = len(dv)
    S["gust_valid_days"] = nv
    S["gust_valid_from"] = dv["Date"].min().strftime("%Y-%m-%d")
    wd = dv.groupby("WindGustDir").agg(days=("Date", "size"), gust=("WindGustSpeed", "mean"),
                                       rain_next=("RainTomorrow_Flag", "mean"), rain_today=("IsRainDay", "mean"),
                                       hum3=("Humidity3pm", "mean"), maxt=("MaxTemp", "mean")).round(3)
    wd["share_pct"] = (wd["days"] / nv * 100).round(1)
    wd[["rain_next", "rain_today"]] = (wd[["rain_next", "rain_today"]] * 100).round(1)
    wd = wd.sort_values("days", ascending=False)
    emit("WIND GUST DIRECTION profile", wd)
    S["gust_dir_top"] = wd.head(3)[["days", "share_pct"]].reset_index().to_dict(orient="records")
    wdr = wd[wd["days"] >= 30].sort_values("rain_today", ascending=False)
    S["wettest_gust_dirs"] = wdr.head(4)[["days", "rain_today", "gust"]].reset_index().to_dict(orient="records")
    S["driest_gust_dirs"] = wdr.tail(3)[["days", "rain_today", "gust"]].reset_index().to_dict(orient="records")
    # onshore-type (south-easterly / southerly) sectors vs everything else
    south_east = ["ESE", "SE", "SSE", "S", "SSW", "SW"]
    in_grp = dv["WindGustDir"].isin(south_east)
    S["se_sector_rain_day_pct"] = round(dv[in_grp]["IsRainDay"].mean() * 100, 1)
    S["other_sector_rain_day_pct"] = round(dv[~in_grp]["IsRainDay"].mean() * 100, 1)
    S["se_sector_share_pct"] = round(in_grp.mean() * 100, 1)
    S["se_sector_share_of_rain_days_pct"] = round(dv[in_grp]["IsRainDay"].sum() / dv["IsRainDay"].sum() * 100, 1)
    S["se_sector_share_of_rain_mm_pct"] = round(dv[in_grp]["Rainfall"].sum() / dv["Rainfall"].sum() * 100, 1)
    S["w_dir_share_pct"] = round((dv["WindGustDir"] == "W").mean() * 100, 1)
    S["w_dir_rain_day_pct"] = round(dv[dv["WindGustDir"] == "W"]["IsRainDay"].mean() * 100, 1)
    emit("South-easterly/southerly sector (ESE,SE,SSE,S,SSW,SW) vs rest", pd.Series({
        "share of days %": S["se_sector_share_pct"], "rain-day % in sector": S["se_sector_rain_day_pct"],
        "rain-day % elsewhere": S["other_sector_rain_day_pct"], "share of all rain days %": S["se_sector_share_of_rain_days_pct"],
        "share of all rain mm %": S["se_sector_share_of_rain_mm_pct"]}))
    # gust seasonality and strongest events
    gs = df.groupby("Season")["WindGustSpeed"].mean().reindex(SEASONS).round(1)
    emit("Mean gust by season", gs)
    S["gust_by_season"] = gs.to_dict()
    S["gust_ge70_days"] = int((df["WindGustSpeed"] >= 70).sum())
    S["gust_ge50_days"] = int((df["WindGustSpeed"] >= 50).sum())
    s70 = df[df["WindGustSpeed"] >= 70]
    emit("Gust >= 70 by season", s70["Season"].value_counts())
    S["gust_ge70_by_season"] = s70["Season"].value_counts().to_dict()
    top_g = df.nlargest(8, "WindGustSpeed")[["Date", "WindGustSpeed", "WindGustDir", "Rainfall", "Pressure9am"]]
    emit("TOP 8 gust days", top_g.to_string(index=False))
    S["top_gust_days"] = [{"date": r.Date.strftime("%Y-%m-%d"), "kmh": int(r.WindGustSpeed), "dir": r.WindGustDir}
                          for r in top_g.itertuples()]
    S["wind_9am_vs_3pm"] = [round(df["WindSpeed9am"].mean(), 1), round(df["WindSpeed3pm"].mean(), 1)]

    # ------------------------------------------------------------------ humidity / pressure
    hs = df.groupby("Season")[["Humidity9am", "Humidity3pm"]].mean().reindex(SEASONS).round(1)
    emit("Humidity by season", hs)
    S["humidity_by_season"] = hs.reset_index().to_dict(orient="list")
    S["humidity_drop_9to3"] = round(df["HumidityDrop_9to3"].mean(), 1)
    hum_rain = df.groupby("IsRainDay")[["Humidity9am", "Humidity3pm", "Pressure9am", "Sunshine", "Cloud3pm", "MaxTemp"]].mean().round(1)
    emit("Conditions on rain days (1) vs dry days (0)", hum_rain)
    S["rain_vs_dry"] = hum_rain.to_dict(orient="index")
    bins = pd.cut(df["Humidity3pm"], [0, 40, 55, 70, 85, 101], right=False)
    hb = df.groupby(bins, observed=True).agg(days=("Date", "size"), rain_tmrw=("RainTomorrow_Flag", "mean"), rain_today=("IsRainDay", "mean"))
    hb[["rain_tmrw", "rain_today"]] = (hb[["rain_tmrw", "rain_today"]] * 100).round(1)
    emit("Rain probability by 3pm humidity band", hb)
    S["rain_by_humidity_band"] = {str(k): [float(v.rain_today), float(v.rain_tmrw), int(v.days)] for k, v in hb.iterrows()}
    pb = pd.cut(df["Pressure9am"], [0, 1010, 1015, 1020, 1025, 2000], right=False)
    pbt = df.groupby(pb, observed=True).agg(days=("Date", "size"), rain_today=("IsRainDay", "mean"), rain_tmrw=("RainTomorrow_Flag", "mean"))
    pbt[["rain_today", "rain_tmrw"]] = (pbt[["rain_today", "rain_tmrw"]] * 100).round(1)
    emit("Rain probability by 9am pressure band (hPa)", pbt)
    S["rain_by_pressure_band"] = {str(k): [float(v.rain_today), float(v.rain_tmrw), int(v.days)] for k, v in pbt.iterrows()}
    # pressure fall 9am -> 3pm on rain days
    pc = df.groupby("IsRainDay")["PressureChange_9to3"].mean().round(2)
    emit("Mean pressure change 9am->3pm (hPa) by rain day", pc)
    S["pressure_change_by_rainday"] = {int(k): float(v) for k, v in pc.items()}

    # ------------------------------------------------------------------ correlations
    cols = ["MaxTemp", "MinTemp", "Rainfall", "Sunshine", "Evaporation", "WindGustSpeed", "Humidity9am", "Humidity3pm",
            "Pressure9am", "Pressure3pm", "Cloud9am", "Cloud3pm", "Temp3pm"]
    corr = df[cols].corr(method="spearman").round(2)
    emit("Spearman correlation (rainfall is skewed so rank correlation is used)", corr)
    S["corr_hum3_sun"] = float(corr.loc["Humidity3pm", "Sunshine"])
    S["corr_rain_hum3"] = float(corr.loc["Rainfall", "Humidity3pm"])
    S["corr_rain_sun"] = float(corr.loc["Rainfall", "Sunshine"])
    S["corr_maxt_evap"] = float(corr.loc["MaxTemp", "Evaporation"])
    S["corr_maxt_pressure3"] = float(corr.loc["MaxTemp", "Pressure3pm"])
    S["corr_maxt_hum3"] = float(corr.loc["MaxTemp", "Humidity3pm"])
    S["corr_rain_cloud3"] = float(corr.loc["Rainfall", "Cloud3pm"])
    S["corr_rain_pressure9"] = float(corr.loc["Rainfall", "Pressure9am"])
    S["corr_maxt_min"] = float(corr.loc["MaxTemp", "MinTemp"])
    S["corr_rain_gust"] = float(corr.loc["Rainfall", "WindGustSpeed"])

    # ------------------------------------------------------------------ anomalies
    an = df[df["IsAnomaly"] == 1]
    emit("ANOMALY days by type", an["AnomalyType"].str.split("; ").explode().value_counts())
    emit("ANOMALY days by year", an.groupby("Year").size())
    S["anomalies_by_year"] = {int(k): int(v) for k, v in an.groupby("Year").size().items()}
    S["anomalies_by_type"] = an["AnomalyType"].str.split("; ").explode().value_counts().to_dict()
    S["anomalies_by_season"] = an.groupby("Season").size().reindex(SEASONS).fillna(0).astype(int).to_dict()
    heat = df[df["AnomalyType"].str.contains("Heat")][["Date", "MaxTemp", "MaxTemp_Z", "WindGustSpeed", "WindGustDir"]]
    emit("HEAT anomaly days (z>=3 vs month)", heat.to_string(index=False))
    S["heat_anomaly_days"] = int(len(heat))
    S["heat_anomaly_by_year"] = {int(k): int(v) for k, v in heat.groupby(heat["Date"].dt.year).size().items()}
    S["heat_anomaly_dirs"] = heat["WindGustDir"].value_counts().to_dict()
    # multi-variable "compound" days
    comp = an[an["AnomalyType"].str.contains(";")]
    emit("COMPOUND anomaly days (>=2 flags)", comp[["Date", "AnomalyType", "MaxTemp", "Rainfall", "WindGustSpeed"]].to_string(index=False))
    S["compound_anomaly_days"] = int(len(comp))
    top_z = df.assign(absz=df["MaxTemp_Z"].abs()).nlargest(8, "absz")[["Date", "MaxTemp", "MaxTemp_Z"]]
    emit("Largest MaxTemp z-scores", top_z.to_string(index=False))
    S["top_heat_z"] = [{"date": r.Date.strftime("%Y-%m-%d"), "t": float(r.MaxTemp), "z": float(r.MaxTemp_Z)} for r in top_z.itertuples()]
    # rain events: rain-anomaly by season and heavy rain (>25mm) by month
    hv = df[df["Rainfall"] > 25]
    emit("Heavy rain days (>25mm) by month", hv["MonthName"].value_counts().reindex(MONTHS).fillna(0).astype(int))
    S["heavy_rain_days"] = int(len(hv))
    S["heavy_rain_by_season"] = hv["Season"].value_counts().reindex(SEASONS).fillna(0).astype(int).to_dict()
    S["heavy_rain_share_of_total_mm"] = round(hv["Rainfall"].sum() / df["Rainfall"].sum() * 100, 1)

    # ------------------------------------------------------------------ extra: heat context, storms, simple rain rule
    h35 = df[df["MaxTemp"] >= 35]
    S["ge35_mean_humidity3pm"] = round(h35["Humidity3pm"].mean(), 1)
    S["ge35_share_below_25_humidity"] = round((h35["Humidity3pm"] < 25).mean() * 100, 1)
    S["ge35_by_season"] = h35["Season"].value_counts().reindex(SEASONS).fillna(0).astype(int).to_dict()
    # like-for-like: four full years each side (2008 and 2017 are partial, so both are left out)
    for lo, hi in [(2009, 2012), (2013, 2016)]:
        blk = df[df["Year"].between(lo, hi)]
        S[f"ge35_days_{lo}_{hi}"] = int((blk["MaxTemp"] >= 35).sum())
        S[f"ge30_days_{lo}_{hi}"] = int((blk["MaxTemp"] >= 30).sum())
        S[f"obs_days_{lo}_{hi}"] = int(len(blk))
    emit("Days >= 35C: context", pd.Series({k: S[k] for k in S if k.startswith(("ge35", "ge30_days", "obs_days"))}))
    S["ge30_rate_per_100d_2008_12"] = round((first["MaxTemp"] >= 30).mean() * 100, 2)
    S["ge30_rate_per_100d_2013_17"] = round((second["MaxTemp"] >= 30).mean() * 100, 2)
    emit("Days >= 30C per 100 days (all rows, month mix uneven)", pd.Series({"2008-12": S["ge30_rate_per_100d_2008_12"], "2013-17": S["ge30_rate_per_100d_2013_17"]}))

    hvv = df[df["Rainfall"] > 25]
    S["heavy_plus_days_pct"] = round(len(hvv) / n * 100, 1)
    S["heavy_plus_mm_share_pct"] = round(hvv["Rainfall"].sum() / df["Rainfall"].sum() * 100, 1)
    S["total_rain_mm"] = round(df["Rainfall"].sum(), 0)
    emit("Days > 25 mm", pd.Series({"share of days %": S["heavy_plus_days_pct"], "share of rain mm %": S["heavy_plus_mm_share_pct"]}))
    r2 = (df["Rainfall"] + df["Rainfall"].shift(-1)).where((df["Date"].shift(-1) - df["Date"]).dt.days == 1)
    two = df.assign(two_day_mm=r2).nlargest(4, "two_day_mm")[["Date", "two_day_mm"]]
    emit("Largest consecutive 2-day rainfall totals", two.to_string(index=False))
    S["two_day_top"] = [{"date": r.Date.strftime("%Y-%m-%d"), "mm": round(float(r.two_day_mm), 1)} for r in two.itertuples()]

    # a one-line rule: "3pm humidity >= 70% -> rain tomorrow"
    pred = (df["Humidity3pm"] >= 70).astype(int)
    act = df["RainTomorrow_Flag"]
    tp, fp, fn = int(((pred == 1) & (act == 1)).sum()), int(((pred == 1) & (act == 0)).sum()), int(((pred == 0) & (act == 1)).sum())
    S["rule_hum70_accuracy_pct"] = round((pred == act).mean() * 100, 1)
    S["rule_hum70_precision_pct"] = round(tp / (tp + fp) * 100, 1)
    S["rule_hum70_recall_pct"] = round(tp / (tp + fn) * 100, 1)
    S["rule_hum70_days_flagged_pct"] = round(pred.mean() * 100, 1)
    emit("Rule: Humidity3pm >= 70 -> RainTomorrow", pd.Series({k: S[k] for k in S if k.startswith("rule_")}))
    r_h = stats.spearmanr(df["Humidity3pm"], df["RainTomorrow_Flag"])
    r_p = stats.spearmanr(df["Pressure9am"], df["RainTomorrow_Flag"])
    r_s = stats.spearmanr(df["Sunshine"], df["RainTomorrow_Flag"])
    cl = df.dropna(subset=["Cloud3pm"])
    r_c = stats.spearmanr(cl["Cloud3pm"], cl["RainTomorrow_Flag"])
    S["rank_corr_rain_tomorrow"] = {"Humidity3pm": round(float(r_h[0]), 2), "Pressure9am": round(float(r_p[0]), 2),
                                    "Sunshine": round(float(r_s[0]), 2), "Cloud3pm": round(float(r_c[0]), 2)}
    emit("Rank correlation with RainTomorrow", pd.Series(S["rank_corr_rain_tomorrow"]))

    # save
    with open("analysis_output.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(out_lines) + "\n")
    with open("analysis_summary.json", "w", encoding="utf-8") as f:
        json.dump(S, f, indent=2, default=lambda o: o.item() if hasattr(o, "item") else str(o))
    print("\n".join(out_lines))


if __name__ == "__main__":
    main()
