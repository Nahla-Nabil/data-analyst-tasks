"""
Step 5: open the base workbook in Excel (COM) and add the interactive layer:
pivot tables, pivot charts, slicers, a date timeline, KPI cards driven by
GETPIVOTDATA/INDEX-MATCH and the insight panels.

Output: GameSales_Dashboard.xlsx
"""
import os

import pythoncom
import win32com.client as win32

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "GameSales_Base.xlsx")
OUT = os.path.join(HERE, "GameSales_Dashboard.xlsx")

# Excel constants
xlDatabase, xlRow, xlCol = 1, 1, 2
xlCount, xlSum, xlAverage = -4112, -4157, -4106
xlColumnClustered, xlBarClustered, xlDoughnut, xlLine = 51, 57, -4120, 4
xlValue, xlCategory, xlSecondary = 2, 1, 2
xlTimeline, xlTimelineLevelYears = 2, 1
FONT = "Arial"


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


NAVY, TEAL, CORAL, GOLD, SKY, GREY, INK, MUTED = "1F3B57", "1B998B", "E4572E", "E0A030", "9BC4E2", "F3F6F9", "22313F", "5A6B7B"
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

    pc = wb.PivotCaches().Create(SourceType=xlDatabase, SourceData="tblGames", Version=6)
    pivots = {}

    def new_pivot(name, label, col):
        piv.Cells(3, col).Value = label
        piv.Cells(3, col).Font.Bold = True
        piv.Cells(3, col).Font.Color = rgb(TEAL)
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
        """Data rows of one pivot column as an absolute range string."""
        t = pt.TableRange1
        r0, c0, n = t.Row, t.Column, t.Rows.Count
        c = col_letter(c0 + offset)
        return f"'Pivot Tables'!${c}${r0 + 1}:${c}${r0 + n - 1}"

    # KPI pivot (grand totals only) -> KPI cards and the region block
    ptK = new_pivot("ptKPI", "KPI measures (GETPIVOTDATA source for the cards)", 1)
    data_field(ptK, "Game", "Titles", xlCount, "#,##0")
    data_field(ptK, "Global_Sales", "Global sales", xlSum, "#,##0.0")
    data_field(ptK, "NA_Sales", "NA sales", xlSum, "#,##0.0")
    data_field(ptK, "EU_Sales", "EU sales", xlSum, "#,##0.0")
    data_field(ptK, "JP_Sales", "Japan sales", xlSum, "#,##0.0")
    data_field(ptK, "Other_Sales", "Rest of world sales", xlSum, "#,##0.0")
    ptK.DataPivotField.Orientation = xlRow

    ptGenre = new_pivot("ptGenre", "Sales by genre", 3)
    rows(ptGenre, "Genre")
    g_s = data_field(ptGenre, "Global_Sales", "Global sales  ", xlSum, "#,##0.0")
    ptGenre.ColumnGrand = False
    ptGenre.RowGrand = False
    sort_desc(ptGenre, "Genre", g_s.Name)

    ptPlat = new_pivot("ptPlatform", "Platforms by sales (chart shows the top 15)", 8)
    rows(ptPlat, "Platform")
    p_s = data_field(ptPlat, "Global_Sales", "Global sales   ", xlSum, "#,##0.0")
    ptPlat.ColumnGrand = False
    ptPlat.RowGrand = False
    sort_desc(ptPlat, "Platform", p_s.Name)

    ptPub = new_pivot("ptPub", "Top 10 publishers by sales", 14)
    rows(ptPub, "Publisher")
    u_s = data_field(ptPub, "Global_Sales", "Global sales    ", xlSum, "#,##0.0")
    ptPub.ColumnGrand = False
    ptPub.RowGrand = False
    sort_desc(ptPub, "Publisher", u_s.Name)
    # NOTE: PivotItems are indexed alphabetically, so the sorted tail is NOT hidden
    # here - the chart simply reads the first 10 (best-selling) rows of the pivot.

    ptTrend = new_pivot("ptTrend", "Titles and sales by release year", 20)
    rows(ptTrend, "Release_Year")
    t_s = data_field(ptTrend, "Global_Sales", "Global sales     ", xlSum, "#,##0.0")
    t_t = data_field(ptTrend, "Game", "Titles      ", xlCount, "#,##0")
    ptTrend.ColumnGrand = False
    ptTrend.RowGrand = False
    try:  # rows with no release year
        ptTrend.PivotFields("Release_Year").PivotItems("(blank)").Visible = False
    except Exception as e:
        print("blank year", e)

    ptCri = new_pivot("ptCritic", "Average sales by critic band", 26)
    rows(ptCri, "Critic_Band")
    c_a = data_field(ptCri, "Global_Sales", "Avg sales       ", xlAverage, "#,##0.000")
    c_t = data_field(ptCri, "Game", "Titles        ", xlCount, "#,##0")
    ptCri.ColumnGrand = False
    ptCri.RowGrand = False
    sort_desc(ptCri, "Critic_Band", c_a.Name)

    ptTop = new_pivot("ptTop", "Titles ranked by sales (chart shows the top 10)", 31)
    rows(ptTop, "Game")
    gm_s = data_field(ptTop, "Global_Sales", "Global sales        ", xlSum, "#,##0.0")
    ptTop.ColumnGrand = False
    ptTop.RowGrand = False
    sort_desc(ptTop, "Game", gm_s.Name)

    # region block (live GETPIVOTDATA values, feeds the donut chart)
    piv.Range("AJ3").Value = "Regional mix (live)"
    piv.Range("AJ3").Font.Bold = True
    piv.Range("AJ3").Font.Color = rgb(TEAL)
    piv.Range("AJ5").Value = "Region"
    piv.Range("AK5").Value = "Global sales (M)"
    gp = lambda f: f'IFERROR(GETPIVOTDATA("{f}",\'Pivot Tables\'!$A$5),0)'
    regions = [("North America", "NA sales"), ("Europe", "EU sales"),
               ("Japan", "Japan sales"), ("Rest of world", "Rest of world sales")]
    for i, (lab, f) in enumerate(regions):
        piv.Cells(6 + i, 36).Value = lab
        piv.Cells(6 + i, 37).Formula = f"={gp(f)}"
        piv.Cells(6 + i, 37).NumberFormat = "#,##0.0"
    for col, w in zip(("A", "C", "H", "N", "T", "Z", "AE", "AJ", "AK", "AL", "AM", "AO", "AP", "AR", "AS"),
                      (16, 18, 14, 20, 14, 16, 30, 16, 16, 14, 12, 20, 12, 30, 12)):
        piv.Columns(col).ColumnWidth = w

    piv.Range("AL3").Value = "Chart feeds (live formulas over the pivots)"
    piv.Range("AL3").Font.Bold = True
    piv.Range("AL3").Font.Color = rgb(TEAL)

    piv.Range("AL5").Value = "Platform"
    piv.Range("AM5").Value = "Sales"
    for i in range(15):
        r = 6 + i
        piv.Cells(r, 38).Formula = f"=IF(H{r}=\"\",\"\",H{r})"
        piv.Cells(r, 39).Formula = f"=IF(I{r}=\"\",\"\",I{r})"
        piv.Cells(r, 39).NumberFormat = "#,##0.0"

    piv.Range("AO5").Value = "Publisher"
    piv.Range("AP5").Value = "Sales"
    for i in range(10):
        r = 6 + i
        piv.Cells(r, 41).Formula = f"=IF(N{r}=\"\",\"\",N{r})"
        piv.Cells(r, 42).Formula = f"=IF(O{r}=\"\",\"\",O{r})"
        piv.Cells(r, 42).NumberFormat = "#,##0.0"

    piv.Range("AR5").Value = "Title"
    piv.Range("AS5").Value = "Sales"
    for i in range(10):
        r = 6 + i
        piv.Cells(r, 44).Formula = f"=IF(AE{r}=\"\",\"\",AE{r})"
        piv.Cells(r, 45).Formula = f"=IF(AF{r}=\"\",\"\",AF{r})"
        piv.Cells(r, 45).NumberFormat = "#,##0.0"

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
    hb = box(0, 0, W - 4, 58, NAVY, None, radius=False)
    text(18, 8, 820, 26, "Video Game Industry Dashboard", 20, True, "FFFFFF")
    text(18, 36, 940, 16, "", 9, False, "D6E4F0", link="='Pivot Tables'!$B$78")
    text(W - 372, 10, 354, 44,
         "Source: Video_Games_Sales_as_at_22_Dec_2016.csv (Kaggle, snapshot 22 Dec 2016)\n"
         "16,717 titles  |  1980-2020  |  31 platforms  |  8,920M copies sold",
         8, False, "D6E4F0", align=3)

    # ------------------------------------------------------------ KPI card formulas
    def topf(name_rng, val_rng):
        return f'=IFERROR(INDEX({name_rng},MATCH(MAX({val_rng}),{val_rng},0)),"-")'

    piv.Range("A60").Value = "Dashboard card values (formulas - they follow the slicers)"
    piv.Range("A60").Font.Bold = True
    piv.Range("A60").Font.Color = rgb(TEAL)
    calc = [
        ("Titles in selection", f"={gp('Titles')}", "#,##0"),
        ("Global sales (M)", f"={gp('Global sales')}", "#,##0.0"),
        ("Avg sales per title (M)", "=IFERROR(B63/B62,0)", "#,##0.000"),
        ("Top genre", topf(col_range(ptGenre), col_range(ptGenre, 1)), "@"),
        ("Top platform", topf(col_range(ptPlat), col_range(ptPlat, 1)), "@"),
        ("Top publisher", topf(col_range(ptPub), col_range(ptPub, 1)), "@"),
        ("Best-selling title", topf(col_range(ptTop), col_range(ptTop, 1)), "@"),
    ]
    for i, (lab, f, fmt) in enumerate(calc):
        piv.Cells(62 + i, 1).Value = lab
        piv.Cells(62 + i, 2).Formula = f
        piv.Cells(62 + i, 2).NumberFormat = fmt
        piv.Cells(62 + i, 2).Font.Bold = True

    piv.Range("A69").Value = "Card and header text (linked to the dashboard text boxes)"
    piv.Range("A69").Font.Bold = True
    subs = {
        71: '="titles in the current selection"',
        72: '="million copies sold (global)"',
        73: '="sales per title in the selection"',
        74: '="top genre by global sales"',
        75: '="top platform by global sales"',
        76: '="top publisher by sales"',
        77: '="best-selling title (all platforms)"',
        78: '="Current selection: "&TEXT(B62,"#,##0")&" titles   |   "&TEXT(B63,"#,##0.0")&"M global sales   |   '
            '"&TEXT(B64,"0.000")&"M per title   |   top genre: "&B65&"   |   top platform: "&B66',
    }
    for r, f in subs.items():
        piv.Cells(r, 2).Formula = f

    # KPI cards
    cards = [("TITLES", 62, 71, NAVY, 18), ("GLOBAL SALES", 63, 72, NAVY, 18),
             ("AVG PER TITLE", 64, 73, TEAL, 18), ("TOP GENRE", 65, 74, CORAL, 13),
             ("TOP PLATFORM", 66, 75, CORAL, 13), ("TOP PUBLISHER", 67, 76, GOLD, 12),
             ("BEST SELLER", 68, 77, TEAL, 12)]
    x0, top, gap = 200, 70, 10
    cw = (W - x0 - 12 - gap * (len(cards) - 1)) / len(cards)
    for i, (lab, vr, sr, accent, vsize) in enumerate(cards):
        left = x0 + i * (cw + gap)
        box(left, top, cw, 82)
        box(left, top, 5, 82, accent, None, radius=False)
        text(left + 12, top + 8, cw - 16, 14, lab, 8, True, MUTED)
        text(left + 12, top + 24, cw - 16, 30, "", vsize, True, accent, link=f"='Pivot Tables'!$B${vr}")
        text(left + 12, top + 58, cw - 16, 18, "", 7.5, False, MUTED, link=f"='Pivot Tables'!$B${sr}")

    # ------------------------------------------------------------ charts
    def style_chart(ch, title_, legend=False, pct_axis=False):
        try:
            ch.ShowAllFieldButtons = False
        except Exception:
            pass  # plain (non pivot) charts have no field buttons
        ch.HasTitle = True
        ch.ChartTitle.Text = title_
        ch.ChartTitle.Format.TextFrame2.TextRange.Font.Size = 11
        ch.ChartTitle.Format.TextFrame2.TextRange.Font.Bold = True
        ch.ChartTitle.Format.TextFrame2.TextRange.Font.Fill.ForeColor.RGB = rgb(NAVY)
        ch.ChartArea.Format.TextFrame2.TextRange.Font.Name = FONT
        ch.ChartArea.Format.Line.ForeColor.RGB = rgb(LINE)
        ch.ChartArea.RoundedCorners = True
        ch.HasLegend = legend
        if legend:
            ch.Legend.Position = -4160
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

    def color_series(s, hexcol, labels=True, fmt="#,##0.0", size=8):
        s.Format.Fill.ForeColor.RGB = rgb(hexcol)
        if labels:
            s.HasDataLabels = True
            s.DataLabels().NumberFormat = fmt
            s.DataLabels().Font.Size = size
            s.DataLabels().Font.Color = rgb(INK)

    def chart(pt, ctype, left, top_, w, h, source=None):
        s = shapes.AddChart2(-1, ctype, left, top_, w, h)
        s.Chart.SetSourceData(source if source is not None else pt.TableRange1)
        s.Placement = 3
        return s.Chart

    CX, CY, CW, CH, G = 200, 262, 388, 250, 10
    pos = lambda c, r: (CX + c * (CW + G), CY + r * (CH + G))

    ch = chart(ptTrend, xlColumnClustered, *pos(0, 0), CW * 2 + G, CH)
    style_chart(ch, "Release year: sales (bars) and number of titles (line)", legend=True)
    s1, s2 = ch.SeriesCollection(1), ch.SeriesCollection(2)
    s1.Format.Fill.ForeColor.RGB = rgb(SKY)
    s2.ChartType = xlLine
    s2.AxisGroup = xlSecondary
    s2.Format.Line.ForeColor.RGB = rgb(CORAL)
    s2.Format.Line.Weight = 2.25
    ch.Axes(xlValue).TickLabels.NumberFormat = "#,##0"
    ch.Axes(xlValue, xlSecondary).TickLabels.NumberFormat = "#,##0"
    ch.Axes(xlValue, xlSecondary).TickLabels.Font.Size = 8
    ch.Axes(xlValue, xlSecondary).MinimumScale = 0
    ch.Axes(xlCategory).TickLabels.Font.Size = 7
    ch.ChartGroups(1).GapWidth = 40

    reg_rng = piv.Range("AJ5:AK9")
    s = shapes.AddChart2(-1, xlDoughnut, *pos(2, 0), CW, CH)
    ch = s.Chart
    ch.SetSourceData(reg_rng, 2)
    s.Placement = 3
    style_chart(ch, "Regional mix of global sales", legend=True)
    sr = ch.SeriesCollection(1)
    for i, colr in enumerate((NAVY, TEAL, CORAL, SKY), 1):
        sr.Points(i).Format.Fill.ForeColor.RGB = rgb(colr)
    sr.HasDataLabels = True
    dl = sr.DataLabels()
    dl.ShowValue = False
    dl.ShowPercentage = True
    dl.NumberFormat = "0.0%"
    dl.Font.Size = 9
    dl.Font.Bold = True
    dl.Font.Color = rgb("FFFFFF")
    ch.ChartGroups(1).DoughnutHoleSize = 55
    ch.Legend.Position = -4107

    ch = chart(ptGenre, xlBarClustered, *pos(0, 1), CW, CH)
    style_chart(ch, "Global sales by genre (top first)")
    color_series(ch.SeriesCollection(1), TEAL, labels=False)
    ch.ChartGroups(1).GapWidth = 55
    ch.Axes(xlCategory).ReversePlotOrder = True
    ch.Axes(xlCategory).TickLabels.Font.Size = 7

    ch = chart(ptPlat, xlColumnClustered, *pos(1, 1), CW, CH, source=piv.Range("AL5:AM20"))
    style_chart(ch, "Top 15 platforms by global sales")
    color_series(ch.SeriesCollection(1), NAVY)
    ch.ChartGroups(1).GapWidth = 55
    ch.Axes(xlCategory).TickLabels.Font.Size = 7

    ch = chart(ptPub, xlBarClustered, *pos(2, 1), CW, CH, source=piv.Range("AO5:AP15"))
    style_chart(ch, "Top 10 publishers by global sales")
    color_series(ch.SeriesCollection(1), GOLD, labels=False)
    ch.ChartGroups(1).GapWidth = 55
    ch.Axes(xlCategory).ReversePlotOrder = True
    ch.Axes(xlCategory).TickLabels.Font.Size = 7

    ch = chart(ptCri, xlColumnClustered, *pos(0, 2), CW * 2 + G, CH)
    style_chart(ch, "Average sales per title by critic band (do reviews sell?)", legend=True)
    s1 = ch.SeriesCollection(1)
    s2 = ch.SeriesCollection(2)
    color_series(s1, CORAL, fmt="#,##0.00")
    s2.ChartType = xlLine
    s2.AxisGroup = xlSecondary
    s2.Format.Line.ForeColor.RGB = rgb(NAVY)
    s2.Format.Line.Weight = 2
    ch.Axes(xlValue, xlSecondary).TickLabels.NumberFormat = "#,##0"
    ch.Axes(xlValue, xlSecondary).MinimumScale = 0
    ch.Axes(xlValue, xlSecondary).TickLabels.Font.Size = 8
    ch.ChartGroups(1).GapWidth = 60
    ch.Axes(xlCategory).TickLabels.Font.Size = 8

    ch = chart(ptTop, xlBarClustered, *pos(2, 2), CW, CH, source=piv.Range("AR5:AS15"))
    style_chart(ch, "Best-selling titles (platforms added up)")
    color_series(ch.SeriesCollection(1), TEAL, labels=False)
    ch.ChartGroups(1).GapWidth = 55
    ch.Axes(xlCategory).ReversePlotOrder = True
    ch.Axes(xlCategory).TickLabels.Font.Size = 7

    # insights panel (static, whole-file findings)
    ix, iy = pos(0, 3)
    box(ix, iy, CW * 2 + G, CH)
    text(ix + 12, iy + 8, CW * 2 + G - 24, 18, "KEY INSIGHTS (all 16,717 rows)", 11, True, NAVY)
    insights = (
        "1. Scale and long tail: 16,717 titles sold 8,920M copies, but the median title sells only 0.17M and "
        "35% never reach 0.1M - the top 1% of titles take 22% of all sales.\n"
        "2. Concentration: Nintendo alone is 20.1% of sales, the top 10 publishers 70.2%, Action 19.6% and PS2 14.1%. "
        "Platform families are almost a tie: PlayStation 40.2% vs Nintendo 39.2%.\n"
        "3. Regions are moving: North America is 49.4% overall but fell from 63% (1980s) to 44% (2010s); Japan fell "
        "27% -> 12% while Europe grew from 8% to 33%.\n"
        "4. Reviews track sales only weakly (Pearson 0.25, Spearman 0.39), yet 90+ titles average 2.83M vs 0.27M for "
        "scores under 60, and reviewed titles sell 0.67M vs 0.39M unreviewed.\n"
        "5. The market peaked in 2008; the 2000s decade alone is 52.5% of every sale in the file.\n"
        "6. Current consoles: PS4 595.6M vs Xbox One 269.0M - the PS4 is Europe-led (43% of its sales), "
        "the Xbox One is North America-led (60%).\n"
        "7. Data quality: 111 release years recovered from another platform, 158 rows carry no year and 4 rows are "
        "dated after the 22 Dec 2016 cutoff - all flagged on the Data sheet."
    )
    t = text(ix + 12, iy + 30, CW * 2 + G - 24, CH - 36, insights, 9.5, False, INK)
    t.TextFrame2.TextRange.ParagraphFormat.SpaceAfter = 3

    # how-to panel
    hx, hy = pos(2, 3)
    box(hx, hy, CW, CH)
    text(hx + 12, hy + 8, CW - 24, 18, "HOW TO USE THIS FILE", 11, True, NAVY)
    howto = (
        "- Every card, chart and the region donut recalculates for the slicer selection; the KPIs and Analysis "
        "sheets keep the unfiltered values for comparison.\n"
        "- Filters: platform family, platform, genre, publisher group, ESRB rating and decade, plus a release-date "
        "timeline. Use the clear-filter icon on each slicer to reset.\n"
        "- Sheets: KPIs (25 live formulas), Analysis (10 tables), Pivot Tables (the numbers behind the cards), "
        "Data (tblGames, 30 columns), Cleaning Log (13 steps) and Data Dictionary.\n"
        "- Quality flags on the Data sheet: Flag_Year_Imputed (111), Flag_Year_Unknown (158), Flag_Year_Future (4), "
        "Flag_Unnamed (1), Flag_Unknown_Publisher (54).\n"
        "- Charts follow Excel's chart engine: right-click any chart to change the type or the colours."
    )
    t = text(hx + 12, hy + 30, CW - 24, CH - 36, howto, 9.5, False, INK)
    t.TextFrame2.TextRange.ParagraphFormat.SpaceAfter = 3

    # ------------------------------------------------------------ slicers
    box(8, 70, 182, CY + 4 * (CH + G) - 10 - 70, "FFFFFF")
    text(18, 78, 160, 16, "FILTERS", 10, True, NAVY)
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

    y = 98
    for field, cap, h, cols in [("Platform_Family", "Platform family", 74, 2),
                                ("Platform", "Platform", 200, 2),
                                ("Genre", "Genre", 158, 2),
                                ("Publisher_Group", "Publisher group", 112, 2),
                                ("Rating_Band", "ESRB rating", 112, 1),
                                ("Decade", "Decade", 96, 2)]:
        slicer(field, cap, y, h, cols)
        y += h + 8

    # timeline (date slicer) between the cards and the charts
    tc = wb.SlicerCaches.Add2(ptK, "Release_Date", "Timeline_Release_Date", xlTimeline)
    for p in all_pts[1:]:
        tc.PivotTables.AddPivotTable(p)
    tl = tc.Slicers.Add(SlicerDestination=dash, Name="tl_ReleaseDate", Caption="Release date",
                        Top=164, Left=200, Width=W - 212, Height=84)
    tl.Top, tl.Left, tl.Width, tl.Height = 164, 200, W - 212, 84
    try:
        tl.TimelineViewState.Level = xlTimelineLevelYears
        print("timeline level set to years")
    except Exception as e:
        print("timeline level error:", e)
    try:
        tl.Style = "TimeSlicerStyleLight1"
    except Exception:
        pass

    text(200, CY + 4 * (CH + G) - 2, W - 212, 14,
         "Tip: Ctrl+click to multi-select in a slicer. All values on this sheet are live; the KPIs and Analysis "
         "sheets always show the full file. Sales are in millions of copies.", 8, False, MUTED, italic=True)

    # ------------------------------------------------------------ finish
    order = ["Dashboard", "KPIs", "Analysis", "Pivot Tables", "Data", "Cleaning Log", "Data Dictionary"]
    wb.Worksheets(order[0]).Move(wb.Worksheets(1))
    for prev, name in zip(order, order[1:]):
        wb.Worksheets(name).Move(None, wb.Worksheets(prev))
    dash.Activate()
    dash.Range("A1").Select()
    xl.ActiveWindow.Zoom = 80
    xl.CalculateFull()
    wb.RefreshAll()
    xl.CalculateFull()
    print("cards:", [piv.Cells(62 + i, 2).Value for i in range(7)])
    print("header:", piv.Range("B78").Value)
    print("sheets:", [s_.Name for s_ in wb.Worksheets])
    print("pivots:", piv.PivotTables().Count, "charts:", dash.ChartObjects().Count,
          "slicer caches:", wb.SlicerCaches.Count)
    if os.path.exists(OUT):
        os.remove(OUT)
    wb.SaveAs(OUT, FileFormat=51)  # .xlsx
    wb.Close(False)
    print("saved", OUT)
finally:
    xl.ScreenUpdating = True
    xl.Quit()
