"""Build the submission zip (NahlaNabil_Task12.zip). Raw data and the base
workbook are left out (the task provides the raw file; the base is rebuilt
by script) to keep the upload small."""
import os
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ZIP = os.path.join(HERE, "NahlaNabil_Task12.zip")
FILES = ["README.md", "FINAL_REPORT.md", "KEY_INSIGHTS.md",
         "Cleaned_AB_NYC_2019.csv",
         "Airbnb_Dashboard.xlsx", "Airbnb_NYC_Dashboard.pbix", "Airbnb_NYC_Dashboard.html",
         "cleaning_log.json", "analysis_summary.json",
         "clean_data.py", "analysis.py", "make_charts.py",
         "build_dashboard.py", "build_excel_base.py", "build_excel_dashboard.py",
         "build_powerbi.py", "export_screenshots.py", "package_submission.py"]
FOLDERS = ["charts", "screenshots"]
PREFIX = "Task 12 - Nahla Nabil"


def pack(zip_path, files, folders):
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for f in files:
            p = os.path.join(HERE, f)
            if os.path.exists(p):
                z.write(p, f"{PREFIX}/{f}")
            else:
                print("not found (skipped):", f)
        for folder in folders:
            d = os.path.join(HERE, folder)
            for root, _, names in os.walk(d):
                for n in names:
                    p = os.path.join(root, n)
                    z.write(p, f"{PREFIX}/{os.path.relpath(p, HERE)}")
        count = len(z.namelist())
    size = os.path.getsize(zip_path) / 1e6
    print(f"{os.path.basename(zip_path)}: {count} files, {size:.1f} MB")
    return size


full = pack(os.path.join(HERE, "NahlaNabil_Task12.zip"), FILES, FOLDERS)
# Slim (for ~10 MB form limits): everything except the three heavy dashboards.
# They are on GitHub (see README links) and rebuildable from the scripts.
SLIM_SKIP = {"Airbnb_Dashboard.xlsx", "Airbnb_NYC_Dashboard.pbix", "Airbnb_NYC_Dashboard.html"}
slim = pack(os.path.join(HERE, "NahlaNabil_Task12_slim.zip"),
            [f for f in FILES if f not in SLIM_SKIP], FOLDERS)
print("note: slim zip links the dashboards on GitHub instead of bundling them")
