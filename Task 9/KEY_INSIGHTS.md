# Key Insights: Customer Data Analysis

Based on 2,100 cleaned customers (one purchase each) from 27 Oct 2022 to 23 Jul 2025. All figures come from `analysis.py`; the full printout is in `analysis_output.txt`.
Statistical tests check whether a difference is real or could be chance: **p < 0.05 means the difference is real**.

## Summary in five sentences

1. The biggest finding is the data itself: only **9.7%** of records are complete, age is usable for **24%** of customers, **27%** of purchases have no category, and **no phone number is real**.
2. Customers spent **$1.02M** across 2,003 priced purchases (average **$510**), and **$750+ orders bring 45% of revenue** from 26% of orders.
3. Satisfaction is split down the middle: average **3.03 / 5**, with as many dissatisfied customers (**39%**) as satisfied ones (**39%**), and the same split in every segment.
4. Sales are **flat**: about 60 purchases and $29K a month for 32 months, with no trend and no seasonality once partial months and calendar coverage are handled correctly.
5. **No customer segment behaves differently**: gender, age, category, weekday and email provider show no significant difference in spend or rating. This is consistent with a randomly generated file.

## 1. KPI scorecard

| Area | KPI | Value | What it tells management |
|---|---|---:|---|
| Customers | Customers | **2,100** | Unique IDs, one purchase each (50 duplicate rows removed) |
| Customers | Gender (where recorded) | **49% F / 51% M** | 12.7% of customers have no gender |
| Customers | Median age (495 real ages) | **55** | Every age from 15 to 90 is represented |
| Revenue | Recorded revenue | **$1,021,324** | 97 purchases have no amount (about $49K unrecorded) |
| Revenue | Average / median order value | **$510 / $519** | Orders are spread evenly from $5 to $1,000 |
| Revenue | Revenue from $750+ orders | **44.9%** | From 26.2% of orders |
| Trend | Purchases / revenue per full month | **59.9 / $29,261** | 32 complete months (Nov 2022 – Jun 2025) |
| Trend | January–June revenue, 2023 → 2024 → 2025 | **$170.7K → $173.0K → $168.5K** | +1.3%, then −2.6%: flat |
| Products | Top category by revenue | **Clothing, $163,865** | 21.7% of categorised revenue; the lead is within chance |
| Products | Revenue with no category | **26.2% ($267,729)** | The biggest "category" is unknown |
| Satisfaction | Average rating (1,487 valid) | **3.03 / 5** | Middle of the scale |
| Satisfaction | Satisfied (4–5★) / dissatisfied (1–2★) | **39.3% / 38.7%** | Net satisfaction +0.6 points |
| Data quality | Complete records | **9.7%** | 204 of 2,100 valid in all 6 fields |
| Data quality | Usable age / rating / category | **23.6% / 70.8% / 73.1%** | Age cannot support targeting yet |

## 2. Main findings

### Finding 1: Data quality is the biggest finding
- Only **204 of 2,100 records (9.7%)** have a valid age, gender, amount, date, category and rating.
- **Age:** 1,099 values are the placeholders `-1` or `200`, and 506 are blank. Only 495 real ages (23.6%) remain.
- **Rating:** 291 ratings are `10` on a 1–5 scale, and 322 are blank. 1,487 (70.8%) are valid.
- **Category:** 565 purchases (26.9%) have none. **Phone:** only two dummy numbers, so 0% of customers can be reached by phone.
- **Gender** was written 6 different ways, and it contradicts the first name in 50% of rows.
- The problems are independent of each other (maximum correlation 0.04). Dropping incomplete rows would lose 90% of the data, so each metric uses all the rows valid for it.

### Finding 2: Big tickets carry the revenue
| Order size | % of orders | % of revenue | Average order |
|---|---:|---:|---:|
| Under $250 | 23.7% | 5.8% | $125 |
| $250–499 | 24.6% | 18.0% | $373 |
| $500–749 | 25.6% | 31.3% | $623 |
| **$750+** | **26.2%** | **44.9%** | **$876** |

- Orders are spread almost perfectly evenly from $5 to $1,000, so there is no "typical basket" (median $519, mean $510).
- One order in four is $750+, and those orders bring **45% of revenue**. Losing a big-ticket customer costs as much as losing seven small ones.

### Finding 3: As many unhappy customers as happy ones
- Ratings are spread almost evenly over the five stars: 1★ 17.9%, 2★ 20.8%, 3★ 21.9%, 4★ 18.7%, 5★ 20.6%. The average is **3.03 / 5**.
- **38.7% of raters are dissatisfied (1–2★)**, as many as are satisfied (39.3%).
- The split is the same everywhere. By category, average ratings range only from 2.96 (Books) to 3.11 (Electronics) (p = 0.84); by age group, from 3.05 to 3.13 (p = 0.99); by gender, 3.00 vs 3.04 (p = 0.59).
- Rating does not depend on how much the customer spent (Spearman rho = −0.03, p = 0.30).
- **Meaning:** dissatisfaction is not caused by any product, price level or customer group in this data. The driver must be something that is not recorded, such as delivery, service or product quality.

### Finding 4: Sales are flat
- About **60 purchases and $29,261 a month** over the 32 complete months. The best month was Dec 2023 ($40.0K) and the weakest Jan 2024 ($19.6K), but these swing around a flat line.
- The trend slope is +0.12 purchases per month, which is not significant (p = 0.48). Revenue gives the same result (p = 0.57).
- Like-for-like, January–June revenue was **$170.7K (2023) → $173.0K (2024) → $168.5K (2025)**: +1.3%, then −2.6%. Purchase counts show no significant change (353 / 366 / 347, p = 0.77).
- **Meaning:** the business is stable but not growing. Growth will need a deliberate action, because it is not happening on its own.

### Finding 5: No seasonality, but two traps that look like patterns
- **Trap 1: the August–September "slump".** In raw totals, August and September have 34% fewer purchases than the other months (116 vs 175 on average).
  The cause is calendar coverage: the data runs from 27 Oct 2022 to 23 Jul 2025, so August and September occur in only 2 of the years covered, while January–June occur in 3.
  Per 30 days of data, every month sits between 53 and 64 purchases, and the months do not differ (p = 0.82).
- **Trap 2: the 2025-Q3 "collapse".** 2025-Q3 has 55 purchases against about 180 in other quarters, but it contains only 23 days of data. Per 30 days it is in line with the others.
- **Weekdays** are also flat: 271–303 purchases per weekday (p = 0.82). Saturday has the highest order value ($550), but the weekday differences are not significant (p = 0.09).

### Finding 6: No customer segment stands out
| Segment | Customers | Recorded revenue | AOV | Avg rating | Satisfied | Dissatisfied |
|---|---:|---:|---:|---:|---:|---:|
| Clothing | 323 | $163,865 | $537 | 3.06 | 39% | 34% |
| Electronics | 323 | $154,692 | $501 | 3.11 | 41% | 38% |
| Books | 305 | $150,083 | $510 | 2.96 | 38% | 41% |
| Home | 296 | $143,571 | $500 | 3.04 | 39% | 39% |
| Toys | 288 | $141,384 | $526 | 3.01 | 37% | 39% |
| *Unknown category* | *565* | *$267,729* | *$497* | *3.01* | *41%* | *40%* |
| Female | 891 | $440,940 | $522 | 3.00 | 38% | 41% |
| Male | 942 | $448,129 | $499 | 3.04 | 39% | 38% |

- **Categories:** each of the five categories brings 14–16% of revenue. Clothing leads, but order values do not differ between categories (p = 0.45).
- **Gender:** women spend $23 more per order ($522 vs $499), but the difference is not significant (p = 0.095). Men and women also buy the same category mix (p = 0.25).
- **Age:** order value does not rise or fall with age (rho = 0.02, p = 0.70). Customers aged 75–90 have the highest AOV ($548) and 30–44 the lowest ($501), a gap chance explains.
- **Email provider** (gmail / hotmail / yahoo): no difference in spend (p = 0.26) or rating (p = 0.60).
- **Meaning:** on this data, demographic targeting has nothing to target. Campaigns should be tested with experiments (A/B tests) rather than aimed at a segment that looks different.

### Finding 7: The file behaves like randomly generated data
Amounts are uniform between $5 and $1,000 (KS test p = 0.50), real ages are uniform between 15 and 90 (p = 0.16), all five star levels are equally likely (p = 0.09), gender is unrelated to the first name (p = 0.12),
the dates cover exactly 1,000 days, and the phone numbers are two digit sequences. With data like this, "no difference" is the correct and expected answer. The analysis is fully scripted, so every chart and test can be re-run on real data.

## 3. Relationships between variables

| Relationship | Result | Real? |
|---|---|---|
| Gender → order value | $522 vs $499 | No (p = 0.095) |
| Age → order value | rho = 0.02 | No (p = 0.70) |
| Category → order value | $500–537 | No (p = 0.45) |
| Weekday → order value | $487–550 | No (p = 0.09) |
| Email provider → order value | $495–520 | No (p = 0.26) |
| Gender → rating | 3.00 vs 3.04 | No (p = 0.59) |
| Age → rating | rho = 0.00 | No (p = 0.95) |
| Category → rating | 2.96–3.11 | No (p = 0.84) |
| Order value → rating | rho = −0.03 | No (p = 0.30) |
| Gender → category mix | same mix | No (p = 0.25) |
| Age group → category mix | same mix | No (p = 0.52) |
| Month → purchases (trend over time) | +0.12 / month | No (p = 0.48) |
| Calendar month → purchases (per 30 days) | 53–64 | No (p = 0.82) |
| Weekday → purchases | 271–303 | No (p = 0.82) |

Out of 35 segment confidence intervals, 2 miss the overall average (Saturday's order value and the $250–499 band's rating). Chance alone would produce about 1.8 such misses, and the group tests for both dimensions are not significant.

## 4. Recommendations

| Priority | Action | Owner | Measure it with |
|---|---|---|---|
| 1 | **Fix data capture at the source:** date of birth instead of free-text age, drop-downs for gender / category / rating (1–5 only), a date picker, phone validation, and no duplicate IDs on import | IT + CRM | Complete-record rate: 9.7% → 90%+ |
| 2 | **Give every purchase a category:** back-fill the 565 uncategorised purchases ($268K) from the order or product system | Data / Sales ops | Revenue with no category: 26% → 0% |
| 3 | **Find out why 2 in 5 customers are dissatisfied:** add a reason code and comment to each rating, link ratings to delivery and returns data, and follow up every 1–2★ rating within 48 hours | Customer service | Average rating 3.03 → 3.5; dissatisfied share 39% → below 25% |
| 4 | **Protect and grow big orders:** priority service for $750+ orders (45% of revenue); A/B-test bundles or upgrades on $250–749 orders | Sales / Marketing | Share of $750+ orders; average order value |
| 5 | **Start measuring loyalty:** one persistent customer ID across orders, so repeat rate and lifetime value become measurable. Track monthly purchases against the ~60 / month baseline | CRM | Repeat-purchase rate; purchases per month |

## 5. Limitations

- Each customer has one purchase, so there is no repeat, retention or lifetime-value analysis.
- Age results rest on 495 customers (24%), and gender is unreliable (it contradicts the first name in 50% of rows).
- Revenue is *recorded* revenue: 97 purchases (about $49K) have no amount, and 26% of revenue has no category.
- The file behaves like synthetic data (finding 7), so the "no difference" results describe this file, not a real customer base.
