"""Step 2: KPIs, segment tables and statistical checks for the customer data.

Reads  Cleaned_Customers.csv
Writes analysis_summary.json  (every KPI, table and test - feeds the charts, dashboards and KEY_INSIGHTS.md)
       analysis_output.txt    (human-readable printout of the same)

Each metric uses every row that is valid for it (pairwise), e.g. average rating uses the 1,487 valid ratings,
revenue uses the 2,003 recorded amounts. Every "is this difference real?" question gets a significance test
(p < 0.05 = unlikely to be chance).

KPI groups and the question each answers:
  customers    -> Customers, gender mix, median age              (who buys?)
  revenue      -> Revenue, AOV, median order, revenue / month   (how much do they spend?)
  products     -> Category revenue share, top category, unassigned revenue (what do they buy?)
  satisfaction -> Avg rating, satisfied %, dissatisfied %       (are they happy?)
  trend        -> Purchases / month, H1 year-on-year, trend slope (is the business growing?)
  data quality -> Complete-record rate, usable-field rates        (can we trust it?)
"""
import json

import numpy as np
import pandas as pd
from scipy import stats

df = pd.read_csv("Cleaned_Customers.csv", parse_dates=["Purchase_Date"])
N = len(df)
A = "Purchase_Amount"
lines = []


def out(s=""):
    lines.append(str(s))


def r2(x, d=2):
    return None if pd.isna(x) else round(float(x), d)


AGE = ["15-29", "30-44", "45-59", "60-74", "75-90"]
CATS = ["Books", "Clothing", "Electronics", "Home", "Toys"]
WD = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
BANDS = ["Under $250", "$250-499", "$500-749", "$750+"]


def seg(col, order=None):
    """Customers, recorded revenue, AOV, rating and satisfaction for each value of col."""
    g = df.groupby(col)
    t = pd.DataFrame({
        "customers": g.size(),
        "priced": g[A].count(),
        "revenue": g[A].sum(),
        "aov": g[A].mean(),
        "median_order": g[A].median(),
        "rated": g["Rating"].count(),
        "avg_rating": g["Rating"].mean(),
        "satisfied": g["Rating"].apply(lambda s: (s >= 4).sum() / s.count() if s.count() else np.nan),
        "dissatisfied": g["Rating"].apply(lambda s: (s <= 2).sum() / s.count() if s.count() else np.nan),
    })
    t["customer_share"] = t.customers / t.customers.sum()
    t["revenue_share"] = t.revenue / t.revenue.sum()
    if order:
        t = t.reindex([o for o in order if o in t.index])
    return t


def kw(col, value, groups=None):
    """Kruskal-Wallis: does `value` differ between the groups of `col`?"""
    d = df[df[col].isin(groups)] if groups else df
    samples = [s.dropna().values for _, s in d.groupby(col)[value] if s.notna().sum() > 1]
    return float(stats.kruskal(*samples).pvalue)


def chi(a, b, da=None):
    d = da if da is not None else df
    ct = pd.crosstab(d[a], d[b])
    return float(stats.chi2_contingency(ct)[1])


def records(t, idx_name):
    t = t.reset_index().rename(columns={t.index.name or "index": idx_name})
    return [{k: (r2(v, 4) if isinstance(v, (float, np.floating)) else (int(v) if isinstance(v, (np.integer,)) else v))
             for k, v in row.items()} for row in t.to_dict("records")]


# ------------------------------------------------------------------ headline KPIs
amt = df[A].dropna()
rat = df["Rating"].dropna()
known_g = df[df.Gender != "Unknown"]
ages = df["Age"].dropna()
valid_dt = df[df.Date_Status == "Valid"]
full = valid_dt[valid_dt.Full_Month == "Yes"]
n_full_months = full.Year_Month.nunique()
cat_known = df[df.Product_Category != "Unknown"]
by_cat = seg("Product_Category", CATS + ["Unknown"])
top_cat = by_cat.loc[CATS, "revenue"].idxmax()
big = df[df[A] >= 750]

kpi = {
    "raw_rows": 2150, "duplicates_removed": 50, "customers": N,
    "priced_purchases": int(amt.size), "missing_amounts": int(df[A].isna().sum()),
    "revenue": r2(amt.sum()), "aov": r2(amt.mean()), "median_order": r2(amt.median()),
    "min_order": r2(amt.min()), "max_order": r2(amt.max()),
    "revenue_per_full_month": r2(full[A].sum() / n_full_months), "purchases_per_full_month": r2(len(full) / n_full_months, 1),
    "full_months": int(n_full_months), "first_date": str(valid_dt.Purchase_Date.min().date()),
    "last_date": str(valid_dt.Purchase_Date.max().date()),
    "big_ticket_order_share": r2(big[A].count() / amt.size, 4), "big_ticket_revenue_share": r2(big[A].sum() / amt.sum(), 4),
    "rated": int(rat.size), "avg_rating": r2(rat.mean()), "median_rating": r2(rat.median(), 1),
    "satisfied_share": r2((rat >= 4).mean(), 4), "neutral_share": r2((rat == 3).mean(), 4),
    "dissatisfied_share": r2((rat <= 2).mean(), 4), "five_star_share": r2((rat == 5).mean(), 4),
    "one_star_share": r2((rat == 1).mean(), 4),
    "net_satisfaction": r2((rat >= 4).mean() - (rat <= 2).mean(), 4),
    "female_share_known": r2((known_g.Gender == "Female").mean(), 4), "male_share_known": r2((known_g.Gender == "Male").mean(), 4),
    "gender_unknown_share": r2((df.Gender == "Unknown").mean(), 4),
    "valid_ages": int(ages.size), "median_age": r2(ages.median(), 1), "mean_age": r2(ages.mean(), 1),
    "min_age": int(ages.min()), "max_age": int(ages.max()),
    "top_category": top_cat, "top_category_revenue": r2(by_cat.loc[top_cat, "revenue"]),
    "top_category_share_of_known": r2(by_cat.loc[top_cat, "revenue"] / by_cat.loc[CATS, "revenue"].sum(), 4),
    "unknown_category_customers": int(by_cat.loc["Unknown", "customers"]),
    "unknown_category_revenue": r2(by_cat.loc["Unknown", "revenue"]),
    "unknown_category_revenue_share": r2(by_cat.loc["Unknown", "revenue_share"], 4),
    "complete_record_rate": r2((df.Complete_Record == "Yes").mean(), 4), "complete_records": int((df.Complete_Record == "Yes").sum()),
    "email_domains": int(df.Email_Domain.nunique()),
}
quality = {  # share of rows usable for each field
    "Age": (df.Age_Status == "Valid").mean(), "Rating": (df.Rating_Status == "Valid").mean(),
    "Product category": (df.Product_Category != "Unknown").mean(), "Gender": (df.Gender != "Unknown").mean(),
    "Purchase date": (df.Date_Status == "Valid").mean(), "Purchase amount": (df.Amount_Status == "Recorded").mean(),
    "Phone": 0.0,
}
quality_detail = {
    "Age": {"Valid": int((df.Age_Status == "Valid").sum()), "Blank": int((df.Age_Status == "Missing").sum()),
            "Invalid": int(df.Age_Status.str.startswith("Placeholder").sum()), "invalid_label": "-1 / 200 placeholders"},
    "Rating": {"Valid": int((df.Rating_Status == "Valid").sum()), "Blank": int((df.Rating_Status == "Missing").sum()),
               "Invalid": int((df.Rating_Status != "Valid").sum() - (df.Rating_Status == "Missing").sum()), "invalid_label": "'10' on a 1-5 scale"},
    "Product category": {"Valid": int((df.Product_Category != "Unknown").sum()), "Blank": int((df.Product_Category == "Unknown").sum()),
                         "Invalid": 0, "invalid_label": ""},
    "Gender": {"Valid": int((df.Gender != "Unknown").sum()), "Blank": int((df.Gender == "Unknown").sum()), "Invalid": 0,
               "invalid_label": "6 spellings merged"},
    "Purchase date": {"Valid": int((df.Date_Status == "Valid").sum()), "Blank": 0, "Invalid": int((df.Date_Status == "Invalid").sum()),
                      "invalid_label": "'32/13/2020'"},
    "Purchase amount": {"Valid": int(amt.size), "Blank": int(df[A].isna().sum()), "Invalid": 0, "invalid_label": ""},
    "Phone": {"Valid": 0, "Blank": int((df.Phone_Status == "Missing").sum()), "Invalid": int((df.Phone_Status == "Placeholder").sum()),
              "invalid_label": "dummy 0123456789 / 0987654321"},
}

# ------------------------------------------------------------------ segment tables
by_gender = seg("Gender", ["Female", "Male", "Unknown"])
by_age = seg("Age_Group", AGE + ["Unknown"])
by_band = seg("Spend_Band", BANDS + ["Unknown"])
by_domain = seg("Email_Domain")
by_wd = seg("Weekday", WD)
rating_dist = rat.value_counts().sort_index()

# rating distribution per segment (for the diverging stacked bars)
def rating_mix(col, order):
    ct = pd.crosstab(df[col], df["Rating"], normalize="index").reindex(order)
    ct.columns = [int(c) for c in ct.columns]
    return {k: [r2(v, 4) for v in row] for k, row in zip(ct.index, ct.values)}


mix = {"Product_Category": rating_mix("Product_Category", CATS + ["Unknown"]), "Gender": rating_mix("Gender", ["Female", "Male", "Unknown"]),
       "Age_Group": rating_mix("Age_Group", AGE), "Spend_Band": rating_mix("Spend_Band", BANDS)}

# ------------------------------------------------------------------ time
monthly = (valid_dt.groupby("Year_Month").agg(purchases=("Customer_ID", "size"), revenue=(A, "sum"), aov=(A, "mean"),
                                              avg_rating=("Rating", "mean"), full=("Full_Month", "first")))
monthly["days_covered"] = [((min(pd.Period(m).end_time.normalize(), valid_dt.Purchase_Date.max()) -
                             max(pd.Period(m).start_time, valid_dt.Purchase_Date.min())).days + 1) for m in monthly.index]
fm = monthly[monthly.full == "Yes"]
x = np.arange(len(fm))
lr_n, lr_rev = stats.linregress(x, fm.purchases), stats.linregress(x, fm.revenue)
quarterly = valid_dt.groupby("Quarter").agg(purchases=("Customer_ID", "size"), revenue=(A, "sum"), aov=(A, "mean"))
quarterly["days_covered"] = monthly.groupby(monthly.index.str[:4] + "-Q" +
                                            ((monthly.index.str[5:].astype(int) - 1) // 3 + 1).astype(str)).days_covered.sum()
quarterly["purchases_per_30d"] = quarterly.purchases / quarterly.days_covered * 30

# like-for-like years: January-June of each year (the only half-year present in full in 2023, 2024 and 2025)
h1 = valid_dt[valid_dt.Month_Num <= 6].groupby("Year").agg(purchases=("Customer_ID", "size"), revenue=(A, "sum"),
                                                          aov=(A, "mean"), avg_rating=("Rating", "mean"))
h1.index = h1.index.astype(int)
h1 = h1.loc[[2023, 2024, 2025]]

# month of year: raw counts are distorted because Aug-Sep occur in 2 of the years covered, Jan-Jun in 3
days = pd.date_range(valid_dt.Purchase_Date.min(), valid_dt.Purchase_Date.max())
exposure = pd.Series(days.month).value_counts().sort_index()
moy = valid_dt.groupby("Month_Num").agg(purchases=("Customer_ID", "size"), revenue=(A, "sum"), aov=(A, "mean"), avg_rating=("Rating", "mean"))
moy.index = moy.index.astype(int)
moy["days_covered"] = exposure
moy["years_covered"] = (moy.days_covered / pd.Series({m: pd.Period(f"2023-{m:02d}").days_in_month for m in range(1, 13)})).round(2)
moy["purchases_per_30d"] = moy.purchases / moy.days_covered * 30
moy.index = [MONTHS[m - 1] for m in moy.index]

wd_days = pd.Series(days.dayofweek).value_counts().sort_index()

# ------------------------------------------------------------------ tests
tests = {
    "Amount by gender (Kruskal-Wallis)": kw("Gender", A, ["Female", "Male"]),
    "Amount by age group (Kruskal-Wallis)": kw("Age_Group", A, AGE),
    "Amount by category (Kruskal-Wallis)": kw("Product_Category", A, CATS),
    "Amount by weekday (Kruskal-Wallis)": kw("Weekday", A, WD),
    "Amount by email domain (Kruskal-Wallis)": kw("Email_Domain", A),
    "Rating by gender (Kruskal-Wallis)": kw("Gender", "Rating", ["Female", "Male"]),
    "Rating by age group (Kruskal-Wallis)": kw("Age_Group", "Rating", AGE),
    "Rating by category (Kruskal-Wallis)": kw("Product_Category", "Rating", CATS),
    "Rating by spend band (Kruskal-Wallis)": kw("Spend_Band", "Rating", BANDS),
    "Category mix by gender (chi-square)": chi("Product_Category", "Gender", df[df.Product_Category.isin(CATS) & df.Gender.isin(["Female", "Male"])]),
    "Category mix by age group (chi-square)": chi("Product_Category", "Age_Group", df[df.Product_Category.isin(CATS) & df.Age_Group.isin(AGE)]),
    "Age vs amount (Spearman)": float(stats.spearmanr(df.Age, df[A], nan_policy="omit").pvalue),
    "Age vs rating (Spearman)": float(stats.spearmanr(df.Age, df.Rating, nan_policy="omit").pvalue),
    "Amount vs rating (Spearman)": float(stats.spearmanr(df[A], df.Rating, nan_policy="omit").pvalue),
    "Monthly purchases trend (linear regression, full months)": float(lr_n.pvalue),
    "Monthly revenue trend (linear regression, full months)": float(lr_rev.pvalue),
    "Month-of-year purchases vs calendar coverage (chi-square)": float(stats.chisquare(moy.purchases, moy.days_covered / moy.days_covered.sum() * moy.purchases.sum()).pvalue),
    "Weekday purchases vs calendar coverage (chi-square)": float(stats.chisquare(by_wd.customers.values, wd_days.values / wd_days.sum() * by_wd.customers.sum()).pvalue),
    "H1 purchases 2023 vs 2024 vs 2025 (chi-square)": float(stats.chisquare(h1.purchases).pvalue),
}
# randomness checks: here a HIGH p means the column is indistinguishable from random generation
randomness = {
    "Amounts follow a uniform $5-$1,000 distribution (Kolmogorov-Smirnov)": float(stats.kstest(amt, "uniform", args=(5, 995)).pvalue),
    "Ages follow a uniform 15-90 distribution (Kolmogorov-Smirnov, discrete-adjusted)": float(stats.kstest(ages + np.random.default_rng(0).uniform(-0.5, 0.5, ages.size), "uniform", args=(14.5, 76)).pvalue),
    "Ratings 1-5 equally likely (chi-square)": float(stats.chisquare(rating_dist.values).pvalue),
    "Gender independent of first name (chi-square)": chi("First_Name", "Gender", df[df.Gender != "Unknown"]),
}
corr = {
    "age_amount_rho": r2(stats.spearmanr(df.Age, df[A], nan_policy="omit").statistic, 3),
    "age_rating_rho": r2(stats.spearmanr(df.Age, df.Rating, nan_policy="omit").statistic, 3),
    "amount_rating_rho": r2(stats.spearmanr(df[A], df.Rating, nan_policy="omit").statistic, 3),
    "purchases_slope_per_month": r2(lr_n.slope, 3), "revenue_slope_per_month": r2(lr_rev.slope, 1),
}

# 95% confidence intervals of AOV per segment (for the "does any segment stand out?" chart)
def ci_rows(col, order, label):
    rows = []
    for v in order:
        s = df.loc[df[col] == v, A].dropna()
        h = stats.t.ppf(0.975, s.size - 1) * s.std(ddof=1) / np.sqrt(s.size)
        rows.append({"dimension": label, "segment": v, "n": int(s.size), "aov": r2(s.mean()), "lo": r2(s.mean() - h), "hi": r2(s.mean() + h)})
    return rows


aov_ci = (ci_rows("Gender", ["Female", "Male"], "Gender") + ci_rows("Age_Group", AGE, "Age group") +
          ci_rows("Product_Category", CATS, "Category") + ci_rows("Weekday", WD, "Weekday"))
rating_ci = []
for col, order, label in [("Gender", ["Female", "Male"], "Gender"), ("Age_Group", AGE, "Age group"),
                          ("Product_Category", CATS, "Category"), ("Spend_Band", BANDS, "Spend band")]:
    for v in order:
        s = df.loc[df[col] == v, "Rating"].dropna()
        h = stats.t.ppf(0.975, s.size - 1) * s.std(ddof=1) / np.sqrt(s.size)
        rating_ci.append({"dimension": label, "segment": v, "n": int(s.size), "avg": r2(s.mean()), "lo": r2(s.mean() - h), "hi": r2(s.mean() + h)})

cat_gender = pd.crosstab(cat_known.Product_Category, cat_known.Gender, normalize="index").round(4)

S = {
    "kpi": kpi, "quality": {k: r2(v, 4) for k, v in quality.items()}, "quality_detail": quality_detail,
    "tests": {k: r2(v, 4) for k, v in tests.items()}, "randomness": {k: r2(v, 4) for k, v in randomness.items()}, "corr": corr,
    "by_gender": records(by_gender, "Gender"), "by_age": records(by_age, "Age_Group"),
    "by_category": records(by_cat, "Product_Category"), "by_spend_band": records(by_band, "Spend_Band"),
    "by_domain": records(by_domain, "Email_Domain"), "by_weekday": records(by_wd, "Weekday"),
    "rating_dist": {int(k): int(v) for k, v in rating_dist.items()}, "rating_mix": mix,
    "monthly": records(monthly, "Year_Month"), "quarterly": records(quarterly, "Quarter"),
    "h1": records(h1, "Year"), "month_of_year": records(moy, "Month"),
    "aov_ci": aov_ci, "rating_ci": rating_ci,
    "category_gender_mix": {c: cat_gender.loc[c].to_dict() for c in cat_gender.index},
}
json.dump(S, open("analysis_summary.json", "w", encoding="utf-8"), indent=2, ensure_ascii=False, default=str)

# ------------------------------------------------------------------ printout
pd.set_option("display.width", 200)
fmt = lambda t: t.round(3).to_string()
out("=== HEADLINE KPIs ===")
for k, v in kpi.items():
    out(f"  {k:32s} {v}")
out("\n=== SHARE OF ROWS USABLE PER FIELD ===")
for k, v in quality.items():
    out(f"  {k:18s} {v:6.1%}   {quality_detail[k]}")
for name, t in [("GENDER", by_gender), ("AGE GROUP", by_age), ("CATEGORY", by_cat), ("SPEND BAND", by_band),
                ("EMAIL DOMAIN", by_domain), ("WEEKDAY", by_wd)]:
    out(f"\n=== BY {name} ===")
    out(fmt(t))
out("\n=== RATING DISTRIBUTION ===")
out((rating_dist / rating_dist.sum()).round(3).to_string())
out("\n=== MONTHLY (all months with valid dates) ===")
out(fmt(monthly))
out("\n=== QUARTERLY ===")
out(fmt(quarterly))
out("\n=== JANUARY-JUNE, YEAR ON YEAR ===")
out(fmt(h1))
out("\n=== MONTH OF YEAR (raw vs per 30 days of coverage) ===")
out(fmt(moy))
out("\n=== CATEGORY x GENDER (row %) ===")
out(fmt(cat_gender))
out("\n=== AOV 95% CI BY SEGMENT ===")
for r in aov_ci:
    out(f"  {r['dimension']:10s} {r['segment']:12s} n={r['n']:4d}  ${r['aov']:.0f}  [{r['lo']:.0f}, {r['hi']:.0f}]")
out("\n=== SIGNIFICANCE TESTS (p < 0.05 = a real difference) ===")
for k, v in tests.items():
    out(f"  {'REAL ' if v < 0.05 else 'none '} p = {v:.3f}   {k}")
out("\n=== RANDOMNESS CHECKS (p > 0.05 = indistinguishable from random generation) ===")
for k, v in randomness.items():
    out(f"  {'random' if v > 0.05 else 'NOT random'} p = {v:.3f}   {k}")
out("\n=== CORRELATIONS / TRENDS ===")
for k, v in corr.items():
    out(f"  {k:28s} {v}")
open("analysis_output.txt", "w", encoding="utf-8").write("\n".join(lines))
print("\n".join(lines))
