"""
Renders DATA_QUALITY_ISSUES.pdf: a short, print-ready summary of the data
quality issues found in FactSale.csv and how each was handled. Same plain
blue look as Sales_Dashboard.html (Arial, simple bordered boxes, no fancy
typography) so everything submitted for this task matches.

Source of truth for the content is DATA_QUALITY_REPORT.md (the full write-up);
this is the "simple summary" version of the same findings, designed to print.
"""

from playwright.sync_api import sync_playwright
import pathlib

OUT_HTML = "DATA_QUALITY_ISSUES.html"
OUT_PDF = "DATA_QUALITY_ISSUES.pdf"

PAGE_BG = "#eef4fb"
CARD_BG = "#ffffff"
BORDER = "#c7dcf0"
INK = "#1c3d5a"
INK_SOFT = "#4d6e8c"
BLUE_DEEP = "#123456"
GOOD = "#1e7a4a"
FLAG = "#a8631a"
KEPT = "#2e75b6"
CRIT = "#b5322f"

FONT = "Arial, Helvetica, sans-serif"

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
     "Only the fact table was provided (no dimension tables) &mdash; those fields are reported by ID.", "Noted", INK_SOFT),
]

row_html = "\n".join(f"""
<tr>
  <td class="c-issue">{issue}</td>
  <td class="c-scope">{scope}</td>
  <td class="c-fix">{fix}</td>
  <td class="c-status"><span class="tag" style="color:{color}">&#9679; {status}</span></td>
</tr>
""" for issue, scope, fix, status, color in rows)

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Data Quality Summary</title>
<style>
  @page {{ size: A4; margin: 0; }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0; background: {PAGE_BG}; color: {INK};
    font-family: {FONT}; font-size: 12.5px; line-height: 1.55;
  }}
  .page {{ width: 210mm; min-height: 297mm; margin: 0 auto; padding: 14mm 14mm 12mm 14mm; }}

  h1 {{ font-size: 22px; font-weight: bold; margin: 0 0 4px 0; color: {BLUE_DEEP}; }}
  .subtitle {{ font-size: 11px; color: {INK_SOFT}; margin-bottom: 8mm; }}

  .stat-row {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-bottom: 8mm; }}
  .stat {{ background: {CARD_BG}; border: 1px solid {BORDER}; border-radius: 6px; padding: 10px 12px; text-align: center; }}
  .stat-num {{ font-size: 18px; font-weight: bold; color: {INK}; }}
  .stat-label {{ font-size: 9.5px; color: {INK_SOFT}; margin-top: 2px; }}

  .box {{ background: {CARD_BG}; border: 1px solid {BORDER}; border-radius: 6px; padding: 10px 14px; margin-bottom: 6mm; }}
  .box p {{ margin: 0; color: {INK}; font-size: 11.5px; }}

  table {{ width: 100%; border-collapse: collapse; background: {CARD_BG}; border: 1px solid {BORDER}; border-radius: 6px; overflow: hidden; margin-bottom: 6mm; }}
  thead th {{
    text-align: left; font-size: 10px; color: {INK_SOFT}; font-weight: bold;
    padding: 8px 10px; background: {PAGE_BG}; border-bottom: 1px solid {BORDER};
  }}
  tbody tr {{ border-bottom: 1px solid {BORDER}; }}
  tbody tr:last-child {{ border-bottom: none; }}
  tbody td {{ padding: 9px 10px; vertical-align: top; font-size: 11.5px; }}
  .c-issue {{ font-weight: bold; width: 24%; }}
  .c-scope {{ width: 15%; color: {INK_SOFT}; white-space: nowrap; }}
  .c-fix {{ width: 45%; }}
  .c-status {{ width: 11%; }}
  .tag {{ font-size: 10.5px; font-weight: bold; white-space: nowrap; }}

  .check-list {{ display: flex; flex-direction: column; gap: 5px; }}
  .check {{ font-size: 11.5px; color: {INK}; }}
  .check b {{ color: {GOOD}; }}

  footer {{
    margin-top: 8mm; color: {INK_SOFT}; font-size: 9.5px; display: flex; justify-content: space-between;
  }}
</style>
</head>
<body>
<div class="page">
  <h1>Data Quality Summary</h1>
  <div class="subtitle">Task 2 &mdash; Sales Data (FactSale) &middot; Nahla Nabil, VOLTIX Data Analyst Internship &middot; what was checked in 26,397 raw sales line items, what was found, and how each issue was resolved before analysis.</div>

  <div class="stat-row">
    <div class="stat"><div class="stat-num">26,397</div><div class="stat-label">Rows checked</div></div>
    <div class="stat"><div class="stat-num">8</div><div class="stat-label">Issues reviewed</div></div>
    <div class="stat"><div class="stat-num">0</div><div class="stat-label">Broken formulas</div></div>
    <div class="stat"><div class="stat-num">100%</div><div class="stat-label">Rows clean after fixes</div></div>
  </div>

  <div class="box">
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

  <div class="box">
    <div class="check-list">
      <div class="check"><b>&#10003;</b> Total Excluding Tax = Quantity &times; Unit Price &mdash; validated across all 26,397 rows</div>
      <div class="check"><b>&#10003;</b> Tax Amount = Total Excluding Tax &times; (Tax Rate &divide; 100) &mdash; validated across all 26,397 rows</div>
      <div class="check"><b>&#10003;</b> Total Including Tax = Total Excluding Tax + Tax Amount &mdash; validated across all 26,397 rows</div>
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
