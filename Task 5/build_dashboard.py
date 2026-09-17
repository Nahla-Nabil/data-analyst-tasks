"""
Task 5 - Titanic Survival: Interactive Dashboard (Python only, Plotly)

Builds Titanic_Dashboard.html from Cleaned_Titanic.csv. Every chart is
interactive (hover tooltips, zoom/pan, legend toggling) and the top scatter
chart adds a dropdown filter by Sex, built entirely with Plotly - no other
BI tool is used anywhere in this task.

Same plain blue KPI/chart-grid style as the Task 2/3 dashboards.
"""

import pandas as pd
import plotly.graph_objects as go

IN_PATH = "Cleaned_Titanic.csv"
OUT_PATH = "Titanic_Dashboard.html"

# ---- simple blue palette (matches Task 2/3) --------------------------------
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


def build():
    df = pd.read_csv(IN_PATH)
    age_order = ["Child (0-12)", "Teen (13-18)", "Young Adult (19-35)", "Adult (36-60)", "Senior (60+)"]
    class_order = ["1st Class", "2nd Class", "3rd Class"]

    # ---------------- KPIs ----------------
    n = len(df)
    surv_rate = df["Survived"].mean() * 100
    avg_age = df["Age"].mean()
    avg_fare = df["Fare"].mean()
    pct_alone = df["IsAlone"].mean() * 100
    pct_cabin = df["HasCabin"].mean() * 100

    # ---------------- 1. Survival rate by Sex ----------------
    sx = df.groupby("Sex", observed=True)["Survived"].mean().reset_index()
    sx["Survived"] *= 100
    fig_sex = go.Figure(go.Bar(x=sx["Sex"], y=sx["Survived"], marker_color=[ORANGE, BLUE],
                                text=[f"{v:.1f}%" for v in sx["Survived"]], textposition="outside",
                                textfont=dict(color=INK_SOFT),
                                hovertemplate="%{x}<br>Survival rate: %{y:.1f}%<extra></extra>"))
    fig_sex.update_layout(**base_layout("\"Survival Rate\" by Sex ⚠ tautological by construction", height=320))
    fig_sex.update_yaxes(ticksuffix="%", range=[0, 100])
    style_axes(fig_sex)

    # ---------------- 2. Survived vs Not (donut) ----------------
    counts = df["Survived"].map({1: "Survived", 0: "Did Not Survive"}).value_counts()
    fig_donut = go.Figure(go.Pie(labels=counts.index, values=counts.values, hole=0.55,
                                  marker=dict(colors=[STATUS_CRITICAL, BLUE], line=dict(color=CARD_BG, width=2)),
                                  hovertemplate="%{label}<br>%{value} passengers (%{percent})<extra></extra>",
                                  textinfo="percent", textfont=dict(color="white", size=13)))
    fig_donut.update_layout(**base_layout("Overall Survival Outcome", height=320, legend=True))

    # ---------------- 3. Survival rate by Class ----------------
    cl = df.groupby("ClassLabel", observed=True)["Survived"].mean().reindex(class_order) * 100
    fig_class = go.Figure(go.Bar(x=cl.index, y=cl.values, marker_color=BLUE_DARK,
                                  text=[f"{v:.1f}%" for v in cl.values], textposition="outside",
                                  textfont=dict(color=INK_SOFT),
                                  hovertemplate="%{x}<br>Survival rate: %{y:.1f}%<extra></extra>"))
    fig_class.update_layout(**base_layout("\"Survival Rate\" by Class (= % female per class)", height=320))
    fig_class.update_yaxes(ticksuffix="%", range=[0, 100])
    style_axes(fig_class)

    # ---------------- 4. Age distribution: survived vs not (overlaid histogram) ----------------
    fig_age_hist = go.Figure()
    fig_age_hist.add_trace(go.Histogram(x=df.loc[df["Survived"] == 0, "Age"], name="Did Not Survive",
                                         marker_color=STATUS_CRITICAL, opacity=0.65, nbinsx=30,
                                         hovertemplate="Age %{x}<br>Count: %{y}<extra></extra>"))
    fig_age_hist.add_trace(go.Histogram(x=df.loc[df["Survived"] == 1, "Age"], name="Survived",
                                         marker_color=BLUE, opacity=0.65, nbinsx=30,
                                         hovertemplate="Age %{x}<br>Count: %{y}<extra></extra>"))
    fig_age_hist.update_layout(**base_layout("Age Distribution by Survival", height=360, legend=True))
    fig_age_hist.update_layout(barmode="overlay")
    fig_age_hist.update_xaxes(title="Age")
    style_axes(fig_age_hist)

    # ---------------- 5. Survival rate by Age Group ----------------
    ag = df.groupby("AgeGroup", observed=True)["Survived"].mean().reindex(age_order) * 100
    fig_agegrp = go.Figure(go.Bar(x=ag.index, y=ag.values, marker_color=BLUE,
                                   hovertemplate="%{x}<br>Survival rate: %{y:.1f}%<extra></extra>"))
    fig_agegrp.update_layout(**base_layout("\"Survival Rate\" by Age Group (= % female per group)", height=320))
    fig_agegrp.update_yaxes(ticksuffix="%")
    style_axes(fig_agegrp)

    # ---------------- 6. Survival rate by Family Size ----------------
    fam = df.groupby("FamilySize")["Survived"].mean().reset_index()
    fam["Survived"] *= 100
    fig_fam = go.Figure(go.Scatter(x=fam["FamilySize"], y=fam["Survived"], mode="lines+markers",
                                    line=dict(color=BLUE_DARK, width=2), marker=dict(size=8, color=ORANGE),
                                    hovertemplate="Family size %{x}<br>Survival rate: %{y:.1f}%<extra></extra>"))
    fig_fam.update_layout(**base_layout("\"Survival Rate\" by Family Size (= % female per group)", height=320))
    fig_fam.update_yaxes(ticksuffix="%")
    fig_fam.update_xaxes(title="Family Size (self + siblings/spouse + parents/children)")
    style_axes(fig_fam)

    # ---------------- 7. Survival rate by Embarkation Port ----------------
    port_names = {"C": "Cherbourg", "Q": "Queenstown", "S": "Southampton"}
    emb = df.groupby("Embarked", observed=True)["Survived"].mean().reset_index()
    emb["Survived"] *= 100
    emb["Port"] = emb["Embarked"].map(port_names)
    emb = emb.sort_values("Survived")
    fig_emb = go.Figure(go.Bar(x=emb["Survived"], y=emb["Port"], orientation="h", marker_color=BLUE_LIGHT,
                                hovertemplate="%{y}<br>Survival rate: %{x:.1f}%<extra></extra>"))
    fig_emb.update_layout(**base_layout("\"Survival Rate\" by Port (= % female per port)", height=280))
    fig_emb.update_xaxes(ticksuffix="%")
    style_axes(fig_emb, ygrid=False)

    # ---------------- 8. Fare distribution by class (box) ----------------
    fig_fare = go.Figure()
    for cls, color in zip(class_order, [BLUE_LIGHT, BLUE, BLUE_DARK]):
        fig_fare.add_trace(go.Box(y=df.loc[df["ClassLabel"] == cls, "Fare"], name=cls, marker_color=color,
                                   boxmean=True))
    fig_fare.update_layout(**base_layout("Fare Distribution by Class", height=360))
    fig_fare.update_yaxes(title="Fare ($)", tickprefix="$")
    style_axes(fig_fare)

    # ---------------- 9. Survival rate by Title ----------------
    ttl = df.groupby("Title")["Survived"].agg(["mean", "count"]).reset_index()
    ttl["mean"] *= 100
    ttl = ttl[ttl["count"] >= 5].sort_values("mean")
    fig_title = go.Figure(go.Bar(x=ttl["mean"], y=ttl["Title"], orientation="h", marker_color=BLUE,
                                  text=[f"n={c}" for c in ttl["count"]], textposition="outside",
                                  textfont=dict(color=INK_SOFT),
                                  hovertemplate="%{y}<br>Survival rate: %{x:.1f}%<extra></extra>"))
    fig_title.update_layout(**base_layout("\"Survival Rate\" by Title (≈ sex; Mr/Master=male, Miss/Mrs=female)", height=320))
    fig_title.update_xaxes(ticksuffix="%", range=[0, 115])
    style_axes(fig_title, ygrid=False)

    # ---------------- 10. Sunburst: Class -> Sex -> Outcome ----------------
    sb = df.copy()
    sb["Outcome"] = sb["Survived"].map({1: "Survived", 0: "Did Not Survive"})
    fig_sun = go.Figure(go.Sunburst(
        labels=None, parents=None,
        ids=None,
    ))
    # build sunburst via px-style manual aggregation (graph_objects only)
    import itertools
    labels, parents, values, colors = [], [], [], []
    labels.append("All Passengers"); parents.append(""); values.append(n); colors.append(BLUE_DEEP)
    for cls in class_order:
        sub = sb[sb["ClassLabel"] == cls]
        labels.append(cls); parents.append("All Passengers"); values.append(len(sub)); colors.append(BLUE_DARK)
        for sex in ["male", "female"]:
            sub2 = sub[sub["Sex"] == sex]
            lbl = f"{cls} - {sex}"
            labels.append(lbl); parents.append(cls); values.append(len(sub2)); colors.append(BLUE)
            for outcome, color in [("Survived", STATUS_GOOD), ("Did Not Survive", STATUS_CRITICAL)]:
                sub3 = sub2[sub2["Outcome"] == outcome]
                labels.append(f"{lbl} - {outcome}"); parents.append(lbl); values.append(len(sub3)); colors.append(color)
    fig_sun = go.Figure(go.Sunburst(labels=labels, parents=parents, values=values,
                                     branchvalues="total", marker=dict(colors=colors),
                                     hovertemplate="%{label}<br>%{value} passengers<extra></extra>"))
    fig_sun.update_layout(**base_layout("Class → Sex → \"Outcome\" (Outcome = Sex; click to drill down)", height=460))

    # ---------------- 11. Age vs Fare scatter with Sex dropdown filter ----------------
    male = df[df["Sex"] == "male"]
    female = df[df["Sex"] == "female"]

    def scatter_trace(sub, visible):
        return go.Scatter(
            x=sub["Age"], y=sub["Fare"], mode="markers", visible=visible,
            marker=dict(size=8, color=sub["Survived"].map({1: BLUE, 0: STATUS_CRITICAL}),
                        line=dict(width=0.5, color="white"), opacity=0.75),
            text=sub["Survived"].map({1: "Survived", 0: "Did Not Survive"}),
            customdata=sub["ClassLabel"],
            hovertemplate="Age %{x}<br>Fare $%{y:.2f}<br>%{text}<br>%{customdata}<extra></extra>",
            showlegend=False,
        )

    fig_scatter = go.Figure()
    fig_scatter.add_trace(scatter_trace(df, True))
    fig_scatter.add_trace(scatter_trace(male, False))
    fig_scatter.add_trace(scatter_trace(female, False))
    fig_scatter.update_layout(**base_layout("Age vs Fare (color = \"outcome\" ≈ sex) — filter by sex", height=420))
    fig_scatter.update_xaxes(title="Age")
    fig_scatter.update_yaxes(title="Fare ($)", tickprefix="$")
    style_axes(fig_scatter)
    fig_scatter.update_layout(
        updatemenus=[dict(
            type="dropdown", direction="down", x=1.0, xanchor="right", y=1.18, yanchor="top",
            bgcolor=CARD_BG, bordercolor=BORDER, font=dict(color=INK, size=11),
            buttons=[
                dict(label="All Passengers", method="update", args=[{"visible": [True, False, False]}]),
                dict(label="Male Only", method="update", args=[{"visible": [False, True, False]}]),
                dict(label="Female Only", method="update", args=[{"visible": [False, False, True]}]),
            ],
        )]
    )
    # legend proxy for red/blue meaning
    fig_scatter.add_trace(go.Scatter(x=[None], y=[None], mode="markers", marker=dict(color=BLUE, size=9),
                                      name="Survived", showlegend=True))
    fig_scatter.add_trace(go.Scatter(x=[None], y=[None], mode="markers", marker=dict(color=STATUS_CRITICAL, size=9),
                                      name="Did Not Survive", showlegend=True))
    fig_scatter.update_layout(showlegend=True,
                               legend=dict(orientation="h", yanchor="bottom", y=1.0, xanchor="left", x=0,
                                           font=dict(color=INK_SOFT)))

    # ---------------- 12. Correlation heatmap ----------------
    num_cols = ["Survived", "Pclass", "Age", "SibSp", "Parch", "Fare", "FamilySize", "HasCabin"]
    corr = df[num_cols].corr().round(2)
    fig_corr = go.Figure(go.Heatmap(z=corr.values, x=corr.columns, y=corr.columns,
                                     colorscale=[[0, STATUS_CRITICAL], [0.5, "#ffffff"], [1, BLUE_DARK]],
                                     zmid=0, zmin=-1, zmax=1,
                                     text=corr.values, texttemplate="%{text}", textfont=dict(size=10),
                                     hovertemplate="%{x} vs %{y}: %{z}<extra></extra>",
                                     colorbar=dict(title="corr")))
    fig_corr.update_layout(**base_layout("Correlation Heatmap (numeric features)", height=420))
    fig_corr.update_yaxes(autorange="reversed")

    figs = dict(sex=fig_sex, donut=fig_donut, cls=fig_class, agehist=fig_age_hist, agegrp=fig_agegrp,
                fam=fig_fam, emb=fig_emb, fare=fig_fare, title=fig_title, sun=fig_sun,
                scatter=fig_scatter, corr=fig_corr)
    html_parts = {k: f.to_html(full_html=False, include_plotlyjs=("cdn" if k == "sex" else False),
                                config={"displaylogo": False})
                  for k, f in figs.items()}

    def money(x):
        return f"${x:,.0f}"

    kpis = [
        ("Total Passengers", f"{n:,}", INK),
        ("Survival Rate", f"{surv_rate:.1f}%", BLUE),
        ("Average Age", f"{avg_age:.1f} yrs", INK),
        ("Average Fare", money(avg_fare), INK),
        ("Traveling Alone", f"{pct_alone:.1f}%", ORANGE),
        ("With Recorded Cabin", f"{pct_cabin:.1f}%", INK),
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
<title>Titanic Survival Dashboard</title>
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
    grid-column: 1 / -1; background: {CARD_BG}; border: 1px solid {BORDER}; border-left: 4px solid {BLUE};
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
  <h1>Titanic Survival Dashboard</h1>
  <div class="subtitle">Task 5 &mdash; Titanic passenger dataset, {n:,} passengers &middot; Nahla Nabil, VOLTIX Data Analyst Internship</div>

  <div class="kpi-row">{kpi_html}</div>

  <div class="note" style="border-left-color:{STATUS_CRITICAL};">
    <strong>&#9888; Data quality caveat &mdash; read first:</strong> <code>Survived</code> matches <code>Sex</code>
    with <strong>zero exceptions</strong> across all {n} rows (every female = survived, every male = did not).
    That is the exact fingerprint of Kaggle's <code>gender_submission.csv</code> naive benchmark, not
    individually verified outcomes (see <code>DATA_QUALITY_REPORT.md</code>). Every chart below that is driven
    by <code>Survived</code> is therefore really showing the <em>sex mix</em> of each group, not a genuine
    survival effect &mdash; chart titles and notes are worded accordingly.
  </div>

  <h2>Who "Survived"? (tautological by construction &mdash; see caveat)</h2>
  <div class="grid3">
    <div class="card">{html_parts['sex']}</div>
    <div class="card">{html_parts['donut']}</div>
    <div class="card">{html_parts['cls']}</div>
  </div>

  <h2>Age &amp; Family (reads as sex-mix by group)</h2>
  <div class="grid">
    <div class="card">{html_parts['agehist']}</div>
    <div class="card">{html_parts['agegrp']}</div>
    <div class="card full">{html_parts['fam']}</div>
  </div>

  <h2>Fare, Class &amp; Embarkation</h2>
  <div class="note">
    <strong>Worth flagging:</strong> since <code>Survived</code> is fully determined by <code>Sex</code>, the
    genuine (non-circular) findings here are about passenger mix, not survival: 1st class and cabin-recorded
    passengers skew notably more female than 3rd class, and that sex-mix difference &mdash; not the port or
    class itself &mdash; is what drives the apparent "survival by class/port" patterns.
  </div>
  <div class="grid3">
    <div class="card">{html_parts['emb']}</div>
    <div class="card">{html_parts['fare']}</div>
    <div class="card">{html_parts['title']}</div>
  </div>

  <h2>Interactive Drill-Down</h2>
  <div class="grid">
    <div class="card full">{html_parts['sun']}</div>
    <div class="card full">{html_parts['scatter']}</div>
    <div class="card full">{html_parts['corr']}</div>
  </div>

  <footer>
    Titanic_Dashboard.html &middot; generated entirely with Python (pandas + Plotly) from Cleaned_Titanic.csv &middot;
    built by build_dashboard.py, no external BI tool used.
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
