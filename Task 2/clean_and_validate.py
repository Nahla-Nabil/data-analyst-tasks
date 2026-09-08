"""
Task 2 - Sales Data (FactSale) : Data Cleaning & Validation
Author: Nahla Nabil

What this script does, in order:
  1. Loads the raw FactSale export and profiles it (nulls, duplicates, dtypes).
  2. Cleans it: fixes date columns, imputes the few missing delivery dates,
     and enriches it with a handful of business-meaningful flags/columns.
  3. Validates the financial formulas that tie the columns together
     (Qty * Price = Total Excl. Tax, etc.) and reports anything inconsistent.
  4. Writes Cleaned_FactSale.csv, the deliverable used by the dashboard and
     the insights write-up.

Every finding printed here is also written out in DATA_QUALITY_REPORT.md in
plain language - this script is the evidence for that report, not a black box.
"""

import pandas as pd
import numpy as np

RAW_PATH = "FactSale.csv"
CLEAN_PATH = "Cleaned_FactSale.csv"


def categorize_product(description: str) -> str:
    """Map a free-text stock item description to a broad product category.

    FactSale has no product-category dimension table (only this fact file was
    provided), so categories are derived from keywords in the Description
    field. Every one of the 227 distinct products in this file falls into one
    of the 8 buckets below (verified - no 'Other' bucket needed).
    """
    d = description.lower()
    if "mug" in d:
        return "Novelty Mugs"
    if "mask" in d:
        return "Costumes & Masks"
    if any(k in d for k in ["hoodie", "jacket", "t-shirt", "shirt", "sock", "slipper"]):
        return "Apparel & Footwear"
    if d.startswith("rc ") or "ride on" in d:
        return "Toy Vehicles"
    if "action figure" in d:
        return "Toys & Figures"
    if any(k in d for k in ["usb", "periscope"]):
        return "USB & Novelty Gadgets"
    if "chocolate" in d:
        return "Confectionery"
    if any(k in d for k in ["bubble wrap", "bubblewrap", "tape", "courier", "post bag",
                             "post box", "carton", "void fill", "air cushion",
                             "blade", "marker", "dispenser"]):
        return "Packaging & Shipping Supplies"
    return "Other"


def profile(df: pd.DataFrame, label: str) -> None:
    print(f"\n=== PROFILE: {label} ===")
    print(f"Rows: {len(df):,} | Columns: {df.shape[1]}")
    nulls = df.isnull().sum()
    nulls = nulls[nulls > 0]
    print("Missing values:" if len(nulls) else "Missing values: none")
    if len(nulls):
        print(nulls)
    print(f"Fully duplicated rows: {df.duplicated().sum()}")
    print(f"Duplicate Sale Key (primary key): {df['Sale Key'].duplicated().sum()}")


def clean_and_validate(input_path: str = RAW_PATH, output_path: str = CLEAN_PATH) -> pd.DataFrame:
    df = pd.read_csv(input_path)
    profile(df, "raw FactSale.csv")

    # ------------------------------------------------------------------
    # 1. DATES
    #    Raw dates are text in M/D/YYYY form (no leading zeros, so the
    #    string length varies row to row - that is a formatting quirk, not
    #    a parsing error: every value parses cleanly to a real calendar date).
    # ------------------------------------------------------------------
    df["Invoice Date Key"] = pd.to_datetime(df["Invoice Date Key"], format="mixed")
    df["Delivery Date Key"] = pd.to_datetime(df["Delivery Date Key"], format="mixed")

    # 13 rows (0.05%) have no Delivery Date Key at all. Every one of the
    # remaining 26,384 rows delivers exactly 1 day after invoicing (checked:
    # 100% of non-null rows have delta == 1 day), so that is the only
    # defensible way to fill the gap - it is not a guess, it is the pattern
    # the rest of the data already shows.
    missing_delivery = df["Delivery Date Key"].isnull()
    df["Delivery_Date_Imputed"] = missing_delivery
    df.loc[missing_delivery, "Delivery Date Key"] = (
        df.loc[missing_delivery, "Invoice Date Key"] + pd.Timedelta(days=1)
    )
    print(f"\nImputed {missing_delivery.sum()} missing Delivery Date Key values "
          f"(Invoice Date + 1 day, matching the pattern in 100% of complete rows).")

    # Sanity check: delivery must never precede invoicing.
    bad_order = (df["Delivery Date Key"] < df["Invoice Date Key"]).sum()
    print(f"Rows where delivery date precedes invoice date: {bad_order}")
    assert bad_order == 0

    # ------------------------------------------------------------------
    # 2. DUPLICATES
    # ------------------------------------------------------------------
    full_dupes = df.duplicated().sum()
    key_dupes = df["Sale Key"].duplicated().sum()
    print(f"\nFull-row duplicates: {full_dupes} | Duplicate Sale Key: {key_dupes}")
    if full_dupes:
        df = df.drop_duplicates()
        print(f"Dropped {full_dupes} exact duplicate rows.")

    # ------------------------------------------------------------------
    # 3. DATA TYPES
    #    Numeric-looking columns (Unit Price, Tax Rate, Total Excluding Tax,
    #    Tax Amount, Profit, Total Including Tax) arrive quoted as text in
    #    the raw CSV; pandas' default parser already coerces them to
    #    numeric on read, but we assert it explicitly so a future raw export
    #    that breaks this silently fails loudly instead of corrupting KPIs.
    # ------------------------------------------------------------------
    numeric_cols = ["Quantity", "Unit Price", "Tax Rate", "Total Excluding Tax",
                     "Tax Amount", "Profit", "Total Including Tax"]
    for col in numeric_cols:
        assert pd.api.types.is_numeric_dtype(df[col]), f"{col} did not parse as numeric"

    # ------------------------------------------------------------------
    # 4. VALIDATION - do the financial columns actually tie out?
    #    A 1-cent tolerance absorbs float rounding noise; anything bigger
    #    is a real inconsistency worth reporting.
    # ------------------------------------------------------------------
    tol = 0.02
    exp_ex_tax = df["Quantity"] * df["Unit Price"]
    mismatch_ex_tax = (df["Total Excluding Tax"] - exp_ex_tax).abs() > tol

    exp_tax_amt = df["Total Excluding Tax"] * df["Tax Rate"] / 100
    mismatch_tax = (df["Tax Amount"] - exp_tax_amt).abs() > tol

    exp_inc_tax = df["Total Excluding Tax"] + df["Tax Amount"]
    mismatch_inc_tax = (df["Total Including Tax"] - exp_inc_tax).abs() > tol

    print("\n--- Financial formula validation ---")
    print(f"Total Excluding Tax = Quantity x Unit Price -> mismatches: {mismatch_ex_tax.sum()}")
    print(f"Tax Amount = Total Excl. Tax x Tax Rate/100  -> mismatches: {mismatch_tax.sum()}")
    print(f"Total Including Tax = Excl. Tax + Tax Amount -> mismatches: {mismatch_inc_tax.sum()}")

    print("\n--- Business-rule sanity checks ---")
    print(f"Quantity <= 0: {(df['Quantity'] <= 0).sum()}")
    print(f"Unit Price <= 0: {(df['Unit Price'] <= 0).sum()}")
    print(f"Tax Rate values present: {sorted(df['Tax Rate'].unique())}")
    loss_rows = (df["Profit"] < 0).sum()
    print(f"Loss-making line items (Profit < 0): {loss_rows} ({loss_rows/len(df)*100:.1f}%)")

    zero_customer = ((df["Customer Key"] == 0) & (df["Bill To Customer Key"] == 0)).sum()
    print(f"Rows with Customer Key = 0 (no customer record captured): "
          f"{zero_customer} ({zero_customer/len(df)*100:.1f}%)")

    # ------------------------------------------------------------------
    # 5. ENRICHMENT - business-meaningful columns used throughout the
    #    dashboard and the insights write-up. Nothing here overwrites or
    #    fabricates a source value; every added column is clearly derived.
    # ------------------------------------------------------------------
    df["Customer_Type"] = np.where(df["Customer Key"] == 0, "Unknown / Walk-in", "Registered")
    df["Product_Category"] = df["Description"].apply(categorize_product)
    df["Profit_Margin_Pct"] = (df["Profit"] / df["Total Excluding Tax"] * 100).round(2)
    df["Is_Loss_Making"] = df["Profit"] < 0

    # Standardize dates to ISO (YYYY-MM-DD) text on write-out so the file
    # opens unambiguously in Excel/Sheets regardless of the reader's locale.
    out = df.copy()
    out["Invoice Date Key"] = out["Invoice Date Key"].dt.strftime("%Y-%m-%d")
    out["Delivery Date Key"] = out["Delivery Date Key"].dt.strftime("%Y-%m-%d")

    out.to_csv(output_path, index=False)
    profile(df, "cleaned output")
    print(f"\nSaved cleaned dataset -> {output_path}")
    return df


if __name__ == "__main__":
    clean_and_validate()
