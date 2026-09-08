# -*- coding: utf-8 -*-
"""
Task 1 - Basic Sales Data Analysis
VOLTIX Data Analyst Internship

Dataset: Sample Superstore sales data (Sales_Dataset.csv)
Author: Nahla Nabil

This script:
  1. Loads and cleans the raw sales data
  2. Answers the required business questions
  3. Builds 5 charts for the analysis
  4. Prints a clean summary of everything to the console (captured into
     analysis_output.txt) which feeds the written report.
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import os

pd.set_option("display.width", 120)
pd.set_option("display.max_columns", 20)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CHARTS_DIR = os.path.join(BASE_DIR, "charts")
os.makedirs(CHARTS_DIR, exist_ok=True)

RAW_FILE = os.path.join(BASE_DIR, "Sales_Dataset.csv")
CLEAN_FILE = os.path.join(BASE_DIR, "Sales_Dataset_Cleaned.csv")

def section(title):
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


# ---------------------------------------------------------------------
# 1. LOAD
# ---------------------------------------------------------------------
section("1. LOADING DATA")
df = pd.read_csv(RAW_FILE, encoding="utf-8-sig")
print(f"Rows loaded: {len(df):,}")
print(f"Columns: {list(df.columns)}")


# ---------------------------------------------------------------------
# 2. DATA CLEANING
# ---------------------------------------------------------------------
section("2. DATA CLEANING")

# --- 2.1 Missing values ---
print("\n-- Missing values per column --")
missing = df.isna().sum()
print(missing[missing > 0] if missing.sum() else "No missing values found in any column.")

# The only column with nulls is 'Postal Code' (not used in this analysis).
# We fill it with a placeholder instead of dropping rows, since every other
# field in those rows (Sales, Profit, Category, Region ...) is complete and
# useful for the analysis.
if "Postal Code" in df.columns and df["Postal Code"].isna().any():
    df["Postal Code"] = df["Postal Code"].fillna(0).astype(int)
    print("-> Filled missing 'Postal Code' values with 0 (placeholder); "
          "column is not used in the analysis below.")

# --- 2.2 Duplicates ---
print("\n-- Duplicate rows --")
dupe_count = df.duplicated().sum()
print(f"Fully duplicated rows: {dupe_count}")
if dupe_count:
    df = df.drop_duplicates()
    print(f"-> Dropped {dupe_count} duplicate rows.")
else:
    print("-> No duplicate rows found.")

# --- 2.3 Data types ---
print("\n-- Data types before cleaning --")
print(df.dtypes)

df["Order Date"] = pd.to_datetime(df["Order Date"], errors="coerce")
df["Ship Date"] = pd.to_datetime(df["Ship Date"], errors="coerce")
bad_dates = df["Order Date"].isna().sum()
print(f"\nRows with unparseable Order Date after conversion: {bad_dates}")

numeric_cols = ["Sales", "Quantity", "Discount", "Profit"]
for col in numeric_cols:
    df[col] = pd.to_numeric(df[col], errors="coerce")
bad_numeric = df[numeric_cols].isna().sum().sum()
print(f"Rows with unparseable numeric values after conversion: {bad_numeric}")

print("\n-- Data types after cleaning --")
print(df.dtypes[["Order Date", "Ship Date", "Sales", "Quantity", "Discount", "Profit"]])

# --- 2.4 Sanity checks on values ---
print("\n-- Sanity checks --")
neg_sales = (df["Sales"] < 0).sum()
neg_qty = (df["Quantity"] <= 0).sum()
print(f"Rows with negative Sales: {neg_sales}")
print(f"Rows with Quantity <= 0: {neg_qty}")
print("-> None found; no rows removed on this basis." if neg_sales == 0 and neg_qty == 0
      else "-> Review flagged rows before trusting totals.")

# Save the cleaned dataset
df.to_csv(CLEAN_FILE, index=False)
print(f"\nCleaned dataset saved to: {os.path.basename(CLEAN_FILE)}  ({len(df):,} rows)")


# ---------------------------------------------------------------------
# 3. DATA ANALYSIS
# ---------------------------------------------------------------------
section("3. DATA ANALYSIS")

total_sales = df["Sales"].sum()
total_profit = df["Profit"].sum()
print(f"\nQ1. Total Sales:  ${total_sales:,.2f}")
print(f"Q2. Total Profit: ${total_profit:,.2f}")
print(f"    Overall profit margin: {total_profit / total_sales:.1%}")

sales_by_category = df.groupby("Category")["Sales"].sum().sort_values(ascending=False)
print("\nQ3. Sales by Category:")
print(sales_by_category.to_string())
top_category = sales_by_category.index[0]
print(f"-> Top category by sales: {top_category} (${sales_by_category.iloc[0]:,.2f})")

sales_by_product = df.groupby("Product Name")["Sales"].sum().sort_values(ascending=False)
qty_by_product = df.groupby("Product Name")["Quantity"].sum().sort_values(ascending=False)
print("\nQ4. Top 5 products by Sales revenue:")
print(sales_by_product.head(5).to_string())
print("\nQ4b. Top 5 products by Quantity sold (units):")
print(qty_by_product.head(5).to_string())
top_product_revenue = sales_by_product.index[0]
top_product_qty = qty_by_product.index[0]
print(f"-> Best-selling product by revenue: {top_product_revenue}")
print(f"-> Best-selling product by units sold: {top_product_qty} ({qty_by_product.iloc[0]} units)")

sales_by_region = df.groupby("Region")["Sales"].sum().sort_values(ascending=False)
print("\nQ5. Sales by Region:")
print(sales_by_region.to_string())
top_region = sales_by_region.index[0]
print(f"-> Top region by sales: {top_region} (${sales_by_region.iloc[0]:,.2f})")

df["Order Month"] = df["Order Date"].dt.to_period("M")
sales_by_month_period = df.groupby("Order Month")["Sales"].sum().sort_values(ascending=False)
best_month_period = sales_by_month_period.index[0]
print("\nQ6. Top 5 single months (year-month) by Sales:")
print(sales_by_month_period.head(5).to_string())
print(f"-> Highest single sales month: {best_month_period} (${sales_by_month_period.iloc[0]:,.2f})")

df["Month Name"] = df["Order Date"].dt.month_name()
month_order = ["January", "February", "March", "April", "May", "June", "July",
               "August", "September", "October", "November", "December"]
sales_by_month_name = df.groupby("Month Name")["Sales"].sum().reindex(month_order)
best_calendar_month = sales_by_month_name.idxmax()
print("\nQ6b. Sales aggregated by calendar month (seasonality, all years combined):")
print(sales_by_month_name.to_string())
print(f"-> Best-performing calendar month overall: {best_calendar_month} "
      f"(${sales_by_month_name.max():,.2f})")


# ---------------------------------------------------------------------
# 4. VISUALIZATIONS
# ---------------------------------------------------------------------
section("4. BUILDING CHARTS")

import textwrap

# A refined, muted palette used consistently across every chart, so the same
# category/region always carries the same color from one chart to the next.
NAVY = "#1F3B57"
TEAL = "#2C6E6B"
GOLD = "#C9A24B"
TERRACOTTA = "#B0563D"
INK = "#1F2A36"
MUTED = "#8C99A6"

CAT_COLORS = {"Technology": NAVY, "Furniture": TEAL, "Office Supplies": GOLD}
REGION_COLORS = {"West": NAVY, "East": TEAL, "Central": GOLD, "South": TERRACOTTA}

plt.rcParams.update({
    "figure.dpi": 150,
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "axes.edgecolor": MUTED,
    "axes.labelcolor": INK,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "font.size": 10.5,
    "text.color": INK,
    "xtick.color": INK,
    "ytick.color": INK,
})


def fmt_k(x, _pos=None):
    """Abbreviate to the nearest thousand, e.g. $836,154 -> $836K."""
    if abs(x) >= 1000:
        return f"${x/1000:,.0f}K"
    return f"${x:,.0f}"


def style_value_axis(ax, axis="x", nbins=4):
    axis_obj = ax.xaxis if axis == "x" else ax.yaxis
    axis_obj.set_major_formatter(mticker.FuncFormatter(fmt_k))
    axis_obj.set_major_locator(mticker.MaxNLocator(nbins=nbins))


def title(ax, text):
    ax.set_title(text, loc="left", pad=14, fontsize=13, fontweight="bold", color=NAVY)


# ---- Chart 1: Sales by Category ----
# (fixed: fewer, rounder tick labels + a value label on every bar, so nothing
# has to rely on a crowded axis to be readable)
fig, ax = plt.subplots(figsize=(7.2, 4))
cat_sorted = sales_by_category.sort_values()
colors = [CAT_COLORS[c] for c in cat_sorted.index]
bars = ax.barh(cat_sorted.index, cat_sorted.values, color=colors, height=0.55, zorder=3)
title(ax, "Total Sales by Category")
ax.set_xlim(0, cat_sorted.max() * 1.24)
style_value_axis(ax, "x", nbins=4)
ax.grid(axis="x", color=MUTED, alpha=0.2, linewidth=0.7, zorder=0)
ax.grid(axis="y", visible=False)
ax.tick_params(axis="y", length=0, labelsize=11)
ax.tick_params(axis="x", labelsize=9.5, colors=MUTED)
for bar, val in zip(bars, cat_sorted.values):
    ax.text(bar.get_width() + cat_sorted.max() * 0.025, bar.get_y() + bar.get_height() / 2,
            fmt_k(val), va="center", ha="left", fontsize=11, color=INK, fontweight="bold")
fig.tight_layout()
fig.savefig(os.path.join(CHARTS_DIR, "01_sales_by_category.png"))
plt.close(fig)

# ---- Chart 2: Sales over time (monthly trend) ----
fig, ax = plt.subplots(figsize=(8.4, 4))
ts = sales_by_month_period.sort_index()
ts.index = ts.index.to_timestamp()
ax.plot(ts.index, ts.values, color=NAVY, linewidth=2, marker="o", markersize=3.5,
         markerfacecolor=NAVY, markeredgecolor="white", markeredgewidth=0.6, zorder=3)
ax.fill_between(ts.index, ts.values, color=NAVY, alpha=0.08, zorder=2)
peak_idx = ts.values.argmax()
ax.annotate(fmt_k(ts.values[peak_idx]), xy=(ts.index[peak_idx], ts.values[peak_idx]),
            xytext=(0, 10), textcoords="offset points", ha="center",
            fontsize=10, fontweight="bold", color=NAVY)
title(ax, "Monthly Sales Over Time (2015–2018)")
style_value_axis(ax, "y", nbins=5)
ax.grid(axis="y", color=MUTED, alpha=0.2, linewidth=0.7, zorder=0)
ax.tick_params(axis="x", colors=MUTED, labelsize=9.5)
ax.tick_params(axis="y", colors=MUTED, labelsize=9.5)
fig.autofmt_xdate()
fig.tight_layout()
fig.savefig(os.path.join(CHARTS_DIR, "02_sales_over_time.png"))
plt.close(fig)

# ---- Chart 3: Top 10 products by sales ----
# (wrapped labels instead of "..." truncation, plus a navy-to-teal gradient
# that reads as a ranking rather than unrelated categories)
fig, ax = plt.subplots(figsize=(7.6, 5.6))
top10 = sales_by_product.head(10).sort_values()
labels = ["\n".join(textwrap.wrap(p, 30)) for p in top10.index]


def blend(c1, c2, t):
    r1, g1, b1 = tuple(int(c1[i:i+2], 16) for i in (1, 3, 5))
    r2, g2, b2 = tuple(int(c2[i:i+2], 16) for i in (1, 3, 5))
    return f"#{round(r1+(r2-r1)*t):02x}{round(g1+(g2-g1)*t):02x}{round(b1+(b2-b1)*t):02x}"


shades = [blend(TEAL, NAVY, i / (len(top10) - 1)) for i in range(len(top10))]
bars = ax.barh(labels, top10.values, color=shades, height=0.62, zorder=3)
title(ax, "Top 10 Products by Sales")
ax.set_xlim(0, top10.max() * 1.28)
style_value_axis(ax, "x", nbins=4)
ax.grid(axis="x", color=MUTED, alpha=0.2, linewidth=0.7, zorder=0)
ax.grid(axis="y", visible=False)
ax.tick_params(axis="y", length=0, labelsize=9)
ax.tick_params(axis="x", labelsize=9.5, colors=MUTED)
for bar, val in zip(bars, top10.values):
    ax.text(bar.get_width() + top10.max() * 0.02, bar.get_y() + bar.get_height() / 2,
            fmt_k(val), va="center", ha="left", fontsize=9.5, color=INK, fontweight="bold")
fig.tight_layout()
fig.savefig(os.path.join(CHARTS_DIR, "03_top_10_products.png"))
plt.close(fig)

# ---- Chart 4: Sales by Region (donut) ----
fig, ax = plt.subplots(figsize=(6, 6))
colors = [REGION_COLORS[r] for r in sales_by_region.index]
wedges, _, autotexts = ax.pie(
    sales_by_region.values, autopct="%1.0f%%", pctdistance=0.8, startangle=90,
    colors=colors, wedgeprops=dict(width=0.42, edgecolor="white", linewidth=2),
    textprops=dict(color="white", fontsize=10.5, fontweight="bold"),
)
ax.text(0, 0.06, fmt_k(total_sales), ha="center", va="center", fontsize=15,
        fontweight="bold", color=NAVY)
ax.text(0, -0.12, "total sales", ha="center", va="center", fontsize=9, color=MUTED)
ax.legend(wedges, sales_by_region.index, loc="upper center", bbox_to_anchor=(0.5, 0.02),
          ncol=4, frameon=False, fontsize=10)
title(ax, "Share of Sales by Region")
fig.tight_layout()
fig.savefig(os.path.join(CHARTS_DIR, "04_sales_by_region.png"))
plt.close(fig)

# ---- Chart 5 (bonus): Sales vs Profit by Category ----
fig, ax = plt.subplots(figsize=(7, 4.2))
profit_by_category = df.groupby("Category")["Profit"].sum().reindex(sales_by_category.index)
x = list(range(len(sales_by_category)))
width = 0.34
bars_sales = ax.bar([i - width/2 for i in x], sales_by_category.values, width,
                     label="Sales", color=NAVY, zorder=3)
bars_profit = ax.bar([i + width/2 for i in x], profit_by_category.values, width,
                      label="Profit", color=GOLD, zorder=3)
ax.set_xticks(x)
ax.set_xticklabels(sales_by_category.index, fontsize=10.5)
title(ax, "Sales vs Profit by Category")
style_value_axis(ax, "y", nbins=5)
ax.grid(axis="y", color=MUTED, alpha=0.2, linewidth=0.7, zorder=0)
ax.tick_params(axis="x", length=0)
ax.tick_params(axis="y", labelsize=9.5, colors=MUTED)
for bars in (bars_sales, bars_profit):
    for bar in bars:
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + sales_by_category.max() * 0.015,
                fmt_k(bar.get_height()), ha="center", va="bottom", fontsize=8.8,
                color=INK, fontweight="bold")
ax.legend(frameon=False, loc="upper right", fontsize=10)
fig.tight_layout()
fig.savefig(os.path.join(CHARTS_DIR, "05_sales_vs_profit_by_category.png"))
plt.close(fig)

print(f"Saved 5 charts to: {os.path.relpath(CHARTS_DIR, BASE_DIR)}/")
print(" - 01_sales_by_category.png")
print(" - 02_sales_over_time.png")
print(" - 03_top_10_products.png")
print(" - 04_sales_by_region.png")
print(" - 05_sales_vs_profit_by_category.png (bonus)")

section("DONE")
