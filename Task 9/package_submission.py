"""Step 8: build the submission zip (NahlaNabil.zip) and check it stays under the 10 MB upload limit.

Includes Customer_Dashboard.pbix when it exists (it is saved from Power BI Desktop, see Power_BI_Guide.md);
the PBIP project folder is always included, without Power BI's local cache files.
"""
import os
import zipfile

ZIP = "NahlaNabil.zip"
FILES = ["README.md", "KEY_INSIGHTS.md", "DATA_QUALITY_REPORT.md", "Power_BI_Guide.md", "Customer_Analysis_Summary.pdf",
         "Customer_Dashboard.html", "Customer_Dashboard.pbix", "Customers_Fakedata.csv", "Cleaned_Customers.csv",
         "cleaning_log.json", "analysis_summary.json", "analysis_output.txt",
         "clean_data.py", "analysis.py", "make_charts.py", "build_dashboard.py", "build_powerbi.py", "export_screenshots.py",
         "build_report.py", "package_submission.py"]
FOLDERS = ["charts", "screenshots", "PowerBI"]
SKIP = ("cache.abf", "localSettings.json")

with zipfile.ZipFile(ZIP, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
    for f in FILES:
        if os.path.exists(f):
            z.write(f, f"Task 9 - Nahla Nabil/{f}")
        else:
            print("not found (skipped):", f)
    for folder in FOLDERS:
        for root, _, names in os.walk(folder):
            if ".pbi" in root.replace("\\", "/").split("/"):      # Power BI's local cache / editor settings
                continue
            for n in names:
                if not n.endswith(SKIP):
                    p = os.path.join(root, n)
                    z.write(p, f"Task 9 - Nahla Nabil/{p}")
    count = len(z.namelist())

size = os.path.getsize(ZIP) / 1e6
print(f"{ZIP}: {count} files, {size:.1f} MB ({'OK' if size < 10 else 'TOO BIG'} for the 10 MB limit)")
