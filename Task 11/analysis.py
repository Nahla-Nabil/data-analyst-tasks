"""
Step 2: exploratory data analysis.

Reads  Cleaned_Video_Games.csv, Cleaned_PS4_Sales.csv, Cleaned_XboxOne_Sales.csv, cleaning_log.json
Prints every number used in README.md / KEY_INSIGHTS.md and writes analysis_summary.json
(the dashboard text, the charts and the docs all take their numbers from there).
"""

import json
import os

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))


def section(title):
    print("\n" + "=" * 78 + f"\n{title}\n" + "=" * 78)


def table(s, fmt=None, head=None):
    if head:
        print(f"\n{head}")
    print(s.to_string(float_format=(fmt or (lambda v: f"{v:,.2f}"))))


def share(series):
    return (series / series.sum() * 100).round(1)


def load():
    df = pd.read_csv(os.path.join(HERE, "Cleaned_Video_Games.csv"),
                     dtype={"Critic_Score": "float64", "Critic_Count": "float64", "User_Count": "float64",
                            "User_Score": "float64", "Release_Year": "float64"})
    for c in ["Flag_Unnamed", "Flag_Year_Imputed", "Flag_Year_Unknown", "Flag_Year_Future", "Flag_Unknown_Publisher"]:
        df[c] = df[c].fillna("")
    df["Game"] = df["Game"].fillna("(unnamed title)")
    ps4 = pd.read_csv(os.path.join(HERE, "Cleaned_PS4_Sales.csv"))
    xone = pd.read_csv(os.path.join(HERE, "Cleaned_XboxOne_Sales.csv"))
    return df, ps4, xone


def main():
    df, ps4, xone = load()
    S = {}
    year = df["Release_Year"]
    rated = df[df["Has_Reviews"] == "Yes"]

    # ---------------------------------------------------------------- 1. overview
    section("1. DATA UNDERSTANDING")
    print(f"rows: {len(df):,}   columns: {df.shape[1]}   global sales: {df['Global_Sales'].sum():,.1f}M")
    print(f"years: {int(year.min())}-{int(year.max())} ({year.notna().sum():,} dated, {year.isna().sum()} unknown)")
    print(f"platforms: {df['Platform'].nunique()}   genres: {df['Genre'].nunique()}   "
          f"publishers: {df['Publisher'].nunique()}   developers: {df['Developer'].nunique()}")
    print(f"rows with critic or user score: {len(rated):,} ({len(rated) / len(df):.1%})")
    print("\nmissing values in the RAW file (per cleaning_log.json):")
    raw = pd.read_csv(os.path.join(HERE, "Video_Games_Sales_as_at_22_Dec_2016.csv"), nrows=5000)
    full = pd.read_csv(os.path.join(HERE, "Video_Games_Sales_as_at_22_Dec_2016.csv"))
    table(full.isna().sum().pipe(lambda s: s[s > 0]).sort_values(ascending=False).to_frame("missing")
          .assign(share=lambda d: (d["missing"] / len(full) * 100).round(1)), head="column / missing / %")
    S["rows_raw"], S["rows_clean"] = len(full), len(df)
    S["missing_pct_overview"] = {k: round(v, 1) for k, v in (full.isna().mean() * 100).items() if v > 0}

    # ---------------------------------------------------------------- 2. quality
    section("2. DATA QUALITY ACTIONS")
    log = json.load(open(os.path.join(HERE, "cleaning_log.json"), encoding="utf-8"))
    for r in log:
        print(f"[{r['step']:>2}] {r['check']}\n     found: {r['found']}\n     action: {r['action']}")
    S["quality_steps"] = log
    S["flags"] = {c.replace("Flag_", "").lower(): int((df[c] == "Yes").sum())
                  for c in df.columns if c.startswith("Flag_")}

    # ---------------------------------------------------------------- 3. genre
    section("3. GENRES: which are the most common?")
    g = df.groupby("Genre").agg(Games=("Game", "count"), Sales=("Global_Sales", "sum"))
    g["Sales_Share_%"] = share(g["Sales"])
    g["Avg_Sales_M"] = (g["Sales"] / g["Games"]).round(2)
    g["Games_Share_%"] = share(g["Games"])
    table(g.sort_values("Games", ascending=False), head="genre / games / sales(M) / % of sales / avg per game")
    print("\ntop genre by volume:", g["Games"].idxmax(), "| top genre by sales:", g["Sales"].idxmax())
    S["genre"] = g.reset_index().to_dict("records")
    S["top_genre_games"], S["top_genre_sales"] = g["Games"].idxmax(), g["Sales"].idxmax()

    # ---------------------------------------------------------------- 4. platform
    section("4. PLATFORMS: which sell the most?")
    p = df.groupby("Platform").agg(Games=("Game", "count"), Sales=("Global_Sales", "sum"))
    p["Sales_Share_%"] = share(p["Sales"])
    p["Avg_Sales_M"] = (p["Sales"] / p["Games"]).round(2)
    table(p.sort_values("Sales", ascending=False).head(12), head="platform / games / sales(M) / % / avg per game")
    fam = df.groupby("Platform_Family").agg(Games=("Game", "count"), Sales=("Global_Sales", "sum"))
    fam["Sales_Share_%"] = share(fam["Sales"])
    table(fam.sort_values("Sales", ascending=False), head="platform family")
    print("\ntop platform:", p["Sales"].idxmax(), f"({p['Sales'].max():,.1f}M)")
    S["platform"] = p.sort_values("Sales", ascending=False).reset_index().to_dict("records")
    S["platform_family"] = fam.sort_values("Sales", ascending=False).reset_index().to_dict("records")
    S["top_platform"] = p["Sales"].idxmax()
    S["worst_platform"] = p["Sales"].idxmin()

    # ---------------------------------------------------------------- 5. publisher
    section("5. PUBLISHERS: who sells the most?")
    pub = df[df["Publisher"] != "Unknown publisher"].groupby("Publisher") \
        .agg(Games=("Game", "count"), Sales=("Global_Sales", "sum"))
    pub["Sales_Share_%"] = share(pub["Sales"])
    pub["Avg_Sales_M"] = (pub["Sales"] / pub["Games"]).round(2)
    table(pub.sort_values("Sales", ascending=False).head(12),
          head="publisher / games / sales(M) / % of all sales / avg per game")
    total = df["Global_Sales"].sum()
    top10 = pub["Sales"].nlargest(10).sum()
    top20 = pub["Sales"].nlargest(20).sum()
    print(f"\ntop 10 publishers = {top10:,.1f}M = {top10 / total:.1%} of all sales; "
          f"top 20 = {top20 / total:.1%}; {len(pub)} publishers in total")
    print("publishers that only ever released a handful of titles:")
    small = pub[pub["Games"] <= 5]
    print(f"  {len(small)} publishers with <=5 titles, together {small['Sales'].sum():,.1f}M "
          f"({small['Sales'].sum() / total:.1%})")
    S["publisher"] = pub.sort_values("Sales", ascending=False).reset_index().to_dict("records")
    S["top_publisher"] = pub["Sales"].idxmax()
    S["top10_publisher_share_pct"] = round(top10 / total * 100, 1)
    S["publisher_count"] = int(len(pub))

    # ---------------------------------------------------------------- 6. best sellers
    section("6. BEST-SELLING GAMES")
    top = df.nlargest(15, "Global_Sales")[
        ["Game", "Platform", "Release_Year", "Genre", "Publisher", "NA_Sales", "EU_Sales", "JP_Sales", "Global_Sales"]]
    table(top, head="game / platform / year / genre / publisher / NA / EU / JP / global (M)")
    print("\nNintendo share of the top 20:",
          f"{(df.nlargest(20, 'Global_Sales')['Publisher'] == 'Nintendo').sum()} of 20")
    S["top_games"] = top.head(10).replace({np.nan: None}).to_dict("records")
    S["top20_nintendo"] = int((df.nlargest(20, "Global_Sales")["Publisher"] == "Nintendo").sum())

    # concentration: how much of the market sits in the best titles
    by_game = df.groupby("Game")["Global_Sales"].sum().sort_values(ascending=False)
    cum = by_game.cumsum() / by_game.sum()
    S["top1pct_share_pct"] = round(cum.iloc[:max(1, len(cum) // 100)].iloc[-1] * 100, 1)
    S["top100_share_pct"] = round(cum.iloc[:100].iloc[-1] * 100, 1)
    S["long_tail_pct"] = round((by_game[by_game < 0.1].size / len(by_game)) * 100, 1)
    print(f"\nconcentration: the top 1% of titles ({len(cum) // 100}) = {S['top1pct_share_pct']}% of sales, "
          f"the top 100 titles = {S['top100_share_pct']}%")
    print(f"{S['long_tail_pct']}% of titles sold under 0.1M copies-equivalent "
          f"({int((by_game < 0.1).sum()):,} titles)")

    # ---------------------------------------------------------------- 7. years
    section("7. SALES OVER THE YEARS")
    y = df.dropna(subset=["Release_Year"]).groupby("Release_Year").agg(
        Games=("Game", "count"), Sales=("Global_Sales", "sum"))
    table(y.tail(12), head="year / games / sales (M) - last 12 years in the data")
    peak = y["Sales"].idxmax()
    print(f"\npeak year: {int(peak)} with {y['Sales'].max():,.1f}M from {int(y.loc[peak, 'Games'])} games")
    print(f"2016 is a partial year (snapshot dated 22 Dec 2016): {y.loc[2016, 'Sales']:.1f}M, "
          f"and 4 rows are dated 2017-2020 (flagged, excluded from the trend)")
    dec = df.dropna(subset=["Release_Year"]).groupby("Decade").agg(Games=("Game", "count"), Sales=("Global_Sales", "sum"))
    dec["Sales_Share_%"] = share(dec["Sales"])
    table(dec, head="decade")
    S["yearly"] = [{"year": int(k), "games": int(v["Games"]), "sales": round(v["Sales"], 2)} for k, v in y.iterrows()]
    S["peak_year"] = int(peak)
    S["decade"] = dec.reset_index().to_dict("records")
    print("\nnew releases per year (peak years):")
    print(y.sort_values("Games", ascending=False).head(5).to_string())

    # ---------------------------------------------------------------- 8. regions
    section("8. WHICH REGIONS GENERATE THE SALES?")
    regions = df[["NA_Sales", "EU_Sales", "JP_Sales", "Other_Sales"]].sum()
    reg = pd.DataFrame({"Sales_M": regions, "Share_%": share(regions)})
    table(reg, head="region / sales (M) / share")
    S["regions"] = [{"region": k, "sales": round(v, 1), "share": share(regions)[k]} for k, v in regions.items()]
    print("\nregional mix by decade (share of that decade's sales):")
    mix = (df.dropna(subset=["Release_Year"]).groupby("Decade")[["NA_Sales", "EU_Sales", "JP_Sales", "Other_Sales"]]
           .sum().pipe(lambda d: d.div(d.sum(axis=1), axis=0) * 100).round(1))
    table(mix, head="decade / NA% / EU% / JP% / Other%")
    S["region_mix_by_decade"] = mix.reset_index().to_dict("records")
    print("\nregional mix for the biggest genres:")
    gm = df.groupby("Genre")[["NA_Sales", "EU_Sales", "JP_Sales", "Other_Sales"]].sum()
    gm = gm.loc[gm.sum(axis=1).nlargest(6).index]
    table((gm.div(gm.sum(axis=1), axis=0) * 100).round(1), head="genre / NA% / EU% / JP% / Other%")
    S["region_mix_by_genre"] = (gm.div(gm.sum(axis=1), axis=0) * 100).round(1).reset_index().to_dict("records")

    # ---------------------------------------------------------------- 9. ratings
    section("9. RATINGS vs SALES")
    r = df.dropna(subset=["Critic_Score"])
    u = df.dropna(subset=["User_Score"])
    pearson_c = r["Critic_Score"].corr(r["Global_Sales"])
    spearman_c = r["Critic_Score"].corr(r["Global_Sales"], method="spearman")
    pearson_u = u["User_Score"].corr(u["Global_Sales"])
    spearman_u = u["User_Score"].corr(u["Global_Sales"], method="spearman")
    print(f"critic score vs sales:  Pearson r = {pearson_c:.3f}, Spearman rho = {spearman_c:.3f}  (n = {len(r):,})")
    print(f"user score vs sales:    Pearson r = {pearson_u:.3f}, Spearman rho = {spearman_u:.3f}  (n = {len(u):,})")
    print(f"critic score vs user score: r = {r['User_Score'].corr(r['Critic_Score']):.3f} on "
          f"{len(r.dropna(subset=['User_Score'])):,} rows rated by both")
    band = df.groupby("Critic_Band", observed=True).agg(Games=("Game", "count"), Sales=("Global_Sales", "sum"))
    band["Avg_Sales_M"] = (band["Sales"] / band["Games"]).round(2)
    order = ["No critic score", "Under 60", "60-69", "70-79", "80-89", "90+"]
    table(band.reindex(order), head="critic band / games / total sales (M) / average per game (M)")
    ranked = df.dropna(subset=["Critic_Score"]).copy()
    ranked["Top"] = np.where(ranked["Global_Sales"].rank(ascending=False, method="first") <= 50,
                             "Top 50 sellers", "The rest")
    print("\nmean critic score of the biggest sellers against everything else:")
    table(ranked.groupby("Top")["Critic_Score"].agg(["count", "mean"]).round(2), head="group / n / mean critic score")
    print("\nthe 10 best-rated games with 100+ critic votes:")
    top_rated = (df.dropna(subset=["Critic_Score"]).query("Critic_Count >= 100")
                 .nlargest(10, "Critic_Score")[["Game", "Platform", "Release_Year", "Critic_Score", "Critic_Count",
                                                "User_Score", "Global_Sales"]])
    table(top_rated, head="game / platform / year / critic / votes / user / global sales (M)")
    S["ratings"] = {"pearson_critic": round(pearson_c, 3), "spearman_critic": round(spearman_c, 3),
                    "pearson_user": round(pearson_u, 3), "spearman_user": round(spearman_u, 3),
                    "n_critic": int(len(r)), "n_user": int(len(u)),
                    "band": band.reindex(order).reset_index().to_dict("records"),
                    "top_rated": top_rated.replace({np.nan: None}).to_dict("records")}

    # ---------------------------------------------------------------- 10. consoles
    section("10. PS4 vs XBOX ONE (separate files, later snapshot)")
    rows = []
    for name, d in [("PS4", ps4), ("Xbox One", xone)]:
        rr = d[["NA_Sales", "EU_Sales", "JP_Sales", "Other_Sales"]].sum()
        rows.append({"Platform": name, "Titles": len(d), "Global_M": round(d["Global_Sales"].sum(), 1),
                     "NA_%": round(rr["NA_Sales"] / rr.sum() * 100, 1), "EU_%": round(rr["EU_Sales"] / rr.sum() * 100, 1),
                     "JP_%": round(rr["JP_Sales"] / rr.sum() * 100, 1),
                     "Other_%": round(rr["Other_Sales"] / rr.sum() * 100, 1),
                     "Avg_M": round(d["Global_Sales"].mean(), 3)})
    table(pd.DataFrame(rows).set_index("Platform"), head="console / titles / global (M) / regional mix / avg per title")
    both = set(ps4["Game"]) & set(xone["Game"])
    print(f"{len(both)} titles released on both consoles")
    cmp = pd.DataFrame({
        "PS4": ps4.set_index("Game")["Global_Sales"],
        "XboxOne": xone.set_index("Game")["Global_Sales"]}).dropna()
    cmp["diff"] = cmp["PS4"] - cmp["XboxOne"]
    print(f"PS4 outsells Xbox One on {(cmp['diff'] > 0).mean():.0%} of the {len(cmp)} shared titles "
          f"(median gap {cmp['diff'].median():.2f}M)")
    shared = cmp[(cmp["PS4"] > 0.05) | (cmp["XboxOne"] > 0.05)]
    print(f"PS4/Xbox One sales ratio over the shared titles with real sales: "
          f"{shared['PS4'].sum() / shared['XboxOne'].sum():.2f}x")
    # cross-check against the main file (which stops at 22 Dec 2016)
    main_ps4 = df[df["Platform"] == "PS4"].groupby("Game")["Global_Sales"].sum()
    common = main_ps4.index.intersection(ps4["Game"])
    newer = ps4.set_index("Game").loc[common, "Global_Sales"]
    older = main_ps4.loc[common]
    diff = newer - older
    print(f"cross-check on the {len(common)} PS4 titles found in both files: the console file records "
          f"{newer.sum():,.1f}M against {older.sum():,.1f}M in the main file "
          f"(+{diff.sum():,.1f}M, higher on {(diff > 0.1).mean():.0%} of titles) - the two files are "
          f"snapshots taken at different dates")
    S["consoles"] = {"rows": rows, "shared_titles": int(len(both)),
                     "ps4_wins_share_pct": round((cmp["diff"] > 0).mean() * 100, 0),
                     "ratio": round(float(shared["PS4"].sum() / shared["XboxOne"].sum()), 2),
                     "cross_check_n": int(len(common)),
                     "cross_check_newer_m": round(float(newer.sum()), 1),
                     "cross_check_main_m": round(float(older.sum()), 1),
                     "cross_check_higher_pct": round((diff > 0.1).mean() * 100, 0)}

    # ---------------------------------------------------------------- 11. KPIs
    section("11. DASHBOARD KPIs (full data)")
    kpi = {
        "Total games": f"{len(df):,}",
        "Total global sales": f"{df['Global_Sales'].sum():,.1f}M",
        "Top genre (sales)": f"{g['Sales'].idxmax()} ({g['Sales'].max():,.1f}M)",
        "Top genre (titles)": f"{g['Games'].idxmax()} ({g['Games'].max():,} games)",
        "Top platform": f"{p['Sales'].idxmax()} ({p['Sales'].max():,.1f}M)",
        "Top publisher": f"{pub['Sales'].idxmax()} ({pub['Sales'].max():,.1f}M)",
        "Top selling game": f"{top.iloc[0]['Game']} ({top.iloc[0]['Global_Sales']}M)",
        "Largest region": f"North America ({regions.idxmax()} = {regions.max():,.1f}M, {regions.max() / total:.1%})",
        "Avg critic score": f"{df['Critic_Score'].mean():.1f} (n = {df['Critic_Score'].notna().sum():,})",
        "Share of rows with reviews": f"{len(rated) / len(df):.1%}",
        "Peak year": f"{int(peak)} ({y.loc[peak, 'Sales']:,.1f}M)",
        "Years covered": f"{int(year.min())}-{int(year.max())}",
    }
    for k, v in kpi.items():
        print(f"  {k:<26} {v}")
    S["kpi"] = kpi
    S["totals"] = {"games": int(len(df)), "global_sales": round(float(df["Global_Sales"].sum()), 1),
                   "avg_per_game": round(float(df["Global_Sales"].mean()), 3),
                   "median_per_game": round(float(df["Global_Sales"].median()), 3),
                   "platforms": int(df["Platform"].nunique()), "genres": int(df["Genre"].nunique()),
                   "rated_rows": int(len(rated)), "avg_critic": round(float(df["Critic_Score"].mean()), 1),
                   "avg_user": round(float(df["User_Score"].mean()), 2),
                   "year_min": int(year.min()), "year_max": int(year.max())}

    with open(os.path.join(HERE, "analysis_summary.json"), "w", encoding="utf-8") as fh:
        json.dump(S, fh, indent=2, default=lambda o: None if (isinstance(o, float) and np.isnan(o)) else str(o))
    print("\nanalysis_summary.json written")


if __name__ == "__main__":
    main()
