"""Step 7: short PDF summary report of the key findings (for readers who will not open the dashboard).

Reads  analysis_summary.json, charts/*.png
Writes Customer_Analysis_Summary.pdf (A4, 5 pages: KPIs and summary, 6 findings with charts, recommendations)
"""
import json

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Image, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

pdfmetrics.registerFont(TTFont("Segoe", "C:/Windows/Fonts/segoeui.ttf"))
pdfmetrics.registerFont(TTFont("Segoe-Bold", "C:/Windows/Fonts/segoeuib.ttf"))
pdfmetrics.registerFontFamily("Segoe", normal="Segoe", bold="Segoe-Bold", italic="Segoe", boldItalic="Segoe-Bold")

S = json.load(open("analysis_summary.json", encoding="utf-8"))
K, T = S["kpi"], S["tests"]
INK, INK2, MUTED, ACCENT, BLUE, GRID, WASH = (colors.HexColor(c) for c in
                                              ("#0b0b0b", "#52514e", "#898781", "#1f3a5f", "#2a78d6", "#e1e0d9", "#f4f5f2"))
W = A4[0] - 32 * mm

st = lambda name, **kw: ParagraphStyle(name, fontName=kw.pop("font", "Segoe"), textColor=kw.pop("color", INK2), **kw)
H1 = st("h1", font="Segoe-Bold", fontSize=20, leading=24, color=ACCENT, spaceAfter=2)
SUB = st("sub", fontSize=9.5, leading=13, color=MUTED, spaceAfter=10)
H2 = st("h2", font="Segoe-Bold", fontSize=13, leading=17, color=ACCENT, spaceBefore=8, spaceAfter=4)
BODY = st("body", fontSize=9.5, leading=13.5, alignment=TA_LEFT, spaceAfter=4)
SMALL = st("small", fontSize=8, leading=11, color=MUTED)
BUL = st("bul", fontSize=9.5, leading=13.5, leftIndent=10, bulletIndent=0, spaceAfter=2)
KL = st("kl", fontSize=7.5, leading=9.5, color=INK2)
KV = st("kv", font="Segoe-Bold", fontSize=15, leading=18, color=INK)
KD = st("kd", fontSize=7, leading=9, color=MUTED)
TH = st("th", font="Segoe-Bold", fontSize=8.5, leading=11, color=INK)
TD = st("td", fontSize=8.5, leading=11.5, color=INK2)

h1 = S["h1"]
g24, g25 = h1[1]["revenue"] / h1[0]["revenue"] - 1, h1[2]["revenue"] / h1[1]["revenue"] - 1


def chart(name, width=W):
    img = Image(f"charts/{name}.png")
    img.drawWidth, img.drawHeight = width, width * img.imageHeight / img.imageWidth
    return img


def bullets(items):
    return [Paragraph(t, BUL, bulletText="•") for t in items]


def finding(num, title, text, chart_name, notes):
    return [KeepTogether([Paragraph(f"Finding {num}: {title}", H2), Paragraph(text, BODY), chart(chart_name)] + bullets(notes))]


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Segoe", 7.5)
    canvas.setFillColor(MUTED)
    canvas.drawString(16 * mm, 10 * mm, "Customer Data Analysis · VOLTIX Data Analyst Internship · Task 9 · Nahla Nabil")
    canvas.drawRightString(A4[0] - 16 * mm, 10 * mm, f"Page {doc.page}")
    canvas.restoreState()


story = [
    Paragraph("Customer Data Analysis: Summary Report", H1),
    Paragraph(f"{K['customers']:,} customers, one purchase each, from 27 Oct 2022 to 23 Jul 2025 · source: Customers_Fakedata.csv "
              f"({K['raw_rows']:,} raw rows, {K['duplicates_removed']} duplicates removed) · tools: Python (pandas, SciPy, matplotlib), "
              "an interactive HTML dashboard and Power BI", SUB),
]

tiles = [("Customers", f"{K['customers']:,}", "unique IDs"),
         ("Recorded revenue", f"${K['revenue'] / 1e6:.2f}M", f"{K['priced_purchases']:,} priced orders"),
         ("Average order", f"${K['aov']:.0f}", f"median ${K['median_order']:.0f}"),
         ("Purchases / month", f"{K['purchases_per_full_month']:.1f}", f"${K['revenue_per_full_month'] / 1000:.1f}K / month"),
         ("Average rating", f"{K['avg_rating']:.2f} / 5", f"{K['rated']:,} valid ratings"),
         ("Satisfied (4-5 stars)", f"{K['satisfied_share']:.0%}", "of valid ratings"),
         ("Dissatisfied (1-2 stars)", f"{K['dissatisfied_share']:.0%}", "of valid ratings"),
         ("Complete records", f"{K['complete_record_rate']:.1%}", "valid in all 6 fields")]
cells = [[[Paragraph(l, KL), Paragraph(v, KV), Paragraph(d, KD)] for l, v, d in tiles[r * 4:(r + 1) * 4]] for r in range(2)]
kpi = Table(cells, colWidths=[W / 4] * 4, rowHeights=[17 * mm] * 2)
kpi.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), WASH), ("BOX", (0, 0), (-1, -1), 0.6, colors.white),
                         ("INNERGRID", (0, 0), (-1, -1), 3, colors.white), ("VALIGN", (0, 0), (-1, -1), "TOP"),
                         ("LEFTPADDING", (0, 0), (-1, -1), 7), ("TOPPADDING", (0, 0), (-1, -1), 5)]))
story += [kpi, Spacer(1, 8), Paragraph("Summary", H2)]
story += bullets([
    f"<b>The biggest finding is the data itself.</b> Only {K['complete_record_rate']:.1%} of records are complete: age is usable for "
    f"{S['quality']['Age']:.0%} of customers, {1 - S['quality']['Product category']:.0%} of purchases have no category, and no phone number is real.",
    f"<b>Big tickets carry the revenue.</b> ${K['revenue'] / 1e6:.2f}M in recorded revenue; $750+ orders are "
    f"{K['big_ticket_order_share']:.0%} of orders but {K['big_ticket_revenue_share']:.0%} of revenue.",
    f"<b>Satisfaction is split down the middle.</b> Average {K['avg_rating']:.2f} / 5: {K['dissatisfied_share']:.0%} dissatisfied, "
    f"{K['satisfied_share']:.0%} satisfied, and the same in every category, gender, age group and order size.",
    f"<b>Sales are flat.</b> About {K['purchases_per_full_month']:.0f} purchases and ${K['revenue_per_full_month'] / 1000:.0f}K a month for "
    f"{K['full_months']} months (trend p = {T['Monthly purchases trend (linear regression, full months)']:.2f}); January-June revenue "
    f"{g24:+.1%} in 2024 and {g25:+.1%} in 2025. The apparent August-September dip is a calendar artefact.",
    "<b>No segment behaves differently.</b> None of 14 tests on gender, age, category, weekday or email provider is significant. "
    "The file behaves like randomly generated data, so this is the expected result.",
])
story += [Spacer(1, 4), Paragraph("How the data was cleaned", H2), Paragraph(
    "50 exact duplicate rows and 2 redundant columns were removed. Impossible values were blanked, not guessed: age placeholders -1 and 200 "
    "(1,099 rows), rating '10' on a 1-5 scale (291), the date '32/13/2020' (118). Six spellings of gender were merged, and blank categories "
    "became 'Unknown'. Missing amounts and ages were <b>not imputed</b>, because imputing would invent 5% of revenue and 76% of ages. Each metric "
    "uses every row that is valid for it. This is safe because the gaps are independent of each other (maximum correlation 0.04). "
    "Details: DATA_QUALITY_REPORT.md.", BODY), chart("01_data_quality", W * 0.92), PageBreak()]

story += finding(1, "the biggest finding is the data itself",
                 "Age is the weakest field: only 495 of 2,100 customers have a real age. The rest are the placeholders -1 or 200, or blank. "
                 "Gender is recorded for 87%, but it contradicts the first name in 50% of rows, so neither field can yet support targeting.",
                 "02_age_gender",
                 ["Real ages cover every value from 15 to 90 (median 55), spread evenly across five 15-year bands.",
                  "Recommendation: collect a date of birth, not a free-text age, and use drop-down lists for gender, category and rating."])
story += finding(2, "big tickets carry the revenue",
                 f"Order values are spread evenly from $5 to $1,000, so there is no typical basket. Because of that, the biggest orders dominate "
                 f"revenue: one order in four is $750+, and those orders bring {K['big_ticket_revenue_share']:.0%} of revenue.",
                 "03_spend",
                 ["An average $750+ order ($876) is worth seven average orders under $250 ($125).",
                  "Recommendation: give big orders priority service, and A/B-test bundles or upgrades on $250-749 orders."])
story += [PageBreak()]
story += finding(3, "as many unhappy customers as happy ones",
                 "All five star levels get about a fifth of the ratings. The split is the same in every category, gender, age group "
                 f"and order size, and the rating does not depend on how much was spent (rho = {S['corr']['amount_rating_rho']}).",
                 "05_ratings",
                 ["Dissatisfaction is not explained by any product, price or customer group recorded here. The cause is outside the data, "
                  "for example delivery, service or product quality.",
                  "Recommendation: add a reason code to every rating, and follow up every 1-2 star rating within 48 hours "
                  "(target: dissatisfied share below 25%, average rating 3.5)."])
story += finding(4, "sales are flat",
                 f"Revenue swings between about $20K and $40K a month around a flat average of ${K['revenue_per_full_month'] / 1000:.1f}K, "
                 "with no upward or downward trend over 32 complete months.",
                 "06_trend",
                 [f"Like-for-like January-June revenue: ${h1[0]['revenue'] / 1000:.1f}K (2023), ${h1[1]['revenue'] / 1000:.1f}K (2024) and "
                  f"${h1[2]['revenue'] / 1000:.1f}K (2025). The business is stable, but growth will need a deliberate action."])
story += [PageBreak()]
story += finding(5, "no seasonality, but two traps that look like patterns",
                 "In raw totals, August and September look about a third weaker than other months, and 2025-Q3 looks like a collapse. "
                 "Both are artefacts: August and September occur in only 2 of the years covered, and 2025-Q3 holds only 23 days of data. "
                 "Measured per 30 days of data, every month is alike.",
                 "07_seasonality",
                 ["Weekdays are also flat (271-303 purchases each). Reports on this data should always use complete periods and compare rates, not totals."])
story += finding(6, "no category or customer segment stands out",
                 f"Each of the five categories brings 14-16% of revenue. {K['top_category']} leads, but order values do not differ between "
                 f"categories (p = {T['Amount by category (Kruskal-Wallis)']:.2f}). {K['unknown_category_revenue_share']:.0%} of revenue "
                 f"(${K['unknown_category_revenue'] / 1000:.0f}K) has no category at all.",
                 "04_categories",
                 ["The same holds for gender, age, weekday and email provider (see the next chart): every difference is within chance."])
story += [chart("08_segment_comparison", W * 0.76), Paragraph(
    "Each dot is a segment average and each bar its 95% confidence interval. 2 of 35 intervals miss the overall line, about what chance alone "
    "produces (1.8).", SMALL), Spacer(1, 4)]

story += [Paragraph("Recommendations", H2)]
recs = [
    ("1", "Fix data capture at the source: date of birth instead of free-text age; drop-downs for gender, category and rating (1-5 only); "
          "a date picker; phone validation; no duplicate IDs on import.", "Complete records 9.7% → 90%+"),
    ("2", "Back-fill a category for the 565 uncategorised purchases ($268K of revenue) from the order or product system.",
     "Revenue with no category 26% → 0%"),
    ("3", "Find out why 2 in 5 customers are dissatisfied: add a reason code and comment to each rating, link ratings to delivery and "
          "returns data, and follow up every 1-2 star rating within 48 hours.", "Avg rating 3.03 → 3.5; dissatisfied 39% → <25%"),
    ("4", "Protect and grow big orders: priority service for $750+ orders (45% of revenue), and A/B-tested bundles or upgrades on $250-749 "
          "orders. Use experiments, not demographic targeting, because no segment behaves differently.", "Share of $750+ orders; AOV"),
    ("5", "Start measuring loyalty: one persistent customer ID across orders, so that repeat rate and lifetime value become measurable. "
          "Track monthly purchases against the ~60 / month baseline.", "Repeat-purchase rate; purchases / month"),
]
rt = Table([[Paragraph("#", TH), Paragraph("Action", TH), Paragraph("Measure it with", TH)]] +
           [[Paragraph(a, TD), Paragraph(b, TD), Paragraph(c, TD)] for a, b, c in recs], colWidths=[8 * mm, W * 0.66, W - 8 * mm - W * 0.66])
rt.setStyle(TableStyle([("LINEBELOW", (0, 0), (-1, 0), 0.8, INK2), ("LINEBELOW", (0, 1), (-1, -1), 0.4, GRID),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"), ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5)]))
story += [rt, Spacer(1, 6), Paragraph("Limitations", H2)]
story += bullets([
    "Each customer has exactly one purchase, so there is no repeat-purchase, retention or lifetime-value analysis.",
    "Age results rest on 495 customers (24%), and gender contradicts the first name in half of the rows.",
    "Revenue is recorded revenue: 97 purchases (about $49K) have no amount, and they were not estimated.",
    "The file behaves like randomly generated data: amounts uniform from $5 to $1,000 (KS p = 0.50), ages uniform from 15 to 90 "
    "(p = 0.16), ratings equally likely (p = 0.09), gender unrelated to the first name (p = 0.12), and exactly a 1,000-day window. "
    "\"No difference\" therefore describes this file, not a real customer base.",
])
story += [Spacer(1, 6), Paragraph("Deliverables", H2)]
story += bullets([
    "<b>Customer_Dashboard.html</b>: an interactive dashboard (8 KPIs, 14 charts, a segment scorecard, 9 filters plus click-to-filter). It opens offline in any browser.",
    "<b>Customer_Dashboard.pbix</b>: the same analysis as a 5-page Power BI report with 30 DAX measures. Also included: KEY_INSIGHTS.md, "
    "DATA_QUALITY_REPORT.md, Cleaned_Customers.csv, charts/ and the Python scripts that rebuild everything from the raw file.",
])

doc = SimpleDocTemplate("Customer_Analysis_Summary.pdf", pagesize=A4, leftMargin=16 * mm, rightMargin=16 * mm, topMargin=14 * mm,
                        bottomMargin=16 * mm, title="Customer Data Analysis - Summary Report", author="Nahla Nabil",
                        subject="VOLTIX Data Analyst Internship - Task 9")
doc.build(story, onFirstPage=footer, onLaterPages=footer)
print("wrote Customer_Analysis_Summary.pdf")
