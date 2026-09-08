# Data Quality & Validation Report — Task 2 (FactSale)

**Source file:** `FactSale.csv` (26,397 rows, 21 columns, one row per invoice line item)
**Output:** `Cleaned_FactSale.csv` (26,397 rows, 26 columns)
**Scripts:** `clean_and_validate.py` (cleaning + validation), `build_dashboard.py` (dashboard)

This is the WWI-style sales fact table: one row per product sold on an invoice.
No customer / salesperson / city / product dimension (lookup) tables were
provided alongside it — only the fact file — which shapes what a few of the
findings below mean.

## 1. Issues found and how they were handled

| # | Issue | Scope | How it was handled |
|---|-------|-------|---------------------|
| 1 | `Delivery Date Key` missing | 13 rows (0.05%) | Imputed as `Invoice Date + 1 day`. This isn't a guess: **100% of the 26,384 complete rows** deliver exactly one day after invoicing, so the pattern in the rest of the data justifies the fill. A `Delivery_Date_Imputed` flag column was added so these 13 rows stay traceable rather than silently blending in. |
| 2 | Dates stored as inconsistent-length text (`10/22/2013` vs `1/1/2013`) | All rows | Parsed to real `datetime`, written back out as ISO `YYYY-MM-DD` so the file opens the same way regardless of the reader's locale. This was a formatting quirk, not corrupt data — every value parsed to a valid calendar date. |
| 3 | Numeric columns (`Unit Price`, `Tax Rate`, `Total Excluding Tax`, `Tax Amount`, `Profit`, `Total Including Tax`) quoted as text in the raw CSV | All rows | Verified/coerced to numeric dtype; asserted explicitly in the script so a future raw export that breaks this fails loudly instead of quietly corrupting KPIs. |
| 4 | `Customer Key` / `Bill To Customer Key` = 0 | 9,077 rows (34.4%) | **Not treated as an error.** These aren't invalid IDs — they represent sales with no customer record captured (walk-in / point-of-sale style transactions), and only 48 distinct non-zero customer IDs exist in the whole file, so "0" is clearly a real, deliberate placeholder, not noise. Rather than fabricate customer IDs, a `Customer_Type` column (`Registered` / `Unknown / Walk-in`) was added so this segment can be analyzed honestly instead of hidden. |
| 5 | Duplicate rows | 0 found | Checked both full-row duplication and `Sale Key` (the primary key) duplication — none. No action needed, but the check runs on every re-run of the pipeline as a safeguard. |
| 6 | Negative `Quantity` / `Unit Price` | 0 found | No invalid transaction volumes or prices. |
| 7 | Negative `Profit` | 566 rows (2.1%) | **Kept as-is — this is a real business finding, not a data error.** See Key Insights. Concentrated almost entirely in a handful of SKUs (all 492 Halloween zombie mask sales, plus a cluster of novelty USB drives), not spread randomly across the catalog — which is itself the evidence it's a pricing issue rather than data noise. |
| 8 | No product/customer/salesperson names | All rows | Only the fact table was supplied, no dimension tables. `City Key`, `Customer Key`, `Salesperson Key` and `Stock Item Key` are surrogate IDs with no lookup available, so any analysis by those fields is reported **by ID**, not by name — flagged directly on the dashboard so it isn't mistaken for a gap in the cleaning work. `Description` (free text) was the one field rich enough to derive a usable dimension from, so it was used to build an 8-bucket `Product_Category` field for category-level analysis (keyword-matched, 100% coverage — no "Other" bucket needed). |

## 2. Calculations validated

Every row was recomputed and checked against a 2-cent tolerance (to absorb float rounding, not real error):

- `Total Excluding Tax = Quantity × Unit Price` → **0 mismatches**
- `Tax Amount = Total Excluding Tax × (Tax Rate / 100)` → **0 mismatches**
- `Total Including Tax = Total Excluding Tax + Tax Amount` → **0 mismatches**

The financial arithmetic in this dataset is internally consistent across all 26,397 rows — the transactional math itself is trustworthy; the issues above are about *completeness* and *interpretation*, not broken formulas.

`Tax Rate` only ever takes two values, 15% (99.6% of rows) and 10% (0.4%) — and the 10% rows are **exactly** the 8 chocolate/confectionery SKUs, i.e. a deliberate, consistent tax rule, not a data entry error.

## 3. What was *not* changed

- Raw `Customer Key` / `Bill To Customer Key` values of 0 were left as 0 (not nulled, not fabricated) — a `Customer_Type` flag documents them instead.
- No rows were dropped for having negative profit — that's real underlying performance, not bad data.
- `Salesperson Key` / `City Key` / `Stock Item Key` were left as numeric IDs (no fabricated names).

## 4. Columns added during cleaning

| Column | Meaning |
|---|---|
| `Delivery_Date_Imputed` | `True` for the 13 rows where Delivery Date Key was filled in |
| `Customer_Type` | `Registered` vs `Unknown / Walk-in` (Customer Key = 0) |
| `Product_Category` | 8-bucket category derived from `Description` keywords |
| `Profit_Margin_Pct` | `Profit / Total Excluding Tax × 100`, per line item |
| `Is_Loss_Making` | `True` where `Profit < 0` |
