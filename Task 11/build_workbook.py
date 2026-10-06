"""
Step 4: build the base Excel workbook (data table, KPI formulas, analysis tables,
cleaning log and data dictionary) with openpyxl.

Pivot tables, pivot charts, slicers, KPI cards and the Dashboard sheet are added in
step 5 (build_dashboard.py) through Excel itself, because openpyxl cannot create them.
"""

import json
import os

import numpy as np
import pandas as pd
from openpyxl import Workbook
from openpyxl.formatting.rule import ColorScaleRule, DataBarRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.table import Table, TableStyleInfo

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "GameSales_Base.xlsx")
NAVY, TEAL, CORAL, GOLD, GREY = "1F3B57", "1B998B", "E4572E", "E0A030", "F3F6F9"
FONT = "Arial"

TEXT_COLS = ["Game", "Platform", "Platform_Family", "Decade", "Genre", "Publisher", "Publisher_Group",
             "Developer", "Critic_Band", "Rating", "Rating_Band", "Has_Reviews",
             "Flag_Unnamed", "Flag_Year_Imputed", "Flag_Year_Unknown", "Flag_Year_Future", "Flag_Unknown_Publisher"]
INT_COLS = ["Release_Year", "Rank_Global", "Critic_Score", "Rank_Critic", "Critic_Count", "User_Count"]
NUM_COLS = ["NA_Sales", "EU_Sales", "JP_Sales", "Other_Sales", "Global_Sales", "User_Score"]
DATE_COLS = ["Release_Date"]

df = pd.read_csv(os.path.join(HERE, "Cleaned_Video_Games.csv"))
log = json.load(open(os.path.join(HERE, "cleaning_log.json"), encoding="utf-8"))


def _py(v):
    """pandas/numpy scalars -> plain Python (openpyxl refuses numpy types)."""
    if v is None or v is pd.NaT:
        return None
    if isinstance(v, float) and np.isnan(v):
        return None
    if isinstance(v, np.integer):
        return int(v)
    if isinstance(v, np.floating):
        return None if np.isnan(v) else float(v)
    return v


df["Release_Date"] = pd.to_datetime(df["Release_Date"], errors="coerce").dt.date
df = df.map(_py)
N = len(df)
LAST = N + 1

wb = Workbook()
thin = Side(style="thin", color="D0D7DE")
BOX = Border(left=thin, right=thin, top=thin, bottom=thin)


def hdr(ws, row, values, col=1, fill=NAVY):
    for i, v in enumerate(values):
        c = ws.cell(row, col + i, v)
        c.font = Font(name=FONT, bold=True, color="FFFFFF", size=10)
        c.fill = PatternFill("solid", fgColor=fill)
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        c.border = BOX


def title(ws, text, sub=None):
    ws["A1"] = text
    ws["A1"].font = Font(name=FONT, bold=True, size=16, color=NAVY)
    if sub:
        ws["A2"] = sub
        ws["A2"].font = Font(name=FONT, italic=True, size=10, color="5A6B7B")
    ws.sheet_view.showGridLines = False


def body(c, fmt=None, bold=False, color="000000"):
    c.font = Font(name=FONT, size=10, bold=bold, color=color)
    c.border = BOX
    if fmt:
        c.number_format = fmt


# ---------------------------------------------------------------- Data sheet
ws = wb.active
ws.title = "Data"
cols = list(df.columns)
ws.append(cols)
for row in df.itertuples(index=False, name=None):
    ws.append(list(row))
L = {c: get_column_letter(i + 1) for i, c in enumerate(cols)}
for c in DATE_COLS:
    for cell in ws[L[c]][1:]:
        cell.number_format = "yyyy-mm-dd"
for c in INT_COLS:
    for cell in ws[L[c]][1:]:
        cell.number_format = "#,##0"
for c in NUM_COLS:
    for cell in ws[L[c]][1:]:
        cell.number_format = "#,##0.00"
tab = Table(displayName="tblGames", ref=f"A1:{get_column_letter(len(cols))}{LAST}")
tab.tableStyleInfo = TableStyleInfo(name="TableStyleMedium2", showRowStripes=True)
ws.add_table(tab)
ws.freeze_panes = "B2"
for i, c in enumerate(cols):
    ws.column_dimensions[get_column_letter(i + 1)].width = max(11, min(26, len(c) + 3))


def R(col):
    """Absolute range of a Data column (fast in formulas, stable in every Excel version)."""
    return f"Data!${L[col]}$2:${L[col]}${LAST}"


GS, NA, EU, JP, OT = R("Global_Sales"), R("NA_Sales"), R("EU_Sales"), R("JP_Sales"), R("Other_Sales")
TOTAL = f"SUM({GS})"

# ---------------------------------------------------------------- KPIs sheet
k = wb.create_sheet("KPIs")
title(k, "Key performance indicators (all 16,717 rows)",
      "Every value is a live formula on the Data sheet. The Dashboard cards show the same measures for the "
      "current slicer selection.")
hdr(k, 4, ["#", "KPI", "Value", "Formula logic", "Why it matters"])
kpis = [
    ("Titles in the file", f"=COUNTA({R('Game')})", "#,##0", "COUNTA of Game", "Size of the catalogue"),
    ("Total global sales", f"={TOTAL}", "#,##0.0\"M\"", "SUM of Global_Sales", "Market size in the file"),
    ("Average sales per title", "=C6/C5", "#,##0.000\"M\"", "Total sales / titles", "How much a typical title earns"),
    ("Median sales per title", f"=MEDIAN({GS})", "#,##0.000\"M\"", "MEDIAN of Global_Sales",
     "The middle title - blockbusters do not move it"),
    ("Titles selling 1M+", f'=COUNTIF({GS},">=1")', "#,##0", 'COUNTIF Global_Sales >= 1', "Hits"),
    ("Share of titles under 0.1M", f'=COUNTIF({GS},"<0.1")/C5', "0.0%", "COUNTIF < 0.1M / titles",
     "The long tail of the catalogue"),
    ("Titles with a release year", f"=COUNT({R('Release_Year')})", "#,##0", "COUNT of Release_Year",
     "158 rows carry no year"),
    ("Share of titles with a year", "=C11/C5", "0.0%", "Dated titles / titles", "Coverage of the trend"),
    ("Titles with a critic score", f"=COUNT({R('Critic_Score')})", "#,##0", "COUNT of Critic_Score",
     "Reviewed titles only"),
    ("Share of titles reviewed", "=C13/C5", "0.0%", "Reviewed / titles", "Half the file has no score"),
    ("Average critic score", f"=AVERAGE({R('Critic_Score')})", "0.0", "AVERAGE of Critic_Score (blanks ignored)",
     "Quality signal where it exists"),
    ("Average user score", f"=AVERAGE({R('User_Score')})", "0.00", "AVERAGE of User_Score (0-10 scale)",
     "Player signal where it exists"),
    ("North America share", f"=SUM({NA})/{TOTAL}", "0.0%", "SUM NA_Sales / total", "Biggest market"),
    ("Europe share", f"=SUM({EU})/{TOTAL}", "0.0%", "SUM EU_Sales / total", "Second market"),
    ("Japan share", f"=SUM({JP})/{TOTAL}", "0.0%", "SUM JP_Sales / total", "Distinct taste profile"),
    ("Rest of world share", f"=SUM({OT})/{TOTAL}", "0.0%", "SUM Other_Sales / total", "Everything else"),
    ("Nintendo sales", f'=SUMIF({R("Publisher")},"Nintendo",{GS})', "#,##0.0\"M\"", 'SUMIF Publisher = "Nintendo"',
     "The single biggest publisher"),
    ("Nintendo share of sales", "=C21/C6", "0.0%", "Nintendo sales / total", "One company, one fifth of the market"),
    ("Action sales", f'=SUMIF({R("Genre")},"Action",{GS})', "#,##0.0\"M\"", 'SUMIF Genre = "Action"',
     "The biggest genre"),
    ("PS2 sales", f'=SUMIF({R("Platform")},"PS2",{GS})', "#,##0.0\"M\"", 'SUMIF Platform = "PS2"',
     "The biggest platform"),
    ("Titles rated 90+ by critics", f'=COUNTIF({R("Critic_Band")},"90+")', "#,##0", 'COUNTIF Critic_Band = "90+"',
     "Critical darlings"),
    ("Average sales, 90+ critic titles",
     f'=AVERAGEIF({R("Critic_Band")},"90+",{GS})', "#,##0.00\"M\"", "AVERAGEIF Critic_Band = 90+",
     "Do great scores sell? (compare with the median title)"),
    ("Average sales, under 60 critic titles",
     f'=AVERAGEIF({R("Critic_Band")},"Under 60",{GS})', "#,##0.00\"M\"", "AVERAGEIF Critic_Band = Under 60",
     "The bottom of the score range"),
    ("Titles with no release year", f'=COUNTIF({R("Flag_Year_Unknown")},"Yes")', "#,##0",
     'COUNTIF Flag_Year_Unknown = "Yes"', "Excluded from the yearly trend"),
    ("Rows dated after the 2016 cutoff", f'=COUNTIF({R("Flag_Year_Future")},"Yes")', "#,##0",
     'COUNTIF Flag_Year_Future = "Yes"', "Flagged, excluded from the trend"),
]
for i, (name, f, fmt, logic, why) in enumerate(kpis):
    r = 5 + i
    for j, v in enumerate([i + 1, name, f, logic, why]):
        c = k.cell(r, 1 + j, v)
        body(c, fmt if j == 2 else None, bold=(j == 2), color=NAVY if j == 2 else "000000")
        if i % 2:
            c.fill = PatternFill("solid", fgColor=GREY)
for col, w in zip("ABCDE", (5, 38, 16, 46, 52)):
    k.column_dimensions[col].width = w
k.freeze_panes = "A5"
KPI_ROW = {name: 5 + i for i, (name, *_) in enumerate(kpis)}

# ----------------------------------------------------------- Analysis sheet
a = wb.create_sheet("Analysis")
title(a, "Analysis tables (all live formulas on the Data sheet)",
      "Category | titles | global sales | share | average per title. Sort order is fixed (highest sales first), "
      "values recalculate for the whole file.")
row = 4
BLOCKS = {}


def factor_block(field, heading, values=None, fill=NAVY):
    """Category table: value | titles | sales | % of sales | avg per title."""
    global row
    a.cell(row, 1, heading).font = Font(name=FONT, bold=True, size=12, color=NAVY)
    row += 1
    hdr(a, row, [field, "Titles", "Global sales (M)", "% of sales", "Avg per title (M)"])
    row += 1
    top = row
    cats = values if values is not None else sorted(df[field].dropna().unique())
    for v in cats:
        a.cell(row, 1, v)
        a.cell(row, 2, f'=COUNTIF({R(field)},A{row})')
        a.cell(row, 3, f'=SUMIF({R(field)},A{row},{GS})')
        a.cell(row, 4, f"=C{row}/{TOTAL}")
        a.cell(row, 5, f"=IFERROR(C{row}/B{row},0)")
        for j, fmt in enumerate([None, "#,##0", "#,##0.00", "0.0%", "0.000"]):
            body(a.cell(row, 1 + j), fmt)
        row += 1
    a.conditional_formatting.add(f"C{top}:C{row - 1}", DataBarRule(start_type="min", end_type="max", color="9BC4E2"))
    a.conditional_formatting.add(f"D{top}:D{row - 1}", ColorScaleRule(
        start_type="min", start_color="E8F6F3", mid_type="percentile", mid_value=50, mid_color="FFF4E0",
        end_type="max", end_color="F4B6A6"))
    BLOCKS[heading] = (top, row - 1)
    row += 2


order_by_sales = lambda col: df.groupby(col)["Global_Sales"].sum().sort_values(ascending=False).index.tolist()

factor_block("Genre", "1. Genres (ordered by total sales)")
factor_block("Platform", "2. Platforms (ordered by total sales)")
factor_block("Platform_Family", "3. Platform families")
factor_block("Publisher", "4. Publishers - top 20 by sales, then the rest",
             order_by_sales("Publisher")[:20] + ["Other publishers", "Unknown publisher"])
factor_block("Critic_Band", "5. Critic score bands",
             ["No critic score", "Under 60", "60-69", "70-79", "80-89", "90+"])
factor_block("Rating_Band", "6. ESRB rating bands",
             ["Everyone", "Everyone 10+", "Teen", "Mature", "Rating pending", "Unknown"])
factor_block("Decade", "7. Decades", ["1980s", "1990s", "2000s", "2010s", "2020s"])

# top games (a title that appears on several platforms is summed)
a.cell(row, 1, "8. Best-selling titles (SUMIF over the Game column)").font = Font(
    name=FONT, bold=True, size=12, color=NAVY)
row += 1
hdr(a, row, ["Game", "Platform rows", "Global sales (M)", "% of sales", "Platforms"])
row += 1
top_row = row
for g in df.groupby("Game")["Global_Sales"].sum().nlargest(15).index:
    a.cell(row, 1, g)
    a.cell(row, 2, f'=COUNTIF({R("Game")},A{row})')
    a.cell(row, 3, f'=SUMIF({R("Game")},A{row},{GS})')
    a.cell(row, 4, f"=C{row}/{TOTAL}")
    a.cell(row, 5, f'=IF(B{row}>1,B{row}&" rows","")')
    for j, fmt in enumerate([None, "#,##0", "#,##0.00", "0.0%", None]):
        body(a.cell(row, 1 + j), fmt)
    row += 1
a.conditional_formatting.add(f"C{top_row}:C{row - 1}", DataBarRule(start_type="min", end_type="max", color="9BC4E2"))
BLOCKS["8. Best-selling titles (SUMIF over the Game column)"] = (top_row, row - 1)
row += 2

# region mix
a.cell(row, 1, "9. Regional mix").font = Font(name=FONT, bold=True, size=12, color=NAVY)
row += 1
hdr(a, row, ["Region", "Sales (M)", "% of total", "2010s share", "Note"])
row += 1
reg_top = row
regs = [("North America", NA, "NA_Sales"), ("Europe", EU, "EU_Sales"), ("Japan", JP, "JP_Sales"),
        ("Rest of world", OT, "Other_Sales")]
for name, rng, col in regs:
    a.cell(row, 1, name)
    a.cell(row, 2, f"=SUM({rng})")
    a.cell(row, 3, f"=B{row}/{TOTAL}")
    a.cell(row, 4, f'=SUMIFS({rng},{R("Decade")},"2010s")/SUMIFS({GS},{R("Decade")},"2010s")')
    a.cell(row, 5, {"North America": "Largest market; share fell from 63% (1980s) to 45% (2010s)",
                    "Europe": "Grew from 8% to 33% of sales",
                    "Japan": "27% in the 1980s, 12% in the 2010s",
                    "Rest of world": "Australia, Latin America, Asia outside Japan"}[name])
    for j, fmt in enumerate([None, "#,##0.00", "0.0%", "0.0%", None]):
        body(a.cell(row, 1 + j), fmt)
    a.cell(row, 5).alignment = Alignment(wrap_text=True, vertical="top")
    row += 1
BLOCKS["9. Regional mix"] = (reg_top, row - 1)
row += 2

# ratings vs sales
a.cell(row, 1, "10. Do reviews go with sales?").font = Font(name=FONT, bold=True, size=12, color=NAVY)
row += 1
hdr(a, row, ["Measure", "Value", "How", "", ""])
row += 1
rate_top = row
corr_rows = [
    ("Critic score vs sales (Pearson)",
     f'=CORREL({R("Critic_Score")},{GS})', "0.000", "CORREL over rows with a critic score"),
    ("Critic score vs sales (Spearman)",
     "={SPEAR}", "0.000", "CORREL of the two rank columns on the Data sheet"),
    ("User score vs sales (Pearson)", f'=CORREL({R("User_Score")},{GS})', "0.000", "CORREL over rows with a user score"),
    ("Critic score vs user score", f'=CORREL({R("Critic_Score")},{R("User_Score")})', "0.000",
     "CORREL where both exist"),
    ("Average critic score", f"=AVERAGE({R('Critic_Score')})", "0.00", "AVERAGE, blanks ignored"),
    ("Average sales of a reviewed title", f'=AVERAGEIF({R("Has_Reviews")},"Yes",{GS})', "0.000",
     "AVERAGEIF Has_Reviews = Yes"),
    ("Average sales of an unreviewed title", f'=AVERAGEIF({R("Has_Reviews")},"No",{GS})', "0.000",
     "AVERAGEIF Has_Reviews = No"),
]
for name, f, fmt, how in corr_rows:
    a.cell(row, 1, name)
    a.cell(row, 2, f.replace("{SPEAR}", f"CORREL({R('Rank_Critic')},{R('Rank_Global')})"))
    a.cell(row, 3, how)
    for j in range(3):
        body(a.cell(row, 1 + j), fmt if j == 1 else None, bold=(j == 1), color=NAVY if j == 1 else "000000")
    row += 1
BLOCKS["10. Do reviews go with sales?"] = (rate_top, row - 1)

for col, w in zip("ABCDE", (46, 15, 19, 16, 44)):
    a.column_dimensions[col].width = w

# ----------------------------------------------------------- Cleaning log
c = wb.create_sheet("Cleaning Log")
title(c, "Data cleaning and preparation log",
      f"Raw file: Video_Games_Sales_as_at_22_Dec_2016.csv (16,719 rows). Clean table: {N:,} rows.")
hdr(c, 4, ["Step", "Check", "Finding", "Action taken", "Rows after"])
for i, r in enumerate(log):
    for j, v in enumerate([r["step"], r["check"], r["found"], r["action"], r["rows_after"]]):
        cell = c.cell(5 + i, 1 + j, v)
        body(cell, "#,##0" if j == 4 else None)
        cell.alignment = Alignment(wrap_text=True, vertical="top")
for col, w in zip("ABCDE", (6, 30, 62, 62, 12)):
    c.column_dimensions[col].width = w

# ----------------------------------------------------------- Data dictionary
d = wb.create_sheet("Data Dictionary")
title(d, "Data dictionary (tblGames)")
hdr(d, 3, ["Column", "Type", "Source", "Description"])
DESC = {
    "Game": ("Text", "Raw (cleaned)", "Game title; one row per title + platform + year"),
    "Platform": ("Text", "Raw", "31 platforms: PS2, X360, Wii, DS, PC, ..."),
    "Platform_Family": ("Text", "Derived", "PlayStation / Xbox / Nintendo / PC / Sega / Other"),
    "Release_Year": ("Integer", "Raw (cleaned)", "Year of release; 111 imputed from other platforms, 158 blank"),
    "Release_Date": ("Date", "Derived", "1 January of the release year - drives the timeline slicer"),
    "Decade": ("Text", "Derived", "1980s ... 2020s, blank when the year is unknown"),
    "Genre": ("Text", "Raw (cleaned)", "12 genres; 1 row set to Unknown after the title was lost"),
    "Publisher": ("Text", "Raw (cleaned)", "582 publishers; 54 rows set to Unknown publisher"),
    "Publisher_Group": ("Text", "Derived", "Top 10 publishers by sales, everything else = Other publishers"),
    "Developer": ("Text", "Raw (cleaned)", "1,697 developers; blank rows set to Unknown developer"),
    "NA_Sales": ("Decimal", "Raw", "North America sales, million units-equivalent"),
    "EU_Sales": ("Decimal", "Raw", "Europe sales, million"),
    "JP_Sales": ("Decimal", "Raw", "Japan sales, million"),
    "Other_Sales": ("Decimal", "Raw", "Rest of the world sales, million"),
    "Global_Sales": ("Decimal", "Raw", "Published world total; kept as published (8 rows differ by 0.01-0.02M)"),
    "Rank_Global": ("Integer", "Derived", "Sales rank of the row, ties share a rank (1 = best seller)"),
    "Critic_Score": ("Integer", "Raw", "Metacritic-style score 0-100; present on 8,136 rows"),
    "Rank_Critic": ("Integer", "Derived", "Critic-score rank - lets Excel reproduce Spearman's rho with CORREL"),
    "Critic_Band": ("Text", "Derived", "No critic score / Under 60 / 60-69 / 70-79 / 80-89 / 90+"),
    "Critic_Count": ("Integer", "Raw", "Number of critic reviews"),
    "User_Score": ("Decimal", "Raw", "User score 0-10; present on 7,589 rows (1 row scores 0 from 4 votes)"),
    "User_Count": ("Integer", "Raw", "Number of user reviews"),
    "Rating": ("Text", "Raw (cleaned)", "ESRB rating; 6,769 blanks set to Unknown"),
    "Rating_Band": ("Text", "Derived", "Everyone / Everyone 10+ / Teen / Mature / Rating pending / Unknown"),
    "Has_Reviews": ("Yes/No", "Derived", "At least one critic or user score (8,709 rows)"),
    "Flag_Unnamed": ("Yes/blank", "Quality flag", "Title was lost in the source"),
    "Flag_Year_Imputed": ("Yes/blank", "Quality flag", "Release year recovered from another platform"),
    "Flag_Year_Unknown": ("Yes/blank", "Quality flag", "No release year - excluded from the trend"),
    "Flag_Year_Future": ("Yes/blank", "Quality flag", "Dated after the 22 Dec 2016 cutoff"),
    "Flag_Unknown_Publisher": ("Yes/blank", "Quality flag", "Publisher missing in the raw file"),
}
for i, col in enumerate(cols):
    t, s, desc = DESC[col]
    for j, v in enumerate([col, t, s, desc]):
        body(d.cell(4 + i, 1 + j, v))
for col, w in zip("ABCD", (24, 11, 17, 78)):
    d.column_dimensions[col].width = w

wb.save(OUT)
print("saved", OUT)
print("rows", N, "| KPIs", len(kpis), "| analysis blocks", len(BLOCKS))
json.dump({name: list(rng) for name, rng in BLOCKS.items()},
          open(os.path.join(HERE, "analysis_blocks.json"), "w"), indent=2)
