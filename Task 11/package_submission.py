"""Build the submission zip (NahlaNabil.zip) and check it stays under the 10 MB upload limit."""
import os
import zipfile

ZIP = "NahlaNabil.zip"
FILES = ["README.md", "KEY_INSIGHTS.md",
         "GameSales_Dashboard.xlsx", "GameSales_Base.xlsx",
         "Video_Games_Sales_as_at_22_Dec_2016.csv", "PS4_GamesSales.csv", "XboxOne_GameSales.csv",
         "Cleaned_Video_Games.csv", "Cleaned_PS4_Sales.csv", "Cleaned_XboxOne_Sales.csv",
         "cleaning_log.json", "analysis_summary.json",
         "clean_data.py", "analysis.py", "make_charts.py", "build_workbook.py",
         "build_dashboard.py", "export_screenshots.py", "package_submission.py"]
FOLDERS = ["charts", "screenshots"]

with zipfile.ZipFile(ZIP, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
    for f in FILES:
        if os.path.exists(f):
            z.write(f, f"Task 11 - Nahla Nabil/{f}")
        else:
            print("not found (skipped):", f)
    for folder in FOLDERS:
        for root, _, names in os.walk(folder):
            for n in names:
                p = os.path.join(root, n)
                z.write(p, f"Task 11 - Nahla Nabil/{p}")
    count = len(z.namelist())

size = os.path.getsize(ZIP) / 1e6
print(f"{ZIP}: {count} files, {size:.1f} MB ({'OK' if size < 10 else 'TOO BIG'} for the 10 MB limit)")
