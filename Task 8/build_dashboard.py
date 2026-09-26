"""Step 3: open the base workbook in Excel (COM) and add the interactive layer:
pivot tables, pivot charts, slicers, a date timeline, KPI cards driven by
GETPIVOTDATA, an insights panel and the Insights sheet.

Output: Healthcare_NoShows_Dashboard.xlsx
"""
import os
import pythoncom
import win32com.client as win32

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "NoShows_Base.xlsx")
OUT = os.path.join(HERE, "Healthcare_NoShows_Dashboard.xlsx")

# Excel constants
xlDatabase, xlRow, xlCol, xlPage = 1, 1, 2, 3
xlCount, xlSum, xlAverage = -4112, -4157, -4106
xlColumnClustered, xlBarClustered, xlDoughnut, xlLine = 51, 57, -4120, 4
xlValue, xlCategory, xlSecondary = 2, 1, 2
xlTimeline, xlTimelineLevelDays = 2, 3
FONT = "Arial"


def rgb(h):
    h = h.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return r + g * 256 + b * 65536


NAVY, TEAL, CORAL, SKY, GREY, INK, MUTED = "1F3B57", "1B998B", "E4572E", "9BC4E2", "F3F6F9", "22313F", "5A6B7B"
LINE = "D0D7DE"

pythoncom.CoInitialize()
xl = win32.DispatchEx("Excel.Application")
xl.Visible = False
xl.DisplayAlerts = False
xl.ScreenUpdating = False
try:
    wb = xl.Workbooks.Open(SRC)
    data = wb.Worksheets("Data")

    # ------------------------------------------------------------ sheets
    dash = wb.Worksheets.Add(Before=wb.Worksheets(1))
    dash.Name = "Dashboard"
    piv = wb.Worksheets.Add(After=wb.Worksheets("Analysis"))
    piv.Name = "Pivot Tables"
    piv.Range("A1").Value = "Pivot tables feeding the Dashboard (all connected to the same slicers and timeline)"
    piv.Range("A1").Font.Size = 14
    piv.Range("A1").Font.Bold = True
    piv.Range("A1").Font.Color = rgb(NAVY)
    piv.Cells.Font.Name = FONT

    pc = wb.PivotCaches().Create(SourceType=xlDatabase, SourceData="tblAppointments", Version=6)
    pivots = {}
    col = [1]

    def new_pivot(name, label, width=4):
        c = col[0]
        piv.Cells(3, c).Value = label
        piv.Cells(3, c).Font.Bold = True
        piv.Cells(3, c).Font.Color = rgb(TEAL)
        pt = pc.CreatePivotTable(TableDestination=piv.Cells(5, c), TableName=name, DefaultVersion=6)
        pt.RowAxisLayout(1)  # tabular
        pt.ShowTableStyleRowStripes = True
        pt.TableStyle2 = "PivotStyleLight16"
        col[0] += width + 1
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

    # KPI pivot (grand totals only) -> KPI cards
    ptK = new_pivot("ptKPI", "KPI measures (GETPIVOTDATA source for the cards)", 7)
    data_field(ptK, "Appointment_ID", "Appointments", xlCount, "#,##0")
    data_field(ptK, "No_Show", "No-Shows", xlSum, "#,##0")
    data_field(ptK, "No_Show", "No-Show Rate", xlAverage, "0.0%")
    data_field(ptK, "First_Appt", "Patients", xlSum, "#,##0")
    data_field(ptK, "Lead_Days", "Avg Lead Days", xlAverage, "0.0")
    data_field(ptK, "SMS_Flag", "SMS Coverage", xlAverage, "0.0%")
    ptK.DataPivotField.Orientation = xlRow

    ptLead = new_pivot("ptLead", "No-show rate by lead time", 3)
    rows(ptLead, "Lead_Time_Group")
    data_field(ptLead, "No_Show", "No-Show Rate ", xlAverage, "0.0%")
    ptLead.ColumnGrand = False
    ptLead.RowGrand = False

    ptSMS = new_pivot("ptSMS", "SMS effect by lead time", 4)
    rows(ptSMS, "Lead_Time_Group")
    ptSMS.PivotFields("SMS_Received").Orientation = xlCol
    data_field(ptSMS, "No_Show", "No-Show Rate  ", xlAverage, "0.0%")
    ptSMS.ColumnGrand = False
    ptSMS.PivotFields("SMS_Received").PivotItems("No").Caption = "No SMS"
    ptSMS.PivotFields("SMS_Received").PivotItems("Yes").Caption = "SMS sent"
    ptSMS.RowGrand = False

    ptAge = new_pivot("ptAge", "No-show rate by age group", 3)
    rows(ptAge, "Age_Group")
    data_field(ptAge, "No_Show", "No-Show Rate   ", xlAverage, "0.0%")
    ptAge.ColumnGrand = False

    ptStatus = new_pivot("ptStatus", "Attendance split", 3)
    rows(ptStatus, "Status")
    data_field(ptStatus, "Appointment_ID", "Appointments ", xlCount, "#,##0")
    ptStatus.ColumnGrand = False
    ptStatus.PivotFields("Status").PivotItems("Showed Up").Position = 1

    ptDay = new_pivot("ptDay", "Daily volume and no-show rate", 4)
    pf = rows(ptDay, "Appointment_Date")
    try:  # Excel may auto-group dates into months; we want days
        pf.DataRange.Cells(1).Ungroup()
    except Exception:
        pass
    for extra in ("Months", "Years", "Quarters", "Days"):
        try:
            ptDay.PivotFields(extra).Orientation = 0
        except Exception:
            pass
    data_field(ptDay, "Appointment_ID", "Appointments  ", xlCount, "#,##0")
    data_field(ptDay, "No_Show", "No-Show Rate    ", xlAverage, "0.0%")
    ptDay.ColumnGrand = False
    ptDay.PivotFields("Appointment_Date").NumberFormat = "dd-mmm"

    ptHist = new_pivot("ptHist", "Patient no-show history", 3)
    rows(ptHist, "NoShow_History")
    data_field(ptHist, "No_Show", "No-Show Rate     ", xlAverage, "0.0%")
    ptHist.ColumnGrand = False
    for i, item in enumerate(["First visit", "Never missed", "Has missed before"], 1):
        ptHist.PivotFields("NoShow_History").PivotItems(item).Position = i

    ptWeek = new_pivot("ptWeek", "No-show rate by weekday", 3)
    rows(ptWeek, "Appt_Weekday")
    data_field(ptWeek, "No_Show", "No-Show Rate      ", xlAverage, "0.0%")
    ptWeek.ColumnGrand = False

    ptNb = new_pivot("ptNb", "Top 10 neighbourhoods by volume", 4)
    nb = rows(ptNb, "Neighbourhood")
    nbc = data_field(ptNb, "Appointment_ID", "Appointments   ", xlCount, "#,##0")
    data_field(ptNb, "No_Show", "No-Show Rate       ", xlAverage, "0.0%")
    ptNb.ColumnGrand = False
    nb.AutoSort(2, nbc.Name)
    nb.PivotFilters.Add2(Type=1, DataField=nbc, Value1=10)  # xlTopCount

    ptChr = new_pivot("ptChronic", "Welfare and chronic conditions", 4)
    rows(ptChr, "Chronic_Group")
    ptChr.PivotFields("Scholarship").Orientation = xlCol
    data_field(ptChr, "No_Show", "No-Show Rate        ", xlAverage, "0.0%")
    ptChr.ColumnGrand = False
    ptChr.PivotFields("Scholarship").PivotItems("No").Caption = "No scholarship"
    ptChr.PivotFields("Scholarship").PivotItems("Yes").Caption = "Scholarship"
    ptChr.RowGrand = False
    for i, item in enumerate(["None", "1 condition", "2+ conditions"], 1):
        ptChr.PivotFields("Chronic_Group").PivotItems(item).Position = i
    piv.Columns.AutoFit()

    # ------------------------------------------------------------ dashboard canvas
    xl.ActiveWindow.Zoom = 100
    dash.Activate()
    xl.ActiveWindow.DisplayGridlines = False
    xl.ActiveWindow.DisplayHeadings = False
    dash.Cells.Font.Name = FONT
    dash.Cells.Interior.Color = rgb(GREY)
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
        r.ParagraphFormat.Alignment = align  # 1 left, 2 center
        return t

    W = 1400
    # header band
    hb = box(0, 0, W - 4, 58, NAVY, None, radius=False)
    text(18, 8, 800, 26, "Patient Appointment No-Show Dashboard", 20, True, "FFFFFF")
    text(18, 36, 900, 16, "", 10, False, "D6E4F0", link="='Pivot Tables'!$B$30")
    text(W - 330, 12, 312, 40, "Source: 106,982 medical appointments, Vitória (Brazil), 29 Apr - 8 Jun 2016\n"
         "Use the slicers and the timeline to filter every KPI and chart.", 8, False, "D6E4F0", align=3)

    # ------------------------------------------------------------ KPI calc area (Pivot Tables sheet)
    gp = lambda f: f'IFERROR(GETPIVOTDATA("{f}",\'Pivot Tables\'!$A$5),0)'
    calc = [
        ("Appointments", f"={gp('Appointments')}"),
        ("No-Shows", f"={gp('No-Shows')}"),
        ("No-Show Rate", f"={gp('No-Show Rate')}"),
        ("Patients", f"={gp('Patients')}"),
        ("Avg Lead Days", f"={gp('Avg Lead Days')}"),
        ("SMS Coverage", f"={gp('SMS Coverage')}"),
        ("Showed Up", "=B20-B21"),
        ("Overall no-show rate (all data)", "=KPIs!$C$10"),
        ("Rate delta (pts)", "=(B22-B27)*100"),
    ]
    piv.Range("A18").Value = "Dashboard card values (formulas)"
    piv.Range("A18").Font.Bold = True
    piv.Range("A18").Font.Color = rgb(TEAL)
    for i, (lab, f) in enumerate(calc):
        piv.Cells(20 + i, 1).Value = lab
        piv.Cells(20 + i, 2).Formula = f
    # text lines for card sub-captions and header
    subs = {
        30: '="Current selection: "&TEXT(B20,"#,##0")&" appointments  |  "&TEXT(B22,"0.0%")&" no-show rate  |  "'
            '&IF(B28>=0,"+","")&TEXT(B28,"0.0")&" pts vs overall "&TEXT(B27,"0.0%")',
        31: '=TEXT(B20,"#,##0")',
        32: '="Showed up: "&TEXT(B26,"#,##0")',
        33: '=TEXT(B23,"#,##0")',
        34: '=IFERROR(TEXT(B20/B23,"0.00"),"-")&" appointments per patient"',
        35: '=TEXT(B21,"#,##0")',
        36: '="Missed slots in selection"',
        37: '=TEXT(B22,"0.0%")',
        38: '=IF(B28>=0,"▲ +","▼ ")&TEXT(B28,"0.0")&" pts vs overall "&TEXT(B27,"0.0%")',
        39: '=TEXT(1-B22,"0.0%")',
        40: '="Share of appointments attended"',
        41: '=TEXT(B24,"0.0")&" days"',
        42: '="Booking-to-visit wait"',
        43: '=TEXT(B25,"0.0%")',
        44: '="Share of appointments with an SMS"',
    }
    piv.Range("A29").Value = "Card and header text (linked to dashboard text boxes)"
    piv.Range("A29").Font.Bold = True
    for r, f in subs.items():
        piv.Cells(r, 2).Formula = f

    # KPI cards
    cards = [("TOTAL APPOINTMENTS", 31, 32, NAVY), ("UNIQUE PATIENTS", 33, 34, NAVY),
             ("NO-SHOWS", 35, 36, CORAL), ("NO-SHOW RATE", 37, 38, CORAL),
             ("ATTENDANCE RATE", 39, 40, TEAL), ("AVG LEAD TIME", 41, 42, NAVY),
             ("SMS COVERAGE", 43, 44, TEAL)]
    x0, top, gap = 200, 70, 10
    cw = (W - x0 - 12 - gap * (len(cards) - 1)) / len(cards)
    for i, (lab, vr, sr, accent) in enumerate(cards):
        left = x0 + i * (cw + gap)
        box(left, top, cw, 78)
        a = box(left, top, 5, 78, accent, None, radius=False)
        text(left + 12, top + 8, cw - 16, 14, lab, 8, True, MUTED)
        text(left + 12, top + 24, cw - 16, 28, "", 20, True, accent, link=f"='Pivot Tables'!$B${vr}")
        text(left + 12, top + 56, cw - 16, 16, "", 7.5, False, MUTED, link=f"='Pivot Tables'!$B${sr}")

    # ------------------------------------------------------------ charts
    def style_chart(ch, title, legend=False, pct_axis=True):
        ch.ShowAllFieldButtons = False
        ch.HasTitle = True
        ch.ChartTitle.Text = title
        ch.ChartTitle.Format.TextFrame2.TextRange.Font.Size = 11
        ch.ChartTitle.Format.TextFrame2.TextRange.Font.Bold = True
        ch.ChartTitle.Format.TextFrame2.TextRange.Font.Fill.ForeColor.RGB = rgb(NAVY)
        ch.ChartArea.Format.TextFrame2.TextRange.Font.Name = FONT
        ch.ChartArea.Format.Line.ForeColor.RGB = rgb(LINE)
        ch.ChartArea.RoundedCorners = True
        ch.HasLegend = legend
        if legend:
            ch.Legend.Position = -4160  # top
            ch.Legend.Font.Size = 8
        try:
            ax = ch.Axes(xlValue)
            ax.MajorGridlines.Format.Line.ForeColor.RGB = rgb("E6EBF0")
            ax.TickLabels.Font.Size = 8
            if pct_axis:
                ax.TickLabels.NumberFormat = "0%"
                ax.MinimumScale = 0
            ch.Axes(xlCategory).TickLabels.Font.Size = 8
            ch.Axes(xlValue).Format.Line.Visible = False
        except Exception:
            pass

    def color_series(s, hexcol, labels=True, fmt="0.0%", size=8):
        s.Format.Fill.ForeColor.RGB = rgb(hexcol)
        if labels:
            s.HasDataLabels = True
            s.DataLabels().NumberFormat = fmt
            s.DataLabels().Font.Size = size
            s.DataLabels().Font.Color = rgb(INK)

    def chart(pt, ctype, left, top, w, h):
        s = shapes.AddChart2(-1, ctype, left, top, w, h)
        s.Chart.SetSourceData(pt.TableRange1)
        s.Placement = 3  # don't move/size with cells
        return s.Chart

    CX, CY, CW, CH, G = 200, 250, 388, 250, 10
    pos = lambda c, r: (CX + c * (CW + G), CY + r * (CH + G))

    ch = chart(ptLead, xlColumnClustered, *pos(0, 0), CW, CH)
    style_chart(ch, "No-show rate rises with waiting time")
    color_series(ch.SeriesCollection(1), CORAL)
    ch.ChartGroups(1).GapWidth = 60

    ch = chart(ptSMS, xlColumnClustered, *pos(1, 0), CW, CH)
    style_chart(ch, "SMS reminder effect (same lead time)", legend=True)
    ch.SeriesCollection(1).Format.Fill.ForeColor.RGB = rgb("B8C2CC")
    ch.SeriesCollection(2).Format.Fill.ForeColor.RGB = rgb(TEAL)
    ch.ChartGroups(1).GapWidth = 70
    ch.ChartGroups(1).Overlap = -5

    ch = chart(ptStatus, xlDoughnut, *pos(2, 0), CW, CH)
    style_chart(ch, "Attendance split", legend=True, pct_axis=False)
    s = ch.SeriesCollection(1)
    s.Points(1).Format.Fill.ForeColor.RGB = rgb(TEAL)
    s.Points(2).Format.Fill.ForeColor.RGB = rgb(CORAL)
    s.HasDataLabels = True
    dl = s.DataLabels()
    dl.ShowValue = False
    dl.ShowPercentage = True
    dl.NumberFormat = "0.0%"
    dl.Font.Size = 9
    dl.Font.Bold = True
    dl.Font.Color = rgb("FFFFFF")
    ch.ChartGroups(1).DoughnutHoleSize = 55
    ch.Legend.Position = -4107  # bottom

    ch = chart(ptAge, xlColumnClustered, *pos(0, 1), CW, CH)
    style_chart(ch, "No-show rate by age group")
    color_series(ch.SeriesCollection(1), NAVY)
    ch.ChartGroups(1).GapWidth = 50
    ch.Axes(xlCategory).TickLabels.Font.Size = 7

    ch = chart(ptHist, xlBarClustered, *pos(1, 1), CW, CH)
    style_chart(ch, "Past no-shows predict the next one")
    color_series(ch.SeriesCollection(1), CORAL)
    ch.ChartGroups(1).GapWidth = 60
    ch.Axes(xlCategory).ReversePlotOrder = True

    ch = chart(ptChr, xlColumnClustered, *pos(2, 1), CW, CH)
    style_chart(ch, "Welfare (scholarship) & chronic conditions", legend=True)
    ch.SeriesCollection(1).Format.Fill.ForeColor.RGB = rgb(SKY)
    ch.SeriesCollection(2).Format.Fill.ForeColor.RGB = rgb(NAVY)
    ch.ChartGroups(1).GapWidth = 70

    ch = chart(ptDay, xlColumnClustered, *pos(0, 2), CW * 2 + G, CH)
    style_chart(ch, "Daily appointments (bars) and no-show rate (line)", legend=True, pct_axis=False)
    s1, s2 = ch.SeriesCollection(1), ch.SeriesCollection(2)
    s1.Format.Fill.ForeColor.RGB = rgb(SKY)
    s2.ChartType = xlLine
    s2.AxisGroup = xlSecondary
    s2.Format.Line.ForeColor.RGB = rgb(CORAL)
    s2.Format.Line.Weight = 2.25
    ch.Axes(xlValue, xlSecondary).TickLabels.NumberFormat = "0%"
    ch.Axes(xlValue, xlSecondary).TickLabels.Font.Size = 8
    ch.Axes(xlValue, xlSecondary).MinimumScale = 0
    ch.Axes(xlValue).TickLabels.NumberFormat = "#,##0"
    ch.ChartGroups(1).GapWidth = 40

    ch = chart(ptWeek, xlColumnClustered, *pos(2, 2), CW, CH)
    style_chart(ch, "No-show rate by weekday (Sat = only 39 appts)")
    color_series(ch.SeriesCollection(1), NAVY)
    ch.ChartGroups(1).GapWidth = 50

    ch = chart(ptNb, xlColumnClustered, *pos(0, 3), CW * 2 + G, CH)
    style_chart(ch, "Top 10 neighbourhoods: volume (bars) and no-show rate (line)", legend=True, pct_axis=False)
    s1, s2 = ch.SeriesCollection(1), ch.SeriesCollection(2)
    s1.Format.Fill.ForeColor.RGB = rgb(SKY)
    s2.ChartType = 65  # line with markers
    s2.AxisGroup = xlSecondary
    s2.Format.Line.ForeColor.RGB = rgb(CORAL)
    s2.MarkerBackgroundColor = rgb(CORAL)
    s2.MarkerForegroundColor = rgb(CORAL)
    s2.HasDataLabels = True
    s2.DataLabels().NumberFormat = "0%"
    s2.DataLabels().Font.Size = 8
    s2.DataLabels().Position = 0  # above
    ch.Axes(xlValue, xlSecondary).TickLabels.NumberFormat = "0%"
    ch.Axes(xlValue, xlSecondary).MinimumScale = 0
    ch.Axes(xlValue, xlSecondary).TickLabels.Font.Size = 8
    ch.Axes(xlValue).TickLabels.NumberFormat = "#,##0"
    ch.Axes(xlCategory).TickLabels.Font.Size = 7
    ch.ChartGroups(1).GapWidth = 50

    # insights panel (static, full-data findings)
    ix, iy = pos(2, 3)
    box(ix, iy, CW, CH)
    text(ix + 12, iy + 8, CW - 24, 18, "KEY INSIGHTS (all data)", 11, True, NAVY)
    insights = (
        "1. Lead time is the #1 driver: same-day bookings miss 4.7%, 15-30 day bookings 32.7%.\n"
        "2. SMS works: at every lead time it cuts no-shows by 1.6-7.8 pts. The raw 27.7% vs 16.7% "
        "is misleading because SMS goes only to advance bookings.\n"
        "3. Patients who missed before miss again 29.4% of the time vs 17.1% for reliable patients.\n"
        "4. Teens and young adults (13-30) are the riskiest group (~25%); seniors the most reliable (~15%).\n"
        "5. Scholarship patients miss 23.8% vs 19.9%. Chronic conditions go with better attendance.\n"
        "6. Gender and weekday barely matter (±1 pt)."
    )
    t = text(ix + 12, iy + 30, CW - 24, CH - 36, insights, 9.5, False, INK)
    t.TextFrame2.TextRange.ParagraphFormat.SpaceAfter = 3

    # slicer panel
    box(8, 70, 182, CY + 4 * (CH + G) - 10 - 70, "FFFFFF")
    text(18, 78, 160, 16, "FILTERS", 10, True, NAVY)
    all_pts = list(pivots.values())

    def slicer(field, caption, top, height, cols=1, name=None):
        sc = wb.SlicerCaches.Add2(ptK, field)
        for p in all_pts[1:]:
            sc.PivotTables.AddPivotTable(p)
        sl = sc.Slicers.Add(SlicerDestination=dash, Name=name or f"sl_{field}", Caption=caption,
                            Top=top, Left=16, Width=166, Height=height)
        sl.Top, sl.Left, sl.Width, sl.Height = top, 16, 166, height
        sl.NumberOfColumns = cols
        sl.Style = "SlicerStyleLight1"
        sl.RowHeight = 17
        sc.CrossFilterType = 1  # show items with no data greyed out
        return sl

    y = 98
    for field, cap, h, cols in [("Gender", "Gender", 62, 2), ("SMS_Received", "SMS reminder", 62, 2),
                                ("Scholarship", "Scholarship (welfare)", 62, 2),
                                ("Age_Group", "Age group", 190, 1), ("Lead_Time_Group", "Lead time", 190, 1),
                                ("Chronic_Group", "Chronic conditions", 100, 1),
                                ("Patient_Type", "Patient type", 100, 1), ("Appt_Weekday", "Weekday", 100, 2),
                                ("Neighbourhood", "Neighbourhood", 236, 1)]:
        slicer(field, cap, y, h, cols)
        y += h + 8

    # timeline (date slicer) above the charts
    tc = wb.SlicerCaches.Add2(ptK, "Appointment_Date", "Timeline_Appointment_Date", xlTimeline)
    for p in all_pts[1:]:
        if p.Name != "ptDay":
            tc.PivotTables.AddPivotTable(p)
    try:
        tc.PivotTables.AddPivotTable(ptDay)
    except Exception:
        pass
    tl = tc.Slicers.Add(SlicerDestination=dash, Name="tl_AppointmentDate", Caption="Appointment date",
                        Top=158, Left=200, Width=W - 212, Height=84)
    tl.Top, tl.Left, tl.Width, tl.Height = 158, 200, W - 212, 84
    tl.TimelineViewState.Level = xlTimelineLevelDays
    try:
        tl.Style = "TimeSlicerStyleLight1"
    except Exception:
        pass

    text(200, CY + 4 * (CH + G) - 2, W - 212, 14,
         "Tip: Ctrl+click to multi-select in a slicer; use the clear-filter icon on each slicer/timeline to reset. "
         "Rates = Average of No_Show (1 = missed).", 8, False, MUTED, italic=True)

    # ------------------------------------------------------------ Insights sheet
    ins = wb.Worksheets.Add(After=dash)
    ins.Name = "Insights"
    xl.ActiveWindow.DisplayGridlines = False
    ins.Cells.Font.Name = FONT
    ins.Columns("A").ColumnWidth = 3
    ins.Columns("B").ColumnWidth = 34
    ins.Columns("C").ColumnWidth = 95
    ins.Range("B1").Value = "Insights & recommendations"
    ins.Range("B1").Font.Size = 16
    ins.Range("B1").Font.Bold = True
    ins.Range("B1").Font.Color = rgb(NAVY)
    ins.Range("B2").Value = "Based on all 106,982 cleaned appointments. Numbers are traceable to the KPIs and Analysis sheets."
    ins.Range("B2").Font.Italic = True
    ins.Range("B2").Font.Color = rgb(MUTED)
    blocks = [
        ("FINDINGS", [
            ("Headline", "20.3% of appointments are missed (21,675 of 106,982) across 60,270 patients: about 1 slot in 5 is wasted."),
            ("1. Lead time is the strongest driver",
             "Same-day bookings (35% of volume) have a 4.7% no-show rate. Anything booked ahead jumps to 22.9% (1-3 days) "
             "and climbs to 32.7% (15-30 days) and 34.4% (31-60 days). No-shows waited 15.8 days on average vs 8.7 for "
             "patients who came. Bookings 15+ days ahead are 25% of appointments but 41% of no-shows."),
            ("2. SMS reminders work - the raw numbers hide it",
             "Overall, SMS patients miss MORE (27.7% vs 16.7%). This is Simpson's paradox: SMS is never sent for same-day "
             "bookings, which almost always attend. Comparing within the same lead time, SMS lowers no-shows at every "
             "level (e.g. 30.0% vs 37.0% at 15-30 days, 28.1% vs 33.9% at 8-14 days). Yet half (50.5%) of advance bookings get no SMS."),
            ("3. Past behaviour predicts future behaviour",
             "Patients with an earlier no-show miss 29.4% of later appointments vs 17.1% for returning patients who never "
             "missed. 3,157 patients with 2+ no-shows account for 36% of all no-shows."),
            ("4. Young patients are the riskiest",
             "Teens (13-18) 26.1% and young adults (19-30) 24.7% vs seniors (61-75) 14.9% and 76+ 16.1%. Risk falls steadily after 30."),
            ("5. Socio-economic signal",
             "Scholarship (Bolsa Familia) patients miss 23.8% vs 19.9%. Patients with chronic conditions attend better "
             "(hypertension 17.3%, diabetes 18.0%) - regular care builds the habit."),
            ("6. What does NOT matter much",
             "Gender (20.4% F vs 20.1% M) and weekday (19.5%-21.3%) have little effect. Neighbourhoods range from 15.7% "
             "(Do Cabral) to 29.1% (Santos Dumont) among those with 500+ appointments."),
        ]),
        ("RECOMMENDATIONS", [
            ("Send SMS to every advance booking", "Extend reminders to the 50% of 1+ day bookings that get none; add a "
             "second reminder 1-2 days before for bookings 15+ days out."),
            ("Shorten lead times", "Keep more same-day / short-notice capacity; long waits are where no-shows concentrate."),
            ("Risk-based overbooking", "Use lead time + prior no-show + age 13-30 + scholarship as a simple risk score; "
             "overbook or call high-risk slots."),
            ("Target repeat no-show patients", "Phone confirmation for patients with a prior no-show; flag them at booking."),
            ("Fix data capture", "Store Patient_ID as text (5 IDs were corrupted), validate age (115) and block bookings "
             "dated after the appointment (5 rows)."),
        ]),
    ]
    r = 4
    for head, items in blocks:
        ins.Cells(r, 2).Value = head
        ins.Cells(r, 2).Font.Bold = True
        ins.Cells(r, 2).Font.Color = rgb("FFFFFF")
        ins.Range(ins.Cells(r, 2), ins.Cells(r, 3)).Interior.Color = rgb(NAVY if head == "FINDINGS" else TEAL)
        r += 1
        for k_, v in items:
            ins.Cells(r, 2).Value = k_
            ins.Cells(r, 2).Font.Bold = True
            ins.Cells(r, 3).Value = v
            ins.Range(ins.Cells(r, 2), ins.Cells(r, 3)).WrapText = True
            ins.Range(ins.Cells(r, 2), ins.Cells(r, 3)).VerticalAlignment = -4160
            ins.Range(ins.Cells(r, 2), ins.Cells(r, 3)).Borders(9).Color = rgb(LINE)
            r += 1
        r += 1

    # ------------------------------------------------------------ finish
    order = ["Dashboard", "Insights", "KPIs", "Analysis", "Pivot Tables", "Data", "Cleaning Log", "Data Dictionary"]
    wb.Worksheets(order[0]).Move(wb.Worksheets(1))
    for prev, name in zip(order, order[1:]):
        wb.Worksheets(name).Move(None, wb.Worksheets(prev))
    dash.Activate()
    dash.Range("A1").Select()
    xl.ActiveWindow.Zoom = 80
    xl.CalculateFull()
    wb.RefreshAll()
    xl.CalculateFull()
    # quick self-check
    print("cards:", [piv.Cells(20 + i, 2).Value for i in range(9)])
    print("header:", piv.Range("B30").Value)
    print("sheets:", [s.Name for s in wb.Worksheets])
    print("pivots:", piv.PivotTables().Count, "charts:", dash.ChartObjects().Count, "slicer caches:", wb.SlicerCaches.Count)
    if os.path.exists(OUT):
        os.remove(OUT)
    wb.SaveAs(OUT, FileFormat=51)
    wb.Close(False)
    print("saved", OUT)
finally:
    xl.ScreenUpdating = True
    xl.Quit()
