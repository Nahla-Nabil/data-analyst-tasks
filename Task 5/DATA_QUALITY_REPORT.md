# Task 5 - Data Quality Report

**Source file:** `File 3.csv`  
**Rows x Cols (raw):** 418 x 12


## 1. Missing Values (raw)

|       |   missing_count |   missing_pct |
|:------|----------------:|--------------:|
| Cabin |             327 |          78.2 |
| Age   |              86 |          20.6 |
| Fare  |               1 |           0.2 |


## 2. Duplicate Checks
- Duplicate `PassengerId`: 0
- Fully duplicated rows: 0


## 3. Categorical Consistency Checks

- `Sex` unique values: ['female', 'male']

- `Embarked` unique values: ['C', 'Q', 'S']

- `Pclass` unique values: [1, 2, 3]

- `Fare` == 0 (free/crew-like tickets, flagged not removed): 2

- `Fare` negative values: 0

- `Age` out-of-range (<0 or >100): 0


## 4. Critical Data Quality Finding: `Survived` Perfectly Matches `Sex`

Every single row (0 mismatches out of 418) has `Survived == 1` when `Sex == 'female'` and `Survived == 0` when `Sex == 'male'`. This is not a coincidence: it is the exact signature of the well-known Kaggle Titanic `gender_submission.csv` file (the "all women survive, all men die" naive benchmark), which appears to have been merged onto the real `test.csv` passenger records to produce this file.

**Implication:** `Survived` in this dataset is a *synthetic placeholder label*, not a verified, individually-recorded outcome. It should **not** be treated as ground truth, and any survival-rate finding that is basically a restatement of `Sex` (e.g. "survival rate by sex") is tautological by construction, not a discovered pattern. This caveat is carried through to `KEY_INSIGHTS.md` and called out directly in the dashboard so it isn't presented as a real finding.


## 5. Cleaning Actions Taken

- **Fare** (1 missing): imputed with the median fare of the same `Pclass`.

- **Age** (86 missing, ~20.6%): imputed with the median age of the same `Title` + `Pclass` group (more accurate than a single global median since age strongly correlates with title/class).

- **Cabin** (327 missing, ~78.2%): too sparse to impute reliably; replaced with engineered `HasCabin` (0/1) and `Deck` (first letter, 'Unknown' if missing) instead of imputing values.

- **Embarked**: guarded with mode-fill (no missing values found in this file).

- Extracted `Title` from `Name` and grouped rare titles into `Rare`.

- Added engineered features: `FamilySize`, `IsAlone`, `AgeGroup`, `FareBin`, `ClassLabel`, `HasCabin`, `Deck`.

- Verified no duplicate `PassengerId` or fully duplicated rows.

- Verified `Sex`, `Embarked`, `Pclass` contain only valid categorical values, and `Fare`/`Age` contain no negative or out-of-range values.


## 6. Missing Values After Cleaning

All columns are fully populated. ✅


## 7. Final Shape
418 rows x 19 columns
