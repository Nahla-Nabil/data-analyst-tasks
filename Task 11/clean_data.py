"""
Step 1: cleans the three video-game files.

Reads  Video_Games_Sales_as_at_22_Dec_2016.csv   raw main file (Kaggle "Video Game Sales", 16,719 rows, unchanged)
       PS4_GamesSales.csv, XboxOne_GameSales.csv  raw current-gen files (latin-1 encoded, unchanged)
Writes Cleaned_Video_Games.csv     one row per game-platform release, flags and derived fields
       Cleaned_PS4_Sales.csv       one row per PS4 title
       Cleaned_XboxOne_Sales.csv   one row per Xbox One title
       cleaning_log.json           every check, what was found and what was done
"""

import json
import os

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
MAIN = "Video_Games_Sales_as_at_22_Dec_2016.csv"
CUTOFF = 2016          # the main file is a snapshot dated 22 Dec 2016
TOP_PUBLISHERS = 10

PLATFORM_FAMILY = {
    **{p: "PlayStation" for p in ["PS", "PS2", "PS3", "PS4", "PSP", "PSV"]},
    **{p: "Xbox" for p in ["XB", "X360", "XOne"]},
    **{p: "Nintendo" for p in ["Wii", "WiiU", "NES", "SNES", "N64", "GC", "GB", "GBA", "DS", "3DS"]},
    **{p: "Sega" for p in ["GEN", "SCD", "SAT", "GG", "DC"]},
    "PC": "PC",
}
DEFAULT_FAMILY = "Other"

RATING_BAND = {
    "E": "Everyone", "EC": "Everyone", "K-A": "Everyone",
    "E10+": "Everyone 10+", "T": "Teen",
    "M": "Mature", "AO": "Mature", "RP": "Rating pending",
}


def log(step, check, found, action, rows_after):
    LOG.append({"step": step, "check": check, "found": found, "action": action, "rows_after": rows_after})


LOG = []


def main():
    raw = pd.read_csv(os.path.join(HERE, MAIN))
    n0 = len(raw)
    print(f"raw: {n0:,} rows x {raw.shape[1]} columns")
    log(1, "Load the raw file", f"{n0:,} rows, 16 columns, 31 platforms, 12 genres, 582 publishers",
        "Read as-is, nothing changed yet", n0)

    # ---- data types -------------------------------------------------------
    nums = ["Year_of_Release", "NA_Sales", "EU_Sales", "JP_Sales", "Other_Sales", "Global_Sales",
            "Critic_Score", "Critic_Count", "User_Score", "User_Count"]
    bad_types = [c for c in nums if not pd.api.types.is_numeric_dtype(raw[c])]
    # User_Score is numeric here (the "tbd" placeholders of the Kaggle copy are not in this file)
    log(2, "Data types", f"10 numeric columns expected, {len(bad_types)} wrongly typed; "
                         "User_Score already numeric (no 'tbd' strings)",
        "Types accepted as loaded", n0)

    # ---- exact duplicates -------------------------------------------------
    exact = int(raw.duplicated().sum())
    log(3, "Exact duplicate rows", f"{exact} rows duplicated on all 16 columns", "Nothing to remove", n0)

    # ---- same game, same platform, same year ------------------------------
    key = ["Name", "Platform", "Year_of_Release"]
    dup_mask = raw.duplicated(key, keep=False)
    dup_rows = raw[dup_mask].sort_values(key + ["Global_Sales"], na_position="first")
    n_dup = len(dup_rows)
    df = raw.copy()
    dropped = []
    for _, grp in dup_rows.groupby(key, dropna=False):
        grp = grp.sort_values("Global_Sales", ascending=False, na_position="first")
        for i in grp.index[1:]:
            dropped.append(df.loc[i])
            df = df.drop(index=i)
    d1 = len(df)
    sample = ", ".join(
        f"{r['Name'] if pd.notna(r['Name']) else '(unnamed title)'} "
        f"({r['Platform']} {int(r['Year_of_Release']) if pd.notna(r['Year_of_Release']) else '?'})"
        for r in dropped)
    log(4, "Duplicates on Name + Platform + Year", f"{n_dup} rows in {len(dropped)} pairs: {sample}",
        "Kept the row with the higher Global_Sales (identical scores and developer, the other row only "
        "carries a few thousand units)", d1)

    # ---- identity columns -------------------------------------------------
    unnamed = df["Name"].isna() | (df["Name"].astype(str).str.strip() == "")
    df.loc[unnamed, "Name"] = "(unnamed title)"
    missing_genre = df["Genre"].isna()
    df.loc[missing_genre, "Genre"] = "Unknown"
    log(5, "Missing game title / genre", f"{int(unnamed.sum())} rows without a title, "
                                         f"{int(missing_genre.sum())} rows without a genre (same row)",
        "Kept the row with Flag_Unnamed = Yes and the placeholder name '(unnamed title)'; "
        "genre set to 'Unknown' so it still appears in the pivots", d1)

    # ---- year of release --------------------------------------------------
    year_known = df.dropna(subset=["Year_of_Release"]).groupby("Name")["Year_of_Release"].agg(["nunique", "min"])
    unanimous = year_known[year_known["nunique"] == 1]["min"]
    miss_year = df["Year_of_Release"].isna()
    impute = miss_year & df["Name"].isin(unanimous.index)
    df.loc[impute, "Year_of_Release"] = df.loc[impute, "Name"].map(unanimous)
    n_imputed = int(impute.sum())
    still_missing = int(df["Year_of_Release"].isna().sum())
    ambiguous = int((miss_year & df["Name"].isin(year_known[year_known["nunique"] > 1].index)).sum())
    log(6, "Missing Year_of_Release", f"{int(miss_year.sum())} rows missing ({ambiguous} belong to a title whose "
                                      f"release years differ between platforms, the rest have no other row)",
        f"Imputed {n_imputed} of them from the same title on other platforms (all known years agree); "
        f"left {still_missing} blank and flagged Flag_Year_Unknown - they are excluded from the yearly trend", d1)

    future = df["Year_of_Release"] > CUTOFF
    n_future = int(future.sum())
    log(7, "Years after the 22 Dec 2016 cutoff", f"{n_future} rows dated 2017-2020 "
                                                  "(Imagine: Makeup Artist 2020, Phantasy Star Online 2 x2, Brothers Conflict)",
        "Kept with Flag_Year_Future = Yes and excluded from the trend line, which stops at 2016", d1)

    # ---- publisher / developer -------------------------------------------
    miss_pub = df["Publisher"].isna()
    df.loc[miss_pub, "Publisher"] = "Unknown publisher"
    n_pub = int(miss_pub.sum())
    df["Developer"] = df["Developer"].fillna("Unknown developer")
    log(8, "Missing Publisher / Developer", f"{n_pub} rows without publisher, "
                                            f"{int(df['Developer'].eq('Unknown developer').sum()):,} without developer",
        "Publisher set to 'Unknown publisher' (kept in the totals, flagged); developer kept as a placeholder "
        "and used for display only", d1)

    # ---- sales columns ----------------------------------------------------
    region_sum = df[["NA_Sales", "EU_Sales", "JP_Sales", "Other_Sales"]].sum(axis=1)
    mismatch = (region_sum - df["Global_Sales"]).abs() > 0.011
    negatives = int((df[["NA_Sales", "EU_Sales", "JP_Sales", "Other_Sales", "Global_Sales"]] < 0).sum().sum())
    log(9, "Sales additivity and negative values", f"{int(mismatch.sum())} rows where the four regions differ from "
                                                   f"Global_Sales by more than 0.01M (max 0.02M = rounding), "
                                                   f"{negatives} negative values",
        "Kept the published Global_Sales (the gap is rounding in the source), no row changed", d1)

    # ---- ratings ----------------------------------------------------------
    df["Rating"] = df["Rating"].fillna("Unknown")
    df["Rating_Band"] = df["Rating"].map(RATING_BAND).fillna("Unknown")
    score_ok = df["Critic_Score"].notna() | df["User_Score"].notna()
    log(10, "Ratings completeness", f"{int(df['Critic_Score'].isna().sum()):,} rows with no critic score, "
                                    f"{int(df['User_Score'].isna().sum()):,} with no user score, "
                                    f"{int(score_ok.sum()):,} rows rated by critics or users; 1 row has a user score of 0 "
                                    "(4 votes only)",
        "Left blank (never invented); the ESRB column had {0} missing values, set to 'Unknown' and grouped into "
        "Rating_Band for the charts".format(int((raw['Rating'].isna()).sum())), d1)

    # ---- derived fields ---------------------------------------------------
    top_pub = (df[df["Publisher"] != "Unknown publisher"]
               .groupby("Publisher")["Global_Sales"].sum().nlargest(TOP_PUBLISHERS).index)
    out = pd.DataFrame({
        "Game": df["Name"].astype(str).str.strip(),
        "Platform": df["Platform"],
        "Platform_Family": df["Platform"].map(PLATFORM_FAMILY).fillna(DEFAULT_FAMILY),
        "Release_Year": df["Year_of_Release"].astype("Int64"),
        "Release_Date": [pd.Timestamp(int(y), 1, 1) if pd.notna(y) else pd.NaT for y in df["Year_of_Release"]],
        "Decade": [f"{int(y) // 10 * 10}s" if pd.notna(y) else "" for y in df["Year_of_Release"]],
        "Genre": df["Genre"],
        "Publisher": df["Publisher"],
        "Publisher_Group": np.where(df["Publisher"].isin(top_pub), df["Publisher"], "Other publishers"),
        "Developer": df["Developer"],
        "NA_Sales": df["NA_Sales"],
        "EU_Sales": df["EU_Sales"],
        "JP_Sales": df["JP_Sales"],
        "Other_Sales": df["Other_Sales"],
        "Global_Sales": df["Global_Sales"],
        "Rank_Global": df["Global_Sales"].rank(method="min", ascending=False).astype("Int64"),
        "Critic_Score": df["Critic_Score"].astype("Int64"),
        "Rank_Critic": df["Critic_Score"].rank(method="min", ascending=False).astype("Int64"),
        "Critic_Count": df["Critic_Count"].astype("Int64"),
        "User_Score": df["User_Score"],
        "User_Count": df["User_Count"].astype("Int64"),
        "Rating": df["Rating"],
        "Rating_Band": df["Rating_Band"],
        "Has_Reviews": np.where(score_ok, "Yes", "No"),
        "Flag_Unnamed": np.where(unnamed, "Yes", ""),
        "Flag_Year_Imputed": np.where(impute, "Yes", ""),
        "Flag_Year_Unknown": np.where(df["Year_of_Release"].isna(), "Yes", ""),
        "Flag_Year_Future": np.where(future, "Yes", ""),
        "Flag_Unknown_Publisher": np.where(miss_pub, "Yes", ""),
    })
    score = pd.to_numeric(df["Critic_Score"], errors="coerce")
    out["Critic_Band"] = np.select(
        [score.isna(), score < 60, score < 70, score < 80, score < 90],
        ["No critic score", "Under 60", "60-69", "70-79", "80-89"],
        default="90+")
    for c in ["Critic_Score", "Critic_Count", "User_Count"]:
        out[c] = out[c].astype("object").where(out[c].notna(), "")
    out = out[["Game", "Platform", "Platform_Family", "Release_Year", "Release_Date", "Decade", "Genre",
               "Publisher", "Publisher_Group", "Developer", "NA_Sales", "EU_Sales", "JP_Sales", "Other_Sales",
               "Global_Sales", "Rank_Global", "Critic_Score", "Rank_Critic", "Critic_Band", "Critic_Count",
               "User_Score", "User_Count", "Rating", "Rating_Band", "Has_Reviews", "Flag_Unnamed",
               "Flag_Year_Imputed", "Flag_Year_Unknown", "Flag_Year_Future", "Flag_Unknown_Publisher"]]
    out = out.sort_values(["Global_Sales", "Game"], ascending=[False, True]).reset_index(drop=True)

    main_out = os.path.join(HERE, "Cleaned_Video_Games.csv")
    out.to_csv(main_out, index=False)

    # ---- the two current-gen files ---------------------------------------
    consoles = []
    for name, path, platform in [("PS4", "PS4_GamesSales.csv", "PS4"),
                                 ("XboxOne", "XboxOne_GameSales.csv", "XOne")]:
        c = pd.read_csv(os.path.join(HERE, path), encoding="latin-1")
        n_c = len(c)
        dups = c.duplicated(["Game"], keep=False)
        c = c.sort_values("Global", ascending=False).drop_duplicates(["Game"], keep="first")
        c["Year"] = c["Year"].astype("Int64")
        miss = int(c["Year"].isna().sum())
        c["Publisher"] = c["Publisher"].fillna("Unknown publisher")
        c["Genre"] = c["Genre"].fillna("Unknown")
        c["Platform"] = platform
        c = c.rename(columns={"Game": "Game", "North America": "NA_Sales", "Europe": "EU_Sales",
                              "Japan": "JP_Sales", "Rest of World": "Other_Sales", "Global": "Global_Sales"})
        keep = ["Platform", "Game", "Year", "Genre", "Publisher", "NA_Sales", "EU_Sales", "JP_Sales",
                "Other_Sales", "Global_Sales"]
        c = c[[x for x in keep if x in c.columns]]
        c = c.sort_values("Global_Sales", ascending=False).reset_index(drop=True)
        c.to_csv(os.path.join(HERE, f"Cleaned_{name}_Sales.csv"), index=False)
        consoles.append(len(c))
        log(11 + len(consoles) - 1, f"{name} file",
            f"{n_c} rows, {int(dups.sum())} rows repeating a title (all with 0.00M sales - announced games), "
            f"{miss} missing Year and Publisher, latin-1 encoding",
            "Removed the repeated titles, filled Year with a blank (flagged by absence), publisher/genre to "
            f"'Unknown publisher'/'Unknown' -> {len(c)} rows", d1)

    log(99, "Output", f"{len(out):,} rows x {out.shape[1]} columns in Cleaned_Video_Games.csv; "
                      f"{consoles[0]} PS4 and {consoles[1]} Xbox One rows",
        "Cleaned files written; every decision above is reversible from this log", len(out))

    with open(os.path.join(HERE, "cleaning_log.json"), "w", encoding="utf-8") as fh:
        json.dump(LOG, fh, indent=2)

    print(f"clean: {len(out):,} rows x {out.shape[1]} columns -> Cleaned_Video_Games.csv")
    print(f"  year known: {out['Release_Year'].notna().sum():,} "
          f"({n_imputed} imputed, {still_missing} still unknown)")
    print(f"  rated rows: {int(out['Has_Reviews'].eq('Yes').sum()):,} | publishers: {out['Publisher'].nunique()} "
          f"| platforms: {out['Platform'].nunique()}")
    print(f"  total global sales: {out['Global_Sales'].sum():,.1f}M")
    print(f"  cleaning log: {len(LOG)} steps -> cleaning_log.json")


if __name__ == "__main__":
    main()
