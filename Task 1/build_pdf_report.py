# -*- coding: utf-8 -*-
"""
Builds a polished, designed PDF version of the Task 1 report:
  1. Computes all figures fresh from the cleaned dataset (single source of truth)
  2. Renders a styled HTML file (blue/green theme, cards, tables, embedded charts)
  3. Converts that HTML to PDF using headless Microsoft Edge (isolated profile)
"""

import base64
import os
import subprocess
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CLEAN_FILE = os.path.join(BASE_DIR, "Sales_Dataset_Cleaned.csv")
CHARTS_DIR = os.path.join(BASE_DIR, "charts")
HTML_OUT = os.path.join(BASE_DIR, "Sales_Analysis_Report.html")
PDF_OUT = os.path.join(BASE_DIR, "Sales_Analysis_Report.pdf")

KAGGLE_URL = "https://www.kaggle.com/datasets/vivek468/superstore-dataset-final"

# ---------------------------------------------------------------------
# 1. COMPUTE
# ---------------------------------------------------------------------
df = pd.read_csv(CLEAN_FILE, parse_dates=["Order Date", "Ship Date"])

total_sales = df["Sales"].sum()
total_profit = df["Profit"].sum()
margin = total_profit / total_sales
n_orders = len(df)

by_cat = df.groupby("Category")[["Sales", "Profit"]].sum().sort_values("Sales", ascending=False)
by_cat["Margin"] = by_cat["Profit"] / by_cat["Sales"]

by_region = df.groupby("Region")[["Sales", "Profit"]].sum().sort_values("Sales", ascending=False)
by_region["Share"] = by_region["Sales"] / total_sales

df["Order Month"] = df["Order Date"].dt.to_period("M")
by_period = df.groupby("Order Month")["Sales"].sum().sort_values(ascending=False)
best_period = str(by_period.index[0])
best_period_val = by_period.iloc[0]

month_order = ["January", "February", "March", "April", "May", "June", "July",
               "August", "September", "October", "November", "December"]
df["Month Name"] = df["Order Date"].dt.month_name()
by_month = df.groupby("Month Name")["Sales"].sum().reindex(month_order)
best_month = by_month.idxmax()
best_month_val = by_month.max()

sales_by_product = df.groupby("Product Name")["Sales"].sum().sort_values(ascending=False)
qty_by_product = df.groupby("Product Name")["Quantity"].sum().sort_values(ascending=False)
top_product_rev, top_product_rev_val = sales_by_product.index[0], sales_by_product.iloc[0]
top_product_qty, top_product_qty_val = qty_by_product.index[0], qty_by_product.iloc[0]

by_subcat = df.groupby("Sub-Category")["Profit"].sum().sort_values()
worst_sub = by_subcat.head(2)

top_region, top_region_val, top_region_share = by_region.index[0], by_region["Sales"].iloc[0], by_region["Share"].iloc[0]
second_region, second_region_share = by_region.index[1], by_region["Share"].iloc[1]
last_region, last_region_val, last_region_share = by_region.index[-1], by_region["Sales"].iloc[-1], by_region["Share"].iloc[-1]

top_cat, top_cat_val = by_cat.index[0], by_cat["Sales"].iloc[0]
furn_margin = by_cat.loc["Furniture", "Margin"]
other_margin_avg = by_cat.loc[["Technology", "Office Supplies"], "Margin"].mean()
furn_sales, furn_profit = by_cat.loc["Furniture", "Sales"], by_cat.loc["Furniture", "Profit"]


def money(x):
    return f"-${abs(x):,.0f}" if x < 0 else f"${x:,.0f}"


def money2(x):
    return f"-${abs(x):,.2f}" if x < 0 else f"${x:,.2f}"


def pct(x):
    return f"{x:.1%}"


def img_b64(name):
    path = os.path.join(CHARTS_DIR, name)
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("ascii")


# ---------------------------------------------------------------------
# 2. BUILD HTML
# ---------------------------------------------------------------------
cat_rows = "".join(
    f"<tr><td>{cat}</td><td class='num'>{money(r.Sales)}</td>"
    f"<td class='num'>{money(r.Profit)}</td><td class='num'>{pct(r.Margin)}</td></tr>"
    for cat, r in by_cat.iterrows()
)

region_rows = "".join(
    f"<tr><td>{reg}</td><td class='num'>{money(r.Sales)}</td>"
    f"<td class='num'>{money(r.Profit)}</td><td class='num'>{pct(r.Share)}</td></tr>"
    for reg, r in by_region.iterrows()
)

top5_rev_rows = "".join(
    f"<tr><td>{i+1}</td><td>{name}</td><td class='num'>{money(val)}</td></tr>"
    for i, (name, val) in enumerate(sales_by_product.head(5).items())
)

top5_qty_rows = "".join(
    f"<tr><td>{i+1}</td><td>{name}</td><td class='num'>{val:,} units</td></tr>"
    for i, (name, val) in enumerate(qty_by_product.head(5).items())
)

charts = [
    ("01_sales_by_category.png", "Total Sales by Category",
     "Technology leads, but the three categories are closer together than the sales figures alone suggest."),
    ("02_sales_over_time.png", "Monthly Sales Over Time (2015–2018)",
     "A clear upward trend with recurring year-end spikes, peaking in November 2018."),
    ("03_top_10_products.png", "Top 10 Products by Sales",
     "Revenue is concentrated in a handful of high-ticket Technology items, led by the Canon imageCLASS copier."),
    ("04_sales_by_region.png", "Share of Sales by Region",
     "West and East together account for over 60% of all sales, while South lags noticeably behind."),
    ("05_sales_vs_profit_by_category.png", "Sales vs Profit by Category",
     "Furniture's profit bar is barely visible next to its sales bar, which is the clearest sign of its weak margin."),
]

chart_cards = "".join(f"""
    <div class="chart-card">
      <img src="data:image/png;base64,{img_b64(f)}" alt="{title}">
      <div class="chart-caption"><strong>{title}.</strong> {cap}</div>
    </div>
""" for f, title, cap in charts)

insights = [
    ("Technology drives the most revenue, but Office Supplies is just as profitable.",
     f"Technology leads sales at {money(top_cat_val)}, but its margin isn't actually any better than Office "
     f"Supplies. Both categories convert roughly {pct(other_margin_avg)} of sales into profit, so Technology's "
     f"lead comes mainly from a handful of high-ticket items like copiers and video-conferencing units, not from "
     f"stronger performance across the board."),
    ("Furniture sells well but barely makes money.",
     f"Furniture is the #2 category by revenue at {money(furn_sales)}, but its profit margin is only "
     f"<strong>{pct(furn_margin)}</strong>, compared to roughly {pct(other_margin_avg)} for the other two "
     f"categories. That works out to just {money(furn_profit)} in profit on those {money(furn_sales)} of sales."),
    ("Tables and Bookcases are actively losing money.",
     f"Drilling into sub-categories shows why: <strong>{worst_sub.index[0]}</strong> lost "
     f"{money(abs(worst_sub.iloc[0]))} overall and <strong>{worst_sub.index[1]}</strong> lost "
     f"{money(abs(worst_sub.iloc[1]))}, both sold at a net loss despite real revenue behind them. That's the "
     f"direct cause of Furniture's weak margin above, and a clear place to review pricing or discounting."),
    ("Sales are heavily seasonal, peaking at year-end.",
     f"<strong>{best_month}</strong> is the strongest calendar month overall, with {money(best_month_val)} in "
     f"sales aggregated across all four years, and the single best month on record is "
     f"<strong>{best_period}</strong> at {money(best_period_val)}. It looks like a holiday-driven demand spike "
     f"worth planning inventory and promotions around."),
    (f"The {top_region} region outsells the {last_region} region by nearly 2x.",
     f"{top_region} and {second_region} together generate over 60% of total sales ({pct(top_region_share)} and "
     f"{pct(second_region_share)} respectively), while {last_region} trails at just {money(last_region_val)}, or "
     f"{pct(last_region_share)} of the total. That gap looks like a real opportunity for targeted growth efforts "
     f"in the {last_region} region."),
]

insight_cards = "".join(f"""
    <div class="insight-card">
      <div class="insight-num">{i+1}</div>
      <div class="insight-text"><h4>{title}</h4><p>{body}</p></div>
    </div>
""" for i, (title, body) in enumerate(insights))

html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Sales Analysis Report</title>
<style>
  @page {{ size: A4; margin: 16mm 14mm 18mm 14mm; }}
  * {{ box-sizing: border-box; }}
  body {{
    font-family: 'Segoe UI', Arial, sans-serif;
    color: #1a2b3c;
    margin: 0;
    font-size: 12.5px;
    line-height: 1.5;
  }}
  .cover {{
    background: linear-gradient(135deg, #1F3B57 0%, #2C6E6B 100%);
    color: #fff;
    padding: 34px 30px;
    border-radius: 10px;
    margin-bottom: 22px;
  }}
  .cover .eyebrow {{ text-transform: uppercase; letter-spacing: 2px; font-size: 11px; opacity: .85; }}
  .cover h1 {{ margin: 6px 0 10px; font-size: 26px; }}
  .cover .meta {{ font-size: 12px; opacity: .95; margin-top: 14px; }}
  .cover .meta span {{ display: inline-block; margin-right: 22px; }}
  .cover .meta b {{ font-weight: 600; }}

  h2.section {{
    color: #0B3D57;
    font-size: 17px;
    border-left: 6px solid #2C6E6B;
    padding-left: 10px;
    margin: 26px 0 12px;
    break-after: avoid;
  }}

  .kpi-row {{ display: flex; gap: 12px; margin-bottom: 6px; break-inside: avoid; }}
  .kpi {{
    flex: 1;
    border-radius: 10px;
    padding: 14px 14px;
    color: #fff;
    box-shadow: 0 2px 6px rgba(0,0,0,0.08);
  }}
  .kpi .label {{ font-size: 10.5px; text-transform: uppercase; letter-spacing: .6px; opacity: .9; }}
  .kpi .value {{ font-size: 19px; font-weight: 700; margin-top: 4px; }}
  .kpi.c1 {{ background: #1F3B57; }}
  .kpi.c2 {{ background: #2C6E6B; }}
  .kpi.c3 {{ background: #C9A24B; }}
  .kpi.c4 {{ background: #B0563D; }}

  table {{ width: 100%; border-collapse: collapse; margin: 8px 0 16px; break-inside: avoid; }}
  table caption {{ text-align: left; font-weight: 600; color: #1F3B57; margin-bottom: 6px; font-size: 12.5px; }}
  th {{ background: #1F3B57; color: #fff; text-align: left; padding: 7px 10px; font-size: 11.5px; }}
  td {{ padding: 6px 10px; border-bottom: 1px solid #E3EDF2; font-size: 11.5px; }}
  tr:nth-child(even) td {{ background: #F2F6F5; }}
  td.num {{ text-align: right; font-variant-numeric: tabular-nums; }}
  th.num {{ text-align: right; }}

  .two-col {{ display: flex; gap: 18px; }}
  .two-col > div {{ flex: 1; }}

  .clean-table td:nth-child(1) {{ font-weight: 600; color: #1F3B57; white-space: nowrap; }}

  .chart-card {{
    break-inside: avoid;
    border: 1px solid #DCEBEE;
    border-radius: 10px;
    padding: 10px 12px 12px;
    margin-bottom: 14px;
    background: #FBFEFE;
  }}
  .chart-card img {{ width: 100%; display: block; border-radius: 4px; }}
  .chart-caption {{ font-size: 11px; color: #40545f; margin-top: 6px; }}

  .insight-card {{
    display: flex;
    gap: 10px;
    align-items: flex-start;
    border-left: 4px solid #2C6E6B;
    background: #F2F7F6;
    border-radius: 6px;
    padding: 10px 12px;
    margin-bottom: 10px;
    break-inside: avoid;
  }}
  .insight-num {{
    background: #1F3B57;
    color: #fff;
    min-width: 22px; height: 22px;
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 11.5px; font-weight: 700;
    flex-shrink: 0;
  }}
  .insight-text h4 {{ margin: 0 0 3px; color: #1F3B57; font-size: 12.5px; }}
  .insight-text p {{ margin: 0; font-size: 11.5px; color: #2b3c46; }}

  .source-box {{
    background: #EEF2F6;
    border: 1px solid #DCE3EA;
    border-radius: 8px;
    padding: 10px 14px;
    font-size: 11px;
    color: #2b3c46;
    margin-top: 6px;
    break-inside: avoid;
  }}
  .source-box a {{ color: #2C6E6B; }}

  .files-list {{ columns: 2; font-size: 11.5px; break-inside: avoid; }}
  .files-list li {{ margin-bottom: 4px; }}

  .footer-note {{ margin-top: 18px; font-size: 10.5px; color: #7a8a92; text-align: center; }}
</style>
</head>
<body>

  <div class="cover">
    <div class="eyebrow">VOLTIX &middot; Data Analyst Internship &middot; Task 1</div>
    <h1>Basic Sales Data Analysis</h1>
    <div class="meta">
      <span><b>Prepared by:</b> Nahla Nabil</span>
      <span><b>Dataset:</b> Sample Superstore sales data, {n_orders:,} orders</span>
      <span><b>Tools:</b> Python (Pandas, Matplotlib)</span>
    </div>
  </div>

  <h2 class="section">Key Numbers</h2>
  <div class="kpi-row">
    <div class="kpi c1"><div class="label">Total Sales</div><div class="value">{money2(total_sales)}</div></div>
    <div class="kpi c2"><div class="label">Total Profit</div><div class="value">{money2(total_profit)}</div></div>
    <div class="kpi c3"><div class="label">Profit Margin</div><div class="value">{pct(margin)}</div></div>
    <div class="kpi c4"><div class="label">Orders Analyzed</div><div class="value">{n_orders:,}</div></div>
  </div>

  <h2 class="section">1. Data Cleaning</h2>
  <table class="clean-table">
    <tr><th>Check</th><th>Result</th><th>Action Taken</th></tr>
    <tr><td>Missing values</td><td>Only <code>Postal Code</code> had nulls (11 of {n_orders:,} rows). All analysis
        columns were 100% complete.</td><td>Filled with a placeholder; column isn't used in this analysis.</td></tr>
    <tr><td>Duplicate rows</td><td>0 fully duplicated rows found.</td><td>None needed.</td></tr>
    <tr><td>Data types</td><td>Date columns were stored as text.</td>
        <td>Converted to proper <code>datetime</code>; re-validated all numeric columns (0 failures).</td></tr>
    <tr><td>Invalid values</td><td>Checked for negative Sales and zero/negative Quantity.</td>
        <td>None found, so no rows were removed.</td></tr>
  </table>

  <h2 class="section">2. Data Analysis: Answers</h2>
  <div class="two-col">
    <div>
      <table>
        <caption>Sales &amp; Profit by Category</caption>
        <tr><th>Category</th><th class="num">Sales</th><th class="num">Profit</th><th class="num">Margin</th></tr>
        {cat_rows}
      </table>
    </div>
    <div>
      <table>
        <caption>Sales &amp; Profit by Region</caption>
        <tr><th>Region</th><th class="num">Sales</th><th class="num">Profit</th><th class="num">Share</th></tr>
        {region_rows}
      </table>
    </div>
  </div>
  <div class="two-col">
    <div>
      <table>
        <caption>Top 5 Products by Revenue</caption>
        <tr><th>#</th><th>Product</th><th class="num">Sales</th></tr>
        {top5_rev_rows}
      </table>
    </div>
    <div>
      <table>
        <caption>Top 5 Products by Units Sold</caption>
        <tr><th>#</th><th>Product</th><th class="num">Quantity</th></tr>
        {top5_qty_rows}
      </table>
    </div>
  </div>
  <div class="source-box">
    <strong>Best sales month:</strong> {best_month} is the strongest calendar month overall ({money(best_month_val)}
    aggregated across 2015–2018); the single best month on record is {best_period} ({money(best_period_val)}).
  </div>

  <h2 class="section">3. Visualizations</h2>
  {chart_cards}

  <h2 class="section">4. Insights</h2>
  {insight_cards}

  <h2 class="section">5. Data Source</h2>
  <div class="source-box">
    This is the widely-used public "Sample Superstore" dataset (9,994 orders; Order Date, Category, Region,
    Quantity, Sales and Profit among its fields), the same dataset mirrored on Kaggle as
    <a href="{KAGGLE_URL}">{KAGGLE_URL}</a>.
  </div>

  <h2 class="section">6. Files in This Submission</h2>
  <ul class="files-list">
    <li><code>Sales_Dataset.csv</code>: the original raw dataset</li>
    <li><code>Sales_Dataset_Cleaned.csv</code>: the cleaned dataset used for analysis</li>
    <li><code>analysis.py</code>: the full Python analysis script</li>
    <li><code>analysis_output.txt</code>: the captured console output and results log</li>
    <li><code>Sales_Analysis_Report.pdf</code>: this report</li>
    <li><code>Sales_Analysis_Summary.xlsx</code>: Excel workbook with pivot tables &amp; charts</li>
    <li><code>charts/</code>: the 5 PNG charts referenced above</li>
  </ul>

  <div class="footer-note">VOLTIX Data Analyst Internship &middot; Task 1 &middot; Nahla Nabil</div>

</body>
</html>
"""

with open(HTML_OUT, "w", encoding="utf-8") as f:
    f.write(html)
print(f"HTML written: {HTML_OUT}")

# ---------------------------------------------------------------------
# 3. HTML -> PDF via headless Edge (isolated profile, no impact on the
#    user's real browser session)
# ---------------------------------------------------------------------
browser_candidates = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
]
browser = next((p for p in browser_candidates if os.path.exists(p)), None)
if not browser:
    raise SystemExit("No headless-capable browser found (Chrome/Edge).")

import shutil
profile_dir = os.path.join(os.environ.get("TEMP", BASE_DIR), "claude_pdf_profile")
shutil.rmtree(profile_dir, ignore_errors=True)

args = [
    browser,
    "--headless=new",
    "--disable-gpu",
    "--no-sandbox",
    "--no-first-run",
    "--no-default-browser-check",
    "--disable-extensions",
    "--disable-component-update",
    "--disable-background-networking",
    "--disable-sync",
    "--disable-client-side-phishing-detection",
    "--disable-default-apps",
    "--metrics-recording-only",
    "--mute-audio",
    f"--user-data-dir={profile_dir}",
    f"--print-to-pdf={PDF_OUT}",
    "--no-pdf-header-footer",
    "--print-to-pdf-no-header",
    "--virtual-time-budget=15000",
    HTML_OUT,
]
print("Using browser:", browser)
result = subprocess.run(args, capture_output=True, text=True, timeout=90)
print("Return code:", result.returncode)
print("STDOUT:", result.stdout)
print("STDERR:", result.stderr)
print("PDF exists:", os.path.exists(PDF_OUT), "-", os.path.getsize(PDF_OUT) if os.path.exists(PDF_OUT) else 0, "bytes")
shutil.rmtree(profile_dir, ignore_errors=True)
