"""
Step 4: interactive customer dashboard (Python builds ONE self-contained HTML file).

Reads  Cleaned_Customers.csv + analysis_summary.json
Writes Customer_Dashboard.html

The 2,100 cleaned customers are embedded as JSON together with Plotly.js; the page re-aggregates every KPI, chart and
table in the browser whenever a filter changes, so filters are real cross-filters (like Power BI slicers):
  * filters: period (from / to month), gender, age group, category, spend band, rating, email domain, weekday
  * click a bar (age group, gender, month, spend band, category, star rating, weekday) to filter by it; click again to clear
  * a chart filtered by its own dimension keeps every category visible and highlights the selection
  * every KPI card compares the selection with all customers
  * the segment scorecard (table view of the charts) can be switched between 6 dimensions
  * "Download filtered rows" exports the current selection as CSV
Opens offline (Plotly is embedded), follows the OS light/dark setting, with a manual theme toggle.
"""
import json

import pandas as pd
from plotly.offline import get_plotlyjs

IN_CSV, IN_JSON, OUT_HTML = "Cleaned_Customers.csv", "analysis_summary.json", "Customer_Dashboard.html"

GEN = ["Female", "Male", "Unknown"]
AGE = ["15-29", "30-44", "45-59", "60-74", "75-90", "Unknown"]
CATS = ["Books", "Clothing", "Electronics", "Home", "Toys", "Unknown"]
BANDS = ["Under $250", "$250-499", "$500-749", "$750+", "Unknown"]
DOMS = ["gmail.com", "hotmail.com", "yahoo.com"]
WD = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def build_data(df):
    d0 = df.Purchase_Date.min()
    idx = lambda s, cats: s.map({c: i for i, c in enumerate(cats)}).astype(int).tolist()
    ym = ((df.Year - 2022) * 12 + df.Month_Num - 10)
    nz = lambda s: [None if pd.isna(v) else v for v in s]
    cols = {
        "id": df.Customer_ID.tolist(), "nm": df.Name.tolist(),
        "g": idx(df.Gender, GEN), "age": [None if pd.isna(v) else int(v) for v in df.Age], "ag": idx(df.Age_Group, AGE),
        "as": idx(df.Age_Status, ["Valid", "Missing", "Placeholder -1", "Placeholder 200"]),
        "dom": idx(df.Email_Domain, DOMS), "ps": idx(df.Phone_Status, ["Missing", "Placeholder"]),
        "amt": nz(df.Purchase_Amount.round(2)), "band": idx(df.Spend_Band, BANDS),
        "d": [None if pd.isna(v) else int(v) for v in (df.Purchase_Date - d0).dt.days],
        "ym": [-1 if pd.isna(v) else int(v) for v in ym], "wd": [-1 if pd.isna(v) else int(v) - 1 for v in df.Weekday_Num],
        "cat": idx(df.Product_Category, CATS), "r": [0 if pd.isna(v) else int(v) for v in df.Rating],
        "rs": idx(df.Rating_Status, ["Valid", "Missing", "Out of range (10)"]), "vf": df.Valid_Fields.astype(int).tolist(),
    }
    return {"cols": cols, "D0": str(d0.date()), "DAYS": int((df.Purchase_Date.max() - d0).days) + 1}


def insights_html(S):
    k, t = S["kpi"], S["tests"]
    h1 = S["h1"]
    moy = {r["Month"]: r for r in S["month_of_year"]}
    others = sum(r["purchases"] for m, r in moy.items() if m not in ("Aug", "Sep")) / 10
    dip = 1 - (moy["Aug"]["purchases"] + moy["Sep"]["purchases"]) / 2 / others
    seg_p = [v for n, v in t.items() if "trend" not in n and "H1" not in n and "calendar" not in n]
    items = [
        ("Data quality is the biggest finding",
         f"Only <b>{k['complete_record_rate']:.1%} of records</b> are valid in every field. Age is usable for "
         f"<b>{S['quality']['Age']:.0%}</b> of customers (the rest are -1, 200 or blank), {1 - S['quality']['Rating']:.0%} of ratings "
         f"are blank or '10', {1 - S['quality']['Product category']:.0%} of purchases have no category, and <b>not one phone number is real</b>."),
        ("Big tickets carry the revenue",
         f"Orders of <b>$750+ are {k['big_ticket_order_share']:.0%} of orders but {k['big_ticket_revenue_share']:.0%} of revenue</b>, while "
         f"orders under $250 are 24% of orders and only 6% of revenue. Average order ${k['aov']:.0f}, total recorded revenue "
         f"${k['revenue'] / 1e6:.2f}M."),
        ("Satisfaction is split down the middle",
         f"Average rating <b>{k['avg_rating']:.2f} / 5</b>: <b>{k['dissatisfied_share']:.0%}</b> of ratings are 1-2 stars and "
         f"<b>{k['satisfied_share']:.0%}</b> are 4-5. The mix is the same in every category, gender, age group and order size "
         f"(all p &ge; 0.11), so the cause lies outside this data, e.g. delivery or service."),
        ("Sales are flat",
         f"About <b>{k['purchases_per_full_month']:.0f} purchases and ${k['revenue_per_full_month'] / 1000:.0f}K a month</b> for "
         f"{k['full_months']} months, with no trend (p = {t['Monthly purchases trend (linear regression, full months)']:.2f}). "
         f"January-June revenue moved {h1[1]['revenue'] / h1[0]['revenue'] - 1:+.1%} in 2024 and {h1[2]['revenue'] / h1[1]['revenue'] - 1:+.1%} in 2025."),
        ("No seasonality: beware calendar traps",
         f"August-September look <b>{dip:.0%} weaker</b>, but only because they occur in 2 of the years covered, not 3. Per 30 days "
         f"of data every month is alike (p = {t['Month-of-year purchases vs calendar coverage (chi-square)']:.2f}). "
         f"2025-Q3 looks like a collapse, but it holds only 23 days."),
        ("No segment stands out",
         f"Order value and rating do not differ by gender, age, category, weekday or email provider: none of {len(seg_p)} tests is "
         f"significant (smallest p = {min(seg_p):.2f}). {k['top_category']} leads revenue by a margin chance explains, and "
         f"<b>{k['unknown_category_revenue_share']:.0%} of revenue</b> has no category at all."),
    ]
    return "".join(f'<article class="insight"><h3>{h}</h3><p>{p}</p></article>' for h, p in items)


TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Customer Analytics Dashboard</title>
<style>
  :root {
    color-scheme: light;
    --page:#f4f5f2; --card:#fcfcfb; --ink:#0b0b0b; --ink-2:#52514e; --muted:#898781;
    --grid:#e1e0d9; --axis:#c3c2b7; --border:rgba(11,11,11,0.10); --wash:#eceae4;
    --s1:#2a78d6; --s2:#eb6834; --s3:#1baf7a; --dim:#cfd8e3; --neutral:#b9b7ae; --light1:#86b6ef;
    --o1:#86b6ef; --o2:#3987e5; --o3:#256abf; --o4:#184f95; --o5:#0d366b;
    --r1:#e34948; --r2:#f19a99; --r3:#d5d3cb; --r4:#86b6ef; --r5:#2a78d6;
    --good:#006300; --bad:#b3261e; --accent:#1f3a5f; --callout:#eef4fc;
  }
  @media (prefers-color-scheme: dark) {
    :root:not([data-theme="light"]) {
      color-scheme: dark;
      --page:#0d0d0d; --card:#1a1a19; --ink:#ffffff; --ink-2:#c3c2b7; --muted:#898781;
      --grid:#2c2c2a; --axis:#383835; --border:rgba(255,255,255,0.10); --wash:#262624;
      --s1:#3987e5; --s2:#d95926; --s3:#199e70; --dim:#34404d; --neutral:#5a5954; --light1:#184f95;
      --o1:#b7d3f6; --o2:#6da7ec; --o3:#3987e5; --o4:#256abf; --o5:#184f95;
      --r1:#e66767; --r2:#9a3b3b; --r3:#4a4944; --r4:#184f95; --r5:#6da7ec;
      --good:#0ca30c; --bad:#e66767; --accent:#9ec5f4; --callout:#15212e;
    }
  }
  :root[data-theme="dark"] {
    color-scheme: dark;
    --page:#0d0d0d; --card:#1a1a19; --ink:#ffffff; --ink-2:#c3c2b7; --muted:#898781;
    --grid:#2c2c2a; --axis:#383835; --border:rgba(255,255,255,0.10); --wash:#262624;
    --s1:#3987e5; --s2:#d95926; --s3:#199e70; --dim:#34404d; --neutral:#5a5954; --light1:#184f95;
    --o1:#b7d3f6; --o2:#6da7ec; --o3:#3987e5; --o4:#256abf; --o5:#184f95;
    --r1:#e66767; --r2:#9a3b3b; --r3:#4a4944; --r4:#184f95; --r5:#6da7ec;
    --good:#0ca30c; --bad:#e66767; --accent:#9ec5f4; --callout:#15212e;
  }
  * { box-sizing:border-box; }
  body { margin:0; background:var(--page); color:var(--ink); font-family:system-ui,-apple-system,"Segoe UI",Arial,sans-serif; }
  .wrap { max-width:1360px; margin:0 auto; padding:20px 16px 32px; }
  header { display:flex; justify-content:space-between; align-items:flex-end; gap:12px; flex-wrap:wrap; }
  h1 { margin:0 0 4px; font-size:1.5rem; color:var(--accent); }
  h2 { margin:28px 0 2px; font-size:1.08rem; color:var(--accent); }
  .sub { color:var(--ink-2); font-size:.88rem; }
  .note { color:var(--ink-2); font-size:.8rem; margin:0 0 10px; }
  .filters { position:sticky; top:0; z-index:20; background:var(--page); padding:10px 0; margin:12px 0 12px;
             border-bottom:1px solid var(--grid); display:flex; flex-wrap:wrap; gap:10px 12px; align-items:flex-end; }
  .filters label { font-size:.72rem; color:var(--ink-2); display:flex; flex-direction:column; gap:3px; }
  select, button { font:inherit; font-size:.85rem; color:var(--ink); background:var(--card); border:1px solid var(--axis);
                   border-radius:6px; padding:6px 8px; min-height:34px; }
  button { cursor:pointer; } button:hover { background:var(--wash); }
  select:focus-visible, button:focus-visible { outline:2px solid var(--s1); outline-offset:1px; }
  .chips { display:flex; gap:6px; flex-wrap:wrap; align-items:center; font-size:.78rem; color:var(--ink-2); width:100%; min-height:24px; }
  .chip { background:var(--wash); border-radius:999px; padding:2px 4px 2px 10px; color:var(--ink); display:inline-flex; align-items:center; }
  .chip button { border:none; background:none; padding:0 6px; min-height:0; font-size:1rem; line-height:1; color:var(--ink-2); }
  .kpis { display:grid; grid-template-columns:repeat(8,minmax(0,1fr)); gap:10px; }
  .kpi { background:var(--card); border:1px solid var(--border); border-radius:10px; padding:12px 12px 10px; }
  .kpi .l { font-size:.72rem; color:var(--ink-2); min-height:2.1em; }
  .kpi .v { font-size:1.55rem; font-weight:650; margin:4px 0 2px; }
  .kpi .d { font-size:.72rem; color:var(--muted); min-height:1.1em; }
  .kpi .d .up { color:var(--good); } .kpi .d .down { color:var(--bad); }
  .insights { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:12px; }
  .insight { background:var(--card); border:1px solid var(--border); border-left:3px solid var(--s1); border-radius:10px; padding:10px 14px; }
  .insight h3 { margin:0 0 4px; font-size:.9rem; }
  .insight p { margin:0; font-size:.8rem; line-height:1.5; color:var(--ink-2); }
  .insight b { color:var(--ink); }
  .callout { background:var(--callout); border:1px solid var(--border); border-radius:10px; padding:10px 14px; margin-top:12px;
             font-size:.8rem; line-height:1.55; color:var(--ink-2); }
  .callout b { color:var(--ink); }
  .grid2 { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:12px; }
  .grid3 { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:12px; }
  .span2 { grid-column:span 2; }
  .card { background:var(--card); border:1px solid var(--border); border-radius:10px; padding:8px 10px 4px; min-width:0; }
  .card .why { font-size:.74rem; color:var(--muted); margin:0 4px 6px; }
  .tbl { overflow-x:auto; }
  .tblhead { display:flex; justify-content:space-between; align-items:center; gap:10px; padding:8px 4px 6px; flex-wrap:wrap; }
  .tblhead b { font-size:.9rem; }
  table { border-collapse:collapse; width:100%; font-size:.8rem; font-variant-numeric:tabular-nums; }
  th { text-align:left; color:var(--ink-2); font-weight:600; border-bottom:1px solid var(--axis); padding:7px 8px; white-space:nowrap; }
  td { border-bottom:1px solid var(--grid); padding:6px 8px; white-space:nowrap; }
  td.n, th.n { text-align:right; }
  tr.sel td { background:var(--wash); font-weight:600; }
  tr.tot td { font-weight:600; border-top:1px solid var(--axis); }
  .bar { display:inline-block; height:8px; border-radius:0 4px 4px 0; background:var(--s1); vertical-align:middle; margin-right:6px; }
  .recs { background:var(--card); border:1px solid var(--border); border-radius:10px; padding:6px 18px 6px 34px; }
  .recs li { margin:8px 0; font-size:.85rem; line-height:1.5; }
  footer { margin-top:26px; font-size:.74rem; color:var(--muted); line-height:1.6; }
  @media (max-width:1100px) { .kpis { grid-template-columns:repeat(4,minmax(0,1fr)); } .insights, .grid3 { grid-template-columns:repeat(2,minmax(0,1fr)); } }
  @media (max-width:720px) { .kpis { grid-template-columns:repeat(2,minmax(0,1fr)); } .insights, .grid2, .grid3 { grid-template-columns:1fr; } .span2 { grid-column:auto; }
                             .filters { position:static; } }
</style>
</head>
<body>
<div class="wrap">
  <header>
    <div>
      <h1>Customer Analytics Dashboard</h1>
      <div class="sub">__N__ customers &middot; purchases from __FIRST__ to __LAST__ &middot; 5 product categories &middot; cleaned data (see DATA_QUALITY_REPORT.md)</div>
    </div>
    <div style="display:flex;gap:8px">
      <button id="btnCsv" type="button">Download filtered rows</button>
      <button id="btnTheme" type="button" aria-label="Toggle light or dark theme">Theme: auto</button>
    </div>
  </header>

  <div class="filters" role="group" aria-label="Filters">
    <label>From<select id="fFrom"></select></label>
    <label>To<select id="fTo"></select></label>
    <label>Gender<select id="fG"></select></label>
    <label>Age group<select id="fAg"></select></label>
    <label>Category<select id="fCat"></select></label>
    <label>Order size<select id="fBand"></select></label>
    <label>Rating<select id="fRb"></select></label>
    <label>Email provider<select id="fDom"></select></label>
    <label>Weekday<select id="fWd"></select></label>
    <button id="btnReset" type="button">Reset all</button>
    <div class="chips" id="chips" aria-live="polite"></div>
  </div>

  <section class="kpis" id="kpis" aria-label="Key performance indicators"></section>

  <h2>Key insights</h2>
  <p class="note">Written from all customers. The charts below follow the filters.</p>
  <section class="insights">__INSIGHTS__</section>
  <div class="callout"><b>How to read the flat results.</b> The source file (<i>Customers_Fakedata.csv</i>) behaves like randomly generated data:
    amounts are spread uniformly from $5 to $1,000 (KS test p = __KS_AMT__), ages uniformly from 15 to 90 (p = __KS_AGE__), all five star levels are equally
    likely (p = __RATE_UNIF__), and gender is unrelated to the first name (p = __G_NAME__). Flat patterns are therefore the expected, honest result, not a
    failure to find something. Every step is scripted, so the same dashboard can be rebuilt on real data.</div>

  <h2>1 &middot; Who are the customers?</h2>
  <p class="note">Age, gender and how complete each customer record is.</p>
  <div class="grid3">
    <div class="card"><div id="cAge"></div><p class="why">Only customers with a real age (15-90). Click a bar to filter.</p></div>
    <div class="card"><div id="cGender"></div><p class="why">Recorded gender contradicts the first name in half of the rows, so treat gender with caution.</p></div>
    <div class="card"><div id="cQuality"></div><p class="why">Share of the selected customers with a usable value in each field.</p></div>
  </div>

  <h2>2 &middot; Purchases &amp; spending</h2>
  <p class="note">How much customers spend and how revenue develops over time.</p>
  <div class="grid3">
    <div class="card span2"><div id="cTrend"></div><p class="why">Hatched bars are partial months (the data starts 27 Oct 2022 and ends 23 Jul 2025). The line is a 3-month average of full months. Click a month to filter.</p></div>
    <div class="card"><div id="cBand"></div><p class="why">Big orders bring a much larger share of revenue than of orders. Click to filter.</p></div>
    <div class="card"><div id="cHist"></div><p class="why">Order values are spread evenly: no typical basket size.</p></div>
    <div class="card"><div id="cH1"></div><p class="why">Same months (January-June) each year, so the years are comparable. Ignores the period filter.</p></div>
    <div class="card"><div id="cMoy"></div><p class="why">Purchases per 30 days of data in each calendar month. Raw totals would make Aug-Sep look low, because they occur in fewer years.</p></div>
  </div>

  <h2>3 &middot; Product categories</h2>
  <p class="note">What customers buy. "Unknown" = purchases with no category recorded.</p>
  <div class="grid3">
    <div class="card"><div id="cCatRev"></div><p class="why">Click a category to filter.</p></div>
    <div class="card"><div id="cCatAov"></div><p class="why">Line = average order value for the current filter.</p></div>
    <div class="card"><div id="cCatMix"></div><p class="why">Left of the line: 1-2 star ratings. Right: 4-5 stars. The 3-star share is split across the line.</p></div>
  </div>

  <h2>4 &middot; Customer ratings</h2>
  <p class="note">How satisfied customers are, on a 1-5 scale. Blank ratings and invalid '10' ratings are excluded.</p>
  <div class="grid3">
    <div class="card"><div id="cRating"></div><p class="why">Click a star level to filter by dissatisfied (1-2), neutral (3) or satisfied (4-5).</p></div>
    <div class="card span2"><div id="cRatingSeg"></div><p class="why">The same diverging view for gender, age group and order size: every segment is split in the same way.</p></div>
  </div>

  <h2>5 &middot; Patterns by weekday and segment</h2>
  <p class="note">Is any day or group different? Use the table to compare segments in numbers.</p>
  <div class="grid3">
    <div class="card"><div id="cWeekday"></div><p class="why">Click a day to filter. Invalid dates are excluded.</p></div>
    <div class="card span2 tbl">
      <div class="tblhead"><b>Segment scorecard</b>
        <label style="font-size:.75rem;color:var(--ink-2)">Compare by <select id="tDim"></select></label></div>
      <div id="tSeg"></div>
      <p class="why">Revenue uses recorded amounts; ratings use valid 1-5 ratings only. Arrows mark order values or ratings more than 5% above or below the selection average.</p>
    </div>
  </div>

  <h2>Recommendations</h2>
  <ol class="recs">
    <li><b>Fix data capture at the source.</b> Replace free-text age with a date of birth, make gender, category and rating drop-downs, validate dates and phone numbers,
      and block duplicate customer IDs. Target: complete records from __COMPLETE__ to 90%+.</li>
    <li><b>Give every purchase a category.</b> Back-fill the __UNK_N__ uncategorised purchases (__UNK_REV__ of revenue, __UNK_SHARE__) from the order or product system.
      Until then every category share has a 26-point blind spot.</li>
    <li><b>Find out why 2 in 5 customers are dissatisfied.</b> Add a reason code and comment to every rating, link ratings to delivery and returns data, and
      contact 1-2 star customers within 48 hours. Targets: average rating 3.0 &rarr; 3.5, dissatisfied share __DIS__ &rarr; below 25%.</li>
    <li><b>Protect and grow big orders.</b> $750+ orders bring __BIG__ of revenue: give them priority service, and A/B-test bundles or upgrades on $250-749 orders.
      Use experiments rather than demographic targeting, because no segment behaves differently.</li>
    <li><b>Start measuring loyalty.</b> Every customer ID here has exactly one purchase, and 2,100 customers share 144 email addresses. A persistent customer ID
      across orders would make repeat rate and lifetime value measurable. Track monthly purchases against the ~60/month baseline.</li>
  </ol>

  <footer>
    Customer_Dashboard.html &middot; built with Python (pandas + Plotly.js) from Cleaned_Customers.csv &middot; works offline.<br>
    Revenue and order value use the __PRICED__ purchases with a recorded amount (97 have none; they were not estimated). Ratings use the __RATED__ valid 1-5 ratings.
    Age charts use the __AGES__ customers with a real age. Purchases with an invalid date (32/13/2020) are included only when the full period is selected.
    "Complete record" = age, gender, amount, date, category and rating are all valid. AOV = average order value.
  </footer>
</div>

<script>__PLOTLYJS__</script>
<script>
"use strict";
const DATA = __DATA__;
const C = DATA.cols, N = C.id.length, D0 = new Date(DATA.D0 + "T00:00:00Z"), NDAYS = DATA.DAYS;
const GEN = ["Female","Male","Unknown"], AGE = ["15-29","30-44","45-59","60-74","75-90","Unknown"];
const CATS = ["Books","Clothing","Electronics","Home","Toys","Unknown"], BANDS = ["Under $250","$250-499","$500-749","$750+","Unknown"];
const RB = ["Dissatisfied (1-2★)","Neutral (3★)","Satisfied (4-5★)","No valid rating"], DOMS = ["gmail.com","hotmail.com","yahoo.com"];
const WD = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"], MON = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
const NM = 34, FIRST_FULL = 1, LAST_FULL = 32;                  // month index 0 = Oct 2022 (partial), 33 = Jul 2025 (partial)
const mLabel = k => MON[(k+9)%12] + " " + (2022 + Math.floor((k+9)/12));
const RBAND = i => C.r[i]===0 ? 3 : (C.r[i]<=2 ? 0 : (C.r[i]===3 ? 1 : 2));
C.rb = Array.from({length:N}, (_,i)=>RBAND(i));
const ALL = Array.from({length:N}, (_,i)=>i);
const DEF = {from:0, to:NM-1, g:null, ag:null, cat:null, band:null, rb:null, dom:null, wd:null};
const state = Object.assign({}, DEF);
const DIMS = {g:"g", ag:"ag", cat:"cat", band:"band", rb:"rb", dom:"dom", wd:"wd"};
let T = {};

// ------------------------------------------------------------------ helpers
const sum = a => a.reduce((x,y)=>x+y,0);
const mean = a => a.length ? sum(a)/a.length : null;
const median = a => { if (!a.length) return null; const s=[...a].sort((x,y)=>x-y), h=s.length>>1; return s.length%2 ? s[h] : (s[h-1]+s[h])/2; };
const fmt = (v,d=1) => (v===null||v===undefined||Number.isNaN(v)) ? "–" : Number(v).toFixed(d);
const pctS = (v,d=0) => (v===null||Number.isNaN(v)) ? "–" : (v*100).toFixed(d)+"%";
const money = v => v===null ? "–" : "$" + Math.round(v).toLocaleString("en-US");
const kMoney = v => v===null ? "–" : (Math.abs(v)>=1e6 ? "$"+(v/1e6).toFixed(2)+"M" : (Math.abs(v)>=1e3 ? "$"+(v/1e3).toFixed(1)+"K" : "$"+Math.round(v)));
const esc = s => String(s).replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const fullRange = () => state.from===0 && state.to===NM-1;
function select(skip) {
  const out = [], per = skip!=="m" && !fullRange();
  for (let i=0;i<N;i++) {
    if (per && (C.ym[i]<state.from || C.ym[i]>state.to)) continue;       // invalid dates (ym = -1) drop out of any period filter
    let ok = true;
    for (const k in DIMS) { if (k!==skip && state[k]!==null && C[DIMS[k]][i]!==state[k]) { ok=false; break; } }
    if (ok) out.push(i);
  }
  return out;
}
function readTheme() {
  const cs = getComputedStyle(document.documentElement), g = n => cs.getPropertyValue(n).trim();
  T = {}; ["page","card","ink","ink-2","muted","grid","axis","wash","s1","s2","s3","dim","neutral","light1",
           "o1","o2","o3","o4","o5","r1","r2","r3","r4","r5"].forEach(k => T[k]=g("--"+k));
}
function layout(title, h, extra) {
  return Object.assign({
    title:{text:title, font:{size:14, color:T.ink}, x:0.01, xanchor:"left", y:0.97, yanchor:"top"},
    paper_bgcolor:T.card, plot_bgcolor:T.card, height:h||300,
    font:{family:'system-ui,-apple-system,"Segoe UI",Arial,sans-serif', color:T["ink-2"], size:11.5},
    margin:{t:48,l:48,r:14,b:38}, bargap:0.3,
    hoverlabel:{bgcolor:T.card, bordercolor:T.axis, font:{color:T.ink, size:12}},
    xaxis:{gridcolor:T.grid, linecolor:T.axis, zeroline:false, tickfont:{color:T.muted}, automargin:true, fixedrange:true},
    yaxis:{gridcolor:T.grid, linecolor:T.axis, zeroline:false, tickfont:{color:T.muted}, automargin:true, fixedrange:true, rangemode:"tozero"},
    legend:{orientation:"h", y:1.0, yanchor:"bottom", x:1, xanchor:"right", font:{color:T["ink-2"], size:11}},
    showlegend:false,
  }, extra||{});
}
const wired = {};
function draw(id, data, lay, onClick) {
  Plotly.react(id, data, lay, {responsive:true, displaylogo:false, displayModeBar:false});
  if (onClick && !wired[id]) { document.getElementById(id).on("plotly_click", onClick); wired[id]=true; }
}
function toggle(key, val) { state[key] = state[key]===val ? null : val; syncUI(); render(); }
const refLine = (v, axis) => axis==="x"
  ? {type:"line", xref:"x", yref:"paper", x0:v, x1:v, y0:0, y1:1, line:{color:T.ink, width:1.5}}
  : {type:"line", xref:"paper", yref:"y", x0:0, x1:1, y0:v, y1:v, line:{color:T.ink, width:1.5}};

// ------------------------------------------------------------------ filters UI
function fillSelect(id, opts, allLabel) {
  const el = document.getElementById(id); el.innerHTML = "";
  if (allLabel) { const o=document.createElement("option"); o.value=""; o.textContent=allLabel; el.appendChild(o); }
  opts.forEach((t,i) => { const o=document.createElement("option"); o.value=String(i); o.textContent=t; el.appendChild(o); });
}
const SEL = {fG:["g",GEN], fAg:["ag",AGE], fCat:["cat",CATS], fBand:["band",BANDS], fRb:["rb",RB], fDom:["dom",DOMS], fWd:["wd",WD]};
function initFilters() {
  const months = Array.from({length:NM}, (_,k)=>mLabel(k) + (k===0||k===NM-1 ? " (partial)" : ""));
  fillSelect("fFrom", months); fillSelect("fTo", months);
  document.getElementById("fFrom").onchange = e => { state.from=+e.target.value; if (state.to<state.from) state.to=state.from; syncUI(); render(); };
  document.getElementById("fTo").onchange = e => { state.to=+e.target.value; if (state.from>state.to) state.from=state.to; syncUI(); render(); };
  for (const [id,[key,opts]] of Object.entries(SEL)) {
    fillSelect(id, opts, "All");
    document.getElementById(id).onchange = e => { state[key] = e.target.value==="" ? null : +e.target.value; render(); };
  }
  fillSelect("tDim", TABLE_DIMS.map(d=>d[0]));
  document.getElementById("tDim").onchange = () => tableSeg(select(null));
  document.getElementById("btnReset").onclick = () => { Object.assign(state, DEF); syncUI(); render(); };
  document.getElementById("btnCsv").onclick = downloadCsv;
  const btn = document.getElementById("btnTheme"), modes = ["auto","light","dark"];
  let mode = "auto";
  try { mode = localStorage.getItem("custTheme") || "auto"; } catch(e) {}
  const apply = () => { if (mode==="auto") document.documentElement.removeAttribute("data-theme"); else document.documentElement.setAttribute("data-theme", mode);
                        btn.textContent = "Theme: "+mode; readTheme(); render(); };
  btn.onclick = () => { mode = modes[(modes.indexOf(mode)+1)%3]; try { localStorage.setItem("custTheme", mode); } catch(e) {} apply(); };
  window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", () => { if (mode==="auto") { readTheme(); render(); } });
  if (mode!=="auto") { document.documentElement.setAttribute("data-theme", mode); btn.textContent = "Theme: "+mode; }
}
function syncUI() {
  document.getElementById("fFrom").value = String(state.from);
  document.getElementById("fTo").value = String(state.to);
  for (const [id,[key]] of Object.entries(SEL)) document.getElementById(id).value = state[key]===null ? "" : String(state[key]);
}
function renderChips() {
  const chips = [];
  if (!fullRange()) chips.push([state.from===state.to ? mLabel(state.from) : mLabel(state.from)+" – "+mLabel(state.to), ()=>{state.from=DEF.from; state.to=DEF.to;}]);
  const names = {g:GEN, ag:AGE.map(a=>a==="Unknown"?"Age unknown":"Age "+a), cat:CATS.map(c=>c==="Unknown"?"No category":c), band:BANDS.map(b=>b==="Unknown"?"No amount":b),
                 rb:RB, dom:DOMS, wd:WD};
  for (const k in names) if (state[k]!==null) chips.push([names[k][state[k]], ()=>{state[k]=null;}]);
  const el = document.getElementById("chips"); el.textContent = "";
  if (!chips.length) { el.textContent = "Showing all customers. Tip: click bars in the charts to filter."; return; }
  const lab = document.createElement("span"); lab.textContent = "Active filters:"; el.appendChild(lab);
  chips.forEach(([txt,fn]) => {
    const s=document.createElement("span"); s.className="chip"; s.appendChild(document.createTextNode(txt));
    const b=document.createElement("button"); b.type="button"; b.textContent="×"; b.setAttribute("aria-label","Remove filter "+txt);
    b.onclick=()=>{fn(); syncUI(); render();}; s.appendChild(b); el.appendChild(s);
  });
}

// ------------------------------------------------------------------ measures
function measures(ids) {
  const amts = ids.filter(i=>C.amt[i]!==null).map(i=>C.amt[i]);
  const rs = ids.filter(i=>C.r[i]>0).map(i=>C.r[i]);
  const lo = Math.max(state.from, FIRST_FULL), hi = Math.min(state.to, LAST_FULL), nfm = Math.max(0, hi-lo+1);
  const inFull = ids.filter(i=>C.ym[i]>=lo && C.ym[i]<=hi);
  return {
    n: ids.length, rev: sum(amts), priced: amts.length, aov: mean(amts), med: median(amts),
    rated: rs.length, avgR: mean(rs), sat: rs.length ? rs.filter(r=>r>=4).length/rs.length : null,
    dis: rs.length ? rs.filter(r=>r<=2).length/rs.length : null,
    complete: ids.length ? ids.filter(i=>C.vf[i]===6).length/ids.length : null,
    perMonth: nfm ? inFull.length/nfm : null, revMonth: nfm ? sum(inFull.filter(i=>C.amt[i]!==null).map(i=>C.amt[i]))/nfm : null, nfm,
  };
}
const BASE = measures(ALL);

// ------------------------------------------------------------------ KPI cards
function delta(v, b, kind, upGood) {
  if (v===null || b===null) return "";
  const diff = kind==="pct" ? (v-b)*100 : (kind==="money" ? v-b : v-b);
  const tiny = kind==="pct" ? 0.5 : (kind==="money" ? 5 : 0.05);
  if (Math.abs(diff) < tiny) return "same as all customers";
  const up = diff > 0, cls = upGood===null ? "" : (up===upGood ? "up" : "down");
  const txt = (up?"▲ ":"▼ ") + (kind==="pct" ? Math.abs(diff).toFixed(0)+" pts" : (kind==="money" ? "$"+Math.abs(diff).toFixed(0) : Math.abs(diff).toFixed(2))) + " vs all";
  return `<span class="${cls}">${txt}</span>`;
}
function renderKPIs(M, filtered) {
  const d = (v,b,k,g) => filtered ? delta(v,b,k,g) : "";
  const cards = [
    ["Customers", M.n.toLocaleString("en-US"), filtered ? `${pctS(M.n/N)} of all ${N.toLocaleString("en-US")}` : "unique customer IDs"],
    ["Recorded revenue", kMoney(M.rev), filtered ? `${pctS(M.rev/BASE.rev)} of all revenue` : `${M.priced.toLocaleString("en-US")} priced orders`],
    ["Average order value", money(M.aov), filtered ? d(M.aov,BASE.aov,"money",true) : `median ${money(M.med)}`],
    ["Purchases per month", fmt(M.perMonth,1), M.nfm ? `${kMoney(M.revMonth)} / month · ${M.nfm} full months` : "no full month selected"],
    ["Average rating", fmt(M.avgR,2) + " / 5", filtered ? d(M.avgR,BASE.avgR,"num",true) : `${M.rated.toLocaleString("en-US")} valid ratings`],
    ["Satisfied (4-5★)", pctS(M.sat), d(M.sat,BASE.sat,"pct",true)],
    ["Dissatisfied (1-2★)", pctS(M.dis), d(M.dis,BASE.dis,"pct",false)],
    ["Complete records", pctS(M.complete,1), filtered ? d(M.complete,BASE.complete,"pct",true) : "valid in all 6 fields"],
  ];
  document.getElementById("kpis").innerHTML = cards.map(([l,v,dd]) =>
    `<div class="kpi"><div class="l">${l}</div><div class="v">${v}</div><div class="d">${dd}</div></div>`).join("");
}

// ------------------------------------------------------------------ chart helpers
function countBy(ids, key, n) { const c=new Array(n).fill(0); for (const i of ids) if (C[key][i]>=0) c[C[key][i]]++; return c; }
function aovBy(ids, key, n) { const s=new Array(n).fill(0), c=new Array(n).fill(0);
  for (const i of ids) if (C.amt[i]!==null && C[key][i]>=0) { s[C[key][i]]+=C.amt[i]; c[C[key][i]]++; } return s.map((v,k)=>c[k]?v/c[k]:null); }
function revBy(ids, key, n) { const s=new Array(n).fill(0); for (const i of ids) if (C.amt[i]!==null && C[key][i]>=0) s[C[key][i]]+=C.amt[i]; return s; }
function ratingBy(ids, key, n) { const s=new Array(n).fill(0), c=new Array(n).fill(0);
  for (const i of ids) if (C.r[i]>0 && C[key][i]>=0) { s[C[key][i]]+=C.r[i]; c[C[key][i]]++; } return s.map((v,k)=>c[k]?v/c[k]:null); }
function starMix(ids) { const c=[0,0,0,0,0]; for (const i of ids) if (C.r[i]>0) c[C.r[i]-1]++; const t=sum(c); return {p:c.map(v=>t?v/t:0), n:t}; }
const hi = (n, sel, col, dimCol) => Array.from({length:n}, (_,k) => sel===null || sel===k ? col : (dimCol||T.dim));

function hbar(id, title, labels, vals, o) {
  o = Object.assign({fmtv:v=>v, colors:null, sel:null, key:null, hover:"", h:300, custom:null, ref:null, refLabel:"", xfmt:null, inside:false}, o);
  const order = labels.map((_,k)=>k).reverse();
  const base = o.colors || labels.map(()=>T.s1);
  const data = [{type:"bar", orientation:"h", y:order.map(k=>labels[k]), x:order.map(k=>vals[k]),
    marker:{color:order.map(k => o.sel===null||o.sel===k ? base[k] : T.dim), cornerradius:4},
    text:order.map(k => vals[k]===null ? "" : o.fmtv(vals[k], k)), textposition:o.inside ? "inside" : "outside", insidetextanchor:"start", cliponaxis:false,
    textfont:{size:10.5, color:o.inside ? order.map(k => (o.sel===null||o.sel===k) && base[k]!==T.neutral ? "#ffffff" : T.ink) : T["ink-2"]},
    customdata:order.map(k => o.custom ? o.custom[k] : k), hovertemplate:o.hover}];
  const lay = layout(title, o.h, {margin:{t:48,l:10,r:60,b:30}, bargap:0.32,
    xaxis:{gridcolor:T.grid, zeroline:false, tickfont:{color:T.muted}, fixedrange:true, rangemode:"tozero", tickformat:o.xfmt||""},
    yaxis:{tickfont:{color:T["ink-2"]}, automargin:true, fixedrange:true}});
  if (o.ref!==null) { lay.shapes=[refLine(o.ref,"x")];
    lay.title.text = `${title}<br><span style="font-size:11px;color:${T.muted}">${o.refLabel}</span>`; lay.margin.t = 58; }
  const key = o.key;
  draw(id, data, lay, key ? ev => { toggle(key, labels.indexOf(ev.points[0].y)); } : null);
}

// ------------------------------------------------------------------ section 1: customers
function chartAge() {
  const ids = select("ag"), c = countBy(ids, "ag", 6), a = aovBy(ids, "ag", 6), r = ratingBy(ids, "ag", 6);
  const known = sum(c.slice(0,5)), ramp = [T.o1,T.o2,T.o3,T.o4,T.o5];
  draw("cAge", [{type:"bar", x:AGE.slice(0,5), y:c.slice(0,5), marker:{color:ramp.map((col,k)=> state.ag===null||state.ag===k ? col : T.dim), cornerradius:4},
    text:c.slice(0,5).map(v=>v ? `${v} (${Math.round(v/(known||1)*100)}%)` : ""), textposition:"outside", cliponaxis:false, textfont:{size:10.5, color:T["ink-2"]},
    customdata:AGE.slice(0,5).map((_,k)=>[money(a[k]), fmt(r[k],2)]),
    hovertemplate:"Age %{x}: <b>%{y} customers</b><br>AOV %{customdata[0]} · rating %{customdata[1]}<extra></extra>"}],
    layout(`Customers by age group <span style="font-size:11px;color:${T.muted}">(${c[5].toLocaleString("en-US")} of ${ids.length.toLocaleString("en-US")} have no real age)</span>`, 300,
      {xaxis:{title:{text:"age (15-year bands)", font:{size:11, color:T.muted}}, tickfont:{color:T["ink-2"]}, fixedrange:true, linecolor:T.axis}}),
    ev => toggle("ag", ev.points[0].pointIndex));
}
function chartGender() {
  const ids = select("g"), c = countBy(ids, "g", 3), a = aovBy(ids, "g", 3), r = ratingBy(ids, "g", 3), n = ids.length||1;
  hbar("cGender", "Customers by gender", GEN, c, {sel:state.g, key:"g", colors:[T.s1,T.s1,T.neutral],
    fmtv:v=>`${v.toLocaleString("en-US")} (${Math.round(v/n*100)}%)`, custom:GEN.map((_,k)=>[money(a[k]), fmt(r[k],2)]),
    hover:"%{y}: <b>%{x} customers</b><br>AOV %{customdata[0]} · rating %{customdata[1]}<extra></extra>"});
}
function chartQuality(ids) {
  const n = ids.length || 1;
  const F = [
    ["Purchase amount", i=>C.amt[i]!==null, i=>false],
    ["Purchase date", i=>C.ym[i]>=0, i=>C.ym[i]<0],
    ["Gender", i=>C.g[i]!==2, i=>false],
    ["Product category", i=>C.cat[i]!==5, i=>false],
    ["Rating", i=>C.rs[i]===0, i=>C.rs[i]===2],
    ["Age", i=>C.as[i]===0, i=>C.as[i]>=2],
    ["Phone", i=>false, i=>C.ps[i]===1],
  ].reverse();
  const val = F.map(([,v])=>ids.filter(v).length/n), inv = F.map(([,,b])=>ids.filter(b).length/n), blank = val.map((v,k)=>1-v-inv[k]);
  const y = F.map(f=>f[0]);
  const tr = (x, name, col, dark) => ({type:"bar", orientation:"h", y, x, name, marker:{color:col, line:{color:T.card, width:2}},
    text:x.map(v=> v>=0.1 ? Math.round(v*100)+"%" : ""), textposition:"inside", textangle:0, insidetextanchor:"middle", textfont:{color:dark?"#ffffff":T.ink, size:11},
    hovertemplate:`%{y}: <b>%{x:.0%}</b> ${name.toLowerCase()}<extra></extra>`});
  draw("cQuality", [tr(val,"Usable",T.s1,true), tr(blank,"Blank",T.neutral,false), tr(inv,"Invalid / placeholder",T.s2,false)],
    layout("Usable data per field", 300, {barmode:"stack", showlegend:true, bargap:0.3, margin:{t:48,l:10,r:10,b:30},
      legend:{orientation:"h", y:-0.08, yanchor:"top", x:0, xanchor:"left", font:{color:T["ink-2"], size:10.5}, traceorder:"normal"},
      xaxis:{range:[0,1], tickformat:".0%", gridcolor:T.grid, tickfont:{color:T.muted}, fixedrange:true, zeroline:false},
      yaxis:{tickfont:{color:T["ink-2"]}, automargin:true, fixedrange:true}}));
}

// ------------------------------------------------------------------ section 2: spend & time
function chartTrend() {
  const ids = select("m"), rev = new Array(NM).fill(0), cnt = new Array(NM).fill(0);
  for (const i of ids) if (C.ym[i]>=0) { cnt[C.ym[i]]++; if (C.amt[i]!==null) rev[C.ym[i]]+=C.amt[i]; }
  const x = Array.from({length:NM}, (_,k)=>mLabel(k));
  const inSel = k => k>=state.from && k<=state.to;
  const full = k => k>=FIRST_FULL && k<=LAST_FULL;
  const roll = x.map((_,k) => full(k) && full(k-1) && full(k+1) ? (rev[k-1]+rev[k]+rev[k+1])/3 : null);
  const fullRev = rev.filter((_,k)=>full(k)), avg = mean(fullRev);
  const cd = x.map((_,k)=>[cnt[k], cnt[k] ? money(rev[k]/cnt[k]) : "–"]);
  const hov = "<b>%{x}</b><br>revenue %{y:$,.0f}<br>%{customdata[0]} purchases · AOV %{customdata[1]}<extra></extra>";
  draw("cTrend", [
    {type:"bar", x, y:rev.map((v,k)=> full(k) ? v : null), name:"Monthly revenue", marker:{color:x.map((_,k)=> inSel(k) ? T.light1 : T.dim)},
     customdata:cd, hovertemplate:hov},
    {type:"bar", x, y:rev.map((v,k)=> full(k) ? null : v), name:"Partial month", marker:{color:T.card, line:{color:T.neutral, width:1.5},
     pattern:{shape:"/", fgcolor:T.neutral, size:5}}, customdata:cd, hovertemplate:hov.replace("</b>", " (partial month)</b>")},
    {type:"scatter", mode:"lines", x, y:roll, name:"3-month average", line:{color:T.s1, width:2}, connectgaps:false, hoverinfo:"skip"},
  ], layout("Recorded revenue per month", 300, {showlegend:true, bargap:0.25, barmode:"overlay",
      xaxis:{tickfont:{color:T.muted}, fixedrange:true, linecolor:T.axis, tickangle:0, nticks:12},
      yaxis:{gridcolor:T.grid, tickfont:{color:T.muted}, fixedrange:true, tickprefix:"$", tickformat:",.0f", rangemode:"tozero"},
      shapes: avg ? [refLine(avg,"y")] : [],
      annotations: avg ? [{xref:"paper", x:0, y:avg, text:`full-month average ${kMoney(avg)}`, showarrow:false, yshift:10, xanchor:"left",
                           font:{color:T.ink, size:11}, bgcolor:T.card}] : []}),
    ev => { const k = x.indexOf(ev.points[0].x); if (state.from===k && state.to===k) { state.from=DEF.from; state.to=DEF.to; } else { state.from=k; state.to=k; } syncUI(); render(); });
}
function chartBand() {
  const ids = select("band"), c = countBy(ids, "band", 5).slice(0,4), rv = revBy(ids, "band", 5).slice(0,4);
  const tc = sum(c)||1, tr = sum(rv)||1, x = BANDS.slice(0,4);
  const mk = (y, name, col) => ({type:"bar", x, y, name, marker:{color:x.map((_,k)=> state.band===null||state.band===k ? col : T.dim), cornerradius:3},
    text:y.map(v=>Math.round(v*100)+"%"), textposition:"outside", cliponaxis:false, textfont:{size:10.5, color:T["ink-2"]},
    hovertemplate:`%{x}: <b>%{y:.0%}</b> ${name}<extra></extra>`});
  draw("cBand", [mk(c.map(v=>v/tc), "of orders", T.s1), mk(rv.map(v=>v/tr), "of revenue", T.s2)],
    layout("Orders vs revenue by order size", 300, {showlegend:true, barmode:"group", bargroupgap:0.08,
      legend:{orientation:"h", y:1.0, yanchor:"bottom", x:1, xanchor:"right", font:{color:T["ink-2"], size:11}},
      yaxis:{gridcolor:T.grid, tickformat:".0%", tickfont:{color:T.muted}, fixedrange:true, rangemode:"tozero"}}),
    ev => toggle("band", ev.points[0].pointIndex));
}
function chartHist(ids) {
  const a = ids.filter(i=>C.amt[i]!==null).map(i=>C.amt[i]), c = new Array(20).fill(0);
  for (const v of a) c[Math.min(19, Math.floor(v/50))]++;
  const x = c.map((_,k)=>k*50+25), med = median(a);
  draw("cHist", [{type:"bar", x, y:c, width:46, marker:{color:T.s1, cornerradius:2},
    customdata:c.map((_,k)=>`$${k*50}-${k*50+50}`), hovertemplate:"%{customdata}: <b>%{y} orders</b><extra></extra>"}],
    layout(`Order values <span style="font-size:11px;color:${T.muted}">(${a.length.toLocaleString("en-US")} priced orders)</span>`, 300, {
      xaxis:{tickprefix:"$", tickfont:{color:T.muted}, fixedrange:true, linecolor:T.axis, range:[0,1000]},
      yaxis:{gridcolor:T.grid, tickfont:{color:T.muted}, fixedrange:true, range:[0, Math.max(10, ...c)*1.2]},
      shapes: med!==null ? [refLine(med,"x")] : [],
      annotations: med!==null ? [{x:med, yref:"paper", y:1, text:`median ${money(med)}`, showarrow:false, xanchor:"left", xshift:4, font:{size:11, color:T.ink}}] : []}));
}
function chartH1() {
  const ids = select("m"), yrs = [2023,2024,2025], rv = [0,0,0], n = [0,0,0];
  for (const i of ids) { const k = C.ym[i]; if (k<0) continue; const y = 2022+Math.floor((k+9)/12), m = (k+9)%12;
    if (m<=5 && y>=2023) { n[y-2023]++; if (C.amt[i]!==null) rv[y-2023]+=C.amt[i]; } }
  const lab = rv.map((v,k)=> k===0 ? kMoney(v) : `${kMoney(v)}<br>${rv[k-1] ? ((v/rv[k-1]-1)*100>=0?"+":"")+((v/rv[k-1]-1)*100).toFixed(1)+"%" : ""}`);
  draw("cH1", [{type:"bar", x:yrs.map(String), y:rv, marker:{color:[T.light1,T.light1,T.s1], cornerradius:4}, text:lab, textposition:"outside", cliponaxis:false,
    textfont:{size:11, color:T["ink-2"]}, customdata:n, hovertemplate:"Jan-Jun %{x}: <b>%{y:$,.0f}</b><br>%{customdata} purchases<extra></extra>"}],
    layout("January-June revenue, year on year", 300, {bargap:0.45,
      yaxis:{gridcolor:T.grid, tickfont:{color:T.muted}, fixedrange:true, tickprefix:"$", tickformat:"~s", rangemode:"tozero"},
      xaxis:{type:"category", tickfont:{color:T["ink-2"]}, fixedrange:true, linecolor:T.axis}}));
}
function chartMoy(ids) {
  const lo = state.from, hi2 = state.to, days = new Array(12).fill(0), c = new Array(12).fill(0);
  for (let t=0; t<NDAYS; t++) { const dt = new Date(D0.getTime()+t*864e5), k = (dt.getUTCFullYear()-2022)*12 + dt.getUTCMonth() - 9;
    if (k>=lo && k<=hi2) days[dt.getUTCMonth()]++; }
  for (const i of ids) if (C.ym[i]>=0) c[(C.ym[i]+9)%12]++;
  const per = c.map((v,k)=> days[k] ? v/days[k]*30 : null), avg = sum(c)/(sum(days)||1)*30;
  draw("cMoy", [{type:"bar", x:MON, y:per, marker:{color:T.s1, cornerradius:3}, text:per.map(v=>v===null?"":v.toFixed(0)), textposition:"outside", cliponaxis:false,
    textfont:{size:10, color:T["ink-2"]}, customdata:MON.map((_,k)=>[c[k], days[k]]),
    hovertemplate:"%{x}: <b>%{y:.1f} purchases per 30 days</b><br>%{customdata[0]} purchases in %{customdata[1]} days of data<extra></extra>"}],
    layout(`Purchases per 30 days, by calendar month <span style="font-size:11px;color:${T.muted}">(average ${avg.toFixed(0)})</span>`, 300, {bargap:0.25,
      xaxis:{tickfont:{color:T.muted, size:10.5}, fixedrange:true, linecolor:T.axis}}));
}

// ------------------------------------------------------------------ section 3: categories
function chartCatRev() {
  const ids = select("cat"), rv = revBy(ids, "cat", 6), c = countBy(ids, "cat", 6), t = sum(rv)||1;
  hbar("cCatRev", "Recorded revenue by category", CATS, rv, {sel:state.cat, key:"cat", colors:[T.s1,T.s1,T.s1,T.s1,T.s1,T.neutral],
    fmtv:v=>`${kMoney(v)} (${Math.round(v/t*100)}%)`, custom:c, xfmt:"$~s",
    hover:"%{y}: <b>%{x:$,.0f}</b><br>%{customdata} purchases<extra></extra>"});
}
function chartCatAov() {
  const ids = select("cat"), a = aovBy(ids, "cat", 6), c = countBy(ids, "cat", 6);
  const all = mean(ids.filter(i=>C.amt[i]!==null).map(i=>C.amt[i]));
  hbar("cCatAov", "Average order value by category", CATS, a, {sel:state.cat, key:"cat", colors:[T.s1,T.s1,T.s1,T.s1,T.s1,T.neutral],
    fmtv:v=>money(v), custom:c, ref:all, refLabel:`vertical line = average ${money(all)}`, xfmt:"$,.0f", inside:true,
    hover:"%{y}: <b>AOV %{x:$,.0f}</b><br>%{customdata} purchases<extra></extra>"});
}
function divergingRows(id, title, rows, h) {
  // rows: [label, ids]; stars 1-2 left of zero, 3 split across zero, 4-5 right
  const cols = [T.r1,T.r2,T.r3,T.r4,T.r5], y = rows.map(r=>r[0]).reverse(), mixes = rows.map(r=>starMix(r[1])).reverse();
  const traces = [];
  for (let s=0; s<5; s++) {
    const base = mixes.map(m => { const p=m.p; return -(p[0]+p[1]+p[2]/2) + p.slice(0,s).reduce((a,b)=>a+b,0); });
    traces.push({type:"bar", orientation:"h", y, x:mixes.map(m=>m.p[s]), base, name:`${s+1}★`, marker:{color:cols[s], line:{color:T.card, width:1.5}},
      customdata:mixes.map(m=>m.n), hovertemplate:`%{y} · ${s+1}★: <b>%{x:.0%}</b> of %{customdata} ratings<extra></extra>`});
  }
  const ann = [];
  mixes.forEach((m,k) => { const p=m.p; if (!m.n) return;
    ann.push({x:-(p[0]+p[1]+p[2]/2), y:y[k], text:Math.round((p[0]+p[1])*100)+"%", showarrow:false, xanchor:"right", xshift:-4, font:{size:10.5, color:T["ink-2"]}});
    ann.push({x:p[2]/2+p[3]+p[4], y:y[k], text:Math.round((p[3]+p[4])*100)+"%", showarrow:false, xanchor:"left", xshift:4, font:{size:10.5, color:T["ink-2"]}}); });
  draw(id, traces, layout(title, h, {barmode:"overlay", showlegend:true, bargap:0.3, margin:{t:48,l:10,r:14,b:58}, annotations:ann,
    legend:{orientation:"h", y:-0.1, yanchor:"top", x:0.5, xanchor:"center", font:{color:T["ink-2"], size:10.5}, traceorder:"normal"},
    xaxis:{range:[-0.8,0.8], tickvals:[-0.6,-0.4,-0.2,0,0.2,0.4,0.6], ticktext:["60%","40%","20%","0","20%","40%","60%"], gridcolor:T.grid,
           tickfont:{color:T.muted}, fixedrange:true, zeroline:true, zerolinecolor:T.ink, zerolinewidth:1},
    yaxis:{tickfont:{color:T["ink-2"]}, automargin:true, fixedrange:true}}));
}
function chartCatMix(ids) {
  divergingRows("cCatMix", "Rating mix by category", CATS.map((c,k)=>[c, ids.filter(i=>C.cat[i]===k)]), 300);
}

// ------------------------------------------------------------------ section 4: ratings
function chartRating() {
  const ids = select("rb"), c = [0,0,0,0,0]; for (const i of ids) if (C.r[i]>0) c[C.r[i]-1]++;
  const t = sum(c)||1, cols = [T.r1,T.r2,T.r3,T.r4,T.r5], bandOf = [0,0,1,2,2];
  draw("cRating", [{type:"bar", x:["1★","2★","3★","4★","5★"], y:c.map(v=>v/t),
    marker:{color:cols.map((col,k)=> state.rb===null||state.rb===bandOf[k] ? col : T.dim), cornerradius:4},
    text:c.map(v=>Math.round(v/t*100)+"%"), textposition:"outside", cliponaxis:false, textfont:{size:11, color:T["ink-2"]}, customdata:c,
    hovertemplate:"%{x}: <b>%{y:.1%}</b> (%{customdata} ratings)<extra></extra>"}],
    layout(`Rating distribution <span style="font-size:11px;color:${T.muted}">(${sum(c).toLocaleString("en-US")} valid ratings, avg ${fmt(mean(ids.filter(i=>C.r[i]>0).map(i=>C.r[i])),2)})</span>`, 300,
      {yaxis:{gridcolor:T.grid, tickformat:".0%", tickfont:{color:T.muted}, fixedrange:true, rangemode:"tozero"},
       xaxis:{tickfont:{color:T["ink-2"]}, fixedrange:true, linecolor:T.axis}}),
    ev => toggle("rb", bandOf[ev.points[0].pointIndex]));
}
function chartRatingSeg(ids) {
  const rows = [["Female", ids.filter(i=>C.g[i]===0)], ["Male", ids.filter(i=>C.g[i]===1)]]
    .concat(AGE.slice(0,5).map((a,k)=>["Age "+a, ids.filter(i=>C.ag[i]===k)]))
    .concat(BANDS.slice(0,4).map((b,k)=>[b, ids.filter(i=>C.band[i]===k)]));
  divergingRows("cRatingSeg", "Rating mix by gender, age group and order size", rows, 420);
}

// ------------------------------------------------------------------ section 5: weekday + scorecard
function chartWeekday() {
  const ids = select("wd"), c = countBy(ids, "wd", 7), a = aovBy(ids, "wd", 7);
  draw("cWeekday", [{type:"bar", x:WD, y:c, marker:{color:hi(7, state.wd, T.s1), cornerradius:4}, text:c.map(v=>v||""), textposition:"outside", cliponaxis:false,
    textfont:{size:10.5, color:T["ink-2"]}, customdata:a.map(v=>money(v)), hovertemplate:"%{x}: <b>%{y} purchases</b><br>AOV %{customdata}<extra></extra>"}],
    layout("Purchases by weekday", 320, {xaxis:{tickfont:{color:T["ink-2"]}, fixedrange:true, linecolor:T.axis}}),
    ev => toggle("wd", ev.points[0].pointIndex));
}
const TABLE_DIMS = [["Product category","cat",CATS,"cat"], ["Gender","g",GEN,"g"], ["Age group","ag",AGE,"ag"], ["Order size","band",BANDS,"band"],
                    ["Email provider","dom",DOMS,"dom"], ["Weekday","wd",WD,"wd"]];
function tableSeg(ids) {
  const [name, key, labels, stKey] = TABLE_DIMS[+document.getElementById("tDim").value || 0];
  const tot = measures(ids), totRev = tot.rev || 1;
  const rows = labels.map((lab,k) => { const s = ids.filter(i=>C[key][i]===k); return [lab, k, measures(s)]; });
  const mx = Math.max(1, ...rows.map(r=>r[2].n));
  const arrow = (v, b) => v===null||b===null ? "" : (v > b*1.05 ? ' <span style="color:var(--good)">▲</span>' : (v < b*0.95 ? ' <span style="color:var(--bad)">▼</span>' : ""));
  let h = `<table><thead><tr><th>${esc(name)}</th><th class="n">Customers</th><th class="n">Revenue</th><th class="n">% revenue</th><th class="n">AOV</th>
           <th class="n">Avg rating</th><th class="n">Satisfied</th><th class="n">Dissatisfied</th><th class="n">Complete</th></tr></thead><tbody>`;
  for (const [lab, k, m] of rows) {
    h += `<tr class="${state[stKey]===k?"sel":""}"><td>${esc(lab)}</td><td class="n"><span class="bar" style="width:${Math.round(60*m.n/mx)}px"></span>${m.n.toLocaleString("en-US")}</td>
      <td class="n">${kMoney(m.rev)}</td><td class="n">${pctS(m.rev/totRev)}</td><td class="n">${money(m.aov)}${arrow(m.aov, tot.aov)}</td>
      <td class="n">${fmt(m.avgR,2)}${arrow(m.avgR, tot.avgR)}</td><td class="n">${pctS(m.sat)}</td><td class="n">${pctS(m.dis)}</td><td class="n">${pctS(m.complete)}</td></tr>`;
  }
  h += `<tr class="tot"><td>Selection</td><td class="n">${tot.n.toLocaleString("en-US")}</td><td class="n">${kMoney(tot.rev)}</td><td class="n">100%</td>
    <td class="n">${money(tot.aov)}</td><td class="n">${fmt(tot.avgR,2)}</td><td class="n">${pctS(tot.sat)}</td><td class="n">${pctS(tot.dis)}</td><td class="n">${pctS(tot.complete)}</td></tr>`;
  document.getElementById("tSeg").innerHTML = h + "</tbody></table>";
}
function downloadCsv() {
  const ids = select(null), ds = t => t===null ? "" : new Date(D0.getTime()+t*864e5).toISOString().slice(0,10);
  const head = ["Customer_ID","Name","Gender","Age","Age_Group","Email_Domain","Purchase_Amount","Spend_Band","Purchase_Date","Product_Category","Rating"];
  const q = v => { const s = v===null||v===undefined ? "" : String(v); return /[",\n]/.test(s) ? '"'+s.replace(/"/g,'""')+'"' : s; };
  const lines = [head.join(",")].concat(ids.map(i => [C.id[i],C.nm[i],GEN[C.g[i]],C.age[i],AGE[C.ag[i]],DOMS[C.dom[i]],C.amt[i],BANDS[C.band[i]],
    ds(C.d[i]),CATS[C.cat[i]],C.r[i]||""].map(q).join(",")));
  const blob = new Blob(["﻿"+lines.join("\n")], {type:"text/csv;charset=utf-8"});
  const a = document.createElement("a"); a.href = URL.createObjectURL(blob); a.download = "customers_filtered.csv"; a.click();
  setTimeout(() => URL.revokeObjectURL(a.href), 1000);
}

// ------------------------------------------------------------------ render
function render() {
  const ids = select(null), filtered = ids.length !== N || !fullRange();
  renderChips();
  renderKPIs(measures(ids), filtered);
  chartAge(); chartGender(); chartQuality(ids);
  chartTrend(); chartBand(); chartHist(ids); chartH1(); chartMoy(ids);
  chartCatRev(); chartCatAov(); chartCatMix(ids);
  chartRating(); chartRatingSeg(ids);
  chartWeekday(); tableSeg(ids);
}
readTheme(); initFilters(); syncUI(); render();
</script>
</body>
</html>
"""


def main():
    df = pd.read_csv(IN_CSV, parse_dates=["Purchase_Date"])
    S = json.load(open(IN_JSON, encoding="utf-8"))
    k, rnd = S["kpi"], S["randomness"]
    fmt_p = lambda v: f"{v:.2f}"
    rep = {
        "__PLOTLYJS__": get_plotlyjs(), "__DATA__": json.dumps(build_data(df), ensure_ascii=False),
        "__INSIGHTS__": insights_html(S), "__N__": f"{k['customers']:,}",
        "__FIRST__": pd.Timestamp(k["first_date"]).strftime("%d %b %Y"), "__LAST__": pd.Timestamp(k["last_date"]).strftime("%d %b %Y"),
        "__KS_AMT__": fmt_p(rnd["Amounts follow a uniform $5-$1,000 distribution (Kolmogorov-Smirnov)"]),
        "__KS_AGE__": fmt_p(rnd["Ages follow a uniform 15-90 distribution (Kolmogorov-Smirnov, discrete-adjusted)"]),
        "__RATE_UNIF__": fmt_p(rnd["Ratings 1-5 equally likely (chi-square)"]), "__G_NAME__": fmt_p(rnd["Gender independent of first name (chi-square)"]),
        "__COMPLETE__": f"{k['complete_record_rate']:.1%}", "__UNK_N__": str(k["unknown_category_customers"]),
        "__UNK_REV__": f"${k['unknown_category_revenue'] / 1000:,.0f}K", "__UNK_SHARE__": f"{k['unknown_category_revenue_share']:.0%}",
        "__DIS__": f"{k['dissatisfied_share']:.0%}", "__BIG__": f"{k['big_ticket_revenue_share']:.0%}",
        "__PRICED__": f"{k['priced_purchases']:,}", "__RATED__": f"{k['rated']:,}", "__AGES__": str(k["valid_ages"]),
    }
    html = TEMPLATE
    for a, b in rep.items():
        if a != "__PLOTLYJS__":
            html = html.replace(a, b)
    html = html.replace("__PLOTLYJS__", rep["__PLOTLYJS__"])      # last, so no placeholder text inside Plotly is touched
    open(OUT_HTML, "w", encoding="utf-8").write(html)
    print(f"wrote {OUT_HTML} ({len(html) / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
