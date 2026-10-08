"""EDA charts for Task 12 -> Task 12/charts/*.png (matplotlib only).

Run from the repo root:  python "Task 12/make_charts.py"
"""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

TASK = Path(__file__).resolve().parent
CLEAN = TASK / "Cleaned_AB_NYC_2019.csv"
FIG = TASK / "charts"
FIG.mkdir(exist_ok=True)

BOROUGH = {"Manhattan": "#1F3B57", "Brooklyn": "#1B998B", "Queens": "#E0A030",
           "Bronx": "#E4572E", "Staten Island": "#8E5572"}
ROOM = {"Entire home/apt": "#1F3B57", "Private room": "#1B998B", "Shared room": "#E0A030"}

plt.rcParams.update({"figure.dpi": 130, "axes.spines.top": False, "axes.spines.right": False,
                     "font.size": 9, "axes.titlesize": 11, "axes.titleweight": "bold"})

df = pd.read_csv(CLEAN)
val = df[df["price"] <= 1000].copy()
order_b = ["Manhattan", "Brooklyn", "Queens", "Bronx", "Staten Island"]


def save(fig, name):
    fig.tight_layout()
    fig.savefig(FIG / name, bbox_inches="tight")
    plt.close(fig)
    print("wrote", name)


# 1. Listings by borough -------------------------------------------------------
c = df["neighbourhood_group"].value_counts().reindex(order_b)
fig, ax = plt.subplots(figsize=(7, 4))
ax.bar(c.index, c.values, color=[BOROUGH[b] for b in c.index])
ax.set_title("Listings by borough (n = 48,884)")
ax.set_ylabel("Listings")
for x, v in zip(c.index, c.values):
    ax.text(x, v + 250, f"{v:,}", ha="center", fontsize=8)
save(fig, "01_listings_by_borough.png")

# 2. Room-type mix ---------------------------------------------------------------
c = df["room_type"].value_counts()
fig, ax = plt.subplots(figsize=(6, 4))
ax.bar(c.index, c.values, color=[ROOM[r] for r in c.index])
ax.set_title("Listing types: entire homes just over half")
ax.set_ylabel("Listings")
for x, v in zip(c.index, c.values):
    ax.text(x, v + 300, f"{v:,}\n({v/len(df):.1%})", ha="center", fontsize=8)
plt.setp(ax.get_xticklabels(), rotation=8, ha="right")
save(fig, "02_room_type_mix.png")

# 3. Median price by borough --------------------------------------------------------
m = val.groupby("neighbourhood_group")["price"].median().reindex(order_b)
fig, ax = plt.subplots(figsize=(7, 4))
ax.bar(m.index, m.values, color=[BOROUGH[b] for b in m.index])
ax.set_title("Median nightly price by borough (outliers > $1,000 excluded)")
ax.set_ylabel("Median price ($)")
for x, v in zip(m.index, m.values):
    ax.text(x, v + 2, f"${v:.0f}", ha="center", fontsize=9, fontweight="bold")
save(fig, "03_median_price_by_borough.png")

# 4. Price distribution -----------------------------------------------------------------
fig, ax = plt.subplots(figsize=(7, 4))
ax.hist(val["price"], bins=100, color="#1F3B57", edgecolor="white", linewidth=0.3)
ax.axvline(val["price"].median(), color="#E4572E", linestyle="--", label=f"Median ${val['price'].median():.0f}")
ax.axvline(val["price"].mean(), color="#E0A030", linestyle=":", label=f"Mean ${val['price'].mean():.0f}")
ax.set_title("Nightly prices cluster at $50-200 (right-skewed)")
ax.set_xlabel("Nightly price ($)")
ax.set_ylabel("Listings")
ax.set_xlim(0, 600)
ax.legend()
save(fig, "04_price_distribution.png")

# 5. Price by room type (boxplot) ------------------------------------------------------------
data = [val[val["room_type"] == r]["price"].clip(upper=500) for r in ROOM]
fig, ax = plt.subplots(figsize=(7, 4))
bp = ax.boxplot(data, tick_labels=list(ROOM), patch_artist=True, showfliers=False)
for p, r in zip(bp["boxes"], ROOM):
    p.set_facecolor(ROOM[r])
    p.set_alpha(0.75)
ax.set_title("Entire homes cost ~2.3x a private room (medians $160 vs $70)")
ax.set_ylabel("Nightly price, capped at $500 ($)")
save(fig, "05_price_by_room_type_box.png")

# 6. Top 15 neighbourhoods by volume ----------------------------------------------------------------
c = df["neighbourhood"].value_counts().head(15).sort_values()
fig, ax = plt.subplots(figsize=(7, 5))
ax.barh(c.index, c.values, color="#1B998B")
ax.set_title("Top 15 neighbourhoods by listing count")
ax.set_xlabel("Listings")
for v, lab in zip(c.values, c.index):
    ax.text(v + 40, lab, f"{v:,}", va="center", fontsize=8)
save(fig, "06_top_neighbourhoods_volume.png")

# 7. Priciest neighbourhoods (n >= 30) ---------------------------------------------------------------------
g = df.groupby("neighbourhood").agg(n=("id", "count"),
                                    med=("price", lambda x: x[x <= 1000].median())).query("n >= 30")
top = g.sort_values("med", ascending=True).tail(12)
fig, ax = plt.subplots(figsize=(7, 5))
ax.barh(top.index, top["med"], color="#8E5572")
ax.set_title("Priciest neighbourhoods, min. 30 listings (median nightly price)")
ax.set_xlabel("Median price ($)")
save(fig, "07_priciest_neighbourhoods.png")

# 8. Price vs reviews scatter (sample) ----------------------------------------------------------------------------
smp = val.sample(4000, random_state=7)
fig, ax = plt.subplots(figsize=(7, 4.5))
ax.scatter(smp["number_of_reviews"], smp["price"].clip(upper=600), s=6, alpha=0.25, color="#1F3B57")
ax.set_title("No link between price and review volume (r = -0.06)")
ax.set_xlabel("Number of reviews")
ax.set_ylabel("Nightly price, capped at $600 ($)")
ax.set_xlim(-5, 400)
save(fig, "08_price_vs_reviews.png")

# 9. Availability segments --------------------------------------------------------------------------------
order_a = ["Inactive (0 days)", "Low (1-90)", "Medium (91-180)", "High (181-364)", "Fully open (365)"]
c = df["avail_segment"].value_counts().reindex(order_a)
fig, ax = plt.subplots(figsize=(7.5, 4))
ax.bar(c.index, c.values, color="#E0A030")
ax.set_title("Availability is barbelled: 36% blocked all year, 30% open > 6 months")
ax.set_ylabel("Listings")
plt.setp(ax.get_xticklabels(), rotation=10, ha="right")
for x, v in zip(c.index, c.values):
    ax.text(x, v + 200, f"{v/len(df):.0%}", ha="center", fontsize=8)
save(fig, "09_availability_segments.png")

# 10. Minimum-nights spikes -----------------------------------------------------------------------------------------
mnc = df[df["minimum_nights"] <= 30]["minimum_nights"].value_counts().sort_index()
fig, ax = plt.subplots(figsize=(7, 4))
ax.bar(mnc.index.astype(str), mnc.values, color="#1F3B57")
ax.set_title("Minimum stay: 1-3 nights dominate, then a spike at 30 (monthly rentals)")
ax.set_xlabel("Minimum nights")
ax.set_ylabel("Listings")
for x, v in zip(mnc.index.astype(str), mnc.values):
    if v > 3000:
        ax.text(x, v + 150, f"{v:,}", ha="center", fontsize=8)
save(fig, "10_minimum_nights.png")

# 11. Geo scatter (borough-coloured sample) -------------------------------------------------------------------------------
smp = df.sample(8000, random_state=11)
fig, ax = plt.subplots(figsize=(7, 6))
for b in order_b:
    d = smp[smp["neighbourhood_group"] == b]
    ax.scatter(d["longitude"], d["latitude"], s=4, alpha=0.3, color=BOROUGH[b], label=b)
ax.set_title("Where the listings are: Manhattan core + western Brooklyn")
ax.set_xlabel("Longitude")
ax.set_ylabel("Latitude")
ax.legend(markerscale=3, fontsize=8)
ax.set_aspect(1.3)
save(fig, "11_map_sample.png")

# 12. Borough x room-type mix (stacked share) --------------------------------------------------------------------------------
ct = pd.crosstab(df["neighbourhood_group"], df["room_type"], normalize="index").reindex(order_b)
fig, ax = plt.subplots(figsize=(7, 4))
ct.plot(kind="bar", stacked=True, ax=ax,
        color=[ROOM["Entire home/apt"], ROOM["Private room"], ROOM["Shared room"]],
        edgecolor="white")
ax.set_title("Manhattan sells whole homes (61%); Bronx/Queens sell private rooms")
ax.set_ylabel("Share of borough listings")
ax.set_xlabel("")
plt.setp(ax.get_xticklabels(), rotation=0)
ax.legend(title="", fontsize=8)
save(fig, "12_borough_roomtype_mix.png")

print("done:", len(list(FIG.glob('*.png'))), "charts")
