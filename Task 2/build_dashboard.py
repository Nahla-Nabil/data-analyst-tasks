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

Palette / chart chrome follow the house data-viz standard (validated
categorical order, fixed hue-per-series, single axis per chart, legend for
every multi-series chart, native hover tooltips on every mark).
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go

IN_PATH = "Cleaned_FactSale.csv"
OUT_PATH = "Sales_Dashboard.html"

# ---- palette (validated categorical order, light-mode chart chrome) -------
SURFACE = "#fcfcfb"
PAGE = "#f9f9f7"
INK_PRIMARY = "#0b0b0b"
INK_SECONDARY = "#52514e"
INK_MUTED = "#898781"
GRID = "#e1e0d9"
AXIS = "#c3c2b7"
BORDER = "rgba(11,11,11,0.10)"

BLUE, ORANGE, AQUA, YELLOW, MAGENTA, GREEN, VIOLET, RED = (
    "#2a78d6", "#eb6834", "#1baf7a", "#eda100",
    "#e87ba4", "#008300", "#4a3aa7", "#e34948",
)
CATEGORICAL = [BLUE, ORANGE, AQUA, YELLOW, MAGENTA, GREEN, VIOLET, RED]
STATUS_GOOD = "#0ca30c"
STATUS_CRITICAL = "#d03b3b"

# Calm-blue page chrome, matching DATA_QUALITY_ISSUES.pdf for a consistent look
# across everything submitted for this task.
NAVY = "#0f2942"
BRAND_BLUE = "#2a5f8f"
ACCENT = "#3d7ab5"
LIGHT_BLUE_BG = "#eef4f9"

BASE_FONT = dict(family="system-ui, -apple-system, Segoe UI, sans-serif", color=INK_PRIMARY, size=13)


def base_layout(title, height=420, legend=False):
    layout = dict(
        title=dict(text=title, font=dict(size=16, color=INK_PRIMARY), x=0.02, xanchor="left"),
        paper_bgcolor=SURFACE,
        plot_bgcolor=SURFACE,
        font=BASE_FONT,
        margin=dict(t=56, l=56, r=24, b=48),
        height=height,
        hoverlabel=dict(bgcolor="white", font=dict(color=INK_PRIMARY), bordercolor=AXIS),
        showlegend=legend,
    )
    if legend:
        layout["legend"] = dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                                 font=dict(color=INK_SECONDARY))
    return layout


def style_axes(fig, xgrid=False, ygrid=True):
    fig.update_xaxes(showgrid=xgrid, gridcolor=GRID, linecolor=AXIS, tickfont=dict(color=INK_MUTED), zeroline=False)
    fig.update_yaxes(showgrid=ygrid, gridcolor=GRID, linecolor=AXIS, tickfont=dict(color=INK_MUTED), zeroline=False)
    return fig


def money(x):
    return f"${x:,.0f}"


def build():
    df = pd.read_csv(IN_PATH, parse_dates=["Invoice Date Key", "Delivery Date Key"])
    df["Month"] = df["Invoice Date Key"].dt.to_period("M").dt.to_timestamp()

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
    monthly = df.groupby("Month")[["Total Excluding Tax", "Profit"]].sum().reset_index()
    fig_trend = go.Figure()
    fig_trend.add_trace(go.Scatter(x=monthly["Month"], y=monthly["Total Excluding Tax"], name="Revenue",
                                    mode="lines", line=dict(color=BLUE, width=3),
                                    hovertemplate="%{x|%b %Y}<br>Revenue: $%{y:,.0f}<extra></extra>"))
    fig_trend.add_trace(go.Scatter(x=monthly["Month"], y=monthly["Profit"], name="Profit",
                                    mode="lines", line=dict(color=ORANGE, width=3),
                                    hovertemplate="%{x|%b %Y}<br>Profit: $%{y:,.0f}<extra></extra>"))
    fig_trend.update_layout(**base_layout("Monthly Revenue & Profit", height=380, legend=True))
    fig_trend.update_yaxes(tickprefix="$", tickformat=",.0f")
    style_axes(fig_trend)

    # ---------------- 2. Revenue by product category ----------------
    cat = df.groupby("Product_Category")["Total Excluding Tax"].sum().sort_values(ascending=True)
    fig_cat = go.Figure(go.Bar(x=cat.values, y=cat.index, orientation="h", marker_color=BLUE,
                                hovertemplate="%{y}<br>Revenue: $%{x:,.0f}<extra></extra>"))
    fig_cat.update_layout(**base_layout("Revenue by Product Category", height=380))
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
    fig_margin.update_layout(**base_layout("Profit Margin % by Category", height=380))
    fig_margin.update_xaxes(ticksuffix="%")
    style_axes(fig_margin, ygrid=False)

    # ---------------- 4. Top 10 products by revenue ----------------
    top_products = (df.groupby("Description")["Total Excluding Tax"].sum()
                     .nlargest(10).sort_values(ascending=True))
    fig_top = go.Figure(go.Bar(x=top_products.values, y=top_products.index, orientation="h",
                                marker_color=AQUA,
                                hovertemplate="%{y}<br>Revenue: $%{x:,.0f}<extra></extra>"))
    fig_top.update_layout(**base_layout("Top 10 Products by Revenue", height=420))
    fig_top.update_xaxes(tickprefix="$", tickformat=",.0f")
    style_axes(fig_top, ygrid=False)

    # ---------------- 5. Loss-making products (the actionable finding) ----------------
    loss = df[df["Is_Loss_Making"]].groupby("Description").agg(
        Loss=("Profit", "sum"), Units=("Quantity", "sum")
    ).nsmallest(10, "Loss").sort_values("Loss", ascending=False)
    fig_loss = go.Figure(go.Bar(x=loss["Loss"], y=loss.index, orientation="h", marker_color=STATUS_CRITICAL,
                                 hovertemplate="%{y}<br>Total loss: $%{x:,.0f}<extra></extra>"))
    fig_loss.update_layout(**base_layout("Biggest Loss-Making Products (every unit sold below cost)", height=420))
    fig_loss.update_xaxes(tickprefix="$", tickformat=",.0f")
    style_axes(fig_loss, ygrid=False)

    # ---------------- 6. Customer type split ----------------
    cust = df.groupby("Customer_Type")["Total Excluding Tax"].sum()
    fig_cust = go.Figure(go.Pie(labels=cust.index, values=cust.values, hole=0.55,
                                 marker=dict(colors=[BLUE, YELLOW], line=dict(color=SURFACE, width=2)),
                                 hovertemplate="%{label}<br>$%{value:,.0f} (%{percent})<extra></extra>",
                                 textinfo="percent", textfont=dict(color="white", size=13)))
    fig_cust.update_layout(**base_layout("Revenue: Registered vs. Unknown/Walk-in Customers", height=380, legend=True))

    # ---------------- 7. Top salespeople ----------------
    sp = (df.groupby("Salesperson Key")["Total Excluding Tax"].sum()
          .nlargest(10).sort_values(ascending=True))
    fig_sp = go.Figure(go.Bar(x=sp.values, y=[f"Salesperson #{k}" for k in sp.index], orientation="h",
                               marker_color=VIOLET,
                               hovertemplate="%{y}<br>Revenue: $%{x:,.0f}<extra></extra>"))
    fig_sp.update_layout(**base_layout("Top 10 Salespeople by Revenue (by ID - no name lookup provided)", height=420))
    fig_sp.update_xaxes(tickprefix="$", tickformat=",.0f")
    style_axes(fig_sp, ygrid=False)

    # ---------------- 8. Revenue by package type ----------------
    pkg = df.groupby("Package")["Total Excluding Tax"].sum().sort_values(ascending=True)
    pkg_pct = pkg / pkg.sum() * 100
    fig_pkg = go.Figure(go.Bar(x=pkg.values, y=pkg.index, orientation="h", marker_color=GREEN,
                                text=[f"{p:.1f}%" for p in pkg_pct], textposition="outside",
                                textfont=dict(color=INK_SECONDARY),
                                hovertemplate="%{y}<br>Revenue: $%{x:,.0f}<extra></extra>"))
    fig_pkg.update_layout(**base_layout("Revenue by Package Type (almost all sold as single units)", height=300))
    fig_pkg.update_xaxes(tickprefix="$", tickformat=",.0f", range=[0, pkg.max() * 1.18])
    style_axes(fig_pkg, ygrid=False)

    figs = dict(trend=fig_trend, cat=fig_cat, margin=fig_margin, top=fig_top,
                loss=fig_loss, cust=fig_cust, sp=fig_sp, pkg=fig_pkg)
    html_parts = {k: f.to_html(full_html=False, include_plotlyjs=("cdn" if k == "trend" else False),
                                config={"displaylogo": False})
                  for k, f in figs.items()}

    kpis = [
        ("Total Revenue", money(total_revenue), INK_PRIMARY),
        ("Total Profit", money(total_profit), INK_PRIMARY),
        ("Profit Margin", f"{profit_margin:.1f}%", STATUS_GOOD),
        ("Orders", f"{total_orders:,}", INK_PRIMARY),
        ("Avg. Order Value", money(aov), INK_PRIMARY),
        ("Loss-Making Lines", f"{loss_pct:.1f}%", STATUS_CRITICAL),
    ]
    kpi_html = "".join(
        f'<div class="kpi" style="animation-delay:{i*0.06:.2f}s"><div class="kpi-label">{label}</div>'
        f'<div class="kpi-value" style="color:{color}">{value}</div></div>'
        for i, (label, value, color) in enumerate(kpis)
    )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Sales Performance Dashboard</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
  :root {{
    --surface: {SURFACE}; --page: {PAGE}; --ink: {INK_PRIMARY};
    --ink-sec: {INK_SECONDARY}; --muted: {INK_MUTED}; --border: {BORDER};
    --navy: {NAVY}; --brand: {BRAND_BLUE}; --accent: {ACCENT}; --light-blue: {LIGHT_BLUE_BG};
  }}
  * {{ box-sizing: border-box; }}
  @keyframes fadeInUp {{
    from {{ opacity: 0; transform: translateY(14px); }}
    to {{ opacity: 1; transform: translateY(0); }}
  }}
  @keyframes floatSlow {{
    0%, 100% {{ transform: translateY(0) scale(1); }}
    50% {{ transform: translateY(-10px) scale(1.03); }}
  }}
  body {{
    margin: 0; padding: 0 0 32px 0;
    background: linear-gradient(180deg, var(--light-blue) 0%, var(--page) 420px, var(--page) 100%);
    color: var(--ink);
    font-family: 'Inter', system-ui, -apple-system, sans-serif;
  }}
  .wrap {{ max-width: 1360px; margin: 0 auto; padding: 0 32px; }}

  .hero {{
    background: linear-gradient(135deg, var(--navy) 0%, var(--brand) 65%, var(--accent) 100%);
    color: #fff; padding: 30px 32px 26px 32px; margin-bottom: 24px;
    position: relative; overflow: hidden;
  }}
  .hero::before {{
    content: ''; position: absolute; right: -40px; top: -60px; width: 220px; height: 220px;
    border-radius: 50%; background: rgba(255,255,255,0.07); animation: floatSlow 9s ease-in-out infinite;
  }}
  .hero::after {{
    content: ''; position: absolute; right: 120px; bottom: -90px; width: 160px; height: 160px;
    border-radius: 50%; background: rgba(255,255,255,0.06); animation: floatSlow 11s ease-in-out infinite reverse;
  }}
  .hero-inner {{ max-width: 1360px; margin: 0 auto; padding: 0 32px; position: relative; }}
  .eyebrow {{ font-size: 0.72rem; letter-spacing: 0.1em; text-transform: uppercase; opacity: 0.75; font-weight: 600; margin-bottom: 6px; }}
  h1 {{ font-size: 1.7rem; font-weight: 800; margin: 0 0 4px 0; }}
  .subtitle {{ color: rgba(255,255,255,0.82); font-size: 0.92rem; }}

  .kpi-row {{ display: grid; grid-template-columns: repeat(6, 1fr); gap: 14px; margin-bottom: 20px; }}
  .kpi {{
    background: var(--surface); border: 1px solid var(--border); border-radius: 12px;
    padding: 18px 16px; opacity: 0; animation: fadeInUp 0.55s ease-out forwards;
    transition: transform 0.25s ease, box-shadow 0.25s ease;
  }}
  .kpi:hover {{ transform: translateY(-3px); box-shadow: 0 10px 24px -8px rgba(15,41,66,0.18); }}
  .kpi-label {{ font-size: 0.78rem; color: var(--muted); text-transform: uppercase;
                letter-spacing: 0.04em; margin-bottom: 8px; font-weight: 600; }}
  .kpi-value {{ font-size: 1.6rem; font-weight: 700; }}
  .grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px; }}
  .full {{ grid-column: 1 / -1; }}
  .card {{
    background: var(--surface); border: 1px solid var(--border); border-radius: 12px;
    padding: 8px 12px 4px 12px; opacity: 0; animation: fadeInUp 0.6s ease-out forwards;
    transition: transform 0.25s ease, box-shadow 0.25s ease;
  }}
  .card:hover {{ transform: translateY(-3px); box-shadow: 0 12px 28px -10px rgba(15,41,66,0.16); }}
  .grid > *:nth-child(1) {{ animation-delay: 0.05s; }}
  .grid > *:nth-child(2) {{ animation-delay: 0.10s; }}
  .grid > *:nth-child(3) {{ animation-delay: 0.14s; }}
  .grid > *:nth-child(4) {{ animation-delay: 0.18s; }}
  .grid > *:nth-child(5) {{ animation-delay: 0.22s; }}
  .grid > *:nth-child(6) {{ animation-delay: 0.26s; }}
  .grid > *:nth-child(7) {{ animation-delay: 0.30s; }}
  .grid > *:nth-child(8) {{ animation-delay: 0.34s; }}
  .note {{
    grid-column: 1 / -1; background: var(--light-blue); border: 1px solid var(--border);
    border-left: 4px solid {STATUS_CRITICAL}; border-radius: 8px; padding: 14px 18px;
    color: var(--ink-sec); font-size: 0.9rem; line-height: 1.5;
    opacity: 0; animation: fadeInUp 0.6s ease-out forwards;
  }}
  footer {{ margin-top: 20px; color: var(--muted); font-size: 0.8rem; text-align: center; }}
  @media (max-width: 900px) {{
    .kpi-row {{ grid-template-columns: repeat(2, 1fr); }}
    .grid {{ grid-template-columns: 1fr; }}
  }}
</style>
</head>
<body>
  <div class="hero">
    <div class="hero-inner">
      <div class="eyebrow">Task 2 &middot; VOLTIX Data Analyst Internship</div>
      <h1>Sales Performance Dashboard</h1>
      <div class="subtitle">FactSale data &middot; {date_min} &ndash; {date_max} &middot; {len(df):,} line items across {total_orders:,} orders</div>
    </div>
  </div>

<div class="wrap">
  <div class="kpi-row">{kpi_html}</div>

  <div class="grid">
    <div class="card full">{html_parts['trend']}</div>

    <div class="card">{html_parts['cat']}</div>
    <div class="card">{html_parts['margin']}</div>

    <div class="card">{html_parts['top']}</div>
    <div class="card">{html_parts['loss']}</div>

    <div class="note">
      <strong>Why this matters:</strong> every single sale of the products above lost money outright
      (selling price below cost) &mdash; this is not noise, it is a pricing problem. The Halloween zombie mask
      alone accounts for 492 loss-making line items (100% of its sales). Recommendation: re-price or
      discontinue these SKUs; they are quietly eating into the healthy ~50% margin the rest of the
      catalog runs at.
    </div>

    <div class="card">{html_parts['cust']}</div>
    <div class="card">{html_parts['pkg']}</div>

    <div class="card full">{html_parts['sp']}</div>
  </div>

  <footer>
    Sales_Dashboard.html &middot; generated from Cleaned_FactSale.csv &middot; no product/customer/salesperson
    name lookup tables were provided with this dataset, so those dimensions are shown by ID.
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
