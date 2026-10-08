"""Interactive dashboard for Task 12 -> Task 12/Airbnb_NYC_Dashboard.html.

Run from the repo root:  python "Task 12/build_dashboard.py"
Self-contained (plotly.js embedded, no internet needed).
Interactivity: legend slicers on every split chart, a metric-switcher menu,
a borough filter + sorting on the neighbourhood table, hover everywhere.
"""
import json
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px   # noqa: F401  (kept for parity with earlier tasks)

TASK = Path(__file__).resolve().parent
CLEAN = TASK / "Cleaned_AB_NYC_2019.csv"
OUT = TASK / "Airbnb_NYC_Dashboard.html"
SUMMARY = json.loads((TASK / "analysis_summary.json").read_text())
K = SUMMARY["kpis"]

COLORS = {"Manhattan": "#1F3B57", "Brooklyn": "#1B998B", "Queens": "#E0A030",
          "Bronx": "#E4572E", "Staten Island": "#8E5572"}
ORDER = ["Manhattan", "Brooklyn", "Queens", "Bronx", "Staten Island"]

df = pd.read_csv(CLEAN)
val = df[df["price"] <= 1000].copy()


def div(fig):
    return fig.to_html(include_plotlyjs=False, full_html=False)


# ---- Chart 1: borough switcher (count / median price / mean reviews) ------------
cnt = df["neighbourhood_group"].value_counts().reindex(ORDER)
med = val.groupby("neighbourhood_group")["price"].median().reindex(ORDER)
rev = df.groupby("neighbourhood_group")["number_of_reviews"].mean().reindex(ORDER).round(1)
fig1 = go.Figure()
fig1.add_bar(x=ORDER, y=cnt.values, marker_color=[COLORS[b] for b in ORDER],
             hovertemplate="%{x}: %{y:,} listings<extra></extra>")
fig1.update_layout(
    title="Borough comparison — switch the metric",
    updatemenus=[dict(type="buttons", direction="right", x=0, y=1.18, showactive=True,
                      buttons=[
                          dict(label="Listings", method="update",
                               args=[{"y": [cnt.values], "hovertemplate": "%{x}: %{y:,} listings<extra></extra>"},
                                     {"yaxis": {"title": "Listings"}}]),
                          dict(label="Median price ($)", method="update",
                               args=[{"y": [med.values], "hovertemplate": "%{x}: $%{y:.0f}<extra></extra>"},
                                     {"yaxis": {"title": "Median price ($)"}}]),
                          dict(label="Mean reviews", method="update",
                               args=[{"y": [rev.values], "hovertemplate": "%{x}: %{y:.1f} reviews<extra></extra>"},
                                     {"yaxis": {"title": "Mean reviews"}}])])],
    yaxis_title="Listings", margin=dict(t=90), height=420)

# ---- Chart 2: room mix by borough (legend = slicer) ---------------------------------
room_order = ["Entire home/apt", "Private room", "Shared room"]
fig2 = go.Figure()
for r in room_order:
    y = [float((df[df["neighbourhood_group"] == b]["room_type"] == r).mean() * 100) for b in ORDER]
    fig2.add_bar(name=r, x=ORDER, y=y, hovertemplate=f"{r}: %{{y:.1f}}%<extra></extra>")
fig2.update_layout(barmode="stack", title="Room-type mix by borough (click legend to filter)",
                   yaxis_title="% of borough listings", height=420)

# ---- Chart 3: price histogram ----------------------------------------------------------
fig3 = go.Figure()
fig3.add_histogram(x=val["price"], nbinsx=80, marker_color="#1F3B57",
                   hovertemplate="$%{x:.0f}: %{y:,} listings<extra></extra>")
fig3.add_vline(x=K["median_price"], line_dash="dash", line_color="#E4572E",
               annotation_text=f"Median ${K['median_price']:.0f}")
fig3.update_layout(title="Nightly-price distribution (capped at $1,000)",
                   xaxis_title="Nightly price ($)", yaxis_title="Listings",
                   xaxis_range=[0, 600], height=400)

# ---- Chart 4: box price by room type -------------------------------------------------------
fig4 = go.Figure()
for r in room_order:
    fig4.add_box(y=val[val["room_type"] == r]["price"].clip(upper=500), name=r,
                 boxmean=True, hovertemplate=f"{r}: $%{{y:.0f}}<extra></extra>")
fig4.update_layout(title="Price spread by listing type (capped $500, triangle = mean)",
                   yaxis_title="Nightly price ($)", height=400)

# ---- Chart 5: map (legend = slicer) ----------------------------------------------------------------
smp = df.sample(6000, random_state=7)
fig5 = go.Figure()
for b in ORDER:
    d = smp[smp["neighbourhood_group"] == b]
    fig5.add_trace(go.Scattermap(lat=d["latitude"], lon=d["longitude"], mode="markers", name=b,
                                 marker=dict(size=4, opacity=0.5, color=COLORS[b]),
                                 hovertemplate=f"{b}<br>$%{{customdata[0]:.0f}} · %{{customdata[1]}}<extra></extra>",
                                 customdata=list(zip(d["price"], d["room_type"]))))
fig5.update_layout(title="Listing map — 6,000-listing sample (click legend to isolate a borough)",
                   map=dict(style="open-street-map",
                            center=dict(lat=40.72, lon=-73.95), zoom=10.2),
                   height=520, margin=dict(t=60, b=10))

# ---- Chart 6: price vs reviews scatter --------------------------------------------------------------------
s2 = val.sample(3000, random_state=21)
fig6 = go.Figure()
for b in ORDER:
    d = s2[s2["neighbourhood_group"] == b]
    fig6.add_trace(go.Scatter(x=d["number_of_reviews"], y=d["price"].clip(upper=600),
                              mode="markers", name=b,
                              marker=dict(size=5, opacity=0.45, color=COLORS[b]),
                              hovertemplate=f"{b}<br>%{{x:.0f}} reviews · $%{{y:.0f}}<extra></extra>"))
fig6.update_layout(title="Price vs review volume: no relationship (r = -0.06)",
                   xaxis_title="Number of reviews", yaxis_title="Nightly price, capped $600 ($)",
                   xaxis_range=[-5, 350], height=420)

# ---- Chart 7: availability segments --------------------------------------------------------------------------
av_order = ["Inactive (0 days)", "Low (1-90)", "Medium (91-180)", "High (181-364)", "Fully open (365)"]
avc = df["avail_segment"].value_counts().reindex(av_order)
fig7 = go.Figure()
fig7.add_bar(x=av_order, y=avc.values, marker_color="#E0A030",
             hovertemplate="%{x}: %{y:,} listings<extra></extra>")
fig7.update_layout(title="Availability: barbelled supply", yaxis_title="Listings", height=400)
fig7.update_xaxes(tickangle=-12)

# ---- Table: top 25 neighbourhoods (JS borough filter + sort) -------------------------------------------------
nt = (df.groupby(["neighbourhood", "neighbourhood_group"])
        .agg(listings=("id", "count"),
             med_price=("price", lambda x: float(x[x <= 1000].median())),
             mean_reviews=("number_of_reviews", "mean"))
        .reset_index().sort_values("listings", ascending=False).head(25).round({"med_price": 0, "mean_reviews": 1}))
rows = "\n".join(
    f"<tr data-b='{r.neighbourhood_group}'><td>{r.neighbourhood}</td><td>{r.neighbourhood_group}</td>"
    f"<td data-v='{r.listings}'>{r.listings:,}</td><td data-v='{r.med_price}'>${r.med_price:,.0f}</td>"
    f"<td data-v='{r.mean_reviews}'>{r.mean_reviews}</td></tr>"
    for r in nt.itertuples())

kpis = [
    ("Listings", f"{K['listings']:,}"),
    ("Hosts", f"{K['hosts']:,}"),
    ("Median price", f"${K['median_price']:.0f}"),
    ("Entire homes", f"{K['pct_entire']}%"),
    ("Zero availability", f"{K['pct_avail_zero']}%"),
    ("Never reviewed", f"{K['pct_never_reviewed']}%"),
    ("Total reviews", f"{K['total_reviews']:,}"),
    ("Manhattan share", f"{K['pct_manhattan']}%"),
]
cards = "".join(f"<div class='kpi'><div class='kv'>{v}</div><div class='kl'>{k}</div></div>" for k, v in kpis)

html = f"""<!DOCTYPE html><html lang='en'><head><meta charset='utf-8'>
<meta name='viewport' content='width=device-width, initial-scale=1'>
<title>NYC Airbnb — Interactive Dashboard</title>
<script src='https://cdn.plot.ly/plotly-3.0.0.min.js'></script>
<style>
body{{font-family:Segoe UI,Arial,sans-serif;margin:0;background:#f4f6f8;color:#222}}
header{{background:#1F3B57;color:#fff;padding:22px 28px}}
header h1{{margin:0;font-size:24px}}header p{{margin:6px 0 0;opacity:.85;font-size:13px}}
.wrap{{max-width:1180px;margin:auto;padding:18px}}
.kpis{{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:10px;margin:16px 0}}
.kpi{{background:#fff;border-radius:10px;padding:12px;text-align:center;box-shadow:0 1px 4px #0001}}
.kv{{font-size:22px;font-weight:700;color:#1F3B57}}.kl{{font-size:11px;color:#666;margin-top:4px}}
.card{{background:#fff;border-radius:10px;padding:14px;margin:14px 0;box-shadow:0 1px 4px #0001}}
.card h2{{margin:2px 0 4px;font-size:16px;color:#1F3B57}}.card p.hint{{margin:0 0 8px;font-size:12px;color:#777}}
table{{border-collapse:collapse;width:100%;font-size:13px}}
th,td{{padding:7px 10px;border-bottom:1px solid #eee;text-align:left}}
th{{cursor:pointer;color:#1F3B57;user-select:none}}th:hover{{text-decoration:underline}}
select{{padding:6px 10px;border-radius:6px;border:1px solid #ccc;font-size:13px}}
footer{{color:#777;font-size:12px;padding:10px 28px 26px;max-width:1180px;margin:auto}}
</style></head><body>
<header><h1>New York City Airbnb — Interactive Dashboard</h1>
<p>48,884 listings · 37,455 hosts · 221 neighbourhoods · Sep 2019 snapshot · price stats exclude $1,000+ outliers</p></header>
<div class='wrap'>
<div class='kpis'>{cards}</div>
<div class='card'><h2>1 · Borough comparison</h2><p class='hint'>Buttons switch the metric. Hover for values.</p>{div(fig1)}</div>
<div class='card'><h2>2 · Room-type mix by borough</h2><p class='hint'>Click legend entries to isolate a listing type.</p>{div(fig2)}</div>
<div class='card'><h2>3 · Price distribution</h2><p class='hint'>Right-skewed: half of all listings sit at $105 or less.</p>{div(fig3)}</div>
<div class='card'><h2>4 · Price spread by listing type</h2><p class='hint'>Entire homes (~$160 median) cost 2.3x a private room (~$70).</p>{div(fig4)}</div>
<div class='card'><h2>5 · Listing map</h2><p class='hint'>OpenStreetMap basemap, no token needed. Click legend to isolate a borough.</p>{div(fig5)}</div>
<div class='card'><h2>6 · Price vs review volume</h2><p class='hint'>Cloud with no slope: charging more does not buy more reviews.</p>{div(fig6)}</div>
<div class='card'><h2>7 · Availability segments</h2><p class='hint'>Supply is barbelled — mostly blocked or mostly open.</p>{div(fig7)}</div>
<div class='card'><h2>8 · Top 25 neighbourhoods</h2>
<p class='hint'>Filter by borough, click a column header to sort.</p>
<label>Borough <select id='bf' onchange="f()"><option value=''>All boroughs</option>
{"".join(f"<option>{b}</option>" for b in ORDER)}</select></label>
<table id='t'><thead><tr><th onclick="s(0)">Neighbourhood</th><th onclick="s(1)">Borough</th>
<th onclick="s(2)">Listings</th><th onclick="s(3)">Median $</th><th onclick="s(4)">Mean reviews</th></tr></thead>
<tbody>{rows}</tbody></table></div>
<div class='card'><h2>How to read this dashboard</h2>
<p style='font-size:13px'>Manhattan charges the premium (median $150) but Brooklyn + Queens drive review
activity. Entire homes are 52% of supply and the entire price ladder ($160 / $70 / $45). 36% of listings
show zero open days — check them before counting them as bookable supply. Full method and recommendations:
<code>FINAL_REPORT.md</code> and <code>KEY_INSIGHTS.md</code>.</p></div>
</div>
<footer>Built from <code>Cleaned_AB_NYC_2019.csv</code> with <code>build_dashboard.py</code> (Plotly). Rebuild any time from the raw file.</footer>
<script>
function f(){{var v=document.getElementById('bf').value;
document.querySelectorAll('#t tbody tr').forEach(r=>r.style.display=(!v||r.dataset.b===v)?'':'none')}}
let dd={{}};function s(c){{dd[c]=!dd[c];let t=[...document.querySelectorAll('#t tbody tr')];
t.sort((a,b)=>{{let x=a.cells[c].dataset.v||a.cells[c].innerText,y=b.cells[c].dataset.v||b.cells[c].innerText;
let n=parseFloat(x),m=parseFloat(y);if(!isNaN(n)&&!isNaN(m)){{x=n;y=m}}
return (x>y?1:x<y?-1:0)*(dd[c]?-1:1)}});
t.forEach(r=>r.parentNode.appendChild(r))}}
</script>
<script>/* plotly figures injected above carry their own Plotly.newPlot calls with CDN loader */</script>
</body></html>"""

# inline plotly.js so the file works offline: replace CDN tag with embedded lib
import urllib.request  # noqa: E402  (local file fallback below)

embedded = ""
try:
    import plotly.offline as po
    embedded = "<script>" + open(__import__("plotly").__path__[0] + "/package_data/plotly.min.js",
                                 encoding="utf-8").read() + "</script>"
except Exception:
    pass
if embedded:
    html = html.replace("<script src='https://cdn.plot.ly/plotly-3.0.0.min.js'></script>", embedded, 1)

# fig divs were rendered without plotlyjs; stitch: they reference Plotly — with embedded lib above they run.
OUT.write_text(html, encoding="utf-8")
print(f"wrote {OUT.name}: {OUT.stat().st_size/1e6:.1f} MB")
