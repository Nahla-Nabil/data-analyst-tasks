"""
Task 6 - Weather Analysis: interactive dashboard (Python builds ONE self-contained HTML file).

Reads  Cleaned_Weather.csv + analysis_summary.json
Writes Weather_Dashboard.html

How it works: the cleaned data (3,271 rows) is embedded as JSON together with Plotly.js, and a small script
re-aggregates every chart and KPI in the browser whenever a filter changes, so the filters are real
cross-filters (like Power BI slicers), not just chart toggles:
  * Year and Season drop-downs
  * click a bar in "Gust direction", "Wind rose" or "Calendar month" charts to filter by it (click again to clear)
  * every KPI card shows its change against the full record

No internet is needed to open the file. No BI tool is used - see Power_BI_Guide.md to rebuild it in Power BI.
"""

import json

import pandas as pd
from plotly.offline import get_plotlyjs

IN_CSV = "Cleaned_Weather.csv"
IN_JSON = "analysis_summary.json"
OUT_HTML = "Weather_Dashboard.html"

DIRS = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
SEASONS = ["Summer", "Autumn", "Winter", "Spring"]


def clean_list(series, cast=None):
    """list with JSON-safe None for missing values (json.dumps would emit invalid NaN)."""
    return [None if pd.isna(v) else (cast(v) if cast else v) for v in series.tolist()]


def build_data(df):
    at_list = sorted(df["AnomalyType"].fillna("").unique().tolist())
    dates = pd.to_datetime(df["Date"])
    cols = {
        "dt": df["Date"].tolist(),
        "t": ((dates - pd.Timestamp("1970-01-01")).dt.days).tolist(),
        "y": df["Year"].tolist(),
        "m": df["Month"].tolist(),
        "s": df["Season"].map({s: i for i, s in enumerate(SEASONS)}).tolist(),
        "mx": df["MaxTemp"].tolist(), "mn": df["MinTemp"].tolist(), "r": df["Rainfall"].tolist(),
        "h9": df["Humidity9am"].tolist(), "h3": df["Humidity3pm"].tolist(),
        "g": clean_list(df["WindGustSpeed"], int), "w9": df["WindSpeed9am"].tolist(), "w3": df["WindSpeed3pm"].tolist(),
        "gd": clean_list(df["WindGustDir"].map({d: i for i, d in enumerate(DIRS)}), int),
        "p9": df["Pressure9am"].tolist(), "p3": df["Pressure3pm"].tolist(),
        "su": df["Sunshine"].tolist(), "c3": clean_list(df["Cloud3pm"], int),
        "rd": df["IsRainDay"].tolist(), "rt": df["RainTomorrow_Flag"].tolist(),
        "mz": clean_list(df["MaxTemp_Z"]),
        "at": df["AnomalyType"].fillna("").map({a: i for i, a in enumerate(at_list)}).tolist(),
    }
    return {"cols": cols, "AT": at_list, "rainFence": None}


def insights_html(S):
    sea = {s: S["seasonal"]["max_t"][i] for i, s in enumerate(S["seasonal"]["Season"])}
    mon = S["monthly"]
    jan_i, jul_i = 0, 6
    rc = S["rain_category_days"]
    hb = S["rain_by_humidity_band"]
    bands = list(hb.keys())
    lo_band, hi_band = hb[bands[0]], hb[bands[-1]]
    wet_dirs = {d["WindGustDir"]: d for d in S["wettest_gust_dirs"]}
    dry_dirs = {d["WindGustDir"]: d for d in S["driest_gust_dirs"]}
    two = S["two_day_top"][0]
    d0 = pd.Timestamp(two["date"])
    two_lbl = f"{d0.day}&ndash;{(d0 + pd.Timedelta(days=1)).day} {d0:%b %Y}"
    items = [
        ("Temperature", f"A clear seasonal cycle: the average daily maximum runs from <b>{mon['max_t'][jul_i]:.1f}&deg;C in July</b> to "
                        f"<b>{mon['max_t'][jan_i]:.1f}&deg;C in January</b>; overnight minimums swing more (<b>{mon['min_t'][jul_i]:.1f}&deg;C to "
                        f"{mon['min_t'][jan_i]:.1f}&deg;C</b>). Summer averages {sea['Summer']:.1f}&deg;C against {sea['Winter']:.1f}&deg;C in winter."),
        ("Rainfall", f"Rain is frequent and spread evenly: <b>{S['rain_day_pct']}% of days</b> are rain days overall and 23&ndash;27% in every "
                     f"season, so there is no dry season. What varies is intensity: just <b>{S['heavy_plus_days_pct']}% of days</b> (&gt;25&nbsp;mm) "
                     f"delivered <b>{S['heavy_plus_mm_share_pct']}% of all rainfall</b>. Wettest by daily average: April and June; driest: September."),
        ("Wind", f"Gust direction is a strong rain signal; gust speed is not (rank correlation with rainfall {S['corr_rain_gust']:.2f}). Gusts from the S/SE sector (ESE&ndash;SW, {S['se_sector_share_pct']}% of days with a real reading) "
                 f"come with rain on <b>{S['se_sector_rain_day_pct']}% of days vs {S['other_sector_rain_day_pct']}%</b> for every other direction &mdash; "
                 f"{S['se_sector_share_of_rain_mm_pct']}% of all rain fell on those days. The most common single direction, W ({S['w_dir_share_pct']}% of days), is mostly dry "
                 f"({S['w_dir_rain_day_pct']}% rain days). Spring is the windiest season (<b>{S['gust_ge70_by_season']['Spring']} of {S['gust_ge70_days']}</b> gusts &ge;70&nbsp;km/h). "
                 f"<i>Gust data start {S['gust_valid_from'][:7]}; earlier values in the source were a constant placeholder and are excluded.</i>"),
        ("Humidity &amp; forecasting", f"3pm humidity is a strong warning sign for rain the next day: <b>{lo_band[1]}%</b> chance when humidity is under 40% "
                                        f"but <b>{hi_band[1]}%</b> at 85% or more. A one-line rule (humidity &ge;70% &rarr; rain tomorrow) is right "
                                        f"<b>{S['rule_hum70_accuracy_pct']}%</b> of the time, versus {S['persistence_accuracy_pct']}% for 'tomorrow = today' and "
                                        f"{S['always_dry_accuracy_pct']}% for always guessing dry. Pressure alone barely separates wet from dry days."),
        ("Unusual patterns", f"<b>{S['anomaly_days']} days ({S['anomaly_days'] / S['days'] * 100:.1f}%)</b> are statistical anomalies. The 45.8&deg;C day on 18 Jan 2013 is the most "
                             f"extreme temperature (z = {S['top_heat_z'][0]['z']:.1f} against January). The wettest event was {two_lbl}: <b>{two['mm']:.0f}&nbsp;mm in two days</b> "
                             f"with gusts to 87&nbsp;km/h. Days &ge;35&deg;C were rarer before 2013: {S['ge35_days_2009_2012']} in 2009&ndash;12 ({S['obs_days_2009_2012']:,} observed days) vs {S['ge35_days_2013_2016']} in 2013&ndash;16 ({S['obs_days_2013_2016']:,} days)."),
        ("Change over time", f"Month-matched, 2013&ndash;17 averaged about <b>+{S['max_temp_diff_month_matched']:.1f}&deg;C</b> hotter maximums than 2008&ndash;12, "
                             f"a step up around 2013 rather than a smooth trend. <b>Caution:</b> nine years cannot separate climate change from natural variability "
                             f"(one hot 2013 and a partial 2017 weigh heavily), so this is an observation about this record, not a climate conclusion."),
    ]
    return "".join(f'<div class="insight"><h3>{h}</h3><p>{p}</p></div>' for h, p in items)


TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Weather Patterns Dashboard</title>
<style>
  :root {
    --page:#eef4fb; --card:#ffffff; --border:#c7dcf0; --ink:#1c3d5a; --ink-soft:#4d6e8c; --deep:#123456;
    --blue:#2e75b6; --orange:#eb6834; --bad:#b5322f; --good:#1e7a4a;
  }
  * { box-sizing:border-box; }
  body { margin:0; background:var(--page); color:var(--ink); font-family:Arial,Helvetica,sans-serif; }
  .wrap { max-width:1320px; margin:0 auto; padding:20px 20px 30px; }
  h1 { margin:0 0 4px; font-size:1.55rem; color:var(--deep); }
  h2 { margin:26px 0 4px; font-size:1.1rem; color:var(--deep); }
  .sub { color:var(--ink-soft); font-size:.9rem; margin-bottom:12px; }
  .section-note { color:var(--ink-soft); font-size:.82rem; margin:0 0 8px 2px; }
  .notice { background:#fff; border:1px solid var(--border); border-left:4px solid var(--orange); border-radius:4px;
            padding:10px 14px; font-size:.85rem; line-height:1.5; margin-bottom:12px; }
  .filters { position:sticky; top:0; z-index:20; background:var(--page); padding:8px 0 10px; border-bottom:1px solid var(--border);
             display:flex; flex-wrap:wrap; gap:14px; align-items:center; margin-bottom:12px; }
  .filters label { font-size:.78rem; color:var(--ink-soft); display:flex; flex-direction:column; gap:3px; }
  select, button { font:inherit; font-size:.88rem; color:var(--ink); background:#fff; border:1px solid var(--border);
                   border-radius:4px; padding:6px 10px; }
  button { cursor:pointer; } button:hover { background:#e3edf7; }
  select:focus-visible, button:focus-visible { outline:2px solid var(--blue); outline-offset:1px; }
  .chips { display:flex; gap:8px; flex-wrap:wrap; align-items:center; font-size:.8rem; color:var(--ink-soft); }
  .chip { background:#e3edf7; border:1px solid var(--border); border-radius:999px; padding:3px 6px 3px 10px; color:var(--ink); }
  .chip button { border:none; background:none; padding:0 4px; font-size:.95rem; line-height:1; color:var(--ink-soft); }
  .kpis { display:grid; grid-template-columns:repeat(8,1fr); gap:10px; margin-bottom:6px; }
  .kpi { background:var(--card); border:1px solid var(--border); border-radius:6px; padding:12px 8px; text-align:center; }
  .kpi .l { font-size:.7rem; color:var(--ink-soft); margin-bottom:5px; min-height:1.9em; }
  .kpi .v { font-size:1.3rem; font-weight:bold; color:var(--deep); }
  .kpi .d { font-size:.7rem; margin-top:4px; color:var(--ink-soft); min-height:1em; }
  .insights { display:grid; grid-template-columns:repeat(3,1fr); gap:12px; }
  .insight { background:var(--card); border:1px solid var(--border); border-radius:6px; padding:10px 14px; }
  .insight h3 { margin:0 0 4px; font-size:.9rem; color:var(--blue); }
  .insight p { margin:0; font-size:.82rem; line-height:1.5; }
  .grid2 { display:grid; grid-template-columns:repeat(2,1fr); gap:12px; }
  .grid3 { display:grid; grid-template-columns:repeat(3,1fr); gap:12px; }
  .card { background:var(--card); border:1px solid var(--border); border-radius:6px; padding:6px 8px 2px; min-width:0; }
  .full { grid-column:1/-1; }
  table { border-collapse:collapse; width:100%; font-size:.82rem; }
  th { text-align:left; color:var(--ink-soft); font-weight:600; border-bottom:1px solid var(--border); padding:6px 8px; }
  td { border-bottom:1px solid #e3edf7; padding:5px 8px; }
  .tag { display:inline-block; background:#fbe9e2; color:#8a3512; border-radius:3px; padding:1px 6px; margin:0 3px 2px 0; font-size:.75rem; }
  footer { margin-top:20px; font-size:.78rem; color:var(--ink-soft); line-height:1.6; }
  .empty { padding:40px; text-align:center; color:var(--ink-soft); }
  @media (max-width:1000px) { .kpis { grid-template-columns:repeat(4,1fr); } .insights,.grid3 { grid-template-columns:1fr 1fr; } }
  @media (max-width:700px) { .kpis { grid-template-columns:repeat(2,1fr); } .insights,.grid2,.grid3 { grid-template-columns:1fr; } }
</style>
</head>
<body>
<div class="wrap">
  <h1>Weather Patterns Dashboard</h1>
  <div class="sub">Task 6 &mdash; daily weather record, 1 Feb 2008 &ndash; 25 Jun 2017 (3,271 days) &middot; Nahla Nabil, VOLTIX Data Analyst Internship</div>

  <div class="notice"><b>Scope note:</b> the dataset has <b>no city or country column</b> &mdash; it is a single unnamed (apparently Sydney, Australia) station,
    so this dashboard compares <b>time periods, seasons and wind directions</b>, not locations. Seasons are southern-hemisphere (Summer = Dec&ndash;Feb).
    Three whole months are missing from the source (__MISSING__) and 2008 / 2017 are partial years, so charts show gaps rather than zeros. Wind-gust readings before Oct 2010 and cloud cover for Dec 2010&ndash;Jun 2012 were constant placeholders in the source and are excluded (see DATA_QUALITY_REPORT.md).</div>

  <div class="filters">
    <label>Year<select id="fYear"></select></label>
    <label>Season<select id="fSeason"></select></label>
    <button id="btnReset" type="button">Reset filters</button>
    <div class="chips" id="chips"><span>Tip: click a wind direction or a month in the charts to filter by it.</span></div>
  </div>

  <div class="kpis" id="kpis"></div>

  <h2>Key insights (full record)</h2>
  <div class="insights">__INSIGHTS__</div>

  <h2>1. Temperature</h2>
  <p class="section-note">Box plots: box = middle 50% of days, line = median, dashed = mean. The heat map ignores the filters and always shows the full record (blank cell = no data that month).</p>
  <div class="grid2">
    <div class="card full"><div id="cTempTs"></div></div>
    <div class="card"><div id="cTempCal"></div></div>
    <div class="card"><div id="cTempBox"></div></div>
    <div class="card full"><div id="cHeat"></div></div>
  </div>

  <h2>2. Humidity</h2>
  <p class="section-note">Morning (9am) air is more humid than afternoon (3pm) in every month.</p>
  <div class="grid2">
    <div class="card"><div id="cHum"></div></div>
    <div class="card"><div id="cScatter"></div></div>
  </div>

  <h2>3. Wind</h2>
  <p class="section-note">Blue bars in the third chart are directions with more rain days than the overall average (dashed line). Click a petal or bar to filter the whole dashboard by gust direction.</p>
  <div class="grid3">
    <div class="card"><div id="cRose"></div></div>
    <div class="card"><div id="cWindMonth"></div></div>
    <div class="card"><div id="cRainByDir"></div></div>
  </div>

  <h2>4. Rainfall</h2>
  <p class="section-note">Months with missing days understate their total (Oct 2010, Aug 2012, Jun 2017); months with no data are left blank. The dashed line in the last chart is the overall chance of rain tomorrow.</p>
  <div class="grid2">
    <div class="card full"><div id="cRainTs"></div></div>
    <div class="card"><div id="cRainDays"></div></div>
    <div class="card"><div id="cRainClass"></div></div>
    <div class="card full"><div id="cRainHum"></div></div>
  </div>

  <h2>5. Unusual patterns &amp; events</h2>
  <p class="section-note">Anomalies: |z| &ge; 3 versus the same calendar month (temperature, humidity, gusts, pressure) or wet-day rainfall above the Tukey far-out fence (&gt; __FENCE__ mm).
     Red markers/bars are anomalies. 2008 and 2017 are partial years, and wind-gust anomalies can only exist from Oct 2010 (earlier gust values were placeholders), so early years show fewer flags.</p>
  <div class="grid2">
    <div class="card full"><div id="cTlTemp"></div></div>
    <div class="card full"><div id="cTlRain"></div></div>
    <div class="card full"><div id="cTlGust"></div></div>
    <div class="card"><div id="cAnomYear"></div></div>
    <div class="card"><div id="cCorr"></div></div>
    <div class="card full"><div id="anomTable"></div></div>
  </div>

  <footer>
    Weather_Dashboard.html &middot; built with Python (pandas + Plotly.js) from Cleaned_Weather.csv &middot; works offline.<br>
    Method: monthly / calendar-month averages use observed days only (nothing interpolated). Heat map anomalies = monthly mean minus the same calendar month's average over all years.
    Correlations are Spearman rank correlations (rainfall is heavily skewed). Rain day = rainfall &gt; 1 mm (the dataset's own definition).
  </footer>
</div>

<script>__PLOTLYJS__</script>
<script>
const DATA = __DATA__;
const C = DATA.cols, AT = DATA.AT, N = C.dt.length;
const MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
const SEASONS = ["Summer","Autumn","Winter","Spring"];
const DIRS = ["N","NNE","NE","ENE","E","ESE","SE","SSE","S","SSW","SW","WSW","W","WNW","NW","NNW"];
// colors: categorical slots (validated set) - entity keeps its color
const COL = {blue:"#2a78d6", orange:"#eb6834", aqua:"#1baf7a", yellow:"#eda100", bad:"#b5322f", grid:"#e3edf7",
             ink:"#1c3d5a", soft:"#4d6e8c", border:"#c7dcf0", brand:"#2e75b6", neutral:"#a9bccd"};
const SCOL = {Summer:COL.orange, Autumn:COL.yellow, Winter:COL.blue, Spring:COL.aqua};
const state = {year:"All", season:"All", dir:null, month:null};
const FONT = "Arial, Helvetica, sans-serif";

// ------------------------------------------------------------------ helpers
const pad = n => String(n).padStart(2,"0");
const fmt = (v,d=1) => (v===null||v===undefined||Number.isNaN(v)) ? "–" : Number(v).toFixed(d);
const sum = (a) => a.reduce((x,y)=>x+y,0);
const meanOf = (ids,k) => { let t=0,c=0; for (const i of ids) { const v=C[k][i]; if (v!==null && v!==undefined) { t+=v; c++; } } return c ? t/c : null; };
const pct = (num,den) => den ? num/den*100 : null;
function select(skip=[]) {
  const out=[];
  for (let i=0;i<N;i++) {
    if (state.year!=="All" && C.y[i]!==+state.year) continue;
    if (state.season!=="All" && SEASONS[C.s[i]]!==state.season) continue;
    if (!skip.includes("dir") && state.dir!==null && C.gd[i]!==state.dir) continue;
    if (!skip.includes("month") && state.month!==null && C.m[i]!==state.month) continue;
    out.push(i);
  }
  return out;
}
function groupIdx(ids, keyFn) {
  const g = new Map();
  for (const i of ids) { const k = keyFn(i); if (!g.has(k)) g.set(k, []); g.get(k).push(i); }
  return g;
}
function baseLayout(title, h=340, extra={}) {
  return Object.assign({
    title:{text:title, font:{size:13.5, color:COL.ink}, x:0.01, xanchor:"left"},
    paper_bgcolor:"#fff", plot_bgcolor:"#fff", height:h,
    font:{family:FONT, color:COL.ink, size:12},
    margin:{t:64,l:52,r:16,b:42},
    hoverlabel:{bgcolor:"#fff", bordercolor:COL.border, font:{family:FONT, color:COL.ink}},
    xaxis:{gridcolor:COL.grid, linecolor:COL.border, tickfont:{color:COL.soft}, zeroline:false},
    yaxis:{gridcolor:COL.grid, linecolor:COL.border, tickfont:{color:COL.soft}, zeroline:false},
    legend:{orientation:"h", y:1.01, yanchor:"bottom", x:0, xanchor:"left", font:{color:COL.soft}},
  }, extra);
}
const clickWired = {};
function draw(id, data, layout, onClick) {
  Plotly.react(id, data, layout, {responsive:true, displaylogo:false, displayModeBar:"hover"});
  if (onClick && !clickWired[id]) { document.getElementById(id).on("plotly_click", onClick); clickWired[id]=true; }
}
function emptyMsg(id, title, msg) {
  try { Plotly.purge(id); } catch(e) {}
  clickWired[id] = false;
  Plotly.react(id, [], baseLayout(title, 200, {annotations:[{text:msg||"No data for this filter combination", showarrow:false,
    font:{color:COL.soft, size:13}, xref:"paper", yref:"paper", x:.5, y:.5}], xaxis:{visible:false}, yaxis:{visible:false}}),
    {displaylogo:false});
}
const ALL = Array.from({length:N}, (_,i)=>i);
// month keys across the whole record (so gaps show as gaps)
const ymAll = []; { let y=C.y[0], m=C.m[0]; const ye=C.y[N-1], me=C.m[N-1];
  while (y<ye || (y===ye && m<=me)) { ymAll.push([y,m]); m++; if (m>12){m=1;y++;} } }
const ymKey = (y,m)=>y*100+m;
const ymDate = ([y,m]) => `${y}-${pad(m)}-01`;
const BASE = {  // full-record baselines for KPI deltas
  mx:meanOf(ALL,"mx"), mn:meanOf(ALL,"mn"), h3:meanOf(ALL,"h3"), g:meanOf(ALL,"g"),
  rainDay:pct(sum(ALL.map(i=>C.rd[i])),N), hot:pct(ALL.filter(i=>C.mx[i]>=30).length,N),
  rainMean:meanOf(ALL,"r"), anom:pct(ALL.filter(i=>AT[C.at[i]]!=="").length,N)
};

// ------------------------------------------------------------------ filters UI
function initFilters() {
  const yrs = ["All", ...Array.from(new Set(C.y)).sort()];
  document.getElementById("fYear").innerHTML = yrs.map(y=>`<option>${y}</option>`).join("");
  document.getElementById("fSeason").innerHTML = ["All",...SEASONS].map(s=>`<option>${s}</option>`).join("");
  document.getElementById("fYear").onchange = e => { state.year=e.target.value; render(); };
  document.getElementById("fSeason").onchange = e => { state.season=e.target.value; render(); };
  document.getElementById("btnReset").onclick = () => { state.year="All"; state.season="All"; state.dir=null; state.month=null; syncUI(); render(); };
}
function syncUI() {
  document.getElementById("fYear").value = state.year;
  document.getElementById("fSeason").value = state.season;
}
function renderChips() {
  const chips=[];
  if (state.year!=="All") chips.push(["Year "+state.year,()=>{state.year="All";}]);
  if (state.season!=="All") chips.push([state.season,()=>{state.season="All";}]);
  if (state.dir!==null) chips.push(["Gusts from "+DIRS[state.dir],()=>{state.dir=null;}]);
  if (state.month!==null) chips.push([MONTHS[state.month-1],()=>{state.month=null;}]);
  const el = document.getElementById("chips");
  if (!chips.length) { el.innerHTML = "<span>Tip: click a wind direction or a month in the charts to filter by it.</span>"; return; }
  el.innerHTML = "<span>Active filters:</span>";
  chips.forEach(([txt,fn])=>{
    const s=document.createElement("span"); s.className="chip"; s.textContent=txt+" ";
    const b=document.createElement("button"); b.type="button"; b.textContent="×"; b.setAttribute("aria-label","Remove filter "+txt);
    b.onclick=()=>{fn(); syncUI(); render();}; s.appendChild(b); el.appendChild(s);
  });
}

// ------------------------------------------------------------------ KPIs
function renderKPIs(ids) {
  const n = ids.length;
  const rainDays = ids.filter(i=>C.rd[i]===1).length;
  const tot = sum(ids.map(i=>C.r[i]));
  const hot = ids.filter(i=>C.mx[i]>=30).length;
  const hot35 = ids.filter(i=>C.mx[i]>=35).length;
  const anom = ids.filter(i=>AT[C.at[i]]!=="").length;
  const cards = [
    ["Avg max temp", n?fmt(meanOf(ids,"mx"))+"°C":"–", n?dlt(meanOf(ids,"mx"),BASE.mx,"°C"):""],
    ["Avg min temp", n?fmt(meanOf(ids,"mn"))+"°C":"–", n?dlt(meanOf(ids,"mn"),BASE.mn,"°C"):""],
    ["Avg humidity (3pm)", n?fmt(meanOf(ids,"h3"),0)+"%":"–", n?dlt(meanOf(ids,"h3"),BASE.h3,"pts",0):""],
    ["Avg wind gust", meanOf(ids,"g")===null?"–":fmt(meanOf(ids,"g"))+" km/h", meanOf(ids,"g")===null?"no gust readings before Oct 2010":dlt(meanOf(ids,"g"),BASE.g," km/h")],
    ["Total rainfall", n?Math.round(tot).toLocaleString()+" mm":"–", n?`${fmt(tot/n,2)} mm/day (all: ${fmt(BASE.rainMean,2)})`:""],
    ["Rain days (>1 mm)", n?fmt(pct(rainDays,n))+"%":"–", n?dlt(pct(rainDays,n),BASE.rainDay,"pts"):""],
    ["Hot days ≥30°C", n?hot.toLocaleString():"–", n?`${hot35} at ≥35°C · ${fmt(pct(hot,n))}% of days`:""],
    ["Anomalous days", n?anom.toLocaleString():"–", n?`${fmt(pct(anom,n))}% (all: ${fmt(BASE.anom)}%)`:""],
  ];
  document.getElementById("kpis").innerHTML = cards.map(([l,v,d])=>`<div class="kpi"><div class="l">${l}</div><div class="v">${v}</div><div class="d">${d}</div></div>`).join("");
  document.getElementById("kpis").insertAdjacentHTML("beforeend","");
}
function dlt(v,base,unit,dec=1) {
  if (v===null || v===undefined) return "";
  const d = +(v-base).toFixed(dec);
  if (d===0) return "same as full record";
  return `${d>0?"+":"−"}${Math.abs(d).toFixed(dec)}${unit.startsWith("pts")?" ":""}${unit} vs full record`;
}

// ------------------------------------------------------------------ chart builders
function monthlySeries(ids, valFn) {
  const g = groupIdx(ids, i=>ymKey(C.y[i],C.m[i]));
  return ymAll.map(p => { const a=g.get(ymKey(...p)); return a? valFn(a) : null; });
}
function chartTempTs(ids) {
  const x = ymAll.map(ymDate);
  const mx = monthlySeries(ids, a=>meanOf(a,"mx")), mn = monthlySeries(ids, a=>meanOf(a,"mn"));
  draw("cTempTs", [
    {x, y:mn, name:"Avg min", type:"scatter", mode:"lines+markers", connectgaps:false, line:{color:COL.blue,width:2}, marker:{size:5},
      hovertemplate:"%{x|%b %Y}<br>Avg min: %{y:.1f}°C<extra></extra>"},
    {x, y:mx, name:"Avg max", type:"scatter", mode:"lines+markers", connectgaps:false, line:{color:COL.orange,width:2}, marker:{size:5},
      hovertemplate:"%{x|%b %Y}<br>Avg max: %{y:.1f}°C<extra></extra>"},
  ], baseLayout("Monthly average max / min temperature (gaps = months with no data)", 330,
    {yaxis:{ticksuffix:"°C", gridcolor:COL.grid, linecolor:COL.border, tickfont:{color:COL.soft}, zeroline:false}}));
}
function chartTempCal() {
  const ids = select(["month"]);
  const g = groupIdx(ids, i=>C.m[i]);
  const mx = MONTHS.map((_,k)=>{const a=g.get(k+1); return a?meanOf(a,"mx"):null;});
  const mn = MONTHS.map((_,k)=>{const a=g.get(k+1); return a?meanOf(a,"mn"):null;});
  const op = MONTHS.map((_,k)=> state.month===null||state.month===k+1 ? 1 : 0.35);
  draw("cTempCal", [
    {x:MONTHS, y:mn, name:"Avg min", type:"bar", marker:{color:COL.blue, opacity:op, cornerradius:3}, hovertemplate:"%{x}<br>Avg min: %{y:.1f}°C<extra></extra>"},
    {x:MONTHS, y:mx, name:"Avg max", type:"bar", marker:{color:COL.orange, opacity:op, cornerradius:3}, hovertemplate:"%{x}<br>Avg max: %{y:.1f}°C<extra></extra>"},
  ], baseLayout("Seasonal cycle by month (click to filter)", 340,
    {barmode:"group", bargap:.25, bargroupgap:.06, yaxis:{ticksuffix:"°C", gridcolor:COL.grid, linecolor:COL.border, tickfont:{color:COL.soft}, zeroline:false}}),
    ev => { const m = MONTHS.indexOf(ev.points[0].x)+1; state.month = state.month===m?null:m; render(); });
}
function chartTempBox(ids) {
  const g = groupIdx(ids, i=>C.s[i]);
  const traces = SEASONS.filter((s,k)=>g.has(k)).map(s=>({
    y:g.get(SEASONS.indexOf(s)).map(i=>C.mx[i]), name:s, type:"box", marker:{color:SCOL[s], size:4}, line:{color:SCOL[s], width:1.6},
    fillcolor:SCOL[s]+"33", boxmean:true, hovertemplate:"%{y}°C<extra>"+s+"</extra>"}));
  if (!traces.length) return emptyMsg("cTempBox","Daily max temperature by season");
  draw("cTempBox", traces, baseLayout("Daily max temperature by season", 340,
    {showlegend:false, yaxis:{ticksuffix:"°C", gridcolor:COL.grid, linecolor:COL.border, tickfont:{color:COL.soft}, zeroline:false}}));
}
function chartHeat() {
  // full-record heat map, independent of filters
  const years = Array.from(new Set(C.y)).sort();
  const mMean = MONTHS.map((_,k)=>meanOf(ALL.filter(i=>C.m[i]===k+1),"mx"));
  const z = years.map(y => MONTHS.map((_,k)=>{
    const a = ALL.filter(i=>C.y[i]===y && C.m[i]===k+1); return a.length ? +(meanOf(a,"mx")-mMean[k]).toFixed(2) : null; }));
  const cnt = years.map(y => MONTHS.map((_,k)=>ALL.filter(i=>C.y[i]===y && C.m[i]===k+1).length));
  draw("cHeat", [{type:"heatmap", z, x:MONTHS, y:years.map(String), zmid:0, zmin:-3, zmax:3, xgap:2, ygap:2,
    colorscale:[[0,COL.blue],[0.5,"#f1f0ee"],[1,COL.orange]], customdata:cnt,
    text:z.map(r=>r.map(v=>v===null?"":(v>0?"+":"")+v.toFixed(1))), texttemplate:"%{text}", textfont:{size:10.5, color:COL.ink},
    hovertemplate:"%{y} %{x}<br>Max-temp anomaly: %{z:+.2f}°C<br>%{customdata} days observed<extra></extra>",
    colorbar:{title:{text:"°C vs avg", side:"right"}, thickness:12, len:.9}}],
    baseLayout("Max-temperature anomaly by month and year (°C vs that month's overall average)", 380,
      {margin:{t:50,l:52,r:16,b:36}, yaxis:{autorange:"reversed", type:"category", tickfont:{color:COL.soft}, linecolor:COL.border},
       xaxis:{type:"category", tickfont:{color:COL.soft}, linecolor:COL.border}}));
}
function chartHum() {
  const ids = select(["month"]);
  const g = groupIdx(ids, i=>C.m[i]);
  const h9 = MONTHS.map((_,k)=>{const a=g.get(k+1); return a?meanOf(a,"h9"):null;});
  const h3 = MONTHS.map((_,k)=>{const a=g.get(k+1); return a?meanOf(a,"h3"):null;});
  const op = MONTHS.map((_,k)=> state.month===null||state.month===k+1 ? 1 : 0.35);
  draw("cHum", [
    {x:MONTHS, y:h9, name:"9am", type:"bar", marker:{color:COL.blue, opacity:op, cornerradius:3}, hovertemplate:"%{x}<br>9am humidity: %{y:.0f}%<extra></extra>"},
    {x:MONTHS, y:h3, name:"3pm", type:"bar", marker:{color:COL.aqua, opacity:op, cornerradius:3}, hovertemplate:"%{x}<br>3pm humidity: %{y:.0f}%<extra></extra>"},
  ], baseLayout("Average humidity by month", 340,
    {barmode:"group", bargap:.25, bargroupgap:.06, yaxis:{range:[0,100], ticksuffix:"%", gridcolor:COL.grid, linecolor:COL.border, tickfont:{color:COL.soft}, zeroline:false}}),
    ev => { const m = MONTHS.indexOf(ev.points[0].x)+1; state.month = state.month===m?null:m; render(); });
}
function chartScatter(ids) {
  const wet = ids.filter(i=>C.rd[i]===1), dry = ids.filter(i=>C.rd[i]===0);
  const mk = (a, name, color) => ({type:"scattergl", mode:"markers", name, x:a.map(i=>C.mx[i]), y:a.map(i=>C.h3[i]),
    marker:{color, size:5, opacity:.55}, customdata:a.map(i=>[C.dt[i], C.r[i]]),
    hovertemplate:"%{customdata[0]}<br>Max temp %{x}°C · humidity %{y}%<br>Rain: %{customdata[1]} mm<extra>"+name+"</extra>"});
  draw("cScatter", [mk(dry,"Dry day",COL.orange), mk(wet,"Rain day",COL.blue)],
    baseLayout("3pm humidity vs max temperature (1 dot = 1 day)", 340,
      {xaxis:{title:{text:"Max temperature (°C)"}, gridcolor:COL.grid, linecolor:COL.border, tickfont:{color:COL.soft}, zeroline:false},
       yaxis:{title:{text:"3pm humidity (%)"}, gridcolor:COL.grid, linecolor:COL.border, tickfont:{color:COL.soft}, zeroline:false}}));
}
function chartRose() {
  const ids = select(["dir"]).filter(i=>C.gd[i]!==null);
  const total = ids.length;
  if (!total) return emptyMsg("cRose","Wind rose: peak-gust direction (click)","No gust readings in this selection (gust data start Oct 2010)");
  const g = groupIdx(ids, i=>C.gd[i]);
  const r = DIRS.map((_,k)=>{const a=g.get(k); return a? a.length/total*100 : 0;});
  const cd = DIRS.map((_,k)=>{const a=g.get(k)||[]; return [a.length, meanOf(a,"g"), pct(a.filter(i=>C.rd[i]===1).length,a.length)];});
  const colors = DIRS.map((_,k)=> state.dir===null||state.dir===k ? COL.brand : COL.neutral);
  draw("cRose", [{type:"barpolar", theta:DIRS, r, customdata:cd, marker:{color:colors, line:{color:"#fff", width:1}},
    hovertemplate:"Gusts from %{theta}<br>%{r:.1f}% of days (%{customdata[0]} days)<br>Mean gust %{customdata[1]:.0f} km/h<br>Rain days: %{customdata[2]:.0f}%<extra></extra>"}],
    baseLayout("Wind rose: peak-gust direction (click)", 340, {
      margin:{t:50,l:40,r:40,b:30},
      polar:{bgcolor:"#fff", angularaxis:{direction:"clockwise", rotation:90, categoryarray:DIRS, type:"category", tickfont:{size:10.5,color:COL.soft}, gridcolor:COL.grid, linecolor:COL.border},
             radialaxis:{ticksuffix:"%", tickfont:{size:9.5,color:COL.soft}, gridcolor:COL.grid, linecolor:COL.border, angle:90}}, showlegend:false}),
    ev => { const k = DIRS.indexOf(ev.points[0].theta); state.dir = state.dir===k?null:k; render(); });
}
function chartWindMonth() {
  const ids = select(["month"]);
  const g = groupIdx(ids, i=>C.m[i]);
  const line = (key,name,color,dash) => ({x:MONTHS, y:MONTHS.map((_,k)=>{const a=g.get(k+1); return a?meanOf(a,key):null;}), name, type:"scatter", mode:"lines+markers",
    line:{color, width:2, dash}, marker:{size:6}, hovertemplate:"%{x}<br>"+name+": %{y:.1f} km/h<extra></extra>"});
  draw("cWindMonth", [line("g","Peak gust",COL.orange), line("w3","3pm wind",COL.blue), line("w9","9am wind",COL.aqua,"dot")],
    baseLayout("Wind speed by month (km/h)", 340, {yaxis:{rangemode:"tozero", gridcolor:COL.grid, linecolor:COL.border, tickfont:{color:COL.soft}, zeroline:false}}));
}
function chartRainByDir() {
  const ids = select(["dir"]).filter(i=>C.gd[i]!==null);
  if (!ids.length) return emptyMsg("cRainByDir","Rain days by gust direction (click)","No gust readings in this selection (gust data start Oct 2010)");
  const g = groupIdx(ids, i=>C.gd[i]);
  const overall = pct(ids.filter(i=>C.rd[i]===1).length, ids.length);
  const rows = DIRS.map((d,k)=>{const a=g.get(k)||[]; return {d,k,n:a.length,v:pct(a.filter(i=>C.rd[i]===1).length,a.length)};})
    .filter(o=>o.n>0).sort((a,b)=>b.v-a.v);
  draw("cRainByDir", [{type:"bar", orientation:"h", y:rows.map(o=>o.d), x:rows.map(o=>o.v), customdata:rows.map(o=>o.n),
    marker:{color:rows.map(o=> state.dir===null||state.dir===o.k ? (o.v>overall?COL.blue:COL.neutral) : "#d5dfe9"), cornerradius:3},
    hovertemplate:"Gusts from %{y}<br>Rain on %{x:.0f}% of these days (n=%{customdata})<extra></extra>"}],
    baseLayout("Rain days by gust direction (click)", 340, {
      margin:{t:50,l:44,r:16,b:40}, showlegend:false,
      xaxis:{ticksuffix:"%", gridcolor:COL.grid, linecolor:COL.border, tickfont:{color:COL.soft}, zeroline:false},
      yaxis:{autorange:"reversed", type:"category", tickfont:{color:COL.soft, size:11}, linecolor:COL.border},
      shapes:[{type:"line", x0:overall, x1:overall, y0:0, y1:1, yref:"paper", line:{color:COL.ink, width:1.2, dash:"dash"}}],
      annotations:[{x:overall, y:1.0, yref:"paper", text:`avg ${overall===null?"–":overall.toFixed(0)}%`, showarrow:false, yanchor:"bottom", font:{size:10.5,color:COL.soft}}]}),
    ev => { const k = DIRS.indexOf(ev.points[0].y); state.dir = state.dir===k?null:k; render(); });
}
function chartRainTs(ids) {
  const g = groupIdx(ids, i=>ymKey(C.y[i],C.m[i]));
  const x=[],y=[],cd=[];
  ymAll.forEach(p=>{const a=g.get(ymKey(...p)); if(a){x.push(ymDate(p)); y.push(+sum(a.map(i=>C.r[i])).toFixed(1)); cd.push(a.length);}});
  draw("cRainTs", [{type:"bar", x, y, customdata:cd, marker:{color:COL.blue, cornerradius:2},
    hovertemplate:"%{x|%b %Y}<br>Total: %{y} mm<br>%{customdata} days observed<extra></extra>"}],
    baseLayout("Monthly rainfall total (mm)", 320,
      {showlegend:false, yaxis:{ticksuffix:" mm", gridcolor:COL.grid, linecolor:COL.border, tickfont:{color:COL.soft}, zeroline:false}}));
}
function chartRainDays() {
  const ids = select(["month"]);
  const g = groupIdx(ids, i=>C.m[i]);
  const v = MONTHS.map((_,k)=>{const a=g.get(k+1); return a?pct(a.filter(i=>C.rd[i]===1).length,a.length):null;});
  const n = MONTHS.map((_,k)=>(g.get(k+1)||[]).length);
  const op = MONTHS.map((_,k)=> state.month===null||state.month===k+1 ? 1 : 0.35);
  draw("cRainDays", [{type:"bar", x:MONTHS, y:v, customdata:n, marker:{color:COL.blue, opacity:op, cornerradius:3},
    hovertemplate:"%{x}<br>Rain on %{y:.0f}% of days (n=%{customdata})<extra></extra>"}],
    baseLayout("Rain days by month (click to filter)", 320,
      {showlegend:false, yaxis:{ticksuffix:"%", rangemode:"tozero", gridcolor:COL.grid, linecolor:COL.border, tickfont:{color:COL.soft}, zeroline:false}}),
    ev => { const m = MONTHS.indexOf(ev.points[0].x)+1; state.month = state.month===m?null:m; render(); });
}
function chartRainClass(ids) {
  const cls = [["Dry (≤1 mm)",r=>r<=1],["Light (1–10)",r=>r>1&&r<=10],["Moderate (10–25)",r=>r>10&&r<=25],["Heavy (25–50)",r=>r>25&&r<=50],["Very heavy (>50)",r=>r>50]];
  const totalMm = sum(ids.map(i=>C.r[i])) || 1, n = ids.length || 1;
  const d = cls.map(([_,f])=>ids.filter(i=>f(C.r[i])).length/n*100);
  const m = cls.map(([_,f])=>sum(ids.filter(i=>f(C.r[i])).map(i=>C.r[i]))/totalMm*100);
  const lbl = cls.map(c=>c[0]);
  draw("cRainClass", [
    {type:"bar", x:lbl, y:d, name:"% of days", marker:{color:COL.neutral, cornerradius:3}, hovertemplate:"%{x}<br>%{y:.1f}% of days<extra></extra>"},
    {type:"bar", x:lbl, y:m, name:"% of total rainfall", marker:{color:COL.blue, cornerradius:3}, hovertemplate:"%{x}<br>%{y:.1f}% of all rainfall<extra></extra>"},
  ], baseLayout("Rain intensity: share of days vs share of rain", 320,
    {barmode:"group", bargap:.25, bargroupgap:.06, yaxis:{ticksuffix:"%", gridcolor:COL.grid, linecolor:COL.border, tickfont:{color:COL.soft}, zeroline:false}}));
}
function chartRainHum(ids) {
  const bands = [[0,40],[40,55],[55,70],[70,85],[85,101]];
  const lab = ["< 40%","40–55%","55–70%","70–85%","≥ 85%"];
  const vals = bands.map(([lo,hi])=>{const a=ids.filter(i=>C.h3[i]>=lo&&C.h3[i]<hi); return {n:a.length, t:a.length?pct(a.filter(i=>C.rt[i]===1).length,a.length):null, d:a.length?pct(a.filter(i=>C.rd[i]===1).length,a.length):null};});
  const base = ids.length ? pct(ids.filter(i=>C.rt[i]===1).length, ids.length) : null;
  draw("cRainHum", [
    {type:"bar", x:lab, y:vals.map(v=>v.d), name:"Rain today", marker:{color:COL.neutral, cornerradius:3}, customdata:vals.map(v=>v.n), hovertemplate:"3pm humidity %{x}<br>Rain today: %{y:.0f}% (n=%{customdata})<extra></extra>"},
    {type:"bar", x:lab, y:vals.map(v=>v.t), name:"Rain tomorrow", marker:{color:COL.blue, cornerradius:3}, customdata:vals.map(v=>v.n), hovertemplate:"3pm humidity %{x}<br>Rain tomorrow: %{y:.0f}% (n=%{customdata})<extra></extra>"},
  ], baseLayout("Chance of rain by 3pm humidity band", 320, {
    barmode:"group", bargap:.25, bargroupgap:.06, yaxis:{range:[0,100], ticksuffix:"%", gridcolor:COL.grid, linecolor:COL.border, tickfont:{color:COL.soft}, zeroline:false},
    shapes: base===null?[]:[{type:"line", xref:"paper", x0:0, x1:1, y0:base, y1:base, line:{color:COL.ink, width:1.2, dash:"dash"}}],
    annotations: base===null?[]:[{xref:"paper", x:0.005, y:base, text:`overall chance of rain tomorrow: ${base.toFixed(0)}%`, showarrow:false, yanchor:"bottom", xanchor:"left", font:{size:10.5,color:COL.soft}}]}));
}
// --- event timelines (filtered days shown, others left blank so line does not bridge them)
function timeline(id, ids, key, title, opts) {
  const inSet = new Set(ids);
  const x=[], y=[]; let prevT=null;
  for (let i=0;i<N;i++) {
    if (!inSet.has(i)) continue;
    if (prevT!==null && C.t[i]-prevT>3) { x.push(C.dt[i]); y.push(null); }
    x.push(C.dt[i]); y.push(C[key][i]); prevT=C.t[i];
  }
  const flagged = ids.filter(i=>opts.flag(i));
  const traces = [];
  if (opts.bars) traces.push({type:"bar", x:ids.filter(i=>!opts.flag(i)).map(i=>C.dt[i]), y:ids.filter(i=>!opts.flag(i)).map(i=>C[key][i]), name:opts.name, marker:{color:COL.blue},
    hovertemplate:"%{x}<br>%{y} "+opts.unit+"<extra></extra>"});
  else traces.push({type:"scattergl", mode:"lines", x, y, name:opts.name, line:{color:opts.color, width:1}, connectgaps:false, hovertemplate:"%{x}<br>%{y} "+opts.unit+"<extra></extra>"});
  traces.push({type:opts.bars?"bar":"scattergl", mode:"markers", x:flagged.map(i=>C.dt[i]), y:flagged.map(i=>C[key][i]), name:opts.flagName,
    marker:opts.bars?{color:COL.bad}:{color:COL.bad, size:8, symbol:"diamond", line:{color:"#fff", width:1}},
    customdata:flagged.map(i=>AT[C.at[i]]), hovertemplate:"%{x}<br>%{y} "+opts.unit+"<br>%{customdata}<extra>"+opts.flagName+"</extra>"});
  draw(id, traces, baseLayout(title, 270, {yaxis:{ticksuffix:opts.suffix||"", rangemode:opts.zero?"tozero":"normal", gridcolor:COL.grid, linecolor:COL.border, tickfont:{color:COL.soft}, zeroline:false},
    xaxis:{gridcolor:COL.grid, linecolor:COL.border, tickfont:{color:COL.soft}, rangeslider:{visible:false}, zeroline:false}, bargap:0}));
}
function chartTimelines(ids) {
  const has = (i,t)=>AT[C.at[i]].split("; ").includes(t);
  timeline("cTlTemp", ids, "mx", "Daily max temperature — red diamonds = unusually hot/cold for the month (|z| ≥ 3)", {name:"Daily max", flagName:"Heat / cold anomaly", unit:"°C", suffix:"°C", color:COL.orange, flag:i=>has(i,"Heat")||has(i,"Cold")});
  timeline("cTlRain", ids, "r", "Daily rainfall — red bars = extreme rain days", {name:"Daily rainfall", flagName:"Extreme rain", unit:"mm", suffix:" mm", bars:true, zero:true, flag:i=>has(i,"Extreme rain")});
  timeline("cTlGust", ids, "g", "Daily peak wind gust — readings start Oct 2010; red diamonds = extreme gust (|z| ≥ 3)", {name:"Peak gust", flagName:"Extreme gust", unit:"km/h", suffix:"", color:COL.blue, zero:true, flag:i=>has(i,"Extreme gust")});
}
function chartAnomYear(ids) {
  const groups = {"Temperature":["Heat","Cold","Warm night","Cold night"], "Rain":["Extreme rain"], "Wind":["Extreme gust"], "Humidity / pressure":["Very humid","Very dry","High pressure","Low pressure"]};
  const colors = {"Temperature":COL.orange, "Rain":COL.blue, "Wind":COL.aqua, "Humidity / pressure":COL.yellow};
  const years = Array.from(new Set(C.y)).sort();
  const traces = Object.entries(groups).map(([name,tags])=>({type:"bar", name, x:years.map(String),
    y:years.map(y=>ids.filter(i=>C.y[i]===y && AT[C.at[i]].split("; ").some(t=>tags.includes(t))).length), marker:{color:colors[name], line:{color:"#fff", width:1}},
    hovertemplate:"%{x}<br>"+name+": %{y} flags<extra></extra>"}));
  draw("cAnomYear", traces, baseLayout("Anomaly flags per year, by type", 340,
    {barmode:"stack", xaxis:{type:"category", tickfont:{color:COL.soft}, linecolor:COL.border}, yaxis:{gridcolor:COL.grid, linecolor:COL.border, tickfont:{color:COL.soft}, zeroline:false}}));
}
function rank(arr) {
  const idx = arr.map((v,i)=>[v,i]).sort((a,b)=>a[0]-b[0]); const r = new Array(arr.length);
  for (let i=0;i<idx.length;) { let j=i; while (j+1<idx.length && idx[j+1][0]===idx[i][0]) j++; const avg=(i+j)/2+1; for (let k=i;k<=j;k++) r[idx[k][1]]=avg; i=j+1; }
  return r;
}
function pearson(a,b) {
  const n=a.length, ma=sum(a)/n, mb=sum(b)/n; let sab=0,saa=0,sbb=0;
  for (let i=0;i<n;i++){ const x=a[i]-ma,y=b[i]-mb; sab+=x*y; saa+=x*x; sbb+=y*y; }
  return saa&&sbb ? sab/Math.sqrt(saa*sbb) : null;
}
function spearmanPair(ids, ka, kb) {
  const xs=[], ys=[];
  for (const i of ids) { const x=C[ka][i], y=C[kb][i]; if (x!==null && y!==null) { xs.push(x); ys.push(y); } }
  return xs.length<30 ? null : pearson(rank(xs), rank(ys));
}
function chartCorr(ids) {
  const vars = [["mx","Max temp"],["mn","Min temp"],["r","Rainfall"],["su","Sunshine"],["g","Wind gust"],["h9","Humidity 9am"],["h3","Humidity 3pm"],["p3","Pressure 3pm"],["c3","Cloud 3pm"]];
  if (ids.length<30) return emptyMsg("cCorr","Rank correlation of measurements");
  const k = vars.length, z = vars.map(()=>new Array(k).fill(null));
  for (let a=0;a<k;a++) { z[a][a]=1; for (let b=a+1;b<k;b++) { const c=spearmanPair(ids, vars[a][0], vars[b][0]); z[a][b]=z[b][a]=(c===null?null:+c.toFixed(2)); } }
  const names = vars.map(v=>v[1]);
  draw("cCorr", [{type:"heatmap", z, x:names, y:names, zmin:-1, zmax:1, zmid:0, xgap:1, ygap:1,
    colorscale:[[0,COL.blue],[0.5,"#f1f0ee"],[1,COL.orange]], text:z.map(r=>r.map(v=>v===null?"":v.toFixed(2))), texttemplate:"%{text}", textfont:{size:9.5, color:COL.ink},
    hovertemplate:"%{y} vs %{x}: %{z:.2f}<extra></extra>", colorbar:{thickness:12, len:.9}}],
    baseLayout("Rank correlation of measurements (days with both values)", 340,
      {margin:{t:50,l:96,r:16,b:86}, yaxis:{autorange:"reversed", tickfont:{color:COL.soft, size:10.5}, linecolor:COL.border},
       xaxis:{tickangle:-40, tickfont:{color:COL.soft, size:10.5}, linecolor:COL.border}}));
}
function tableAnom(ids) {
  const rows = ids.filter(i=>AT[C.at[i]]!=="").map(i=>({i, n:AT[C.at[i]].split("; ").length, z:Math.abs(C.mz[i])}))
    .sort((a,b)=>b.n-a.n || b.z-a.z).slice(0,15);
  const el = document.getElementById("anomTable");
  if (!rows.length) { el.innerHTML = '<div class="empty">No anomalous days in the current selection.</div>'; return; }
  const tags = s => s.split("; ").map(t=>`<span class="tag">${t}</span>`).join("");
  el.innerHTML = `<div style="padding:8px 4px 4px;font-weight:bold;font-size:13.5px">Most unusual days in the selection (most flags first, then hottest z-score) — showing ${rows.length} of ${ids.filter(i=>AT[C.at[i]]!=="").length}</div>
  <table><thead><tr><th>Date</th><th>What was unusual</th><th>Max °C</th><th>Rain mm</th><th>Gust km/h</th><th>Gust from</th><th>3pm humidity</th></tr></thead><tbody>` +
    rows.map(({i})=>`<tr><td>${C.dt[i]}</td><td>${tags(AT[C.at[i]])}</td><td>${C.mx[i]}</td><td>${C.r[i]}</td><td>${C.g[i]===null?"–":C.g[i]}</td><td>${C.gd[i]===null?"–":DIRS[C.gd[i]]}</td><td>${C.h3[i]}%</td></tr>`).join("") + "</tbody></table>";
}

// ------------------------------------------------------------------ render
function render() {
  const ids = select();
  renderChips(); renderKPIs(ids);
  if (!ids.length) { ["cTempTs","cTempBox","cScatter","cRainTs","cRainClass","cRainHum","cTlTemp","cTlRain","cTlGust","cAnomYear","cCorr"].forEach(id=>emptyMsg(id,"")); document.getElementById("anomTable").innerHTML='<div class="empty">No days match this filter combination.</div>'; }
  else {
    chartTempTs(ids); chartTempBox(ids); chartScatter(ids); chartRainTs(ids); chartRainClass(ids); chartRainHum(ids);
    chartTimelines(ids); chartAnomYear(ids); chartCorr(ids); tableAnom(ids);
  }
  chartTempCal(); chartHum(); chartRose(); chartWindMonth(); chartRainByDir(); chartRainDays();
  if (!chartHeat.done) { chartHeat(); chartHeat.done = true; }
}
initFilters(); render();
</script>
</body>
</html>
"""


def main():
    df = pd.read_csv(IN_CSV)
    with open(IN_JSON, encoding="utf-8") as f:
        S = json.load(f)
    data = build_data(df)
    wet = df.loc[df["IsRainDay"] == 1, "Rainfall"]
    q1, q3 = wet.quantile([0.25, 0.75])
    fence = q3 + 3 * (q3 - q1)
    d = pd.to_datetime(df["Date"]).dt.to_period("M")
    months = pd.period_range(d.min(), d.max(), freq="M")
    missing = [p.strftime("%b %Y") for p in months if p not in set(d)]
    html = (TEMPLATE
            .replace("__PLOTLYJS__", get_plotlyjs())
            .replace("__DATA__", json.dumps(data, separators=(",", ":")))
            .replace("__INSIGHTS__", insights_html(S))
            .replace("__FENCE__", f"{fence:.1f}")
            .replace("__MISSING__", ", ".join(missing)))
    with open(OUT_HTML, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Wrote {OUT_HTML} ({len(html) / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
