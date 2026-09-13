# Task 3 — HR Employee Attrition: Key Insights

Dataset: IBM HR Analytics Employee Attrition (1,470 employees, 35 original columns). No missing values, no duplicates, no impossible values — see `DATA_QUALITY_REPORT.md`.

## Headline numbers
- **Overall attrition rate: 16.1%** (237 of 1,470 employees left).
- Average monthly income: **$6,503**. Average tenure: **7.0 years**. Average job satisfaction: **2.73 / 4**.
- **28.3% of employees work overtime**, and they leave at nearly **3x** the rate of those who don't.

## 1. Departments & job roles
- **Sales has the highest departmental attrition (21.0%)**, ahead of Human Resources (19.0%) and Research & Development (14.0%) — despite R&D holding 65% of headcount.
- By job role, attrition is heavily concentrated at the entry/front-line level: **Sales Representative (40.0%)** and **Laboratory Technician (24.0%)** are the two highest-risk roles. Senior roles are essentially stable: Manager (5.0%) and Research Director (2.0%).
- This is not just a pay story — Sales Executives earn more than Lab Technicians but still churn at 17%, so role content/pressure matters as much as salary.

## 2. Salary, experience & performance
- Income scales cleanly with job level: **$2,787 (Level 1) → $19,192 (Level 5)**, and monthly income correlates strongly with total working years (**r = 0.77**) — the pay structure is internally consistent, not random.
- Performance ratings are compressed: **84.6% of employees are rated 3 ("Excellent")** and the rest rated 4 ("Outstanding") — nobody is rated below 3, which limits how useful `PerformanceRating` is for distinguishing employees, and salary-hike differences between the two groups are modest (14.0% vs 21.8% avg hike).
- **Employees who left earned $4,787/month on average vs. $6,833 for those who stayed** — a ~30% gap, though this is partly explained by leavers skewing younger/more junior.

## 3. Satisfaction
- Average satisfaction scores are middling across the board (Job 2.73, Environment 2.72, Relationship 2.71, Work-Life Balance 2.76, all on a 1–4 scale) — there's no single satisfaction dimension that stands out as a company-wide strength or crisis.
- Every satisfaction dimension is measurably lower among employees who left: Job Satisfaction **2.47 vs 2.78**, Environment Satisfaction **2.46 vs 2.77**, Work-Life Balance **2.66 vs 2.78**. The gap is consistent, not driven by one factor.

## 4. Attrition drivers (the actionable part)
Ranked by how sharply attrition rate moves:

| Factor | Highest-risk group | Attrition rate |
|---|---|---|
| **OverTime** | Works overtime | **30.5%** vs 10.4% (no overtime) |
| **Tenure** | 0–2 years at company | **29.8%** vs 6.7% (11–20 yrs) |
| **Age** | 18–25 years old | **35.8%** vs 9.2% (36–45) |
| **Marital status** | Single | **25.5%** vs 10.1% (divorced) |
| **Business travel** | Travels frequently | **24.9%** vs 8.0% (non-travel) |
| **Work-life balance** | Rated "Bad" (1/4) | **31.2%** vs 14.2% (rated 3/4) |
| **Job satisfaction** | Rated "Low" (1/4) | **22.8%** vs 11.3% (rated "Very High") |

**OverTime and early tenure are the two strongest single signals in the whole dataset.** A new hire (0–2 years) who also works overtime is the profile HR should watch most closely; a Sales Representative under 26 who travels frequently and has low job satisfaction is close to worst-case on every axis at once.

## Recommendations
1. **Audit overtime load in Sales and Laboratory Technician roles first** — the two roles combine high attrition with high overtime exposure.
2. **Strengthen onboarding/retention support in the first 2 years** — nearly 30% of new hires leave, roughly 4-5x the rate of 10+ year veterans.
3. **Cap or rotate frequent business travel** where possible; it nearly triples attrition risk vs. no travel.
4. Performance ratings currently can't distinguish top performers from average ones (only 2 values used across 1,470 people) — worth revisiting the rating scale/process if it's meant to inform retention decisions.

## Deliverables in this folder
- `Cleaned_HR_Attrition.csv` — cleaned dataset + engineered columns (`AttritionFlag`, `AgeGroup`, `IncomeBand`, `TenureBand`)
- `DATA_QUALITY_REPORT.md` — cleaning/validation log
- `analysis.py` / `analysis_output.txt` / `analysis_summary.json` — full analysis
- `HR_Attrition_Dashboard.html` — interactive dashboard (open in any browser)
- `Power_BI_Guide.md` — step-by-step recipe (DAX measures + layout) to rebuild the same dashboard natively in Power BI Desktop
