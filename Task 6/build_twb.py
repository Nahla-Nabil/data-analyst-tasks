"""
Task 6 - builds Weather_Dashboard.twbx (Tableau packaged workbook) from Weather.hyper.

The .twb XML is generated here (no Tableau needed to run this script); Tableau Public / Desktop opens the result.
Contents: 8 KPI sheets, 16 chart sheets, one dashboard ("Weather Dashboard") with Year / Season quick filters and
click-to-filter actions on the month, season and wind-direction charts.
"""

import uuid
import zipfile
from xml.sax.saxutils import escape, quoteattr as q

HYPER = "Weather.hyper"
TWB_NAME = "Weather_Dashboard.twb"
OUT = "Weather_Dashboard.twbx"
DS = "federated.0k3v9x2b4t7w1e5r8y6u0i2o3p4a"
CONN = "hyper.1a2b3c4d5e6f7g8h9i0j1k2l3m4n"

# ---------------------------------------------------------------- palette (same as the HTML dashboard)
BLUE, ORANGE, AQUA, YELLOW, BAD, NEUTRAL, INK = "#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#b5322f", "#a9bccd", "#1c3d5a"
SEASON_COLORS = {"Summer": ORANGE, "Autumn": YELLOW, "Winter": BLUE, "Spring": AQUA}


def uid():
    return "{" + str(uuid.uuid4()).upper() + "}"


# ---------------------------------------------------------------- field catalogue
# name -> (datatype, role, type)
BASE = {}
for c in ["Season", "MonthName", "YearMonth", "WindGustDir", "WindDir9am", "WindDir3pm", "RainToday", "RainTomorrow",
          "RainCategory", "HeatCategory", "GustCategory", "AnomalyType"]:
    BASE[c] = ("string", "dimension", "nominal")
for c in ["Year", "Month", "Quarter", "DayOfYear"]:
    BASE[c] = ("integer", "dimension", "ordinal")
BASE["Date"] = ("date", "dimension", "ordinal")
BASE["MonthStart"] = ("date", "dimension", "ordinal")
for c in ["IsRainDay", "RainToday_Flag", "RainTomorrow_Flag", "IsAnomaly", "WindGustSpeed", "WindSpeed9am", "WindSpeed3pm",
          "Humidity9am", "Humidity3pm", "Cloud9am", "Cloud3pm", "SeasonSort", "DirSort"]:
    BASE[c] = ("integer", "measure", "quantitative")
for c in ["MinTemp", "MaxTemp", "Rainfall", "Sunshine", "Evaporation", "Pressure9am", "Pressure3pm", "MeanTemp", "TempRange",
          "MaxTemp_Z"]:
    BASE[c] = ("real", "measure", "quantitative")

# calculated fields: caption -> (internal name, datatype, role, type, formula, referenced base fields)
CALC = {
    "Rain Day %": ("Calculation_1000000000000001", "real", "measure", "quantitative", "AVG([IsRainDay])", ["IsRainDay"]),
    "Rain Tomorrow %": ("Calculation_1000000000000002", "real", "measure", "quantitative", "AVG([RainTomorrow_Flag])", ["RainTomorrow_Flag"]),
    "Rain Today %": ("Calculation_1000000000000003", "real", "measure", "quantitative", "AVG([IsRainDay])", ["IsRainDay"]),
    "Hot Days (max >= 30C)": ("Calculation_1000000000000004", "integer", "measure", "quantitative",
                              "SUM(IF [MaxTemp] >= 30 THEN 1 ELSE 0 END)", ["MaxTemp"]),
    "Max Temp Anomaly (vs same month)": ("Calculation_1000000000000005", "real", "measure", "quantitative",
                                         "AVG([MaxTemp]) - AVG({ FIXED [Month] : AVG([MaxTemp]) })", ["MaxTemp", "Month"]),
    "Share of Total Rainfall": ("Calculation_1000000000000006", "real", "measure", "quantitative",
                                "SUM([Rainfall]) / SUM({ FIXED : SUM([Rainfall]) })", ["Rainfall"]),
    "Share of Days": ("Calculation_1000000000000007", "real", "measure", "quantitative",
                      "COUNT([Date]) / SUM({ FIXED : COUNT([Date]) })", ["Date"]),
    "3pm Humidity Band": ("Calculation_1000000000000008", "string", "dimension", "nominal",
                          "IF [Humidity3pm] < 40 THEN '1  under 40%' ELSEIF [Humidity3pm] < 55 THEN '2  40-55%' "
                          "ELSEIF [Humidity3pm] < 70 THEN '3  55-70%' ELSEIF [Humidity3pm] < 85 THEN '4  70-85%' "
                          "ELSE '5  85% and over' END", ["Humidity3pm"]),
    "Rain Class": ("Calculation_1000000000000009", "string", "dimension", "nominal",
                   "IF [Rainfall] <= 1 THEN '1  Dry (<=1 mm)' ELSEIF [Rainfall] <= 10 THEN '2  Light (1-10)' "
                   "ELSEIF [Rainfall] <= 25 THEN '3  Moderate (10-25)' ELSEIF [Rainfall] <= 50 THEN '4  Heavy (25-50)' "
                   "ELSE '5  Very heavy (>50)' END", ["Rainfall"]),
    "Heat Anomaly?": ("Calculation_1000000000000010", "string", "dimension", "nominal",
                      "IF CONTAINS([AnomalyType], 'Heat') THEN 'Heat anomaly' ELSE 'Normal' END", ["AnomalyType"]),
    "Extreme Rain?": ("Calculation_1000000000000011", "string", "dimension", "nominal",
                      "IF CONTAINS([AnomalyType], 'Extreme rain') THEN 'Extreme rain' ELSE 'Normal' END", ["AnomalyType"]),
    "Is Anomaly?": ("Calculation_1000000000000013", "boolean", "dimension", "nominal", "[IsAnomaly] = 1", ["IsAnomaly"]),
    "Anomaly Days": ("Calculation_1000000000000012", "integer", "measure", "quantitative", "SUM([IsAnomaly])", ["IsAnomaly"]),
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


# instance constructors
def avg(f): return Inst(f, "Avg", "avg", "quantitative", "qk")
def sm(f): return Inst(f, "Sum", "sum", "quantitative", "qk")
def mn(f): return Inst(f, "Min", "min", "quantitative", "qk")
def mx(f): return Inst(f, "Max", "max", "quantitative", "qk")
def cnt(f): return Inst(f, "Count", "cnt", "quantitative", "qk")
def dim(f): return Inst(f, "None", "none", "nominal", "nk")           # string dimension
def dim_o(f): return Inst(f, "None", "none", "ordinal", "ok")         # integer / date dimension (discrete)
def meas(f): return Inst(f, "None", "none", "quantitative", "qk")     # un-aggregated (row-level) measure
def month_trunc(f): return Inst(f, "Month-Trunc", "tmn", "quantitative", "qk")
def day_trunc(f): return Inst(f, "Day-Trunc", "tdy", "quantitative", "qk")
def calc_m(caption): return Inst(cname(caption), "User", "usr", "quantitative", "qk", caption)   # aggregated calc measure
def calc_d(caption): return Inst(cname(caption), "None", "none", "nominal", "nk", caption)        # row-level calc dimension


def base_column_xml(name):
    dt, role, typ = BASE[name]
    return f"<column datatype={q(dt)} name={q('[' + name + ']')} role={q(role)} type={q(typ)} />"


def calc_column_xml(caption, include_caption=True):
    nm, dt, role, typ, formula, _ = CALC[caption]
    cap = f" caption={q(caption)}" if include_caption else ""
    return (f"<column{cap} datatype={q(dt)} name={q('[' + nm + ']')} role={q(role)} type={q(typ)}>"
            f"<calculation class='tableau' formula={q(formula)} /></column>")


# ---------------------------------------------------------------- worksheet builder
GLOBAL_FILTERS = [("Year", dim_o("Year")), ("Season", dim("Season"))]


class Sheet:
    def __init__(self, name, rows=(), cols=(), mark="Automatic", color=None, text=None, size=None, lod=(), tooltip=(),
                 sorts=(), extra_filters=(), fixed_color=None, title=None, palette=None, fmt=None, pane_marks=None,
                 hide_axes=False, global_filters=True, aggregate=True, diverging=None, cat_filters=(), null_excl=()):
        self.name, self.rows, self.cols, self.mark = name, list(rows), list(cols), mark
        self.color, self.text, self.size, self.lod, self.tooltip = color, text, size, list(lod), list(tooltip)
        self.sorts, self.extra_filters, self.fixed_color = list(sorts), list(extra_filters), fixed_color
        self.title = title or name
        self.palette = palette      # (Inst, {value: color})
        self.fmt = fmt or {}        # {Inst: 'p0.0%'}
        self.pane_marks = pane_marks  # optional {index: (mark, color)} for multi-measure panes
        self.hide_axes = hide_axes
        self.global_filters = global_filters
        self.aggregate = aggregate
        self.cat_filters = list(cat_filters)
        self.null_excl = list(null_excl)
        self.diverging = diverging
        self.uuid = uid()

    # every Inst that appears anywhere on the sheet
    def all_insts(self):
        out = list(self.rows) + list(self.cols)
        for e in [self.color, self.text, self.size] + self.lod + self.tooltip:
            if e is not None:
                out.append(e)
        for s in self.sorts:
            out.append(s[0]); out.append(s[2])
        for f in self.extra_filters:
            out.append(f[0])
        for f in self.cat_filters:
            out.append(f[0])
        for f in self.null_excl:
            out.append(f)
        if self.global_filters:
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
            b = i.base
            cap = next((k for k, v in CALC.items() if v[0] == b), None)
            if cap:
                if cap not in seen_c:
                    seen_c.add(cap); calc_cols.append(cap)
                    for r in CALC[cap][5]:
                        if r not in seen_b:
                            seen_b.add(r); base_cols.append(r)
            elif b not in seen_b:
                seen_b.add(b); base_cols.append(b)
        deps = "".join(base_column_xml(b) for b in base_cols) + "".join(calc_column_xml(c) for c in calc_cols) + \
               "".join(i.xml() for i in insts)
        filt = ""
        slices = ""
        if self.global_filters:
            for _, inst in GLOBAL_FILTERS:
                filt += (f"<filter class='categorical' column={q(inst.ref)}><groupfilter function='level-members' "
                         f"level={q(inst.name)} user:ui-enumeration='all' user:ui-marker='enumerate' /></filter>")
                slices += f"<column>{inst.ref}</column>"
        for inst, lo in self.extra_filters:
            filt += f"<filter class='quantitative' column={q(inst.ref)} included-values='in-range'><min>{lo}</min></filter>"
        for inst, member in self.cat_filters:
            filt += (f"<filter class='categorical' column={q(inst.ref)}><groupfilter function='member' level={q(inst.name)} "
                     f"member={q(member)} user:ui-domain='database' user:ui-enumeration='inclusive' user:ui-marker='enumerate' /></filter>")
            slices += f"<column>{inst.ref}</column>"
        for inst in self.null_excl:
            filt += (f"<filter class='categorical' column={q(inst.ref)}><groupfilter function='except' user:ui-domain='database' "
                     f"user:ui-enumeration='exclusive' user:ui-marker='enumerate'><groupfilter function='level-members' level={q(inst.name)} />"
                     f"<groupfilter function='member' level={q(inst.name)} member='%null%' /></groupfilter></filter>")
            slices += f"<column>{inst.ref}</column>"
        slice_xml = f"<slices>{slices}</slices>" if slices else ""
        sorts = "".join(f"<sort class='computed' column={q(c.ref)} direction={q(d)} using={q(u.ref)} />" for c, d, u in self.sorts)

        # panes: one per measure when several measures share a shelf
        measures = [i for i in (self.rows + self.cols) if i.typ == "quantitative" and i.deriv not in ("Month-Trunc", "Day-Trunc")]
        axis_attr = "y-axis-name" if any(m in self.rows for m in measures) else "x-axis-name"
        panes_xml = ""
        enc_style = ""
        n_panes = max(1, len(measures)) if len(measures) > 1 else 1
        for idx in range(n_panes):
            mark = self.mark
            color = self.fixed_color
            if self.pane_marks and idx in self.pane_marks:
                mark, color = self.pane_marks[idx]
            enc = ""
            if self.color is not None:
                enc += f"<color column={q(self.color.ref)} />"
            if self.size is not None:
                enc += f"<size column={q(self.size.ref)} />"
            if self.text is not None:
                enc += f"<text column={q(self.text.ref)} />"
            for l in self.lod:
                enc += f"<lod column={q(l.ref)} />"
            for t in self.tooltip:
                enc += f"<tooltip column={q(t.ref)} />"
            style = ""
            if color and self.color is None:
                style += f"<format attr='mark-color' value={q(color)} />"
            pass
            if self.mark == "Text" and self.text is not None and not self.rows and not self.cols:
                style_xml = ("<style><style-rule element='cell'><format attr='text-align' value='center' />"
                             "<format attr='vertical-align' value='center' /></style-rule>"
                             "<style-rule element='label'><format attr='font-size' value='26' /><format attr='font-weight' value='bold' />"
                             f"<format attr='color' value='{INK}' /></style-rule></style>")
            else:
                style_xml = f"<style><style-rule element='mark'>{style}</style-rule></style>" if style else ""
            attrs = "selection-relaxation-option='selection-relaxation-allow'"
            if n_panes > 1:
                attrs += f" id={q(str(idx + 1))} {axis_attr}={q(measures[idx].ref)}"
            panes_xml += f"<pane {attrs}><view><breakdown value='auto' /></view><mark class={q(mark)} />"
            if enc:
                panes_xml += f"<encodings>{enc}</encodings>"
            panes_xml += style_xml + "</pane>"

        cell_style = ""
        for inst, f in self.fmt.items():
            cell_style += f"<format attr='text-format' field={q(inst.ref)} value={q(f)} />"
        hide = ""
        if self.hide_axes:
            hide = ("<style-rule element='axis'><format attr='display' value='false' /></style-rule>")
        table_style = ""
        if cell_style or hide or enc_style:
            table_style = ("<style>" + (f"<style-rule element='cell'>{cell_style}</style-rule>" if cell_style else "") + hide
                           + (f"<style-rule element='mark'>{enc_style}</style-rule>" if enc_style else "") + "</style>")
        else:
            table_style = "<style />"
        return (
            f"<worksheet name={q(self.name)}>"
            f"<layout-options><title><formatted-text><run fontsize='11' fontcolor='{INK}'>{escape(self.title)}</run></formatted-text></title></layout-options>"
            f"<table><view><datasources><datasource caption='Weather' name={q(DS)} /></datasources>"
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


# KPI sheets (text marks)
def kpi(name, inst, fmt=None, title=None):
    return add(Sheet(name, mark="Text", text=inst, fmt={inst: fmt} if fmt else None, title=title or name, hide_axes=True))


KPI_SHEETS = [
    kpi("KPI Avg Max Temp", avg("MaxTemp"), "n#,##0.0", "Avg max temp (°C)"),
    kpi("KPI Avg Min Temp", avg("MinTemp"), "n#,##0.0", "Avg min temp (°C)"),
    kpi("KPI Avg Humidity 3pm", avg("Humidity3pm"), "n#,##0", "Avg humidity 3pm (%)"),
    kpi("KPI Avg Gust", avg("WindGustSpeed"), "n#,##0.0", "Avg wind gust (km/h)"),
    kpi("KPI Total Rainfall", sm("Rainfall"), "n#,##0", "Total rainfall (mm)"),
    kpi("KPI Rain Day", calc_m("Rain Day %"), "p0.0%", "Rain days (> 1 mm)"),
    kpi("KPI Hot Days", calc_m("Hot Days (max >= 30C)"), "n#,##0", "Hot days (max >= 30 °C)"),
    kpi("KPI Anomaly Days", calc_m("Anomaly Days"), "n#,##0", "Anomalous days"),
]

# 1 Temperature
add(Sheet("Monthly Temp", rows=[avg("MaxTemp"), avg("MinTemp")], cols=[month_trunc("Date")], mark="Line",
          pane_marks={0: ("Line", ORANGE), 1: ("Line", BLUE)}, title="Monthly average max (orange) / min (blue) temperature (°C)"))
add(Sheet("Seasonal Cycle", rows=[avg("MaxTemp"), avg("MinTemp")], cols=[dim_o("Month")], mark="Bar",
          pane_marks={0: ("Bar", ORANGE), 1: ("Bar", BLUE)}, title="Seasonal cycle by month (click a month to filter): max orange, min blue"))
add(Sheet("Temp by Season", rows=[avg("MaxTemp")], cols=[dim("Season")], mark="Bar", fixed_color=BLUE,
          sorts=[(dim("Season"), "ASC", mn("SeasonSort"))],
          title="Average daily max temperature by season (click to filter)"))
add(Sheet("Temp Anomaly Heatmap", rows=[dim_o("Year")], cols=[dim_o("Month")], mark="Square", color=calc_m("Max Temp Anomaly (vs same month)"),
          text=calc_m("Max Temp Anomaly (vs same month)"), fmt={calc_m("Max Temp Anomaly (vs same month)"): "n+0.0;-0.0"},
          title="Max-temperature anomaly by month and year, °C vs that month's average: green = cooler than usual, orange/red = hotter", diverging=calc_m("Max Temp Anomaly (vs same month)")))

# 2 Humidity
add(Sheet("Humidity by Month", rows=[avg("Humidity9am"), avg("Humidity3pm")], cols=[dim_o("Month")], mark="Bar",
          pane_marks={0: ("Bar", BLUE), 1: ("Bar", AQUA)}, title="Average humidity by month: 9am blue, 3pm green (%)"))
add(Sheet("Rain vs Humidity", rows=[calc_m("Rain Today %"), calc_m("Rain Tomorrow %")], cols=[calc_d("3pm Humidity Band")], mark="Bar",
          pane_marks={0: ("Bar", NEUTRAL), 1: ("Bar", BLUE)}, fmt={calc_m("Rain Today %"): "p0%", calc_m("Rain Tomorrow %"): "p0%"},
          title="Chance of rain by 3pm humidity band: today grey, tomorrow blue"))

# 3 Wind
add(Sheet("Gust Direction Frequency", rows=[cnt("Date")], cols=[dim("WindGustDir")], mark="Bar", fixed_color=BLUE,
          sorts=[(dim("WindGustDir"), "ASC", mn("DirSort"))], extra_filters=[(mn("DirSort"), 1)],
          title="How often gusts come from each direction (days; click to filter)"))
add(Sheet("Rain by Gust Direction", rows=[dim("WindGustDir")], cols=[calc_m("Rain Day %")], mark="Bar", fixed_color=BLUE,
          sorts=[(dim("WindGustDir"), "DESC", calc_m("Rain Day %"))], extra_filters=[(mn("DirSort"), 1)], fmt={calc_m("Rain Day %"): "p0%"},
          title="Share of days with rain, by gust direction (S/SE sector is wettest)"))
add(Sheet("Wind Speed by Month", rows=[avg("WindGustSpeed"), avg("WindSpeed3pm"), avg("WindSpeed9am")], cols=[dim_o("Month")], mark="Line",
          pane_marks={0: ("Line", ORANGE), 1: ("Line", BLUE), 2: ("Line", AQUA)}, title="Wind speed by month (km/h): gust orange, 3pm blue, 9am green"))

# 4 Rainfall
add(Sheet("Monthly Rainfall", rows=[sm("Rainfall")], cols=[month_trunc("Date")], mark="Bar", fixed_color=BLUE,
          title="Monthly rainfall total (mm); months with no data are blank"))
add(Sheet("Rain Days by Month", rows=[calc_m("Rain Day %")], cols=[dim_o("Month")], mark="Bar", fixed_color=BLUE,
          fmt={calc_m("Rain Day %"): "p0%"}, title="Share of days with rain, by month (click to filter)"))
add(Sheet("Rain Intensity", rows=[calc_m("Share of Days"), calc_m("Share of Total Rainfall")], cols=[calc_d("Rain Class")], mark="Bar",
          pane_marks={0: ("Bar", NEUTRAL), 1: ("Bar", BLUE)}, fmt={calc_m("Share of Days"): "p0%", calc_m("Share of Total Rainfall"): "p0%"},
          title="Rain intensity: share of days (grey) vs share of all rainfall (blue)"))

# 5 Unusual patterns
add(Sheet("Daily Max Temp", rows=[meas("MaxTemp")], cols=[day_trunc("Date")], mark="Circle", color=calc_d("Heat Anomaly?"),
          palette=(calc_d("Heat Anomaly?"), {"Heat anomaly": BAD, "Normal": ORANGE}), lod=[dim("AnomalyType")], aggregate=False,
          title="Daily max temperature (°C): blue dots = unusually hot for the month (z >= 3), orange = normal"))
add(Sheet("Daily Rainfall", rows=[meas("Rainfall")], cols=[day_trunc("Date")], mark="Circle", color=calc_d("Extreme Rain?"),
          palette=(calc_d("Extreme Rain?"), {"Extreme rain": BAD, "Normal": BLUE}), lod=[dim("AnomalyType")], aggregate=False,
          title="Daily rainfall (mm): blue dots = extreme rain days (above 53 mm), orange = other days"))
add(Sheet("Anomalies by Year", rows=[calc_m("Anomaly Days")], cols=[dim_o("Year")], mark="Bar", fixed_color=BAD,
          title="Anomalous days per year (2008 and 2017 are partial years)"))
add(Sheet("Unusual Days", rows=[dim_o("Date"), dim("AnomalyType")], mark="Text", text=meas("MaxTemp"),
          lod=[meas("Rainfall"), meas("WindGustSpeed")], null_excl=[dim("AnomalyType")], aggregate=False,
          title="Most unusual days (max temp °C; hover for rain and gust)", hide_axes=True))

# ---------------------------------------------------------------- dashboard layout
W = 1400
TITLE_TXT = "Weather Patterns - single station, 1 Feb 2008 to 25 Jun 2017 (see DATA_QUALITY_REPORT.md for caveats)"
def filter_row(anchor):
    return (52, [(300, "filter", (anchor, "Year")), (300, "filter", (anchor, "Season")),
                 (800, "note", "Year and Season filter every sheet on every dashboard. Click a month, season or wind direction to cross-filter.")])


def title_row(text):
    return (48, [(W, "title", text)])


DASHBOARDS = {
    "Overview": [
        title_row(TITLE_TXT), filter_row("Monthly Temp"),
        (95, [(175, "sheet", s.name) for s in KPI_SHEETS]),
        (215, [(W, "insights", None)]),
        (250, [(W, "sheet", "Monthly Temp")]),
        (245, [(700, "sheet", "Seasonal Cycle"), (700, "sheet", "Temp by Season")]),
    ],
    "Temperature and Humidity": [
        title_row("Temperature and humidity"), filter_row("Temp Anomaly Heatmap"),
        (400, [(1150, "sheet", "Temp Anomaly Heatmap"), (250, "legend", "Temp Anomaly Heatmap")]),
        (350, [(700, "sheet", "Humidity by Month"), (700, "sheet", "Rain vs Humidity")]),
    ],
    "Wind and Rainfall": [
        title_row("Wind and rainfall"), filter_row("Gust Direction Frequency"),
        (300, [(467, "sheet", "Gust Direction Frequency"), (467, "sheet", "Rain by Gust Direction"), (466, "sheet", "Wind Speed by Month")]),
        (220, [(W, "sheet", "Monthly Rainfall")]),
        (250, [(700, "sheet", "Rain Days by Month"), (700, "sheet", "Rain Intensity")]),
    ],
    "Unusual Events": [
        title_row("Unusual patterns and events"), filter_row("Daily Max Temp"),
        (215, [(W, "sheet", "Daily Max Temp")]),
        (215, [(W, "sheet", "Daily Rainfall")]),
        (320, [(600, "sheet", "Anomalies by Year"), (800, "sheet", "Unusual Days")]),
    ],
}
DASHBOARDS["Lab"] = [
    (300, [(700, "sheet", "Temp by Season"), (700, "sheet", "Rain Intensity")]),
    (300, [(700, "sheet", "Anomalies by Year"), (700, "sheet", "Unusual Days")]),
    (240, [(W, "sheet", "KPI Avg Max Temp")]),
]
HEAT_REF = f"[{DS}].[usr:Calculation_1000000000000005:qk]"
ONLY = None   # set by --only for screenshot testing


def active_dashboards():
    return [n for n in DASHBOARDS if (n == ONLY) or (ONLY is None and n != "Lab")]


def insights_runs():
    import json
    S = json.load(open("analysis_summary.json", encoding="utf-8"))
    mon, sea = S["monthly"], dict(zip(S["seasonal"]["Season"], S["seasonal"]["max_t"]))
    two = S["two_day_top"][0]
    hb = S["rain_by_humidity_band"]
    items = [
        f"Temperature: average daily maximum runs from {mon['max_t'][6]:.1f} °C in July to {mon['max_t'][0]:.1f} °C in January; summer {sea['Summer']:.1f} °C vs winter {sea['Winter']:.1f} °C.",
        f"Rainfall: {S['rain_day_pct']}% of days are rain days in every season (no dry season), but {S['heavy_plus_days_pct']}% of days (>25 mm) deliver {S['heavy_plus_mm_share_pct']}% of all rain.",
        f"Wind: gusts from the S/SE sector come with rain on {S['se_sector_rain_day_pct']}% of days vs {S['other_sector_rain_day_pct']}% for other directions (gust data start Oct 2010; earlier values were placeholders and are blank).",
        f"Forecasting: chance of rain tomorrow is {hb['[0, 40)'][1]:.0f}% when 3pm humidity is under 40% but {hb['[85, 101)'][1]:.0f}% at 85%+; the rule '3pm humidity >= 70% means rain tomorrow' is right {S['rule_hum70_accuracy_pct']}% of the time.",
        f"Unusual: {S['anomaly_days']} anomalous days ({S['anomaly_days'] / S['days'] * 100:.1f}%); hottest 45.8 °C on 18 Jan 2013; wettest spell {two['mm']:.0f} mm in two days from {two['date']}.",
        f"Change: month-matched, 2013-17 maximums were about +{S['max_temp_diff_month_matched']:.1f} °C above 2008-12 - a step around 2013, not proof of a trend (nine years only).",
    ]
    runs = "<run bold='true' fontsize='11' fontcolor='#123456'>Key insights (full record)</run><run>&#198;&#10;</run>"
    for it in items:
        runs += f"<run fontsize='9' fontcolor='{INK}'>{escape('- ' + it)}</run><run>&#198;&#10;</run>"
    return runs


def dashboard_xml(name, ROWS):
    H = sum(r[0] for r in ROWS)
    zid = [10]

    def nid():
        zid[0] += 1
        return zid[0]

    def u(v, total):
        return str(round(v / total * 100000))

    border = "<zone-style><format attr='border-color' value='#c7dcf0' /><format attr='border-style' value='solid' /><format attr='border-width' value='1' /></zone-style>"
    zones = ""
    y = 0
    for h_px, cells in ROWS:
        x = 0
        for w_px, kind, payload in cells:
            geo = f"h={q(u(h_px, H))} w={q(u(w_px, W))} x={q(u(x, W))} y={q(u(y, H))}"
            if kind == "sheet":
                zones += f"<zone {geo} id={q(str(nid()))} name={q(payload)}>{border}</zone>"
            elif kind == "filter":
                sheet, field = payload
                inst = dict(GLOBAL_FILTERS)[field]
                zones += f"<zone {geo} id={q(str(nid()))} mode='dropdown' name={q(sheet)} param={q(inst.ref)} type-v2='filter' />"
            elif kind == "legend":
                zones += f"<zone {geo} id={q(str(nid()))} name={q(payload)} param={q(HEAT_REF)} type-v2='color' />"
            elif kind == "title":
                zones += (f"<zone {geo} id={q(str(nid()))} type-v2='text'><formatted-text><run bold='true' fontsize='16' "
                          f"fontcolor='#123456'>{escape(payload)}</run></formatted-text></zone>")
            elif kind == "insights":
                zones += f"<zone {geo} id={q(str(nid()))} type-v2='text'><formatted-text>{insights_runs()}</formatted-text>{border}</zone>"
            elif kind == "note":
                zones += (f"<zone {geo} id={q(str(nid()))} type-v2='text'><formatted-text><run fontsize='9' "
                          f"fontcolor='#4d6e8c'>{escape(payload)}</run></formatted-text></zone>")
            else:
                zones += f"<zone {geo} id={q(str(nid()))} type-v2='empty' />"
            x += w_px
        y += h_px
    root = f"<zone h='100000' id='4' type-v2='layout-basic' w='100000' x='0' y='0'>{zones}</zone>"
    return (f"<dashboard name={q(name)}><style />"
            f"<size sizing-mode='automatic' />"
            f"<datasources><datasource caption='Weather' name={q(DS)} /></datasources>"
            f"<zones>{root}</zones></dashboard>")


def dashboards_xml():
    return "".join(dashboard_xml(n, DASHBOARDS[n]) for n in active_dashboards())


ACTION_SOURCES = {
    "Overview": ["Seasonal Cycle", "Temp by Season"],
    "Wind and Rainfall": ["Gust Direction Frequency", "Rain by Gust Direction", "Rain Days by Month"],
    "Temperature and Humidity": [],
    "Unusual Events": [],
}


def actions_xml():
    out, i = "", 0
    for dash, sources in ACTION_SOURCES.items():
        if dash not in active_dashboards():
            continue
        for src in sources:
            i += 1
            out += (f"<action caption={q(f'Filter {i} ({src})')} name={q(f'[Action{i}_{uuid.uuid4().hex[:16]}]')}>"
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
        if sh.diverging is not None and sh.diverging.name not in seen:
            seen.add(sh.diverging.name)
            out += f"<encoding attr='color' center='0' field={q(sh.diverging.name)} palette='tableau-map-temperatur' type='interpolated' />"
    return f"<style><style-rule element='mark'>{out}</style-rule></style>" if out else ""


def datasource_xml():
    cols = "".join(base_column_xml(c) for c in ["Year", "Month", "Quarter", "DayOfYear", "Date", "MonthStart"])
    cols += "".join(calc_column_xml(c) for c in CALC)
    return (
        f"<datasource caption='Weather' inline='true' name={q(DS)} version='18.1'>"
        f"<connection class='federated'><named-connections><named-connection caption='Weather' name={q(CONN)}>"
        f"<connection class='hyper' dbname='Data/Extracts/{HYPER}' default-settings='yes' schema='Extract' sslmode='' "
        f"tablename='Extract' username='' /></named-connection></named-connections>"
        f"<relation connection={q(CONN)} name='Extract' table='[Extract].[Extract]' type='table' /></connection>"
        f"<aliases enabled='yes' />{cols}{datasource_style()}</datasource>"
    )


def windows_xml():
    cards = ("<cards><edge name='left'><strip size='160'><card type='pages' /><card type='filters' /><card type='marks' /></strip></edge>"
             "<edge name='top'><strip size='2147483647'><card type='columns' /></strip><strip size='2147483647'><card type='rows' /></strip>"
             "<strip size='31'><card type='title' /></strip></edge></cards>")
    out = ""
    for sh in SHEETS:
        out += f"<window class='worksheet' name={q(sh.name)}>{cards}</window>"
    for k, n in enumerate(active_dashboards()):
        used = []
        for _, cells in DASHBOARDS[n]:
            used += [p for _, kind, p in cells if kind == "sheet"]
        vps = "".join((f"<viewpoint name={q(x)}><zoom type='entire-view' /></viewpoint>" if x != "Unusual Days" else f"<viewpoint name={q(x)} />")
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
        f"<dashboards>{dashboards_xml()}</dashboards>"
        f"{windows_xml()}"
        "</workbook>\n"
    )


def main():
    global ONLY
    import sys
    if "--only" in sys.argv:
        ONLY = sys.argv[sys.argv.index("--only") + 1]
    twb = build_twb()
    with open(TWB_NAME, "w", encoding="utf-8") as f:
        f.write(twb)
    out = OUT if ONLY is None else f"test_{ONLY.replace(' ', '_')}.twbx"
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr(TWB_NAME, twb)
        z.write(HYPER, f"Data/Extracts/{HYPER}")
    print(f"Wrote {out}: {len(SHEETS)} worksheets + {len(active_dashboards())} dashboard(s), {len(twb) / 1e3:.0f} KB of XML")


if __name__ == "__main__":
    main()
