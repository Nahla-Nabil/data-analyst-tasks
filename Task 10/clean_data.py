"""
Step 1: cleans the TMDB 5000 movies + credits files.

Reads  tmdb_5000_movies.csv, tmdb_5000_credits.csv   (Kaggle "TMDB 5000 Movie Dataset", unchanged)
Writes movies_clean.csv    one row per released movie, with genre, director, lead actor, money and rating columns
       movie_genres.csv    one row per movie-genre pair (a movie has 1-7 genres), used by the genre charts and slicer
"""

import json
import os

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
MIN_MONEY = 1_000      # budgets/revenues below $1,000 are typing errors (e.g. 7 or 30, meaning millions) -> unknown
MIN_VOTES = 50         # a rating needs at least 50 votes to count in averages


def names(cell, key="name"):
    return [d[key] for d in json.loads(cell)] if isinstance(cell, str) else []


def band(value, edges, labels):
    if pd.isna(value):
        return "Unknown"
    return labels[np.searchsorted(edges, value, side="right") - 1]


def main():
    movies = pd.read_csv(os.path.join(HERE, "tmdb_5000_movies.csv"))
    credits = pd.read_csv(os.path.join(HERE, "tmdb_5000_credits.csv"))
    print(f"raw: {len(movies):,} movies, {len(credits):,} credit rows")

    df = movies.merge(credits[["movie_id", "cast", "crew"]], left_on="id", right_on="movie_id", how="left")
    assert df["cast"].notna().all(), "every movie should have a credits row"

    # keep released movies with a release date (8 are Rumored / Post Production, 1 has no date)
    df = df[(df["status"] == "Released") & df["release_date"].notna()].copy()
    print(f"released with a date: {len(df):,}")

    # 0 means "not recorded" in TMDB, not "free" or "earned nothing"
    for c in ["budget", "revenue"]:
        bad = df[c] < MIN_MONEY
        print(f"{c}: {(df[c] == 0).sum():,} zeros and {((df[c] > 0) & bad).sum()} values under ${MIN_MONEY:,} set to unknown")
        df.loc[bad, c] = np.nan
    df.loc[df["runtime"] <= 0, "runtime"] = np.nan
    df.loc[df["vote_count"] == 0, "vote_average"] = np.nan

    date = pd.to_datetime(df["release_date"])
    genres = df["genres"].apply(names)
    crew = df["crew"].apply(json.loads)
    cast = df["cast"].apply(json.loads)
    fin = df["budget"].notna() & df["revenue"].notna()

    out = pd.DataFrame({
        "Movie_ID": df["id"],
        "Title": df["title"],
        "Title_Year": df["title"] + " (" + date.dt.year.astype(str) + ")",   # 3 titles are shared by two movies
        "Release_Date": date.dt.strftime("%Y-%m-%d"),
        "Release_Year": date.dt.year,
        "Decade": (date.dt.year // 10 * 10).astype(str) + "s",
        "Release_Month": date.dt.strftime("%b"),
        "Month_Num": date.dt.month,
        "Language": df["original_language"].map({"en": "English"}).fillna("Other languages"),
        "Primary_Genre": genres.apply(lambda g: g[0] if g else "No genre"),
        "Genre_Count": genres.str.len(),
        "Director": crew.apply(lambda c: next((p["name"] for p in c if p["job"] == "Director"), "Unknown")),
        "Lead_Actor": cast.apply(lambda c: min(c, key=lambda p: p["order"])["name"] if c else "Unknown"),
        "Budget": df["budget"],
        "Revenue": df["revenue"],
        "Profit": np.where(fin, df["revenue"] - df["budget"], np.nan),
        "ROI": np.where(fin, df["revenue"] / df["budget"], np.nan),
        "Financials_Known": np.where(fin, "Yes", "No"),
        "Runtime": df["runtime"],
        "Rating": df["vote_average"],
        "Vote_Count": df["vote_count"],
        "Rating_Reliable": np.where(df["vote_count"] >= MIN_VOTES, "Yes", "No"),
        "Popularity": df["popularity"].round(2),
    })
    out["Budget_Tier"] = [band(v, [0, 10e6, 40e6, 100e6], ["Under $10M", "$10M-40M", "$40M-100M", "$100M+"]) for v in out["Budget"]]
    out["Runtime_Band"] = [band(v, [0, 90, 110, 130, 150], ["Under 90 min", "90-109 min", "110-129 min", "130-149 min", "150+ min"])
                           for v in out["Runtime"]]
    out["Vote_Band"] = [band(v, [0, 50, 500, 2000, 5000], ["Under 50", "50-499", "500-1,999", "2,000-4,999", "5,000+"]) for v in out["Vote_Count"]]
    out["Partial_Year"] = np.where(out["Release_Year"] >= 2016, "Yes", "No")   # data was collected in early 2017
    for c in ["Budget", "Revenue", "Profit", "Runtime", "Vote_Count"]:
        out[c] = out[c].round().astype("Int64")
    out["ROI"] = out["ROI"].round(3)
    out = out.sort_values("Release_Date").reset_index(drop=True)
    out.to_csv(os.path.join(HERE, "movies_clean.csv"), index=False)

    pairs = pd.DataFrame({"Movie_ID": df["id"].values, "Genre": genres.values}).explode("Genre").dropna()
    pairs.to_csv(os.path.join(HERE, "movie_genres.csv"), index=False)

    print(f"clean: {len(out):,} movies x {out.shape[1]} columns; {len(pairs):,} movie-genre pairs; "
          f"{(out['Primary_Genre'] == 'No genre').sum()} movies with no genre")
    print(f"budget and revenue both known: {fin.sum():,} ({fin.mean():.0%}); runtime known: {out['Runtime'].notna().sum():,}; "
          f"ratings with {MIN_VOTES}+ votes: {(out['Rating_Reliable'] == 'Yes').sum():,}")


if __name__ == "__main__":
    main()
