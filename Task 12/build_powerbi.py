"""Step 6: builds the Power BI project (PBIP) for the NYC Airbnb dashboard.

Run from the repo root:  python "Task 12/build_powerbi.py"
Writes Task 12/PowerBI/Airbnb_NYC_Dashboard.pbip (+ .SemanticModel with the
Listings table, sort columns and DAX measures, + .Report with 5 pages,
synced slicers and a candy theme).

Open the .pbip in Power BI Desktop, press Refresh (the project stores no data,
the CSV path is absolute - rerun this script if the folder moves), then
File > Save as > .pbix. Same pattern as Task 10/build_powerbi.py.
"""
import json
import os
import shutil
import uuid
import zipfile

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "PowerBI")
NAME = "Airbnb_NYC_Dashboard"
T = "Listings"
THEME_SRC = os.path.join(HERE, "..", "Task 3", "HR_Attrition_Model_Nahla.pbix")
BASE_THEME = "Fluent2-CY26SU09"

BOROUGH_ORDER = ["Manhattan", "Brooklyn", "Queens", "Bronx", "Staten Island"]
ROOM_ORDER = ["Entire home/apt", "Private room", "Shared room"]
BAND_ORDER = ["Budget (<$75)", "Mid ($75-150)", "Premium ($150-300)", "Luxury ($300+)"]
AVAIL_ORDER = ["Inactive (0 days)", "Low (1-90)", "Medium (91-180)", "High (181-364)", "Fully open (365)"]
STAY_ORDER = ["1 night", "2 nights", "3 nights", "4-7 nights", "8-29 nights",
              "30 nights (monthly)", "31+ nights"]
HOST_ORDER = ["Single (1)", "Small (2-5)", "Mid (6-20)", "Large (21+)"]

CSV = os.path.join(HERE, "Cleaned_AB_NYC_2019.csv")
df = pd.read_csv(CSV, keep_default_na=False, dtype=str)
N_FULL = len(pd.read_csv(CSV, nrows=0).columns)  # the M must read ALL file columns first ...
KEEP = ["id", "name", "host_id", "host_name", "neighbourhood_group", "neighbourhood",
        "latitude", "longitude", "room_type", "price", "price_capped", "minimum_nights",
        "stay_bin", "number_of_reviews", "last_review", "reviews_per_month",
        "calculated_host_listings_count", "availability_365", "price_band",
        "avail_segment", "host_size", "flag_never_reviewed", "flag_price_outlier",
        "flag_min_nights_extreme", "is_entire_home", "is_zero_avail"]
df = df[KEEP]
INTS = ["id", "host_id", "price", "price_capped", "minimum_nights", "number_of_reviews",
        "calculated_host_listings_count", "availability_365", "flag_never_reviewed",
        "flag_price_outlier", "flag_min_nights_extreme", "is_entire_home", "is_zero_avail"]
DOUBLES = ["latitude", "longitude", "reviews_per_month"]
TYPES = {}
for c in df.columns:
    if c == "last_review":
        TYPES[c] = ("dateTime", "type datetime")
    elif c in DOUBLES:
        TYPES[c] = ("double", "type number")
    elif c in INTS:
        TYPES[c] = ("int64", "Int64.Type")
    else:
        TYPES[c] = ("string", "type text")
BLANKABLE = [c for c in df.columns if (df[c] == "").any()]


def order_col(prev, name, column, order):
    items = ", ".join('"%s"' % v for v in order)
    return ('Table.AddColumn(%s, "%s", each List.PositionOf({%s}, [%s]) + 1, Int64.Type)'
            % (prev, name, items, column))


steps = [
    'Source = Csv.Document(File.Contents("%s"), [Delimiter = ",", Columns = %d, Encoding = 65001, QuoteStyle = QuoteStyle.Csv])'
    % (CSV, N_FULL),
    "Promoted = Table.PromoteHeaders(Source, [PromoteAllScalars = true])",
    'Selected = Table.SelectColumns(Promoted, {%s})' % ", ".join('"%s"' % c for c in KEEP),
    'Blanks = Table.ReplaceValue(Selected, "", null, Replacer.ReplaceValue, {%s})'
    % ", ".join('"%s"' % c for c in BLANKABLE),
    'Typed = Table.TransformColumnTypes(Blanks, {%s}, "en-US")'
    % ", ".join('{"%s", %s}' % (c, mt) for c, (_, mt) in TYPES.items()),
    "S1 = " + order_col("Typed", "BoroughSort", "neighbourhood_group", BOROUGH_ORDER),
    "S2 = " + order_col("S1", "RoomSort", "room_type", ROOM_ORDER),
    "S3 = " + order_col("S2", "BandSort", "price_band", BAND_ORDER),
    "S4 = " + order_col("S3", "AvailSort", "avail_segment", AVAIL_ORDER),
    "S5 = " + order_col("S4", "StaySort", "stay_bin", STAY_ORDER),
    "S6 = " + order_col("S5", "HostSort", "host_size", HOST_ORDER),
]
M = ["let"] + ["    " + s + "," for s in steps[:-1]] + ["    " + steps[-1]] + ["in", "    S6"]

FMT = {"price": "$#,0", "price_capped": "$#,0", "latitude": "0.0000", "longitude": "0.0000",
       "reviews_per_month": "0.00", "last_review": "yyyy-mm-dd", "id": "0", "host_id": "0",
       "minimum_nights": "0", "number_of_reviews": "#,0",
       "calculated_host_listings_count": "0", "availability_365": "0"}
SORT_BY = {"neighbourhood_group": "BoroughSort", "room_type": "RoomSort", "price_band": "BandSort",
           "avail_segment": "AvailSort", "stay_bin": "StaySort", "host_size": "HostSort"}
columns = []
for c, (dt, _) in TYPES.items():
    col_ = {"name": c, "dataType": dt, "sourceColumn": c, "summarizeBy": "none"}
    if c in FMT:
        col_["formatString"] = FMT[c]
    if c in SORT_BY:
        col_["sortByColumn"] = SORT_BY[c]
    columns.append(col_)
for c in ["BoroughSort", "RoomSort", "BandSort", "AvailSort", "StaySort", "HostSort"]:
    columns.append({"name": c, "dataType": "int64", "sourceColumn": c, "summarizeBy": "none", "isHidden": True})


def pearson(x, y):
    return "\n".join([
        "VAR t = FILTER ( Listings, NOT ISBLANK ( Listings[%s] ) && NOT ISBLANK ( Listings[%s] ) && Listings[price] <= 1000 )" % (x, y),
        "VAR mx = AVERAGEX ( t, Listings[%s] )" % x,
        "VAR my = AVERAGEX ( t, Listings[%s] )" % y,
        "VAR sxy = SUMX ( t, ( Listings[%s] - mx ) * ( Listings[%s] - my ) )" % (x, y),
        "VAR sxx = SUMX ( t, ( Listings[%s] - mx ) ^ 2 )" % x,
        "VAR syy = SUMX ( t, ( Listings[%s] - my ) ^ 2 )" % y,
        "RETURN DIVIDE ( sxy, SQRT ( sxx * syy ) )"])


MEASURES = [
    ("Listings", "COUNTROWS ( Listings )", "#,0", "Listings in the current selection"),
    ("Hosts", "DISTINCTCOUNT ( Listings[host_id] )", "#,0", "Distinct hosts in the selection"),
    ("Median Price", "CALCULATE ( MEDIAN ( Listings[price] ), Listings[price] <= 1000 )", "$#,0",
     "Median nightly price ($1,000+ outliers excluded, like the report)"),
    ("Avg Price", "CALCULATE ( AVERAGE ( Listings[price] ), Listings[price] <= 1000 )", "$#,0",
     "Average nightly price ($1,000+ outliers excluded)"),
    ("Entire %", "AVERAGE ( Listings[is_entire_home] )", "0.0%", "Share of entire homes"),
    ("Zero Avail %", "AVERAGE ( Listings[is_zero_avail] )", "0.0%", "Share with zero open days - audit before counting"),
    ("Never Reviewed %", "AVERAGE ( Listings[flag_never_reviewed] )", "0.0%", "Share with zero reviews"),
    ("Total Reviews", "SUM ( Listings[number_of_reviews] )", "#,0", "Guest reviews in the selection"),
    ("Avg Reviews", "AVERAGE ( Listings[number_of_reviews] )", "#,0.0", "Mean reviews per listing"),
    ("Avg Availability", "AVERAGE ( Listings[availability_365] )", "#,0", "Mean open days per year"),
    ("Manhattan %", 'DIVIDE ( CALCULATE ( [Listings], Listings[neighbourhood_group] = "Manhattan" ), [Listings] )',
     "0.0%", "Manhattan share of the selection"),
    ("Luxury %", 'DIVIDE ( CALCULATE ( [Listings], Listings[price_band] = "Luxury ($300+)" ), [Listings] )',
     "0.0%", "Share priced $300+"),
    ("Monthly Stays", 'CALCULATE ( [Listings], Listings[stay_bin] = "30 nights (monthly)" )', "#,0",
     "Listings requiring exactly 30 nights (monthly-rental business)"),
    ("Top Neighbourhood",
     "MAXX ( TOPN ( 1, ADDCOLUMNS ( VALUES ( Listings[neighbourhood] ), \"@n\", [Listings] ), [@n], DESC ), Listings[neighbourhood] )",
     "", "Neighbourhood with the most listings in the selection"),
    ("r Price-Reviews", pearson("price_capped", "number_of_reviews"), "0.00",
     "Pearson correlation between capped price and review count (near zero: price buys no reviews)"),
]


def lineage():
    return str(uuid.uuid4())


def m_measure(n, e, f, d):
    m = {"name": n, "expression": e.split("\n") if "\n" in e else e, "description": d,
         "lineageTag": lineage()}
    if f:  # text measures carry no format string ("" breaks model validation)
        m["formatString"] = f
    return m


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
            m_table(T, columns, M, [m_measure(n, e, f, d) for n, e, f, d in MEASURES]),
        ],
        "annotations": [{"name": "PBI_QueryOrder", "value": json.dumps([T])},
                        {"name": "__PBI_TimeIntelligenceEnabled", "value": "0"},
                        {"name": "PBIDesktopVersion", "value": "2.157.1354.0"}],
    },
}

# ------------------------------------------------------------------ report (PBIR)
SCHEMA = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition"
lit = lambda v: {"expr": {"Literal": {"Value": v}}}  # noqa: E731
TRUE, FALSE = lit("true"), lit("false")


def col(p, entity=None):
    return {"Column": {"Expression": {"SourceRef": {"Entity": entity or T}}, "Property": p}}


def mea(p):
    return {"Measure": {"Expression": {"SourceRef": {"Entity": T}}, "Property": p}}


DISPLAY = {"neighbourhood_group": "Borough", "neighbourhood": "Neighbourhood", "room_type": "Room type",
           "price_band": "Price band", "avail_segment": "Availability", "stay_bin": "Minimum stay",
           "host_size": "Host size", "host_name": "Host", "Listings": "Listings",
           "Median Price": "Median price", "Avg Price": "Avg price", "Entire %": "Entire homes",
           "Zero Avail %": "Zero availability", "Never Reviewed %": "Never reviewed",
           "Total Reviews": "Reviews", "Avg Reviews": "Avg reviews", "Avg Availability": "Open days",
           "Top Neighbourhood": "Top area", "r Price-Reviews": "Price-reviews r"}


def proj(field):
    kind = "Column" if "Column" in field else "Measure"
    ent = field[kind]["Expression"]["SourceRef"]["Entity"]
    prop = field[kind]["Property"]
    p = {"field": field, "queryRef": "%s.%s" % (ent, prop), "nativeQueryRef": prop}
    if prop in DISPLAY:
        p["displayName"] = DISPLAY[prop]
    return p


def top_n(column, measure, n):
    src = lambda: {"SourceRef": {"Source": "m"}}  # noqa: E731
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


def include(column, value):
    """Visual-level filter that keeps a single category (e.g. only Large operators)."""
    ref = {"Column": {"Expression": {"SourceRef": {"Source": "m"}}, "Property": column}}
    where = {"Condition": {"In": {"Expressions": [ref],
                                  "Values": [[{"Literal": {"Value": "'%s'" % value}}]]}}}
    filtr = {"Version": 2, "From": [{"Name": "m", "Entity": T, "Type": 0}], "Where": [where]}
    return {"filters": [{"name": vid(), "field": col(column), "type": "Categorical", "filter": filtr}]}


def exclude_many(column, values):
    """Visual-level filter hiding several categories (e.g. tiny neighbourhoods)."""
    ref = {"Column": {"Expression": {"SourceRef": {"Source": "m"}}, "Property": column}}
    vals = [[{"Literal": {"Value": "'%s'" % v.replace("'", "''")}}] for v in values]
    not_in = {"Not": {"Expression": {"In": {"Expressions": [ref], "Values": vals}}}}
    filtr = {"Version": 2, "From": [{"Name": "m", "Entity": T, "Type": 0}], "Where": [{"Condition": not_in}]}
    return {"filters": [{"name": vid(), "field": col(column), "type": "Categorical", "filter": filtr}]}


def vid():
    return uuid.uuid4().hex[:20]


class Page:
    def __init__(self, name, title):
        self.name, self.title, self.visuals, self.z = vid(), name, [], 0
        self.add_text(title, 16, 8, 1248, 36, size="18pt", bold=True)

    def _container(self, x, y, w, h, visual, filters=None):
        self.z += 1000
        c = {"$schema": "%s/visualContainer/2.12.0/schema.json" % SCHEMA, "name": vid(),
             "position": {"x": x, "y": y, "z": self.z, "height": h, "width": w, "tabOrder": self.z},
             "visual": visual}
        if filters:
            c["filterConfig"] = filters
        self.visuals.append(c)

    def add(self, vtype, x, y, w, h, roles, title=None, sort=None, labels=True,
            objects=None, extra=None, title_size=None, filters=None):
        qs = {role: {"projections": [proj(f) for f in fields]} for role, fields in roles.items()}
        query = {"queryState": qs}
        if sort:
            field, direction = sort
            query["sortDefinition"] = {"sort": [{"field": field, "direction": direction}]}
        objs = dict(objects or {})
        extra_labels = objs.pop("labels_extra", {})
        if labels and vtype not in ("card", "tableEx", "slicer", "scatterChart", "lineChart", "donutChart"):
            objs["labels"] = [{"properties": {"show": TRUE, "labels_extra": extra_labels}}]
        if labels and vtype == "donutChart":
            objs["labels"] = [{"properties": {"show": TRUE, "labelStyle": lit("'Data and percentage'"),
                                              "position": lit("'Outside'"), "extra_labels": extra_labels}}]
        visual = {"visualType": vtype, "query": query, "objects": objs, "drillFilterOtherVisuals": True}
        if title:
            tprops = {"show": TRUE, "text": lit("'" + title.replace("'", "''") + "'")}
            if title_size:
                tprops["fontSize"] = lit("%sD" % title_size)
            visual["visualContainerObjects"] = {"title": [{"properties": tprops}],
                                                "subTitle": [{"properties": {"show": FALSE}}]}
        if extra:
            visual.update(extra)
        self._container(x, y, w, h, visual, filters)

    def add_card(self, x, y, w, h, measure, label):
        props = {"fontSize": lit("20D"), "color": {"solid": {"color": lit("'#2E6FA3'")}}}
        self.add("card", x, y, w, h, {"Values": [mea(measure)]}, title=label, labels=False,
                 title_size=10,
                 objects={"categoryLabels": [{"properties": {"show": FALSE}}],
                          "labels": [{"properties": props}]})

    def add_slicer(self, x, y, w, h, column, title, mode="Dropdown", sync=True):
        objects = {"data": [{"properties": {"mode": lit("'%s'" % mode)}}],
                   "header": [{"properties": {"show": FALSE}}]}
        extra = {"syncGroup": {"groupName": column, "fieldChanges": True,
                               "filterChanges": True}} if sync else None
        self.add("slicer", x, y, w, h, {"Values": [col(column)]}, title=title,
                 labels=False, title_size=9, objects=objects, extra=extra)

    def add_text(self, text, x, y, w, h, size="10pt", bold=False, color="#2E6FA3"):
        paragraphs = []
        for line in text.split("\n"):
            style = {"fontSize": size, "color": color}
            if bold or line.startswith("# "):
                style["fontWeight"] = "bold"
                line = line[2:] if line.startswith("# ") else line
            paragraphs.append({"textRuns": [{"value": line, "textStyle": style}]})
        self._container(x, y, w, h, {"visualType": "textbox",
                                     "objects": {"general": [{"properties": {"paragraphs": paragraphs}}]},
                                     "drillFilterOtherVisuals": True})


SLICERS = [("neighbourhood_group", "Borough", "Dropdown"), ("room_type", "Room type", "Dropdown"),
           ("price_band", "Price band", "Dropdown"), ("avail_segment", "Availability", "Dropdown"),
           ("host_size", "Host size", "Dropdown")]


def slicer_row(p):
    w = 1248 // len(SLICERS)
    for i, (c, t, mode) in enumerate(SLICERS):
        p.add_slicer(16 + i * w, 44, w - 8, 64, c, t, mode)


DESC = lambda f: (f, "Descending")  # noqa: E731
ASC = lambda f: (f, "Ascending")  # noqa: E731
NO_TOTALS = {"total": [{"properties": {"totals": FALSE}}]}
LEGEND_TOP = {"legend": [{"properties": {"show": TRUE, "position": lit("'Top'")}}]}
pages = []

# 1 Overview
p = Page("Overview", "NYC Airbnb Sweet-Stay Overview - 48,884 listings, 37,455 hosts, 221 neighbourhoods")
slicer_row(p)
for i, (m, label) in enumerate([("Listings", "Listings"), ("Median Price", "Median price"),
                                ("Entire %", "Entire homes"), ("Zero Avail %", "Zero availability"),
                                ("Total Reviews", "Reviews"), ("Hosts", "Hosts"),
                                ("Never Reviewed %", "Never reviewed"), ("Top Neighbourhood", "Top area")]):
    p.add_card(16 + i * 156, 112, 148, 84, m, label)
p.add("clusteredBarChart", 16, 204, 624, 250, {"Category": [col("neighbourhood_group")], "Y": [mea("Listings")]},
      "Listings by borough - Manhattan + Brooklyn are 85%", sort=DESC(mea("Listings")))
p.add("donutChart", 648, 204, 300, 250, {"Category": [col("room_type")], "Y": [mea("Listings")]},
      "Listing types", sort=DESC(mea("Listings")))
p.add("clusteredColumnChart", 956, 204, 308, 250, {"Category": [col("price_band")], "Y": [mea("Listings")]},
      "Price bands", sort=ASC(col("price_band")))
p.add("tableEx", 16, 462, 624, 250,
      {"Values": [col("neighbourhood_group"), mea("Listings"), mea("Median Price"), mea("Entire %"),
                   mea("Avg Reviews")]},
      "Borough scorecard", sort=DESC(mea("Listings")), objects=NO_TOTALS)
p.add("tableEx", 648, 462, 616, 250,
      {"Values": [col("neighbourhood"), mea("Listings"), mea("Median Price"), mea("Avg Reviews")]},
      "Top 10 neighbourhoods by listings", sort=DESC(mea("Listings")), objects=NO_TOTALS,
      filters=top_n("neighbourhood", "Listings", 10))
pages.append(p)

# 2 Prices
p = Page("Prices", "Prices: a clean ladder - room type first, borough second, reviews move nothing (r = -0.06)")
slicer_row(p)
for i, (m, label) in enumerate([("Median Price", "Median price"), ("Avg Price", "Avg price"),
                                ("Entire %", "Entire homes"), ("Luxury %", "Luxury $300+"),
                                ("r Price-Reviews", "Price-reviews r"), ("Manhattan %", "Manhattan share")]):
    p.add_card(16 + i * 208, 112, 200, 84, m, label)
p.add("clusteredColumnChart", 16, 204, 624, 250, {"Category": [col("neighbourhood_group")], "Y": [mea("Median Price")]},
      "Median price by borough: $149 Manhattan vs $65 Bronx", sort=DESC(mea("Median Price")))
p.add("clusteredColumnChart", 648, 204, 616, 250, {"Category": [col("room_type")], "Y": [mea("Median Price")]},
      "Median price by listing type: $160 / $70 / $45", sort=DESC(mea("Median Price")))
# tiny areas (1-3 listings) would top a raw median ranking, so they are hidden:
# the chart then matches the min-30 priciest list in the analysis
TINY_RICH = ["Fort Wadsworth", "Woodrow", "Neponsit", "Willowbrook", "Breezy Point"]
pricey_top = top_n("neighbourhood", "Median Price", 10)
pricey_top["filters"] += exclude_many("neighbourhood", TINY_RICH)["filters"]
p.add("clusteredBarChart", 16, 462, 624, 250, {"Category": [col("neighbourhood")], "Y": [mea("Median Price")]},
      "Priciest neighbourhoods (top 10 by median, min. 30 listings)", sort=DESC(mea("Median Price")),
      filters=pricey_top)
p.add("scatterChart", 648, 462, 616, 250,
      {"Category": [col("neighbourhood")], "X": [mea("Median Price")], "Y": [mea("Avg Reviews")]},
      "Price vs traction per neighbourhood: no slope, value areas win reviews")
pages.append(p)

# 3 Demand
p = Page("Demand", "Demand follows value, not luxury - review leaders are Queens and Bed-Stuy, not Tribeca")
slicer_row(p)
for i, (m, label) in enumerate([("Total Reviews", "Reviews"), ("Avg Reviews", "Avg reviews"),
                                ("Never Reviewed %", "Never reviewed"), ("r Price-Reviews", "Price-reviews r"),
                                ("Top Neighbourhood", "Top area"), ("Listings", "Listings")]):
    p.add_card(16 + i * 208, 112, 200, 84, m, label)
p.add("clusteredBarChart", 16, 204, 624, 250, {"Category": [col("neighbourhood")], "Y": [mea("Total Reviews")]},
      "Top 10 neighbourhoods by total reviews", sort=DESC(mea("Total Reviews")),
      filters=top_n("neighbourhood", "Total Reviews", 10))
p.add("clusteredColumnChart", 648, 204, 616, 250, {"Category": [col("neighbourhood_group")], "Y": [mea("Avg Reviews")]},
      "Average reviews per listing by borough", sort=DESC(mea("Avg Reviews")))
p.add("tableEx", 16, 462, 1248, 250,
      {"Values": [col("neighbourhood"), col("neighbourhood_group"), mea("Listings"),
                   mea("Median Price"), mea("Total Reviews"), mea("Avg Reviews")]},
      "Neighbourhood demand table (top 15 by reviews)", sort=DESC(mea("Total Reviews")),
      objects=NO_TOTALS, filters=top_n("neighbourhood", "Total Reviews", 15))
pages.append(p)

# 4 Supply
p = Page("Supply", "Supply: a barbelled calendar, two stay-businesses, fragmented hosts with a professional head")
slicer_row(p)
for i, (m, label) in enumerate([("Zero Avail %", "Zero availability"), ("Avg Availability", "Open days"),
                                ("Monthly Stays", "30-night listings"), ("Hosts", "Hosts"),
                                ("Manhattan %", "Manhattan share"), ("Luxury %", "Luxury $300+")]):
    p.add_card(16 + i * 208, 112, 200, 84, m, label)
p.add("clusteredColumnChart", 16, 204, 408, 250, {"Category": [col("avail_segment")], "Y": [mea("Listings")]},
      "Availability: 36% blocked, 30% mostly open", sort=ASC(col("avail_segment")))
p.add("clusteredColumnChart", 432, 204, 408, 250, {"Category": [col("stay_bin")], "Y": [mea("Listings")]},
      "Minimum stay: 1-3 nights plus a 30-night spike", sort=ASC(col("stay_bin")))
p.add("clusteredColumnChart", 848, 204, 416, 250, {"Category": [col("host_size")], "Y": [mea("Listings")]},
      "66% of listings sit with single-listing hosts", sort=ASC(col("host_size")))
hosts_top = top_n("host_name", "Listings", 10)
hosts_top["filters"] += include("host_size", "Large (21+)")["filters"]
p.add("clusteredBarChart", 16, 462, 624, 250, {"Category": [col("host_name")], "Y": [mea("Listings")]},
      "Largest operators (21+ listings): firms top the chart", sort=DESC(mea("Listings")),
      filters=hosts_top)
p.add("clusteredColumnChart", 648, 462, 616, 250, {"Category": [col("host_size")], "Y": [mea("Median Price")]},
      "Median price by host size", sort=ASC(col("host_size")))
pages.append(p)

# 5 Insights
INSIGHTS = "\n".join([
    "# Key insights (48,884 listings, Sep 2019 snapshot)",
    "- Two boroughs run the market: Manhattan (21,660, 44%) + Brooklyn (20,095, 41%) = 85% of listings.",
    "- Clean price ladder: Manhattan $149 vs Bronx $65; entire homes $160 vs private rooms $70 vs shared $45.",
    "- Price buys ZERO reviews (r = -0.06). Tribeca ($282) and NoHo ($250) average the fewest reviews; "
    "East Elmhurst (81.7), Jamaica (42.9) and Flushing (34.8) lead demand.",
    "- 35.9% of listings show zero open days and 20.6% were never reviewed: audit the tail before counting supply.",
    "- 86% of hosts hold one listing (66% of supply); only 4.5% sits with 21+ operators - "
    "but the top two are firms: Sonder (327) and Blueground (232).",
    "- Two businesses in one file: 1-3 night stays (67%) plus a 30-night monthly spike (3,758 listings).",
    "",
    "# Recommendations",
    "- Price by ladder: room-type base ($160/$70/$45) x borough factor, not by gut.",
    "- Acquire and promote in value corridors (Queens, Bed-Stuy); coach entry pricing near $100 for new hosts.",
    "- Split operations by minimum stay; counter professional hosts on reliability signals (instant book, reviews).",
    "",
    "# Data notes",
    "- Source: AB_NYC_2019.csv (Inside Airbnb). 11 rows priced $0 removed; 239 listings over $1,000 kept and flagged.",
    "- Price averages exclude $1,000+ outliers. Reviews-per-month gaps (= zero-review rows) filled with 0.",
])
p = Page("Insights", "Insights, recommendations and data notes")
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
    sm_dir, rp_dir = os.path.join(OUT, "%s.SemanticModel" % NAME), os.path.join(OUT, "%s.Report" % NAME)
    dump(os.path.join(OUT, "%s.pbip" % NAME),
         {"version": "1.0", "artifacts": [{"report": {"path": "%s.Report" % NAME}}],
          "settings": {"enableAutoRecovery": True}})
    dump(os.path.join(sm_dir, "definition.pbism"), {"version": "1.0", "settings": {}})
    dump(os.path.join(sm_dir, "model.bim"), model)
    dump(os.path.join(rp_dir, "definition.pbir"),
         {"version": "4.0", "datasetReference": {"byPath": {"path": "../%s.SemanticModel" % NAME}}})
    d = os.path.join(rp_dir, "definition")
    dump(os.path.join(d, "version.json"),
         {"$schema": "%s/versionMetadata/1.0.0/schema.json" % SCHEMA, "version": "2.0.0"})

    with zipfile.ZipFile(THEME_SRC) as z:
        base = z.read("Report/StaticResources/SharedResources/BaseThemes/%s.json" % BASE_THEME)
    os.makedirs(os.path.join(rp_dir, "StaticResources", "SharedResources", "BaseThemes"), exist_ok=True)
    with open(os.path.join(rp_dir, "StaticResources", "SharedResources", "BaseThemes", "%s.json" % BASE_THEME),
              "wb") as fh:
        fh.write(base)
    # candy theme: pastel blue / pink / green / light yellow + lavender + peach
    dump(os.path.join(rp_dir, "StaticResources", "RegisteredResources", "CandyTheme.json"),
         {"name": "Candy", "dataColors": ["#7FB6D9", "#F4A7C3", "#9BDBA6", "#FFE08A",
                                          "#C3B2E8", "#FFC9A3", "#2E6FA3", "#D94F7A"],
          "foreground": "#33475B", "background": "#FFFFFF", "tableAccent": "#7FB6D9"})
    dump(os.path.join(d, "report.json"), {
        "$schema": "%s/report/3.3.0/schema.json" % SCHEMA,
        "themeCollection": {
            "baseTheme": {"name": BASE_THEME, "reportVersionAtImport": {"visual": "2.13.0", "report": "3.4.0",
                                                                       "page": "2.3.1"}, "type": "SharedResources"},
            "customTheme": {"name": "CandyTheme.json",
                            "reportVersionAtImport": {"visual": "2.13.0", "report": "3.4.0", "page": "2.3.1"},
                            "type": "RegisteredResources"}},
        "resourcePackages": [
            {"name": "SharedResources", "type": "SharedResources",
             "items": [{"name": BASE_THEME, "path": "BaseThemes/%s.json" % BASE_THEME, "type": "BaseTheme"}]},
            {"name": "RegisteredResources", "type": "RegisteredResources",
             "items": [{"name": "CandyTheme.json", "path": "CandyTheme.json", "type": "CustomTheme"}]}],
        "settings": {"useStylableVisualContainerHeader": True, "exportDataMode": "AllowSummarized",
                     "defaultDrillFilterOtherVisuals": True, "allowChangeFilterTypes": True,
                     "useEnhancedTooltips": True, "useDefaultAggregateDisplayName": True}})
    dump(os.path.join(d, "pages", "pages.json"),
         {"$schema": "%s/pagesMetadata/1.1.0/schema.json" % SCHEMA,
          "pageOrder": [pg.name for pg in pages], "activePageName": pages[0].name})
    for pg in pages:
        dump(os.path.join(d, "pages", pg.name, "page.json"),
             {"$schema": "%s/page/2.1.0/schema.json" % SCHEMA, "name": pg.name,
              "displayName": pg.title, "displayOption": "FitToPage", "height": 720, "width": 1280})
        for v in pg.visuals:
            dump(os.path.join(d, "pages", pg.name, "visuals", v["name"], "visual.json"), v)
    n = sum(len(pg.visuals) for pg in pages)
    print("Wrote %s: %d pages, %d visuals, %d measures, %d Listings columns"
          % (OUT, len(pages), n, len(MEASURES), len(columns)))


if __name__ == "__main__":
    main()
