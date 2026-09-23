# Key Insights: Hospital Performance 2023

Based on 247 cleaned admissions (1 Jan – 28 Dec 2023), 7 doctors and 10 diagnoses. All figures come from `analysis.py` (full printout in `analysis_output.txt`).
The statistical tests check whether a difference is real or could be chance (p < 0.05 means the difference is real).

## 1. KPI scorecard

| Area | KPI | Value | What it tells management |
|---|---|---:|---|
| Volume | Total admissions | **247** | About 20 per month, 35 per doctor |
| Volume | Average / peak daily census | **4.2 / 13** patients | Beds needed on a normal night vs the busiest night (16 May) |
| Efficiency | Average length of stay (ALOS) | **6.3 days** (median 4) | The gap between mean and median shows a long tail of very long stays |
| Efficiency | Total bed-days | **1,547** | Total bed capacity used |
| Efficiency | Long-stay rate (over 7 days) | **25.5%** | One patient in four stays more than a week |
| Efficiency | Bed-days used by 15+ day stays | **34.7%** | 11% of patients use a third of the beds |
| Acuity | High-severity share | **36.0%** | Case-mix intensity (but see finding 3) |
| Acuity | Senior share (60+) | **36.0%** | Ageing patient base |
| Finance | Uninsured rate | **29.1%** | Revenue exposed to non-payment |
| Finance | Billing completeness | **21.1%** | Only 52 admissions have a genuine bill |
| Finance | Average genuine bill / median per bed-day | **2,945 / 785** | Indicative only: based on short stays |
| Data quality | Date-correction rate | **11.7%** | Admission and discharge dates were reversed in 29 records |
| Data quality | Records flagged for clinical review | **9.7%** | 24 records need a chart or coding check |

## 2. Main findings

### Finding 1: A small group of very long stays uses a third of the hospital's capacity
- 28 admissions (11%) lasted **15 days or more** and used **537 bed-days, 35% of the total**.
- Stays of 1–3 days are 46% of admissions but only 16% of bed-days.
- **17 of the 28 are minor conditions** (common cold, influenza, chronic allergy, migraine). A 24-day stay for a cold is not clinically normal.
  Either discharge is being delayed (social, administrative or bed-blocking reasons) or the diagnosis is coded wrongly.
- Cutting those 17 stays to the 4-day median would free about **250 bed-days (16% of the year)**.

### Finding 2: Age is the only factor that really lengthens stays
- ALOS rises steadily with age: **Child 4.7 → Adult 5.6 → Middle age 6.8 → Senior 7.1 days** (Spearman rho = 0.16, p = 0.01).
- Seniors (60+) are **36% of admissions but 41% of bed-days**.
- Diagnosis, insurance and gender show no real difference in stay length (p = 0.98, 0.92 and 0.12).

### Finding 3: Recorded severity does not match how sick patients are
- High-severity patients stay **6.3 days**, low-severity **5.9**, and medium **6.6**. No real difference (p = 0.91).
- The severity mix within diagnoses is inconsistent: **stroke is 45% "Low"**, while **common cold is 48% "High"** and pneumonia is 75% "High".
  Diagnosis and severity are only weakly related (chi-square p = 0.03).
- A common cold has the **longest ALOS (7.7 days)**, longer than stroke (7.5) and pneumonia (4.8).
- **Meaning:** the severity field cannot currently be used for triage, staffing or case-mix funding decisions. The coding needs an audit.

### Finding 4: Billing data is too incomplete for revenue reporting
- **79% of bills are placeholder values** (999 or 3852) instead of real charges.
- The 52 genuine bills follow stay length closely (rho = 0.59, about **+521 per extra day**), which confirms that the placeholders are not real.
- **None of the 28 longest stays has a genuine bill.** The costliest care is exactly the care that is not being billed, so revenue is
  probably badly understated.
- Uninsured patients are 29% of admissions and have average stays similar to insured patients (6.4 vs 6.1–6.3 days). They are highest in migraine (40%), pneumonia (38%)
  and kidney failure (37%), and in December (46% of that month's admissions).

### Finding 5: Demand follows a seasonal and weekly pattern
- **May** is the busiest month (32 admissions, 235 bed-days, peak census **13** on 16 May). **October** is second (28 admissions, peak 9).
  **August** is the quietest month (10).
- Admissions cluster on **Tuesday–Wednesday (95, 38%)** and are lowest on **Friday (20)**, the regional weekend. Friday admissions stay longest
  (9.0 days on average), which suggests fewer discharges happen over the weekend.
- Average occupancy is only 4.2 beds, so capacity needs to be **flexible for the peaks** rather than fixed high.

### Finding 6: Stay lengths differ between doctors (not yet conclusive)
| Doctor | Admissions | % of admissions | % of bed-days | ALOS | Long-stay rate |
|---|---:|---:|---:|---:|---:|
| Dr. Reem Abdullah | 42 | 17% | 20% | 7.5 | 36% |
| Dr. Mohamed Hassan | 41 | 17% | 19% | 7.2 | 34% |
| Dr. Yasmin Mahmoud | 39 | 16% | 17% | 6.9 | 26% |
| Dr. Khaled Sami | 34 | 14% | 13% | 5.8 | 21% |
| Dr. Nour Khaled | 27 | 11% | 10% | 5.6 | 19% |
| Dr. Ahmed Ali | 40 | 16% | 13% | 5.2 | 20% |
| Dr. Sara Ibrahim | 24 | 10% | 7% | 4.7 | 17% |

- Dr. Reem Abdullah and Dr. Mohamed Hassan treat 34% of patients but use 39% of bed-days. Dr. Mohamed Hassan also has the most flagged records (9).
- Case mix explains this only partly. Dr. Reem Abdullah's patients are more often high-severity (45% against 36% for the hospital), but
  Dr. Mohamed Hassan's are not (32%), and severity does not predict stay length anyway (finding 3). The difference in stay length is
  **not statistically significant (p = 0.30)** with this sample size, so it is a reason to review case notes, not to judge performance.
- Workload is uneven: Dr. Reem Abdullah has 42 admissions, while Dr. Sara Ibrahim has 24.

## 3. Relationships between variables

| Relationship | Result | Real? |
|---|---|---|
| Age → length of stay | Rises with age (rho 0.16) | **Yes** (p = 0.01) |
| Genuine bill → length of stay | Strong positive (rho 0.59) | **Yes** (p < 0.001) |
| Diagnosis → severity | Weak link | Yes, but weak (p = 0.03) |
| Severity → length of stay | Flat | No (p = 0.91) |
| Diagnosis → length of stay | Flat | No (p = 0.98) |
| Doctor → length of stay | 4.7–7.5 days | Not proven (p = 0.30) |
| Insurance → severity or age | No link | No (p = 0.88 / 0.29) |

## 4. Problems that need attention

1. **Billing capture is broken:** 79% placeholders, and no bills at all for long stays.
2. **Long stays for minor conditions:** 17 cases, 320 bed-days.
3. **Severity coding is unreliable:** it does not reflect resource use.
4. **Admission system data entry:** 12% of records had reversed dates, there is no patient ID (so readmissions cannot be tracked), and gender conflicts with the name in 53% of rows.

## 5. Recommendations (decision support)

| Priority | Action | Owner | Measure it with |
|---|---|---|---|
| 1 | Make a real bill mandatory at discharge and block default values (999/3852) | Finance + IT | Billing completeness: 21% → 100% |
| 2 | Weekly review of every patient past day 7, starting with minor-condition cases | Medical director | Long-stay rate: 25.5% → under 15%; ALOS |
| 3 | Audit severity coding against clear triage criteria (sample of stroke and pneumonia records) | Quality team | High-severity ALOS should exceed low-severity ALOS |
| 4 | Flexible capacity and staff rosters for May/October peaks and Tuesday–Wednesday intake; geriatric discharge support | Operations | Peak census vs staffed beds; senior ALOS |
| 5 | Add a unique patient ID and date validation to the admission form | IT | Date-correction rate: 11.7% → 0%; readmission rate becomes measurable |
| 6 | Peer review of case notes for the two doctors with the longest stays | Clinical governance | Doctor ALOS spread |

## 6. Limitations

- A single year and 247 admissions: small numbers per doctor, diagnosis or month, so most gaps are not statistically significant.
- Finance figures cover 21% of admissions, mostly short stays, so they understate the average charge.
- Gender is unreliable (see DATA_QUALITY_REPORT.md), and there are no bed-capacity figures, so occupancy % cannot be calculated. Census counts are used instead.
