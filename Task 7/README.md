# Task 7: Hospital Analytics (complete data analysis and interactive dashboard)

The data covers 247 hospital admissions in 2023, across 7 doctors and 10 diagnoses. The source file is in Arabic; the outputs are in English and keep the Arabic originals.
The workflow is **raw data → clean data → measures and KPIs → analysis → interactive dashboard → insights and recommendations**.

**Start here:** open `Hospital_Dashboard.html` in any browser (it works offline), then read `KEY_INSIGHTS.md`.

| File | What it is |
|---|---|
| `Hospital Analytics.xlsx` | Raw input (unchanged) |
| `Cleaned_Hospital_Data.csv` | Cleaned data: 247 rows × 34 columns, including calculated columns |
| `Hospital_Analytics_Clean.xlsx` | Excel workbook: **KPIs** (19 live-formula measures with their purpose), **Summary Tables** (10 dimensions), Severity × Diagnosis matrix, Daily Census, Clean Data table, Cleaning Log, Data Dictionary, Raw Data |
| `Hospital_Dashboard.html` | Interactive dashboard: 8 KPI cards, 15 charts and tables, 8 slicers plus click-to-filter, CSV export, light/dark mode |
| `DATA_QUALITY_REPORT.md` | Every cleaning check, the evidence for it, and the decision taken |
| `KEY_INSIGHTS.md` | KPI scorecard, 6 findings, variable relationships (with significance tests), problems, recommendations |
| `Hospital_Dashboard.twbx` | Tableau workbook: 4 dashboards, 23 sheets, 6 shared filters plus click-to-filter. See `Tableau_Guide.md` |
| `Hospital_Dashboard.pbix` | **Power BI report** (data included): 5 pages, 22 DAX measures, synced slicers. Open it in Power BI Desktop |
| `PowerBI/Hospital_Dashboard.pbip` | The same report as a generated Power BI project (the source for the .pbix). See `Power_BI_Guide.md` |
| `Power_BI_Guide.md` / `Tableau_Guide.md` | How the Power BI and Tableau versions are built, and what was checked |
| `clean_and_validate.py` → `analysis.py` → `build_workbook.py` → `build_dashboard.py` → `build_tableau.py` → `build_twb.py` → `build_powerbi.py` | The pipeline, in run order (`cleaning_log.json`, `analysis_summary.json`, `analysis_output.txt` and `Hospital.hyper` are intermediate outputs) |

## Main cleaning decisions

- 1 duplicate row removed. 29 rows had admission and discharge dates reversed; the dates were swapped and the rows flagged.
- **195 of 247 bills (79%) are placeholders** (999 and 3852). These values are the same for every diagnosis and stay length, while genuine bills rise with
  stay length (r = 0.64). They were blanked, not imputed, and finance KPIs use the 52 genuine bills only.
- Clinically unusual rows were flagged, not deleted: 17 very long stays for minor conditions and 7 unusual ages for the diagnosis.
- Gender conflicts with the patient's first name in 53% of rows, and names are not unique. A `Patient_ID` was added and gender is marked unreliable.

## Headline results

- Stays of 15+ days are **11% of admissions but 35% of bed-days**, and 17 of them are for colds, flu, allergy or migraine.
- **Recorded severity does not predict length of stay** (p = 0.91), and a common cold stays longer than a stroke, so severity coding needs an audit.
- **Age is the one real driver of stay length.** Seniors are 36% of admissions and 41% of bed-days.
- Only **21% of admissions have a genuine bill**, and none of the longest stays is billed.
- Demand peaks in May (census 13) and October, and on Tuesday–Wednesday.

## Screenshots

![KPIs and insights](screenshots/1_kpis_and_insights.png)
![Demand and capacity](screenshots/2_demand_and_capacity.png)
![Case mix and length of stay](screenshots/3_case_mix_and_length_of_stay.png)
![Doctors, insurance and billing](screenshots/4_doctors_insurance_billing.png)
![Review list and recommendations](screenshots/5_review_list_and_recommendations.png)
![Filtered example: senior patients of Dr. Reem Abdullah](screenshots/6_filtered_example_senior_dr_reem.png)
![Dark mode](screenshots/7_dark_mode.png)

### Tableau workbook (`Hospital_Dashboard.twbx`)

![Tableau overview](screenshots/tableau_1_overview.png)
![Tableau case mix](screenshots/tableau_2_case_mix.png)
![Tableau doctors and billing](screenshots/tableau_3_doctors_billing.png)
![Tableau clinical review](screenshots/tableau_4_clinical_review.png)
![Tableau shared-filter test: Dr. Sara Ibrahim](screenshots/tableau_5_filter_test_dr_sara_ibrahim.png)

### Power BI report (`Hospital_Dashboard.pbix`)

![Power BI overview](screenshots/powerbi_1_overview.png)
![Power BI case mix](screenshots/powerbi_2_case_mix.png)
![Power BI doctors and billing](screenshots/powerbi_3_doctors_billing.png)
![Power BI clinical review](screenshots/powerbi_4_clinical_review.png)
![Power BI insights](screenshots/powerbi_5_insights.png)

## Re-run

```bash
python clean_and_validate.py && python analysis.py && python build_workbook.py && python build_dashboard.py
python build_tableau.py && python build_twb.py && python build_powerbi.py
```
Requires pandas, scipy, openpyxl, plotly and tableauhyperapi. `build_workbook.py` uses LibreOffice (if installed) to calculate and cache the formula results.
