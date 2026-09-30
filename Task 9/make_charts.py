"""Step 3: static charts (PNG) for the summary report, README and submission.

Reads  Cleaned_Customers.csv, analysis_summary.json
Writes charts/01_data_quality.png ... charts/08_segment_comparison.png

Colour roles (validated with the dataviz palette validator):
  series blue #2a78d6 / orange #eb6834 (categorical slots 1-2), gray #b9b7ae = "unknown / no data",
  age bands = one-hue ordinal blue ramp, ratings = diverging red <- gray -> blue (1-2 stars red, 3 gray, 4-5 blue).
Every chart title states the takeaway; the subtitle says what is plotted.
"""
import json
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import FuncFormatter

S = json.load(open("analysis_summary.json", encoding="utf-8"))
K = S["kpi"]
df = pd.read_csv("Cleaned_Customers.csv", parse_dates=["Purchase_Date"])
os.makedirs("charts", exist_ok=True)

SURF, INK, INK2, MUTED, GRID, AXIS = "#fcfcfb", "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7"
BLUE, ORANGE, GRAY, LIGHTBLUE = "#2a78d6", "#eb6834", "#b9b7ae", "#86b6ef"
ORD = ["#86b6ef", "#3987e5", "#256abf", "#184f95", "#0d366b"]               # ordinal ramp (age bands)
STARS = {1: "#e34948", 2: "#f19a99", 3: "#d5d3cb", 4: "#86b6ef", 5: "#2a78d6"}  # diverging (rating)
AGE = ["15-29", "30-44", "45-59", "60-74", "75-90"]
CATS = ["Books", "Clothing", "Electronics", "Home", "Toys"]

plt.rcParams.update({
    "font.family": ["Segoe UI", "DejaVu Sans"], "font.size": 10, "text.color": INK2,
    "axes.facecolor": SURF, "figure.facecolor": SURF, "savefig.facecolor": SURF,
    "axes.edgecolor": AXIS, "axes.linewidth": 0.8, "axes.labelcolor": MUTED, "axes.titlesize": 11.5,
    "axes.titleweight": "semibold", "axes.titlecolor": INK, "axes.titlelocation": "left", "axes.titlepad": 10,
    "xtick.color": MUTED, "ytick.color": MUTED, "xtick.labelcolor": INK2, "ytick.labelcolor": INK2,
    "axes.grid": False, "grid.color": GRID, "grid.linewidth": 0.8, "legend.frameon": False,
    "axes.spines.top": False, "axes.spines.right": False, "text.parse_math": False,
})
money = FuncFormatter(lambda v, _: f"${v / 1000:,.0f}K" if abs(v) >= 1000 else f"${v:,.0f}")
pct = FuncFormatter(lambda v, _: f"{v:.0%}")


def headline(fig, title, sub):
    fig.text(0.012, 0.975, title, fontsize=15, fontweight="bold", color=INK, va="top")
    fig.text(0.012, 0.915, sub, fontsize=10.5, color=INK2, va="top")


def save(fig, name):
    fig.savefig(f"charts/{name}.png", dpi=150)
    plt.close(fig)
    print("saved", name)


def ygrid(ax):
    ax.grid(axis="y")
    ax.set_axisbelow(True)
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)


def xgrid(ax):
    ax.grid(axis="x")
    ax.set_axisbelow(True)
    ax.spines["bottom"].set_visible(False)
    ax.tick_params(axis="x", length=0)


def bar_labels(ax, bars, texts, horizontal=False, pad=3, color=INK2, size=9.5):
    for b, t in zip(bars, texts):
        if horizontal:
            ax.annotate(t, (b.get_width(), b.get_y() + b.get_height() / 2), xytext=(pad, 0), textcoords="offset points",
                        va="center", ha="left", color=color, fontsize=size)
        else:
            ax.annotate(t, (b.get_x() + b.get_width() / 2, b.get_height()), xytext=(0, pad), textcoords="offset points",
                        ha="center", va="bottom", color=color, fontsize=size)


# ------------------------------------------------------------------ 01 data quality
qd = S["quality_detail"]
fields = sorted(qd, key=lambda f: qd[f]["Valid"])            # worst at the bottom after barh reversal
fig, ax = plt.subplots(figsize=(12, 5.4))
fig.subplots_adjust(left=0.15, right=0.97, top=0.78, bottom=0.12)
y = np.arange(len(fields))
left = np.zeros(len(fields))
for key, col, lab in [("Valid", BLUE, "Usable"), ("Blank", GRAY, "Blank"), ("Invalid", ORANGE, "Invalid / placeholder")]:
    vals = np.array([qd[f][key] / K["customers"] for f in fields])
    bars = ax.barh(y, vals, left=left, color=col, height=0.56, label=lab, edgecolor=SURF, linewidth=2)
    for b, v in zip(bars, vals):
        if v >= 0.07:
            ax.text(b.get_x() + b.get_width() / 2, b.get_y() + b.get_height() / 2, f"{v:.0%}", ha="center", va="center",
                    color="#ffffff" if col == BLUE else INK, fontsize=9.5, fontweight="semibold")
    left += vals
ax.set_yticks(y, fields)
for i, f in enumerate(fields):
    note = qd[f]["invalid_label"]
    if note:
        ax.annotate(note, (1, i), xytext=(6, 0), textcoords="offset points", va="center", fontsize=8.5, color=MUTED,
                    annotation_clip=False)
ax.set_xlim(0, 1)
ax.xaxis.set_major_formatter(pct)
ax.spines["left"].set_visible(False)
ax.tick_params(axis="y", length=0)
ax.legend(loc="lower left", bbox_to_anchor=(0, 1.0), ncol=3, fontsize=9.5, handlelength=1.2, borderaxespad=0.2)
fig.subplots_adjust(right=0.80)
headline(fig, f"Only {K['complete_record_rate']:.1%} of customer records are complete",
         f"Share of the {K['customers']:,} customers with a usable value in each field, after removing 50 duplicate rows")
save(fig, "01_data_quality")

# ------------------------------------------------------------------ 02 age and gender
fig, (a1, a2) = plt.subplots(1, 2, figsize=(12, 5), gridspec_kw={"width_ratios": [1.35, 1]})
fig.subplots_adjust(left=0.05, right=0.97, top=0.76, bottom=0.12, wspace=0.28)
ag = {r["Age_Group"]: r for r in S["by_age"]}
bars = a1.bar(AGE, [ag[g]["customers"] for g in AGE], color=ORD, width=0.6)
bar_labels(a1, bars, [f"{ag[g]['customers']}  ({ag[g]['customers'] / K['valid_ages']:.0%})" for g in AGE])
a1.set_title(f"Customers by age group (the {K['valid_ages']} with a real age)")
a1.set_xlabel("age (15-year bands)")
ygrid(a1)
a1.margins(y=0.15)
gd = {r["Gender"]: r for r in S["by_gender"]}
order = ["Female", "Male", "Unknown"]
bars = a2.barh(order[::-1], [gd[g]["customers"] for g in order[::-1]], color=[GRAY, BLUE, BLUE], height=0.5)
bar_labels(a2, bars, [f"{gd[g]['customers']:,}  ({gd[g]['customer_share']:.0%})" for g in order[::-1]], horizontal=True)
a2.set_title("Customers by gender")
xgrid(a2)
a2.margins(x=0.25)
a2.spines["left"].set_color(AXIS)
headline(fig, f"Customers span every age from {K['min_age']} to {K['max_age']} (median {K['median_age']:.0f}); genders are balanced",
         f"Age is usable for only {K['valid_ages'] / K['customers']:.0%} of customers (the rest are -1, 200 or blank). "
         f"Gender is {K['female_share_known']:.0%} female / {K['male_share_known']:.0%} male where recorded")
save(fig, "02_age_gender")

# ------------------------------------------------------------------ 03 spend
amt = df.Purchase_Amount.dropna()
fig, (a1, a2) = plt.subplots(1, 2, figsize=(12, 5), gridspec_kw={"width_ratios": [1.35, 1]})
fig.subplots_adjust(left=0.06, right=0.97, top=0.76, bottom=0.12, wspace=0.25)
a1.hist(amt, bins=np.arange(0, 1050, 50), color=BLUE, edgecolor=SURF, linewidth=2)
a1.set_ylim(0, 145)
a1.axvline(K["median_order"], color=INK, lw=1.3, ymax=0.93)
a1.annotate(f"median ${K['median_order']:.0f}", (K["median_order"], 140), ha="center", fontsize=9.5, color=INK, va="center")
a1.set_title(f"Purchase amounts ({K['priced_purchases']:,} priced orders, $50 bins)")
a1.xaxis.set_major_formatter(money)
a1.set_ylabel("orders")
ygrid(a1)
bands = S["by_spend_band"][:4]
x = np.arange(4)
w = 0.36
b1 = a2.bar(x - w / 2 - 0.01, [b["customer_share"] / (1 - S["by_spend_band"][4]["customer_share"]) for b in bands], w, color=BLUE, label="% of orders")
b2 = a2.bar(x + w / 2 + 0.01, [b["revenue_share"] for b in bands], w, color=ORANGE, label="% of revenue")
bar_labels(a2, b1, [f"{b.get_height():.0%}" for b in b1], size=9)
bar_labels(a2, b2, [f"{b.get_height():.0%}" for b in b2], size=9)
a2.set_xticks(x, [b["Spend_Band"] for b in bands])
a2.yaxis.set_major_formatter(pct)
a2.set_title("Orders vs revenue by order size")
a2.legend(loc="upper left", fontsize=9.5)
ygrid(a2)
a2.margins(y=0.15)
headline(fig, f"$750+ orders are {K['big_ticket_order_share']:.0%} of orders but {K['big_ticket_revenue_share']:.0%} of revenue",
         f"Spending is spread evenly from ${K['min_order']:.0f} to ${K['max_order']:.0f} (average ${K['aov']:.0f}); "
         f"total recorded revenue ${K['revenue'] / 1e6:.2f}M. {K['missing_amounts']} orders have no amount")
save(fig, "03_spend")

# ------------------------------------------------------------------ 04 categories
cat = {r["Product_Category"]: r for r in S["by_category"]}
fig, (a1, a2) = plt.subplots(1, 2, figsize=(12, 5))
fig.subplots_adjust(left=0.09, right=0.97, top=0.76, bottom=0.12, wspace=0.35)
known = sorted(CATS, key=lambda c: cat[c]["revenue"])
names = ["Unknown"] + known
bars = a1.barh(names, [cat[c]["revenue"] for c in names], color=[GRAY] + [BLUE] * 5, height=0.56)
bar_labels(a1, bars, [f"${cat[c]['revenue'] / 1000:,.0f}K  ({cat[c]['revenue_share']:.0%})" for c in names], horizontal=True)
a1.set_title("Recorded revenue by category")
a1.xaxis.set_major_formatter(money)
xgrid(a1)
a1.margins(x=0.28)
ci = {r["segment"]: r for r in S["aov_ci"] if r["dimension"] == "Category"}
for i, c in enumerate(known):
    a2.plot([ci[c]["lo"], ci[c]["hi"]], [i, i], color=LIGHTBLUE, lw=6, solid_capstyle="round")
    a2.plot(ci[c]["aov"], i, "o", color=BLUE, ms=8, mec=SURF, mew=2)
    a2.annotate(f"${ci[c]['aov']:.0f}", (ci[c]["hi"], i), xytext=(6, 0), textcoords="offset points", va="center", fontsize=9.5)
a2.axvline(K["aov"], color=INK, lw=1.2)
a2.annotate(f"all orders ${K['aov']:.0f}", (K["aov"], len(known) - 0.45), xytext=(4, 0), textcoords="offset points", fontsize=9, color=INK)
a2.set_yticks(range(len(known)), known)
a2.set_title("Average order value with 95% confidence interval")
a2.xaxis.set_major_formatter(money)
a2.set_xlim(440, 620)
a2.set_ylim(-0.6, len(known) - 0.1)
xgrid(a2)
a2.spines["left"].set_color(AXIS)
headline(fig, f"No category leads: each has 14-16% of revenue, and {K['unknown_category_revenue_share']:.0%} is unassigned",
         f"{K['top_category']} is first by a margin chance can explain (order value p = {S['tests']['Amount by category (Kruskal-Wallis)']:.2f}). "
         f"{K['unknown_category_customers']} purchases (${K['unknown_category_revenue'] / 1000:,.0f}K) have no category")
save(fig, "04_categories")

# ------------------------------------------------------------------ 05 ratings
rd = S["rating_dist"]
tot = sum(rd.values())
fig, (a1, a2) = plt.subplots(1, 2, figsize=(12, 5), gridspec_kw={"width_ratios": [0.8, 1.4]})
fig.subplots_adjust(left=0.05, right=0.97, top=0.76, bottom=0.15, wspace=0.22)
bars = a1.bar([f"{s}★" for s in range(1, 6)], [rd[str(s)] / tot for s in range(1, 6)], color=[STARS[s] for s in range(1, 6)], width=0.62)
bar_labels(a1, bars, [f"{rd[str(s)] / tot:.0%}" for s in range(1, 6)])
a1.set_title(f"Rating distribution ({K['rated']:,} valid ratings)")
a1.yaxis.set_major_formatter(pct)
ygrid(a1)
a1.margins(y=0.15)
mix = S["rating_mix"]
rows = [("Product_Category", c) for c in CATS] + [("Gender", g) for g in ["Female", "Male"]] + [("Age_Group", g) for g in AGE]
labels = CATS + ["Female", "Male"] + [f"Age {g}" for g in AGE]
for i, (dim, key) in enumerate(rows[::-1]):
    p = mix[dim][key]                      # shares of 1..5 stars
    start = -(p[0] + p[1] + p[2] / 2)
    for s in range(5):
        a2.barh(i, p[s], left=start, color=STARS[s + 1], height=0.64, edgecolor=SURF, linewidth=1.5)
        if s in (0, 4) or p[s] >= 0.1:
            pass
        start += p[s]
    neg, posv = p[0] + p[1], p[3] + p[4]
    a2.text(-(p[0] + p[1] + p[2] / 2) - 0.015, i, f"{neg:.0%}", ha="right", va="center", fontsize=9, color=INK2)
    a2.text(p[2] / 2 + p[3] + p[4] + 0.015, i, f"{posv:.0%}", ha="left", va="center", fontsize=9, color=INK2)
a2.axvline(0, color=INK, lw=0.8)
for yline in (4.5, 6.5):
    a2.axhline(yline, color=GRID, lw=0.8)
a2.set_yticks(range(len(labels)), labels[::-1])
a2.set_xlim(-0.75, 0.75)
a2.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{abs(v):.0%}"))
a2.spines["left"].set_visible(False)
a2.tick_params(axis="y", length=0)
a2.set_title("Rating mix by segment: dissatisfied (1-2★) left, satisfied (4-5★) right")
handles = [plt.Rectangle((0, 0), 1, 1, color=STARS[s]) for s in range(1, 6)]
a2.legend(handles, [f"{s}★" for s in range(1, 6)], ncol=5, loc="upper center", bbox_to_anchor=(0.5, -0.06), fontsize=9, handlelength=1)
headline(fig, f"As many customers are unhappy ({K['dissatisfied_share']:.0%}) as happy ({K['satisfied_share']:.0%}): average {K['avg_rating']:.2f} / 5",
         "Every star level gets about a fifth of ratings, and the mix is the same in every category, gender and age group "
         f"(all p > {min(S['tests'][k] for k in S['tests'] if k.startswith('Rating by')):.2f})")
save(fig, "05_ratings")

# ------------------------------------------------------------------ 06 trend over time
mo = pd.DataFrame(S["monthly"])
mo["date"] = pd.to_datetime(mo.Year_Month)
full = mo[mo.full == "Yes"].copy()
full["roll"] = full.revenue.rolling(3, center=True).mean()
fig = plt.figure(figsize=(12, 6.4))
gs = fig.add_gridspec(1, 2, width_ratios=[2.6, 1], left=0.06, right=0.97, top=0.8, bottom=0.1, wspace=0.18)
a1, a2 = fig.add_subplot(gs[0]), fig.add_subplot(gs[1])
a1.bar(full.date, full.revenue, width=20, color=LIGHTBLUE, label="Monthly revenue")
part = mo[mo.full != "Yes"]
a1.bar(part.date, part.revenue, width=20, color="none", edgecolor=GRAY, hatch="////", linewidth=1, label="Partial month (excluded)")
a1.plot(full.date, full.roll, color=BLUE, lw=2, label="3-month average")
a1.axhline(K["revenue_per_full_month"], color=INK, lw=1)
a1.annotate(f"average ${K['revenue_per_full_month'] / 1000:.1f}K / month", (full.date.iloc[0], K["revenue_per_full_month"]),
            xytext=(0, 5), textcoords="offset points", fontsize=9, color=INK,
            bbox=dict(boxstyle="square,pad=0.15", fc=SURF, ec="none", alpha=0.85))
a1.xaxis.set_major_locator(mdates.MonthLocator(bymonth=[1, 7]))
a1.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
a1.yaxis.set_major_formatter(money)
a1.set_title(f"Recorded revenue per month ({K['full_months']} full months, Nov 2022 - Jun 2025)")
a1.legend(loc="upper right", ncol=3, fontsize=9, bbox_to_anchor=(1, 1.0))
a1.set_ylim(0, 48000)
ygrid(a1)
h1 = S["h1"]
bars = a2.bar([str(h["Year"]) for h in h1], [h["revenue"] for h in h1], color=[LIGHTBLUE, LIGHTBLUE, BLUE], width=0.55)
chg = [""] + [f"{h1[i]['revenue'] / h1[i - 1]['revenue'] - 1:+.1%}" for i in (1, 2)]
bar_labels(a2, bars, [f"${h['revenue'] / 1000:.1f}K\n{c}".strip() for h, c in zip(h1, chg)], size=9.5)
a2.yaxis.set_major_formatter(money)
a2.set_title("January-June revenue, year on year")
ygrid(a2)
a2.set_ylim(0, 215000)
headline(fig, f"Sales are flat: about {K['purchases_per_full_month']:.0f} purchases and ${K['revenue_per_full_month'] / 1000:.0f}K a month, with no trend",
         f"Trend slope +{S['corr']['purchases_slope_per_month']:.2f} purchases per month (p = {S['tests']['Monthly purchases trend (linear regression, full months)']:.2f}); "
         f"the same half-year moved {chg[1]} then {chg[2]}. The Oct 2022 and Jul 2025 bars are partial months")
save(fig, "06_trend")

# ------------------------------------------------------------------ 07 seasonality (calendar-coverage trap)
moy = pd.DataFrame(S["month_of_year"])
others = moy[~moy.Month.isin(["Aug", "Sep"])].purchases.mean()
dip = 1 - moy[moy.Month.isin(["Aug", "Sep"])].purchases.mean() / others
fig, (a1, a2, a3) = plt.subplots(1, 3, figsize=(12.5, 5), gridspec_kw={"width_ratios": [1.25, 1.25, 0.75]})
fig.subplots_adjust(left=0.04, right=0.99, top=0.74, bottom=0.12, wspace=0.18)
for ax, col, light, title, fmt_ in [
        (a1, "purchases", True, f"1. Raw purchases by month:\nAug-Sep look {dip:.0%} lower", lambda v: f"{v:.0f}"),
        (a2, "purchases_per_30d", False, "2. Purchases per 30 days of data:\nthe dip disappears", lambda v: f"{v:.0f}")]:
    colors = [ORANGE if m in ("Aug", "Sep") else (LIGHTBLUE if light else BLUE) for m in moy.Month]
    bars = ax.bar(moy.Month, moy[col], color=colors, width=0.66)
    bar_labels(ax, bars, [fmt_(v) for v in moy[col]], size=8.5)
    ax.set_title(title, fontsize=11)
    ax.tick_params(axis="x", labelsize=8.5)
    ygrid(ax)
    ax.margins(y=0.14)
wd = {r["Weekday"]: r for r in S["by_weekday"]}
days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
bars = a3.bar(days, [wd[d]["customers"] for d in days], color=BLUE, width=0.62)
bar_labels(a3, bars, [str(wd[d]["customers"]) for d in days], size=8.5)
a3.set_title("3. Purchases by weekday:\nflat", fontsize=11)
a3.tick_params(axis="x", labelsize=8.5)
ygrid(a3)
a3.margins(y=0.14)
headline(fig, "No seasonal or weekly pattern once calendar coverage is accounted for",
         f"The data runs {K['first_date']} to {K['last_date']}: Aug and Sep occur in 2 of the years covered, Jan-Jun in 3. "
         f"Adjusted, months differ only by chance (p = {S['tests']['Month-of-year purchases vs calendar coverage (chi-square)']:.2f}); "
         f"so do weekdays (p = {S['tests']['Weekday purchases vs calendar coverage (chi-square)']:.2f})")
save(fig, "07_seasonality")

# ------------------------------------------------------------------ 08 segment comparison (forest plot)
fig, (a1, a2) = plt.subplots(1, 2, figsize=(12, 6.6), sharey=False)
fig.subplots_adjust(left=0.11, right=0.97, top=0.8, bottom=0.08, wspace=0.3)


def forest(ax, rows, val, ref, fmtv, title, xlim, ref_label):
    ylabels, y, pos, last = [], [], 0, None
    for r in rows:
        if last is not None and r["dimension"] != last:
            pos += 0.6
        ylabels.append(f"{r['segment']}" if r["dimension"] != "Age group" else f"Age {r['segment']}")
        y.append(-pos)
        last = r["dimension"]
        pos += 1
    for r, yy in zip(rows, y):
        ax.plot([r["lo"], r["hi"]], [yy, yy], color=LIGHTBLUE, lw=5, solid_capstyle="round")
        ax.plot(r[val], yy, "o", color=BLUE, ms=7, mec=SURF, mew=1.5)
    ax.axvline(ref, color=INK, lw=1.1)
    ax.set_yticks(y, ylabels, fontsize=9)
    ax.set_xlim(*xlim)
    ax.xaxis.set_major_formatter(FuncFormatter(fmtv))
    ax.set_title(title)
    xgrid(ax)
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)
    ax.annotate(f"overall {ref_label}", (ref, y[0] + 0.8), xytext=(4, 0), textcoords="offset points", fontsize=9, color=INK)
    ax.set_ylim(y[-1] - 0.8, y[0] + 1.3)


forest(a1, S["aov_ci"], "aov", K["aov"], lambda v, _: f"${v:,.0f}", "Average order value (95% CI)", (420, 640), f"${K['aov']:.0f}")
forest(a2, S["rating_ci"], "avg", K["avg_rating"], lambda v, _: f"{v:.1f}", "Average rating out of 5 (95% CI)", (2.5, 3.6), f"{K['avg_rating']:.2f}")
seg_p = [v for k, v in S["tests"].items() if "trend" not in k and "H1" not in k and "calendar" not in k]
miss = ([r for r in S["aov_ci"] if not r["lo"] <= K["aov"] <= r["hi"]] +
        [r for r in S["rating_ci"] if not r["lo"] <= K["avg_rating"] <= r["hi"]])
n_ci = len(S["aov_ci"]) + len(S["rating_ci"])
headline(fig, "No customer segment spends or rates differently from the rest",
         f"None of the {len(seg_p)} segment tests is significant (smallest p = {min(seg_p):.2f}). {len(miss)} of {n_ci} intervals "
         f"miss the overall line ({', '.join(r['segment'] for r in miss)}): chance alone predicts about {0.05 * n_ci:.1f}")
save(fig, "08_segment_comparison")
