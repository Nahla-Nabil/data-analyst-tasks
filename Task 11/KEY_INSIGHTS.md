# Key insights: Video Game Industry

These figures cover all 16,717 titles that remain after cleaning (1980–2020, 31 platforms).
Each number can be traced to the **KPIs** and **Analysis** sheets of `GameSales_Dashboard.xlsx`.

## KPI scorecard

| KPI | Value |
|---|---|
| Titles / global sales | 16,717 / **8,920.3M** (0.534M per title, median 0.17M) |
| Top genre / platform / publisher | **Action** (1,745.3M) / **PS2** (1,255.6M) / **Nintendo** (1,788.8M, 20.1%) |
| Best-selling title | **Wii Sports** (82.53M) |
| Regional mix | NA **49.4%** / Europe 27.2% / Japan 14.6% / Rest 8.9% |
| Critic scores | Average 69.0 (n = 8,136); **52.1%** of rows have any review |
| Peak year / peak decade | **2008** (680.8M) / 2000s (4,652.7M, 52.5%) |

## Findings

1. **Scale and a long tail.** 16,717 titles sold 8,920.3M copies, but the median title sells only 0.17M and 34.6% never
   reach 0.1M. The top 1% of titles take **22%** of all sales; the top 100 alone take 20.5%.
2. **Concentration everywhere.** Nintendo alone (20.1%) outsells the next publisher (EA, 1,115.7M). The top 10 publishers
   hold **70.2%**. Action (19.6%) and PS2 (14.1%) lead their groups, while the platform families are almost tied:
   PlayStation 40.2% vs Nintendo 39.2%, Xbox 15.6%.
3. **Regions are moving.** North America fell from 63% (1980s) to 44% (2010s); Japan fell from 27% to 12% while Europe
   grew from 8% to **33%**. Genre tastes differ too: Japan takes 29% of Role-Playing sales but only 9% of Shooter sales.
4. **Reviews track sales weakly, until the very top (Pearson 0.25, Spearman 0.39).** 90+ titles average **2.83M** vs 0.27M
   for scores under 60, and reviewed titles average 0.67M vs 0.39M unreviewed. User scores barely move at all (r = 0.09).
5. **The market peaked in 2008 (680.8M) and the 2000s are 52.5% of the file.** Wii Sports (2006, 82.53M) is the
   best-selling title on any single platform; 17 of the top 20 Nintendo titles are Nintendo-published.
6. **Current consoles (at the Dec 2016 snapshot): PS4 595.6M vs Xbox One 269.0M — roughly 2 to 1.** The PS4 is
   Europe-led (43% of its sales) while the Xbox One is North America-led (60.5%) and nearly absent in Japan (0.2%).
   On 516 shared titles the PS4 wins 72% of the comparisons.
7. **Data quality notes.** 111 release years were recovered from another platform, 158 rows carry no year and 4 rows
   are dated after the 22 Dec 2016 cutoff — all flagged on the Data sheet, never silently dropped.

## Recommendations

- **Chase the concentrated head, not the tail:** the top 1% of titles drive 22% of sales — green-light sequels and
  remasters of proven franchises (Mario, GTA, Call of Duty) over untested mid-tier bets.
- **Localise for Europe and Japan:** Europe is now a third of the market and Japan still decides Role-Playing hits —
  release timing, pricing and genre mix should differ by region.
- **Treat critic scores as a lottery ticket, not a plan:** only 90+ scores move the needle, so fund quality to the level
  that can actually reach 90+, or spend that budget on marketing instead.
- **Plan for the post-peak cycle:** the 2008 peak and the 2000s' 52.5% share show a hit-driven, cyclical market —
  smooth revenue with back-catalogue sales and services rather than launch-year bets.
- **Keep the flags:** the year/publisher/unnamed flags make every number auditable — keep them in any downstream model.
