"""
Renders DATA_QUALITY_ISSUES.pdf: a short, calm-blue, print-ready summary of
the data quality issues found in FactSale.csv and how each was handled.
Source of truth for the content is DATA_QUALITY_REPORT.md (the full write-up);
this is the "simple summary" version of the same findings, designed to print.
"""

from playwright.sync_api import sync_playwright
import pathlib

OUT_HTML = "DATA_QUALITY_ISSUES.html"
OUT_PDF = "DATA_QUALITY_ISSUES.pdf"

NAVY = "#0f2942"
BLUE = "#2a5f8f"
ACCENT = "#3d7ab5"
LIGHT_BLUE_BG = "#eef4f9"
PAGE_BG = "#f7fafc"
INK = "#1c2b36"
INK_SOFT = "#54697a"
GOOD = "#1e7a4a"
FLAG = "#b5651d"
KEPT = "#3d7ab5"

rows = [
    ("Missing Delivery Date", "13 rows (0.05%)",
     "Filled in as Invoice Date + 1 day &mdash; the pattern in 100% of the complete rows.", "Fixed"),
    ("Inconsistent date text format", "All rows",
     "Parsed and standardized to ISO format (YYYY-MM-DD).", "Fixed"),
    ("Numeric columns stored as quoted text", "All rows",
     "Verified / converted to proper numeric types.", "Fixed"),
    ("Customer Key = 0 (no customer captured)", "9,077 rows (34.4%)",
     "Not an error &mdash; flagged with a new Customer_Type column instead of guessing an ID.", "Flagged"),
    ("Duplicate rows", "0 found",
     "Checked full-row and Sale Key (primary key) duplication &mdash; none present.", "Checked"),
    ("Negative Quantity / Unit Price", "0 found",
     "No invalid transaction volumes or prices.", "Checked"),
    ("Negative Profit (loss-making sales)", "566 rows (2.1%)",
     "Kept as-is &mdash; a real, concentrated business finding (see Key Insights), not a data error.", "Kept"),
    ("No product / customer / salesperson names", "All rows",
     "Only the fact table was provided (no dimension tables) &mdash; those fields are reported by ID.", "Noted"),
]

badge_color = {"Fixed": GOOD, "Flagged": FLAG, "Checked": BLUE, "Kept": KEPT, "Noted": INK_SOFT}

row_html = "\n".join(f"""
<tr>
  <td class="c-issue">{issue}</td>
  <td class="c-scope">{scope}</td>
  <td class="c-fix">{fix}</td>
  <td class="c-status"><span class="badge" style="background:{badge_color[status]}1a;color:{badge_color[status]};border-color:{badge_color[status]}55">{status}</span></td>
</tr>
""" for issue, scope, fix, status in rows)

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Data Quality Summary</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
  @page {{ size: A4; margin: 0; }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0; background: {PAGE_BG}; color: {INK};
    font-family: 'Inter', system-ui, -apple-system, sans-serif;
    font-size: 13px; line-height: 1.55;
  }}
  .page {{ width: 210mm; min-height: 297mm; margin: 0 auto; padding: 0 0 16mm 0; position: relative; }}

  .hero {{
    background: linear-gradient(135deg, {NAVY} 0%, {BLUE} 65%, {ACCENT} 100%);
    color: #fff; padding: 15mm 16mm 11mm 16mm; position: relative; overflow: hidden;
  }}
  .hero::after {{
    content: ''; position: absolute; right: -60px; top: -60px; width: 220px; height: 220px;
    border-radius: 50%; background: rgba(255,255,255,0.07);
  }}
  .hero::before {{
    content: ''; position: absolute; right: 40px; bottom: -80px; width: 160px; height: 160px;
    border-radius: 50%; background: rgba(255,255,255,0.06);
  }}
  .eyebrow {{ font-size: 11px; letter-spacing: 0.12em; text-transform: uppercase; opacity: 0.75; font-weight: 600; margin-bottom: 8px; }}
  h1 {{ font-size: 26px; font-weight: 800; margin: 0 0 6px 0; }}
  .hero-sub {{ font-size: 13px; opacity: 0.85; max-width: 460px; }}

  .stats {{ display: flex; gap: 10mm; margin-top: 12mm; }}
  .stat-num {{ font-size: 22px; font-weight: 800; }}
  .stat-label {{ font-size: 10.5px; opacity: 0.8; }}

  .content {{ padding: 10mm 16mm 0 16mm; }}
  .intro {{
    background: {LIGHT_BLUE_BG}; border-left: 3px solid {ACCENT}; border-radius: 6px;
    padding: 10px 14px; color: {INK_SOFT}; font-size: 12.5px; margin-bottom: 8mm;
  }}

  table {{ width: 100%; border-collapse: collapse; margin-bottom: 8mm; }}
  thead th {{
    text-align: left; font-size: 10px; text-transform: uppercase; letter-spacing: 0.05em;
    color: {INK_SOFT}; font-weight: 700; padding: 0 10px 8px 10px; border-bottom: 2px solid {NAVY};
  }}
  tbody tr {{ border-bottom: 1px solid #dbe6ee; }}
  tbody td {{ padding: 10px; vertical-align: top; font-size: 12px; }}
  .c-issue {{ font-weight: 700; color: {NAVY}; width: 24%; }}
  .c-scope {{ width: 15%; color: {INK_SOFT}; white-space: nowrap; }}
  .c-fix {{ width: 43%; color: {INK}; }}
  .c-status {{ width: 12%; }}
  .badge {{
    display: inline-block; font-size: 10.5px; font-weight: 700; padding: 3px 10px;
    border-radius: 20px; border: 1px solid; white-space: nowrap;
  }}

  .validated {{
    background: {LIGHT_BLUE_BG}; border-radius: 10px; padding: 12px 16px; margin-bottom: 6mm;
  }}
  .validated h3 {{ margin: 0 0 8px 0; font-size: 13px; color: {NAVY}; }}
  .check-list {{ display: flex; flex-direction: column; gap: 6px; }}
  .check {{ display: flex; align-items: center; gap: 8px; font-size: 12px; color: {INK}; }}
  .check .dot {{
    width: 16px; height: 16px; border-radius: 50%; background: {GOOD}; color: #fff;
    display: flex; align-items: center; justify-content: center; font-size: 10px; flex: none;
  }}

  footer {{ position: absolute; bottom: 0; left: 0; right: 0; padding: 6mm 16mm; color: {INK_SOFT}; font-size: 9.5px; display: flex; justify-content: space-between; border-top: 1px solid #dbe6ee; }}
</style>
</head>
<body>
<div class="page">
  <div class="hero">
    <div class="eyebrow">Task 2 &middot; Sales Data (FactSale)</div>
    <h1>Data Quality Summary</h1>
    <div class="hero-sub">What was checked in 26,397 raw sales line items, what was found, and how each issue was resolved before analysis.</div>
    <div class="stats">
      <div><div class="stat-num">26,397</div><div class="stat-label">rows checked</div></div>
      <div><div class="stat-num">8</div><div class="stat-label">issues reviewed</div></div>
      <div><div class="stat-num">0</div><div class="stat-label">broken formulas</div></div>
      <div><div class="stat-num">100%</div><div class="stat-label">rows clean after fixes</div></div>
    </div>
  </div>

  <div class="content">
    <div class="intro">
      Only the fact table (<em>FactSale.csv</em>) was provided &mdash; no product, customer, or salesperson
      lookup tables. That shapes two of the findings below: they aren't cleaning gaps, they're a known limit
      of the source data, handled by labelling rather than guessing.
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
      <h3>Financial formulas validated across all 26,397 rows</h3>
      <div class="check-list">
        <div class="check"><span class="dot">&#10003;</span> Total Excluding Tax = Quantity &times; Unit Price</div>
        <div class="check"><span class="dot">&#10003;</span> Tax Amount = Total Excluding Tax &times; (Tax Rate &divide; 100)</div>
        <div class="check"><span class="dot">&#10003;</span> Total Including Tax = Total Excluding Tax + Tax Amount</div>
      </div>
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
