"""EDA for the cleaned NYC Airbnb file -> Task 12/analysis_summary.json.

Run from the repo root:  python "Task 12/analysis.py"
Money/relationship stats use the outlier-capped frame (price <= 1000);
counts and shares use all cleaned rows.
"""
import json
from pathlib import Path
import pandas as pd

TASK = Path(__file__).resolve().parent
CLEAN = TASK / "Cleaned_AB_NYC_2019.csv"
OUT = TASK / "analysis_summary.json"

df = pd.read_csv(CLEAN, parse_dates=["last_review"])
val = df[df["price"] <= 1000].copy()      # value stats, outliers excluded
N = len(df)
s = {}

# ---- KPIs ------------------------------------------------------------------
s["kpis"] = {
    "listings": N,
    "hosts": int(df["host_id"].nunique()),
    "neighbourhoods": int(df["neighbourhood"].nunique()),
    "median_price": float(val["price"].median()),
    "mean_price_capped": round(float(val["price"].mean()), 1),
    "median_price_entire": float(val[val["room_type"] == "Entire home/apt"]["price"].median()),
    "median_price_private": float(val[val["room_type"] == "Private room"]["price"].median()),
    "median_price_shared": float(val[val["room_type"] == "Shared room"]["price"].median()),
    "pct_entire": round(float((df["room_type"] == "Entire home/apt").mean() * 100), 1),
    "pct_private": round(float((df["room_type"] == "Private room").mean() * 100), 1),
    "pct_shared": round(float((df["room_type"] == "Shared room").mean() * 100), 1),
    "pct_manhattan": round(float((df["neighbourhood_group"] == "Manhattan").mean() * 100), 1),
    "pct_brooklyn": round(float((df["neighbourhood_group"] == "Brooklyn").mean() * 100), 1),
    "pct_never_reviewed": round(float(df["flag_never_reviewed"].mean() * 100), 1),
    "pct_avail_zero": round(float((df["availability_365"] == 0).mean() * 100), 1),
    "mean_availability": round(float(df["availability_365"].mean()), 1),
    "median_availability": float(df["availability_365"].median()),
    "total_reviews": int(df["number_of_reviews"].sum()),
    "mean_reviews": round(float(df["number_of_reviews"].mean()), 2),
}

# ---- Borough table ------------------------------------------------------------
b = df.groupby("neighbourhood_group").agg(
    n=("id", "count"),
    entire_share=("room_type", lambda x: round((x == "Entire home/apt").mean(), 3)),
    mean_reviews=("number_of_reviews", "mean"),
    mean_avail=("availability_365", "mean"))
bv = val.groupby("neighbourhood_group")["price"].agg(["median", "mean"]).round(1)
b = b.join(bv)
b["share"] = (b["n"] / N).round(4)
s["boroughs"] = b.reset_index().to_dict("records")

# ---- Room-type table -------------------------------------------------------------
r = df.groupby("room_type").agg(n=("id", "count"),
                                mean_reviews=("number_of_reviews", "mean"),
                                mean_avail=("availability_365", "mean"))
rv = val.groupby("room_type")["price"].agg(["median", "mean"]).round(1)
r = r.join(rv)
r["share"] = (r["n"] / N).round(4)
s["room_types"] = r.reset_index().to_dict("records")

# ---- Neighbourhoods ----------------------------------------------------------------
nb = df.groupby("neighbourhood").agg(n=("id", "count"),
                                     med_price_capped=("price", lambda x: float(x[x <= 1000].median())),
                                     mean_reviews=("number_of_reviews", "mean"))
nb_big = nb[nb["n"] >= 30].sort_values("med_price_capped", ascending=False)
s["top_neighbourhoods_by_count"] = nb.sort_values("n", ascending=False).head(15).reset_index().to_dict("records")
s["priciest_neighbourhoods_min30"] = nb_big.head(15).reset_index().to_dict("records")
s["cheapest_neighbourhoods_min30"] = nb_big.tail(10).reset_index().to_dict("records")

# ---- Relationships ----------------------------------------------------------------------
s["correlations_capped"] = {
    "price_vs_reviews": round(float(val["price"].corr(val["number_of_reviews"])), 3),
    "price_vs_reviews_per_month": round(float(val["price"].corr(val["reviews_per_month"])), 3),
    "price_vs_availability": round(float(val["price"].corr(val["availability_365"])), 3),
    "reviews_vs_rpm": round(float(df["number_of_reviews"].corr(df["reviews_per_month"])), 3),
}
s["median_price_by_reviews_bucket"] = (
    val.assign(rev_bucket=pd.cut(val["number_of_reviews"], [-1, 0, 10, 50, 200, 10**9],
                                 labels=["0", "1-10", "11-50", "51-200", "200+"]))
    .groupby("rev_bucket", observed=True)["price"].median().round(0).to_dict())

# ---- Supply structure ------------------------------------------------------------------------
s["avail_segments"] = df["avail_segment"].value_counts().to_dict()
s["price_bands"] = df["price_band"].value_counts().to_dict()
s["host_sizes_listings_share"] = (df["host_size"].value_counts(normalize=True).round(4).to_dict())
s["single_listing_hosts_share"] = round(float((df.groupby("host_id")["id"].count() == 1).mean()), 3)
s["top_hosts"] = (df.groupby(["host_id", "host_name"])["id"].count()
                  .sort_values(ascending=False).head(10).reset_index()
                  .rename(columns={"id": "listings"}).to_dict("records"))
s["min_nights_spikes"] = df["minimum_nights"].value_counts().head(8).to_dict()
s["last_review_range"] = [str(df["last_review"].min()), str(df["last_review"].max())]

# ---- Performance: demand proxies -------------------------------------------------------------
perf = df.groupby("neighbourhood_group").agg(
    mean_reviews=("number_of_reviews", "mean"),
    mean_rpm=("reviews_per_month", "mean"),
    mean_booked=("booked_proxy", "mean"),
    median_revenue_proxy=("revenue_proxy", "median")).round(1)
s["performance_by_borough"] = perf.reset_index().to_dict("records")
top_perf = (df.groupby("neighbourhood").agg(n=("id", "count"),
                                            mean_reviews=("number_of_reviews", "mean"),
                                            mean_rpm=("reviews_per_month", "mean"))
            .query("n >= 100").sort_values("mean_reviews", ascending=False).head(10))
s["top_neighbourhoods_by_reviews"] = top_perf.reset_index().to_dict("records")

OUT.write_text(json.dumps(s, indent=2, default=str))
print(f"wrote {OUT.name}: {len(json.dumps(s))} chars")
print(json.dumps(s["kpis"], indent=2))
print("correlations:", json.dumps(s["correlations_capped"]))
