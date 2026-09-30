"""
Step 5: builds a Power BI project (PBIP) for the customer dashboard.

Reads  Cleaned_Customers.csv, analysis_summary.json
Writes PowerBI/Customer_Dashboard.pbip
       PowerBI/Customer_Dashboard.SemanticModel/   model.bim: Power Query load of the CSV, Calendar table, a disconnected
                                                   'Field Quality' table, sort columns, relationship and every DAX measure
       PowerBI/Customer_Dashboard.Report/          PBIR report: 5 pages, synced slicers, KPI cards, charts, tables

Open the .pbip in Power BI Desktop, press Refresh (the project stores no data), then File > Save as > .pbix.
The CSV path is written into the Power Query as an absolute path - rerun this script if the folder moves.
Pattern reused from Task 7 (build_powerbi.py), which was verified in Power BI Desktop 2.157.
"""

import json
import os
import shutil
import uuid
import zipfile

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
CSV = os.path.join(HERE, "Cleaned_Customers.csv")
OUT = os.path.join(HERE, "PowerBI")
NAME = "Customer_Dashboard"
T = "Customers"
THEME_SRC = os.path.join(HERE, "..", "Task 3", "HR_Attrition_Model_Nahla.pbix")   # source of the base theme file
BASE_THEME = "Fluent2-CY26SU09"
S = json.load(open(os.path.join(HERE, "analysis_summary.json"), encoding="utf-8"))
K = S["kpi"]

# ------------------------------------------------------------------ semantic model: Customers table
df = pd.read_csv(CSV, keep_default_na=False, dtype=str)
INTS = ["Age", "Year", "Month_Num", "Weekday_Num", "Rating", "Valid_Fields"]
TYPES = {}
for c in df.columns:
    if c == "Purchase_Date":
        TYPES[c] = ("dateTime", "type date")
    elif c == "Purchase_Amount":
        TYPES[c] = ("double", "type number")
    elif c in INTS:
        TYPES[c] = ("int64", "Int64.Type")
    else:
        TYPES[c] = ("string", "type text")
BLANKABLE = [c for c in df.columns if (df[c] == "").any()]

m_types = ", ".join(f'{{"{c}", {mt}}}' for c, (_, mt) in TYPES.items())
m_blank = ", ".join(f'"{c}"' for c in BLANKABLE)
M = [
    "let",
    f'    Source = Csv.Document(File.Contents("{CSV}"), [Delimiter = ",", Columns = {len(df.columns)}, Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),',
    "    Promoted = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),",
    f'    Blanks = Table.ReplaceValue(Promoted, "", null, Replacer.ReplaceValue, {{{m_blank}}}),',
    f'    Typed = Table.TransformColumnTypes(Blanks, {{{m_types}}}, "en-US"),',
    # sort helpers and labels are built here, not as DAX columns (a DAX sort column derived from its own target is circular)
    '    AgeSort = Table.AddColumn(Typed, "AgeSort", each List.PositionOf({"15-29", "30-44", "45-59", "60-74", "75-90", "Unknown"}, [Age_Group]) + 1, Int64.Type),',
    '    BandSort = Table.AddColumn(AgeSort, "BandSort", each List.PositionOf({"Under $250", "$250-499", "$500-749", "$750+", "Unknown"}, [Spend_Band]) + 1, Int64.Type),',
    '    RatingSort = Table.AddColumn(BandSort, "RatingBandSort", each List.PositionOf({"Dissatisfied (1-2)", "Neutral (3)", "Satisfied (4-5)", "No rating"}, [Rating_Band]) + 1, Int64.Type),',
    '    Stars = Table.AddColumn(RatingSort, "Stars", each if [Rating] = null then null else Text.From([Rating]) & " star", type text)',
    "in",
    "    Stars",
]

FMT = {"Purchase_Amount": "\\$#,0.00", "Purchase_Date": "yyyy-mm-dd", "Age": "0", "Rating": "0", "Year": "0"}
SORT_BY = {"Age_Group": "AgeSort", "Spend_Band": "BandSort", "Rating_Band": "RatingBandSort", "Month_Name": "Month_Num", "Weekday": "Weekday_Num"}
columns = []
for c, (dt, _) in TYPES.items():
    col = {"name": c, "dataType": dt, "sourceColumn": c, "summarizeBy": "none"}
    if c in FMT:
        col["formatString"] = FMT[c]
    if c == "Purchase_Amount":
        col["summarizeBy"] = "sum"
    if c in SORT_BY:
        col["sortByColumn"] = SORT_BY[c]
    columns.append(col)
for c in ["AgeSort", "BandSort", "RatingBandSort"]:
    columns.append({"name": c, "dataType": "int64", "sourceColumn": c, "summarizeBy": "none", "isHidden": True})
columns.append({"name": "Stars", "dataType": "string", "sourceColumn": "Stars", "summarizeBy": "none"})

# ------------------------------------------------------------------ data-quality helper table (disconnected)
FIELDS = ["Purchase amount", "Purchase date", "Gender", "Product category", "Rating", "Age", "Phone"]
STATUSES = ["Usable", "Blank", "Invalid"]
rows = ", ".join(f'{{"{f}", {i + 1}, "{s}", {j + 1}}}' for i, f in enumerate(FIELDS) for j, s in enumerate(STATUSES))
M_FQ = ["let", f"    Source = #table(type table [Field = text, FieldSort = Int64.Type, Status = text, StatusSort = Int64.Type], {{{rows}}})",
        "in", "    Source"]
Q = {  # (field, status) -> filter on Customers
    ("Purchase amount", "Usable"): 'Customers[Amount_Status] = "Recorded"', ("Purchase amount", "Blank"): 'Customers[Amount_Status] = "Missing"',
    ("Purchase date", "Usable"): 'Customers[Date_Status] = "Valid"', ("Purchase date", "Invalid"): 'Customers[Date_Status] = "Invalid"',
    ("Gender", "Usable"): 'Customers[Gender] <> "Unknown"', ("Gender", "Blank"): 'Customers[Gender] = "Unknown"',
    ("Product category", "Usable"): 'Customers[Product_Category] <> "Unknown"', ("Product category", "Blank"): 'Customers[Product_Category] = "Unknown"',
    ("Rating", "Usable"): 'Customers[Rating_Status] = "Valid"', ("Rating", "Blank"): 'Customers[Rating_Status] = "Missing"',
    ("Rating", "Invalid"): 'Customers[Rating_Status] = "Out of range (10)"',
    ("Age", "Usable"): 'Customers[Age_Status] = "Valid"', ("Age", "Blank"): 'Customers[Age_Status] = "Missing"',
    ("Age", "Invalid"): 'Customers[Age_Status] IN { "Placeholder -1", "Placeholder 200" }',
    ("Phone", "Blank"): 'Customers[Phone_Status] = "Missing"', ("Phone", "Invalid"): 'Customers[Phone_Status] = "Placeholder"',
}
quality_expr = ("VAR k = SELECTEDVALUE ( 'Field Quality'[Field] ) & \"|\" & SELECTEDVALUE ( 'Field Quality'[Status] )\nRETURN\n    SWITCH ( k,\n" +
                ",\n".join(f'        "{f}|{s}", CALCULATE ( [Customers], {flt} )' for (f, s), flt in Q.items()) + "\n    )")

# ------------------------------------------------------------------ measures
MEASURES = [
    ("Customers", "COUNTROWS ( Customers )", "#,0", "Customers: unique customer IDs (one purchase each)"),
    ("Revenue", "SUM ( Customers[Purchase_Amount] )", "\\$#,0", "Revenue: recorded amounts only (97 blanks are not estimated)"),
    ("Priced Orders", "COUNT ( Customers[Purchase_Amount] )", "#,0", "Revenue: purchases with a recorded amount"),
    ("AOV", "AVERAGE ( Customers[Purchase_Amount] )", "\\$#,0", "Revenue: average order value"),
    ("Median Order", "MEDIAN ( Customers[Purchase_Amount] )", "\\$#,0", "Revenue: median order value"),
    ("Valid Ratings", "COUNT ( Customers[Rating] )", "#,0", "Satisfaction: ratings on the 1-5 scale (blank and '10' excluded)"),
    ("Rated", "VAR r = [Valid Ratings] RETURN IF ( r > 0, r )", "#,0", "Valid ratings, blank when zero (hides 'No rating' in stacked charts)"),
    ("Avg Rating", "AVERAGE ( Customers[Rating] )", "0.00", "Satisfaction: average of valid ratings"),
    ("Satisfied %", "DIVIDE ( CALCULATE ( [Valid Ratings], Customers[Rating] >= 4 ), [Valid Ratings] )", "0.0%", "Satisfaction: 4-5 star share"),
    ("Dissatisfied %", "DIVIDE ( CALCULATE ( [Valid Ratings], Customers[Rating] <= 2 ), [Valid Ratings] )", "0.0%", "Satisfaction: 1-2 star share"),
    ("Net Satisfaction", "[Satisfied %] - [Dissatisfied %]", "+0.0%;-0.0%;0.0%", "Satisfaction: satisfied minus dissatisfied"),
    ("Rating Share", "VAR r = [Valid Ratings] RETURN IF ( r > 0, DIVIDE ( r, CALCULATE ( [Valid Ratings], ALLSELECTED ( Customers[Stars] ) ) ) )",
     "0.0%", "Share of valid ratings at each star level"),
    ("Complete Records %", 'DIVIDE ( CALCULATE ( [Customers], Customers[Complete_Record] = "Yes" ), [Customers] )', "0.0%",
     "Data quality: age, gender, amount, date, category and rating all valid"),
    ("Usable Age %", 'DIVIDE ( CALCULATE ( [Customers], Customers[Age_Status] = "Valid" ), [Customers] )', "0.0%", "Data quality: real ages (not -1 / 200 / blank)"),
    ("Customers with Age", 'CALCULATE ( [Customers], Customers[Age_Status] = "Valid" )', "#,0", "Customers with a real age"),
    ("Customer Share", "DIVIDE ( [Customers], CALCULATE ( [Customers], ALLSELECTED ( Customers ) ) )", "0.0%", "Share of the current selection"),
    ("Order Share", "DIVIDE ( [Priced Orders], CALCULATE ( [Priced Orders], ALLSELECTED ( Customers ) ) )", "0%", "Share of priced orders in the selection"),
    ("Revenue Share", "DIVIDE ( [Revenue], CALCULATE ( [Revenue], ALLSELECTED ( Customers ) ) )", "0%", "Share of revenue in the selection"),
    ("Big Ticket Revenue %", 'DIVIDE ( CALCULATE ( [Revenue], Customers[Spend_Band] = "$750+" ), [Revenue] )', "0%", "Revenue from $750+ orders"),
    ("Unassigned Revenue %", 'DIVIDE ( CALCULATE ( [Revenue], Customers[Product_Category] = "Unknown" ), [Revenue] )', "0%",
     "Revenue with no product category"),
    ("Full Months", "CALCULATE ( DISTINCTCOUNT ( 'Calendar'[Year_Month] ), KEEPFILTERS ( 'Calendar'[Year_Month] >= \"2022-11\" && 'Calendar'[Year_Month] <= \"2025-06\" ) )",
     "0", "Trend: complete months in the selected period (Oct 2022 and Jul 2025 are partial)"),
    ("Purchases per Month", 'DIVIDE ( CALCULATE ( [Customers], Customers[Full_Month] = "Yes" ), [Full Months] )', "0.0", "Trend: purchases per full month"),
    ("Revenue per Month", 'DIVIDE ( CALCULATE ( [Revenue], Customers[Full_Month] = "Yes" ), [Full Months] )', "\\$#,0", "Trend: revenue per full month"),
    ("Full-Month Revenue", 'CALCULATE ( [Revenue], Customers[Full_Month] = "Yes" )', "\\$#,0", "Trend: revenue, blank for the two partial months"),
    ("Full-Month Purchases", 'CALCULATE ( [Customers], Customers[Full_Month] = "Yes" )', "#,0", "Trend: purchases, blank for the two partial months"),
    ("Dated Purchases", 'CALCULATE ( [Customers], Customers[Date_Status] = "Valid" )', "#,0", "Purchases with a valid date"),
    ("Days of Data", "COUNTROWS ( 'Calendar' )", "#,0", "Calendar days covered by the data in the current filter"),
    ("Purchases per 30 Days", "DIVIDE ( [Customers], [Days of Data] ) * 30", "0.0",
     "Seasonality: purchases per 30 days of data (fair across months that occur in 2 or 3 years)"),
    ("H1 Revenue", "CALCULATE ( [Revenue], KEEPFILTERS ( 'Calendar'[Month_Num] IN { 1, 2, 3, 4, 5, 6 } ) )", "\\$#,0", "Trend: January-June revenue (like-for-like across years)"),
    ("Quality Rows", quality_expr, "#,0", "Data quality: customers per field and status (Usable / Blank / Invalid)"),
]


def lineage():
    return str(uuid.uuid4())


def calc_col(name, dt, fmt=None, sort=None):
    c = {"type": "calculatedTableColumn", "name": name, "dataType": dt, "isNameInferred": True, "isDataTypeInferred": True,
         "sourceColumn": f"[{name}]", "summarizeBy": "none"}
    if fmt:
        c["formatString"] = fmt
    if sort:
        c["sortByColumn"] = sort
    return c


model = {
    "compatibilityLevel": 1567,
    "model": {
        "culture": "en-US",
        "dataAccessOptions": {"legacyRedirects": True, "returnErrorValuesAsNull": True},
        "defaultPowerBIDataSourceVersion": "powerBI_V3",
        "sourceQueryCulture": "en-US",
        "tables": [
            {"name": T, "lineageTag": lineage(), "columns": columns,
             "partitions": [{"name": T, "mode": "import", "source": {"type": "m", "expression": M}}],
             "measures": [{"name": n, "expression": e.split("\n") if "\n" in e else e, "formatString": f, "description": d,
                           "lineageTag": lineage()} for n, e, f, d in MEASURES]},
            {"name": "Calendar", "lineageTag": lineage(),
             "columns": [calc_col("Date", "dateTime", "yyyy-mm-dd"), calc_col("Year", "int64", "0"), calc_col("Month_Num", "int64"),
                         calc_col("Month", "string", sort="Month_Num"), calc_col("Year_Month", "string")],
             "partitions": [{"name": "Calendar", "mode": "import", "source": {"type": "calculated", "expression":
                             'ADDCOLUMNS ( CALENDAR ( DATE ( 2022, 10, 27 ), DATE ( 2025, 7, 23 ) ), "Year", YEAR ( [Date] ), '
                             '"Month_Num", MONTH ( [Date] ), "Month", FORMAT ( [Date], "MMM" ), "Year_Month", FORMAT ( [Date], "YYYY-MM" ) )'}}]},
            {"name": "Field Quality", "lineageTag": lineage(),
             "columns": [{"name": "Field", "dataType": "string", "sourceColumn": "Field", "summarizeBy": "none", "sortByColumn": "FieldSort"},
                         {"name": "FieldSort", "dataType": "int64", "sourceColumn": "FieldSort", "summarizeBy": "none", "isHidden": True},
                         {"name": "Status", "dataType": "string", "sourceColumn": "Status", "summarizeBy": "none", "sortByColumn": "StatusSort"},
                         {"name": "StatusSort", "dataType": "int64", "sourceColumn": "StatusSort", "summarizeBy": "none", "isHidden": True}],
             "partitions": [{"name": "Field Quality", "mode": "import", "source": {"type": "m", "expression": M_FQ}}]},
        ],
        "relationships": [{"name": lineage(), "fromTable": T, "fromColumn": "Purchase_Date", "toTable": "Calendar", "toColumn": "Date"}],
        "annotations": [{"name": "PBI_QueryOrder", "value": json.dumps([T, "Field Quality"])},
                        {"name": "__PBI_TimeIntelligenceEnabled", "value": "0"},
                        {"name": "PBIDesktopVersion", "value": "2.157.1354.0"}],
    },
}

# ------------------------------------------------------------------ report (PBIR)
SCHEMA = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition"
lit = lambda v: {"expr": {"Literal": {"Value": v}}}
TRUE, FALSE = lit("true"), lit("false")
ENTITY_OF = {"Year": "Calendar", "Month": "Calendar", "Field": "Field Quality", "Status": "Field Quality"}


def col(p, entity=None):
    return {"Column": {"Expression": {"SourceRef": {"Entity": entity or ENTITY_OF.get(p, T)}}, "Property": p}}


def mea(p):
    return {"Measure": {"Expression": {"SourceRef": {"Entity": T}}, "Property": p}}


def proj(field):
    kind = "Column" if "Column" in field else "Measure"
    ent = field[kind]["Expression"]["SourceRef"]["Entity"]
    prop = field[kind]["Property"]
    p = {"field": field, "queryRef": f"{ent}.{prop}", "nativeQueryRef": prop}
    if prop in DISPLAY:
        p["displayName"] = DISPLAY[prop]
    return p


DISPLAY = {"Product_Category": "Category", "Revenue Share": "% of revenue", "Avg Rating": "Avg rating", "Satisfied %": "Satisfied",
           "Dissatisfied %": "Dissatisfied", "Order Share": "% of orders", "H1 Revenue": "Jan-Jun revenue"}
UNITS_K = {"labelDisplayUnits": lit("1000D"), "labelPrecision": lit("0L")}      # $164K instead of $0.16M


def money_axis(objects=None, precision=0):
    o = dict(objects or {})
    o["valueAxis"] = [{"properties": {"labelDisplayUnits": lit("1000D")}}]
    o["labels_extra"] = {"labelDisplayUnits": lit("1000D"), "labelPrecision": lit(f"{precision}L")}
    return o


def series_colors(column, colors):
    """dataPoint colour per series value (e.g. red for 'Dissatisfied', blue for 'Satisfied')."""
    return [{"properties": {"fill": {"solid": {"color": lit(f"'{c}'")}}},
             "selector": {"data": [{"scopeId": {"Comparison": {"ComparisonKind": 0, "Left": column, "Right": {"Literal": {"Value": f"'{v}'"}}}}}]}}
            for v, c in colors.items()]


def vid():
    return uuid.uuid4().hex[:20]


class Page:
    def __init__(self, name, title):
        self.name, self.title, self.visuals, self.z = vid(), name, [], 0
        self.add_text(title, 16, 8, 1248, 36, size="18pt", bold=True)

    def _container(self, x, y, w, h, visual):
        self.z += 1000
        self.visuals.append({"$schema": f"{SCHEMA}/visualContainer/2.12.0/schema.json", "name": vid(),
                             "position": {"x": x, "y": y, "z": self.z, "height": h, "width": w, "tabOrder": self.z},
                             "visual": visual})

    def add(self, vtype, x, y, w, h, roles, title=None, sort=None, labels=True, objects=None, extra=None, title_size=None):
        qs = {role: {"projections": [proj(f) for f in fields]} for role, fields in roles.items()}
        query = {"queryState": qs}
        if sort:
            field, direction = sort
            query["sortDefinition"] = {"sort": [{"field": field, "direction": direction}]}
        objs = dict(objects or {})
        extra_labels = objs.pop("labels_extra", {})
        if labels and vtype not in ("card", "tableEx", "pivotTable", "slicer", "scatterChart"):
            objs["labels"] = [{"properties": {"show": TRUE, **extra_labels}}]
        visual = {"visualType": vtype, "query": query, "objects": objs, "drillFilterOtherVisuals": True}
        if title:
            tprops = {"show": TRUE, "text": lit("'" + title.replace("'", "''") + "'")}
            if title_size:
                tprops["fontSize"] = lit(f"{title_size}D")
            visual["visualContainerObjects"] = {"title": [{"properties": tprops}],
                                                "subTitle": [{"properties": {"show": FALSE}}]}
        if extra:
            visual.update(extra)
        self._container(x, y, w, h, visual)

    def add_card(self, x, y, w, h, measure, label, units=None, precision=None):
        props = {"fontSize": lit("20D"), "color": {"solid": {"color": lit("'#1F3A5F'")}}}
        if units:
            props["labelDisplayUnits"] = lit(f"{units}D")
        if precision is not None:
            props["labelPrecision"] = lit(f"{precision}L")
        self.add("card", x, y, w, h, {"Values": [mea(measure)]}, title=label, labels=False, title_size=10,
                 objects={"categoryLabels": [{"properties": {"show": FALSE}}], "labels": [{"properties": props}]})

    def add_slicer(self, x, y, w, h, column, title):
        self.add("slicer", x, y, w, h, {"Values": [col(column)]}, title=title, labels=False, title_size=9,
                 objects={"data": [{"properties": {"mode": lit("'Dropdown'")}}],
                          "header": [{"properties": {"show": FALSE}}]},
                 extra={"syncGroup": {"groupName": column, "fieldChanges": True, "filterChanges": True}})

    def add_text(self, text, x, y, w, h, size="10pt", bold=False, color="#1F3A5F"):
        paragraphs = []
        for line in text.split("\n"):
            style = {"fontSize": size, "color": color}
            if bold or line.startswith("# "):
                style["fontWeight"] = "bold"
                line = line[2:] if line.startswith("# ") else line
            paragraphs.append({"textRuns": [{"value": line, "textStyle": style}]})
        self._container(x, y, w, h, {"visualType": "textbox", "objects": {"general": [{"properties": {"paragraphs": paragraphs}}]},
                                     "drillFilterOtherVisuals": True})


SLICERS = [("Year", "Year"), ("Gender", "Gender"), ("Age_Group", "Age group"), ("Product_Category", "Category"),
           ("Spend_Band", "Order size"), ("Rating_Band", "Rating")]
RATING_COLORS = {"Dissatisfied (1-2)": "#E34948", "Neutral (3)": "#8F8D85", "Satisfied (4-5)": "#2A78D6"}
STAR_COLORS = {"1 star": "#E34948", "2 star": "#F19A99", "3 star": "#D5D3CB", "4 star": "#86B6EF", "5 star": "#2A78D6"}
QUALITY_COLORS = {"Usable": "#2A78D6", "Blank": "#8F8D85", "Invalid": "#EB6834"}


def slicer_row(p):
    w = 1248 // len(SLICERS)
    for i, (c, t) in enumerate(SLICERS):
        p.add_slicer(16 + i * w, 44, w - 8, 64, c, t)


DESC = lambda f: (f, "Descending")
ASC = lambda f: (f, "Ascending")
STACK_LABELS = {"labelPrecision": lit("0L")}     # Power BI keeps inside-segment labels white, so the grey segments use a mid grey
stacked_rating = lambda: {"dataPoint": series_colors(col("Rating_Band"), RATING_COLORS), "labels_extra": STACK_LABELS}
UNKNOWN_GRAY = lambda c: series_colors(col(c), {"Unknown": "#B9B7AE"})
pages = []

# 1 Overview
p = Page("Overview", f"Customer Analytics - {K['customers']:,} customers, Oct 2022 to Jul 2025")
slicer_row(p)
CARDS = [("Customers", "Customers"), ("Revenue", "Recorded revenue"), ("AOV", "Avg order value"), ("Purchases per Month", "Purchases / month"),
         ("Avg Rating", "Avg rating (1-5)"), ("Satisfied %", "Satisfied (4-5)"), ("Dissatisfied %", "Dissatisfied (1-2)"),
         ("Complete Records %", "Complete records")]
for i, (m, label) in enumerate(CARDS):
    p.add_card(16 + i * 156, 110, 148, 88, m, label, *((1000000, 2) if m == "Revenue" else (None, None)))
p.add("clusteredColumnChart", 16, 206, 800, 250, {"Category": [col("Year_Month")], "Y": [mea("Full-Month Revenue")]},
      "Recorded revenue per full month - flat, about $29K a month", sort=ASC(col("Year_Month")), labels=False, objects=money_axis())
p.add("clusteredBarChart", 824, 206, 440, 250, {"Category": [col("Product_Category")], "Y": [mea("Revenue")]},
      "Revenue by category (Unknown = no category)", sort=DESC(mea("Revenue")),
      objects=money_axis({"dataPoint": UNKNOWN_GRAY("Product_Category")}))
p.add("clusteredColumnChart", 16, 464, 408, 248, {"Category": [col("Spend_Band")], "Y": [mea("Order Share"), mea("Revenue Share")]},
      "Orders vs revenue by order size - $750+ = 45% of revenue", sort=ASC(col("Spend_Band")))
p.add("clusteredColumnChart", 432, 464, 408, 248, {"Category": [col("Year")], "Y": [mea("H1 Revenue")]},
      "January-June revenue by year (like-for-like)", sort=ASC(col("Year")), objects=money_axis(precision=1))
p.add("clusteredColumnChart", 848, 464, 416, 248, {"Category": [col("Month")], "Y": [mea("Purchases per 30 Days")]},
      "Purchases per 30 days of data, by calendar month", sort=ASC(col("Month")), objects={"labels_extra": {"labelPrecision": lit("0L")}})
pages.append(p)

# 2 Customers & categories
p = Page("Customers & Categories", "Who buys, and what do they buy?")
slicer_row(p)
p.add("clusteredColumnChart", 16, 112, 408, 300, {"Category": [col("Age_Group")], "Y": [mea("Customers with Age")]},
      "Customers by age group (only the 495 with a real age)", sort=ASC(col("Age_Group")))
p.add("clusteredBarChart", 432, 112, 408, 300, {"Category": [col("Gender")], "Y": [mea("Customers")]},
      "Customers by gender", sort=ASC(col("Gender")), objects={"dataPoint": UNKNOWN_GRAY("Gender")})
p.add("clusteredBarChart", 848, 112, 416, 300, {"Category": [col("Product_Category")], "Y": [mea("AOV")]},
      "Average order value by category - all within $500-537", sort=ASC(col("Product_Category")),
      objects={"dataPoint": UNKNOWN_GRAY("Product_Category")})
p.add("tableEx", 16, 420, 832, 292, {"Values": [col("Product_Category"), mea("Customers"), mea("Revenue"), mea("Revenue Share"), mea("AOV"),
                                                mea("Avg Rating"), mea("Satisfied %"), mea("Dissatisfied %")]},
      "Category scorecard", sort=DESC(mea("Revenue")))
p.add("clusteredColumnChart", 856, 420, 408, 292, {"Category": [col("Weekday")], "Y": [mea("Dated Purchases")]},
      "Purchases by weekday (invalid dates excluded)", sort=ASC(col("Weekday")))
pages.append(p)

# 3 Ratings
p = Page("Ratings", "Customer satisfaction: as many unhappy as happy customers, in every segment")
slicer_row(p)
p.add("clusteredColumnChart", 16, 112, 408, 300, {"Category": [col("Stars")], "Y": [mea("Rating Share")]},
      "Rating distribution (valid 1-5 ratings)", sort=ASC(col("Stars")),
      objects={"dataPoint": series_colors(col("Stars"), STAR_COLORS)})
p.add("hundredPercentStackedBarChart", 432, 112, 832, 300,
      {"Category": [col("Product_Category")], "Series": [col("Rating_Band")], "Y": [mea("Rated")]},
      "Rating mix by category", sort=ASC(col("Product_Category")), objects=stacked_rating())
p.add("hundredPercentStackedBarChart", 16, 420, 624, 292,
      {"Category": [col("Age_Group")], "Series": [col("Rating_Band")], "Y": [mea("Rated")]},
      "Rating mix by age group", sort=ASC(col("Age_Group")), objects=stacked_rating())
p.add("hundredPercentStackedBarChart", 648, 420, 616, 292,
      {"Category": [col("Spend_Band")], "Series": [col("Rating_Band")], "Y": [mea("Rated")]},
      "Rating mix by order size", sort=ASC(col("Spend_Band")), objects=stacked_rating())
pages.append(p)

# 4 Data quality
p = Page("Data Quality", f"Data quality: only {K['complete_record_rate']:.1%} of records are complete")
p.add("hundredPercentStackedBarChart", 16, 56, 832, 400,
      {"Category": [col("Field")], "Series": [col("Status")], "Y": [mea("Quality Rows")]},
      "Usable, blank and invalid values per field (all 2,100 customers)",
      sort=ASC(col("Field")), objects={"dataPoint": series_colors(col("Status"), QUALITY_COLORS), "labels_extra": STACK_LABELS})
p.add("clusteredBarChart", 16, 464, 412, 248, {"Category": [col("Age_Status")], "Y": [mea("Customers")]},
      "Age values as recorded: only 495 real ages", sort=DESC(mea("Customers")))
p.add("clusteredBarChart", 436, 464, 412, 248, {"Category": [col("Rating_Status")], "Y": [mea("Customers")]},
      "Rating values as recorded ('10' is out of range)", sort=DESC(mea("Customers")))
for i, (m, label) in enumerate([("Complete Records %", "Complete records"), ("Usable Age %", "Usable ages"),
                                ("Unassigned Revenue %", "Revenue with no category"), ("Valid Ratings", "Valid ratings")]):
    p.add_card(856 + (i % 2) * 208, 56 + (i // 2) * 100, 200, 92, m, label)
qlog = S["quality_detail"]
p.add_text("\n".join([
    "# Cleaning decisions",
    "- 50 exact duplicate rows removed (all appended at the end of the file); the padded '  Gender  ' copy and the empty 'Unnamed' column dropped.",
    f"- Age: {qlog['Age']['Invalid']} placeholders (-1 / 200) and {qlog['Age']['Blank']} blanks set to missing, NOT imputed (76% unusable).",
    f"- Rating: {qlog['Rating']['Invalid']} values of '10' on a 1-5 scale set to missing (no 6-9 exist, so it is not a 10-point scale).",
    f"- Date: {qlog['Purchase date']['Invalid']} impossible dates '32/13/2020' set to missing; rows kept for non-time analysis.",
    "- Gender: 6 spellings (M, male, Male, F, female, Female) merged; blanks = 'Unknown'. Gender contradicts the first name in 50% of rows.",
    "- Category blanks = 'Unknown' (27%); amounts left blank (5%), not estimated; phone dropped (only 2 dummy numbers).",
]), 856, 256, 408, 456, size="10.5pt")
pages.append(p)

# 5 Insights
t = S["tests"]
h1 = S["h1"]
INSIGHTS = "\n".join([
    "# Key findings",
    f"- Data quality is the biggest finding: only {K['complete_record_rate']:.1%} of records are valid in every field; age is usable for 24% of customers and no phone number is real.",
    f"- Big tickets carry the revenue: $750+ orders are {K['big_ticket_order_share']:.0%} of orders but {K['big_ticket_revenue_share']:.0%} of the ${K['revenue'] / 1e6:.2f}M revenue (average order ${K['aov']:.0f}).",
    f"- Satisfaction is split: average {K['avg_rating']:.2f} / 5, with {K['dissatisfied_share']:.0%} dissatisfied (1-2) and {K['satisfied_share']:.0%} satisfied (4-5), the same in every segment.",
    f"- Sales are flat: about {K['purchases_per_full_month']:.0f} purchases and ${K['revenue_per_full_month'] / 1000:.0f}K a month, no trend (p = {t['Monthly purchases trend (linear regression, full months)']:.2f}); "
    f"Jan-Jun revenue {h1[1]['revenue'] / h1[0]['revenue'] - 1:+.1%} in 2024 and {h1[2]['revenue'] / h1[1]['revenue'] - 1:+.1%} in 2025.",
    f"- No seasonality: Aug-Sep only look low because they occur in 2 of the years covered; per 30 days all months are alike (p = {t['Month-of-year purchases vs calendar coverage (chi-square)']:.2f}).",
    f"- No segment stands out: gender, age, category, weekday and email provider show no significant difference in order value or rating (all p >= 0.09).",
    f"- {K['unknown_category_revenue_share']:.0%} of revenue (${K['unknown_category_revenue'] / 1000:.0f}K) has no product category.",
    "",
    "# Recommendations",
    "1. Fix data capture: date of birth instead of age, drop-downs for gender / category / rating, validated dates and phones, no duplicate IDs (target: 90%+ complete records).",
    "2. Back-fill the 565 uncategorised purchases from the order system.",
    "3. Add a reason code to every rating and follow up 1-2 star customers within 48 hours (targets: rating 3.5, dissatisfied below 25%).",
    "4. Protect $750+ orders (45% of revenue) and A/B-test upgrades for $250-749 orders; use experiments, not demographic targeting.",
    "5. Use one customer ID across orders so repeat rate and lifetime value can be measured; track purchases against the ~60 / month baseline.",
    "",
    "Note: the file behaves like randomly generated data (uniform amounts and ages, equally likely ratings, gender unrelated to name), so flat results are expected.",
])
p = Page("Insights", "Insights and recommendations")
p.add_text(INSIGHTS, 16, 56, 1248, 640, size="14pt")
pages.append(p)


# ------------------------------------------------------------------ write files
def dump(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, ensure_ascii=False, indent=2)


def main():
    if os.path.exists(OUT):
        shutil.rmtree(OUT)
    sm_dir, rp_dir = os.path.join(OUT, f"{NAME}.SemanticModel"), os.path.join(OUT, f"{NAME}.Report")
    dump(os.path.join(OUT, f"{NAME}.pbip"), {"version": "1.0", "artifacts": [{"report": {"path": f"{NAME}.Report"}}],
                                             "settings": {"enableAutoRecovery": True}})
    dump(os.path.join(sm_dir, "definition.pbism"), {"version": "1.0", "settings": {}})
    dump(os.path.join(sm_dir, "model.bim"), model)
    dump(os.path.join(rp_dir, "definition.pbir"), {"version": "4.0", "datasetReference": {"byPath": {"path": f"../{NAME}.SemanticModel"}}})
    d = os.path.join(rp_dir, "definition")
    dump(os.path.join(d, "version.json"), {"$schema": f"{SCHEMA}/versionMetadata/1.0.0/schema.json", "version": "2.0.0"})

    with zipfile.ZipFile(THEME_SRC) as z:
        base = z.read(f"Report/StaticResources/SharedResources/BaseThemes/{BASE_THEME}.json")
    os.makedirs(os.path.join(rp_dir, "StaticResources", "SharedResources", "BaseThemes"), exist_ok=True)
    with open(os.path.join(rp_dir, "StaticResources", "SharedResources", "BaseThemes", f"{BASE_THEME}.json"), "wb") as fh:
        fh.write(base)
    dump(os.path.join(rp_dir, "StaticResources", "RegisteredResources", "CustomerTheme.json"),
         {"name": "Customer", "dataColors": ["#2A78D6", "#EB6834", "#1BAF7A", "#EDA100", "#E87BA4", "#008300", "#4A3AA7", "#E34948"],
          "foreground": "#0B0B0B", "background": "#FFFFFF", "tableAccent": "#2A78D6"})
    dump(os.path.join(d, "report.json"), {
        "$schema": f"{SCHEMA}/report/3.3.0/schema.json",
        "themeCollection": {
            "baseTheme": {"name": BASE_THEME, "reportVersionAtImport": {"visual": "2.13.0", "report": "3.4.0", "page": "2.3.1"}, "type": "SharedResources"},
            "customTheme": {"name": "CustomerTheme.json", "reportVersionAtImport": {"visual": "2.13.0", "report": "3.4.0", "page": "2.3.1"},
                            "type": "RegisteredResources"}},
        "resourcePackages": [
            {"name": "SharedResources", "type": "SharedResources", "items": [{"name": BASE_THEME, "path": f"BaseThemes/{BASE_THEME}.json", "type": "BaseTheme"}]},
            {"name": "RegisteredResources", "type": "RegisteredResources", "items": [{"name": "CustomerTheme.json", "path": "CustomerTheme.json", "type": "CustomTheme"}]}],
        "settings": {"useStylableVisualContainerHeader": True, "exportDataMode": "AllowSummarized", "defaultDrillFilterOtherVisuals": True,
                     "allowChangeFilterTypes": True, "useEnhancedTooltips": True, "useDefaultAggregateDisplayName": True}})
    dump(os.path.join(d, "pages", "pages.json"), {"$schema": f"{SCHEMA}/pagesMetadata/1.1.0/schema.json",
                                                  "pageOrder": [pg.name for pg in pages], "activePageName": pages[0].name})
    for pg in pages:
        dump(os.path.join(d, "pages", pg.name, "page.json"), {"$schema": f"{SCHEMA}/page/2.1.0/schema.json", "name": pg.name,
                                                               "displayName": pg.title, "displayOption": "FitToPage", "height": 720, "width": 1280})
        for v in pg.visuals:
            dump(os.path.join(d, "pages", pg.name, "visuals", v["name"], "visual.json"), v)
    n = sum(len(pg.visuals) for pg in pages)
    print(f"Wrote {OUT}: {len(pages)} pages, {n} visuals, {len(MEASURES)} measures, {len(columns)} columns")


if __name__ == "__main__":
    main()
