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

Kept deliberately plain: a simple blue KPI/chart grid, default system font,
plain bordered boxes. No custom typography pairing, no sparklines, no hover
copywriting - just the charts and the numbers.
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go

IN_PATH = "Cleaned_FactSale.csv"
OUT_PATH = "Sales_Dashboard.html"

# ---- simple blue palette ---------------------------------------------------
PAGE_BG = "#eef4fb"
CARD_BG = "#ffffff"
BORDER = "#c7dcf0"
INK = "#1c3d5a"
INK_SOFT = "#4d6e8c"

BLUE_LIGHT, BLUE, BLUE_DARK, BLUE_DEEP = "#5b9bd5", "#2e75b6", "#1c4e80", "#123456"
ORANGE, YELLOW = "#eb6834", "#eda100"
STATUS_GOOD = "#1e7a4a"
STATUS_CRITICAL = "#b5322f"

FONT = "Arial, Helvetica, sans-serif"
BASE_FONT = dict(family=FONT, color=INK, size=12.5)


def base_layout(title, height=360, legend=False):
    layout = dict(
        title=dict(text=title, font=dict(size=14, color=INK), x=0.01, xanchor="left"),
        paper_bgcolor=CARD_BG,
        plot_bgcolor=CARD_BG,
        font=BASE_FONT,
        margin=dict(t=44, l=48, r=20, b=40),
        height=height,
        hoverlabel=dict(bgcolor="white", font=dict(family=FONT, color=INK), bordercolor=BORDER),
        showlegend=legend,
    )
    if legend:
        layout["legend"] = dict(orientation="h", yanchor="bottom", y=1.0, xanchor="right", x=1,
                                 font=dict(color=INK_SOFT))
    return layout


def style_axes(fig, xgrid=False, ygrid=True):
    fig.update_xaxes(showgrid=xgrid, gridcolor="#e3edf7", linecolor=BORDER, tickfont=dict(color=INK_SOFT), zeroline=False)
    fig.update_yaxes(showgrid=ygrid, gridcolor="#e3edf7", linecolor=BORDER, tickfont=dict(color=INK_SOFT), zeroline=False)
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
                                    mode="lines", line=dict(color=BLUE, width=2.5),
                                    hovertemplate="%{x|%b %Y}<br>Revenue: $%{y:,.0f}<extra></extra>"))
    fig_trend.add_trace(go.Scatter(x=monthly["Month"], y=monthly["Profit"], name="Profit",
                                    mode="lines", line=dict(color=ORANGE, width=2.5),
                                    hovertemplate="%{x|%b %Y}<br>Profit: $%{y:,.0f}<extra></extra>"))
    fig_trend.update_layout(**base_layout("Monthly Revenue & Profit", height=360, legend=True))
    fig_trend.update_yaxes(tickprefix="$", tickformat=",.0f")
    style_axes(fig_trend)

    # ---------------- 2. Revenue by product category ----------------
    cat = df.groupby("Product_Category")["Total Excluding Tax"].sum().sort_values(ascending=True)
    fig_cat = go.Figure(go.Bar(x=cat.values, y=cat.index, orientation="h", marker_color=BLUE,
                                hovertemplate="%{y}<br>Revenue: $%{x:,.0f}<extra></extra>"))
    fig_cat.update_layout(**base_layout("Revenue by Product Category", height=360))
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
    fig_margin.update_layout(**base_layout("Profit Margin % by Category", height=360))
    fig_margin.update_xaxes(ticksuffix="%")
    style_axes(fig_margin, ygrid=False)

    # ---------------- 4. Top 10 products by revenue ----------------
    top_products = (df.groupby("Description")["Total Excluding Tax"].sum()
                     .nlargest(10).sort_values(ascending=True))
    fig_top = go.Figure(go.Bar(x=top_products.values, y=top_products.index, orientation="h",
                                marker_color=BLUE_LIGHT,
                                hovertemplate="%{y}<br>Revenue: $%{x:,.0f}<extra></extra>"))
    fig_top.update_layout(**base_layout("Top 10 Products by Revenue", height=400))
    fig_top.update_xaxes(tickprefix="$", tickformat=",.0f")
    style_axes(fig_top, ygrid=False)

    # ---------------- 5. Loss-making products (the actionable finding) ----------------
    loss = df[df["Is_Loss_Making"]].groupby("Description").agg(
        Loss=("Profit", "sum"), Units=("Quantity", "sum")
    ).nsmallest(10, "Loss").sort_values("Loss", ascending=False)
    fig_loss = go.Figure(go.Bar(x=loss["Loss"], y=loss.index, orientation="h", marker_color=STATUS_CRITICAL,
                                 hovertemplate="%{y}<br>Total loss: $%{x:,.0f}<extra></extra>"))
    fig_loss.update_layout(**base_layout("Biggest Loss-Making Products", height=400))
    fig_loss.update_xaxes(tickprefix="$", tickformat=",.0f")
    style_axes(fig_loss, ygrid=False)

    # ---------------- 6. Customer type split ----------------
    cust = df.groupby("Customer_Type")["Total Excluding Tax"].sum()
    fig_cust = go.Figure(go.Pie(labels=cust.index, values=cust.values, hole=0.5,
                                 marker=dict(colors=[BLUE, YELLOW], line=dict(color=CARD_BG, width=2)),
                                 hovertemplate="%{label}<br>$%{value:,.0f} (%{percent})<extra></extra>",
                                 textinfo="percent", textfont=dict(color="white", size=13)))
    fig_cust.update_layout(**base_layout("Registered vs. Unknown/Walk-in Revenue", height=340, legend=True))

    # ---------------- 7. Top salespeople ----------------
    sp = (df.groupby("Salesperson Key")["Total Excluding Tax"].sum()
          .nlargest(10).sort_values(ascending=True))
    fig_sp = go.Figure(go.Bar(x=sp.values, y=[f"Salesperson #{k}" for k in sp.index], orientation="h",
                               marker_color=BLUE_DARK,
                               hovertemplate="%{y}<br>Revenue: $%{x:,.0f}<extra></extra>"))
    fig_sp.update_layout(**base_layout("Top 10 Salespeople by Revenue (by ID)", height=400))
    fig_sp.update_xaxes(tickprefix="$", tickformat=",.0f")
    style_axes(fig_sp, ygrid=False)

    # ---------------- 8. Revenue by package type ----------------
    pkg = df.groupby("Package")["Total Excluding Tax"].sum().sort_values(ascending=True)
    pkg_pct = pkg / pkg.sum() * 100
    fig_pkg = go.Figure(go.Bar(x=pkg.values, y=pkg.index, orientation="h", marker_color=BLUE_LIGHT,
                                text=[f"{p:.1f}%" for p in pkg_pct], textposition="outside",
                                textfont=dict(color=INK_SOFT),
                                hovertemplate="%{y}<br>Revenue: $%{x:,.0f}<extra></extra>"))
    fig_pkg.update_layout(**base_layout("Revenue by Package Type", height=300))
    fig_pkg.update_xaxes(tickprefix="$", tickformat=",.0f", range=[0, pkg.max() * 1.18])
    style_axes(fig_pkg, ygrid=False)

    figs = dict(trend=fig_trend, cat=fig_cat, margin=fig_margin, top=fig_top,
                loss=fig_loss, cust=fig_cust, sp=fig_sp, pkg=fig_pkg)
    html_parts = {k: f.to_html(full_html=False, include_plotlyjs=("cdn" if k == "trend" else False),
                                config={"displaylogo": False})
                  for k, f in figs.items()}

    kpis = [
        ("Total Revenue", money(total_revenue), INK),
        ("Total Profit", money(total_profit), INK),
        ("Profit Margin", f"{profit_margin:.1f}%", STATUS_GOOD),
        ("Orders", f"{total_orders:,}", INK),
        ("Avg. Order Value", money(aov), INK),
        ("Loss-Making Lines", f"{loss_pct:.1f}%", STATUS_CRITICAL),
    ]
    kpi_html = "".join(
        f'<div class="kpi"><div class="kpi-label">{label}</div>'
        f'<div class="kpi-value" style="color:{color}">{value}</div></div>'
        for label, value, color in kpis
    )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Sales Performance Dashboard</title>
<style>
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0; padding: 24px; background: {PAGE_BG}; color: {INK};
    font-family: {FONT};
  }}
  .wrap {{ max-width: 1280px; margin: 0 auto; }}
  h1 {{ font-size: 1.5rem; font-weight: bold; margin: 0 0 4px 0; color: {BLUE_DEEP}; }}
  .subtitle {{ color: {INK_SOFT}; font-size: 0.9rem; margin-bottom: 18px; }}

  .kpi-row {{ display: grid; grid-template-columns: repeat(6, 1fr); gap: 12px; margin-bottom: 16px; }}
  .kpi {{
    background: {CARD_BG}; border: 1px solid {BORDER}; border-radius: 6px;
    padding: 14px 12px; text-align: center;
  }}
  .kpi-label {{ font-size: 0.72rem; color: {INK_SOFT}; margin-bottom: 6px; }}
  .kpi-value {{ font-size: 1.35rem; font-weight: bold; }}

  .grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 14px; }}
  .full {{ grid-column: 1 / -1; }}
  .card {{
    background: {CARD_BG}; border: 1px solid {BORDER}; border-radius: 6px; padding: 6px 10px 2px 10px;
  }}
  .note {{
    grid-column: 1 / -1; background: {CARD_BG}; border: 1px solid {BORDER}; border-left: 4px solid {STATUS_CRITICAL};
    border-radius: 4px; padding: 12px 16px; font-size: 0.88rem; color: {INK}; line-height: 1.5;
  }}
  footer {{ margin-top: 16px; color: {INK_SOFT}; font-size: 0.78rem; text-align: center; }}
  @media (max-width: 900px) {{
    .kpi-row {{ grid-template-columns: repeat(2, 1fr); }}
    .grid {{ grid-template-columns: 1fr; }}
  }}
</style>
</head>
<body>
<div class="wrap">
  <h1>Sales Performance Dashboard</h1>
  <div class="subtitle">Task 2 &mdash; FactSale data, {date_min} to {date_max} &middot; {len(df):,} line items, {total_orders:,} orders &middot; Nahla Nabil, VOLTIX Data Analyst Internship</div>

  <div class="kpi-row">{kpi_html}</div>

  <div class="grid">
    <div class="card full">{html_parts['trend']}</div>

    <div class="card">{html_parts['cat']}</div>
    <div class="card">{html_parts['margin']}</div>

    <div class="card">{html_parts['top']}</div>
    <div class="card">{html_parts['loss']}</div>

    <div class="note">
      <strong>Worth flagging:</strong> the Halloween zombie mask sold 492 times and lost money all 492 times.
      The almost-identical skull mask makes about 17% margin, so this looks like one SKU with the wrong price,
      not a bad product. A few USB novelty drives have the same problem on a smaller scale. Fixing the price
      (or dropping the SKU) recovers real money without any new sales.
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
