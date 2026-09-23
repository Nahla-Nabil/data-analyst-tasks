"""
Task 7 - builds a Power BI project (PBIP) for the hospital dashboard.

Reads  Cleaned_Hospital_Data.csv, analysis_summary.json
Writes PowerBI/Hospital_Dashboard.pbip
       PowerBI/Hospital_Dashboard.SemanticModel/   model.bim: Power Query load of the CSV, Calendar table, sort columns,
                                                   relationship and every DAX measure
       PowerBI/Hospital_Dashboard.Report/          PBIR report: 5 pages, synced slicers, KPI cards, charts, tables

Open the .pbip in Power BI Desktop, press Refresh (the project stores no data), then File > Save as > .pbix.
The CSV path is written into the Power Query as an absolute path - rerun this script if the folder moves.
"""

import json
import os
import shutil
import uuid

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
CSV = os.path.join(HERE, "Cleaned_Hospital_Data.csv")
OUT = os.path.join(HERE, "PowerBI")
NAME = "Hospital_Dashboard"
T = "Admissions"
THEME_SRC = os.path.join(HERE, "..", "Task 3", "HR_Attrition_Model_Nahla.pbix")   # source of the base theme file
BASE_THEME = "Fluent2-CY26SU09"

# ------------------------------------------------------------------ semantic model
df = pd.read_csv(CSV)
TYPES = {}
for c in df.columns:
    if c in ("Admission_Date", "Discharge_Date"):
        TYPES[c] = ("dateTime", "type date")
    elif df[c].dtype == bool:
        TYPES[c] = ("boolean", "type logical")
    elif c in ("Bill", "Bill_Raw", "Bill_Per_Day"):
        TYPES[c] = ("double", "type number")
    elif pd.api.types.is_integer_dtype(df[c]):
        TYPES[c] = ("int64", "Int64.Type")
    else:
        TYPES[c] = ("string", "type text")

m_types = ", ".join(f'{{"{c}", {mt}}}' for c, (_, mt) in TYPES.items())
M = [
    "let",
    f'    Source = Csv.Document(File.Contents("{CSV}"), [Delimiter = ",", Columns = {len(df.columns)}, Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),',
    "    Promoted = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),",
    '    Blanks = Table.ReplaceValue(Promoted, "", null, Replacer.ReplaceValue, {"Bill", "Bill_Per_Day", "Review_Flag"}),',
    f'    Typed = Table.TransformColumnTypes(Blanks, {{{m_types}}}, "en-US"),',
    # sort helpers are built here, not as DAX columns (a DAX sort column derived from its own target is circular)
    '    SevSort = Table.AddColumn(Typed, "SeveritySort", each if [Severity] = "Low" then 1 else if [Severity] = "Medium" then 2 else 3, Int64.Type),',
    '    AgeSort = Table.AddColumn(SevSort, "AgeSort", each if [Age] <= 17 then 1 else if [Age] <= 39 then 2 else if [Age] <= 59 then 3 else 4, Int64.Type),',
    '    StaySort = Table.AddColumn(AgeSort, "StaySort", each if [Length_of_Stay] <= 3 then 1 else if [Length_of_Stay] <= 7 then 2 '
    'else if [Length_of_Stay] <= 14 then 3 else 4, Int64.Type),',
    '    WdSort = Table.AddColumn(StaySort, "WeekdaySort", each List.PositionOf({"Saturday", "Sunday", "Monday", "Tuesday", "Wednesday", '
    '"Thursday", "Friday"}, [Admission_Weekday]) + 1, Int64.Type)',
    "in",
    "    WdSort",
]

FMT = {"Bill": "#,0", "Bill_Raw": "#,0", "Bill_Per_Day": "#,0", "Admission_Date": "yyyy-mm-dd", "Discharge_Date": "yyyy-mm-dd"}
SORT_BY = {"Admission_Month_Name": "Admission_Month", "Severity": "SeveritySort", "Age_Group": "AgeSort",
           "Stay_Band": "StaySort", "Admission_Weekday": "WeekdaySort"}
columns = []
for c, (dt, _) in TYPES.items():
    col = {"name": c, "dataType": dt, "sourceColumn": c, "summarizeBy": "none"}
    if c in FMT:
        col["formatString"] = FMT[c]
    if c in ("Length_of_Stay", "Age", "Bill"):
        col["summarizeBy"] = "sum"
    if c in SORT_BY:
        col["sortByColumn"] = SORT_BY[c]
    columns.append(col)
CALC_COLS = ["SeveritySort", "AgeSort", "StaySort", "WeekdaySort"]   # built in Power Query (see M above), hidden
for c in CALC_COLS:
    columns.append({"name": c, "dataType": "int64", "sourceColumn": c, "summarizeBy": "none", "isHidden": True})

MEASURES = [
    ("Admissions", "COUNTROWS ( Admissions )", "#,0", "Volume: number of admissions"),
    ("Bed Days", "SUM ( Admissions[Length_of_Stay] )", "#,0", "Efficiency: total bed-days used"),
    ("ALOS", "AVERAGE ( Admissions[Length_of_Stay] )", "0.0", "Efficiency: average length of stay (days)"),
    ("Median LOS", "MEDIAN ( Admissions[Length_of_Stay] )", "0.0", "Efficiency: median length of stay"),
    ("Long Stay Rate", "DIVIDE ( CALCULATE ( [Admissions], Admissions[Long_Stay] = TRUE () ), [Admissions] )", "0.0%",
     "Efficiency: share of stays over 7 days"),
    ("Bed Days 15+ Share", "DIVIDE ( CALCULATE ( [Bed Days], Admissions[Length_of_Stay] >= 15 ), [Bed Days] )", "0.0%",
     "Efficiency: bed-days used by stays of 15+ days"),
    ("High Severity Share", 'DIVIDE ( CALCULATE ( [Admissions], Admissions[Severity] = "High" ), [Admissions] )', "0.0%", "Acuity"),
    ("Senior Share", "DIVIDE ( CALCULATE ( [Admissions], Admissions[Age] >= 60 ), [Admissions] )", "0.0%", "Acuity: patients 60+"),
    ("Uninsured Rate", 'DIVIDE ( CALCULATE ( [Admissions], Admissions[Insurance] = "Uninsured" ), [Admissions] )', "0.0%",
     "Finance: revenue exposed to non-payment"),
    ("Billing Completeness", "DIVIDE ( COUNT ( Admissions[Bill] ), [Admissions] )", "0.0%",
     "Finance: admissions with a genuine bill (999/3852 placeholders are blank)"),
    ("Avg Genuine Bill", "AVERAGE ( Admissions[Bill] )", "#,0", "Finance: average of genuine bills only"),
    ("Median Bill per Day", "MEDIAN ( Admissions[Bill_Per_Day] )", "#,0", "Finance: price of a bed-day"),
    ("Date Correction Rate", "DIVIDE ( CALCULATE ( [Admissions], Admissions[Date_Corrected] = TRUE () ), [Admissions] )", "0.0%",
     "Data quality: reversed admission/discharge dates"),
    ("Review Flags", "CALCULATE ( [Admissions], NOT ISBLANK ( Admissions[Review_Flag] ) )", "#,0",
     "Data quality: records flagged for clinical review"),
    ("Admission Share", "DIVIDE ( [Admissions], CALCULATE ( [Admissions], ALLSELECTED ( Admissions ) ) )", "0%", "Share of the current slice"),
    ("Bed Day Share", "DIVIDE ( [Bed Days], CALCULATE ( [Bed Days], ALLSELECTED ( Admissions ) ) )", "0%", "Share of the current slice"),
    ("Severity Row %", "DIVIDE ( [Admissions], CALCULATE ( [Admissions], ALLSELECTED ( Admissions[Severity], Admissions[SeveritySort] ) ) )", "0%",
     "Severity mix within a diagnosis (matrix)"),
    ("ALOS vs Hospital", "[ALOS] - CALCULATE ( [ALOS], ALL ( Admissions ) )", "+0.0;-0.0;0.0", "Gap to the hospital average"),
    ("Census", "VAR d = MAX ( 'Calendar'[Date] )\nRETURN\n    CALCULATE ( [Admissions], REMOVEFILTERS ( 'Calendar' ),\n"
               "        Admissions[Admission_Date] <= d, Admissions[Discharge_Date] > d ) + 0", "#,0",
     "Capacity: patients in a bed on a date"),
    ("Peak Census", "MAXX ( VALUES ( 'Calendar'[Date] ), [Census] )", "#,0", "Capacity: busiest night"),
    ("Avg Census", "AVERAGEX ( FILTER ( VALUES ( 'Calendar'[Date] ), YEAR ( 'Calendar'[Date] ) = 2023 ), [Census] )", "0.0",
     "Capacity: average occupied beds per night in 2023"),
    ("Flagged Stay (days)", "IF ( NOT ISBLANK ( SELECTEDVALUE ( Admissions[Review_Flag] ) ), SUM ( Admissions[Length_of_Stay] ) )", "#,0",
     "Review list: shows only flagged records"),
]


def lineage():
    return str(uuid.uuid4())


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
             "columns": [{"type": "calculatedTableColumn", "name": "Date", "dataType": "dateTime", "isNameInferred": True,
                          "isDataTypeInferred": True, "sourceColumn": "[Date]", "formatString": "yyyy-mm-dd", "summarizeBy": "none"}],
             "partitions": [{"name": "Calendar", "mode": "import",
                             "source": {"type": "calculated", "expression": "CALENDAR ( DATE ( 2022, 12, 31 ), DATE ( 2024, 1, 14 ) )"}}]},
        ],
        "relationships": [{"name": lineage(), "fromTable": T, "fromColumn": "Admission_Date", "toTable": "Calendar", "toColumn": "Date"}],
        "annotations": [{"name": "PBI_QueryOrder", "value": json.dumps([T])},
                        {"name": "__PBI_TimeIntelligenceEnabled", "value": "0"},
                        {"name": "PBIDesktopVersion", "value": "2.157.1354.0"}],
    },
}

# ------------------------------------------------------------------ report (PBIR)
S = json.load(open(os.path.join(HERE, "analysis_summary.json"), encoding="utf-8"))
SCHEMA = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition"
lit = lambda v: {"expr": {"Literal": {"Value": v}}}
TRUE, FALSE = lit("true"), lit("false")


def col(p):
    return {"Column": {"Expression": {"SourceRef": {"Entity": "Calendar" if p == "Date" else T}}, "Property": p}}


def mea(p):
    return {"Measure": {"Expression": {"SourceRef": {"Entity": T}}, "Property": p}}


def proj(field):
    kind = "Column" if "Column" in field else "Measure"
    ent = field[kind]["Expression"]["SourceRef"]["Entity"]
    prop = field[kind]["Property"]
    return {"field": field, "queryRef": f"{ent}.{prop}", "nativeQueryRef": prop}


def vid():
    return uuid.uuid4().hex[:20]


class Page:
    def __init__(self, name, title):
        self.name, self.title, self.visuals, self.z = vid(), name, [], 0
        self.add_text(title, 16, 8, 1248, 36, size="18pt", bold=True)

    def _container(self, x, y, w, h, visual):
        self.z += 1000
        name = vid()
        self.visuals.append({"$schema": f"{SCHEMA}/visualContainer/2.12.0/schema.json", "name": name,
                             "position": {"x": x, "y": y, "z": self.z, "height": h, "width": w, "tabOrder": self.z},
                             "visual": visual})

    def add(self, vtype, x, y, w, h, roles, title=None, sort=None, labels=True, objects=None, extra=None, title_size=None):
        qs = {role: {"projections": [proj(f) for f in fields]} for role, fields in roles.items()}
        query = {"queryState": qs}
        if sort:
            field, direction = sort
            query["sortDefinition"] = {"sort": [{"field": field, "direction": direction}]}
        objs = dict(objects or {})
        if labels and vtype not in ("card", "tableEx", "pivotTable", "slicer", "scatterChart"):
            objs["labels"] = [{"properties": {"show": TRUE}}]
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

    def add_card(self, x, y, w, h, measure, label):
        self.add("card", x, y, w, h, {"Values": [mea(measure)]}, title=label, labels=False, title_size=10,
                 objects={"categoryLabels": [{"properties": {"show": FALSE}}],
                          "labels": [{"properties": {"fontSize": lit("20D"), "color": {"solid": {"color": lit("'#1F3A5F'")}}}}]})

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


SLICERS = [("Admission_Month_Name", "Month"), ("Doctor", "Doctor"), ("Diagnosis", "Diagnosis"),
           ("Insurance", "Insurance"), ("Severity", "Severity"), ("Age_Group", "Age group")]


def slicer_row(p):
    w = 1248 // len(SLICERS)
    for i, (c, t) in enumerate(SLICERS):
        p.add_slicer(16 + i * w, 44, w - 8, 64, c, t)


DESC = lambda f: (f, "Descending")
ASC = lambda f: (f, "Ascending")
pages = []

# 1 Overview
p = Page("Overview", "Hospital Performance 2023 - 247 admissions, 7 doctors, 10 diagnoses")
slicer_row(p)
CARDS = [("Admissions", "Admissions"), ("ALOS", "Avg stay (days)"), ("Bed Days", "Bed-days"),
         ("Long Stay Rate", "Long-stay rate"), ("Peak Census", "Peak census"), ("High Severity Share", "High severity"),
         ("Uninsured Rate", "Uninsured"), ("Billing Completeness", "Genuine bills")]
for i, (m, label) in enumerate(CARDS):
    p.add_card(16 + i * 156, 110, 148, 88, m, label)
p.add("clusteredColumnChart", 16, 206, 616, 250, {"Category": [col("Admission_Month_Name")], "Y": [mea("Admissions")]},
      "Admissions by month", sort=ASC(col("Admission_Month_Name")))
p.add("clusteredColumnChart", 640, 206, 300, 250, {"Category": [col("Admission_Weekday")], "Y": [mea("Admissions")]},
      "Admissions by weekday (Fri-Sat = weekend)", sort=ASC(col("Admission_Weekday")))
p.add("clusteredColumnChart", 948, 206, 316, 250, {"Category": [col("Stay_Band")], "Y": [mea("Admission Share"), mea("Bed Day Share")]},
      "Share of admissions vs bed-days by stay length", sort=ASC(col("Stay_Band")))
p.add("lineChart", 16, 464, 800, 248, {"Category": [col("Date")], "Y": [mea("Census")]},
      "Daily bed census (patients in hospital each night)", labels=False)
p.add("clusteredColumnChart", 824, 464, 440, 248, {"Category": [col("Length_of_Stay")], "Y": [mea("Admissions")]},
      "Length-of-stay distribution (patients by days in hospital)", sort=ASC(col("Length_of_Stay")), labels=False)
pages.append(p)

# 2 Case mix & LOS
p = Page("Case Mix & LOS", "Case mix and length of stay: does stay length match how sick patients are?")
slicer_row(p)
p.add("clusteredBarChart", 16, 112, 408, 300, {"Category": [col("Diagnosis")], "Y": [mea("Admissions")]},
      "Admissions by diagnosis", sort=DESC(mea("Admissions")))
p.add("clusteredBarChart", 432, 112, 408, 300, {"Category": [col("Diagnosis")], "Y": [mea("ALOS")]},
      "Average length of stay by diagnosis (days)", sort=DESC(mea("ALOS")))
p.add("pivotTable", 848, 112, 416, 300, {"Rows": [col("Diagnosis")], "Columns": [col("Severity")], "Values": [mea("Severity Row %")]},
      "Severity mix within each diagnosis (% of row) - stroke mostly Low, cold mostly High")
p.add("clusteredColumnChart", 16, 420, 408, 292, {"Category": [col("Age_Group")], "Y": [mea("ALOS")]},
      "Average stay by age group (days) - the one real driver", sort=ASC(col("Age_Group")))
p.add("clusteredColumnChart", 432, 420, 408, 292, {"Category": [col("Severity")], "Y": [mea("ALOS")]},
      "Average stay by recorded severity (days) - almost flat", sort=ASC(col("Severity")))
p.add("clusteredBarChart", 848, 420, 416, 292, {"Category": [col("Insurance")], "Y": [mea("Admissions")]},
      "Admissions by insurance", sort=DESC(mea("Admissions")))
pages.append(p)

# 3 Doctors & billing
p = Page("Doctors & Billing", "Doctor performance and billing data quality")
slicer_row(p)
p.add("clusteredBarChart", 16, 112, 408, 300, {"Category": [col("Doctor")], "Y": [mea("ALOS")]},
      "Average length of stay by doctor (days)", sort=DESC(mea("ALOS")))
p.add("clusteredBarChart", 432, 112, 408, 300, {"Category": [col("Doctor")], "Y": [mea("Admission Share"), mea("Bed Day Share")]},
      "Share of admissions vs share of bed-days by doctor", sort=DESC(mea("Admission Share")))
p.add("tableEx", 848, 112, 416, 300, {"Values": [col("Doctor"), mea("Admissions"), mea("ALOS"), mea("Long Stay Rate"),
                                                 mea("High Severity Share"), mea("Review Flags")]},
      "Doctor scorecard", sort=DESC(mea("Admissions")))
p.add("clusteredBarChart", 16, 420, 408, 292, {"Category": [col("Bill_Status")], "Y": [mea("Admissions")]},
      "Billing data quality: genuine vs placeholder bills", sort=DESC(mea("Admissions")))
p.add("scatterChart", 432, 420, 832, 292, {"Category": [col("Patient_ID")], "X": [mea("ALOS")], "Y": [mea("Avg Genuine Bill")]},
      "Genuine bill vs length of stay (one dot per admission with a genuine bill)", labels=False)
pages.append(p)

# 4 Clinical review
p = Page("Clinical Review", "Records flagged for clinical review (kept in the analysis)")
slicer_row(p)
p.add("tableEx", 16, 112, 1248, 600, {"Values": [col("Patient_ID"), col("Review_Flag"), col("Diagnosis"), col("Age"), col("Severity"),
                                                 col("Doctor"), col("Admission_Date"), mea("Flagged Stay (days)")]},
      "Flagged records - long stays for minor conditions and atypical ages", sort=DESC(mea("Flagged Stay (days)")))
pages.append(p)

# 5 Insights
k, f = S["kpi"], S["findings"]
INSIGHTS = "\n".join([
    "# Key insights (full year)",
    f"- Very long stays: stays of 15+ days are {k['stays_15plus'] / k['total_admissions']:.0%} of admissions but {k['bed_days_15plus_share']:.0%} of bed-days; "
    f"{f['minor_in_15plus']} of them are colds, flu, allergy or migraine.",
    f"- Severity does not predict stay: high {f['alos_high']} days vs low {f['alos_low']} (p = 0.91); a common cold ({f['cold_alos']} d) stays longer than a stroke ({f['stroke_alos']} d).",
    f"- Age is the one real driver: children 4.7 days, seniors 7.1; seniors are {k['senior_share']:.0%} of admissions and {f['senior_bed_day_share']:.0%} of bed-days.",
    f"- Billing: only {k['billing_completeness']:.0%} of admissions have a genuine bill (the rest are 999/3852 placeholders); none of the 28 longest stays is billed.",
    f"- Demand: May is busiest (32 admissions, peak census {k['peak_census']} on 16 May), August quietest (10); admissions cluster Tuesday-Wednesday and drop on Friday.",
    f"- Doctors: {f['top2_doctors'][0]} and {f['top2_doctors'][1]} treat {f['top2_doctor_admission_share']:.0%} of patients but use "
    f"{f['top2_doctor_bed_day_share']:.0%} of bed-days (not statistically conclusive, p = 0.30).",
    "",
    "# Recommendations",
    "1. Fix billing capture: make a real bill mandatory at discharge and block the 999/3852 defaults (target: 100% completeness).",
    "2. Weekly review of every patient past day 7, starting with the 17 minor-condition stays of 15+ days (about 250 bed-days, 16% of the year).",
    "3. Audit severity coding against clear triage criteria (sample of stroke and pneumonia records).",
    "4. Flexible capacity for the May / October peaks (13 and 9 beds vs an average of about 4); roster for Tuesday-Wednesday intake; geriatric discharge support.",
    "5. Add a unique patient ID and date validation to the admission form (12% of records had reversed dates; readmissions cannot be tracked).",
])
p = Page("Insights", "Insights and recommendations")
p.add_text(INSIGHTS, 16, 56, 1248, 640, size="12pt")
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

    # themes: base theme copied from an existing Power BI file + a custom theme with the dashboard palette
    import zipfile
    with zipfile.ZipFile(THEME_SRC) as z:
        base = z.read(f"Report/StaticResources/SharedResources/BaseThemes/{BASE_THEME}.json")
    os.makedirs(os.path.join(rp_dir, "StaticResources", "SharedResources", "BaseThemes"), exist_ok=True)
    with open(os.path.join(rp_dir, "StaticResources", "SharedResources", "BaseThemes", f"{BASE_THEME}.json"), "wb") as fh:
        fh.write(base)
    dump(os.path.join(rp_dir, "StaticResources", "RegisteredResources", "HospitalTheme.json"),
         {"name": "Hospital", "dataColors": ["#2A78D6", "#EB6834", "#1BAF7A", "#EDA100", "#E87BA4", "#008300", "#4A3AA7", "#E34948"],
          "foreground": "#0B0B0B", "background": "#FFFFFF", "tableAccent": "#2A78D6"})
    dump(os.path.join(d, "report.json"), {
        "$schema": f"{SCHEMA}/report/3.3.0/schema.json",
        "themeCollection": {
            "baseTheme": {"name": BASE_THEME, "reportVersionAtImport": {"visual": "2.13.0", "report": "3.4.0", "page": "2.3.1"}, "type": "SharedResources"},
            "customTheme": {"name": "HospitalTheme.json", "reportVersionAtImport": {"visual": "2.13.0", "report": "3.4.0", "page": "2.3.1"},
                            "type": "RegisteredResources"}},
        "resourcePackages": [
            {"name": "SharedResources", "type": "SharedResources", "items": [{"name": BASE_THEME, "path": f"BaseThemes/{BASE_THEME}.json", "type": "BaseTheme"}]},
            {"name": "RegisteredResources", "type": "RegisteredResources", "items": [{"name": "HospitalTheme.json", "path": "HospitalTheme.json", "type": "CustomTheme"}]}],
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
