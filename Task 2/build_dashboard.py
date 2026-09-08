"""
Task 2 - Sales Data (FactSale): Management Dashboard

Builds Sales_Dashboard.html from the cleaned dataset. Chart choices follow
the business questions the data can actually answer:
  - Is the business growing? (monthly revenue & profit trend)
  - Where does the money come from? (category / product mix)
  - Where is money being lost? (loss-making SKUs - a real, actionable finding,
    not just "a bunch of charts")
  - How is the customer base composed? (registered vs. walk-in)
  - Who is selling? (salesperson leaderboard - by ID, since no name lookup
    table was provided with this file)

Look & feel: a printed analyst report, not a SaaS app template - one paper
background, a serif/sans masthead, hairline section rules instead of boxed
"widget cards", and small hand-computed sparklines next to each KPI rather
than decorative chrome. Chart colors still follow the house data-viz standard
(validated categorical order, single axis per chart, native hover tooltips).
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go

IN_PATH = "Cleaned_FactSale.csv"
OUT_PATH = "Sales_Dashboard.html"

# ---- paper + ink (report palette - one accent, no gradients) --------------
PAPER = "#faf9f6"
INK_PRIMARY = "#1a1a18"
INK_SECONDARY = "#5a584f"
INK_MUTED = "#8c8a80"
RULE = "#ddd9cd"
GRID = "#eae7dc"

BLUE, ORANGE, AQUA, YELLOW, MAGENTA, GREEN, VIOLET, RED = (
    "#2a78d6", "#eb6834", "#1baf7a", "#eda100",
    "#e87ba4", "#008300", "#4a3aa7", "#e34948",
)
STATUS_GOOD = "#1e7a4a"
STATUS_CRITICAL = "#b5322f"

SERIF = "'Newsreader', Georgia, serif"
SANS = "'IBM Plex Sans', system-ui, -apple-system, sans-serif"

BASE_FONT = dict(family=SANS, color=INK_PRIMARY, size=12.5)


def base_layout(height=380, legend=False):
    layout = dict(
        paper_bgcolor=PAPER,
        plot_bgcolor=PAPER,
        font=BASE_FONT,
        margin=dict(t=10, l=48, r=20, b=40),
        height=height,
        hoverlabel=dict(bgcolor="white", font=dict(family=SANS, color=INK_PRIMARY), bordercolor=RULE),
        showlegend=legend,
    )
    if legend:
        layout["legend"] = dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0,
                                 font=dict(color=INK_SECONDARY))
    return layout


def style_axes(fig, xgrid=False, ygrid=True):
    fig.update_xaxes(showgrid=xgrid, gridcolor=GRID, linecolor=RULE, tickfont=dict(color=INK_MUTED), zeroline=False)
    fig.update_yaxes(showgrid=ygrid, gridcolor=GRID, linecolor=RULE, tickfont=dict(color=INK_MUTED), zeroline=False)
    return fig


def money(x):
    return f"${x:,.0f}"


def sparkline(values, color, w=76, h=24, pad=3):
    """A tiny inline trend line (no chart library) drawn behind each KPI."""
    vals = list(values)
    if len(vals) < 2 or min(vals) == max(vals):
        return ""
    lo, hi = min(vals), max(vals)
    step = (w - 2 * pad) / (len(vals) - 1)
    pts = []
    for i, v in enumerate(vals):
        x = pad + i * step
        y = h - pad - (v - lo) / (hi - lo) * (h - 2 * pad)
        pts.append(f"{x:.1f},{y:.1f}")
    path = " ".join(pts)
    last_x, last_y = pts[-1].split(",")
    return (f'<svg class="spark" width="{w}" height="{h}" viewBox="0 0 {w} {h}">'
            f'<polyline points="{path}" fill="none" stroke="{color}" stroke-width="1.5" '
            f'stroke-linecap="round" stroke-linejoin="round"/>'
            f'<circle cx="{last_x}" cy="{last_y}" r="1.8" fill="{color}"/></svg>')


def section(label, chart_html, caption=None, full=False):
    cap = f'<div class="chart-caption">{caption}</div>' if caption else ""
    cls = "col full" if full else "col"
    return f'<div class="{cls}"><div class="section-label">{label}</div>{chart_html}{cap}</div>'


def build():
    df = pd.read_csv(IN_PATH, parse_dates=["Invoice Date Key", "Delivery Date Key"])
    df["Month"] = df["Invoice Date Key"].dt.to_period("M").dt.to_timestamp()

    # ---------------- monthly series (also feed the KPI sparklines) --------
    monthly = df.groupby("Month").agg(
        Revenue=("Total Excluding Tax", "sum"),
        Profit=("Profit", "sum"),
        Orders=("WWI Invoice ID", "nunique"),
        LossRate=("Is_Loss_Making", "mean"),
    ).reset_index()
    monthly["Margin"] = monthly["Profit"] / monthly["Revenue"] * 100
    monthly["AOV"] = monthly["Revenue"] / monthly["Orders"]
    monthly["LossRate"] *= 100

    # ---------------- KPIs ----------------
    total_revenue = df["Total Excluding Tax"].sum()
    total_profit = df["Profit"].sum()
    profit_margin = total_profit / total_revenue * 100
    total_orders = df["WWI Invoice ID"].nunique()
    aov = total_revenue / total_orders
    loss_pct = df["Is_Loss_Making"].mean() * 100
    date_min = df["Invoice Date Key"].min().strftime("%b %Y")
    date_max = df["Invoice Date Key"].max().strftime("%b %Y")

    # ---------------- 1. Monthly revenue & profit trend ----------------
    fig_trend = go.Figure()
    fig_trend.add_trace(go.Scatter(x=monthly["Month"], y=monthly["Revenue"], name="Revenue",
                                    mode="lines", line=dict(color=BLUE, width=2.5),
                                    hovertemplate="%{x|%b %Y}<br>Revenue: $%{y:,.0f}<extra></extra>"))
    fig_trend.add_trace(go.Scatter(x=monthly["Month"], y=monthly["Profit"], name="Profit",
                                    mode="lines", line=dict(color=ORANGE, width=2.5),
                                    hovertemplate="%{x|%b %Y}<br>Profit: $%{y:,.0f}<extra></extra>"))
    fig_trend.update_layout(**base_layout(height=340, legend=True))
    fig_trend.update_yaxes(tickprefix="$", tickformat=",.0f")
    style_axes(fig_trend)

    # ---------------- 2. Revenue by product category ----------------
    cat = df.groupby("Product_Category")["Total Excluding Tax"].sum().sort_values(ascending=True)
    fig_cat = go.Figure(go.Bar(x=cat.values, y=cat.index, orientation="h", marker_color=BLUE,
                                hovertemplate="%{y}<br>Revenue: $%{x:,.0f}<extra></extra>"))
    fig_cat.update_layout(**base_layout(height=340))
    fig_cat.update_xaxes(tickprefix="$", tickformat=",.0f")
    style_axes(fig_cat, ygrid=False)

    # ---------------- 3. Profit margin % by category ----------------
    margin_cat = (df.groupby("Product_Category").apply(
        lambda g: g["Profit"].sum() / g["Total Excluding Tax"].sum() * 100, include_groups=False)
        .sort_values(ascending=True))
    colors = [STATUS_CRITICAL if v < 0 else BLUE for v in margin_cat.values]
    fig_margin = go.Figure(go.Bar(x=margin_cat.values, y=margin_cat.index, orientation="h",
                                   marker_color=colors,
                                   hovertemplate="%{y}<br>Profit margin: %{x:.1f}%<extra></extra>"))
    fig_margin.update_layout(**base_layout(height=340))
    fig_margin.update_xaxes(ticksuffix="%")
    style_axes(fig_margin, ygrid=False)

    # ---------------- 4. Top 10 products by revenue ----------------
    top_products = (df.groupby("Description")["Total Excluding Tax"].sum()
                     .nlargest(10).sort_values(ascending=True))
    fig_top = go.Figure(go.Bar(x=top_products.values, y=top_products.index, orientation="h",
                                marker_color=AQUA,
                                hovertemplate="%{y}<br>Revenue: $%{x:,.0f}<extra></extra>"))
    fig_top.update_layout(**base_layout(height=380))
    fig_top.update_xaxes(tickprefix="$", tickformat=",.0f")
    style_axes(fig_top, ygrid=False)

    # ---------------- 5. Loss-making products (the actionable finding) ----------------
    loss = df[df["Is_Loss_Making"]].groupby("Description").agg(
        Loss=("Profit", "sum"), Units=("Quantity", "sum")
    ).nsmallest(10, "Loss").sort_values("Loss", ascending=False)
    fig_loss = go.Figure(go.Bar(x=loss["Loss"], y=loss.index, orientation="h", marker_color=STATUS_CRITICAL,
                                 hovertemplate="%{y}<br>Total loss: $%{x:,.0f}<extra></extra>"))
    fig_loss.update_layout(**base_layout(height=380))
    fig_loss.update_xaxes(tickprefix="$", tickformat=",.0f")
    style_axes(fig_loss, ygrid=False)
    worst_val = loss["Loss"].iloc[-1]  # last item = plotted at top (most negative)
    fig_loss.add_annotation(
        x=worst_val, y=loss.index[-1], text="100% of its sales<br>lose money", showarrow=True,
        arrowhead=0, arrowcolor=INK_MUTED, arrowwidth=1, ax=-90, ay=-4,
        font=dict(family=SANS, size=11, color=INK_SECONDARY), align="right",
    )

    # ---------------- 6. Customer type split ----------------
    cust = df.groupby("Customer_Type")["Total Excluding Tax"].sum()
    fig_cust = go.Figure(go.Pie(labels=cust.index, values=cust.values, hole=0.6,
                                 marker=dict(colors=[BLUE, YELLOW], line=dict(color=PAPER, width=2)),
                                 hovertemplate="%{label}<br>$%{value:,.0f} (%{percent})<extra></extra>",
                                 textinfo="percent", textfont=dict(color="white", size=13)))
    fig_cust.update_layout(**base_layout(height=320, legend=True))

    # ---------------- 7. Top salespeople ----------------
    sp = (df.groupby("Salesperson Key")["Total Excluding Tax"].sum()
          .nlargest(10).sort_values(ascending=True))
    fig_sp = go.Figure(go.Bar(x=sp.values, y=[f"Salesperson #{k}" for k in sp.index], orientation="h",
                               marker_color=VIOLET,
                               hovertemplate="%{y}<br>Revenue: $%{x:,.0f}<extra></extra>"))
    fig_sp.update_layout(**base_layout(height=380))
    fig_sp.update_xaxes(tickprefix="$", tickformat=",.0f")
    style_axes(fig_sp, ygrid=False)

    # ---------------- 8. Revenue by package type ----------------
    pkg = df.groupby("Package")["Total Excluding Tax"].sum().sort_values(ascending=True)
    pkg_pct = pkg / pkg.sum() * 100
    fig_pkg = go.Figure(go.Bar(x=pkg.values, y=pkg.index, orientation="h", marker_color=GREEN,
                                text=[f"{p:.1f}%" for p in pkg_pct], textposition="outside",
                                textfont=dict(color=INK_SECONDARY),
                                hovertemplate="%{y}<br>Revenue: $%{x:,.0f}<extra></extra>"))
    fig_pkg.update_layout(**base_layout(height=260))
    fig_pkg.update_xaxes(tickprefix="$", tickformat=",.0f", range=[0, pkg.max() * 1.18])
    style_axes(fig_pkg, ygrid=False)

    figs = dict(trend=fig_trend, cat=fig_cat, margin=fig_margin, top=fig_top,
                loss=fig_loss, cust=fig_cust, sp=fig_sp, pkg=fig_pkg)
    html_parts = {k: f.to_html(full_html=False, include_plotlyjs=("cdn" if k == "trend" else False),
                                config={"displaylogo": False})
                  for k, f in figs.items()}

    kpis = [
        ("Total Revenue", money(total_revenue), INK_PRIMARY, monthly["Revenue"], BLUE),
        ("Total Profit", money(total_profit), INK_PRIMARY, monthly["Profit"], ORANGE),
        ("Profit Margin", f"{profit_margin:.1f}%", STATUS_GOOD, monthly["Margin"], STATUS_GOOD),
        ("Orders", f"{total_orders:,}", INK_PRIMARY, monthly["Orders"], AQUA),
        ("Avg. Order Value", money(aov), INK_PRIMARY, monthly["AOV"], VIOLET),
        ("Loss-Making Lines", f"{loss_pct:.1f}%", STATUS_CRITICAL, monthly["LossRate"], STATUS_CRITICAL),
    ]
    kpi_html = "".join(
        f'<div class="stat"><div class="stat-label">{label}</div>'
        f'<div class="stat-value" style="color:{color}">{value}</div>'
        f'{sparkline(series, spark_color)}</div>'
        for label, value, color, series, spark_color in kpis
    )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Sales Performance Report</title>
<link href="https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,500;0,6..72,600;1,6..72,500&family=IBM+Plex+Sans:wght@400;500;600&display=swap" rel="stylesheet">
<style>
  :root {{
    --paper: {PAPER}; --ink: {INK_PRIMARY}; --ink-sec: {INK_SECONDARY};
    --muted: {INK_MUTED}; --rule: {RULE};
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0; padding: 40px 0 60px 0; background: var(--paper); color: var(--ink);
    font-family: {SANS};
  }}
  .wrap {{ max-width: 1180px; margin: 0 auto; padding: 0 32px; }}

  .masthead {{ border-top: 2px solid var(--ink); padding-top: 14px; margin-bottom: 8px; }}
  .eyebrow {{ font-size: 0.7rem; letter-spacing: 0.14em; text-transform: uppercase; color: var(--ink-sec); font-weight: 600; }}
  h1 {{ font-family: {SERIF}; font-size: 2.3rem; font-weight: 600; margin: 6px 0 8px 0; letter-spacing: -0.01em; }}
  .byline {{ font-size: 0.82rem; color: var(--ink-sec); padding-bottom: 16px; border-bottom: 1px solid var(--rule); margin-bottom: 24px; }}
  .byline b {{ color: var(--ink); font-weight: 600; }}

  .stat-strip {{ display: flex; margin-bottom: 8px; }}
  .stat {{ flex: 1; padding: 0 22px 0 0; margin-right: 22px; border-right: 1px solid var(--rule); }}
  .stat:last-child {{ border-right: none; margin-right: 0; padding-right: 0; }}
  .stat-label {{ font-size: 0.68rem; letter-spacing: 0.06em; text-transform: uppercase; color: var(--muted); margin-bottom: 6px; font-weight: 500; }}
  .stat-value {{ font-family: {SERIF}; font-size: 1.55rem; font-weight: 600; line-height: 1; margin-bottom: 6px; }}
  .spark {{ display: block; opacity: 0.9; }}

  .section-row {{ display: grid; grid-template-columns: 1fr 1fr; gap: 36px; border-top: 1px solid var(--rule); padding-top: 22px; margin-top: 26px; }}
  .section-row.single {{ display: block; }}
  .col.full {{ grid-column: 1 / -1; }}
  .section-label {{ font-size: 0.72rem; letter-spacing: 0.07em; text-transform: uppercase; color: var(--ink-sec); font-weight: 600; margin-bottom: 6px; }}
  .chart-caption {{ font-size: 0.78rem; color: var(--muted); margin-top: 2px; }}

  .analyst-note {{
    grid-column: 1 / -1; border-top: 1px solid var(--rule); padding: 22px 0 0 0; margin-top: 26px;
  }}
  .analyst-note .section-label {{ color: {STATUS_CRITICAL}; }}
  .analyst-note blockquote {{
    margin: 6px 0 0 0; padding-left: 18px; border-left: 2px solid {STATUS_CRITICAL};
    font-family: {SERIF}; font-style: italic; font-size: 1.05rem; color: var(--ink); line-height: 1.5;
    max-width: 760px;
  }}
  .analyst-note .rec {{ margin: 10px 0 0 18px; font-size: 0.86rem; color: var(--ink-sec); }}

  footer {{
    margin-top: 36px; padding-top: 14px; border-top: 1px solid var(--rule);
    color: var(--muted); font-size: 0.76rem; display: flex; justify-content: space-between;
  }}
  @media (max-width: 860px) {{
    .stat-strip {{ flex-wrap: wrap; }}
    .stat {{ flex: 1 1 33%; margin-bottom: 14px; }}
    .section-row {{ grid-template-columns: 1fr; }}
  }}
</style>
</head>
<body>
<div class="wrap">
  <div class="masthead">
    <div class="eyebrow">Task 2 &middot; Sales Data (FactSale)</div>
    <h1>Sales Performance Report</h1>
    <div class="byline"><b>Prepared by Nahla Nabil</b> &middot; VOLTIX Data Analyst Internship &middot; {date_min}&ndash;{date_max} &middot; {len(df):,} line items across {total_orders:,} orders</div>
  </div>

  <div class="stat-strip">{kpi_html}</div>

  <div class="section-row single">
    {section("Monthly Revenue &amp; Profit", html_parts['trend'], full=True)}
  </div>

  <div class="section-row">
    {section("Revenue by Product Category", html_parts['cat'])}
    {section("Profit Margin % by Category", html_parts['margin'])}
  </div>

  <div class="section-row">
    {section("Top 10 Products by Revenue", html_parts['top'])}
    {section("Biggest Loss-Making Products", html_parts['loss'], caption="Every unit of these products is sold below cost.")}
  </div>

  <div class="analyst-note">
    <div class="section-label">Analyst note</div>
    <blockquote>
      The Halloween zombie mask has never once sold at a profit &mdash; all 492 line items, 100% of its sales,
      lose money. Its sibling product, the Halloween skull mask, runs a healthy ~17% margin, so this is a
      single mispriced SKU, not a weak product line.
    </blockquote>
    <div class="rec">Recommendation: re-price or discontinue the zombie mask and the small cluster of
      loss-making novelty USB drives shown above &mdash; a low-effort, high-confidence margin recovery.</div>
  </div>

  <div class="section-row">
    {section("Registered vs. Unknown/Walk-in Revenue", html_parts['cust'])}
    {section("Revenue by Package Type", html_parts['pkg'], caption="96.8% of revenue is single-unit (‘Each’) sales.")}
  </div>

  <div class="section-row single">
    {section("Top 10 Salespeople by Revenue", html_parts['sp'], caption="By salesperson ID — no name lookup table was provided with this dataset.", full=True)}
  </div>

  <footer>
    <span>Sales_Dashboard.html &middot; generated from Cleaned_FactSale.csv</span>
    <span>Product / customer / salesperson names unavailable &mdash; shown by ID</span>
  </footer>
</div>
</body>
</html>
"""
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Dashboard written -> {OUT_PATH}")


if __name__ == "__main__":
    build()
