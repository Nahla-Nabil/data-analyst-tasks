"""
Task 5 - KPI & Insight Extraction
Reads the cleaned Titanic dataset and computes the key metrics used in the
dashboard and the written insights summary.
"""

import pandas as pd

df = pd.read_csv("Cleaned_Titanic.csv")

lines = []
lines.append("# Task 5 - Key Insights\n")
lines.append(f"Dataset: {len(df)} passengers (Cleaned_Titanic.csv)\n")

lines.append("## ⚠ Data Quality Caveat (read first)\n")
lines.append(
    "`Survived` in this file matches `Sex` with **zero exceptions** across all 418 rows (every female = "
    "survived, every male = did not survive). That is the exact signature of Kaggle's `gender_submission.csv` "
    "naive benchmark, not individually verified outcomes - see `DATA_QUALITY_REPORT.md` for the full check. "
    "Because of this, any 'survival by sex' finding is tautological by construction (it is just restating the "
    "input), so it is reported below for completeness but should **not** be read as a discovered pattern. "
    "The other relationships (class, fare, family size, age, embarkation, cabin) are still meaningful because "
    "they come from genuine passenger records - Pclass/Fare/Age/Embarked/Cabin were not touched by this "
    "artifact - but readers should treat every `Survived`-based rate in this report as illustrative of the "
    "benchmark's structure rather than of real 1912 outcomes.\n")

# --- Core KPIs ---
overall_rate = df["Survived"].mean() * 100
lines.append("## Headline KPIs\n")
lines.append(f"- **Overall survival rate:** {overall_rate:.1f}%")
lines.append(f"- **Total passengers:** {len(df)}")
lines.append(f"- **Survivors:** {df['Survived'].sum()} | **Did not survive:** {(df['Survived']==0).sum()}")
lines.append(f"- **Average age:** {df['Age'].mean():.1f} | **Average fare:** ${df['Fare'].mean():.2f}")
lines.append(f"- **% traveling alone:** {df['IsAlone'].mean()*100:.1f}%")
lines.append(f"- **% with recorded cabin:** {df['HasCabin'].mean()*100:.1f}%\n")

# --- Survival by Sex (tautological - see caveat above) ---
by_sex = df.groupby("Sex", observed=True)["Survived"].agg(["mean", "count"])
by_sex["mean"] = (by_sex["mean"] * 100).round(1)
lines.append("## Survival by Sex ⚠ tautological (Survived is defined as Sex=='female')\n")
lines.append(by_sex.rename(columns={"mean": "survival_rate_%", "count": "passengers"}).to_markdown())
lines.append(f"\n**Insight:** Women show {by_sex.loc['female','mean']}% and men {by_sex.loc['male','mean']}% "
              f"by construction, not by observed outcome - this table just confirms the caveat above, it is "
              f"not evidence of 'women and children first' in this specific file.\n")

# --- "Survival" by Class -> actually reflects % female per class ---
by_class = df.groupby("ClassLabel", observed=True)["Survived"].agg(["mean", "count"]).sort_index()
by_class["mean"] = (by_class["mean"] * 100).round(1)
lines.append("## \"Survival Rate\" by Passenger Class (reads as % female per class)\n")
lines.append(by_class.rename(columns={"mean": "pct_female_%", "count": "passengers"}).to_markdown())
lines.append(f"\n**Insight:** Because `Survived` ≡ `Sex`, this table is really showing that 1st class had a "
              f"notably higher share of female passengers ({by_class.loc['1st Class','mean']}%) than 3rd class "
              f"({by_class.loc['3rd Class','mean']}%) - a genuine, non-circular fact about who was in each "
              f"cabin class, just not a survival finding.\n")

# --- "Survival" by Age Group -> actually reflects % female per age group ---
by_age = df.groupby("AgeGroup", observed=True)["Survived"].agg(["mean", "count"])
by_age["mean"] = (by_age["mean"] * 100).round(1)
lines.append("## \"Survival Rate\" by Age Group (reads as % female per age group)\n")
lines.append(by_age.rename(columns={"mean": "pct_female_%", "count": "passengers"}).to_markdown())
lines.append(f"\n**Insight:** Genuine, non-circular takeaway: the female share of passengers is lowest for "
              f"Teens and highest for Children/Young Adults in this dataset - useful for understanding the "
              f"passenger mix, not survival dynamics.\n")

# --- "Survival" by Family Size -> actually reflects % female per family size ---
by_family = df.groupby("FamilySize")["Survived"].agg(["mean", "count"])
by_family["mean"] = (by_family["mean"] * 100).round(1)
lines.append("## \"Survival Rate\" by Family Size (reads as % female per family-size group)\n")
lines.append(by_family.rename(columns={"mean": "pct_female_%", "count": "passengers"}).to_markdown())
lines.append(f"\n**Insight:** Genuine takeaway: passengers traveling completely alone (FamilySize=1) are "
              f"disproportionately male in this dataset, while small-family groups have a higher female share.\n")

# --- "Survival" by Embarkation Port -> actually reflects % female per port ---
by_embark = df.groupby("Embarked", observed=True)["Survived"].agg(["mean", "count"])
by_embark["mean"] = (by_embark["mean"] * 100).round(1)
lines.append("## \"Survival Rate\" by Embarkation Port (reads as % female per port)\n")
lines.append(by_embark.rename(columns={"mean": "pct_female_%", "count": "passengers"}).to_markdown())
lines.append(f"\n**Insight:** Genuine takeaway: the female share of boarding passengers differs by port; this "
              f"is a passenger-mix fact, not a survival-by-port finding (the earlier apparent 'port effect on "
              f"survival' is fully explained by each port's sex mix, not by the port itself).\n")

# --- "Survival" by Cabin Availability -> actually reflects % female among those with/without a recorded cabin ---
by_cabin = df.groupby("HasCabin")["Survived"].agg(["mean", "count"])
by_cabin["mean"] = (by_cabin["mean"] * 100).round(1)
lines.append("## \"Survival Rate\" by Cabin Record (reads as % female among cabin-recorded passengers)\n")
lines.append(by_cabin.rename(columns={"mean": "pct_female_%", "count": "passengers"}).to_markdown())
lines.append(f"\n**Insight:** Genuine takeaway: passengers with a recorded cabin number ({df['HasCabin'].mean()*100:.1f}% "
              f"of the file) skew female, consistent with the higher-class skew noted above (cabins were "
              f"recorded far more often for 1st class).\n")

# --- Survival by Title (also mostly reflects sex, since titles map ~1:1 to sex) ---
by_title = df.groupby("Title")["Survived"].agg(["mean", "count"]).sort_values("count", ascending=False)
by_title["mean"] = (by_title["mean"] * 100).round(1)
lines.append("## \"Survival Rate\" by Title ⚠ also mostly a restatement of sex (Mr/Master are male-only titles; "
              "Miss/Mrs are female-only)\n")
lines.append(by_title.rename(columns={"mean": "pct_female_equiv_%", "count": "passengers"}).to_markdown())

# --- Fare vs "Survival" -> actually Fare vs Sex ---
fare_corr = df["Fare"].corr(df["Survived"])
lines.append(f"\n## Fare vs \"Survival\" (i.e. Fare vs Sex)\n- Correlation between `Fare` and `Survived`: {fare_corr:.2f} "
              f"- given the caveat above, this is really a (weak) correlation between fare paid and passenger "
              f"sex in this file, not fare's effect on survival.\n")

with open("KEY_INSIGHTS.md", "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

print("Insights written to KEY_INSIGHTS.md")
print(f"\nOverall survival rate: {overall_rate:.1f}%")
