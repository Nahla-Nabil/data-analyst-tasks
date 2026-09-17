# Task 5 - Key Insights

Dataset: 418 passengers (Cleaned_Titanic.csv)

## ⚠ Data Quality Caveat (read first)

`Survived` in this file matches `Sex` with **zero exceptions** across all 418 rows (every female = survived, every male = did not survive). That is the exact signature of Kaggle's `gender_submission.csv` naive benchmark, not individually verified outcomes - see `DATA_QUALITY_REPORT.md` for the full check. Because of this, any 'survival by sex' finding is tautological by construction (it is just restating the input), so it is reported below for completeness but should **not** be read as a discovered pattern. The other relationships (class, fare, family size, age, embarkation, cabin) are still meaningful because they come from genuine passenger records - Pclass/Fare/Age/Embarked/Cabin were not touched by this artifact - but readers should treat every `Survived`-based rate in this report as illustrative of the benchmark's structure rather than of real 1912 outcomes.

## Headline KPIs

- **Overall survival rate:** 36.4%
- **Total passengers:** 418
- **Survivors:** 152 | **Did not survive:** 266
- **Average age:** 29.4 | **Average fare:** $35.56
- **% traveling alone:** 60.5%
- **% with recorded cabin:** 21.8%

## Survival by Sex ⚠ tautological (Survived is defined as Sex=='female')

| Sex    |   survival_rate_% |   passengers |
|:-------|------------------:|-------------:|
| female |               100 |          152 |
| male   |                 0 |          266 |

**Insight:** Women show 100.0% and men 0.0% by construction, not by observed outcome - this table just confirms the caveat above, it is not evidence of 'women and children first' in this specific file.

## "Survival Rate" by Passenger Class (reads as % female per class)

| ClassLabel   |   pct_female_% |   passengers |
|:-------------|---------------:|-------------:|
| 1st Class    |           46.7 |          107 |
| 2nd Class    |           32.3 |           93 |
| 3rd Class    |           33   |          218 |

**Insight:** Because `Survived` ≡ `Sex`, this table is really showing that 1st class had a notably higher share of female passengers (46.7%) than 3rd class (33.0%) - a genuine, non-circular fact about who was in each cabin class, just not a survival finding.

## "Survival Rate" by Age Group (reads as % female per age group)

| AgeGroup            |   pct_female_% |   passengers |
|:--------------------|---------------:|-------------:|
| Adult (36-60)       |           37.9 |          103 |
| Child (0-12)        |           41.4 |           29 |
| Senior (60+)        |           36.4 |           11 |
| Teen (13-18)        |           41.4 |           29 |
| Young Adult (19-35) |           34.6 |          246 |

**Insight:** Genuine, non-circular takeaway: the female share of passengers is lowest for Teens and highest for Children/Young Adults in this dataset - useful for understanding the passenger mix, not survival dynamics.

## "Survival Rate" by Family Size (reads as % female per family-size group)

|   FamilySize |   pct_female_% |   passengers |
|-------------:|---------------:|-------------:|
|            1 |           26.9 |          253 |
|            2 |           48.6 |           74 |
|            3 |           52.6 |           57 |
|            4 |           71.4 |           14 |
|            5 |           28.6 |            7 |
|            6 |           66.7 |            3 |
|            7 |           25   |            4 |
|            8 |           50   |            2 |
|           11 |           50   |            4 |

**Insight:** Genuine takeaway: passengers traveling completely alone (FamilySize=1) are disproportionately male in this dataset, while small-family groups have a higher female share.

## "Survival Rate" by Embarkation Port (reads as % female per port)

| Embarked   |   pct_female_% |   passengers |
|:-----------|---------------:|-------------:|
| C          |           39.2 |          102 |
| Q          |           52.2 |           46 |
| S          |           32.6 |          270 |

**Insight:** Genuine takeaway: the female share of boarding passengers differs by port; this is a passenger-mix fact, not a survival-by-port finding (the earlier apparent 'port effect on survival' is fully explained by each port's sex mix, not by the port itself).

## "Survival Rate" by Cabin Record (reads as % female among cabin-recorded passengers)

|   HasCabin |   pct_female_% |   passengers |
|-----------:|---------------:|-------------:|
|          0 |           33   |          327 |
|          1 |           48.4 |           91 |

**Insight:** Genuine takeaway: passengers with a recorded cabin number (21.8% of the file) skew female, consistent with the higher-class skew noted above (cabins were recorded far more often for 1st class).

## "Survival Rate" by Title ⚠ also mostly a restatement of sex (Mr/Master are male-only titles; Miss/Mrs are female-only)

| Title   |   pct_female_equiv_% |   passengers |
|:--------|---------------------:|-------------:|
| Mr      |                  0   |          240 |
| Miss    |                100   |           79 |
| Mrs     |                100   |           72 |
| Master  |                  0   |           21 |
| Rare    |                 16.7 |            6 |

## Fare vs "Survival" (i.e. Fare vs Sex)
- Correlation between `Fare` and `Survived`: 0.19 - given the caveat above, this is really a (weak) correlation between fare paid and passenger sex in this file, not fare's effect on survival.
