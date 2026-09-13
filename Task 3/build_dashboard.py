"""
Task 3 - HR Employee Attrition: Interactive Dashboard

Builds HR_Attrition_Dashboard.html from Cleaned_HR_Attrition.csv, covering
every angle the task asks for:
  - Headcount & attrition by department / job role
  - Salary by job level & experience
  - Satisfaction levels (overall + stayed vs left)
  - Attrition drivers: OverTime, Job Satisfaction, Work-Life Balance,
    Business Travel, Marital Status, Age, Tenure

Same plain blue KPI/chart-grid style as the Task 2 dashboard: default
system font, plain bordered cards, no decorative styling.
"""

import pandas as pd
import plotly.graph_objects as go

IN_PATH = "Cleaned_HR_Attrition.csv"
OUT_PATH = "HR_Attrition_Dashboard.html"

# ---- simple blue palette (matches Task 2) ----------------------------------
PAGE_BG = "#eef4fb"
CARD_BG = "#ffffff"
BORDER = "#c7dcf0"
INK = "#1c3d5a"
INK_SOFT = "#4d6e8c"

BLUE_LIGHT, BLUE, BLUE_DARK, BLUE_DEEP = "#5b9bd5", "#2e75b6", "#1c4e80", "#123456"
ORANGE = "#eb6834"
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
    df = pd.read_csv(IN_PATH)

    # ---------------- KPIs ----------------
    n = len(df)
    attr_rate = df["AttritionFlag"].mean() * 100
    avg_income = df["MonthlyIncome"].mean()
    avg_jobsat = df["JobSatisfaction"].mean()
    pct_overtime = (df["OverTime"] == "Yes").mean() * 100
    avg_tenure = df["YearsAtCompany"].mean()

    # ---------------- 1. Attrition rate by department ----------------
    dept = df.groupby("Department").agg(Headcount=("EmployeeNumber", "count"),
                                         AttritionRate=("AttritionFlag", "mean")).reset_index()
    dept["AttritionRate"] *= 100
    dept = dept.sort_values("AttritionRate")
    fig_dept = go.Figure(go.Bar(x=dept["AttritionRate"], y=dept["Department"], orientation="h",
                                 marker_color=BLUE,
                                 text=[f"{v:.1f}% ({h} people)" for v, h in zip(dept["AttritionRate"], dept["Headcount"])],
                                 textposition="outside", textfont=dict(color=INK_SOFT),
                                 hovertemplate="%{y}<br>Attrition rate: %{x:.1f}%<extra></extra>"))
    fig_dept.update_layout(**base_layout("Attrition Rate by Department", height=280))
    fig_dept.update_xaxes(ticksuffix="%", range=[0, dept["AttritionRate"].max() * 1.35])
    style_axes(fig_dept, ygrid=False)

    # ---------------- 2. Attrition rate by job role ----------------
    role = df.groupby("JobRole").agg(Headcount=("EmployeeNumber", "count"),
                                      AttritionRate=("AttritionFlag", "mean")).reset_index()
    role["AttritionRate"] *= 100
    role = role.sort_values("AttritionRate")
    colors_role = [STATUS_CRITICAL if v >= 20 else BLUE for v in role["AttritionRate"]]
    fig_role = go.Figure(go.Bar(x=role["AttritionRate"], y=role["JobRole"], orientation="h",
                                 marker_color=colors_role,
                                 hovertemplate="%{y}<br>Attrition rate: %{x:.1f}%<extra></extra>"))
    fig_role.update_layout(**base_layout("Attrition Rate by Job Role", height=420))
    fig_role.update_xaxes(ticksuffix="%")
    style_axes(fig_role, ygrid=False)

    # ---------------- 3. Headcount by department (donut) ----------------
    dept_hc = df["Department"].value_counts()
    fig_hc = go.Figure(go.Pie(labels=dept_hc.index, values=dept_hc.values, hole=0.5,
                               marker=dict(colors=[BLUE, BLUE_LIGHT, BLUE_DARK], line=dict(color=CARD_BG, width=2)),
                               hovertemplate="%{label}<br>%{value} employees (%{percent})<extra></extra>",
                               textinfo="percent", textfont=dict(color="white", size=13)))
    fig_hc.update_layout(**base_layout("Headcount by Department", height=320, legend=True))

    # ---------------- 4. Salary by job level ----------------
    lvl = df.groupby("JobLevel").agg(AvgIncome=("MonthlyIncome", "mean")).reset_index()
    fig_lvl = go.Figure(go.Bar(x=lvl["JobLevel"].astype(str), y=lvl["AvgIncome"], marker_color=BLUE_DARK,
                                hovertemplate="Job Level %{x}<br>Avg income: $%{y:,.0f}<extra></extra>"))
    fig_lvl.update_layout(**base_layout("Average Monthly Income by Job Level", height=320))
    fig_lvl.update_yaxes(tickprefix="$", tickformat=",.0f")
    fig_lvl.update_xaxes(title="Job Level")
    style_axes(fig_lvl)

    # ---------------- 5. Satisfaction: stayed vs left ----------------
    sat_cols = ["JobSatisfaction", "EnvironmentSatisfaction", "RelationshipSatisfaction", "WorkLifeBalance"]
    sat_by_attr = df.groupby("Attrition")[sat_cols].mean()
    fig_sat = go.Figure()
    fig_sat.add_trace(go.Bar(name="Stayed", x=sat_cols, y=sat_by_attr.loc["No"], marker_color=BLUE,
                              hovertemplate="%{x}<br>Stayed avg: %{y:.2f}<extra></extra>"))
    fig_sat.add_trace(go.Bar(name="Left", x=sat_cols, y=sat_by_attr.loc["Yes"], marker_color=STATUS_CRITICAL,
                              hovertemplate="%{x}<br>Left avg: %{y:.2f}<extra></extra>"))
    fig_sat.update_layout(**base_layout("Satisfaction Scores (1-4): Stayed vs. Left", height=360, legend=True))
    fig_sat.update_layout(barmode="group")
    fig_sat.update_yaxes(range=[0, 4])
    style_axes(fig_sat)

    # ---------------- 6. Attrition by OverTime ----------------
    ot = df.groupby("OverTime")["AttritionFlag"].mean().reset_index()
    ot["AttritionFlag"] *= 100
    fig_ot = go.Figure(go.Bar(x=ot["OverTime"], y=ot["AttritionFlag"],
                               marker_color=[BLUE, STATUS_CRITICAL],
                               text=[f"{v:.1f}%" for v in ot["AttritionFlag"]], textposition="outside",
                               textfont=dict(color=INK_SOFT),
                               hovertemplate="Overtime: %{x}<br>Attrition rate: %{y:.1f}%<extra></extra>"))
    fig_ot.update_layout(**base_layout("Attrition Rate by OverTime", height=320))
    fig_ot.update_yaxes(ticksuffix="%", range=[0, 40])
    style_axes(fig_ot, ygrid=True)

    # ---------------- 7. Attrition by Job Satisfaction ----------------
    js = df.groupby("JobSatisfaction")["AttritionFlag"].mean().reset_index()
    js["AttritionFlag"] *= 100
    fig_js = go.Figure(go.Bar(x=js["JobSatisfaction"].astype(str), y=js["AttritionFlag"], marker_color=BLUE,
                               hovertemplate="Job satisfaction %{x}<br>Attrition rate: %{y:.1f}%<extra></extra>"))
    fig_js.update_layout(**base_layout("Attrition Rate by Job Satisfaction (1=Low, 4=Very High)", height=320))
    fig_js.update_yaxes(ticksuffix="%")
    fig_js.update_xaxes(title="Job Satisfaction Level")
    style_axes(fig_js)

    # ---------------- 8. Attrition by Work-Life Balance ----------------
    wlb = df.groupby("WorkLifeBalance")["AttritionFlag"].mean().reset_index()
    wlb["AttritionFlag"] *= 100
    fig_wlb = go.Figure(go.Bar(x=wlb["WorkLifeBalance"].astype(str), y=wlb["AttritionFlag"], marker_color=BLUE,
                                hovertemplate="Work-life balance %{x}<br>Attrition rate: %{y:.1f}%<extra></extra>"))
    fig_wlb.update_layout(**base_layout("Attrition Rate by Work-Life Balance (1=Bad, 4=Best)", height=320))
    fig_wlb.update_yaxes(ticksuffix="%")
    fig_wlb.update_xaxes(title="Work-Life Balance Level")
    style_axes(fig_wlb)

    # ---------------- 9. Attrition by Business Travel ----------------
    bt = df.groupby("BusinessTravel")["AttritionFlag"].mean().reset_index()
    bt["AttritionFlag"] *= 100
    bt = bt.sort_values("AttritionFlag")
    fig_bt = go.Figure(go.Bar(x=bt["AttritionFlag"], y=bt["BusinessTravel"], orientation="h", marker_color=BLUE_LIGHT,
                               hovertemplate="%{y}<br>Attrition rate: %{x:.1f}%<extra></extra>"))
    fig_bt.update_layout(**base_layout("Attrition Rate by Business Travel", height=280))
    fig_bt.update_xaxes(ticksuffix="%")
    style_axes(fig_bt, ygrid=False)

    # ---------------- 10. Attrition by Age Group & Tenure Band ----------------
    age_order = ["18-25", "26-35", "36-45", "46-55", "56-60"]
    ag = df.groupby("AgeGroup", observed=True)["AttritionFlag"].mean().reindex(age_order) * 100
    fig_age = go.Figure(go.Bar(x=ag.index, y=ag.values, marker_color=BLUE_DARK,
                                hovertemplate="Age %{x}<br>Attrition rate: %{y:.1f}%<extra></extra>"))
    fig_age.update_layout(**base_layout("Attrition Rate by Age Group", height=320))
    fig_age.update_yaxes(ticksuffix="%")
    style_axes(fig_age)

    tenure_order = ["0-2 yrs", "3-5 yrs", "6-10 yrs", "11-20 yrs", "20+ yrs"]
    tb = df.groupby("TenureBand", observed=True)["AttritionFlag"].mean().reindex(tenure_order) * 100
    fig_ten = go.Figure(go.Bar(x=tb.index, y=tb.values, marker_color=ORANGE,
                                hovertemplate="Tenure %{x}<br>Attrition rate: %{y:.1f}%<extra></extra>"))
    fig_ten.update_layout(**base_layout("Attrition Rate by Tenure at Company", height=320))
    fig_ten.update_yaxes(ticksuffix="%")
    style_axes(fig_ten)

    # ---------------- 11. Attrition by Marital Status ----------------
    ms = df.groupby("MaritalStatus")["AttritionFlag"].mean().reset_index()
    ms["AttritionFlag"] *= 100
    ms = ms.sort_values("AttritionFlag")
    fig_ms = go.Figure(go.Bar(x=ms["AttritionFlag"], y=ms["MaritalStatus"], orientation="h", marker_color=BLUE_LIGHT,
                               hovertemplate="%{y}<br>Attrition rate: %{x:.1f}%<extra></extra>"))
    fig_ms.update_layout(**base_layout("Attrition Rate by Marital Status", height=260))
    fig_ms.update_xaxes(ticksuffix="%")
    style_axes(fig_ms, ygrid=False)

    figs = dict(dept=fig_dept, role=fig_role, hc=fig_hc, lvl=fig_lvl, sat=fig_sat,
                ot=fig_ot, js=fig_js, wlb=fig_wlb, bt=fig_bt, age=fig_age, ten=fig_ten, ms=fig_ms)
    html_parts = {k: f.to_html(full_html=False, include_plotlyjs=("cdn" if k == "dept" else False),
                                config={"displaylogo": False})
                  for k, f in figs.items()}

    kpis = [
        ("Total Employees", f"{n:,}", INK),
        ("Attrition Rate", f"{attr_rate:.1f}%", STATUS_CRITICAL),
        ("Avg. Monthly Income", money(avg_income), INK),
        ("Avg. Job Satisfaction", f"{avg_jobsat:.2f} / 4", INK),
        ("Work Overtime", f"{pct_overtime:.1f}%", ORANGE),
        ("Avg. Tenure", f"{avg_tenure:.1f} yrs", INK),
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
<title>HR Employee Attrition Dashboard</title>
<style>
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0; padding: 24px; background: {PAGE_BG}; color: {INK};
    font-family: {FONT};
  }}
  .wrap {{ max-width: 1280px; margin: 0 auto; }}
  h1 {{ font-size: 1.5rem; font-weight: bold; margin: 0 0 4px 0; color: {BLUE_DEEP}; }}
  h2 {{ font-size: 1.05rem; font-weight: bold; margin: 20px 0 8px 2px; color: {BLUE_DEEP}; }}
  .subtitle {{ color: {INK_SOFT}; font-size: 0.9rem; margin-bottom: 18px; }}

  .kpi-row {{ display: grid; grid-template-columns: repeat(6, 1fr); gap: 12px; margin-bottom: 8px; }}
  .kpi {{
    background: {CARD_BG}; border: 1px solid {BORDER}; border-radius: 6px;
    padding: 14px 12px; text-align: center;
  }}
  .kpi-label {{ font-size: 0.72rem; color: {INK_SOFT}; margin-bottom: 6px; }}
  .kpi-value {{ font-size: 1.35rem; font-weight: bold; }}

  .grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 14px; }}
  .grid3 {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; }}
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
    .grid3 {{ grid-template-columns: 1fr; }}
  }}
</style>
</head>
<body>
<div class="wrap">
  <h1>HR Employee Attrition Dashboard</h1>
  <div class="subtitle">Task 3 &mdash; IBM HR Analytics dataset, {n:,} employees &middot; Nahla Nabil, VOLTIX Data Analyst Internship</div>

  <div class="kpi-row">{kpi_html}</div>

  <h2>Departments &amp; Job Roles</h2>
  <div class="grid3">
    <div class="card">{html_parts['dept']}</div>
    <div class="card">{html_parts['hc']}</div>
    <div class="card">{html_parts['lvl']}</div>
    <div class="card full">{html_parts['role']}</div>
  </div>

  <h2>Satisfaction</h2>
  <div class="grid">
    <div class="card full">{html_parts['sat']}</div>
  </div>

  <h2>Attrition Drivers</h2>
  <div class="note">
    <strong>Worth flagging:</strong> employees who work overtime leave nearly 3x as often as those who
    don't (30.5% vs 10.4%). Combined with low job satisfaction, poor work-life balance, frequent travel,
    being single, and being new (0-2 years tenure), these are the clearest attrition risk signals in the
    data &mdash; and the ones HR can actually act on (workload/overtime policy, onboarding support for new
    hires, travel load management).
  </div>
  <div class="grid3">
    <div class="card">{html_parts['ot']}</div>
    <div class="card">{html_parts['js']}</div>
    <div class="card">{html_parts['wlb']}</div>
    <div class="card">{html_parts['bt']}</div>
    <div class="card">{html_parts['ms']}</div>
    <div class="card">{html_parts['age']}</div>
    <div class="card full">{html_parts['ten']}</div>
  </div>

  <footer>
    HR_Attrition_Dashboard.html &middot; generated from Cleaned_HR_Attrition.csv &middot;
    a full interactive Power BI (.pbix) build using the same measures is described in Power_BI_Guide.md.
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
