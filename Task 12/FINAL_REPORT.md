# Final Report: New York City Airbnb Analysis

## 1. Project overview

**Problem:** New York is Airbnb's most competitive US market, but public discussion runs on
anecdotes — "Manhattan prices", "entire-home takeovers" — without numbers. This project turns the
September 2019 Inside Airbnb snapshot into quantified answers: what the supply looks like, what
moves nightly prices, where demand actually lands, and what hosts, guests and the platform should do.

**Approach:** understand → clean (flag, don't silently delete) → exploratory analysis →
visualisation → interactive dashboard → insights → recommendations. Four reproducible scripts
(`clean_data.py` → `analysis.py` + `make_charts.py` → `build_dashboard.py`) rebuild every
deliverable from the raw file.

## 2. Dataset information

- **Source:** Inside Airbnb open data, `AB_NYC_2019.csv` (New York City, snapshot through July 2019
  reviews). The only dataset used — nothing added, nothing replaced.
- **Size:** 48,895 rows × 16 columns → **48,884 × 26** after cleaning.
- **Main columns:** `id`, `name`, `host_id`/`host_name`, `neighbourhood_group` (5 boroughs) /
  `neighbourhood` (221 areas), `latitude`/`longitude`, `room_type` (Entire home/apt, Private room,
  Shared room), `price` (nightly $), `minimum_nights`, `number_of_reviews`, `last_review`,
  `reviews_per_month`, `calculated_host_listings_count`, `availability_365` (open days next year).
- **Types:** ids/counts integers, coordinates floats, `last_review` parsed to datetime,
  `reviews_per_month` float.
- **Questions answered:** most common listing types (§5-Q1) · highest-activity areas (§5-Q2) ·
  price gaps between areas (§5-Q3) · price/ratings/reviews relationship (§5-Q4) · price drivers (§5-Q5) ·
  strongest performers (§5-Q6) · supply patterns (§5-Q7).

## 3. Data cleaning process

| # | Issue | Evidence | Action |
|---|---|---|---|
| 1 | Duplicates | 0 duplicate rows, 0 duplicate ids | none needed |
| 2 | Impossible prices | 11 rows with `price == 0` | removed (0.02%) |
| 3 | Missing names | 16 listings, 21 host names | filled (`Unnamed listing` / `Unknown host`) + flags |
| 4 | Missing reviews | 10,052 gaps in `last_review`/`reviews_per_month` | verified 1:1 equal to zero-review rows → `reviews_per_month = 0`, `flag_never_reviewed = 1` |
| 5 | Price outliers | 239 listings > $1,000, max $10,000 | kept + `flag_price_outlier`; value stats use price ≤ $1,000 |
| 6 | Extreme minimum stays | 43 listings demand ≥ 365 nights (max 1,250) | kept + `flag_min_nights_extreme` |
| 7 | Coordinates | all inside NYC bbox | none needed |
| 8 | Features | — | `price_band`, `avail_segment`, `host_size`, `booked_proxy`, `revenue_proxy` |

Full record: `cleaning_log.json`. Policy throughout: flag, never silently delete.

## 4. Exploratory analysis

- **Q1 — Most common listing types?** Entire homes 52.0% (25,407), private rooms 45.7% (22,319),
  shared rooms 2.4% (1,158). A two-horse market: whole apartments vs spare rooms.
- **Q2 — Highest-activity areas?** Manhattan 21,660 (44.3%) and Brooklyn 20,095 (41.1%) hold 85% of
  listings; top corridors: Williamsburg (3,919), Bedford-Stuyvesant (3,710), Harlem (2,658), Bushwick (2,462).
- **Q3 — Price gaps?** Manhattan median $149 vs Bronx $65 (2.3×); room ladder $160 / $70 / $45.
  Priciest (min. 30 listings): Tribeca $282, NoHo $250, Flatiron $223, Midtown $208;
  cheapest: Elmhurst $59 and Queens value belt ~$60.
- **Q4 — Price vs ratings/reviews?** No relationship: price–reviews r = −0.06, price–reviews/month
  r = −0.06, price–availability r = +0.12. Median price by review bucket is flat ($120 at zero
  reviews → ~$100 once reviewed). Priciest pockets average the fewest reviews — demand follows value.
- **Q5 — What moves price?** Room type first (2–3× steps), borough second (Manhattan ×1.4 of city
  median, Bronx ×0.6), micro-neighbourhood third. Reviews, availability and host size move it ~zero.
- **Q6 — Strongest performance?** Review leaders: East Elmhurst (81.7 mean reviews), Jamaica (42.9),
  Flushing (34.8) — Queens value areas, not luxury cores. Highest median revenue proxy: Manhattan
  ($33,945) on rate; Brooklyn ($23,542) on rate × occupancy balance.
- **Q7 — Supply patterns?** Barbelled availability: 35.9% blocked all year vs ~30% open 6+ months.
  Minimum stays split short-stay (1–3 nights, 67%) and monthly (30-night spike, 3,758). Host base is
  fragmented (86% single-listing) with a professional head (Sonder 327, Blueground 232).

## 5. Important visualizations (`charts/`)

- `01_listings_by_borough` — Manhattan/Brooklyn dominance. · `02_room_type_mix` — entire vs private.
- `03_median_price_by_borough` — the $149→$65 ladder. · `04_price_distribution` — right-skew, $50–200 mass.
- `05_price_by_room_type_box` — 2.3× entire/private gap. · `06_top_neighbourhoods_volume` — Brooklyn corridors.
- `07_priciest_neighbourhoods` — lower-Manhattan business core. · `08_price_vs_reviews` — the flat cloud (r = −0.06).
- `09_availability_segments` — the barbell. · `10_minimum_nights` — 1-2-3 + 30-night spike.
- `11_map_sample` — Manhattan core + western Brooklyn. · `12_borough_roomtype_mix` — Manhattan sells homes, Bronx/Queens sell rooms.

## 6. Dashboard (`Airbnb_NYC_Dashboard.html`)

Self-contained Plotly dashboard (plotly.js embedded; map tiles need internet): **8 KPI cards**,
**7 charts** — borough metric-switcher, stacked room mix, price histogram, room-type boxes,
6,000-point listing map, price-vs-reviews scatter, availability bar — plus a **Top-25 neighbourhood
table with borough filter and click-to-sort**. Slicers: chart legends, switcher buttons, table filter.

The same story ships in Excel too. **`Airbnb_Dashboard.xlsx`** (candy design with clouds):
7 live KPI cards, 7 pivot charts, 5 slicers (borough, room type, price band, availability, host size)
on one shared pivot cache, plus KPIs/Analysis/Pivot Tables/Data/Cleaning Log/Data Dictionary sheets.
And in Power BI: **`Airbnb_NYC_Dashboard.pbix`** (built from `PowerBI/` via `build_powerbi.py`):
5 pages (Overview, Prices, Demand, Supply, Insights), 15 DAX measures including a Pearson
price–reviews correlation and a Top Neighbourhood measure, synced slicers and the same candy theme.
Price averages exclude $1,000+ outliers, matching this report.

## 7. Key findings

1. 85% of supply sits in two boroughs — city-wide averages are Manhattan–Brooklyn averages.
2. Price follows a clean ladder (room type × borough); ratings and reviews carry no pricing power.
3. Reviews concentrate in value corridors (Queens, Bedford-Stuyvesant), not in luxury cores.
4. 36% zero-availability + 21% never-reviewed: over a third of "supply" is not bookable or not proven.
5. Fragmented hosts (86% single-listing) face two professional firms at the top.

## 8. Business insights

- The Manhattan premium ($149 vs $65 Bronx) is a *mix* effect (61% entire homes) plus location —
  copying Manhattan rates without an entire home misprices the listing.
- Zero-review listings price *highest* ($120 median): new hosts overprice, then converge near $100 —
  the platform could suggest entry pricing instead of letting hosts learn by vacancy.
- High-availability listings (181+ days) and low-availability ones price alike (r = 0.12):
  neither hotels-style yield management nor scarcity pricing is practised — an open pricing gap.
- Queens/outer-Brooklyn value areas deliver reviews per dollar far above Tribeca/NoHo — the
  marketing budget buys more occupancy there.

## 9. Recommendations

1. **Price by ladder:** room-type base ($160/$70/$45) × borough factor (Manhattan 1.4 … Bronx 0.6).
2. **Audit the 36% blocked tail:** re-engage or purge before any supply decision.
3. **Acquire and promote in value corridors** (East Elmhurst, Jamaica, Flushing, Bed-Stuy).
4. **Coach entry pricing near $100**, not $120+, for zero-review hosts.
5. **Split operations by minimum stay** (turnover vs monthly playbooks).
6. **Counter professional hosts on reliability signals** (instant book, response time, review velocity).
7. **Carry the quality flags** into every downstream model.

## 10. Conclusion

NYC Airbnb 2019 is a two-borough, two-product market with a transparent price ladder, demand that
rewards value over luxury, and a supply count inflated by dead listings. The analysis, dashboard and
recommendations above are all rebuilt from the raw file by four scripts — and every figure traces
back to `analysis_summary.json`. Skills applied: data-quality auditing, type-safe cleaning with
flags, feature engineering, grouped EDA, correlation analysis, chart selection for the question
(not decoration), interactive dashboard design, and insight writing that ties each number to a decision.
