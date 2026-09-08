# Key Insights — Task 2 (FactSale Sales Data)

Period covered: **January 2013 – May 2016** (41 months; 2016 has only 5 months of data — don't compare it directly to a full year). 26,397 line items across 8,188 orders.

## Headline numbers

- **Total revenue:** $19.88M | **Total profit:** $9.92M | **Overall margin: 49.9%** — a genuinely healthy business, once the loss-making SKUs (below) are set aside.
- **Average order value:** $2,428, across an average of 3.2 line items per invoice.
- **8,188 orders**, 99 salespeople, 227 distinct products, only 48 identifiable (registered) customers.

## 1. Growth is real, but 2016 is decelerating

Revenue grew every full year on record: $5.26M (2013) → $5.84M (2014, +11.1%) → $6.35M (2015, +8.6%). The 5 months of 2016 on file run at **~$486K/month**, slightly below 2015's **~$529K/month** average. It's too early to call this a trend reversal off five months, but it's worth watching rather than assuming 2015's growth rate simply continues.

**Recommendation:** re-check this once June–December 2016 data is available before drawing conclusions; in the meantime, treat 2016 pace as a flag, not a verdict.

## 2. A handful of SKUs are structurally unprofitable — this is a pricing problem, not noise

566 line items (2.1% of all sales) lose money, and they are **not** randomly scattered:

- **Every single sale of the Halloween zombie mask** (492 line items, 100% of that product's sales) is sold at a loss, totaling roughly $33K in losses on $595K of revenue for that item alone.
- Its sibling product, the **Halloween skull mask, is healthy** (~16.7% margin) — so this isn't "masks don't sell," it's specifically that one SKU's price is set below its cost. That distinction matters: fixing one price fixes the problem.
- A cluster of **novelty USB flash drives** (food-shaped drives, USB missile/rocket launchers) shows the same pattern — consistently sold at a loss, unit after unit.
- Because these losses recur on the *same* SKUs every time they sell (not occasional discounting), this reads as a **pricing/costing error**, not clearance activity or noise.

**Recommendation:** re-price (or discontinue) the Halloween zombie mask and the loss-making USB novelty line. At current volumes this is a low-effort, high-confidence margin recovery — it doesn't require new sales, just fixing prices already being charged.

## 3. Packaging & Shipping Supplies is the revenue engine, but not the margin leader

| Category | Revenue share | Margin |
|---|---|---|
| Packaging & Shipping Supplies | 58.4% | 51.6% |
| Apparel & Footwear | 21.3% | 58.6% |
| Toy Vehicles | 8.4% | 41.0% |
| Costumes & Masks | 5.8% | 5.2% (dragged down entirely by the zombie mask — see #2) |
| USB & Novelty Gadgets | 3.4% | 57.0% |
| Novelty Mugs | 1.8% | 65.4% |
| Confectionery | 0.6% | 43.9% |
| Toys & Figures | 0.2% | 65.6% |

Packaging & Shipping Supplies (bubble wrap, tape, boxes, bags) drives well over half of all revenue — this looks less like a "novelty gift shop" business and more like a **packaging/fulfillment supplies wholesaler that also carries a novelty-gift side line**. Novelty Mugs and Toys & Figures are small in volume but the most profitable per dollar sold (65%+ margin) — worth a look for targeted promotion, even though they won't move the revenue needle much on their own.

## 4. A third of revenue comes with no customer record at all

34.4% of revenue ($6.77M across 2,842 orders) is tied to `Customer Key = 0` — i.e., no customer was identified at the point of sale (only 48 distinct registered customer IDs exist in the whole 3+ year file). Registered and unregistered orders have almost identical average order value ($2,452 vs $2,382), so this isn't a segment of smaller/casual buyers — it's simply **untracked**. A third of the business is effectively invisible for any kind of customer-level analysis (repeat purchase rate, lifetime value, loyalty targeting) as things stand.

**Recommendation:** if growing repeat business or loyalty programs is a goal, capturing customer identity at the point of sale for these transactions would unlock analysis that's currently impossible with this data.

## 5. Sales are broadly distributed across the sales team, not a few reps carrying the business

The top 10 salespeople (out of 99) generate 39% of revenue, and no single salesperson exceeds 10.1% of total revenue. That's healthy diversification — the business isn't overexposed to any one rep leaving. (Salespeople are identified by ID only — no name lookup table was provided with this dataset.)

## 6. Nearly all sales are single-unit ("Each") transactions

96.8% of revenue comes through the `Each` package type, versus a combined 3.2% for `Packet`, `Pair`, and `Bag`. Bulk-packaged sales are a minor share of the business as currently sold — any bulk-pricing or wholesale-tier strategy would be starting from a very small existing base.

## Summary of recommendations

1. **Re-price or discontinue the Halloween zombie mask and the loss-making USB novelty SKUs** — the single most actionable, lowest-effort finding in this data.
2. **Watch 2016's pace** against a full prior year before assuming growth continues at 2015's rate.
3. **Capture customer identity at checkout** where possible — a third of revenue is currently unattributable to any customer.
4. **Consider promoting Novelty Mugs and Toys & Figures** — small categories, but the highest margins in the catalog.
