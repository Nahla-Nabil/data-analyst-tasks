# Data Quality Report: Customer Dataset

**Source:** `Customers_Fakedata.csv`: 2,150 rows × 12 columns (CustomerID, Name, Age, Gender, Email, Phone, PurchaseAmount, PurchaseDate, ProductCategory, Rating, plus 2 stray columns).
**Output:** `Cleaned_Customers.csv`: 2,100 rows × 31 columns.
**Script:** `clean_data.py`. Every check below is re-run from the raw file, and each count is logged in `cleaning_log.json`.

## Summary

Almost every column has a problem, and the problems are spread across different rows. After cleaning, **only 204 of 2,100 customers (9.7%) have a valid value in all six analytic fields** (age, gender, amount, date, category, rating).
Deleting incomplete rows would therefore throw away 90% of the data. Instead, each invalid value was blanked, its reason was kept in a `*_Status` column, and every metric uses all the rows that are valid for that metric.

| # | Issue | Rows | Action |
|---|---|---:|---|
| 1 | Column `'  Gender  '` (header padded with spaces) is an exact copy of `Gender`; column `Unnamed` is 100% empty | all | Both dropped |
| 2 | Exact duplicate rows, all appended at the end of the file (lines 2102–2151) | 50 | Removed; `CustomerID` is now unique |
| 3 | Age **-1** (553) and **200** (546): impossible values used as placeholders | 1,099 | Blanked, `Age_Status` keeps the reason |
| 4 | Age blank | 506 | Kept blank; **not imputed** (see section 3) |
| 5 | Gender written 6 ways (`M`, `Male`, `male`, `F`, `Female`, `female`) | 1,833 | Mapped to Male / Female |
| 6 | Gender blank | 267 | `Unknown`, kept as its own group |
| 7 | Recorded gender contradicts a clearly gendered first name | 797 of 1,602 (50%) | Flagged in `Gender_Name_Conflict`, not changed |
| 8 | Phone: blank (1,057) or one of two dummy numbers `0123456789` / `0987654321` (1,043) | 2,100 | Column dropped (no real number exists), `Phone_Status` kept |
| 9 | Purchase amount blank | 97 | Kept blank; **not imputed** |
| 10 | Purchase date `32/13/2020` (day 32, month 13) | 118 | Blanked, `Date_Status = Invalid`; excluded from time analysis only |
| 11 | Product category blank | 565 (27%) | `Unknown`, kept visible as its own group |
| 12 | Rating **10** on a 1–5 scale | 291 | Blanked, `Rating_Status = Out of range (10)` |
| 13 | Rating blank | 322 | Kept blank |
| 14 | First and last month only partly covered (27 Oct 2022, 23 Jul 2025) | 65 | `Full_Month` flag; trends use full months only |

## 1. Structure and duplicates

- The header has a second `Gender` column named `'  Gender  '` (spaces around the name). It is identical to `Gender` in all 2,150 rows, so it was dropped. `Unnamed` has no value in any row.
- 50 rows are exact copies of earlier rows. All of them sit at the end of the file, which is the typical result of a batch being appended twice. Every repeated `CustomerID` belongs to one of these exact copies, so removing them leaves one row per ID (`CUST1000`–`CUST3099`).
- **Each customer has exactly one purchase.** Repeat-purchase rate and customer lifetime value therefore cannot be measured from this file.

## 2. Identity fields

- **Names are not unique:** 48 name combinations (8 first names × 6 last names) cover 2,100 customers.
- **Emails are not unique either:** every address is built as `first.last@domain` (100% of rows), so there are only 144 distinct addresses. A name or an email cannot identify a person, so `Customer_ID` is the only key.
- **Gender vs first name:** the recorded gender contradicts a clearly gendered first name in **50%** of the rows where it can be tested (for example *Sara* recorded as Male 125 times, *Ahmed* as Female 98 times). A chi-square test finds no relationship at all between first name and recorded gender (p = 0.12), which is what random assignment produces. It is impossible to tell which field is wrong, so gender was kept as recorded, and every gender result carries this caveat. *Alaa*, which is used for both sexes, was not tested.
- **Phone:** not one real number. Half the rows are blank, and the other half hold one of two digit sequences. The column was dropped; `Phone_Status` records which case applied. **0% of customers can be reached by phone.**

## 3. Age: 76% unusable, and not imputed

| Age value | Customers | Share |
|---|---:|---:|
| Real age (15–90) | 495 | 23.6% |
| Blank | 506 | 24.1% |
| -1 (placeholder) | 553 | 26.3% |
| 200 (placeholder) | 546 | 26.0% |

`-1` and `200` cannot be ages, and each appears more than 500 times, so they are system placeholders for "unknown", not typing errors. **Why they were not imputed:** a median fill would invent 76% of the column and turn the age distribution into one spike at 55, and any age comparison would then mostly compare invented values.
Age results therefore use the 495 real ages, which run from 15 to 90 (median 55). Because age is missing independently of every other field (see section 8), these 495 are a fair sample. Age groups use equal 15-year bands (15–29, 30–44, 45–59, 60–74, 75–90), so that no band looks bigger just because it is wider.

## 4. Purchase amount

- Recorded amounts run from **$5.06 to $999.56**. There are no zero or negative values, and no value lies outside the IQR fences.
- 97 amounts are blank. They were **not imputed**, because an imputed amount would be invented revenue. Revenue KPIs are labelled *recorded revenue* and use the 2,003 priced purchases. At the average order value, the 97 missing amounts represent roughly $49K (about 5%) of unrecorded revenue.

## 5. Purchase date

- Format `M/D/YYYY`. 118 rows hold `32/13/2020`, which is not a real date (day 32 of month 13), and there is no way to recover the intended date. They were blanked. These rows stay in all non-time analyses and are excluded from trends.
- Valid dates run from **27 Oct 2022 to 23 Jul 2025**, exactly 1,000 days, with no future dates.
- **Partial periods:** October 2022 (5 days) and July 2025 (23 days) are incomplete months. Left in, they would make the first month look like a slow start and the last quarter look like a collapse (2025-Q3 has 55 purchases against about 180 in a full quarter). `Full_Month` marks the 32 complete months (Nov 2022 – Jun 2025), and monthly trends and growth rates use only those.
- **Calendar coverage:** because the window is 1,000 days, August and September occur in only 2 of the years covered, January–June in 3. Month-of-year comparisons are therefore made per 30 days of data, not on raw totals (see KEY_INSIGHTS.md, finding 5).

## 6. Product category and rating

- `ProductCategory` has 5 consistent values (Books, Clothing, Electronics, Home, Toys), and **565 purchases (27%) have none**. These were kept as `Unknown` rather than dropped. They carry **$268K, 26% of recorded revenue**, so hiding them would misstate every category's share.
- `Rating` should be 1–5. **291 ratings are `10`.** No 6, 7, 8 or 9 exists anywhere, so these are not ratings on a 10-point scale that could be rescaled to 5. They are invalid entries, so they were blanked. Capping them at 5 would have added 291 fake top scores and nearly doubled the 5-star count (307 → 598). With 322 blanks as well, **1,487 valid ratings (70.8%)** remain.
- `Rating_Band` groups valid ratings into Dissatisfied (1–2), Neutral (3) and Satisfied (4–5).

## 7. Columns added

`First_Name`, `Last_Name`, `Gender_Name_Conflict`, `Age_Group`, `Age_Status`, `Email_Domain`, `Phone_Status`, `Amount_Status`, `Spend_Band` (under $250 / $250–499 / $500–749 / $750+),
`Date_Status`, `Year`, `Quarter`, `Year_Month`, `Month_Num`, `Month_Name`, `Weekday_Num`, `Weekday`, `Full_Month`, `Rating_Status`, `Rating_Band`, `Valid_Fields` (0–6), `Complete_Record`.

## 8. How the missing values behave

| Field | Usable | Blank | Invalid |
|---|---:|---:|---:|
| Purchase amount | 95.4% | 4.6% | – |
| Purchase date | 94.4% | – | 5.6% |
| Gender | 87.3% | 12.7% | – |
| Product category | 73.1% | 26.9% | – |
| Rating | 70.8% | 15.3% | 13.9% |
| Age | 23.6% | 24.1% | 52.3% |
| Phone | 0% | 50.3% | 49.7% |

The problems are **independent of each other**: the largest correlation between any two "is missing" flags is 0.04. A missing age, for example, says nothing about whether the rating or category is also missing.
This is what makes pairwise handling safe: the 1,487 customers with a valid rating are a fair sample of all customers, so comparing ratings between segments is not biased by who left the rating blank.

## 9. The data behaves like generated data

Several checks show that the file is almost certainly synthetic, which the file name (`Customers_Fakedata.csv`) also suggests:

| Check | Result |
|---|---|
| Purchase amounts vs a uniform $5–$1,000 distribution | indistinguishable (Kolmogorov-Smirnov p = 0.50) |
| Real ages vs a uniform 15–90 distribution | indistinguishable (p = 0.16) |
| Ratings 1–5 equally likely | yes (chi-square p = 0.09) |
| Gender related to first name | no (p = 0.12) |
| Date window | exactly 1,000 days |
| Phone numbers | two dummy digit sequences |

This matters for how the results should be read. Flat patterns, where no segment differs, are the **expected** result here, not a failure of the analysis. The pipeline is fully scripted, so it can be re-run unchanged on real customer data.

## Data quality scorecard (after cleaning)

| Dimension | Status |
|---|---|
| Uniqueness | Good: 0 duplicate rows, `Customer_ID` unique |
| Validity | Good: every remaining value is in range (ages 15–90, amounts $5–$1,000, ratings 1–5, real dates) |
| Completeness | **Poor:** age 24%, rating 71%, category 73%; only 9.7% of records are complete |
| Consistency | **Poor:** gender contradicts the first name in 50% of rows; names and emails are shared between IDs |
| Contactability | **None:** no real phone numbers |
