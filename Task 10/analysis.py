"""
Step 2: the numbers behind the dashboard and the README findings.

Reads  movies_clean.csv, movie_genres.csv
Revenue/budget medians use every movie where that value is known (as the dashboard does); ROI and profit need both.
Prints KPIs, genre table, money, ratings, trends and runtime results (with correlations).
summary() returns the same numbers as a dict; build_powerbi.py uses it for the Insights page.
"""

import os

import pandas as pd
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
M_VOTES = 1000      # default vote threshold for the weighted (Bayesian) rating, same as the dashboard default
TIER_ORDER = ["Under $10M", "$10M-40M", "$40M-100M", "$100M+"]
RUNTIME_ORDER = ["Under 90 min", "90-109 min", "110-129 min", "130-149 min", "150+ min"]


def load():
    d = pd.read_csv(os.path.join(HERE, "movies_clean.csv"))
    g = pd.read_csv(os.path.join(HERE, "movie_genres.csv")).merge(d, on="Movie_ID")
    return d, g


def weighted_top(d, m=M_VOTES, n=10):
    """IMDb-style score: v/(v+m)*R + m/(v+m)*C, for movies with at least m votes (C = average rating)."""
    c = d.loc[d["Rating_Reliable"] == "Yes", "Rating"].mean()
    e = d[d["Vote_Count"] >= m].copy()
    e["Score"] = e["Vote_Count"] / (e["Vote_Count"] + m) * e["Rating"] + m / (e["Vote_Count"] + m) * c
    return e.nlargest(n, "Score")[["Title_Year", "Rating", "Vote_Count", "Score"]]


def summary():
    d, g = load()
    fin = d[d["Financials_Known"] == "Yes"]
    rated = d[d["Rating_Reliable"] == "Yes"]
    gfin, grated = g[g["Financials_Known"] == "Yes"], g[g["Rating_Reliable"] == "Yes"]

    genre = pd.DataFrame({
        "movies": g.groupby("Genre").size(),
        "rated": grated.groupby("Genre").size(),
        "avg_rating": grated.groupby("Genre")["Rating"].mean(),
        "median_revenue": g.groupby("Genre")["Revenue"].median(),
        "total_revenue": g.groupby("Genre")["Revenue"].sum(),
        "median_roi": gfin.groupby("Genre")["ROI"].median(),
        "profitable": gfin.groupby("Genre")["Profit"].apply(lambda s: (s > 0).mean()),
    }).sort_values("movies", ascending=False)
    genre["rated"] = genre["rated"].fillna(0).astype(int)

    tier = fin.groupby("Budget_Tier").agg(movies=("ROI", "size"), median_roi=("ROI", "median"),
                                          profitable=("Profit", lambda s: (s > 0).mean()), median_revenue=("Revenue", "median")).reindex(TIER_ORDER)
    decade = pd.DataFrame({"movies": d.groupby("Decade").size(), "avg_rating": rated.groupby("Decade")["Rating"].mean(),
                           "median_revenue": d.groupby("Decade")["Revenue"].median(),
                           "median_budget": d.groupby("Decade")["Budget"].median(),
                           "avg_runtime": d.groupby("Decade")["Runtime"].mean()})
    runtime = pd.DataFrame({"movies": d.groupby("Runtime_Band").size(), "avg_rating": rated.groupby("Runtime_Band")["Rating"].mean(),
                            "median_revenue": d.groupby("Runtime_Band")["Revenue"].median()}).reindex(RUNTIME_ORDER)
    month = d.groupby("Release_Month")["Revenue"].median().sort_values(ascending=False)

    rr = rated.dropna(subset=["Runtime"])
    fr = fin.dropna(subset=["Runtime"])
    frr = fin[fin["Rating_Reliable"] == "Yes"]
    core = rated[rated["Release_Year"].between(1995, 2015)]
    return {
        "kpi": {
            "movies": len(d), "first_year": int(d["Release_Year"].min()), "last_year": int(d["Release_Year"].max()),
            "since_2000": (d["Release_Year"] >= 2000).mean(),
            "with_financials": len(fin), "total_revenue": d["Revenue"].sum(), "total_budget": d["Budget"].sum(),
            "avg_budget": d["Budget"].mean(), "median_revenue": d["Revenue"].median(), "avg_revenue": d["Revenue"].mean(),
            "median_roi": fin["ROI"].median(), "profitable": (fin["Profit"] > 0).mean(), "hit_2_5x": (fin["ROI"] >= 2.5).mean(),
            "avg_rating": rated["Rating"].mean(), "rated": len(rated), "avg_runtime": d["Runtime"].mean(),
        },
        "genre": genre, "tier": tier, "decade": decade, "runtime": runtime, "month": month,
        "top_revenue": fin.nlargest(10, "Revenue")[["Title_Year", "Revenue", "Budget", "Rating"]],
        "top_rated": weighted_top(d),
        "raw_top": d.nlargest(5, "Rating")[["Title_Year", "Rating", "Vote_Count"]],
        "top_roi": fin.nlargest(3, "ROI")[["Title_Year", "Budget", "Revenue", "ROI"]],
        "flops": fin.nsmallest(3, "Profit")[["Title_Year", "Budget", "Revenue", "Profit"]],
        "r": {
            "budget_revenue": stats.pearsonr(fin["Budget"], fin["Revenue"])[0],
            "votes_revenue": stats.spearmanr(fin["Vote_Count"], fin["Revenue"])[0],
            "rating_revenue": stats.spearmanr(frr["Rating"], frr["Revenue"])[0],
            "runtime_rating": stats.pearsonr(rr["Runtime"], rr["Rating"])[0],
            "runtime_revenue": stats.pearsonr(fr["Runtime"], fr["Revenue"])[0],
            "rating_trend_p": stats.linregress(core["Release_Year"], core["Rating"]).pvalue,
        },
    }


def main():
    s = summary()
    k, r = s["kpi"], s["r"]
    pd.set_option("display.width", 160)
    pd.set_option("display.max_columns", 10)
    pd.set_option("display.float_format", lambda v: f"{v:,.2f}")
    print(f"{k['movies']:,} released movies, {k['first_year']}-{k['last_year']} ({k['since_2000']:.0%} from 2000 on)")
    print(f"known revenue ${k['total_revenue'] / 1e9:.1f}B, known budgets ${k['total_budget'] / 1e9:.1f}B; "
          f"budget and revenue both known for {k['with_financials']:,}: "
          f"median ROI {k['median_roi']:.2f}x, {k['profitable']:.0%} earn more than their budget, {k['hit_2_5x']:.0%} earn 2.5x+")
    print(f"average rating {k['avg_rating']:.2f} ({k['rated']:,} movies with 50+ votes); average runtime {k['avg_runtime']:.0f} min")

    print("\nGENRES (a movie counts in each of its genres)\n", s["genre"])
    print("\nBUDGET TIERS\n", s["tier"])
    print(f"\nbudget vs revenue: r = {r['budget_revenue']:.2f}; vote count vs revenue: rho = {r['votes_revenue']:.2f}; "
          f"rating vs revenue: rho = {r['rating_revenue']:.2f}")
    print("\nTOP 10 BY REVENUE\n", s["top_revenue"].to_string(index=False))
    print("\nHIGHEST RAW RATINGS (why vote count matters)\n", s["raw_top"].to_string(index=False))
    print(f"\nTOP 10 BY WEIGHTED RATING (min {M_VOTES:,} votes)\n", s["top_rated"].to_string(index=False))
    print("\nDECADES\n", s["decade"])
    print(f"rating trend 1995-2015: p = {r['rating_trend_p']:.2f}")
    print("\nRUNTIME\n", s["runtime"])
    print(f"runtime vs rating: r = {r['runtime_rating']:.2f}; runtime vs revenue: r = {r['runtime_revenue']:.2f}")
    print("\nMEDIAN REVENUE BY RELEASE MONTH\n", (s["month"] / 1e6).round(1).to_dict())
    print("\nBEST ROI\n", s["top_roi"].to_string(index=False))
    print("\nBIGGEST LOSSES\n", s["flops"].to_string(index=False))


if __name__ == "__main__":
    main()
