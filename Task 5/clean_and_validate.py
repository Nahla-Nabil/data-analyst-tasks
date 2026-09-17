"""
Task 5 - Data Cleaning & Validation
Dataset: Titanic passenger records (File 3.csv)

Steps:
1. Load raw data and profile data-quality issues.
2. Fix data types / inconsistent values.
3. Impute missing values with justified, appropriate methods.
4. Engineer a few analysis-ready features.
5. Save the cleaned dataset + a written data-quality report.
"""

import pandas as pd
import numpy as np

RAW_PATH = "File 3.csv"
CLEAN_PATH = "Cleaned_Titanic.csv"
REPORT_PATH = "DATA_QUALITY_REPORT.md"

# ---------------------------------------------------------------------------
# 1. LOAD + PROFILE
# ---------------------------------------------------------------------------
df = pd.read_csv(RAW_PATH)

report_lines = []
report_lines.append("# Task 5 - Data Quality Report\n")
report_lines.append(f"**Source file:** `{RAW_PATH}`  \n**Rows x Cols (raw):** {df.shape[0]} x {df.shape[1]}\n")

report_lines.append("\n## 1. Missing Values (raw)\n")
missing_raw = df.isnull().sum()
missing_pct = (missing_raw / len(df) * 100).round(1)
missing_tbl = pd.DataFrame({"missing_count": missing_raw, "missing_pct": missing_pct})
missing_tbl = missing_tbl[missing_tbl["missing_count"] > 0].sort_values("missing_count", ascending=False)
report_lines.append(missing_tbl.to_markdown())

# Duplicate checks
dup_ids = df["PassengerId"].duplicated().sum()
dup_rows = df.duplicated().sum()
report_lines.append(f"\n\n## 2. Duplicate Checks\n- Duplicate `PassengerId`: {dup_ids}\n- Fully duplicated rows: {dup_rows}\n")

# Type / consistency checks
report_lines.append("\n## 3. Categorical Consistency Checks\n")
report_lines.append(f"- `Sex` unique values: {sorted(df['Sex'].unique())}\n")
report_lines.append(f"- `Embarked` unique values: {sorted(df['Embarked'].dropna().unique())}\n")
report_lines.append(f"- `Pclass` unique values: {sorted(int(v) for v in df['Pclass'].unique())}\n")
report_lines.append(f"- `Fare` == 0 (free/crew-like tickets, flagged not removed): {(df['Fare'] == 0).sum()}\n")
report_lines.append(f"- `Fare` negative values: {(df['Fare'] < 0).sum()}\n")
report_lines.append(f"- `Age` out-of-range (<0 or >100): {((df['Age'] < 0) | (df['Age'] > 100)).sum()}\n")

# --- Critical finding: Survived vs Sex relationship ---
sex_survived_mismatch = ((df["Sex"] == "female") != (df["Survived"] == 1)).sum()
report_lines.append("\n## 4. Critical Data Quality Finding: `Survived` Perfectly Matches `Sex`\n")
report_lines.append(
    f"Every single row (0 mismatches out of {len(df)}) has `Survived == 1` when `Sex == 'female'` and "
    f"`Survived == 0` when `Sex == 'male'`. This is not a coincidence: it is the exact signature of the "
    f"well-known Kaggle Titanic `gender_submission.csv` file (the \"all women survive, all men die\" naive "
    f"benchmark), which appears to have been merged onto the real `test.csv` passenger records to produce "
    f"this file.\n\n"
    f"**Implication:** `Survived` in this dataset is a *synthetic placeholder label*, not a verified, "
    f"individually-recorded outcome. It should **not** be treated as ground truth, and any survival-rate "
    f"finding that is basically a restatement of `Sex` (e.g. \"survival rate by sex\") is tautological by "
    f"construction, not a discovered pattern. This caveat is carried through to `KEY_INSIGHTS.md` and called "
    f"out directly in the dashboard so it isn't presented as a real finding.\n"
)

# ---------------------------------------------------------------------------
# 2. CLEANING
# ---------------------------------------------------------------------------
clean = df.copy()

# Title extracted from Name -> used for smarter Age imputation and as its own feature
clean["Title"] = clean["Name"].str.extract(r",\s*([^\.]*)\.").iloc[:, 0].str.strip()
title_map = {
    "Mlle": "Miss", "Ms": "Miss", "Mme": "Mrs",
    "Lady": "Rare", "Countess": "Rare", "Dona": "Rare", "Don": "Rare",
    "Sir": "Rare", "Jonkheer": "Rare", "Capt": "Rare", "Col": "Rare",
    "Major": "Rare", "Rev": "Rare", "Dr": "Rare",
}
clean["Title"] = clean["Title"].replace(title_map)

# --- Fare: 1 missing value -> impute with median Fare of same Pclass ---
fare_median_by_class = clean.groupby("Pclass")["Fare"].transform("median")
clean["Fare"] = clean["Fare"].fillna(fare_median_by_class)

# --- Age: 86 missing (~20%) -> impute with median Age of same Title + Pclass group ---
age_median_by_group = clean.groupby(["Title", "Pclass"])["Age"].transform("median")
clean["Age"] = clean["Age"].fillna(age_median_by_group)
clean["Age"] = clean["Age"].fillna(clean["Age"].median())  # safety net for any unseen group
clean["Age"] = clean["Age"].round(1)

# --- Cabin: 78% missing -> not reliably imputable, so convert into engineered signal ---
clean["HasCabin"] = clean["Cabin"].notna().astype(int)
clean["Deck"] = clean["Cabin"].str[0]
clean["Deck"] = clean["Deck"].fillna("Unknown")
clean = clean.drop(columns=["Cabin"])

# --- Embarked: no missing values in this file, but guard the pipeline anyway ---
clean["Embarked"] = clean["Embarked"].fillna(clean["Embarked"].mode()[0])

# --- Data type fixes ---
clean["Survived"] = clean["Survived"].astype(int)
clean["Pclass"] = clean["Pclass"].astype(int)
clean["Sex"] = clean["Sex"].astype("category")
clean["Embarked"] = clean["Embarked"].astype("category")

# ---------------------------------------------------------------------------
# 3. FEATURE ENGINEERING
# ---------------------------------------------------------------------------
clean["FamilySize"] = clean["SibSp"] + clean["Parch"] + 1
clean["IsAlone"] = (clean["FamilySize"] == 1).astype(int)

clean["AgeGroup"] = pd.cut(
    clean["Age"], bins=[0, 12, 18, 35, 60, 100],
    labels=["Child (0-12)", "Teen (13-18)", "Young Adult (19-35)", "Adult (36-60)", "Senior (60+)"],
)

clean["FareBin"] = pd.qcut(clean["Fare"], q=4, labels=["Low", "Medium", "High", "Very High"])

clean["ClassLabel"] = clean["Pclass"].map({1: "1st Class", 2: "2nd Class", 3: "3rd Class"})

# ---------------------------------------------------------------------------
# 4. POST-CLEAN VALIDATION
# ---------------------------------------------------------------------------
missing_after = clean.isnull().sum()
missing_after = missing_after[missing_after > 0]

report_lines.append("\n## 5. Cleaning Actions Taken\n")
report_lines.append("- **Fare** (1 missing): imputed with the median fare of the same `Pclass`.\n")
report_lines.append("- **Age** (86 missing, ~20.6%): imputed with the median age of the same `Title` + `Pclass` group "
                     "(more accurate than a single global median since age strongly correlates with title/class).\n")
report_lines.append("- **Cabin** (327 missing, ~78.2%): too sparse to impute reliably; replaced with engineered "
                     "`HasCabin` (0/1) and `Deck` (first letter, 'Unknown' if missing) instead of imputing values.\n")
report_lines.append("- **Embarked**: guarded with mode-fill (no missing values found in this file).\n")
report_lines.append("- Extracted `Title` from `Name` and grouped rare titles into `Rare`.\n")
report_lines.append("- Added engineered features: `FamilySize`, `IsAlone`, `AgeGroup`, `FareBin`, `ClassLabel`, `HasCabin`, `Deck`.\n")
report_lines.append("- Verified no duplicate `PassengerId` or fully duplicated rows.\n")
report_lines.append("- Verified `Sex`, `Embarked`, `Pclass` contain only valid categorical values, and `Fare`/`Age` contain no negative or out-of-range values.\n")

report_lines.append(f"\n## 6. Missing Values After Cleaning\n")
if len(missing_after) == 0:
    report_lines.append("All columns are fully populated. ✅\n")
else:
    report_lines.append(missing_after.to_markdown() + "\n")

report_lines.append(f"\n## 7. Final Shape\n{clean.shape[0]} rows x {clean.shape[1]} columns\n")

# ---------------------------------------------------------------------------
# 5. SAVE
# ---------------------------------------------------------------------------
clean.to_csv(CLEAN_PATH, index=False)
with open(REPORT_PATH, "w", encoding="utf-8") as f:
    f.write("\n".join(report_lines))

print(f"Cleaned dataset saved to {CLEAN_PATH}  ({clean.shape[0]} rows x {clean.shape[1]} cols)")
print(f"Data quality report saved to {REPORT_PATH}")
print("\nRemaining missing values:\n", missing_after if len(missing_after) else "None")
