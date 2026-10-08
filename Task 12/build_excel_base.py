"""Step 4b: build the base Excel workbook with openpyxl.

Run from the repo root:  python "Task 12/build_excel_base.py"
Output: Task 12/Airbnb_Base.xlsx  (Data table, KPI formulas, analysis tables,
        cleaning log, data dictionary). The interactive layer (pivots, charts,
        slicers, dashboard) is added by build_excel_dashboard.py through Excel COM.
"""
import json
from pathlib import Path
import numpy as np
import pandas as pd
from openpyxl import Workbook
from openpyxl.formatting.rule import ColorScaleRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.table import Table, TableStyleInfo

TASK = Path(__file__).resolve().parent
OUT = TASK / "Airbnb_Base.xlsx"

# candy palette -----------------------------------------------------------------
BLUE, PINK, GREEN, YELLOW = "7FB6D9", "F4A7C3", "9BDBA6", "FFE08A"
LAV, PEACH = "C3B2E8", "FFC9A3"
INK, MUTED, BG, LINE = "33475B", "7A8FA6", "F2F7FD", "D0D7DE"
HDR_FILLS = {"Data": BLUE, "KPIs": PINK, "Analysis": GREEN,
             "Cleaning Log": YELLOW, "Data Dictionary": LAV}
FONT = "Calibri"

DROP = ["flag_name_missing", "flag_host_name_missing", "booked_proxy", "revenue_proxy"]
df = pd.read_csv(TASK / "Cleaned_AB_NYC_2019.csv", parse_dates=["last_review"],
                 ).drop(columns=[c for c in DROP if c in ["flag_name_missing", "flag_host_name_missing",
                                                          "booked_proxy", "revenue_proxy"]])
log = json.loads((TASK / "cleaning_log.json").read_text())


def _py(v):
    if v is None or v is pd.NaT:
        return None
    if isinstance(v, float) and np.isnan(v):
        return None
    if isinstance(v, (np.integer,)):
        return int(v)
    if isinstance(v, (np.floating,)):
        return None if np.isnan(v) else float(v)
    if isinstance(v, pd.Timestamp):
        return None if pd.isna(v) else v.date()
    return v


df = df.map(_py)
N = len(df)
LAST = N + 1
cols = list(df.columns)

wb = Workbook()
thin = Side(style="thin", color=LINE)
BOX = Border(left=thin, right=thin, top=thin, bottom=thin)


def hdr(ws, row, values, fill, col=1):
    for i, v in enumerate(values):
        c = ws.cell(row, col + i, v)
        c.font = Font(name=FONT, bold=True, color="33475B", size=10)
        c.fill = PatternFill("solid", fgColor=fill)
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        c.border = BOX


def title(ws, text, sub=None):
    ws["A1"] = text
    ws["A1"].font = Font(name=FONT, bold=True, size=16, color="2E6FA3")
    if sub:
        ws["A2"] = sub
        ws["A2"].font = Font(name=FONT, italic=True, size=10, color=MUTED)
    ws.sheet_view.showGridLines = False


def body(c, fmt=None, bold=False):
    c.font = Font(name=FONT, size=10, bold=bold, color=INK)
    c.border = BOX
    if fmt:
        c.number_format = fmt


# ------------------------------------------------------------- Data sheet
ws = wb.active
ws.title = "Data"
ws.append(cols)
# Guard: openpyxl turns any value starting with "=" into a formula node (<f>),
# e.g. the listing "== Modern, A/C, Easy Check-in ... ==" - Excel then refuses to
# open the file. Forcing data_type "s" stores it as plain text instead.
# (Values starting with + - @ are safe; they only get quotePrefix below.)
TRIGGER = ("=", "+", "-", "@")
TEXT_GUARD = {"name", "host_name"}
for r_idx, row in enumerate(df.itertuples(index=False, name=None), start=2):
    vals = list(row)
    ws.append(vals)
    for c_idx, col in enumerate(cols, start=1):
        if col in TEXT_GUARD:
            v = vals[c_idx - 1]
            if isinstance(v, str) and v[:1] in TRIGGER:
                cell = ws.cell(r_idx, c_idx)
                cell.quotePrefix = True
                if v[:1] == "=":
                    cell.data_type = "s"
L = {c: get_column_letter(i + 1) for i, c in enumerate(cols)}
for cell in ws[L["last_review"]][1:]:
    cell.number_format = "yyyy-mm-dd"
for c in ["price", "price_capped", "minimum_nights", "number_of_reviews",
          "calculated_host_listings_count", "availability_365", "id", "host_id"]:
    for cell in ws[L[c]][1:]:
        cell.number_format = "#,##0"
for cell in ws[L["reviews_per_month"]][1:]:
    cell.number_format = "#,##0.00"
tab = Table(displayName="tblAirbnb", ref=f"A1:{get_column_letter(len(cols))}{LAST}")
tab.tableStyleInfo = TableStyleInfo(name="TableStyleMedium9", showRowStripes=True)
ws.add_table(tab)
ws.freeze_panes = "B2"
for i, c in enumerate(cols):
    ws.column_dimensions[get_column_letter(i + 1)].width = max(11, min(24, len(c) + 3))
ws.sheet_properties.tabColor = BLUE


def R(col):
    return f"Data!${L[col]}$2:${L[col]}${LAST}"


PR, PRC = R("price"), R("price_capped")
NR, AV, ENT = R("number_of_reviews"), R("availability_365"), R("is_entire_home")
ZAV, NVR = R("is_zero_avail"), R("flag_never_reviewed")
BGH, RT, NBH = R("neighbourhood_group"), R("room_type"), R("neighbourhood")

# ------------------------------------------------------------- KPIs sheet
k = wb.create_sheet("KPIs")
k.sheet_properties.tabColor = PINK
title(k, f"Key performance indicators (all {N:,} rows)",
      "Every value is a live formula on the Data sheet. Dashboard cards show the same measures for the slicer selection.")
hdr(k, 4, ["#", "KPI", "Value", "Why it matters / logic"], PINK)
KPI_ROWS = [
    ("Listings", f"=ROWS({R('id')})", "#,##0", "Market size = denominator of every share"),
    # Hosts is a static value, not a formula: the live-formula distinct count
    # SUMPRODUCT(1/COUNTIF(...)) is O(n^2) and freezes Excel on 48,884 rows.
    ("Hosts", int(pd.read_csv(TASK / "Cleaned_AB_NYC_2019.csv", usecols=["host_id"])["host_id"].nunique()),
     "#,##0", "Static full-file value: a live distinct-count would freeze Excel; Dashboard cards stay live"),
    ("Median price ($)", f"=MEDIAN({PRC})", "#,##0", "Typical nightly rate (capped at $1,000)"),
    ("Mean price, capped ($)", f"=AVERAGE({PRC})", "#,##0.0", "Mean is pulled by luxury; capped version stays honest"),
    ("Entire-home share", f"=AVERAGE({ENT})", "0.0%", "Product mix driver of price"),
    ("Manhattan share", f'=COUNTIF({BGH},"Manhattan")/ROWS({BGH})', "0.0%", "Geographic concentration"),
    ("Brooklyn share", f'=COUNTIF({BGH},"Brooklyn")/ROWS({BGH})', "0.0%", "Second core of the market"),
    ("% zero availability", f"=AVERAGE({ZAV})", "0.0%", "Possibly dead supply"),
    ("% never reviewed", f"=AVERAGE({NVR})", "0.0%", "Unproven supply"),
    ("Total reviews", f"=SUM({NR})", "#,##0", "Demand volume"),
    ("Mean reviews / listing", f"=AVERAGE({NR})", "#,##0.0", "Typical traction"),
    ("Mean availability (days)", f"=AVERAGE({AV})", "#,##0.0", "How open the calendars are"),
    ("Median availability (days)", f"=MEDIAN({AV})", "#,##0", " robust centre (distribution is barbelled)"),
    ("Entire-home median ($)", f'=MEDIAN(IF({RT}="Entire home/apt",{PRC}))', "#,##0",
     "Array formula: price ladder step 1 (confirm with Ctrl+Shift+Enter on old Excel)"),
    ("Private-room median ($)", f'=MEDIAN(IF({RT}="Private room",{PRC}))', "#,##0", "Price ladder step 2"),
    ("Manhattan median ($)", f'=MEDIAN(IF({BGH}="Manhattan",{PRC}))', "#,##0", "Premium pole"),
    ("Bronx median ($)", f'=MEDIAN(IF({BGH}="Bronx",{PRC}))', "#,##0", "Value pole"),
]
for i, (name, f, fmt, why) in enumerate(KPI_ROWS):
    r = 5 + i
    k.cell(r, 1, i + 1)
    k.cell(r, 2, name)
    c = k.cell(r, 3)
    c.value = f  # formula string ("=...") or plain number
    for cc in (1, 2, 3):
        body(k.cell(r, cc), fmt if cc == 3 else None, bold=(cc == 2))
    k.cell(r, 3).number_format = fmt
    k.cell(r, 4, why)
    body(k.cell(r, 4))
    k.cell(r, 1).border = BOX
for w, col in [(6, "A"), (26, "B"), (18, "C"), (70, "D")]:
    k.column_dimensions[col].width = w

# ------------------------------------------------------------- Analysis sheet (values)
a = wb.create_sheet("Analysis")
a.sheet_properties.tabColor = GREEN
title(a, "Analysis tables (full file values)",
      "Static values for reference; the Dashboard pivots recalculate for every slicer selection.")
val = pd.read_csv(TASK / "Cleaned_AB_NYC_2019.csv")
valc = val[val["price"] <= 1000]
row = 4


def table(title_, frame, fills=(GREEN,)):
    global row
    a.cell(row, 1, title_).font = Font(name=FONT, bold=True, size=11, color="2E6FA3")
    row += 1
    hdr(a, row, list(frame.columns), GREEN)
    row += 1
    for _, rec in frame.iterrows():
        for j, v in enumerate(rec):
            c = a.cell(row, 1 + j, v)
            body(c, "#,##0.0" if isinstance(v, float) else ("#,##0" if isinstance(v, int) else None))
        row += 1
    # colour scale on the last numeric column
    a.conditional_formatting.add(f"{get_column_letter(len(frame.columns))}{row - len(frame)}:"
                                 f"{get_column_letter(len(frame.columns))}{row - 1}",
                                 ColorScaleRule(start_type="min", start_color="F2F7FD",
                                                end_type="max", end_color="2E6FA3"))
    row += 1


btab = (val.assign(sh=lambda d: 1).groupby("neighbourhood_group")
        .agg(listings=("sh", "count"), entire_pct=("is_entire_home", "mean"),
             mean_reviews=("number_of_reviews", "mean"), mean_avail=("availability_365", "mean"))
        .assign(med_price=valc.groupby("neighbourhood_group")["price"].median())
        .round({"entire_pct": 3, "mean_reviews": 1, "mean_avail": 1, "med_price": 0})
        .reset_index())
table("Listings, mix and traction by borough", btab)
rtab = (val.assign(sh=lambda d: 1).groupby("room_type")
        .agg(listings=("sh", "count"), mean_reviews=("number_of_reviews", "mean"))
        .assign(med_price=valc.groupby("room_type")["price"].median()).reset_index())
table("Listing types: volume, price, traction", rtab)
ntop = (val.groupby("neighbourhood").agg(listings=("id", "count"),
        med_price=("price", lambda x: round(float(x[x <= 1000].median()), 0)),
        mean_reviews=("number_of_reviews", "mean"))
        .sort_values("listings", ascending=False).head(15).reset_index().round({"mean_reviews": 1}))
table("Top 15 neighbourhoods by listing count", ntop)
nprice = (val.groupby("neighbourhood").agg(listings=("id", "count"),
          med_price=("price", lambda x: round(float(x[x <= 1000].median()), 0)))
          .query("listings >= 30").sort_values("med_price", ascending=False).head(12).reset_index())
table("Priciest neighbourhoods (min. 30 listings)", nprice)
atable = (val["avail_segment"].value_counts().reset_index()
          .rename(columns={"index": "availability", "avail_segment": "listings"}))
atable.columns = ["availability", "listings"]
table("Availability segments", atable)
ptab = (val["price_band"].value_counts().reset_index())
ptab.columns = ["price_band", "listings"]
table("Price bands", ptab)
a.column_dimensions["A"].width = 32
for col in ("B", "C", "D", "E", "F"):
    a.column_dimensions[col].width = 18

# ------------------------------------------------------------- Cleaning Log
cl = wb.create_sheet("Cleaning Log")
cl.sheet_properties.tabColor = YELLOW
title(cl, "Cleaning log: every check, finding and action")
hdr(cl, 4, ["Step", "Action", "Detail"], YELLOW)
for i, s in enumerate(log["steps"]):
    cl.cell(5 + i, 1, i + 1)
    cl.cell(5 + i, 2, s["action"])
    cl.cell(5 + i, 3, s["detail"])
    for cc in (1, 2, 3):
        body(cl.cell(5 + i, cc))
        cl.cell(5 + i, cc).alignment = Alignment(wrap_text=True, vertical="top")
cl.column_dimensions["A"].width = 8
cl.column_dimensions["B"].width = 24
cl.column_dimensions["C"].width = 130

# ------------------------------------------------------------- Data Dictionary
dd = wb.create_sheet("Data Dictionary")
dd.sheet_properties.tabColor = LAV
title(dd, "Data dictionary: every column and its source")
hdr(dd, 4, ["Column", "Type", "Source / logic"], LAV)
DICT = [
    ("id", "int", "raw listing id"), ("name", "text", "raw; 16 blanks -> 'Unnamed listing'"),
    ("host_id", "int", "raw"), ("host_name", "text", "raw; 21 blanks -> 'Unknown host'"),
    ("neighbourhood_group", "text", "raw borough"), ("neighbourhood", "text", "raw area (221)"),
    ("latitude / longitude", "float", "raw; all inside NYC bbox"),
    ("room_type", "text", "raw: Entire home/apt, Private room, Shared room"),
    ("price", "int $", "raw nightly price; 11 zeros removed"),
    ("price_capped", "int $", "MIN(price,1000): outlier-safe averages"),
    ("minimum_nights / stay_bin", "int / band", "raw + 7-bin grouping (1..31+)"),
    ("number_of_reviews", "int", "raw"), ("last_review", "date", "raw; NaT = never reviewed"),
    ("reviews_per_month", "float", "raw; 10,052 gaps = zero-review rows -> 0"),
    ("calculated_host_listings_count", "int", "raw portfolio size"),
    ("availability_365", "int", "raw open days next year"),
    ("price_band / avail_segment / host_size", "bands", "Budget/Mid/Premium/Luxury; Inactive..Fully open; Single..Large"),
    ("flag_never_reviewed / flag_price_outlier / flag_min_nights_extreme",
     "0/1", "reviews=0; price>1000 (239); min_nights>=365 (43)"),
    ("is_entire_home / is_zero_avail", "0/1", "pivot helpers: AVERAGE = share"),
]
for i, (c, t, s) in enumerate(DICT):
    dd.cell(5 + i, 1, c)
    dd.cell(5 + i, 2, t)
    dd.cell(5 + i, 3, s)
    for cc in (1, 2, 3):
        body(dd.cell(5 + i, cc))
dd.column_dimensions["A"].width = 52
dd.column_dimensions["B"].width = 12
dd.column_dimensions["C"].width = 80

wb.save(OUT)
print(f"saved {OUT.name}: {OUT.stat().st_size/1e6:.1f} MB, {N:,} rows x {len(cols)} cols")
