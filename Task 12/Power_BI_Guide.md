# Power BI Guide: NYC Airbnb Dashboard

## Open it (2 minutes)

1. Open Power BI Desktop (any 2024+ version) and then **File > Open > `PowerBI/Airbnb_NYC_Dashboard.pbip`**.
2. Press **Refresh** (Home ribbon). The project stores no data — it loads
   `Cleaned_AB_NYC_2019.csv` (48,884 rows) through the Power Query in the semantic model.
3. **File > Save as > `Airbnb_NYC_Dashboard.pbix`** so the data is stored with the report.

> The CSV path is written into Power Query as an absolute path. If you move the folder,
> rerun `python "Task 12/build_powerbi.py"` from the repo root and open the fresh `.pbip`.

## Pages (5)

| Page | Contents |
|---|---|
| **Overview** | 8 KPI cards, listings by borough, room-type donut, price bands, borough scorecard, top-10 neighbourhoods |
| **Prices** | 6 cards incl. the price–reviews correlation, median by borough and room type, priciest areas, price-vs-traction scatter |
| **Demand** | Review leaders, averages by borough, top-15 demand table |
| **Supply** | Availability barbell, minimum-stay habits, host sizes, top-10 hosts, price by host size |
| **Insights** | Findings, recommendations and data notes as text |

Every page carries the same 5 synced slicers: **Borough, Room type, Price band, Availability, Host size**.
Band fields (borough, room, price band, availability, stay, host size) have hidden `*Sort`
columns built in Power Query, so charts always sort logically — never alphabetically.

## Measures (15, all in the `Listings` table)

Listings, Hosts, Median/Avg Price (capped $1,000), Entire %, Zero Avail %, Never Reviewed %,
Total/Avg Reviews, Avg Availability, Manhattan %, Luxury %, Monthly Stays, Top Neighbourhood,
r Price-Reviews (Pearson DAX).

## Design

Candy theme (`CandyTheme.json`): pastel blue `#7FB6D9`, pink `#F4A7C3`, green `#9BDBA6`,
light yellow `#FFE08A`, lavender `#C3B2E8`, peach `#FFC9A3` on ink `#33475B` —
same palette as the Excel dashboard.

## Checks before submitting

- Each card on Overview matches `analysis_summary.json` with no slicer selection
  (48,884 listings · $105 median · 52.0% entire · 35.9% zero-avail · 1,137,628 reviews).
- Selecting **Manhattan** in the Borough slicer shows 21,660 listings and ~$185 average.
