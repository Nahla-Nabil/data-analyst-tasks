# Key insights: New York City Airbnb

All figures from `Cleaned_AB_NYC_2019.csv` (48,884 listings, September 2019 snapshot).
Money statistics exclude the 239 listings priced over $1,000; shares and counts use all rows.
Every number is reproducible via `analysis.py` → `analysis_summary.json`.

## KPI scorecard

| KPI | Value |
|---|---|
| Listings / hosts / neighbourhoods | **48,884** / **37,455** / **221** |
| Median / mean nightly price | **$105** / $141 |
| Entire home / private room / shared room | **52.0%** ($160) / 45.7% ($70) / 2.4% ($45) |
| Manhattan / Brooklyn share of listings | **44.3%** / 41.1% |
| Borough medians (M / Bk / Q / SI / Bx) | **$149** / $90 / $75 / $75 / **$65** |
| Zero availability / never reviewed | **35.9%** / **20.6%** |
| Total reviews / mean per listing | **1,137,628** / 23.3 |
| Price–reviews correlation | **r = −0.06 (none)** |

## Findings

1. **Two boroughs are the market.** Manhattan (21,660) + Brooklyn (20,095) hold 85% of listings;
   Queens adds 12%, the Bronx and Staten Island together barely 3%. Any city-wide statement is
   really a Manhattan–Brooklyn statement.
2. **A steep, clean price ladder.** Manhattan ($149) costs 2.3× the Bronx ($65); entire homes
   ($160) cost 2.3× private rooms ($70) and 3.6× shared rooms ($45). Room type explains price
   far better than ratings do. Manhattan is 61% entire homes; the Bronx and Queens are
   majority private rooms — product mix, not just location, drives the borough gap.
3. **Price does not buy reviews (r = −0.06).** Median price barely moves across review buckets
   ($120 with zero reviews → $99–$105 once reviewed). The priciest pockets — Tribeca ($282),
   NoHo ($250), Flatiron ($223) — average the *fewest* reviews (~11–18); the review leaders are
   value areas: East Elmhurst (81.7), Jamaica (42.9), Flushing (34.8). Demand follows value, not luxury.
4. **A third of supply looks dead.** 35.9% of listings show zero open days in the next year and
   20.6% were never reviewed (1.14M reviews sit on the other 79%). Zero-availability listings still
   average ~23 reviews, so many are paused/delinquent rather than new — counting them as bookable
   supply overstates the market by more than a third.
5. **Small hosts dominate, professionals lurk at the top.** 86% of hosts hold exactly one listing
   (66% of all listings); only 4.5% of listings sit with 21+ listing operators. But the two largest
   "hosts" are firms — Sonder (327 listings) and Blueground (232) — competing on consistency and
   instant booking, not on price.
6. **Minimum stays reveal two businesses.** 1–3 nights dominate (67%), then a sharp spike at
   30 nights (3,758 listings): short-stay tourism plus monthly-rental arbitrage in one file.
   43 listings demand ≥ 365 nights — Miscategorised long-term rentals, flagged, not deleted.
7. **Volume and value live in different neighbourhoods.** The biggest inventories are Brooklyn
   value corridors — Williamsburg (3,919), Bedford-Stuyvesant (3,710), Bushwick (2,462, median $65) —
   while the price peaks are lower-Manhattan business districts (Tribeca, Midtown $208, Financial
   District $200). Chasing listing count and chasing nightly rate point at opposite ends of the map.

## Recommendations

- **Price by ladder, not by gut:** anchor new listings on room type ($160 / $70 / $45) then adjust
  ± borough (Manhattan ×1.4, Bronx ×0.6) — the two variables that actually move price.
- **Audit the 36% zero-availability tail** before any supply-side decision: re-engage paused hosts
  or purge delisted units; reported "supply" is overstated by more than a third until then.
- **Market value corridors, not luxury cores, for occupancy:** East Elmhurst, Jamaica, Flushing and
  Bedford-Stuyvesant convert browsing into reviews far better than Tribeca/NoHo — steer promotions
  and new-host acquisition there.
- **Compete with Sonder/Blueground on reliability, not rate:** professional operators win on
  consistency — individual hosts should counter with instant book, sub-24h response, and review
  velocity, the metrics guests can see.
- **Split strategy by minimum stay:** 1–3 night listings need turnover operations (cleaning, dynamic
  weekend pricing); 30-night listings need monthly discounts and tenant screening — one playbook
  serves neither.
- **Keep the flags downstream:** `flag_price_outlier`, `flag_never_reviewed` and
  `flag_min_nights_extreme` make every KPI auditable — carry them into any pricing or demand model
  instead of silently dropping the rows.
