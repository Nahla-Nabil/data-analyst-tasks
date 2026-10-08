"""Clean the raw AB_NYC_2019 file into Cleaned_AB_NYC_2019.csv.

Run from the repo root:  python "Task 12/clean_data.py"
Inputs : Task 12/data_raw/AB_NYC_2019.csv  (never modified)
Outputs: Task 12/Cleaned_AB_NYC_2019.csv, Task 12/cleaning_log.json

Policy: flag, don't silently delete. Only price == 0 rows (impossible
nightly prices) are removed; everything else is kept with quality flags.
"""
import json
from pathlib import Path
import numpy as np
import pandas as pd

TASK = Path(__file__).resolve().parent
RAW = TASK / "data_raw" / "AB_NYC_2019.csv"
CLEAN = TASK / "Cleaned_AB_NYC_2019.csv"
LOG = TASK / "cleaning_log.json"

log = {"source": str(RAW.name), "steps": []}


def step(action, detail):
    log["steps"].append({"action": action, "detail": detail})


def main():
    df = pd.read_csv(RAW)
    log["rows_in"] = int(len(df))
    log["cols_in"] = list(df.columns)

    # 1. Duplicates ---------------------------------------------------------
    n_dup_rows = int(df.duplicated().sum())
    n_dup_ids = int(df["id"].duplicated().sum())
    step("duplicates", f"{n_dup_rows} fully-duplicate rows, {n_dup_ids} duplicate ids -> none found, nothing removed")

    # 2. Impossible prices ----------------------------------------------------
    n_zero = int((df["price"] == 0).sum())
    df = df[df["price"] > 0].copy()
    step("price_zero", f"removed {n_zero} rows with price == 0 (impossible nightly price, 0.02% of file)")

    # 3. Missing names ---------------------------------------------------------
    n_name = int(df["name"].isna().sum())
    df["flag_name_missing"] = df["name"].isna().astype(int)
    df["name"] = df["name"].fillna("Unnamed listing")
    n_host = int(df["host_name"].isna().sum())
    df["flag_host_name_missing"] = df["host_name"].isna().astype(int)
    df["host_name"] = df["host_name"].fillna("Unknown host")
    step("missing_names", f"name: {n_name} -> 'Unnamed listing'; host_name: {n_host} -> 'Unknown host' (both flagged)")

    # 4. Reviews: missing <=> zero reviews (verified 1:1 in EDA) ----------------
    assert ((df["reviews_per_month"].isna()) == (df["number_of_reviews"] == 0)).all(), \
        "reviews missingness does not match zero-review rows"
    df["flag_never_reviewed"] = (df["number_of_reviews"] == 0).astype(int)
    df["reviews_per_month"] = df["reviews_per_month"].fillna(0.0)
    df["last_review"] = pd.to_datetime(df["last_review"], errors="coerce")
    step("reviews", "10052 rows missing last_review/reviews_per_month are exactly the zero-review rows: "
                    "reviews_per_month filled with 0, flag_never_reviewed set, last_review left as NaT")

    # 5. Price outliers: keep, flag, exclude from means -------------------------
    df["flag_price_outlier"] = (df["price"] > 1000).astype(int)
    step("price_outliers", f"{int(df['flag_price_outlier'].sum())} rows priced above $1000 (max ${int(df['price'].max())}) "
                           "kept with flag_price_outlier; means/correlations use price <= 1000")

    # 6. Extreme minimum_nights --------------------------------------------------
    df["flag_min_nights_extreme"] = (df["minimum_nights"] >= 365).astype(int)
    step("minimum_nights", f"{int(df['flag_min_nights_extreme'].sum())} rows require >= 365 nights "
                           "(max 1250) kept with flag_min_nights_extreme; spikes at 1/2/3/30 nights are genuine monthly-rental behaviour")

    # 7. Coordinates sanity ---------------------------------------------------------
    outside = int(((df["latitude"] < 40.49) | (df["latitude"] > 40.92) |
                   (df["longitude"] < -74.26) | (df["longitude"] > -73.70)).sum())
    step("coordinates", f"{outside} rows outside the NYC bounding box -> none, no action")

    # 8. Engineered columns ------------------------------------------------------------
    df["price_band"] = pd.cut(df["price"], [-1, 75, 150, 300, 10**9],
                              labels=["Budget (<$75)", "Mid ($75-150)", "Premium ($150-300)", "Luxury ($300+)"])
    df["avail_segment"] = pd.cut(df["availability_365"], [-1, 0, 90, 180, 364, 365],
                                 labels=["Inactive (0 days)", "Low (1-90)", "Medium (91-180)",
                                         "High (181-364)", "Fully open (365)"])
    df["host_size"] = pd.cut(df["calculated_host_listings_count"], [0, 1, 5, 20, 10**9],
                             labels=["Single (1)", "Small (2-5)", "Mid (6-20)", "Large (21+)"])
    df["booked_proxy"] = 365 - df["availability_365"]          # nights plausibly booked/off-market
    df["revenue_proxy"] = df["price"] * df["booked_proxy"]     # rough annual revenue signal
    # 8b. Excel/Power-BI helpers (averages of 0/1 flags act as shares in pivots) ----------------
    df["price_capped"] = df["price"].clip(upper=1000)          # outlier-safe price for averages
    df["is_entire_home"] = (df["room_type"] == "Entire home/apt").astype(int)
    df["is_zero_avail"] = (df["availability_365"] == 0).astype(int)
    df["stay_bin"] = pd.cut(df["minimum_nights"], [0, 1, 2, 3, 7, 29, 30, 10**9], right=True,
                            labels=["1 night", "2 nights", "3 nights", "4-7 nights",
                                    "8-29 nights", "30 nights (monthly)", "31+ nights"])
    step("excel_helpers", "added price_capped (min(price,1000)), is_entire_home, is_zero_avail, stay_bin")
    step("features", "added price_band, avail_segment, host_size, booked_proxy (=365-availability_365), "
                      "revenue_proxy (=price*booked_proxy), price_capped, is_entire_home, is_zero_avail, stay_bin")

    log["rows_out"] = int(len(df))
    log["cols_out"] = list(df.columns)
    df.to_csv(CLEAN, index=False)
    LOG.write_text(json.dumps(log, indent=2, default=str))
    print(f"in={log['rows_in']} out={log['rows_out']} cols={len(df.columns)} -> {CLEAN.name}")


if __name__ == "__main__":
    main()
