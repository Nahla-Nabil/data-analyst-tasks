# -*- coding: utf-8 -*-
"""
Builds Sales_Analysis_Summary.xlsx from the cleaned dataset:
  - "Cleaned Data" sheet: the full cleaned dataset
  - "Summary" sheet: KPI totals, pivot-style tables (Category / Region / Month /
    Top Products) plus native Excel charts
"""

import os
import pandas as pd
from openpyxl.chart import BarChart, LineChart, PieChart, Reference
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CLEAN_FILE = os.path.join(BASE_DIR, "Sales_Dataset_Cleaned.csv")
OUT_FILE = os.path.join(BASE_DIR, "Sales_Analysis_Summary.xlsx")

df = pd.read_csv(CLEAN_FILE, parse_dates=["Order Date", "Ship Date"])

by_category = (df.groupby("Category")[["Sales", "Profit"]].sum()
                 .sort_values("Sales", ascending=False).reset_index())
by_region = (df.groupby("Region")[["Sales", "Profit"]].sum()
               .sort_values("Sales", ascending=False).reset_index())

month_order = ["January", "February", "March", "April", "May", "June", "July",
               "August", "September", "October", "November", "December"]
df["Month Name"] = df["Order Date"].dt.month_name()
by_month = (df.groupby("Month Name")[["Sales", "Profit"]].sum()
              .reindex(month_order).reset_index())
by_month.columns = ["Month", "Sales", "Profit"]

top_products = (df.groupby("Product Name")["Sales"].sum()
                   .sort_values(ascending=False).head(10).reset_index())
top_products.columns = ["Product Name", "Sales"]

total_sales = float(df["Sales"].sum())
total_profit = float(df["Profit"].sum())

# --- Write data with pandas first ---
with pd.ExcelWriter(OUT_FILE, engine="openpyxl") as writer:
    df.drop(columns=["Month Name"]).to_excel(writer, sheet_name="Cleaned Data", index=False)
    by_category.to_excel(writer, sheet_name="Summary", index=False, startrow=9, startcol=0)
    by_region.to_excel(writer, sheet_name="Summary", index=False, startrow=9, startcol=4)
    by_month.to_excel(writer, sheet_name="Summary", index=False, startrow=24, startcol=0)
    top_products.to_excel(writer, sheet_name="Summary", index=False, startrow=9, startcol=8)

# --- Reopen for styling + KPI header + native charts ---
import openpyxl
wb = openpyxl.load_workbook(OUT_FILE)
ws = wb["Summary"]

header_font = Font(bold=True, size=14, color="FFFFFF")
header_fill = PatternFill("solid", fgColor="2E86AB")
label_font = Font(bold=True, size=11)
table_header_font = Font(bold=True)
table_header_fill = PatternFill("solid", fgColor="D9E7F0")

ws["A1"] = "Task 1 — Basic Sales Data Analysis: Summary"
ws["A1"].font = header_font
ws["A1"].fill = header_fill
ws.merge_cells("A1:L1")
ws["A1"].alignment = Alignment(horizontal="left", vertical="center")
ws.row_dimensions[1].height = 24

ws["A3"] = "Total Sales"
ws["A3"].font = label_font
ws["B3"] = total_sales
ws["B3"].number_format = '"$"#,##0.00'

ws["A4"] = "Total Profit"
ws["A4"].font = label_font
ws["B4"] = total_profit
ws["B4"].number_format = '"$"#,##0.00'

ws["A5"] = "Overall Profit Margin"
ws["A5"].font = label_font
ws["B5"] = total_profit / total_sales
ws["B5"].number_format = "0.0%"

ws["A6"] = "Orders Analyzed"
ws["A6"].font = label_font
ws["B6"] = len(df)

ws["A8"] = "Sales & Profit by Category"
ws["E8"] = "Sales & Profit by Region"
ws["I8"] = "Top 10 Products by Sales"
ws["A23"] = "Sales & Profit by Calendar Month"
for cell in ("A8", "E8", "I8", "A23"):
    ws[cell].font = label_font

# style table headers + currency formatting for the three money tables
def style_table(start_row, start_col, ncols, money_cols):
    hdr_row = start_row + 1
    for c in range(ncols):
        col_letter = get_column_letter(start_col + c)
        cell = ws[f"{col_letter}{hdr_row}"]
        cell.font = table_header_font
        cell.fill = table_header_fill
    for money_col in money_cols:
        col_letter = get_column_letter(start_col + money_col)
        for r in range(hdr_row + 1, hdr_row + 20):
            cell = ws[f"{col_letter}{r}"]
            if cell.value is None:
                break
            cell.number_format = '"$"#,##0'

style_table(9, 1, 3, [1, 2])    # Category table (A..C), cols 1,2 are Sales/Profit
style_table(9, 5, 3, [1, 2])    # Region table (E..G)
style_table(9, 9, 2, [1])       # Top products (I..J)
style_table(24, 1, 3, [1, 2])   # Month table (A..C)

# widen columns
for col, width in {"A": 22, "B": 14, "C": 12, "E": 12, "F": 14, "G": 12,
                    "I": 40, "J": 14}.items():
    ws.column_dimensions[col].width = width

# --- Charts ---
# Bar: Sales by Category
bar1 = BarChart()
bar1.title = "Sales by Category"
bar1.y_axis.title = "Sales"
data = Reference(ws, min_col=2, min_row=10, max_row=13, max_col=2)
cats = Reference(ws, min_col=1, min_row=11, max_row=13)
bar1.add_data(data, titles_from_data=True)
bar1.set_categories(cats)
bar1.width, bar1.height = 11, 7
ws.add_chart(bar1, "A38")

# Pie: Sales by Region
pie1 = PieChart()
pie1.title = "Sales Share by Region"
data = Reference(ws, min_col=6, min_row=10, max_row=13, max_col=6)
cats = Reference(ws, min_col=5, min_row=11, max_row=13)
pie1.add_data(data, titles_from_data=True)
pie1.set_categories(cats)
pie1.width, pie1.height = 11, 7
ws.add_chart(pie1, "F38")

# Line: Sales by Month
line1 = LineChart()
line1.title = "Sales by Calendar Month"
line1.y_axis.title = "Sales"
data = Reference(ws, min_col=2, min_row=25, max_row=37, max_col=2)
cats = Reference(ws, min_col=1, min_row=26, max_row=37)
line1.add_data(data, titles_from_data=True)
line1.set_categories(cats)
line1.width, line1.height = 22, 7
ws.add_chart(line1, "A55")

wb.save(OUT_FILE)
print(f"Saved: {OUT_FILE}")
