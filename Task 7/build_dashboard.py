"""
Task 7 - Hospital Analytics: interactive dashboard (Python builds ONE self-contained HTML file).

Reads  Cleaned_Hospital_Data.csv + analysis_summary.json
Writes Hospital_Dashboard.html

How it works: the 247 cleaned admissions are embedded as JSON together with Plotly.js; a script re-aggregates
every KPI, chart and table in the browser whenever a slicer changes, so the filters are real cross-filters
(like Power BI slicers):
  * slicers: month range, doctor, diagnosis, insurance, severity, age group, gender
  * click a bar (month, diagnosis, doctor, age group, severity, insurance) to filter by it - click again to clear
  * a chart that is filtered by its own dimension keeps showing every category and highlights the selection
  * every KPI card compares the filtered value with the whole hospital
  * "Download filtered rows" exports the current slice as CSV

Opens offline (Plotly is embedded), follows the OS light/dark setting, with a manual theme toggle.
"""

import json

import pandas as pd
from plotly.offline import get_plotlyjs

IN_CSV = "Cleaned_Hospital_Data.csv"
IN_JSON = "analysis_summary.json"
OUT_HTML = "Hospital_Dashboard.html"

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
WEEKDAYS = ["Saturday", "Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
SEV = ["Low", "Medium", "High"]
AGE = ["Child (0-17)", "Adult (18-39)", "Middle age (40-59)", "Senior (60+)"]
INS = ["Private", "Government", "Uninsured"]
BS = ["Recorded", "Placeholder 999", "Placeholder 3852"]
RF = ["", "Long stay for minor condition", "Atypical age for diagnosis"]


def build_data(df):
    dx = df["Diagnosis"].value_counts().index.tolist()          # fixed order = overall volume
    doc = df["Doctor"].value_counts().index.tolist()
    d0 = pd.Timestamp("2023-01-01")
    idx = lambda s, cats: s.map({c: i for i, c in enumerate(cats)}).astype(int).tolist()
    cols = {
        "id": df["Patient_ID"].tolist(), "nm": df["Patient_Name"].tolist(), "age": df["Age"].tolist(),
        "ag": idx(df["Age_Group"], AGE), "g": idx(df["Gender"], ["Female", "Male"]),
        "dx": idx(df["Diagnosis"], dx), "doc": idx(df["Doctor"], doc),
        "a": (df["Admission_Date"] - d0).dt.days.tolist(), "d": (df["Discharge_Date"] - d0).dt.days.tolist(),
        "los": df["Length_of_Stay"].tolist(), "ins": idx(df["Insurance"], INS), "sev": idx(df["Severity"], SEV),
        "bill": [None if pd.isna(v) else int(v) for v in df["Bill"]], "bs": idx(df["Bill_Status"], BS),
        "m": df["Admission_Month"].tolist(), "wd": idx(df["Admission_Weekday"], WEEKDAYS),
        "dc": df["Date_Corrected"].astype(int).tolist(), "rf": idx(df["Review_Flag"].fillna(""), RF),
    }
    return {"cols": cols, "DX": dx, "DOC": doc}


def insights_html(S):
    k, f, t = S["kpi"], S["findings"], S["tests"]
    pct = lambda v: f"{v * 100:.0f}%"
    items = [
        ("Very long stays eat a third of the beds",
         f"Only <b>{k['stays_15plus']} admissions ({k['stays_15plus'] / k['total_admissions']:.0%})</b> lasted 15+ days, yet they used "
         f"<b>{pct(k['bed_days_15plus_share'])} of all bed-days</b>. {f['minor_in_15plus']} of them were minor conditions "
         f"(cold, flu, migraine, allergy) - the clearest target for a discharge-planning review."),
        ("Severity does not predict stay length",
         f"High-severity patients stay <b>{f['alos_high']} days</b> vs <b>{f['alos_low']}</b> for low severity - no real difference "
         f"(p = {t['LOS by Severity (Kruskal-Wallis)']:.2f}). Diagnosis doesn't either: a common cold averages <b>{f['cold_alos']} days</b>, "
         f"longer than a stroke ({f['stroke_alos']}). Triage coding or discharge criteria need an audit."),
        ("Age is the one real driver of LOS",
         f"Stay length rises with age (Spearman rho = {S['corr']['age_los_rho']}, p = {t['Age vs LOS (Spearman)']:.2f}): children average "
         f"4.7 days, seniors 7.1. Seniors are <b>{pct(k['senior_share'])} of admissions but {pct(f['senior_bed_day_share'])} of bed-days</b> "
         f"- plan geriatric beds and early social-care discharge support."),
        ("Billing data cannot support revenue reporting",
         f"Only <b>{pct(k['billing_completeness'])} of admissions</b> have a genuine bill; the rest hold the placeholders 999 or 3852. "
         f"Genuine bills rise with stay (rho = {S['corr']['bill_los_rho']}), but <b>none of the {k['stays_15plus']} longest stays</b> "
         f"has one - the costliest care is exactly what is not being billed."),
        ("Demand peaks in May and October",
         f"May had the most admissions (32) and the highest census ({k['peak_census']} patients on "
         f"{pd.Timestamp(k['peak_census_date']):%d %b}); August was quietest (10). Admissions cluster Tuesday-Wednesday "
         f"({f['tue_wed_admissions']}) and drop on Friday ({f['friday_admissions']}) - roster staff to that weekly rhythm."),
        ("Uneven stay lengths across doctors",
         f"{f['top2_doctors'][0]} and {f['top2_doctors'][1]} treat {pct(f['top2_doctor_admission_share'])} of patients but use "
         f"{pct(f['top2_doctor_bed_day_share'])} of bed-days (ALOS 7.5 and 7.2 vs 4.7 for Dr. Sara Ibrahim). Not statistically "
         f"conclusive (p = {t['LOS by Doctor (Kruskal-Wallis)']:.2f}) - review case notes before drawing conclusions."),
    ]
    return "".join(f'<article class="insight"><h3>{h}</h3><p>{p}</p></article>' for h, p in items)


TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Hospital Performance Dashboard</title>
<style>
  :root {
    color-scheme: light;
    --page:#f4f5f2; --card:#fcfcfb; --ink:#0b0b0b; --ink-2:#52514e; --muted:#898781;
    --grid:#e1e0d9; --axis:#c3c2b7; --border:rgba(11,11,11,0.10); --wash:#eceae4;
    --s1:#2a78d6; --s2:#eb6834; --s3:#1baf7a; --dim:#cfd8e3; --neutral:#b9b7ae; --neutral-2:#8f8d85;
    --o1:#86b6ef; --o2:#3987e5; --o3:#1c5cab; --o4:#0d366b;
    --seq0:#fcfcfb; --seq1:#9ec5f4; --seq2:#2a78d6; --seq3:#104281;
    --good:#006300; --bad:#b3261e; --accent:#1f3a5f;
  }
  @media (prefers-color-scheme: dark) {
    :root:not([data-theme="light"]) {
      color-scheme: dark;
      --page:#0d0d0d; --card:#1a1a19; --ink:#ffffff; --ink-2:#c3c2b7; --muted:#898781;
      --grid:#2c2c2a; --axis:#383835; --border:rgba(255,255,255,0.10); --wash:#262624;
      --s1:#3987e5; --s2:#d95926; --s3:#199e70; --dim:#34404d; --neutral:#5a5954; --neutral-2:#7d7b74;
      --o1:#b7d3f6; --o2:#6da7ec; --o3:#2a78d6; --o4:#184f95;
      --seq0:#1a1a19; --seq1:#184f95; --seq2:#3987e5; --seq3:#b7d3f6;
      --good:#0ca30c; --bad:#e66767; --accent:#9ec5f4;
    }
  }
  :root[data-theme="dark"] {
    color-scheme: dark;
    --page:#0d0d0d; --card:#1a1a19; --ink:#ffffff; --ink-2:#c3c2b7; --muted:#898781;
    --grid:#2c2c2a; --axis:#383835; --border:rgba(255,255,255,0.10); --wash:#262624;
    --s1:#3987e5; --s2:#d95926; --s3:#199e70; --dim:#34404d; --neutral:#5a5954; --neutral-2:#7d7b74;
    --o1:#b7d3f6; --o2:#6da7ec; --o3:#2a78d6; --o4:#184f95;
    --seq0:#1a1a19; --seq1:#184f95; --seq2:#3987e5; --seq3:#b7d3f6;
    --good:#0ca30c; --bad:#e66767; --accent:#9ec5f4;
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
  .kpi .d .up { color:var(--bad); } .kpi .d .down { color:var(--good); }
  .insights { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:12px; }
  .insight { background:var(--card); border:1px solid var(--border); border-left:3px solid var(--s1); border-radius:10px; padding:10px 14px; }
  .insight h3 { margin:0 0 4px; font-size:.9rem; }
  .insight p { margin:0; font-size:.8rem; line-height:1.5; color:var(--ink-2); }
  .insight b { color:var(--ink); }
  .grid2 { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:12px; }
  .grid3 { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:12px; }
  .span2 { grid-column:span 2; }
  .card { background:var(--card); border:1px solid var(--border); border-radius:10px; padding:8px 10px 4px; min-width:0; }
  .card .why { font-size:.74rem; color:var(--muted); margin:0 4px 6px; }
  .tbl { overflow-x:auto; }
  table { border-collapse:collapse; width:100%; font-size:.8rem; font-variant-numeric:tabular-nums; }
  th { text-align:left; color:var(--ink-2); font-weight:600; border-bottom:1px solid var(--axis); padding:7px 8px; white-space:nowrap; }
  td { border-bottom:1px solid var(--grid); padding:6px 8px; white-space:nowrap; }
  td.n, th.n { text-align:right; }
  tr.sel td { background:var(--wash); font-weight:600; }
  .bar { display:inline-block; height:8px; border-radius:0 4px 4px 0; background:var(--s1); vertical-align:middle; margin-right:6px; }
  .recs { background:var(--card); border:1px solid var(--border); border-radius:10px; padding:6px 18px; }
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
      <h1>Hospital Performance Dashboard &middot; 2023</h1>
      <div class="sub">__N__ admissions &middot; 7 doctors &middot; 10 diagnoses &middot; cleaned data (see DATA_QUALITY_REPORT.md)</div>
    </div>
    <div style="display:flex;gap:8px">
      <button id="btnCsv" type="button">Download filtered rows</button>
      <button id="btnTheme" type="button" aria-label="Toggle light or dark theme">Theme: auto</button>
    </div>
  </header>

  <div class="filters" role="group" aria-label="Filters">
    <label>From month<select id="fFrom"></select></label>
    <label>To month<select id="fTo"></select></label>
    <label>Doctor<select id="fDoc"></select></label>
    <label>Diagnosis<select id="fDx"></select></label>
    <label>Insurance<select id="fIns"></select></label>
    <label>Severity<select id="fSev"></select></label>
    <label>Age group<select id="fAg"></select></label>
    <label>Gender<select id="fG"></select></label>
    <button id="btnReset" type="button">Reset all</button>
    <div class="chips" id="chips" aria-live="polite"></div>
  </div>

  <section class="kpis" id="kpis" aria-label="Key performance indicators"></section>

  <h2>Key insights</h2>
  <p class="note">Written from the full year. The charts below follow the filters.</p>
  <section class="insights">__INSIGHTS__</section>

  <h2>1 &middot; Demand &amp; capacity</h2>
  <p class="note">When do patients arrive, and how many beds are occupied?</p>
  <div class="grid3">
    <div class="card span2"><div id="cMonth"></div><p class="why">Click a month to filter; click again to clear.</p></div>
    <div class="card"><div id="cWeekday"></div><p class="why">Staff rosters should follow this weekly rhythm.</p></div>
    <div class="card span2"><div id="cCensus"></div><p class="why">Patients in a bed each night of 2023. The peak sets the bed and nurse capacity needed.</p></div>
    <div class="card"><div id="cStayShare"></div><p class="why">A few very long stays use a large share of bed capacity.</p></div>
  </div>

  <h2>2 &middot; Case mix &amp; length of stay</h2>
  <p class="note">What do we treat, and does length of stay match how sick patients are?</p>
  <div class="grid3">
    <div class="card"><div id="cDx"></div><p class="why">Click a diagnosis to filter.</p></div>
    <div class="card"><div id="cDxLos"></div><p class="why">Line = average for the current filter. A cold staying longer than a stroke points to discharge delays.</p></div>
    <div class="card"><div id="cHeat"></div><p class="why">Share of each diagnosis by recorded severity. Stroke mostly 'Low' and cold mostly 'High' suggest coding problems.</p></div>
    <div class="card"><div id="cLosDist"></div><p class="why">Stays over 7 days (orange) are long stays.</p></div>
    <div class="card"><div id="cAge"></div><p class="why">Age is the one factor that clearly lengthens stays. Click to filter.</p></div>
    <div class="card"><div id="cSev"></div><p class="why">High-severity patients should stay longer. Here they do not. Click to filter.</p></div>
  </div>

  <h2>3 &middot; Doctor performance</h2>
  <p class="note">Workload and efficiency per doctor. Click a bar or pick a doctor in the filter.</p>
  <div class="grid3">
    <div class="card"><div id="cDoc"></div><p class="why">Line = average for the current filter.</p></div>
    <div class="card span2 tbl"><div style="padding:8px 4px 0;font-weight:600;font-size:.9rem">Doctor scorecard</div><div id="tDoc"></div>
      <p class="why">Bed-day share above admission share means a doctor's patients stay longer than average.</p></div>
  </div>

  <h2>4 &middot; Insurance &amp; billing</h2>
  <p class="note">Who pays, and can we trust the billing data?</p>
  <div class="grid3">
    <div class="card"><div id="cIns"></div><p class="why">Uninsured admissions carry the highest non-payment risk. Click to filter.</p></div>
    <div class="card"><div id="cBillStatus"></div><p class="why">Most bills are placeholder values (999 or 3852), not real charges.</p></div>
    <div class="card"><div id="cBillLos"></div><p class="why">Genuine bills rise with length of stay. None exist for stays over 12 days.</p></div>
  </div>

  <h2>5 &middot; Records for clinical review</h2>
  <p class="note">Rows flagged during cleaning: kept in the analysis, but worth a check of the chart or coding.</p>
  <div class="card tbl"><div id="tFlags"></div></div>

  <h2>Recommendations</h2>
  <ol class="recs">
    <li><b>Fix billing capture first.</b> Stop the system from saving 999/3852 as defaults and make a real bill mandatory at discharge. Until then, revenue KPIs cover only 21% of admissions.</li>
    <li><b>Run a long-stay review.</b> Hold a weekly review for any patient past day 7, starting with the 17 minor-condition stays of 15+ days. Cutting those 17 stays to the 4-day median would free about 250 bed-days, 16% of the year's total.</li>
    <li><b>Audit severity coding.</b> Severity currently tells us nothing about resource use. Use clear triage criteria and re-check a sample of stroke and pneumonia records.</li>
    <li><b>Plan capacity around seniors and the peaks.</b> The average is about 4 occupied beds a night, but peaks reach 13 (May) and 9 (October). Size flexible capacity for those peaks, add geriatric discharge support, and roster more staff on Tuesday and Wednesday than on Friday.</li>
    <li><b>Fix the admission system.</b> 12% of records had admission and discharge dates reversed, and there is no patient ID. Add date validation and a unique ID so readmissions can be tracked.</li>
  </ol>

  <footer>
    Hospital_Dashboard.html &middot; built with Python (pandas + Plotly.js) from Cleaned_Hospital_Data.csv &middot; works offline.<br>
    ALOS = average length of stay (discharge minus admission, days). Bed-days = sum of stays. Census = patients in a bed each night.
    Finance figures use the __RB__ genuine bills only; placeholder bills (999/3852) are excluded, not estimated.
    Gender is shown as recorded, but it disagrees with the patient's first name in 53% of rows, so treat gender comparisons with caution.
  </footer>
</div>

<script>__PLOTLYJS__</script>
<script>
"use strict";
const DATA = __DATA__;
const C = DATA.cols, DX = DATA.DX, DOC = DATA.DOC, N = C.id.length;
const MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
const WEEKDAYS = ["Sat","Sun","Mon","Tue","Wed","Thu","Fri"];
const SEV = ["Low","Medium","High"], AGE = ["Child (0-17)","Adult (18-39)","Middle age (40-59)","Senior (60+)"];
const INS = ["Private","Government","Uninsured"], GEN = ["Female","Male"];
const BS = ["Recorded","Placeholder 999","Placeholder 3852"];
const RF = ["","Long stay for minor condition","Atypical age for diagnosis"];
const ALL = Array.from({length:N}, (_,i)=>i);
const state = {from:1, to:12, doc:null, dx:null, ins:null, sev:null, ag:null, g:null};
const DIMS = {doc:"doc", dx:"dx", ins:"ins", sev:"sev", ag:"ag", g:"g"};
let T = {};   // theme tokens, read from CSS

// ------------------------------------------------------------------ helpers
const sum = a => a.reduce((x,y)=>x+y,0);
const mean = a => a.length ? sum(a)/a.length : null;
const median = a => { if (!a.length) return null; const s=[...a].sort((x,y)=>x-y), h=s.length>>1; return s.length%2 ? s[h] : (s[h-1]+s[h])/2; };
const fmt = (v,d=1) => (v===null||v===undefined||Number.isNaN(v)) ? "–" : Number(v).toFixed(d);
const pctS = (v,d=0) => v===null ? "–" : (v*100).toFixed(d)+"%";
const esc = s => String(s).replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
function select(skip) {
  const out = [];
  for (let i=0;i<N;i++) {
    if (skip!=="m" && (C.m[i]<state.from || C.m[i]>state.to)) continue;
    let ok = true;
    for (const k in DIMS) { if (k!==skip && state[k]!==null && C[DIMS[k]][i]!==state[k]) { ok=false; break; } }
    if (ok) out.push(i);
  }
  return out;
}
function readTheme() {
  const cs = getComputedStyle(document.documentElement), g = n => cs.getPropertyValue(n).trim();
  T = {}; ["page","card","ink","ink-2","muted","grid","axis","wash","s1","s2","s3","dim","neutral","neutral-2",
           "o1","o2","o3","o4","seq0","seq1","seq2","seq3"].forEach(k => T[k]=g("--"+k));
}
function layout(title, h, extra) {
  return Object.assign({
    title:{text:title, font:{size:14, color:T.ink}, x:0.01, xanchor:"left", y:0.97, yanchor:"top"},
    paper_bgcolor:T.card, plot_bgcolor:T.card, height:h||300,
    font:{family:'system-ui,-apple-system,"Segoe UI",Arial,sans-serif', color:T["ink-2"], size:11.5},
    margin:{t:48,l:48,r:14,b:38}, bargap:0.28,
    hoverlabel:{bgcolor:T.card, bordercolor:T.axis, font:{color:T.ink, size:12}},
    xaxis:{gridcolor:T.grid, linecolor:T.axis, zeroline:false, tickfont:{color:T.muted}, automargin:true, fixedrange:true},
    yaxis:{gridcolor:T.grid, linecolor:T.axis, zeroline:false, tickfont:{color:T.muted}, automargin:true, fixedrange:true},
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
// bar colours: selected category keeps the series colour, the rest dim; nothing selected -> all series colour
const hi = (n, selIdx, col) => Array.from({length:n}, (_,i) => selIdx===null || selIdx===i ? col : T.dim);

// ------------------------------------------------------------------ filters UI
function fillSelect(id, opts, allLabel) {
  const el = document.getElementById(id); el.innerHTML = "";
  if (allLabel) { const o=document.createElement("option"); o.value=""; o.textContent=allLabel; el.appendChild(o); }
  opts.forEach((t,i) => { const o=document.createElement("option"); o.value=String(allLabel?i:i+1); o.textContent=t; el.appendChild(o); });
}
const SEL = {fDoc:["doc",DOC], fDx:["dx",DX], fIns:["ins",INS], fSev:["sev",SEV], fAg:["ag",AGE], fG:["g",GEN]};
function initFilters() {
  fillSelect("fFrom", MONTHS); fillSelect("fTo", MONTHS);
  document.getElementById("fFrom").onchange = e => { state.from=+e.target.value; if (state.to<state.from) state.to=state.from; syncUI(); render(); };
  document.getElementById("fTo").onchange = e => { state.to=+e.target.value; if (state.from>state.to) state.from=state.to; syncUI(); render(); };
  for (const [id,[key,opts]] of Object.entries(SEL)) {
    fillSelect(id, opts, "All");
    document.getElementById(id).onchange = e => { state[key] = e.target.value==="" ? null : +e.target.value; render(); };
  }
  document.getElementById("btnReset").onclick = () => { Object.assign(state,{from:1,to:12,doc:null,dx:null,ins:null,sev:null,ag:null,g:null}); syncUI(); render(); };
  document.getElementById("btnCsv").onclick = downloadCsv;
  const btn = document.getElementById("btnTheme"), modes = ["auto","light","dark"];
  let mode = "auto";
  try { mode = localStorage.getItem("hospTheme") || "auto"; } catch(e) {}
  const apply = () => { if (mode==="auto") document.documentElement.removeAttribute("data-theme"); else document.documentElement.setAttribute("data-theme", mode);
                        btn.textContent = "Theme: "+mode; readTheme(); render(); };
  btn.onclick = () => { mode = modes[(modes.indexOf(mode)+1)%3]; try { localStorage.setItem("hospTheme", mode); } catch(e) {} apply(); };
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
  if (state.from!==1 || state.to!==12) chips.push([state.from===state.to ? MONTHS[state.from-1] : MONTHS[state.from-1]+"–"+MONTHS[state.to-1], ()=>{state.from=1;state.to=12;}]);
  const names = {doc:DOC, dx:DX, ins:INS, sev:SEV.map(s=>s+" severity"), ag:AGE, g:GEN};
  for (const k in names) if (state[k]!==null) chips.push([names[k][state[k]], ()=>{state[k]=null;}]);
  const el = document.getElementById("chips"); el.textContent = "";
  if (!chips.length) { el.textContent = "Showing all 2023 admissions. Tip: click bars in the charts to filter."; return; }
  const lab = document.createElement("span"); lab.textContent = "Active filters:"; el.appendChild(lab);
  chips.forEach(([txt,fn]) => {
    const s=document.createElement("span"); s.className="chip"; s.appendChild(document.createTextNode(txt));
    const b=document.createElement("button"); b.type="button"; b.textContent="×"; b.setAttribute("aria-label","Remove filter "+txt);
    b.onclick=()=>{fn(); syncUI(); render();}; s.appendChild(b); el.appendChild(s);
  });
}

// ------------------------------------------------------------------ measures
function measures(ids) {
  const los = ids.map(i=>C.los[i]), n = ids.length, bd = sum(los);
  const bills = ids.filter(i=>C.bill[i]!==null);
  const cen = census(ids), cen23 = cen.slice(1, 366);
  return {
    n, alos: mean(los), med: median(los), bd,
    longRate: n ? ids.filter(i=>C.los[i]>7).length/n : null,
    high: n ? ids.filter(i=>C.sev[i]===2).length/n : null,
    unins: n ? ids.filter(i=>C.ins[i]===2).length/n : null,
    billComp: n ? bills.length/n : null,
    avgBill: mean(bills.map(i=>C.bill[i])),
    peak: Math.max(0, ...cen), avgCen: sum(cen23)/365,
    bd15: bd ? sum(ids.filter(i=>C.los[i]>=15).map(i=>C.los[i]))/bd : null,
  };
}
const DAY0 = -1, NDAYS = Math.max(...C.d) + 2;     // index 0 = 31 Dec 2022
function census(ids) {
  const c = new Array(NDAYS).fill(0);
  for (const i of ids) for (let t=C.a[i]; t<C.d[i]; t++) c[t-DAY0]++;
  return c;
}
const BASE = measures(ALL);

// ------------------------------------------------------------------ KPI cards
function delta(v, b, kind, goodWhenDown) {
  if (v===null || b===null) return "";
  const diff = kind==="pct" ? (v-b)*100 : v-b;
  if (Math.abs(diff) < (kind==="pct" ? 0.5 : 0.05)) return "same as hospital";
  const up = diff > 0, cls = goodWhenDown===null ? "" : ((up && goodWhenDown) || (!up && !goodWhenDown) ? "up" : "down");
  const txt = (up?"▲ ":"▼ ") + (kind==="pct" ? Math.abs(diff).toFixed(0)+" pts" : Math.abs(diff).toFixed(1)) + " vs hospital";
  return `<span class="${cls}">${txt}</span>`;
}
function renderKPIs(M, filtered) {
  const d = (v,b,k,g) => filtered ? delta(v,b,k,g) : "";
  const cards = [
    ["Admissions", M.n.toLocaleString(), filtered ? `${pctS(M.n/N)} of all ${N}` : "Jan–Dec 2023"],
    ["Avg length of stay", fmt(M.alos,1)+" d", filtered ? d(M.alos,BASE.alos,"num",true) : `median ${fmt(M.med,0)} days`],
    ["Bed-days used", M.bd.toLocaleString(), filtered ? `${pctS(M.bd/BASE.bd)} of hospital total` : `${pctS(M.bd15)} by 15+ day stays`],
    ["Long-stay rate (>7 d)", pctS(M.longRate), d(M.longRate,BASE.longRate,"pct",true)],
    ["Peak bed census", String(M.peak), `avg ${fmt(M.avgCen,1)} patients / night`],
    ["High-severity share", pctS(M.high), d(M.high,BASE.high,"pct",null)],
    ["Uninsured rate", pctS(M.unins), d(M.unins,BASE.unins,"pct",true)],
    ["Billing completeness", pctS(M.billComp), M.avgBill===null ? "no genuine bills" : `avg genuine bill ${Math.round(M.avgBill).toLocaleString()}`],
  ];
  document.getElementById("kpis").innerHTML = cards.map(([l,v,dd]) =>
    `<div class="kpi"><div class="l">${l}</div><div class="v">${v}</div><div class="d">${dd}</div></div>`).join("");
}

// ------------------------------------------------------------------ charts
function countBy(ids, key, n) { const c=new Array(n).fill(0); for (const i of ids) c[C[key][i]]++; return c; }
function losBy(ids, key, n) { const s=new Array(n).fill(0), c=new Array(n).fill(0); for (const i of ids) { s[C[key][i]]+=C.los[i]; c[C[key][i]]++; } return s.map((v,k)=>c[k]?v/c[k]:null); }
const refLine = (v, axis) => axis==="x"
  ? {type:"line", xref:"x", yref:"paper", x0:v, x1:v, y0:0, y1:1, line:{color:T.ink, width:1.5}}
  : {type:"line", xref:"paper", yref:"y", x0:0, x1:1, y0:v, y1:v, line:{color:T.ink, width:1.5}};

function chartMonth() {
  const ids = select("m"), c = new Array(12).fill(0), bd = new Array(12).fill(0);
  for (const i of ids) { c[C.m[i]-1]++; bd[C.m[i]-1]+=C.los[i]; }
  const col = MONTHS.map((_,k) => (k+1>=state.from && k+1<=state.to) ? T.s1 : T.dim);
  draw("cMonth", [{type:"bar", x:MONTHS, y:c, marker:{color:col, cornerradius:4}, text:c.map(v=>v||""), textposition:"outside", cliponaxis:false,
    textfont:{color:T["ink-2"], size:11}, customdata:bd, hovertemplate:"<b>%{y} admissions</b><br>%{x} · %{customdata} bed-days<extra></extra>"}],
    layout("Admissions by month", 300, {yaxis:{gridcolor:T.grid, zeroline:false, tickfont:{color:T.muted}, fixedrange:true, rangemode:"tozero"}}),
    ev => { const m = ev.points[0].pointIndex+1; if (state.from===m && state.to===m) { state.from=1; state.to=12; } else { state.from=m; state.to=m; } syncUI(); render(); });
}
function chartWeekday(ids) {
  const c = countBy(ids, "wd", 7), los = losBy(ids, "wd", 7);
  const col = WEEKDAYS.map(w => w==="Fri"||w==="Sat" ? T.o1 : T.s1);
  draw("cWeekday", [{type:"bar", x:WEEKDAYS, y:c, marker:{color:col, cornerradius:4}, text:c.map(v=>v||""), textposition:"outside", cliponaxis:false,
    textfont:{color:T["ink-2"], size:11}, customdata:los.map(v=>fmt(v,1)), hovertemplate:"<b>%{y} admissions</b><br>%{x} · ALOS %{customdata} d<extra></extra>"}],
    layout("Admissions by weekday (Fri–Sat weekend lighter)", 300));
}
function chartCensus(ids) {
  const cen = census(ids).slice(1, 366);
  const dates = cen.map((_,k) => new Date(Date.UTC(2023,0,1+k)).toISOString().slice(0,10));
  const avg = sum(cen)/365, peak = Math.max(...cen), pk = cen.indexOf(peak);
  const roll = cen.map((_,k) => { const w = cen.slice(Math.max(0,k-6), k+1); return sum(w)/w.length; });
  draw("cCensus", [
    {type:"scatter", mode:"lines", x:dates, y:cen, name:"Nightly census", line:{color:T.o1, width:1, shape:"hv"}, hovertemplate:"%{x|%d %b}: <b>%{y} patients</b><extra></extra>"},
    {type:"scatter", mode:"lines", x:dates, y:roll, name:"7-day average", line:{color:T.s1, width:2}, hovertemplate:"7-day avg <b>%{y:.1f}</b><extra></extra>"},
  ], layout("Daily bed census (patients in hospital)", 300, {showlegend:true, hovermode:"x unified",
    xaxis:{gridcolor:T.grid, linecolor:T.axis, tickformat:"%b", dtick:"M1", tickfont:{color:T.muted}, fixedrange:true, showspikes:true, spikecolor:T.axis, spikethickness:1, spikedash:"solid"},
    shapes:[refLine(avg,"y")],
    annotations:[{x:dates[pk], y:peak, text:`Peak ${peak} (${dates[pk].slice(5)})`, showarrow:true, arrowhead:0, ax:30, ay:-18, font:{color:T.ink, size:11}},
                 {xref:"paper", x:1, y:avg, text:`avg ${avg.toFixed(1)}`, showarrow:false, yshift:9, xanchor:"right", font:{color:T.ink, size:11}}]}));
}
function chartStayShare(ids) {
  const bands = ["1-3 d","4-7 d","8-14 d","15+ d"], lim = [[1,3],[4,7],[8,14],[15,999]];
  const n = ids.length, bd = sum(ids.map(i=>C.los[i]));
  const a = lim.map(([lo,hi]) => ids.filter(i=>C.los[i]>=lo&&C.los[i]<=hi).length/(n||1));
  const b = lim.map(([lo,hi]) => sum(ids.filter(i=>C.los[i]>=lo&&C.los[i]<=hi).map(i=>C.los[i]))/(bd||1));
  const tr = (y,name,col) => ({type:"bar", x:bands, y, name, marker:{color:col, cornerradius:3}, text:y.map(v=>(v*100).toFixed(0)+"%"),
    textposition:"outside", cliponaxis:false, textfont:{size:10.5, color:T["ink-2"]}, hovertemplate:`${name}: <b>%{y:.0%}</b><extra>%{x}</extra>`});
  draw("cStayShare", [tr(a,"% of admissions",T.s1), tr(b,"% of bed-days",T.s2)],
    layout("Admissions vs bed-days by stay length", 300, {showlegend:true, barmode:"group", bargroupgap:0.08,
      yaxis:{gridcolor:T.grid, tickformat:".0%", tickfont:{color:T.muted}, fixedrange:true, rangemode:"tozero"}}));
}
function hbar(id, title, labels, vals, opts) {
  const o = Object.assign({fmtv:v=>v, color:T.s1, sel:null, ref:null, key:null, hover:"", h:320, custom:null}, opts);
  const order = labels.map((_,k)=>k).reverse();                  // top = first label
  const data = [{type:"bar", orientation:"h", y:order.map(k=>labels[k]), x:order.map(k=>vals[k]),
    marker:{color:order.map(k => o.sel===null||o.sel===k ? o.color : T.dim), cornerradius:4},
    text:order.map(k => vals[k]===null ? "" : o.fmtv(vals[k])), textposition:"outside", cliponaxis:false, textfont:{size:10.5, color:T["ink-2"]},
    customdata:order.map(k => o.custom ? o.custom[k] : k), hovertemplate:o.hover}];
  const lay = layout(title, o.h, {margin:{t:48,l:10,r:34,b:30}, bargap:0.3,
    xaxis:{gridcolor:T.grid, zeroline:false, tickfont:{color:T.muted}, fixedrange:true, rangemode:"tozero"},
    yaxis:{tickfont:{color:T["ink-2"]}, automargin:true, fixedrange:true}});
  if (o.ref!==null) { lay.shapes=[refLine(o.ref,"x")];
    lay.title.text = `${title}<br><span style="font-size:11px;color:${T.muted}">vertical line = average ${o.ref.toFixed(1)} days</span>`;
    lay.margin.t = 58; }
  const k2 = o.key;
  draw(id, data, lay, k2 ? ev => { const idx = labels.indexOf(ev.points[0].y); toggle(k2, idx); } : null);
}
function chartDx() {
  const ids = select("dx"), c = countBy(ids, "dx", DX.length), los = losBy(ids, "dx", DX.length);
  hbar("cDx", "Admissions by diagnosis", DX, c, {sel:state.dx, key:"dx", custom:los.map(v=>fmt(v,1)),
    hover:"<b>%{x} admissions</b><br>%{y} · ALOS %{customdata} d<extra></extra>"});
}
function chartDxLos() {
  const ids = select("dx"), los = losBy(ids, "dx", DX.length), c = countBy(ids, "dx", DX.length);
  hbar("cDxLos", "Average length of stay by diagnosis (days)", DX, los, {sel:state.dx, key:"dx", fmtv:v=>v.toFixed(1),
    ref:mean(ids.map(i=>C.los[i])), custom:c, hover:"<b>%{x:.1f} days</b><br>%{y} · n = %{customdata}<extra></extra>", color:T.s1});
}
function chartHeat(ids) {
  const z = DX.map(() => [0,0,0]), n = new Array(DX.length).fill(0);
  for (const i of ids) { z[C.dx[i]][C.sev[i]]++; n[C.dx[i]]++; }
  const zp = z.map((r,k) => r.map(v => n[k] ? v/n[k] : null));
  const rev = DX.map((_,k)=>k).reverse();
  draw("cHeat", [{type:"heatmap", x:SEV, y:rev.map(k=>DX[k]), z:rev.map(k=>zp[k]), zmin:0, zmax:0.8, xgap:2, ygap:2,
    colorscale:[[0,T.seq0],[0.35,T.seq1],[0.7,T.seq2],[1,T.seq3]], showscale:false,
    text:rev.map(k=>zp[k].map(v=>v===null?"":Math.round(v*100)+"%")), texttemplate:"%{text}", textfont:{size:10.5},
    customdata:rev.map(k=>z[k]), hovertemplate:"%{y} · %{x}: <b>%{text}</b> (%{customdata} patients)<extra></extra>"}],
    layout("Severity mix within each diagnosis", 320, {margin:{t:48,l:10,r:10,b:30},
      xaxis:{side:"bottom", tickfont:{color:T["ink-2"]}, fixedrange:true}, yaxis:{tickfont:{color:T["ink-2"]}, automargin:true, fixedrange:true}}));
}
function chartLosDist(ids) {
  const mx = 30, c = new Array(mx).fill(0); for (const i of ids) c[C.los[i]-1]++;
  const x = c.map((_,k)=>k+1);
  draw("cLosDist", [{type:"bar", x, y:c, marker:{color:x.map(v=>v>7?T.s2:T.s1), cornerradius:2}, hovertemplate:"%{x} days: <b>%{y} patients</b><extra></extra>"}],
    layout("Length-of-stay distribution", 300, {bargap:0.15,
      xaxis:{title:{text:"days in hospital", font:{size:11, color:T.muted}}, tickfont:{color:T.muted}, dtick:5, fixedrange:true, linecolor:T.axis},
      shapes:[{type:"line", x0:7.5, x1:7.5, yref:"paper", y0:0, y1:1, line:{color:T.ink, width:1}}],
      annotations:[{x:7.5, yref:"paper", y:1, text:"7-day long-stay line", showarrow:false, xanchor:"left", xshift:4, font:{size:10.5, color:T.ink}}]}));
}
function ordinalBars(id, title, labels, key, n) {
  const ids = select(key), los = losBy(ids, key, n), c = countBy(ids, key, n);
  const ramp = [T.o1, T.o2, T.o3, T.o4].slice(4-n);
  const ticks = labels.map(l => l.replace(" (", "<br>(").replace("Middle age", "Middle age"));
  draw(id, [{type:"bar", x:ticks, y:los, marker:{color:labels.map((_,k)=> state[key]===null||state[key]===k ? ramp[k] : T.dim), cornerradius:4},
    text:los.map((v,k)=> v===null ? "" : `${v.toFixed(1)} d`), textposition:"outside", cliponaxis:false, textfont:{size:11, color:T["ink-2"]},
    customdata:c, hovertemplate:"%{x}: <b>%{y:.1f} days</b> · n = %{customdata}<extra></extra>"}],
    layout(title, 300, {yaxis:{gridcolor:T.grid, tickfont:{color:T.muted}, fixedrange:true, rangemode:"tozero", title:{text:"avg days", font:{size:11, color:T.muted}}}}),
    ev => toggle(key, ev.points[0].pointIndex));
}
function chartDoc() {
  const ids = select("doc"), los = losBy(ids, "doc", DOC.length), c = countBy(ids, "doc", DOC.length);
  hbar("cDoc", "Average length of stay by doctor (days)", DOC, los, {sel:state.doc, key:"doc", fmtv:v=>v.toFixed(1),
    ref:mean(ids.map(i=>C.los[i])), custom:c, hover:"<b>%{x:.1f} days</b><br>%{y} · %{customdata} patients<extra></extra>", h:300});
}
function tableDoc() {
  const ids = select("doc"), tot = ids.length, bdTot = sum(ids.map(i=>C.los[i]));
  const rows = DOC.map((name,k) => {
    const d = ids.filter(i=>C.doc[i]===k), bd = sum(d.map(i=>C.los[i]));
    return {k, name, n:d.length, share:tot?d.length/tot:0, alos:mean(d.map(i=>C.los[i])), bd, bdShare:bdTot?bd/bdTot:0,
      long:d.length?d.filter(i=>C.los[i]>7).length/d.length:null, high:d.length?d.filter(i=>C.sev[i]===2).length/d.length:null,
      flags:d.filter(i=>C.rf[i]>0).length};
  });
  const mx = Math.max(1, ...rows.map(r=>r.n));
  let h = `<table><thead><tr><th>Doctor</th><th class="n">Admissions</th><th class="n">% adm.</th><th class="n">% bed-days</th><th class="n">ALOS</th>
           <th class="n">Long-stay</th><th class="n">High severity</th><th class="n">Review flags</th></tr></thead><tbody>`;
  for (const r of rows) {
    const gap = r.bdShare - r.share;
    h += `<tr class="${state.doc===r.k?"sel":""}"><td>${esc(r.name)}</td>
      <td class="n"><span class="bar" style="width:${Math.round(60*r.n/mx)}px"></span>${r.n}</td><td class="n">${pctS(r.share)}</td>
      <td class="n">${pctS(r.bdShare)} <span style="color:var(--${gap>0.01?"bad":gap<-0.01?"good":"muted"})">${gap>0.01?"▲":gap<-0.01?"▼":""}</span></td>
      <td class="n">${fmt(r.alos,1)}</td><td class="n">${pctS(r.long)}</td><td class="n">${pctS(r.high)}</td><td class="n">${r.flags}</td></tr>`;
  }
  document.getElementById("tDoc").innerHTML = h + "</tbody></table>";
}
function chartIns() {
  const ids = select("ins"), c = countBy(ids, "ins", 3), los = losBy(ids, "ins", 3), n = ids.length || 1;
  hbar("cIns", "Admissions by insurance", INS, c, {sel:state.ins, key:"ins", h:300, fmtv:v=>`${v} (${Math.round(v/n*100)}%)`,
    custom:los.map(v=>fmt(v,1)), hover:"<b>%{x} admissions</b><br>%{y} · ALOS %{customdata} d<extra></extra>"});
}
function chartBillStatus(ids) {
  const c = countBy(ids, "bs", 3), n = ids.length || 1;
  const cols = [T.s1, T.neutral, T["neutral-2"]];
  draw("cBillStatus", BS.map((b,k) => ({type:"bar", orientation:"h", y:["Bills"], x:[c[k]/n], name:b, marker:{color:cols[k], line:{color:T.card, width:2}},
      text:[c[k] ? `${Math.round(c[k]/n*100)}%` : ""], textposition:"inside", insidetextanchor:"middle", textfont:{color:k===0?"#ffffff":T.ink, size:12},
      hovertemplate:`${b}: <b>${c[k]} bills</b> (%{x:.0%})<extra></extra>`})),
    layout("Billing data quality", 300, {barmode:"stack", showlegend:true, bargap:0.45, margin:{t:48,l:10,r:14,b:30},
      legend:{orientation:"h", y:0.08, yanchor:"top", x:0, xanchor:"left", traceorder:"normal", font:{color:T["ink-2"], size:11}},
      xaxis:{visible:false, range:[0,1], fixedrange:true}, yaxis:{visible:false, fixedrange:true},
      annotations:[{xref:"paper", yref:"paper", x:0, y:0.9, xanchor:"left", showarrow:false, align:"left", font:{size:11.5, color:T.ink},
        text:`<b>${c[0]}</b> of ${ids.length} admissions have a genuine bill`}]}));
}
function chartBillLos(ids) {
  const r = ids.filter(i=>C.bill[i]!==null);
  const x = r.map(i=>C.los[i]), y = r.map(i=>C.bill[i]);
  const tr = [{type:"scatter", mode:"markers", x, y, marker:{color:T.s1, size:9, opacity:0.85, line:{color:T.card, width:2}},
    customdata:r.map(i=>[DX[C.dx[i]], C.id[i]]), hovertemplate:"%{customdata[1]} · %{customdata[0]}<br>%{x} days · <b>%{y:,}</b><extra></extra>", name:"Genuine bill"}];
  if (r.length >= 3) {
    const mx = mean(x), my = mean(y), sxx = sum(x.map(v=>(v-mx)**2));
    if (sxx > 0) { const b = sum(x.map((v,k)=>(v-mx)*(y[k]-my)))/sxx, a = my-b*mx, x0 = Math.min(...x), x1 = Math.max(...x);
      tr.push({type:"scatter", mode:"lines", x:[x0,x1], y:[a+b*x0, a+b*x1], line:{color:T.s2, width:2}, name:`Trend: +${Math.round(b).toLocaleString()} per day`, hoverinfo:"skip"}); }
  }
  draw("cBillLos", tr, layout("Genuine bill vs length of stay", 300, {showlegend:true, hovermode:"closest",
    xaxis:{title:{text:"days in hospital", font:{size:11, color:T.muted}}, gridcolor:T.grid, tickfont:{color:T.muted}, fixedrange:true, rangemode:"tozero"},
    yaxis:{gridcolor:T.grid, tickfont:{color:T.muted}, fixedrange:true, tickformat:",", rangemode:"tozero"}}));
}
function tableFlags(ids) {
  const r = ids.filter(i=>C.rf[i]>0).sort((p,q)=>C.los[q]-C.los[p]);
  if (!r.length) { document.getElementById("tFlags").innerHTML = '<p class="note" style="padding:10px">No flagged records in this filter.</p>'; return; }
  const d0 = Date.UTC(2023,0,1), ds = t => new Date(d0 + t*864e5).toISOString().slice(0,10);
  let h = `<table><thead><tr><th>ID</th><th>Flag</th><th>Diagnosis</th><th class="n">Age</th><th class="n">Stay (d)</th><th>Severity</th>
           <th>Doctor</th><th>Admitted</th><th>Insurance</th></tr></thead><tbody>`;
  for (const i of r) h += `<tr><td>${esc(C.id[i])}</td><td>${esc(RF[C.rf[i]])}</td><td>${esc(DX[C.dx[i]])}</td><td class="n">${C.age[i]}</td>
     <td class="n">${C.los[i]}</td><td>${SEV[C.sev[i]]}</td><td>${esc(DOC[C.doc[i]])}</td><td>${ds(C.a[i])}</td><td>${INS[C.ins[i]]}</td></tr>`;
  document.getElementById("tFlags").innerHTML = `<p class="note" style="padding:8px 8px 0">${r.length} flagged record(s) in the current filter, longest stay first.</p>` + h + "</tbody></table>";
}
function downloadCsv() {
  const ids = select(null), d0 = Date.UTC(2023,0,1), ds = t => new Date(d0 + t*864e5).toISOString().slice(0,10);
  const head = ["Patient_ID","Patient_Name","Age","Age_Group","Gender","Diagnosis","Doctor","Admission_Date","Discharge_Date","Length_of_Stay","Insurance","Severity","Bill","Bill_Status","Review_Flag"];
  const q = v => { const s = v===null||v===undefined ? "" : String(v); return /[",\n]/.test(s) ? '"'+s.replace(/"/g,'""')+'"' : s; };
  const lines = [head.join(",")].concat(ids.map(i => [C.id[i],C.nm[i],C.age[i],AGE[C.ag[i]],GEN[C.g[i]],DX[C.dx[i]],DOC[C.doc[i]],ds(C.a[i]),ds(C.d[i]),
    C.los[i],INS[C.ins[i]],SEV[C.sev[i]],C.bill[i],BS[C.bs[i]],RF[C.rf[i]]].map(q).join(",")));
  const blob = new Blob(["﻿"+lines.join("\n")], {type:"text/csv;charset=utf-8"});
  const a = document.createElement("a"); a.href = URL.createObjectURL(blob); a.download = "hospital_filtered.csv"; a.click();
  setTimeout(() => URL.revokeObjectURL(a.href), 1000);
}

// ------------------------------------------------------------------ render
function render() {
  const ids = select(null);
  const filtered = ids.length !== N;
  renderChips();
  renderKPIs(measures(ids), filtered);
  chartMonth(); chartWeekday(ids); chartCensus(ids); chartStayShare(ids);
  chartDx(); chartDxLos(); chartHeat(ids); chartLosDist(ids);
  ordinalBars("cAge", "Average stay by age group", AGE, "ag", 4);
  ordinalBars("cSev", "Average stay by recorded severity", SEV, "sev", 3);
  chartDoc(); tableDoc(); chartIns(); chartBillStatus(ids); chartBillLos(ids); tableFlags(ids);
}
readTheme(); initFilters(); syncUI(); render();
</script>
</body>
</html>
"""


def main():
    df = pd.read_csv(IN_CSV, parse_dates=["Admission_Date", "Discharge_Date"])
    with open(IN_JSON, encoding="utf-8") as f:
        S = json.load(f)
    html = (TEMPLATE
            .replace("__PLOTLYJS__", get_plotlyjs())
            .replace("__DATA__", json.dumps(build_data(df), ensure_ascii=False))
            .replace("__INSIGHTS__", insights_html(S))
            .replace("__N__", str(len(df)))
            .replace("__RB__", str(S["kpi"]["recorded_bills"])))
    with open(OUT_HTML, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"wrote {OUT_HTML} ({len(html) / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
