"""Step 5b: open Airbnb_Base.xlsx in Excel (COM) and add the interactive layer.

Run from the repo root:  python "Task 12/build_excel_dashboard.py"
Output: Task 12/Airbnb_Dashboard.xlsx (+ Airbnb_Dashboard.pdf preview)

Candy design: pastel blue / pink / green / light-yellow (+ lavender, peach),
white cloud shapes, rounded cards. 7 pivots on one shared cache, 7 charts,
5 slicers, GETPIVOTDATA KPI cards.
"""
import os

import pythoncom
import win32com.client as win32

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "Airbnb_Base.xlsx")
OUT = os.path.join(HERE, "Airbnb_Dashboard.xlsx")
PDF = os.path.join(HERE, "Airbnb_Dashboard.pdf")

xlDatabase, xlRow = 1, 1
xlCount, xlSum, xlAverage = -4112, -4157, -4106
xlColumnClustered, xlBarClustered, xlDoughnut = 51, 57, -4120
xlValue, xlCategory = 2, 1
FONT = "Calibri"
CLOUD, OVAL = 79, 9  # msoShapeCloud, msoShapeOval (fallback)

# candy palette ---------------------------------------------------------------
BLUE, PINK, GREEN, YELLOW = "7FB6D9", "F4A7C3", "9BDBA6", "FFE08A"
LAV, PEACH = "C3B2E8", "FFC9A3"
DEEPBLUE, DEEPPINK, DEEPGREEN = "2E6FA3", "D94F7A", "3E9B5F"
GOLD, INK, MUTED = "C9930A", "33475B", "7A8FA6"
SKY_BG, LINE = "F2F7FD", "D0D7DE"
CANDY = [BLUE, PINK, GREEN, YELLOW, LAV, PEACH]


def rgb(h):
    h = h.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return r + g * 256 + b * 65536


def col_letter(c):
    s = ""
    while c:
        c, r = divmod(c - 1, 26)
        s = chr(65 + r) + s
    return s


pythoncom.CoInitialize()
xl = win32.DispatchEx("Excel.Application")
xl.Visible = False
xl.DisplayAlerts = False
xl.ScreenUpdating = False
try:
    wb = xl.Workbooks.Open(SRC)
    xl.Calculation = -4135  # manual: 48k-row array formulas would recalc on every step otherwise
    data = wb.Worksheets("Data")

    # ------------------------------------------------------------ sheets
    dash = wb.Worksheets.Add(Before=wb.Worksheets(1))
    dash.Name = "Dashboard"
    piv = wb.Worksheets.Add(After=wb.Worksheets("Analysis"))
    piv.Name = "Pivot Tables"
    piv.Range("A1").Value = "Pivot tables feeding the Dashboard (one shared cache: every slicer filters every pivot)"
    piv.Range("A1").Font.Size = 14
    piv.Range("A1").Font.Bold = True
    piv.Range("A1").Font.Color = rgb(DEEPBLUE)
    piv.Cells.Font.Name = FONT

    pc = wb.PivotCaches().Create(SourceType=xlDatabase, SourceData="tblAirbnb", Version=6)
    pivots = {}

    def new_pivot(name, label, col):
        piv.Cells(3, col).Value = label
        piv.Cells(3, col).Font.Bold = True
        piv.Cells(3, col).Font.Color = rgb(DEEPPINK)
        pt = pc.CreatePivotTable(TableDestination=piv.Cells(5, col), TableName=name, DefaultVersion=6)
        pt.RowAxisLayout(1)
        pt.ShowTableStyleRowStripes = True
        pt.TableStyle2 = "PivotStyleLight16"
        pivots[name] = pt
        return pt

    def data_field(pt, src, caption, func, fmt):
        f = pt.AddDataField(pt.PivotFields(src), caption, func)
        f.NumberFormat = fmt
        return f

    def rows(pt, field, pos=1):
        pf = pt.PivotFields(field)
        pf.Orientation = xlRow
        pf.Position = pos
        return pf

    def sort_desc(pt, field, df_cap):
        try:
            pt.PivotFields(field).AutoSort(2, df_cap)
        except Exception as e:
            print("autosort", field, e)

    def col_range(pt, offset=0):
        t = pt.TableRange1
        r0, c0, n = t.Row, t.Column, t.Rows.Count
        c = col_letter(c0 + offset)
        return f"'Pivot Tables'!${c}${r0 + 1}:${c}${r0 + n - 1}"

    def set_order(pt, field, items):
        """Logical (not alphabetical) item order for banded fields."""
        pf = pt.PivotFields(field)
        for i, it in enumerate(items, 1):
            try:
                pf.PivotItems(it).Position = i
            except Exception as e:
                print("order", field, it, e)

    # KPI pivot (grand totals -> cards + header line)
    ptK = new_pivot("ptKPI", "Totals for the KPI cards (GETPIVOTDATA source)", 1)
    data_field(ptK, "id", "Listings", xlCount, "#,##0")
    data_field(ptK, "price_capped", "Avg price", xlAverage, "#,##0")
    data_field(ptK, "is_entire_home", "Entire share", xlAverage, "0.0%")
    data_field(ptK, "is_zero_avail", "Zero avail", xlAverage, "0.0%")
    data_field(ptK, "flag_never_reviewed", "Never reviewed", xlAverage, "0.0%")
    data_field(ptK, "number_of_reviews", "Reviews", xlSum, "#,##0")
    data_field(ptK, "availability_365", "Avg avail", xlAverage, "#,##0")
    ptK.DataPivotField.Orientation = xlRow

    ptBor = new_pivot("ptBorough", "Listings, price and traction by borough", 3)
    rows(ptBor, "neighbourhood_group")
    b_c = data_field(ptBor, "id", "Listings  ", xlCount, "#,##0")
    b_p = data_field(ptBor, "price_capped", "Avg price  ", xlAverage, "#,##0")
    data_field(ptBor, "number_of_reviews", "Avg reviews  ", xlAverage, "#,##0.0")
    ptBor.ColumnGrand = False
    ptBor.RowGrand = False
    set_order(ptBor, "neighbourhood_group",
              ["Manhattan", "Brooklyn", "Queens", "Bronx", "Staten Island"])

    ptRoom = new_pivot("ptRoom", "Listing types: volume and price", 8)
    rows(ptRoom, "room_type")
    data_field(ptRoom, "id", "Listings   ", xlCount, "#,##0")
    data_field(ptRoom, "price_capped", "Avg price   ", xlAverage, "#,##0")
    ptRoom.ColumnGrand = False
    ptRoom.RowGrand = False
    set_order(ptRoom, "room_type", ["Entire home/apt", "Private room", "Shared room"])

    ptNb = new_pivot("ptNeigh", "Neighbourhoods ranked (chart reads the top 15)", 12)
    rows(ptNb, "neighbourhood")
    n_c = data_field(ptNb, "id", "Listings    ", xlCount, "#,##0")
    ptNb.ColumnGrand = False
    ptNb.RowGrand = False
    sort_desc(ptNb, "neighbourhood", n_c.Name)

    ptBand = new_pivot("ptBand", "Price bands", 16)
    rows(ptBand, "price_band")
    data_field(ptBand, "id", "Listings     ", xlCount, "#,##0")
    ptBand.ColumnGrand = False
    ptBand.RowGrand = False
    set_order(ptBand, "price_band",
              ["Budget (<$75)", "Mid ($75-150)", "Premium ($150-300)", "Luxury ($300+)"])

    ptAv = new_pivot("ptAvail", "Availability segments", 19)
    rows(ptAv, "avail_segment")
    data_field(ptAv, "id", "Listings      ", xlCount, "#,##0")
    ptAv.ColumnGrand = False
    ptAv.RowGrand = False
    set_order(ptAv, "avail_segment",
              ["Inactive (0 days)", "Low (1-90)", "Medium (91-180)", "High (181-364)", "Fully open (365)"])

    ptStay = new_pivot("ptStay", "Minimum-stay habits", 22)
    rows(ptStay, "stay_bin")
    data_field(ptStay, "id", "Listings       ", xlCount, "#,##0")
    ptStay.ColumnGrand = False
    ptStay.RowGrand = False
    set_order(ptStay, "stay_bin",
              ["1 night", "2 nights", "3 nights", "4-7 nights", "8-29 nights",
               "30 nights (monthly)", "31+ nights"])

    for col, w in zip(("A", "C", "D", "E", "H", "I", "J", "L", "M", "P", "Q", "S", "T", "V", "W", "AL", "AM"),
                       (14, 20, 12, 12, 20, 12, 12, 26, 12, 22, 12, 20, 12, 22, 12, 26, 12)):
        piv.Columns(col).ColumnWidth = w

    # live feed: top-15 neighbourhoods for the bar chart
    piv.Range("AL3").Value = "Chart feed: top 15 neighbourhoods (live)"
    piv.Range("AL3").Font.Bold = True
    piv.Range("AL3").Font.Color = rgb(DEEPPINK)
    piv.Range("AL5").Value = "Neighbourhood"
    piv.Range("AM5").Value = "Listings"
    for i in range(15):
        r = 6 + i
        piv.Cells(r, 38).Formula = f"=IF(L{r}=\"\",\"\",L{r})"
        piv.Cells(r, 39).Formula = f"=IF(M{r}=\"\",\"\",M{r})"
        piv.Cells(r, 39).NumberFormat = "#,##0"

    # ------------------------------------------------------------ canvas
    dash.Activate()
    xl.ActiveWindow.DisplayGridlines = False
    xl.ActiveWindow.DisplayHeadings = False
    dash.Cells.Font.Name = FONT
    dash.Cells.Interior.Color = rgb(SKY_BG)
    dash.Columns.ColumnWidth = 2.14
    dash.Rows.RowHeight = 15
    shapes = dash.Shapes

    def box(left, top, w, h, fill="FFFFFF", line=LINE, radius=True):
        s = shapes.AddShape(5 if radius else 1, left, top, w, h)
        s.Fill.ForeColor.RGB = rgb(fill)
        if line:
            s.Line.ForeColor.RGB = rgb(line)
            s.Line.Weight = 0.75
        else:
            s.Line.Visible = False
        if radius:
            s.Adjustments.SetItem(1, 0.06)
        s.Shadow.Visible = False
        return s

    def cloud(left, top, w, h, fill="FFFFFF", alpha=0.0):
        try:
            s = shapes.AddShape(CLOUD, left, top, w, h)
        except Exception:
            s = shapes.AddShape(OVAL, left, top, w, h)
        s.Fill.ForeColor.RGB = rgb(fill)
        try:
            s.Fill.Transparency = alpha
        except Exception:
            pass
        s.Line.ForeColor.RGB = rgb("D6E7F5")
        s.Line.Weight = 1.0
        s.Shadow.Visible = False
        return s

    def text(left, top, w, h, value, size=10, bold=False, color=INK, align=1, link=None, italic=False):
        t = shapes.AddTextbox(1, left, top, w, h)
        t.Fill.Visible = False
        t.Line.Visible = False
        tf = t.TextFrame2
        tf.MarginLeft = tf.MarginRight = 2
        tf.MarginTop = tf.MarginBottom = 0
        tf.WordWrap = True
        if link:
            t.DrawingObject.Formula = link
        else:
            tf.TextRange.Text = value
        r = tf.TextRange
        r.Font.Name = FONT
        r.Font.Size = size
        r.Font.Bold = bold
        r.Font.Italic = italic
        r.Font.Fill.ForeColor.RGB = rgb(color)
        r.ParagraphFormat.Alignment = align
        return t

    W = 1400
    # header: deep-blue sky band + pink strip + clouds
    box(0, 0, W - 4, 66, DEEPBLUE, None, radius=False)
    box(0, 66, W - 4, 10, PINK, None, radius=False)
    for cx, cy, cw, chh in [(1050, 6, 120, 40), (1210, 22, 90, 30), (60, 10, 70, 24), (950, 30, 70, 22)]:
        cloud(cx, cy, cw, chh, alpha=0.15)
    text(18, 10, 700, 26, "New York City Airbnb  |  Sweet-Stay Dashboard", 20, True, "FFFFFF")
    text(18, 40, 900, 16, "", 9, False, "D6E4F0", link="='Pivot Tables'!$B$80")
    text(W - 380, 12, 362, 44,
         "Source: AB_NYC_2019.csv (Inside Airbnb, snapshot Sep 2019)\n48,884 listings  |  37,455 hosts  |  221 neighbourhoods",
         8, False, "D6E4F0", align=3)

    # KPI card formulas on the Pivot Tables sheet
    gp = lambda f: f'IFERROR(GETPIVOTDATA("{f}",\'Pivot Tables\'!$A$5),0)'
    piv.Range("A60").Value = "Dashboard card values (follow the slicers)"
    piv.Range("A60").Font.Bold = True
    piv.Range("A60").Font.Color = rgb(DEEPPINK)
    calc = [
        ("Listings in selection", f"={gp('Listings')}", "#,##0"),
        ("Avg nightly price ($)", f"={gp('Avg price')}", "#,##0"),
        ("Entire-home share", f"={gp('Entire share')}", "0.0%"),
        ("Zero-availability share", f"={gp('Zero avail')}", "0.0%"),
        ("Never-reviewed share", f"={gp('Never reviewed')}", "0.0%"),
        ("Total reviews", f"={gp('Reviews')}", "#,##0"),
        ("Mean open days / year", f"={gp('Avg avail')}", "#,##0"),
    ]
    for i, (lab, f, fmt) in enumerate(calc):
        piv.Cells(62 + i, 1).Value = lab
        piv.Cells(62 + i, 2).Formula = f
        piv.Cells(62 + i, 2).NumberFormat = fmt
        piv.Cells(62 + i, 2).Font.Bold = True
    topf = f'=IFERROR(INDEX({col_range(ptNb)},{""}MATCH(MAX({col_range(ptNb, 1)}),{col_range(ptNb, 1)},0)),"-")'
    piv.Cells(69, 1).Value = "Top neighbourhood"
    piv.Cells(69, 2).Formula = topf
    piv.Range("A71").Value = "Header + card subtitles (linked text)"
    piv.Range("A71").Font.Bold = True
    subs = {
        73: '="listings in the current selection"',
        74: '="average nightly price (capped $1,000)"',
        75: '="entire homes in the selection"',
        76: '="blocked all year - audit before counting"',
        77: '="zero reviews so far"',
        78: '="guest reviews in the selection"',
        79: '="calendar openness"',
        80: '="Current selection: "&TEXT(B62,"#,##0")&" listings  |  $"&TEXT(B63,"#,##0")&" avg  |  "&TEXT(B64,"0%")&" entire homes  |  top area: "&B69',
    }
    for r, f in subs.items():
        piv.Cells(r, 2).Formula = f

    # KPI cards (candy accent bars)
    cards = [("LISTINGS", 62, 73, DEEPBLUE, 18), ("AVG PRICE", 63, 74, DEEPPINK, 18),
             ("ENTIRE HOMES", 64, 75, DEEPGREEN, 18), ("ZERO AVAIL", 65, 76, GOLD, 18),
             ("NEVER REVIEWED", 66, 77, "9B7ED9", 18), ("REVIEWS", 67, 78, DEEPBLUE, 18),
             ("OPEN DAYS", 68, 79, DEEPGREEN, 18)]
    x0, top, gap = 200, 88, 10
    cw = (W - x0 - 12 - gap * (len(cards) - 1)) / len(cards)
    for i, (lab, vr, sr, accent, vsize) in enumerate(cards):
        left = x0 + i * (cw + gap)
        box(left, top, cw, 82)
        box(left, top, 6, 82, accent, None, radius=False)
        text(left + 14, top + 8, cw - 18, 14, lab, 8, True, MUTED)
        text(left + 14, top + 24, cw - 18, 30, "", vsize, True, accent, link=f"='Pivot Tables'!$B${vr}")
        text(left + 14, top + 58, cw - 18, 18, "", 7.5, False, MUTED, link=f"='Pivot Tables'!$B${sr}")

    # ------------------------------------------------------------ charts
    def style_chart(ch, title_, legend=False):
        try:
            ch.ShowAllFieldButtons = False
        except Exception:
            pass
        ch.HasTitle = True
        ch.ChartTitle.Text = title_
        ch.ChartTitle.Format.TextFrame2.TextRange.Font.Size = 11
        ch.ChartTitle.Format.TextFrame2.TextRange.Font.Bold = True
        ch.ChartTitle.Format.TextFrame2.TextRange.Font.Fill.ForeColor.RGB = rgb(DEEPBLUE)
        ch.ChartArea.Format.TextFrame2.TextRange.Font.Name = FONT
        ch.ChartArea.Format.Line.ForeColor.RGB = rgb(LINE)
        ch.ChartArea.Format.Fill.ForeColor.RGB = rgb("FFFFFF")
        ch.ChartArea.RoundedCorners = True
        ch.PlotArea.Format.Fill.ForeColor.RGB = rgb("FFFFFF")
        ch.HasLegend = legend
        if legend:
            ch.Legend.Position = -4160
            ch.Legend.Font.Size = 8
        try:
            ax = ch.Axes(xlValue)
            ax.MajorGridlines.Format.Line.ForeColor.RGB = rgb("E6EBF0")
            ax.TickLabels.Font.Size = 8
            ch.Axes(xlCategory).TickLabels.Font.Size = 8
            ch.Axes(xlValue).Format.Line.Visible = False
        except Exception:
            pass

    def color_series(s, hexcol, labels=True, fmt="#,##0", size=8):
        s.Format.Fill.ForeColor.RGB = rgb(hexcol)
        if labels:
            s.HasDataLabels = True
            s.DataLabels().NumberFormat = fmt
            s.DataLabels().Font.Size = size
            s.DataLabels().Font.Color = rgb(INK)

    def candy_points(series, palette=CANDY):
        for i in range(1, series.Points().Count + 1):
            try:
                series.Points(i).Format.Fill.ForeColor.RGB = rgb(palette[(i - 1) % len(palette)])
            except Exception:
                break

    def chart(pt, ctype, left, top_, w, h, source=None):
        s = shapes.AddChart2(-1, ctype, left, top_, w, h)
        s.Chart.SetSourceData(source if source is not None else pt.TableRange1)
        s.Placement = 3
        return s.Chart

    CX, CY, CW, CH, G = 200, 282, 388, 250, 10
    pos = lambda c, r: (CX + c * (CW + G), CY + r * (CH + G))

    ch = chart(ptBor, xlColumnClustered, *pos(0, 0), CW, CH)
    style_chart(ch, "Listings by borough (85% in two boroughs)")
    candy_points(ch.SeriesCollection(1))
    ch.SeriesCollection(1).HasDataLabels = True
    ch.SeriesCollection(1).DataLabels().NumberFormat = "#,##0"
    ch.ChartGroups(1).GapWidth = 55

    ch = chart(ptBor, xlColumnClustered, *pos(1, 0), CW, CH,
               source=piv.Range(f"D5:E{5 + ptBor.TableRange1.Rows.Count - 1}"))
    style_chart(ch, "Average nightly price by borough ($)")
    color_series(ch.SeriesCollection(1), PINK)
    ch.ChartGroups(1).GapWidth = 55

    ch = chart(ptRoom, xlColumnClustered, *pos(2, 0), CW, CH)
    style_chart(ch, "Listing types: volume vs price")
    color_series(ch.SeriesCollection(1), BLUE, labels=False)
    try:
        s2 = ch.SeriesCollection(2)
        s2.ChartType = 4  # line on secondary axis
        s2.AxisGroup = 2
        s2.Format.Line.ForeColor.RGB = rgb(DEEPPINK)
        s2.Format.Line.Weight = 2.25
        s2.HasDataLabels = True
        s2.DataLabels().NumberFormat = "$#,##0"
        ch.HasLegend = True
        ch.Legend.Position = -4160
    except Exception as e:
        print("room combo", e)
    ch.ChartGroups(1).GapWidth = 60

    ch = chart(ptNb, xlBarClustered, *pos(0, 1), CW, CH, source=piv.Range("AL5:AM20"))
    style_chart(ch, "Top 15 neighbourhoods by listings")
    color_series(ch.SeriesCollection(1), GREEN, labels=False)
    ch.ChartGroups(1).GapWidth = 55
    ch.Axes(xlCategory).ReversePlotOrder = True
    ch.Axes(xlCategory).TickLabels.Font.Size = 7

    ch = chart(ptBand, xlDoughnut, *pos(1, 1), CW, CH)
    style_chart(ch, "Price bands (share of listings)", legend=True)
    sr = ch.SeriesCollection(1)
    candy_points(sr)
    sr.HasDataLabels = True
    dl = sr.DataLabels()
    dl.ShowValue = False
    dl.ShowPercentage = True
    dl.NumberFormat = "0%"
    dl.Font.Size = 9
    dl.Font.Bold = True
    dl.Font.Color = rgb(INK)
    try:
        ch.ChartGroups(1).DoughnutHoleSize = 55
    except Exception:
        pass

    ch = chart(ptAv, xlColumnClustered, *pos(2, 1), CW, CH)
    style_chart(ch, "Availability: barbelled supply")
    color_series(ch.SeriesCollection(1), YELLOW)
    ch.ChartGroups(1).GapWidth = 55
    ch.Axes(xlCategory).TickLabels.Font.Size = 7

    ch = chart(ptStay, xlColumnClustered, *pos(0, 2), CW * 2 + G, CH)
    style_chart(ch, "Minimum stay: short breaks + a 30-night monthly spike")
    color_series(ch.SeriesCollection(1), LAV, fmt="#,##0")
    ch.ChartGroups(1).GapWidth = 55

    # insights panel (lavender) + how-to (peach) + clouds
    ix, iy = pos(2, 2)
    box(ix, iy, CW, CH, "F3EEFB", LAV)
    cloud(ix + CW - 120, iy + 6, 100, 34, fill="FFFFFF")
    text(ix + 12, iy + 8, CW - 24, 18, "KEY INSIGHTS (all 48,884 rows)", 11, True, DEEPBLUE)
    insights = (
        "1. Two boroughs run the market: Manhattan (44%) + Brooklyn (41%) = 85% of listings.\n"
        "2. Clean price ladder: Manhattan $149 vs Bronx $65; entire homes $160 vs private $70.\n"
        "3. Price buys ZERO reviews (r = -0.06): Tribeca/NoHo cost most, value areas win demand.\n"
        "4. 36% of listings show zero open days and 21% were never reviewed - audit the tail.\n"
        "5. 86% of hosts hold one listing, but firms (Sonder 327, Blueground 232) top the chart.\n"
        "6. Two businesses in one file: 1-3 night stays plus a 30-night monthly spike."
    )
    t = text(ix + 12, iy + 30, CW - 24, CH - 36, insights, 9, False, INK)
    t.TextFrame2.TextRange.ParagraphFormat.SpaceAfter = 2

    # how-to panel spans full width below
    hx, hy = CX, CY + 3 * (CH + G)
    box(hx, hy, CW * 3 + G * 2, 120, "FFF6E8", PEACH)
    cloud(hx + CW * 3 + G * 2 - 130, hy + 8, 110, 36, fill="FFFFFF")
    text(hx + 12, hy + 8, 300, 18, "HOW TO USE THIS FILE", 11, True, DEEPBLUE)
    howto = (
        "Slicers on the left (borough, room type, price band, availability, host size) recalculate every card and chart. "
        "Ctrl+click multi-selects; use the clear-filter icon to reset. KPIs and Analysis sheets keep the full-file values. "
        "Sheets: Dashboard | KPIs (17 live formulas) | Analysis (6 tables) | Pivot Tables | Data (tblAirbnb, 26 cols) | Cleaning Log | Data Dictionary. "
        "Price averages use price_capped (max $1,000) so one $10,000 listing cannot move a bar."
    )
    text(hx + 320, hy + 8, CW * 3 + G * 2 - 340, 104, howto, 9, False, INK)

    # ------------------------------------------------------------ slicers
    box(8, 88, 182, hy + 120 - 88, "FFFFFF")
    text(18, 96, 160, 16, "FILTERS", 10, True, DEEPBLUE)
    cloud(100, 96, 70, 22, fill="F2F7FD")
    all_pts = list(pivots.values())

    def slicer(field, caption, top_, height, cols=1, name=None):
        sc = wb.SlicerCaches.Add2(ptK, field)
        for p in all_pts[1:]:
            sc.PivotTables.AddPivotTable(p)
        sl = sc.Slicers.Add(SlicerDestination=dash, Name=name or f"sl_{field}", Caption=caption,
                            Top=top_, Left=16, Width=166, Height=height)
        sl.Top, sl.Left, sl.Width, sl.Height = top_, 16, 166, height
        sl.NumberOfColumns = cols
        sl.Style = "SlicerStyleLight1"
        sl.RowHeight = 17
        sc.CrossFilterType = 1
        return sl

    y = 118
    for field, cap, h, cols in [("neighbourhood_group", "Borough", 96, 1),
                                ("room_type", "Room type", 74, 1),
                                ("price_band", "Price band", 96, 1),
                                ("avail_segment", "Availability", 112, 1),
                                ("host_size", "Host size", 96, 1)]:
        slicer(field, cap, y, h, cols)
        y += h + 8

    text(200, hy + 122, W - 212, 14,
         "Tip: open with Enable Editing so the slicers work. All values on this sheet are live; KPIs and Analysis show the full file.",
         8, False, MUTED, italic=True)

    # ------------------------------------------------------------ finish
    order = ["Dashboard", "KPIs", "Analysis", "Pivot Tables", "Data", "Cleaning Log", "Data Dictionary"]
    wb.Worksheets(order[0]).Move(wb.Worksheets(1))
    for prev, name in zip(order, order[1:]):
        wb.Worksheets(name).Move(None, wb.Worksheets(prev))
    dash.Activate()
    dash.Range("A1").Select()
    xl.ActiveWindow.Zoom = 72
    xl.Calculation = -4105  # back to automatic
    wb.RefreshAll()
    xl.CalculateFull()
    print("cards:", [piv.Cells(62 + i, 2).Value for i in range(7)])
    print("header:", piv.Range("B80").Value)
    print("sheets:", [s_.Name for s_ in wb.Worksheets])
    print("pivots:", piv.PivotTables().Count, "charts:", dash.ChartObjects().Count,
          "slicer caches:", wb.SlicerCaches.Count)
    if os.path.exists(OUT):
        os.remove(OUT)
    wb.SaveAs(OUT, FileFormat=51)
    try:
        dash.ExportAsFixedFormat(0, PDF)  # preview pdf of the dashboard sheet
        print("pdf preview:", os.path.basename(PDF))
    except Exception as e:
        print("pdf preview skipped:", str(e)[:120])
    print("saved", OUT)
    wb.Close(False)
finally:
    xl.ScreenUpdating = True
    xl.Quit()
