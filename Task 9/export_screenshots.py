"""Step 6: capture the HTML dashboard as PNG screenshots (headless Chromium via Playwright).

Writes screenshots/1_kpis_and_insights.png ... 6_dark_mode.png
Also re-checks that the page loads without console errors and that a filter changes the KPIs.
"""
import os

from playwright.sync_api import sync_playwright

URL = "file:///" + os.path.abspath("Customer_Dashboard.html").replace("\\", "/")
os.makedirs("screenshots", exist_ok=True)


def section_box(pg, first_h2, next_h2):
    """Clip from the top of section heading `first_h2` (0 = page top) to the top of `next_h2` (None = page end)."""
    return pg.evaluate("""([a, b]) => {
        const hs = Array.from(document.querySelectorAll('h2'));
        const top = a === 0 ? 0 : hs[a - 1].getBoundingClientRect().top + window.scrollY - 12;
        const bottom = b === null ? document.body.scrollHeight : hs[b - 1].getBoundingClientRect().top + window.scrollY - 16;
        return {x: 0, y: top, width: document.documentElement.clientWidth, height: bottom - top};
    }""", [first_h2, next_h2])


with sync_playwright() as p:
    browser = p.chromium.launch()
    pg = browser.new_page(viewport={"width": 1400, "height": 900}, color_scheme="light", device_scale_factor=1)
    errors = []
    pg.on("pageerror", lambda e: errors.append(str(e)))
    pg.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
    pg.goto(URL)
    pg.wait_for_timeout(2000)
    # h2 order: 1 Key insights, 2 Customers, 3 Spending, 4 Categories, 5 Ratings, 6 Patterns, 7 Recommendations
    shots = [("1_kpis_and_insights", 0, 3), ("2_spending_and_trends", 3, 4), ("3_categories_and_ratings", 4, 6),
             ("4_patterns_scorecard_recommendations", 6, None)]
    for name, a, b in shots:
        pg.screenshot(path=f"screenshots/{name}.png", clip=section_box(pg, a, b), full_page=True)
    before = pg.inner_text("#kpis .kpi .v")
    pg.select_option("#fCat", "2")          # Electronics
    pg.select_option("#fRb", "0")           # dissatisfied (1-2 stars)
    pg.wait_for_timeout(1200)
    after = pg.inner_text("#kpis .kpi .v")
    pg.screenshot(path="screenshots/5_filtered_electronics_dissatisfied.png", clip=section_box(pg, 0, 3), full_page=True)
    pg.click("#btnReset")
    pg.emulate_media(color_scheme="dark")
    pg.wait_for_timeout(1200)
    pg.screenshot(path="screenshots/6_dark_mode.png", clip=section_box(pg, 3, 5), full_page=True)
    browser.close()

print("customers before/after filter:", before, "->", after)
print("console errors:", errors or "none")
print("saved:", sorted(os.listdir("screenshots")))
