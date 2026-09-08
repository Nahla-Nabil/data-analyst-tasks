"""
Renders DATA_QUALITY_ISSUES.pdf: a short, print-ready summary of the data
quality issues found in FactSale.csv and how each was handled. Same editorial
"analyst report" look as Sales_Dashboard.html (serif/sans masthead, hairline
rules, one ink palette, no gradients/boxed cards) so everything submitted for
this task reads as one consistent, hand-built piece of work.

Source of truth for the content is DATA_QUALITY_REPORT.md (the full write-up);
this is the "simple summary" version of the same findings, designed to print.
"""

from playwright.sync_api import sync_playwright
import pathlib

OUT_HTML = "DATA_QUALITY_ISSUES.html"
OUT_PDF = "DATA_QUALITY_ISSUES.pdf"

INK = "#1a1a18"
INK_SEC = "#5a584f"
MUTED = "#8c8a80"
RULE = "#ddd9cd"
PAPER = "#faf9f6"
GOOD = "#1e7a4a"
FLAG = "#a8631a"
KEPT = "#2a5f8f"
CRIT = "#b5322f"

SERIF = "'Newsreader', Georgia, serif"
SANS = "'IBM Plex Sans', system-ui, -apple-system, sans-serif"

rows = [
    ("Missing Delivery Date", "13 rows (0.05%)",
     "Filled in as Invoice Date + 1 day &mdash; the pattern in 100% of the complete rows.", "Fixed", GOOD),
    ("Inconsistent date text format", "All rows",
     "Parsed and standardized to ISO format (YYYY-MM-DD).", "Fixed", GOOD),
    ("Numeric columns stored as quoted text", "All rows",
     "Verified / converted to proper numeric types.", "Fixed", GOOD),
    ("Customer Key = 0 (no customer captured)", "9,077 rows (34.4%)",
     "Not an error &mdash; flagged with a new Customer_Type column instead of guessing an ID.", "Flagged", FLAG),
    ("Duplicate rows", "0 found",
     "Checked full-row and Sale Key (primary key) duplication &mdash; none present.", "Checked", KEPT),
    ("Negative Quantity / Unit Price", "0 found",
     "No invalid transaction volumes or prices.", "Checked", KEPT),
    ("Negative Profit (loss-making sales)", "566 rows (2.1%)",
     "Kept as-is &mdash; a real, concentrated business finding (see Key Insights), not a data error.", "Kept", CRIT),
    ("No product / customer / salesperson names", "All rows",
     "Only the fact table was provided (no dimension tables) &mdash; those fields are reported by ID.", "Noted", MUTED),
]

row_html = "\n".join(f"""
<tr>
  <td class="c-issue">{issue}</td>
  <td class="c-scope">{scope}</td>
  <td class="c-fix">{fix}</td>
  <td class="c-status"><span class="tag"><span class="dot" style="background:{color}"></span>{status}</span></td>
</tr>
""" for issue, scope, fix, status, color in rows)

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Data Quality Summary</title>
<link href="https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,500;0,6..72,600;1,6..72,500&family=IBM+Plex+Sans:wght@400;500;600&display=swap" rel="stylesheet">
<style>
  @page {{ size: A4; margin: 0; }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0; background: {PAPER}; color: {INK};
    font-family: {SANS}; font-size: 12.5px; line-height: 1.55;
  }}
  .page {{ width: 210mm; min-height: 297mm; margin: 0 auto; padding: 16mm 16mm 14mm 16mm; }}

  .masthead {{ border-top: 2px solid {INK}; padding-top: 10px; }}
  .eyebrow {{ font-size: 10px; letter-spacing: 0.13em; text-transform: uppercase; color: {INK_SEC}; font-weight: 600; }}
  h1 {{ font-family: {SERIF}; font-size: 27px; font-weight: 600; margin: 6px 0 6px 0; letter-spacing: -0.01em; }}
  .byline {{ font-size: 11px; color: {INK_SEC}; padding-bottom: 10mm; border-bottom: 1px solid {RULE}; margin-bottom: 8mm; }}
  .byline b {{ color: {INK}; font-weight: 600; }}

  .stat-strip {{ display: flex; margin-bottom: 8mm; }}
  .stat {{ flex: 1; padding-right: 14px; margin-right: 14px; border-right: 1px solid {RULE}; }}
  .stat:last-child {{ border-right: none; }}
  .stat-num {{ font-family: {SERIF}; font-size: 21px; font-weight: 600; }}
  .stat-label {{ font-size: 9.5px; color: {MUTED}; text-transform: uppercase; letter-spacing: 0.05em; margin-top: 2px; }}

  .context {{ border-top: 1px solid {RULE}; padding-top: 10px; margin-bottom: 8mm; }}
  .section-label {{ font-size: 10px; letter-spacing: 0.07em; text-transform: uppercase; color: {INK_SEC}; font-weight: 600; margin-bottom: 6px; }}
  .context p {{ margin: 0; color: {INK_SEC}; font-size: 12px; max-width: 165mm; }}
  .context em {{ font-style: italic; color: {INK}; }}

  table {{ width: 100%; border-collapse: collapse; margin-bottom: 8mm; }}
  thead th {{
    text-align: left; font-size: 9.5px; text-transform: uppercase; letter-spacing: 0.05em;
    color: {INK_SEC}; font-weight: 600; padding: 0 10px 8px 0; border-bottom: 2px solid {INK};
  }}
  tbody tr {{ border-bottom: 1px solid {RULE}; }}
  tbody td {{ padding: 10px 10px 10px 0; vertical-align: top; font-size: 11.5px; }}
  .c-issue {{ font-weight: 600; width: 24%; }}
  .c-scope {{ width: 15%; color: {INK_SEC}; white-space: nowrap; }}
  .c-fix {{ width: 45%; color: {INK}; }}
  .c-status {{ width: 11%; }}
  .tag {{ display: inline-flex; align-items: center; gap: 5px; font-size: 10.5px; font-weight: 600; color: {INK_SEC}; white-space: nowrap; }}
  .dot {{ width: 6px; height: 6px; border-radius: 50%; display: inline-block; }}

  .validated {{ border-top: 1px solid {RULE}; padding-top: 10px; }}
  .check-list {{ display: flex; flex-direction: column; gap: 6px; margin-top: 6px; }}
  .check {{ display: flex; align-items: baseline; gap: 8px; font-size: 11.5px; color: {INK}; font-family: {SERIF}; }}
  .check .mark {{ color: {GOOD}; font-family: {SANS}; font-weight: 600; }}

  footer {{
    margin-top: 12mm; padding-top: 8px; border-top: 1px solid {RULE};
    color: {MUTED}; font-size: 9.5px; display: flex; justify-content: space-between;
  }}
</style>
</head>
<body>
<div class="page">
  <div class="masthead">
    <div class="eyebrow">Task 2 &middot; Sales Data (FactSale)</div>
    <h1>Data Quality Summary</h1>
    <div class="byline"><b>Prepared by Nahla Nabil</b> &middot; VOLTIX Data Analyst Internship &middot; what was checked in 26,397 raw sales line items, what was found, and how each issue was resolved before analysis.</div>
  </div>

  <div class="stat-strip">
    <div class="stat"><div class="stat-num">26,397</div><div class="stat-label">Rows checked</div></div>
    <div class="stat"><div class="stat-num">8</div><div class="stat-label">Issues reviewed</div></div>
    <div class="stat"><div class="stat-num">0</div><div class="stat-label">Broken formulas</div></div>
    <div class="stat"><div class="stat-num">100%</div><div class="stat-label">Rows clean after fixes</div></div>
  </div>

  <div class="context">
    <div class="section-label">Context</div>
    <p>I only got the fact table (<em>FactSale.csv</em>) &mdash; no lookup tables for products, customers, or
    salespeople. So a couple of items below aren't things I "fixed," they're just limits of what I was
    given. I flagged those instead of making up IDs or names that don't actually exist in the data.</p>
  </div>

  <table>
    <thead>
      <tr><th>Issue</th><th>Scope</th><th>How it was handled</th><th>Status</th></tr>
    </thead>
    <tbody>
      {row_html}
    </tbody>
  </table>

  <div class="validated">
    <div class="section-label">Financial formulas validated across all 26,397 rows</div>
    <div class="check-list">
      <div class="check"><span class="mark">&#10003;</span> Total Excluding Tax = Quantity &times; Unit Price</div>
      <div class="check"><span class="mark">&#10003;</span> Tax Amount = Total Excluding Tax &times; (Tax Rate &divide; 100)</div>
      <div class="check"><span class="mark">&#10003;</span> Total Including Tax = Total Excluding Tax + Tax Amount</div>
    </div>
  </div>

  <footer>
    <span>Cleaned_FactSale.csv &middot; clean_and_validate.py</span>
    <span>Nahla Nabil &middot; VOLTIX Data Analyst Internship</span>
  </footer>
</div>
</body>
</html>
"""

pathlib.Path(OUT_HTML).write_text(html, encoding="utf-8")

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto(pathlib.Path(OUT_HTML).resolve().as_uri())
    page.wait_for_timeout(200)
    page.pdf(path=OUT_PDF, format="A4", print_background=True, margin={"top": "0", "bottom": "0", "left": "0", "right": "0"})
    browser.close()

print(f"Wrote {OUT_HTML} and {OUT_PDF}")
