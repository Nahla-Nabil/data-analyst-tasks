"""
Step 3: builds the Power BI project (PBIP) for the movie dashboard.

Reads  movies_clean.csv, movie_genres.csv (and analysis.summary() for the Insights page)
Writes PowerBI/Movie_Dashboard.pbip
       PowerBI/Movie_Dashboard.SemanticModel/   model.bim: Movies and Genres tables (Power Query), a 'Vote Threshold' table,
                                                the Genres -> Movies relationship and every DAX measure
       PowerBI/Movie_Dashboard.Report/          PBIR report: 7 pages, synced slicers, KPI cards, charts, Top N tables

Open the .pbip in Power BI Desktop, press Refresh (the project stores no data), then File > Save as > .pbix.
The CSV paths are written into Power Query as absolute paths - rerun this script if the folder moves.
Same pattern as Task 9/build_powerbi.py.
"""

import json
import os
import shutil
import uuid
import zipfile

import pandas as pd

from analysis import summary

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "PowerBI")
NAME = "Movie_Dashboard"
T = "Movies"
THEME_SRC = os.path.join(HERE, "..", "Task 3", "HR_Attrition_Model_Nahla.pbix")   # source of the base theme file
BASE_THEME = "Fluent2-CY26SU09"
TIER_ORDER = ["Under $10M", "$10M-40M", "$40M-100M", "$100M+", "Unknown"]
RUNTIME_ORDER = ["Under 90 min", "90-109 min", "110-129 min", "130-149 min", "150+ min", "Unknown"]
VOTE_ORDER = ["Under 50", "50-499", "500-1,999", "2,000-4,999", "5,000+"]
THRESHOLDS = [100, 500, 1000, 2000, 5000]

# ------------------------------------------------------------------ semantic model: Movies table
movies_csv = os.path.join(HERE, "movies_clean.csv")
genres_csv = os.path.join(HERE, "movie_genres.csv")
df = pd.read_csv(movies_csv, keep_default_na=False, dtype=str)
INTS = ["Movie_ID", "Release_Year", "Month_Num", "Genre_Count", "Runtime", "Vote_Count"]
DOUBLES = ["Budget", "Revenue", "Profit", "ROI", "Rating", "Popularity"]
TYPES = {}
for c in df.columns:
    if c == "Release_Date":
        TYPES[c] = ("dateTime", "type date")
    elif c in DOUBLES:
        TYPES[c] = ("double", "type number")
    elif c in INTS:
        TYPES[c] = ("int64", "Int64.Type")
    else:
        TYPES[c] = ("string", "type text")
BLANKABLE = [c for c in df.columns if (df[c] == "").any()]


def order_col(step, prev, name, column, order):
    items = ", ".join(f'"{v}"' for v in order)
    return f'    {step} = Table.AddColumn({prev}, "{name}", each List.PositionOf({{{items}}}, [{column}]) + 1, Int64.Type),'


M = [
    "let",
    f'    Source = Csv.Document(File.Contents("{movies_csv}"), [Delimiter = ",", Columns = {len(df.columns)}, Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),',
    "    Promoted = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),",
    f'    Blanks = Table.ReplaceValue(Promoted, "", null, Replacer.ReplaceValue, {{{", ".join(chr(34) + c + chr(34) for c in BLANKABLE)}}}),',
    f'    Typed = Table.TransformColumnTypes(Blanks, {{{", ".join(f"{{{chr(34)}{c}{chr(34)}, {mt}}}" for c, (_, mt) in TYPES.items())}}}, "en-US"),',
    # sort helpers are built here, not as DAX columns (a DAX sort column derived from its own target is circular)
    order_col("TierSort", "Typed", "TierSort", "Budget_Tier", TIER_ORDER),
    order_col("RuntimeSort", "TierSort", "RuntimeSort", "Runtime_Band", RUNTIME_ORDER),
    order_col("VoteSort", "RuntimeSort", "VoteSort", "Vote_Band", VOTE_ORDER),
    '    RatingBin = Table.AddColumn(VoteSort, "Rating_Bin", each if [Rating] = null then null else Number.RoundDown([Rating]), Int64.Type)',
    "in",
    "    RatingBin",
]

FMT = {"Budget": "\\$#,0", "Revenue": "\\$#,0", "Profit": "\\$#,0", "ROI": '0.00"x"', "Rating": "0.0", "Release_Date": "yyyy-mm-dd",
       "Release_Year": "0", "Runtime": "0", "Vote_Count": "#,0", "Movie_ID": "0"}
SORT_BY = {"Budget_Tier": "TierSort", "Runtime_Band": "RuntimeSort", "Vote_Band": "VoteSort", "Release_Month": "Month_Num"}
columns = []
for c, (dt, _) in TYPES.items():
    col_ = {"name": c, "dataType": dt, "sourceColumn": c, "summarizeBy": "none"}
    if c in FMT:
        col_["formatString"] = FMT[c]
    if c in SORT_BY:
        col_["sortByColumn"] = SORT_BY[c]
    columns.append(col_)
for c in ["TierSort", "RuntimeSort", "VoteSort"]:
    columns.append({"name": c, "dataType": "int64", "sourceColumn": c, "summarizeBy": "none", "isHidden": True})
columns.append({"name": "Rating_Bin", "dataType": "int64", "sourceColumn": "Rating_Bin", "summarizeBy": "none", "formatString": "0"})

M_GENRES = [
    "let",
    f'    Source = Csv.Document(File.Contents("{genres_csv}"), [Delimiter = ",", Columns = 2, Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),',
    "    Promoted = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),",
    '    Typed = Table.TransformColumnTypes(Promoted, {{"Movie_ID", Int64.Type}, {"Genre", type text}}, "en-US")',
    "in",
    "    Typed",
]
rows = ", ".join(f'{{{v}, "{v:,}+ votes"}}' for v in THRESHOLDS)
M_VOTES = ["let", f"    Source = #table(type table [Min_Votes = Int64.Type, Threshold = text], {{{rows}}})", "in", "    Source"]


# ------------------------------------------------------------------ measures
def pearson(x, y, extra=""):
    return "\n".join([
        f"VAR t = FILTER ( Movies, NOT ISBLANK ( Movies[{x}] ) && NOT ISBLANK ( Movies[{y}] ){extra} )",
        f"VAR mx = AVERAGEX ( t, Movies[{x}] )",
        f"VAR my = AVERAGEX ( t, Movies[{y}] )",
        f"VAR sxy = SUMX ( t, ( Movies[{x}] - mx ) * ( Movies[{y}] - my ) )",
        f"VAR sxx = SUMX ( t, ( Movies[{x}] - mx ) ^ 2 )",
        f"VAR syy = SUMX ( t, ( Movies[{y}] - my ) ^ 2 )",
        "RETURN DIVIDE ( sxy, SQRT ( sxx * syy ) )"])


RELIABLE = '&& Movies[Rating_Reliable] = "Yes"'
WEIGHTED = "\n".join([
    "VAR m = [Min Votes]",
    'VAR c = CALCULATE ( AVERAGE ( Movies[Rating] ), REMOVEFILTERS ( Movies ), REMOVEFILTERS ( Genres ), Movies[Rating_Reliable] = "Yes" )',
    "VAR v = SUM ( Movies[Vote_Count] )",
    "VAR r = AVERAGE ( Movies[Rating] )",
    "RETURN IF ( HASONEVALUE ( Movies[Title_Year] ) && v >= m, DIVIDE ( v * r + m * c, v + m ) )"])

MEASURES = [
    ("Movies", "COUNTROWS ( Movies )", "#,0", "Released movies in the current selection"),
    ("Total Revenue", "SUM ( Movies[Revenue] )", "\\$#,0", "Box-office revenue (only movies with a known revenue)"),
    ("Total Budget", "SUM ( Movies[Budget] )", "\\$#,0", "Production budget (only movies with a known budget)"),
    ("Total Profit", "SUM ( Movies[Profit] )", "\\$#,0", "Revenue minus budget, for movies with both known"),
    ("Avg Budget", "AVERAGE ( Movies[Budget] )", "\\$#,0", "Average budget of movies with a known budget"),
    ("Avg Revenue", "AVERAGE ( Movies[Revenue] )", "\\$#,0", "Average revenue of movies with a known revenue"),
    ("Median Revenue", "MEDIAN ( Movies[Revenue] )", "\\$#,0", "Median revenue (less affected by blockbusters than the average)"),
    ("Median Budget", "MEDIAN ( Movies[Budget] )", "\\$#,0", "Median budget"),
    ("Movies with Financials", 'CALCULATE ( [Movies], KEEPFILTERS ( Movies[Financials_Known] = "Yes" ) )', "#,0",
     "Movies with both budget and revenue known"),
    ("Median ROI", "MEDIAN ( Movies[ROI] )", '0.00"x"', "Median revenue / budget (2.0x = revenue is twice the budget)"),
    ("Profitable %", "DIVIDE ( CALCULATE ( [Movies], KEEPFILTERS ( Movies[Profit] > 0 ) ), [Movies with Financials] )", "0%",
     "Share of movies whose revenue is higher than their budget"),
    ("Avg Rating", 'CALCULATE ( AVERAGE ( Movies[Rating] ), KEEPFILTERS ( Movies[Rating_Reliable] = "Yes" ) )', "0.00",
     "Average TMDB rating (0-10) of movies with 50+ votes"),
    ("Rated Movies", 'CALCULATE ( [Movies], KEEPFILTERS ( Movies[Rating_Reliable] = "Yes" ) )', "#,0", "Movies with 50+ votes"),
    ("Votes", "SUM ( Movies[Vote_Count] )", "#,0", "Number of TMDB votes"),
    ("Raw Rating", "AVERAGE ( Movies[Rating] )", "0.0", "Rating with no vote threshold"),
    ("Avg Runtime", "AVERAGE ( Movies[Runtime] )", '0" min"', "Average runtime in minutes"),
    ("Median Runtime", "MEDIAN ( Movies[Runtime] )", '0" min"', "Median runtime in minutes"),
    ("Revenue $bn", "DIVIDE ( [Total Revenue], 1e9 )", '\\$#,0.0"bn"', "Revenue in billions (for tables)"),
    ("Avg Rating 10+", "IF ( [Rated Movies] >= 10, [Avg Rating] )", "0.00", "Average rating, blank when fewer than 10 rated movies (years before ~1960)"),
    ("Median Revenue 10+", "IF ( [Movies] >= 10, [Median Revenue] )", "\\$#,0", "Median revenue, blank when fewer than 10 movies"),
    ("Avg Runtime 10+", "IF ( [Movies] >= 10, [Avg Runtime] )", '0" min"', "Average runtime, blank when fewer than 10 movies"),
    ("Min Votes", "SELECTEDVALUE ( 'Vote Threshold'[Min_Votes], 1000 )", "#,0", "Vote threshold picked in the slicer (default 1,000)"),
    ("Weighted Rating", WEIGHTED, "0.00",
     "IMDb-style score v/(v+m)*R + m/(v+m)*C: pulls ratings with few votes towards the average C; only movies with at least m votes"),
    ("WR Rating", "IF ( NOT ISBLANK ( [Weighted Rating] ), AVERAGE ( Movies[Rating] ) )", "0.0", "Rating, shown only for movies in the weighted ranking"),
    ("WR Votes", "IF ( NOT ISBLANK ( [Weighted Rating] ), [Votes] )", "#,0", "Votes, shown only for movies in the weighted ranking"),
    ("r Budget-Revenue", pearson("Budget", "Revenue"), "0.00", "Pearson correlation between budget and revenue"),
    ("r Runtime-Rating", pearson("Runtime", "Rating", " " + RELIABLE), "0.00", "Pearson correlation between runtime and rating (50+ votes)"),
    ("r Runtime-Revenue", pearson("Runtime", "Revenue"), "0.00", "Pearson correlation between runtime and revenue"),
]


def lineage():
    return str(uuid.uuid4())


def m_table(name, cols, expr, measures=None):
    t = {"name": name, "lineageTag": lineage(), "columns": cols,
         "partitions": [{"name": name, "mode": "import", "source": {"type": "m", "expression": expr}}]}
    if measures:
        t["measures"] = measures
    return t


model = {
    "compatibilityLevel": 1567,
    "model": {
        "culture": "en-US",
        "dataAccessOptions": {"legacyRedirects": True, "returnErrorValuesAsNull": True},
        "defaultPowerBIDataSourceVersion": "powerBI_V3",
        "sourceQueryCulture": "en-US",
        "tables": [
            m_table(T, columns, M, [{"name": n, "expression": e.split("\n") if "\n" in e else e, "formatString": f, "description": d,
                                     "lineageTag": lineage()} for n, e, f, d in MEASURES]),
            m_table("Genres", [{"name": "Movie_ID", "dataType": "int64", "sourceColumn": "Movie_ID", "summarizeBy": "none", "isHidden": True},
                               {"name": "Genre", "dataType": "string", "sourceColumn": "Genre", "summarizeBy": "none"}], M_GENRES),
            m_table("Vote Threshold", [{"name": "Min_Votes", "dataType": "int64", "sourceColumn": "Min_Votes", "summarizeBy": "none", "isHidden": True},
                                       {"name": "Threshold", "dataType": "string", "sourceColumn": "Threshold", "summarizeBy": "none",
                                        "sortByColumn": "Min_Votes"}], M_VOTES),
        ],
        # a movie has several genres, so the genre slicer filters Movies through the bridge table (both directions)
        "relationships": [{"name": lineage(), "fromTable": "Genres", "fromColumn": "Movie_ID", "toTable": T, "toColumn": "Movie_ID",
                           "crossFilteringBehavior": "bothDirections"}],
        "annotations": [{"name": "PBI_QueryOrder", "value": json.dumps([T, "Genres", "Vote Threshold"])},
                        {"name": "__PBI_TimeIntelligenceEnabled", "value": "0"},
                        {"name": "PBIDesktopVersion", "value": "2.157.1354.0"}],
    },
}

# ------------------------------------------------------------------ report (PBIR)
SCHEMA = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition"
lit = lambda v: {"expr": {"Literal": {"Value": v}}}
TRUE, FALSE = lit("true"), lit("false")
ENTITY_OF = {"Genre": "Genres", "Threshold": "Vote Threshold"}


def col(p, entity=None):
    return {"Column": {"Expression": {"SourceRef": {"Entity": entity or ENTITY_OF.get(p, T)}}, "Property": p}}


def mea(p):
    return {"Measure": {"Expression": {"SourceRef": {"Entity": T}}, "Property": p}}


DISPLAY = {"Title_Year": "Movie", "Release_Year": "Year", "Release_Month": "Month", "Budget_Tier": "Budget tier", "Runtime_Band": "Runtime",
           "Vote_Band": "Votes", "Rating_Bin": "Rating (6 = 6.0-6.9)", "Total Revenue": "Revenue", "Total Budget": "Budget",
           "Avg Rating": "Avg rating", "Median Revenue": "Median revenue", "Revenue $bn": "Revenue", "Avg Rating 10+": "Avg rating", "Median Revenue 10+": "Median revenue", "Avg Runtime 10+": "Avg runtime", "Median Budget": "Median budget", "Median ROI": "ROI (median)",
           "Profitable %": "Profitable", "Rated Movies": "Rated movies", "Weighted Rating": "Weighted rating", "WR Rating": "Rating",
           "WR Votes": "Votes", "Raw Rating": "Rating", "Avg Runtime": "Avg runtime", "Primary_Genre": "Main genre", "Lead_Actor": "Lead actor"}


def proj(field):
    kind = "Column" if "Column" in field else "Measure"
    ent = field[kind]["Expression"]["SourceRef"]["Entity"]
    prop = field[kind]["Property"]
    p = {"field": field, "queryRef": f"{ent}.{prop}", "nativeQueryRef": prop}
    if prop in DISPLAY:
        p["displayName"] = DISPLAY[prop]
    return p


def top_n(column, measure, n):
    """Visual-level Top N filter, the same one the Filters pane creates (Show items: Top n by measure)."""
    src = lambda: {"SourceRef": {"Source": "m"}}
    return {"filters": [{
        "name": vid(), "field": col(column), "type": "TopN",
        "filter": {"Version": 2,
                   "From": [{"Name": "subquery", "Type": 2, "Expression": {"Subquery": {"Query": {
                       "Version": 2, "From": [{"Name": "m", "Entity": T, "Type": 0}],
                       "Select": [{"Column": {"Expression": src(), "Property": column}, "Name": "field"}],
                       "OrderBy": [{"Direction": 2, "Expression": {"Measure": {"Expression": src(), "Property": measure}}}],
                       "Top": n}}}},
                       {"Name": "m", "Entity": T, "Type": 0}],
                   "Where": [{"Condition": {"In": {"Expressions": [{"Column": {"Expression": src(), "Property": column}}],
                                                   "Table": {"SourceRef": {"Source": "subquery"}}}}}]}}]}


def exclude(column, value):
    """Visual-level filter that hides one category (e.g. the 'Unknown' runtime band)."""
    ref = {"Column": {"Expression": {"SourceRef": {"Source": "m"}}, "Property": column}}
    return {"filters": [{
        "name": vid(), "field": col(column), "type": "Categorical",
        "filter": {"Version": 2, "From": [{"Name": "m", "Entity": T, "Type": 0}],
                   "Where": [{"Condition": {"Not": {"Expression": {"In": {"Expressions": [ref],
                                                                          "Values": [[{"Literal": {"Value": f"'{value}'"}}]]}}}}}]}}]}


def units(u, precision=0, axis="valueAxis"):
    """Display units for data labels and the value axis, e.g. 1e6 -> $370M instead of $370,555,515."""
    return {axis: [{"properties": {"labelDisplayUnits": lit(f"{u}D")}}],
            "labels_extra": {"labelDisplayUnits": lit(f"{u}D"), "labelPrecision": lit(f"{precision}L")}}


def vid():
    return uuid.uuid4().hex[:20]


class Page:
    def __init__(self, name, title):
        self.name, self.title, self.visuals, self.z = vid(), name, [], 0
        self.add_text(title, 16, 8, 1248, 36, size="18pt", bold=True)

    def _container(self, x, y, w, h, visual, filters=None):
        self.z += 1000
        c = {"$schema": f"{SCHEMA}/visualContainer/2.12.0/schema.json", "name": vid(),
             "position": {"x": x, "y": y, "z": self.z, "height": h, "width": w, "tabOrder": self.z}, "visual": visual}
        if filters:
            c["filterConfig"] = filters
        self.visuals.append(c)

    def add(self, vtype, x, y, w, h, roles, title=None, sort=None, labels=True, objects=None, extra=None, title_size=None, filters=None):
        qs = {role: {"projections": [proj(f) for f in fields]} for role, fields in roles.items()}
        query = {"queryState": qs}
        if sort:
            field, direction = sort
            query["sortDefinition"] = {"sort": [{"field": field, "direction": direction}]}
        objs = dict(objects or {})
        extra_labels = objs.pop("labels_extra", {})
        if labels and vtype not in ("card", "tableEx", "slicer", "scatterChart", "lineChart"):
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
        self._container(x, y, w, h, visual, filters)

    def add_card(self, x, y, w, h, measure, label, units_=None, precision=None):
        props = {"fontSize": lit("20D"), "color": {"solid": {"color": lit("'#1F3A5F'")}}}
        if units_:
            props["labelDisplayUnits"] = lit(f"{units_}D")
        if precision is not None:
            props["labelPrecision"] = lit(f"{precision}L")
        self.add("card", x, y, w, h, {"Values": [mea(measure)]}, title=label, labels=False, title_size=10,
                 objects={"categoryLabels": [{"properties": {"show": FALSE}}], "labels": [{"properties": props}]})

    def add_slicer(self, x, y, w, h, column, title, mode="Dropdown", sync=True, single=False):
        objects = {"data": [{"properties": {"mode": lit(f"'{mode}'")}}], "header": [{"properties": {"show": FALSE}}]}
        if single:
            objects["selection"] = [{"properties": {"singleSelect": TRUE}}]
        extra = {"syncGroup": {"groupName": column, "fieldChanges": True, "filterChanges": True}} if sync else None
        self.add("slicer", x, y, w, h, {"Values": [col(column)]}, title=title, labels=False, title_size=9, objects=objects, extra=extra)

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


SLICERS = [("Release_Year", "Release year", "Between"), ("Genre", "Genre", "Dropdown"), ("Budget_Tier", "Budget tier", "Dropdown"),
           ("Runtime_Band", "Runtime", "Dropdown"), ("Language", "Original language", "Dropdown")]


def slicer_row(p):
    w = 1248 // len(SLICERS)
    for i, (c, t, mode) in enumerate(SLICERS):
        p.add_slicer(16 + i * w, 44, w - 8, 64, c, t, mode)


DESC = lambda f: (f, "Descending")
ASC = lambda f: (f, "Ascending")
NO_TOTALS = {"total": [{"properties": {"totals": FALSE}}]}
LEGEND_TOP = {"legend": [{"properties": {"show": TRUE, "position": lit("'Top'")}}]}
S = summary()
K, R = S["kpi"], S["r"]
pages = []

# 1 Overview
p = Page("Overview", f"Movie Analytics - {K['movies']:,} movies released {K['first_year']}-{K['last_year']} (TMDB 5000)")
slicer_row(p)
CARDS = [("Movies", "Movies", None, None), ("Total Revenue", "Box-office revenue", 1000000000, 1), ("Avg Budget", "Avg budget", 1000000, 1),
         ("Median ROI", "Median ROI", None, None), ("Profitable %", "Earned > budget", None, None), ("Avg Rating", "Avg rating (0-10)", None, None),
         ("Avg Runtime", "Avg runtime", None, None), ("Votes", "TMDB votes", 1000000, 1)]
for i, (m, label, u, prec) in enumerate(CARDS):
    p.add_card(16 + i * 156, 112, 148, 84, m, label, u, prec)
p.add("lineChart", 16, 204, 800, 250, {"Category": [col("Release_Year")], "Y": [mea("Movies")]},
      "Movies released per year - 73% of the list is from 2000 on (2016-17 only partly collected)", sort=ASC(col("Release_Year")))
p.add("clusteredBarChart", 824, 204, 440, 508, {"Category": [col("Genre")], "Y": [mea("Movies")]},
      "Movies by genre (a movie counts in each of its genres)", sort=DESC(mea("Movies")))
p.add("clusteredColumnChart", 16, 462, 400, 250, {"Category": [col("Release_Month")], "Y": [mea("Median Revenue")]},
      "Median revenue by release month - June, July, December lead", sort=ASC(col("Release_Month")), labels=False,
      objects={"valueAxis": [{"properties": {"labelDisplayUnits": lit("1000000D")}}]})
p.add("clusteredBarChart", 424, 462, 392, 250, {"Category": [col("Director")], "Y": [mea("Total Revenue")]},
      "Top 6 directors by total box office", sort=DESC(mea("Total Revenue")), objects=units(1000000000, 1),
      filters=top_n("Director", "Total Revenue", 6))
pages.append(p)

# 2 Genres
p = Page("Genres", "Genres: War and History rate best, Animation earns most per movie, Horror rates lowest")
slicer_row(p)
p.add("clusteredBarChart", 16, 112, 360, 600, {"Category": [col("Genre")], "Y": [mea("Avg Rating")]},
      "Average rating by genre (movies with 50+ votes)", sort=DESC(mea("Avg Rating")), objects={"labels_extra": {"labelPrecision": lit("2L")}})
p.add("clusteredBarChart", 384, 112, 360, 600, {"Category": [col("Genre")], "Y": [mea("Median Revenue")]},
      "Median revenue per movie by genre", sort=DESC(mea("Median Revenue")), objects=units(1000000))
p.add("tableEx", 752, 112, 512, 600, {"Values": [col("Genre"), mea("Movies"), mea("Avg Rating"), mea("Revenue $bn"), mea("Median ROI"),
                                                 mea("Profitable %")]},
      "Genre scorecard", sort=DESC(mea("Movies")), objects=NO_TOTALS)
pages.append(p)

# 3 Budget & revenue
t = S["tier"]
p = Page("Budget & Revenue", f"Bigger budgets earn more (r = {R['budget_revenue']:.2f}), but small films earn the best return per dollar")
slicer_row(p)
p.add("scatterChart", 16, 112, 624, 340, {"Category": [col("Title_Year")], "X": [mea("Total Budget")], "Y": [mea("Total Revenue")]},
      "Budget vs revenue - one dot per movie", objects={**units(1000000, axis="categoryAxis"),
                                                         "valueAxis": [{"properties": {"labelDisplayUnits": lit("1000000D")}}]})
p.add("clusteredBarChart", 648, 112, 616, 340, {"Category": [col("Title_Year")], "Y": [mea("Total Revenue")]},
      "Top 10 highest-grossing movies", sort=DESC(mea("Total Revenue")), objects=units(1000000000, 2),
      filters=top_n("Title_Year", "Total Revenue", 10))
p.add("clusteredColumnChart", 16, 460, 408, 252, {"Category": [col("Budget_Tier")], "Y": [mea("Median ROI")]},
      "Median return (revenue / budget) by budget tier", sort=ASC(col("Budget_Tier")), objects={"labels_extra": {"labelPrecision": lit("2L")}})
p.add("clusteredColumnChart", 432, 460, 408, 252, {"Category": [col("Budget_Tier")], "Y": [mea("Profitable %")]},
      "Share of movies that earned more than their budget", sort=ASC(col("Budget_Tier")))
for i, (m, label, u, prec) in enumerate([("r Budget-Revenue", "Budget-revenue correlation", None, None),
                                         ("Movies with Financials", "Movies with budget + revenue", None, None),
                                         ("Total Profit", "Total profit", 1000000000, 1), ("Median Budget", "Median budget", 1000000, 1)]):
    p.add_card(848 + (i % 2) * 212, 460 + (i // 2) * 130, 204, 122, m, label, u, prec)
pages.append(p)

# 4 Ratings
p = Page("Ratings", "Highest-rated movies: a fair top 10 needs a minimum number of votes")
slicer_row(p)
p.add_slicer(16, 112, 300, 64, "Threshold", "Minimum votes (default 1,000+)", sync=False, single=True)
p.add_text("Weighted rating = v/(v+m) x R + m/(v+m) x C\nv = votes, R = rating, m = minimum votes, C = average rating (6.31)",
           324, 112, 316, 64, size="9pt")
p.add("tableEx", 16, 184, 624, 528, {"Values": [col("Title_Year"), mea("WR Rating"), mea("WR Votes"), mea("Weighted Rating")]},
      "Top 10 highest-rated movies, weighted by vote count", sort=DESC(mea("Weighted Rating")), objects=NO_TOTALS,
      filters=top_n("Title_Year", "Weighted Rating", 10))
p.add("clusteredColumnChart", 648, 112, 616, 292, {"Category": [col("Rating_Bin")], "Y": [mea("Rated Movies")]},
      "Rating distribution (movies with 50+ votes) - most score 5 to 7", sort=ASC(col("Rating_Bin")))
p.add("clusteredColumnChart", 648, 412, 272, 300, {"Category": [col("Vote_Band")], "Y": [mea("Raw Rating")]},
      "Average rating by number of votes", sort=ASC(col("Vote_Band")), objects={"labels_extra": {"labelPrecision": lit("1L")}})
p.add("tableEx", 928, 412, 336, 300, {"Values": [col("Title_Year"), mea("Raw Rating"), mea("Votes")]},
      "Without a vote filter, the 'best' movies have 1-2 votes", sort=DESC(mea("Raw Rating")), objects=NO_TOTALS,
      filters=top_n("Title_Year", "Raw Rating", 5))
pages.append(p)

# 5 Trends
p = Page("Trends", "Over the years: revenue and budgets rise, average ratings fall (older films in the list are the classics)")
slicer_row(p)
p.add("lineChart", 16, 112, 624, 296, {"Category": [col("Release_Year")], "Y": [mea("Median Revenue 10+")]},
      "Median revenue per movie by year (years with 10+ movies, not inflation-adjusted)", sort=ASC(col("Release_Year")), objects=units(1000000))
p.add("lineChart", 648, 112, 616, 296, {"Category": [col("Release_Year")], "Y": [mea("Avg Rating 10+")]},
      "Average rating by year (years with 10+ rated movies)", sort=ASC(col("Release_Year")))
p.add("clusteredColumnChart", 16, 416, 624, 296, {"Category": [col("Decade")], "Y": [mea("Median Budget"), mea("Median Revenue")]},
      "Median budget and revenue by decade", sort=ASC(col("Decade")), labels=False,
      objects={"valueAxis": [{"properties": {"labelDisplayUnits": lit("1000000D")}}], **LEGEND_TOP})
p.add("clusteredColumnChart", 648, 416, 616, 296, {"Category": [col("Decade")], "Y": [mea("Avg Rating 10+")]},
      "Average rating by decade (decades with 10+ rated movies)", sort=ASC(col("Decade")), objects={"labels_extra": {"labelPrecision": lit("2L")}})
pages.append(p)

# 6 Runtime
p = Page("Runtime", f"Runtime: longer movies are rated higher (r = {R['runtime_rating']:.2f}); the link to revenue is weak (r = {R['runtime_revenue']:.2f})")
slicer_row(p)
p.add("scatterChart", 16, 112, 624, 300, {"Category": [col("Title_Year")], "X": [mea("Avg Runtime")], "Y": [mea("Avg Rating")]},
      "Runtime (minutes) vs rating - one dot per movie with 50+ votes")
p.add("clusteredColumnChart", 648, 112, 616, 300, {"Category": [col("Runtime_Band")], "Y": [mea("Avg Rating")]},
      "Average rating by runtime", sort=ASC(col("Runtime_Band")), objects={"labels_extra": {"labelPrecision": lit("2L")}})
p.add("clusteredColumnChart", 16, 420, 408, 292, {"Category": [col("Runtime_Band")], "Y": [mea("Median Revenue")]},
      "Median revenue by runtime", sort=ASC(col("Runtime_Band")), objects=units(1000000),
      filters=exclude("Runtime_Band", "Unknown"))
p.add("lineChart", 432, 420, 408, 292, {"Category": [col("Decade")], "Y": [mea("Avg Runtime 10+")]},
      "Average runtime by decade (decades with 10+ movies)", sort=ASC(col("Decade")))
for i, (m, label) in enumerate([("r Runtime-Rating", "Runtime-rating correlation"), ("r Runtime-Revenue", "Runtime-revenue correlation"),
                                ("Avg Runtime", "Avg runtime"), ("Median Runtime", "Median runtime")]):
    p.add_card(848 + (i % 2) * 212, 420 + (i // 2) * 150, 204, 142, m, label)
pages.append(p)

# 7 Insights
g, dec, rt, mon = S["genre"], S["decade"], S["runtime"], S["month"]
top_rev, top_rated = S["top_revenue"].iloc[0], S["top_rated"].iloc[0]
recent = S["top_revenue"]["Title_Year"].str[-5:-1].astype(int).between(2012, 2016).sum()
INSIGHTS = "\n".join([
    "# Key insights",
    f"- Volume: {K['movies']:,} released movies, {K['since_2000']:.0%} of them from 2000 onwards. Drama ({g.loc['Drama', 'movies']:,}) and Comedy "
    f"({g.loc['Comedy', 'movies']:,}) are the most common genres.",
    f"- Money: budget and revenue move together (r = {R['budget_revenue']:.2f}). Of the {K['with_financials']:,} movies with both known, "
    f"{K['profitable']:.0%} earned more than their budget and the median movie earned {K['median_roi']:.1f}x its budget.",
    f"- Risk vs return: $100M+ movies are the safest ({t.loc['$100M+', 'profitable']:.0%} profitable), but films under $10M have the best "
    f"median return ({t.loc['Under $10M', 'median_roi']:.1f}x, e.g. Paranormal Activity earned {S['top_roi'].iloc[0]['ROI']:,.0f}x its $15K budget).",
    f"- Biggest hits: {top_rev['Title_Year']} leads with ${top_rev['Revenue'] / 1e9:.2f}B; {recent} of the top 10 grossers came out in 2012-2016, "
    "and most are franchise action/adventure movies.",
    f"- Genres: War ({g.loc['War', 'avg_rating']:.2f}) and History ({g.loc['History', 'avg_rating']:.2f}) are rated highest "
    f"(Documentary is {g.loc['Documentary', 'avg_rating']:.2f} but only 36 have 50+ votes); Horror is rated lowest "
    f"({g.loc['Horror', 'avg_rating']:.2f}) but has one of the best returns ({g.loc['Horror', 'median_roi']:.1f}x, "
    f"{g.loc['Horror', 'profitable']:.0%} profitable). Animation has the highest median revenue (${g.loc['Animation', 'median_revenue'] / 1e6:.0f}M).",
    f"- Ratings need votes: the raw top ratings are 10/10 from 1-2 votes. With 1,000+ votes the top movie is {top_rated['Title_Year']} "
    f"(rating {top_rated['Rating']:.1f}, {top_rated['Vote_Count']:,} votes). Votes track revenue closely (rho = {R['votes_revenue']:.2f}); "
    f"rating barely does (rho = {R['rating_revenue']:.2f}).",
    f"- Over time: median revenue rose from ${dec.loc['1980s', 'median_revenue'] / 1e6:.0f}M (1980s) to ${dec.loc['2010s', 'median_revenue'] / 1e6:.0f}M "
    f"(2010s, not inflation-adjusted). Average rating fell from {dec.loc['1970s', 'avg_rating']:.2f} (1970s) to {dec.loc['2010s', 'avg_rating']:.2f}: "
    "older movies in the list are mostly the well-known classics.",
    f"- Runtime: 150+ minute movies average {rt.loc['150+ min', 'avg_rating']:.2f} vs {rt.loc['Under 90 min', 'avg_rating']:.2f} for movies under "
    f"90 minutes (r = {R['runtime_rating']:.2f}). Runtime only weakly relates to revenue (r = {R['runtime_revenue']:.2f}).",
    f"- Release timing: June (${mon['Jun'] / 1e6:.0f}M median), December and July releases earn the most; September the least (${mon['Sep'] / 1e6:.0f}M).",
    "",
    "# Data notes",
    "- Source: Kaggle TMDB 5000 (movies + credits joined on movie id). 9 unreleased or undated movies removed.",
    "- Budget/revenue of 0 or under $1,000 = unknown (not zero). Ratings count in averages only with 50+ votes. Money is in nominal US$.",
])
p = Page("Insights", "Insights and trends")
p.add_text(INSIGHTS, 16, 56, 1248, 656, size="13pt")
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
    dump(os.path.join(rp_dir, "StaticResources", "RegisteredResources", "MovieTheme.json"),
         {"name": "Movie", "dataColors": ["#2A78D6", "#EB6834", "#1BAF7A", "#EDA100", "#E87BA4", "#008300", "#4A3AA7", "#E34948"],
          "foreground": "#0B0B0B", "background": "#FFFFFF", "tableAccent": "#2A78D6"})
    dump(os.path.join(d, "report.json"), {
        "$schema": f"{SCHEMA}/report/3.3.0/schema.json",
        "themeCollection": {
            "baseTheme": {"name": BASE_THEME, "reportVersionAtImport": {"visual": "2.13.0", "report": "3.4.0", "page": "2.3.1"}, "type": "SharedResources"},
            "customTheme": {"name": "MovieTheme.json", "reportVersionAtImport": {"visual": "2.13.0", "report": "3.4.0", "page": "2.3.1"},
                            "type": "RegisteredResources"}},
        "resourcePackages": [
            {"name": "SharedResources", "type": "SharedResources", "items": [{"name": BASE_THEME, "path": f"BaseThemes/{BASE_THEME}.json", "type": "BaseTheme"}]},
            {"name": "RegisteredResources", "type": "RegisteredResources", "items": [{"name": "MovieTheme.json", "path": "MovieTheme.json", "type": "CustomTheme"}]}],
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
    print(f"Wrote {OUT}: {len(pages)} pages, {n} visuals, {len(MEASURES)} measures, {len(columns)} Movies columns")


if __name__ == "__main__":
    main()
