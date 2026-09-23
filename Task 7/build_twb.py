"""
Task 7 - builds Hospital_Dashboard.twbx (Tableau packaged workbook) from Hospital.hyper.

The .twb XML is generated here (no Tableau needed to run this script); Tableau Public / Desktop opens the result.
Engine adapted from Task 6/build_twb.py.

Contents: 8 KPI sheets + 17 chart/table sheets on 4 dashboards (Overview, Case Mix & Length of Stay,
Doctors & Billing, Clinical Review). Six drop-down filters (Quarter, Doctor, Diagnosis, Insurance, Severity, Age group)
sit on every dashboard. Each one is placed on every sheet in the same filter group, so changing it filters every sheet.
Clicking a bar filters the rest of that dashboard (filter actions).

    python build_twb.py                       # -> Hospital_Dashboard.twbx
    python build_twb.py --test "Doctor=Dr. Sara Ibrahim"   # test copy with that doctor pre-selected in the shared filter
    python build_twb.py --first "Doctors & Billing"        # test copy that opens on that dashboard
"""

import json
import sys
import uuid
import zipfile
from xml.sax.saxutils import escape, quoteattr as q

HYPER = "Hospital.hyper"
TWB_NAME = "Hospital_Dashboard.twb"
OUT = "Hospital_Dashboard.twbx"
DS = "federated.1h0sp1t4l2023dsx7k9m3q5w8e2r"
CONN = "hyper.7h0sp1t4lc0nn3ct10n4b6d8f0"

# ---------------------------------------------------------------- palette (same as the HTML dashboard)
BLUE, ORANGE, NEUTRAL, NEUTRAL2, INK, SOFT = "#2a78d6", "#eb6834", "#b9b7ae", "#8f8d85", "#1f3a5f", "#52514e"
ORD = ["#86b6ef", "#3987e5", "#1c5cab", "#0d366b"]


def uid():
    return "{" + str(uuid.uuid4()).upper() + "}"


# ---------------------------------------------------------------- field catalogue: name -> (datatype, role, type)
BASE = {}
for c in ["Patient_ID", "Patient_Name", "Age_Group", "Gender", "Diagnosis", "Diagnosis_Group", "Doctor", "Stay_Band",
          "Admission_Month_Name", "Admission_Quarter", "Admission_Weekday", "Insurance", "Severity", "Bill_Status", "Review_Flag"]:
    BASE[c] = ("string", "dimension", "nominal")
for c in ["Admission_Date", "Discharge_Date"]:
    BASE[c] = ("date", "dimension", "ordinal")
for c in ["Long_Stay", "High_Severity", "Is_Uninsured", "Date_Corrected"]:
    BASE[c] = ("boolean", "dimension", "nominal")
for c in ["Age", "Length_of_Stay", "Admission_Month", "SeveritySort", "AgeSort", "StaySort", "WeekdaySort"]:
    BASE[c] = ("integer", "measure", "quantitative")
for c in ["Bill", "Bill_Per_Day"]:
    BASE[c] = ("real", "measure", "quantitative")
# integer fields also used as discrete dimensions (e.g. stay length on the x-axis)
DIM_INT = {"Length_of_Stay", "Admission_Month"}

# calculated fields: caption -> (internal name, datatype, role, type, formula, referenced base fields)
CALC = {
    "Admissions": ("Calculation_7000000000000001", "integer", "measure", "quantitative", "COUNT([Patient_ID])", ["Patient_ID"]),
    "Long-Stay Rate": ("Calculation_7000000000000002", "real", "measure", "quantitative", "AVG(IIF([Long_Stay],1,0))", ["Long_Stay"]),
    "High-Severity Share": ("Calculation_7000000000000003", "real", "measure", "quantitative", "AVG(IIF([High_Severity],1,0))", ["High_Severity"]),
    "Uninsured Rate": ("Calculation_7000000000000004", "real", "measure", "quantitative", "AVG(IIF([Is_Uninsured],1,0))", ["Is_Uninsured"]),
    "Billing Completeness": ("Calculation_7000000000000005", "real", "measure", "quantitative",
                             "COUNT([Bill]) / COUNT([Patient_ID])", ["Bill", "Patient_ID"]),
    "Review Flags": ("Calculation_7000000000000006", "integer", "measure", "quantitative",
                     "SUM(IIF(ISNULL([Review_Flag]),0,1))", ["Review_Flag"]),
    "% of Admissions (stay band)": ("Calculation_7000000000000007", "real", "measure", "quantitative",
                                    "COUNT([Patient_ID]) / MIN({ EXCLUDE [Stay_Band] : COUNT([Patient_ID]) })", ["Patient_ID", "Stay_Band"]),
    "% of Bed-Days (stay band)": ("Calculation_7000000000000008", "real", "measure", "quantitative",
                                  "SUM([Length_of_Stay]) / MIN({ EXCLUDE [Stay_Band] : SUM([Length_of_Stay]) })", ["Length_of_Stay", "Stay_Band"]),
    "% of Admissions (doctor)": ("Calculation_7000000000000009", "real", "measure", "quantitative",
                                 "COUNT([Patient_ID]) / MIN({ EXCLUDE [Doctor] : COUNT([Patient_ID]) })", ["Patient_ID", "Doctor"]),
    "% of Bed-Days (doctor)": ("Calculation_7000000000000010", "real", "measure", "quantitative",
                               "SUM([Length_of_Stay]) / MIN({ EXCLUDE [Doctor] : SUM([Length_of_Stay]) })", ["Length_of_Stay", "Doctor"]),
    "Severity Share within Diagnosis": ("Calculation_7000000000000011", "real", "measure", "quantitative",
                                        "COUNT([Patient_ID]) / MIN({ EXCLUDE [Severity] : COUNT([Patient_ID]) })", ["Patient_ID", "Severity"]),
    "Stay Class": ("Calculation_7000000000000012", "string", "dimension", "nominal",
                   "IIF([Long_Stay], 'Long stay (over 7 days)', 'Up to 7 days')", ["Long_Stay"]),
}


class Inst:
    """A field as used on a shelf: column-instance name + the underlying column."""

    def __init__(self, base, deriv, prefix, typ, suffix, caption=None):
        self.base, self.deriv, self.typ = base, deriv, typ
        self.name = f"[{prefix}:{base}:{suffix}]"
        self.ref = f"[{DS}].{self.name}"
        self.caption = caption or base

    def xml(self):
        return (f"<column-instance column={q('[' + self.base + ']')} derivation={q(self.deriv)} "
                f"name={q(self.name)} pivot='key' type={q(self.typ)} />")


def cname(caption):
    return CALC[caption][0]


def avg(f): return Inst(f, "Avg", "avg", "quantitative", "qk")
def sm(f): return Inst(f, "Sum", "sum", "quantitative", "qk")
def mn(f): return Inst(f, "Min", "min", "quantitative", "qk")
def cnt(f): return Inst(f, "Count", "cnt", "quantitative", "qk")
def dim(f): return Inst(f, "None", "none", "nominal", "nk")           # string / boolean dimension
def dim_o(f): return Inst(f, "None", "none", "ordinal", "ok")         # integer / date dimension (discrete)
def meas(f): return Inst(f, "None", "none", "quantitative", "qk")     # row-level measure
def calc_m(caption): return Inst(cname(caption), "User", "usr", "quantitative", "qk", caption)
def calc_d(caption): return Inst(cname(caption), "None", "none", "nominal", "nk", caption)


def base_column_xml(name):
    dt, role, typ = BASE[name]
    return f"<column datatype={q(dt)} name={q('[' + name + ']')} role={q(role)} type={q(typ)} />"


def calc_column_xml(caption):
    nm, dt, role, typ, formula, _ = CALC[caption]
    return (f"<column caption={q(caption)} datatype={q(dt)} name={q('[' + nm + ']')} role={q(role)} type={q(typ)}>"
            f"<calculation class='tableau' formula={q(formula)} /></column>")


# ---------------------------------------------------------------- shared (global) filters
GLOBAL_FILTERS = [("Quarter", dim("Admission_Quarter")), ("Doctor", dim("Doctor")), ("Diagnosis", dim("Diagnosis")),
                  ("Insurance", dim("Insurance")), ("Severity", dim("Severity")), ("Age group", dim("Age_Group"))]
TEST = {}   # {"Doctor": "Dr. Sara Ibrahim"} when --test is used


def global_filter_xml(k, label, inst):
    if label in TEST or inst.base in TEST:
        member = TEST.get(label, TEST.get(inst.base))
        gf = (f"<groupfilter function='member' level={q(inst.name)} member={q(chr(34) + member + chr(34))} "
              f"user:ui-domain='database' user:ui-enumeration='inclusive' user:ui-marker='enumerate' />")
    else:
        gf = f"<groupfilter function='level-members' level={q(inst.name)} user:ui-enumeration='all' user:ui-marker='enumerate' />"
    return f"<filter class='categorical' column={q(inst.ref)} filter-group={q(str(k + 2))}>{gf}</filter>"


# ---------------------------------------------------------------- worksheet builder
class Sheet:
    def __init__(self, name, rows=(), cols=(), mark="Automatic", color=None, text=None, lod=(), tooltip=(),
                 sorts=(), fixed_color=None, title=None, palette=None, fmt=None, pane_marks=None,
                 hide_axes=False, aggregate=True, null_excl=(), min_filters=(), label=None, no_labels=False):
        self.name, self.rows, self.cols, self.mark = name, list(rows), list(cols), mark
        self.color, self.text, self.lod, self.tooltip = color, text, list(lod), list(tooltip)
        self.sorts, self.fixed_color = list(sorts), fixed_color
        self.title = title or name
        self.palette = palette          # (Inst, {value: color})
        self.fmt = fmt or {}            # {Inst: format}
        self.pane_marks = pane_marks    # {index: (mark, color)} for multi-measure panes
        self.hide_axes, self.aggregate = hide_axes, aggregate
        self.null_excl = list(null_excl)   # dimension instances: exclude NULL
        self.label = label              # Inst shown as a mark label (bar value)
        self.min_filters = list(min_filters)   # [(Inst, min value)] quantitative range filters (also drop NULLs)
        self.no_labels = no_labels
        self.uuid = uid()

    def all_insts(self):
        out = list(self.rows) + list(self.cols)
        for e in [self.color, self.text, self.label] + self.lod + self.tooltip:
            if e is not None:
                out.append(e)
        for s in self.sorts:
            out.append(s[0]); out.append(s[2])
        out += self.null_excl
        out += [f[0] for f in self.min_filters]
        out += [g[1] for g in GLOBAL_FILTERS]
        if self.palette:
            out.append(self.palette[0])
        seen, uniq = set(), []
        for i in out:
            if i.name not in seen:
                seen.add(i.name); uniq.append(i)
        return uniq

    def shelf(self, items):
        if not items:
            return ""
        return items[0].ref if len(items) == 1 else "(" + " / ".join(i.ref for i in items) + ")"

    def xml(self):
        insts = self.all_insts()
        base_cols, calc_cols, seen_b, seen_c = [], [], set(), set()
        for i in insts:
            cap = next((k for k, v in CALC.items() if v[0] == i.base), None)
            if cap:
                if cap not in seen_c:
                    seen_c.add(cap); calc_cols.append(cap)
                    for r in CALC[cap][5]:
                        if r not in seen_b:
                            seen_b.add(r); base_cols.append(r)
            elif i.base not in seen_b:
                seen_b.add(i.base); base_cols.append(i.base)
        deps = "".join(base_column_xml(b) for b in base_cols) + "".join(calc_column_xml(c) for c in calc_cols) + \
               "".join(i.xml() for i in insts)
        filt, slices = "", ""
        for k, (label, inst) in enumerate(GLOBAL_FILTERS):
            filt += global_filter_xml(k, label, inst)
            slices += f"<column>{inst.ref}</column>"
        for inst in self.null_excl:
            filt += (f"<filter class='categorical' column={q(inst.ref)}><groupfilter function='except' user:ui-domain='database' "
                     f"user:ui-enumeration='exclusive' user:ui-marker='enumerate'><groupfilter function='level-members' level={q(inst.name)} />"
                     f"<groupfilter function='member' level={q(inst.name)} member='%null%' /></groupfilter></filter>")
            slices += f"<column>{inst.ref}</column>"
        for inst, lo in self.min_filters:
            filt += f"<filter class='quantitative' column={q(inst.ref)} included-values='in-range'><min>{lo}</min></filter>"
        slice_xml = f"<slices>{slices}</slices>" if slices else ""
        sorts = "".join(f"<sort class='computed' column={q(c.ref)} direction={q(d)} using={q(u.ref)} />" for c, d, u in self.sorts)

        measures = [i for i in (self.rows + self.cols) if i.typ == "quantitative"]
        axis_attr = "y-axis-name" if any(m in self.rows for m in measures) else "x-axis-name"
        n_panes = len(measures) if len(measures) > 1 else 1
        panes_xml = ""
        for idx in range(n_panes):
            mark, color = self.mark, self.fixed_color
            if self.pane_marks and idx in self.pane_marks:
                mark, color = self.pane_marks[idx]
            enc = ""
            if self.color is not None:
                enc += f"<color column={q(self.color.ref)} />"
            if self.text is not None:
                enc += f"<text column={q(self.text.ref)} />"
            lab = self.label if self.label is not None else (measures[idx] if n_panes > 1 else None)
            if lab is not None and self.text is None:
                enc += f"<text column={q(lab.ref)} />"
            for l in self.lod:
                enc += f"<lod column={q(l.ref)} />"
            for t in self.tooltip:
                enc += f"<tooltip column={q(t.ref)} />"
            mstyle = ""
            if color and self.color is None:
                mstyle += f"<format attr='mark-color' value={q(color)} />"
            if lab is not None and self.text is None:
                mstyle += "<format attr='mark-labels-show' value='true' /><format attr='mark-labels-cull' value='true' />"
            if self.text is not None and self.mark != "Text":
                mstyle += "<format attr='mark-labels-show' value='true' />"
            if self.no_labels:
                mstyle += "<format attr='mark-labels-show' value='false' />"
            if self.mark == "Text" and self.text is not None and not self.rows and not self.cols:
                style_xml = ("<style><style-rule element='cell'><format attr='text-align' value='center' />"
                             "<format attr='vertical-align' value='center' /></style-rule>"
                             "<style-rule element='label'><format attr='font-size' value='24' /><format attr='font-weight' value='bold' />"
                             f"<format attr='color' value='{INK}' /></style-rule></style>")
            else:
                style_xml = f"<style><style-rule element='mark'>{mstyle}</style-rule></style>" if mstyle else ""
            attrs = "selection-relaxation-option='selection-relaxation-allow'"
            if n_panes > 1:
                attrs += f" id={q(str(idx + 1))} {axis_attr}={q(measures[idx].ref)}"
            panes_xml += f"<pane {attrs}><view><breakdown value='auto' /></view><mark class={q(mark)} />"
            if enc:
                panes_xml += f"<encodings>{enc}</encodings>"
            panes_xml += style_xml + "</pane>"

        cell_style = "".join(f"<format attr='text-format' field={q(i.ref)} value={q(f)} />" for i, f in self.fmt.items())
        hide = "<style-rule element='axis'><format attr='display' value='false' /></style-rule>" if self.hide_axes else ""
        table_style = ("<style>" + (f"<style-rule element='cell'>{cell_style}</style-rule>" if cell_style else "") + hide + "</style>") \
            if (cell_style or hide) else "<style />"
        return (
            f"<worksheet name={q(self.name)}>"
            f"<layout-options><title><formatted-text><run fontsize='11' fontcolor='{INK}'>{escape(self.title)}</run></formatted-text></title></layout-options>"
            f"<table><view><datasources><datasource caption='Hospital' name={q(DS)} /></datasources>"
            f"<datasource-dependencies datasource={q(DS)}>{deps}</datasource-dependencies>"
            f"{filt}{sorts}{slice_xml}<aggregation value={q('true' if self.aggregate else 'false')} /></view>"
            f"{table_style}<panes>{panes_xml}</panes>"
            f"<rows>{self.shelf(self.rows)}</rows><cols>{self.shelf(self.cols)}</cols></table>"
            f"</worksheet>"
        )


# ---------------------------------------------------------------- sheets
SHEETS = []


def add(sheet):
    SHEETS.append(sheet)
    return sheet


def kpi(name, inst, fmt, title):
    return add(Sheet(name, mark="Text", text=inst, fmt={inst: fmt}, title=title, hide_axes=True))


ADM = calc_m("Admissions")
KPI_SHEETS = [
    kpi("KPI Admissions", ADM, "n#,##0", "Admissions"),
    kpi("KPI ALOS", avg("Length_of_Stay"), "n#,##0.0", "Avg length of stay (days)"),
    kpi("KPI Bed-Days", sm("Length_of_Stay"), "n#,##0", "Bed-days used"),
    kpi("KPI Long-Stay Rate", calc_m("Long-Stay Rate"), "p0.0%", "Long-stay rate (> 7 days)"),
    kpi("KPI High Severity", calc_m("High-Severity Share"), "p0.0%", "High-severity share"),
    kpi("KPI Uninsured", calc_m("Uninsured Rate"), "p0.0%", "Uninsured rate"),
    kpi("KPI Billing", calc_m("Billing Completeness"), "p0.0%", "Billing completeness"),
    kpi("KPI Review Flags", calc_m("Review Flags"), "n#,##0", "Records flagged for review"),
]
P0 = "p0%"
D1 = "n#,##0.0"

# Overview
add(Sheet("Admissions by Month", rows=[ADM], cols=[dim("Admission_Month_Name")], mark="Bar", fixed_color=BLUE, label=ADM,
          sorts=[(dim("Admission_Month_Name"), "ASC", mn("Admission_Month"))],
          title="Admissions by month (click a month to filter)"))
add(Sheet("Admissions by Weekday", rows=[ADM], cols=[dim("Admission_Weekday")], mark="Bar", fixed_color=BLUE, label=ADM,
          sorts=[(dim("Admission_Weekday"), "ASC", mn("WeekdaySort"))],
          title="Admissions by weekday (Friday-Saturday = weekend)"))
add(Sheet("Stay Length vs Bed-Days", rows=[calc_m("% of Admissions (stay band)"), calc_m("% of Bed-Days (stay band)")],
          cols=[dim("Stay_Band")], mark="Bar", pane_marks={0: ("Bar", BLUE), 1: ("Bar", ORANGE)},
          sorts=[(dim("Stay_Band"), "ASC", mn("StaySort"))],
          fmt={calc_m("% of Admissions (stay band)"): P0, calc_m("% of Bed-Days (stay band)"): P0},
          title="Share of admissions (blue) vs share of bed-days (orange) by stay length"))
add(Sheet("LOS Distribution", rows=[ADM], cols=[dim_o("Length_of_Stay")], mark="Bar", color=calc_d("Stay Class"),
          palette=(calc_d("Stay Class"), {"Up to 7 days": BLUE, "Long stay (over 7 days)": ORANGE}),
          title="Length-of-stay distribution: patients by days in hospital (orange = over 7 days)"))

# Case mix & LOS
add(Sheet("Admissions by Diagnosis", rows=[dim("Diagnosis")], cols=[ADM], mark="Bar", fixed_color=BLUE, label=ADM,
          sorts=[(dim("Diagnosis"), "DESC", ADM)], title="Admissions by diagnosis (click to filter)"))
add(Sheet("ALOS by Diagnosis", rows=[dim("Diagnosis")], cols=[avg("Length_of_Stay")], mark="Bar", fixed_color=BLUE,
          label=avg("Length_of_Stay"), fmt={avg("Length_of_Stay"): D1}, sorts=[(dim("Diagnosis"), "DESC", avg("Length_of_Stay"))],
          title="Average length of stay by diagnosis (days) - a cold stays longer than a stroke"))
add(Sheet("Severity Mix by Diagnosis", rows=[dim("Diagnosis")], cols=[dim("Severity")], mark="Square",
          color=calc_m("Severity Share within Diagnosis"), text=calc_m("Severity Share within Diagnosis"),
          fmt={calc_m("Severity Share within Diagnosis"): P0}, sorts=[(dim("Severity"), "ASC", mn("SeveritySort"))],
          title="Severity mix within each diagnosis (% of the row) - stroke mostly Low, cold mostly High"))
add(Sheet("ALOS by Age Group", rows=[avg("Length_of_Stay")], cols=[dim("Age_Group")], mark="Bar", fixed_color=ORD[2],
          label=avg("Length_of_Stay"), fmt={avg("Length_of_Stay"): D1}, sorts=[(dim("Age_Group"), "ASC", mn("AgeSort"))],
          title="Average stay by age group (days) - the one real driver"))
add(Sheet("ALOS by Severity", rows=[avg("Length_of_Stay")], cols=[dim("Severity")], mark="Bar", fixed_color=ORD[2],
          label=avg("Length_of_Stay"), fmt={avg("Length_of_Stay"): D1}, sorts=[(dim("Severity"), "ASC", mn("SeveritySort"))],
          title="Average stay by recorded severity (days) - almost flat"))
add(Sheet("Admissions by Insurance", rows=[dim("Insurance")], cols=[ADM], mark="Bar", fixed_color=BLUE, label=ADM,
          sorts=[(dim("Insurance"), "DESC", ADM)], title="Admissions by insurance (click to filter)"))

# Doctors & billing
add(Sheet("ALOS by Doctor", rows=[dim("Doctor")], cols=[avg("Length_of_Stay")], mark="Bar", fixed_color=BLUE,
          label=avg("Length_of_Stay"), fmt={avg("Length_of_Stay"): D1}, sorts=[(dim("Doctor"), "DESC", avg("Length_of_Stay"))],
          title="Average length of stay by doctor (days; click to filter)"))
add(Sheet("Doctor Workload", rows=[dim("Doctor")], cols=[calc_m("% of Admissions (doctor)"), calc_m("% of Bed-Days (doctor)")],
          mark="Bar", pane_marks={0: ("Bar", BLUE), 1: ("Bar", ORANGE)}, sorts=[(dim("Doctor"), "DESC", ADM)],
          fmt={calc_m("% of Admissions (doctor)"): P0, calc_m("% of Bed-Days (doctor)"): P0},
          title="Share of admissions (blue) vs share of bed-days (orange) by doctor"))
add(Sheet("Billing Status", rows=[dim("Bill_Status")], cols=[ADM], mark="Bar", color=dim("Bill_Status"), label=ADM,
          palette=(dim("Bill_Status"), {"Recorded": BLUE, "Placeholder 999": NEUTRAL, "Placeholder 3852": NEUTRAL2}),
          sorts=[(dim("Bill_Status"), "DESC", ADM)], title="Billing data quality: only 52 admissions have a genuine bill"))
add(Sheet("Bill vs Length of Stay", rows=[meas("Bill")], cols=[meas("Length_of_Stay")], mark="Circle", fixed_color=BLUE,
          lod=[dim("Patient_ID"), dim("Diagnosis")], aggregate=False, min_filters=[(meas("Bill"), 1)], no_labels=True,
          title="Genuine bill vs length of stay (placeholder bills excluded) - bills rise about 521 per day"))

# Review list
add(Sheet("Review List", rows=[dim("Review_Flag"), dim("Patient_ID"), dim("Diagnosis"), dim("Doctor"), dim("Severity")],
          mark="Text", text=sm("Length_of_Stay"), null_excl=[dim("Review_Flag")],
          title="Records flagged for clinical review - value = length of stay (days)", hide_axes=True))

# ---------------------------------------------------------------- dashboards
W = 1400
TITLE = "Hospital Performance 2023 - 247 admissions, 7 doctors, 10 diagnoses (cleaned data)"


def filter_row(anchor):
    return (52, [(233, "filter", (anchor, lab)) for lab, _ in GLOBAL_FILTERS[:5]] + [(235, "filter", (anchor, GLOBAL_FILTERS[5][0]))])


def title_row(text):
    return (44, [(W, "title", text)])


def note_row(text):
    return (26, [(W, "note", text)])


NOTE = "The six filters apply to every sheet on every dashboard. Click a bar to filter the rest of the dashboard; click it again to clear."
DASHBOARDS = {
    "Overview": [
        title_row(TITLE), filter_row("Admissions by Month"), note_row(NOTE),
        (95, [(175, "sheet", s.name) for s in KPI_SHEETS]),
        (190, [(W, "insights", None)]),
        (270, [(933, "sheet", "Admissions by Month"), (467, "sheet", "Admissions by Weekday")]),
        (270, [(700, "sheet", "Stay Length vs Bed-Days"), (700, "sheet", "LOS Distribution")]),
    ],
    "Case Mix & Length of Stay": [
        title_row("Case mix and length of stay: does stay length match how sick patients are?"), filter_row("Admissions by Diagnosis"), note_row(NOTE),
        (360, [(467, "sheet", "Admissions by Diagnosis"), (467, "sheet", "ALOS by Diagnosis"), (466, "sheet", "Severity Mix by Diagnosis")]),
        (300, [(467, "sheet", "ALOS by Age Group"), (467, "sheet", "ALOS by Severity"), (466, "sheet", "Admissions by Insurance")]),
    ],
    "Doctors & Billing": [
        title_row("Doctor performance and billing data quality"), filter_row("ALOS by Doctor"), note_row(NOTE),
        (330, [(700, "sheet", "ALOS by Doctor"), (700, "sheet", "Doctor Workload")]),
        (320, [(560, "sheet", "Billing Status"), (840, "sheet", "Bill vs Length of Stay")]),
    ],
    "Clinical Review": [
        title_row("Records flagged for clinical review (kept in the analysis)"), filter_row("Review List"), note_row(NOTE),
        (620, [(W, "sheet", "Review List")]),
    ],
}
ACTION_SOURCES = {
    "Overview": ["Admissions by Month", "Admissions by Weekday"],
    "Case Mix & Length of Stay": ["Admissions by Diagnosis", "ALOS by Diagnosis", "ALOS by Age Group", "ALOS by Severity", "Admissions by Insurance"],
    "Doctors & Billing": ["ALOS by Doctor", "Doctor Workload", "Billing Status"],
    "Clinical Review": [],
}


def insights_runs():
    S = json.load(open("analysis_summary.json", encoding="utf-8"))
    k, f = S["kpi"], S["findings"]
    items = [
        f"Long stays: stays of 15+ days are {k['stays_15plus'] / k['total_admissions']:.0%} of admissions but {k['bed_days_15plus_share']:.0%} of bed-days; "
        f"{f['minor_in_15plus']} of them are colds, flu, allergy or migraine.",
        f"Severity: high-severity patients stay {f['alos_high']} days vs {f['alos_low']} for low severity (no real difference, p = 0.91); "
        f"a common cold ({f['cold_alos']} d) stays longer than a stroke ({f['stroke_alos']} d) - severity coding needs an audit.",
        f"Age is the one real driver: children 4.7 days, seniors 7.1; seniors are {k['senior_share']:.0%} of admissions and {f['senior_bed_day_share']:.0%} of bed-days.",
        f"Billing: only {k['billing_completeness']:.0%} of admissions have a genuine bill (the rest are 999/3852 placeholders); none of the 28 longest stays is billed.",
        f"Demand: May is busiest (32 admissions, peak census {k['peak_census']}), August quietest (10); admissions cluster Tuesday-Wednesday and drop on Friday.",
    ]
    runs = "<run bold='true' fontsize='11' fontcolor='#1f3a5f'>Key insights (full year)</run><run>&#198;&#10;</run>"
    for it in items:
        runs += f"<run fontsize='9' fontcolor='{SOFT}'>{escape('- ' + it)}</run><run>&#198;&#10;</run>"
    return runs


def dashboard_xml(name, ROWS):
    H = sum(r[0] for r in ROWS)
    zid = [10]

    def nid():
        zid[0] += 1
        return zid[0]

    def u(v, total):
        return str(round(v / total * 100000))

    border = ("<zone-style><format attr='border-color' value='#e1e0d9' /><format attr='border-style' value='solid' />"
              "<format attr='border-width' value='1' /></zone-style>")
    zones, y = "", 0
    for h_px, cells in ROWS:
        x = 0
        for w_px, kind, payload in cells:
            geo = f"h={q(u(h_px, H))} w={q(u(w_px, W))} x={q(u(x, W))} y={q(u(y, H))}"
            if kind == "sheet":
                zones += f"<zone {geo} id={q(str(nid()))} name={q(payload)}>{border}</zone>"
            elif kind == "filter":
                sheet, label = payload
                inst = dict(GLOBAL_FILTERS)[label]
                zones += f"<zone {geo} id={q(str(nid()))} mode='dropdown' name={q(sheet)} param={q(inst.ref)} type-v2='filter' />"
            elif kind == "title":
                zones += (f"<zone {geo} id={q(str(nid()))} type-v2='text'><formatted-text><run bold='true' fontsize='15' "
                          f"fontcolor='{INK}'>{escape(payload)}</run></formatted-text></zone>")
            elif kind == "insights":
                zones += f"<zone {geo} id={q(str(nid()))} type-v2='text'><formatted-text>{insights_runs()}</formatted-text>{border}</zone>"
            elif kind == "note":
                zones += (f"<zone {geo} id={q(str(nid()))} type-v2='text'><formatted-text><run fontsize='9' "
                          f"fontcolor='{SOFT}'>{escape(payload)}</run></formatted-text></zone>")
            x += w_px
        y += h_px
    root = f"<zone h='100000' id='4' type-v2='layout-basic' w='100000' x='0' y='0'>{zones}</zone>"
    return (f"<dashboard name={q(name)}><style /><size sizing-mode='automatic' />"
            f"<datasources><datasource caption='Hospital' name={q(DS)} /></datasources>"
            f"<zones>{root}</zones></dashboard>")


def actions_xml():
    out, i = "", 0
    for dash, sources in ACTION_SOURCES.items():
        for src in sources:
            i += 1
            out += (f"<action caption={q(f'Filter {i} ({src})')} name={q(f'[Action{i}_{uuid.uuid4().hex[:16]}]')}>"
                    f"<activation auto-clear='true' type='on-select' />"
                    f"<source dashboard={q(dash)} type='sheet' worksheet={q(src)} />"
                    f"<command command='tsc:tsl-filter'><param name='special-fields' value='all' />"
                    f"<param name='target' value={q(dash)} /></command></action>")
    return f"<actions>{out}</actions>" if out else ""


def datasource_style():
    """Per-field colour assignments (Tableau stores them on the datasource, keyed by the field instance)."""
    seen, out = set(), ""
    for sh in SHEETS:
        if sh.palette and sh.palette[0].name not in seen:
            pf, pmap = sh.palette
            seen.add(pf.name)
            maps = "".join(f"<map to={q(c)}><bucket>{q(chr(34) + v + chr(34))[1:-1]}</bucket></map>" for v, c in pmap.items())
            out += f"<encoding attr='color' field={q(pf.name)} type='palette'>{maps}</encoding>"
    return f"<style><style-rule element='mark'>{out}</style-rule></style>" if out else ""


def palette_instances_xml():
    seen, out = set(), ""
    for sh in SHEETS:
        if sh.palette and sh.palette[0].name not in seen:
            seen.add(sh.palette[0].name)
            out += sh.palette[0].xml()
    return out


def datasource_xml():
    cols = "".join(base_column_xml(c) for c in BASE)
    cols += "".join(calc_column_xml(c) for c in CALC)
    return (
        f"<datasource caption='Hospital' inline='true' name={q(DS)} version='18.1'>"
        f"<connection class='federated'><named-connections><named-connection caption='Hospital' name={q(CONN)}>"
        f"<connection class='hyper' dbname='Data/Extracts/{HYPER}' default-settings='yes' schema='Extract' sslmode='' "
        f"tablename='Extract' username='' /></named-connection></named-connections>"
        f"<relation connection={q(CONN)} name='Extract' table='[Extract].[Extract]' type='table' /></connection>"
        f"<aliases enabled='yes' />{cols}{palette_instances_xml()}{datasource_style()}</datasource>"
    )


def windows_xml():
    cards = ("<cards><edge name='left'><strip size='160'><card type='pages' /><card type='filters' /><card type='marks' /></strip></edge>"
             "<edge name='top'><strip size='2147483647'><card type='columns' /></strip><strip size='2147483647'><card type='rows' /></strip>"
             "<strip size='31'><card type='title' /></strip></edge></cards>")
    out = "".join(f"<window class='worksheet' name={q(sh.name)}>{cards}</window>" for sh in SHEETS)
    for k, n in enumerate(DASHBOARDS):
        used = [p for _, cells in DASHBOARDS[n] for _, kind, p in cells if kind == "sheet"]
        vps = "".join((f"<viewpoint name={q(x)}><zoom type='entire-view' /></viewpoint>" if x != "Review List" else f"<viewpoint name={q(x)} />")
                      for x in used)
        maxi = " maximized='true'" if k == 0 else ""
        out += f"<window class='dashboard'{maxi} name={q(n)}><viewpoints>{vps}</viewpoints><active id='-1' /></window>"
    return f"<windows>{out}</windows>"


def build_twb():
    return (
        "<?xml version='1.0' encoding='utf-8' ?>\n"
        "<workbook original-version='18.1' source-build='2025.1.0 (20251.25.0422.1131)' source-platform='win' version='18.1' "
        "xmlns:user='http://www.tableausoftware.com/xml/user'>"
        "<preferences><preference name='ui.encoding.shelf.height' value='24' /><preference name='ui.shelf.height' value='26' /></preferences>"
        f"<datasources>{datasource_xml()}</datasources>"
        f"{actions_xml()}"
        f"<worksheets>{''.join(s.xml() for s in SHEETS)}</worksheets>"
        f"<dashboards>{''.join(dashboard_xml(n, r) for n, r in DASHBOARDS.items())}</dashboards>"
        f"{windows_xml()}"
        "</workbook>\n"
    )


def main():
    out = OUT
    if "--first" in sys.argv:
        first = sys.argv[sys.argv.index("--first") + 1]
        order = [first] + [n for n in DASHBOARDS if n != first]
        items = {n: DASHBOARDS[n] for n in order}
        DASHBOARDS.clear(); DASHBOARDS.update(items)
        out = "test_first.twbx"
    if "--test" in sys.argv:
        field, member = sys.argv[sys.argv.index("--test") + 1].split("=", 1)
        TEST[field] = member
        out = "test_filter.twbx"
    twb = build_twb()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr(TWB_NAME, twb)
        z.write(HYPER, f"Data/Extracts/{HYPER}")
    print(f"Wrote {out}: {len(SHEETS)} worksheets + {len(DASHBOARDS)} dashboards, {len(twb) / 1e3:.0f} KB of XML")


if __name__ == "__main__":
    main()
