"""
Step 3: the chart set behind README.md, KEY_INSIGHTS.md and the submission.

Reads  Cleaned_Video_Games.csv, Cleaned_PS4_Sales.csv, Cleaned_XboxOne_Sales.csv, analysis_summary.json
Writes charts/01_data_quality.png ... charts/10_consoles.png
Every chart answers one question - the takeaway is written on the chart itself.
"""

import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "charts")
os.makedirs(OUT, exist_ok=True)

NAVY, TEAL, CORAL, SKY, GREY, INK, MUTED = "#1F3B57", "#1B998B", "#E4572E", "#9BC4E2", "#F3F6F9", "#22313F", "#5A6B7B"
GOLD, PLUM = "#E0A030", "#8E5572"
SRC = "Source: Video_Games_Sales_as_at_22_Dec_2016.csv (16,717 rows after cleaning)"

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 10,
    "axes.edgecolor": "#C9D2DA",
    "axes.labelcolor": INK,
    "text.color": INK,
    "xtick.color": MUTED,
    "ytick.color": MUTED,
    "axes.titleweight": "bold",
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "savefig.facecolor": "white",
})


def frame(fig, title, subtitle=None, takeaway=None, takeaway_color=CORAL):
    fig.subplots_adjust(bottom=0.17, top=0.87)
    fig.text(0.01, 0.99, title, ha="left", va="top", fontsize=15, fontweight="bold", color=NAVY)
    if subtitle:
        fig.text(0.01, 0.935, subtitle, ha="left", va="top", fontsize=9.5, color=MUTED)
    if takeaway:
        fig.text(0.01, 0.05, takeaway, ha="left", va="bottom", fontsize=10, color=takeaway_color,
                 fontweight="bold")
    fig.text(0.01, 0.015, SRC, ha="left", va="bottom", fontsize=8, color="#8A97A3")


def tidy(ax, ygrid=True):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    if ygrid:
        ax.grid(axis="y", color="#E6EBF0", linewidth=0.8)
        ax.set_axisbelow(True)


def save(fig, name):
    fig.savefig(os.path.join(OUT, name), dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("saved", name)


def load():
    df = pd.read_csv(os.path.join(HERE, "Cleaned_Video_Games.csv"),
                     dtype={"Critic_Score": "float64", "Critic_Count": "float64", "User_Score": "float64",
                            "User_Count": "float64", "Release_Year": "float64"})
    for c in df.columns:
        if c.startswith("Flag_"):
            df[c] = df[c].fillna("")
    df["Game"] = df["Game"].fillna("(unnamed title)")
    return (df,
            pd.read_csv(os.path.join(HERE, "Cleaned_PS4_Sales.csv")),
            pd.read_csv(os.path.join(HERE, "Cleaned_XboxOne_Sales.csv")),
            json.load(open(os.path.join(HERE, "analysis_summary.json"), encoding="utf-8")))


def chart_quality(df, S):
    miss = S["missing_pct_overview"]
    fig, ax = plt.subplots(figsize=(11, 5.6))
    labels = list(miss.keys())[::-1]
    vals = [miss[k] for k in labels]
    colors = [CORAL if v >= 40 else GOLD if v >= 5 else TEAL for v in vals]
    ax.barh(labels, vals, color=colors, height=0.62)
    for i, v in enumerate(vals):
        ax.text(v + 0.7, i, f"{v:.1f}%", va="center", fontsize=9, color=INK, fontweight="bold")
    ax.set_xlim(0, max(vals) * 1.18)
    ax.set_xlabel("% of rows missing in the raw file")
    ax.set_title("Ratings are the only heavily missing blocks; identifiers and sales are complete", pad=10)
    tidy(ax, ygrid=False)
    ax.grid(axis="x", color="#E6EBF0", linewidth=0.8)
    ax.set_axisbelow(True)
    frame(fig, "1. Data quality: where the raw file is incomplete",
          "16,719 raw rows. Scores come from review sites, so only reviewed games carry them - the blanks are not errors.",
          "Action: blanks were never filled in; 2 duplicate rows removed, 111 release years recovered, "
          "everything else flagged.")
    save(fig, "01_data_quality.png")


def chart_genres(df, S):
    g = df.groupby("Genre").agg(Games=("Game", "count"), Sales=("Global_Sales", "sum")).sort_values("Games")
    fig, axes = plt.subplots(1, 2, figsize=(12.5, 5.4))
    ax = axes[0]
    ax.barh(g.index, g["Games"], color=NAVY, height=0.62)
    for i, v in enumerate(g["Games"]):
        ax.text(v + 40, i, f"{v:,}", va="center", fontsize=8.5, color=INK)
    ax.set_xlim(0, g["Games"].max() * 1.16)
    ax.set_title("Number of titles released", fontsize=11.5)
    ax.set_xlabel("titles")
    tidy(ax, ygrid=False)
    ax.grid(axis="x", color="#E6EBF0", linewidth=0.8)
    ax.set_axisbelow(True)

    ax = axes[1]
    gs = g.sort_values("Sales")
    ax.barh(gs.index, gs["Sales"], color=TEAL, height=0.62)
    for i, v in enumerate(gs["Sales"]):
        ax.text(v + 20, i, f"{v:,.0f}M", va="center", fontsize=8.5, color=INK)
    ax.set_xlim(0, gs["Sales"].max() * 1.2)
    ax.set_title("Total global sales", fontsize=11.5)
    ax.set_xlabel("million units-equivalent")
    tidy(ax, ygrid=False)
    ax.grid(axis="x", color="#E6EBF0", linewidth=0.8)
    ax.set_axisbelow(True)
    fig.subplots_adjust(wspace=0.32)
    frame(fig, "2. Genres: Action is both the biggest and the busiest",
          "12 genres. Left: how many titles were released. Right: how much they sold.",
          "Action = 3,370 titles (20.2%) and 19.6% of sales; Platform earns the most per title (0.93M), "
          "Adventure the least (0.18M).")
    save(fig, "02_genres.png")


def chart_platforms(df, S):
    p = df.groupby("Platform").agg(Games=("Game", "count"), Sales=("Global_Sales", "sum")).sort_values("Sales")
    top = p.tail(14)
    fig, ax = plt.subplots(figsize=(11.5, 6))
    colors = [CORAL if i >= len(top) - 4 else NAVY for i in range(len(top))]
    ax.barh(top.index, top["Sales"], color=colors, height=0.66)
    for i, (k, v) in enumerate(zip(top.index, top["Sales"])):
        ax.text(v + 12, i, f"{v:,.0f}M   ({int(top.loc[k, 'Games']):,} titles, "
                           f"{v / top.loc[k, 'Games']:.2f}M each)", va="center", fontsize=8.5, color=INK)
    ax.set_xlim(0, top["Sales"].max() * 1.45)
    ax.set_xlabel("total global sales (million)")
    ax.set_title("PS2 leads every platform; the five newest platforms are highlighted", pad=10)
    tidy(ax, ygrid=False)
    ax.grid(axis="x", color="#E6EBF0", linewidth=0.8)
    ax.set_axisbelow(True)
    frame(fig, "3. Platforms: PlayStation and Nintendo split the market",
          "31 platforms. Labels show total sales, title count and the average per title.",
          "PS2 sold 1,255M from 2,161 titles. PlayStation 40.2% + Nintendo 39.2% = 79% of every sale in the file.")
    save(fig, "03_platforms.png")


def chart_trend(df, S):
    y = df.dropna(subset=["Release_Year"]).groupby("Release_Year").agg(
        Games=("Game", "count"), Sales=("Global_Sales", "sum"))
    y = y[y.index <= 2016]
    fig, ax = plt.subplots(figsize=(12.5, 5.6))
    ax.bar(y.index, y["Sales"], color=SKY, width=0.72, label="Global sales (M)")
    ax2 = ax.twinx()
    ax2.plot(y.index, y["Games"], color=CORAL, linewidth=2.1, marker="o", ms=3, label="Titles released")
    ax2.set_ylabel("titles released", color=CORAL)
    ax2.tick_params(axis="y", colors=CORAL)
    ax2.spines["top"].set_visible(False)
    for sp in ("top",):
        ax.spines[sp].set_visible(False)
    ax.set_ylabel("global sales (million)")
    ax.set_xlabel("year of release")
    ax.grid(axis="y", color="#E6EBF0", linewidth=0.8)
    ax.set_axisbelow(True)
    ax.set_xlim(1979, 2017)
    peak = y["Sales"].idxmax()
    ax.annotate(f"peak {int(peak)}: {y['Sales'].max():,.0f}M", xy=(peak, y["Sales"].max()),
                xytext=(peak - 9, y["Sales"].max() + 30), fontsize=9.5, fontweight="bold", color=NAVY,
                arrowprops=dict(arrowstyle="->", color=NAVY, lw=1.1))
    ax.annotate("2016 partial (snapshot 22 Dec)", xy=(2016, y.loc[2016, "Sales"]), xytext=(2008.5, 645),
                fontsize=9, color=MUTED, arrowprops=dict(arrowstyle="->", color=MUTED, lw=1))
    h1, l1 = ax.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax.legend(h1 + h2, l1 + l2, loc="upper left", frameon=False, fontsize=9)
    frame(fig, "4. Sales over the years: the market peaked in 2008 and cooled afterwards",
          "1980-2016 (4 rows dated 2017-2020 are excluded; 158 rows have no release year).",
          "2008 = 680.8M from 1,440 titles. Sales then fall to 268M by 2015 while titles stay numerous - "
          "more games split a flatter market.")
    save(fig, "04_sales_trend.png")


def chart_regions(df, S):
    reg = pd.Series({r["region"]: r["sales"] for r in S["regions"]})
    names = {"NA_Sales": "North America", "EU_Sales": "Europe", "JP_Sales": "Japan", "Other_Sales": "Rest of world"}
    fig, axes = plt.subplots(1, 2, figsize=(12.5, 5.4), gridspec_kw={"width_ratios": [1, 1.35]})
    ax = axes[0]
    wedges, _, autotexts = ax.pie(reg.values,
                                  labels=[f"{names[k]}\n{v:,.0f}M" for k, v in reg.items()],
                                  autopct=lambda p: f"{p:.1f}%",
                                  colors=[NAVY, TEAL, CORAL, SKY], startangle=90, pctdistance=0.79,
                                  labeldistance=1.16,
                                  wedgeprops=dict(width=0.42, edgecolor="white", linewidth=2),
                                  textprops=dict(fontsize=9.5, color=INK))
    for t in autotexts:
        t.set_fontweight("bold")
        t.set_color("white")
        t.set_fontsize(9.5)
    ax.text(0, 0, f"{reg.sum():,.0f}M\nall regions", ha="center", va="center", fontsize=11,
            fontweight="bold", color=NAVY)
    ax.set_title("Regional share of all sales", fontsize=11.5)

    ax = axes[1]
    mix = pd.DataFrame(S["region_mix_by_decade"]).set_index("Decade")
    mix = mix[mix.index != "2020s"].loc[:, ["NA_Sales", "EU_Sales", "JP_Sales", "Other_Sales"]]
    bottom = np.zeros(len(mix))
    cols = [NAVY, TEAL, CORAL, SKY]
    short = {"NA_Sales": "NA", "EU_Sales": "EU", "JP_Sales": "JP", "Other_Sales": "Other"}
    for c, col in zip(mix.columns, cols):
        ax.bar(mix.index, mix[c].values, bottom=bottom, color=col, width=0.6,
               label=names[c])
        for i, v in enumerate(mix[c].values):
            if v > 6:
                ax.text(i, bottom[i] + v / 2, f"{short[c]} {v:.0f}%", ha="center", va="center", fontsize=8.8,
                        color="white", fontweight="bold")
        bottom += mix[c].values
    ax.set_ylim(0, 100)
    ax.set_ylabel("% of that decade's sales")
    ax.set_title("Mix by decade (colours match the donut)", fontsize=11.5)
    tidy(ax)
    fig.subplots_adjust(wspace=0.22)
    frame(fig, "5. Regions: North America is half the market",
          "Regional sales of all 16,717 rows, and how that split changed decade by decade.",
          "NA 49.4% | EU 27.2% | JP 14.6% | rest 8.9%. Japan's share halved since the 1990s while Europe grew.")
    save(fig, "05_regions.png")


def chart_top_games(df, S):
    top = df.nlargest(15, "Global_Sales").iloc[::-1]
    fam_col = {"Nintendo": CORAL, "PlayStation": NAVY, "Xbox": TEAL}
    fam = df.groupby("Game")["Platform_Family"].first()
    colors = [fam_col.get(f, SKY) for f in fam.loc[top["Game"]].values]
    fig, ax = plt.subplots(figsize=(11.5, 6.4))
    ax.barh(top["Game"], top["Global_Sales"], color=colors, height=0.66)
    for i, (v, plat, yr) in enumerate(zip(top["Global_Sales"], top["Platform"], top["Release_Year"])):
        ax.text(v + 1.2, i, f"{v:.1f}M   {plat} {int(yr) if pd.notna(yr) else '?'}",
                va="center", fontsize=8.5, color=INK)
    ax.set_xlim(0, top["Global_Sales"].max() * 1.35)
    ax.set_xlabel("global sales (million)")
    handles = [plt.Rectangle((0, 0), 1, 1, color=c) for c in [CORAL, NAVY, TEAL, SKY]]
    ax.legend(handles, ["Nintendo", "PlayStation", "Xbox", "Other"], frameon=False, fontsize=9,
              loc="lower right")
    tidy(ax, ygrid=False)
    ax.grid(axis="x", color="#E6EBF0", linewidth=0.8)
    ax.set_axisbelow(True)
    frame(fig, "6. The 15 best-selling games of all time",
          "Title level (a game that appeared on several platforms is summed). Platform and year on the right.",
          "11 of the top 15 are Nintendo titles and Wii Sports alone sold 82.5M - 0.9% of the whole market.")
    save(fig, "06_top_games.png")


def chart_publishers(df, S):
    pub = df[df["Publisher"] != "Unknown publisher"].groupby("Publisher")["Global_Sales"].sum().sort_values()
    total = df["Global_Sales"].sum()
    top = pub.tail(14)
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.8), gridspec_kw={"width_ratios": [1.45, 1]})
    ax = axes[0]
    colors = [CORAL if p in ("Nintendo", "Electronic Arts") else NAVY for p in top.index]
    ax.barh(top.index, top.values, color=colors, height=0.66)
    for i, v in enumerate(top.values):
        ax.text(v + 14, i, f"{v:,.0f}M", va="center", fontsize=8.5, color=INK)
    ax.set_xlim(0, top.values.max() * 1.24)
    ax.set_xlabel("total global sales (million)")
    ax.set_title("Top 14 publishers by sales", fontsize=11.5)
    tidy(ax, ygrid=False)
    ax.grid(axis="x", color="#E6EBF0", linewidth=0.8)
    ax.set_axisbelow(True)

    ax = axes[1]
    ranked = pub.sort_values(ascending=False).reset_index(drop=True).cumsum() / total * 100
    x = np.arange(1, len(ranked) + 1)
    ax.plot(x, ranked.values, color=NAVY, linewidth=2.2)
    for n in (10, 20, 50):
        ax.scatter([n], [ranked.iloc[n - 1]], color=CORAL, zorder=3, s=32)
        ax.annotate(f"top {n}: {ranked.iloc[n - 1]:.0f}%", xy=(n, ranked.iloc[n - 1]),
                    xytext=(n + 18, ranked.iloc[n - 1] - 13), fontsize=9, color=CORAL, fontweight="bold")
    ax.set_xlabel("publishers ranked by sales")
    ax.set_ylabel("% of all sales")
    ax.set_xlim(0, len(ranked))
    ax.set_ylim(0, 105)
    ax.set_title("Concentration: 10 of 582 publishers = 70% of sales", fontsize=11.5)
    tidy(ax, ygrid=False)
    ax.grid(color="#E6EBF0", linewidth=0.8)
    ax.set_axisbelow(True)
    fig.subplots_adjust(wspace=0.3)
    frame(fig, "7. Publishers: a market dominated by a handful of houses",
          "582 publishers. Nintendo alone holds 20.1% of every sale in the file.",
          "Top 10 publishers = 70.2%, top 20 = 85.5%; 371 publishers with 5 titles or fewer together make 1.6%.")
    save(fig, "07_publishers.png")


def chart_ratings(df, S):
    r = df.dropna(subset=["Critic_Score"])
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.6))
    ax = axes[0]
    band = (df.groupby("Critic_Band").agg(Games=("Game", "count"), Sales=("Global_Sales", "sum")))
    band["Avg"] = band["Sales"] / band["Games"]
    order = ["Under 60", "60-69", "70-79", "80-89", "90+"]
    b = band.loc[order]
    ax.bar(b.index, b["Avg"], color=[CORAL, GOLD, SKY, TEAL, NAVY], width=0.62)
    for i, (v, n) in enumerate(zip(b["Avg"], b["Games"])):
        ax.text(i, v + 0.06, f"{v:.2f}M\n{n:,} games", ha="center", fontsize=8.8, color=INK)
    ax.set_ylim(0, b["Avg"].max() * 1.28)
    ax.set_ylabel("average sales per title (million)")
    ax.set_title("Average sales per title by critic score", fontsize=11.5)
    ax.tick_params(axis="x", labelsize=9)
    tidy(ax)

    ax = axes[1]
    sample = r.sample(min(len(r), 3000), random_state=7)
    ax.scatter(sample["Critic_Score"], sample["Global_Sales"], s=11, alpha=0.35, color=NAVY, edgecolors="none")
    ax.set_yscale("log")
    ax.set_xlabel("critic score (0-100)")
    ax.set_ylabel("global sales (M, log scale)")
    ax.set_title(f"Critic score vs sales: r = {S['ratings']['pearson_critic']:.2f}, "
                 f"rho = {S['ratings']['spearman_critic']:.2f}", fontsize=11.5)
    ax.grid(color="#E6EBF0", linewidth=0.8)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    fig.subplots_adjust(wspace=0.28)
    frame(fig, "8. Reviews and sales: scores help, but they do not decide",
          f"Critic scores exist for {S['ratings']['n_critic']:,} of 16,717 rows; user scores for "
          f"{S['ratings']['n_user']:,}. Scatter shows a 3,000-row random sample.",
          "A 90+ title sells 2.83M on average against 0.27M under 60 - yet the rank correlation is only "
          "0.39, so score alone cannot predict sales.")
    save(fig, "08_ratings.png")


def chart_concentration(df, S):
    by_game = df.groupby("Game")["Global_Sales"].sum().sort_values(ascending=False)
    cum = by_game.cumsum() / by_game.sum() * 100
    fig, ax = plt.subplots(figsize=(11.5, 5.4))
    x = np.arange(1, len(cum) + 1)
    ax.plot(x, cum.values, color=NAVY, linewidth=2.4)
    ax.plot([0, len(cum)], [0, 100], color="#C9D2DA", linewidth=1, linestyle="--")
    for n, lab in ((100, "top 100 titles"), (500, "top 500"), (2000, "top 2,000")):
        ax.scatter([n], [cum.iloc[n - 1]], color=CORAL, s=34, zorder=3)
        ax.annotate(f"{lab}: {cum.iloc[n - 1]:.0f}%", xy=(n, cum.iloc[n - 1]),
                    xytext=(n + 60, cum.iloc[n - 1] - 11), fontsize=9.5, color=CORAL, fontweight="bold")
    ax.set_xlabel("titles ranked by total sales")
    ax.set_ylabel("% of all sales")
    ax.set_xlim(0, len(cum))
    ax.set_ylim(0, 102)
    ax.set_title("Cumulative share of sales by ranked title", pad=10)
    tidy(ax, ygrid=False)
    ax.grid(color="#E6EBF0", linewidth=0.8)
    ax.set_axisbelow(True)
    frame(fig, "9. How concentrated the market is",
          f"{len(cum):,} distinct titles. The dashed line would be a perfectly even market.",
          "The top 1% of titles (115) take 22% of sales and 34.6% of titles sell under 0.1M - "
          "a long tail, not a hit-only market.")
    save(fig, "09_concentration.png")


def chart_consoles(ps4, xone, S):
    fig, axes = plt.subplots(1, 2, figsize=(12.5, 5.4))
    names = ["North America", "Europe", "Japan", "Rest of world"]
    cols = [NAVY, TEAL, CORAL, SKY]
    ax = axes[0]
    totals = [ps4["Global_Sales"].sum(), xone["Global_Sales"].sum()]
    ax.bar(["PS4", "Xbox One"], totals, color=[NAVY, TEAL], width=0.5)
    for i, v in enumerate(totals):
        ax.text(i, v + 12, f"{v:,.0f}M", ha="center", fontsize=12, fontweight="bold", color=INK)
    ax.set_ylim(0, max(totals) * 1.2)
    ax.set_ylabel("global sales (million)")
    ax.set_title(f"PS4 sells {S['consoles']['ratio']}x more across shared titles", fontsize=11.5)
    tidy(ax)

    ax = axes[1]
    short = ["NA", "EU", "JP", "Other"]
    for i, (d, n) in enumerate([(ps4, "PS4"), (xone, "Xbox One")]):
        reg = d[["NA_Sales", "EU_Sales", "JP_Sales", "Other_Sales"]].sum()
        vals = (reg / reg.sum() * 100).values
        base = 0.0
        for j, (v, c, nm) in enumerate(zip(vals, cols, short)):
            ax.bar([n], [v], bottom=[base], color=c, width=0.5)
            if v >= 6:
                ax.text(i, base + v / 2, f"{nm} {v:.0f}%", ha="center", va="center",
                        color="white", fontweight="bold", fontsize=9.5)
            base += v
    ax.set_ylim(0, 100)
    ax.set_ylabel("% of that console's sales")
    ax.set_title("Regional mix: Japan is 5.8% of PS4, 0.2% of Xbox One", fontsize=11.5)
    tidy(ax)
    fig.subplots_adjust(wspace=0.3)
    frame(fig, "10. Current generation: PS4 vs Xbox One (separate files)",
          f"{len(ps4)} PS4 and {len(xone)} Xbox One titles, later snapshot than the main file. "
          "PS4 outsells Xbox One on 72% of the 516 shared titles.",
          "Europe is PS4's biggest region (43%); Xbox One is a North-American console (60%).")
    save(fig, "10_consoles.png")


def main():
    df, ps4, xone, S = load()
    chart_quality(df, S)
    chart_genres(df, S)
    chart_platforms(df, S)
    chart_trend(df, S)
    chart_regions(df, S)
    chart_top_games(df, S)
    chart_publishers(df, S)
    chart_ratings(df, S)
    chart_concentration(df, S)
    chart_consoles(ps4, xone, S)
    print("charts written to", OUT)


if __name__ == "__main__":
    main()
