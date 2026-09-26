"""Step 4: export the Dashboard to PDF/PNG (unfiltered and with a slicer selection)
to check the layout and to test that slicers drive every KPI and chart."""
import os
import time
from PIL import ImageGrab
import pythoncom
import win32com.client as win32

HERE = os.path.dirname(os.path.abspath(__file__))
WB = os.path.join(HERE, "Healthcare_NoShows_Dashboard.xlsx")
AREA = "A1:CS88"
SHOTS = os.path.join(HERE, "screenshots")
os.makedirs(SHOTS, exist_ok=True)


def export(ws, name):
    """Copy the dashboard area as a bitmap (no default printer is needed, unlike PDF export)."""
    ws.Activate()
    xl.CalculateFull()
    time.sleep(1.5)
    for _ in range(5):
        try:
            ws.Range(AREA).CopyPicture(1, 2)  # xlScreen, xlBitmap
            time.sleep(0.8)
            img = ImageGrab.grabclipboard()
            if img is not None:
                img.save(os.path.join(SHOTS, name + ".png"))
                print("saved", name, img.size)
                return
        except Exception as e:
            print("retry", e)
        time.sleep(1)
    raise RuntimeError("clipboard capture failed")


pythoncom.CoInitialize()
xl = win32.DispatchEx("Excel.Application")
xl.Visible = True
xl.WindowState = -4137  # maximised
xl.DisplayAlerts = False
try:
    wb = xl.Workbooks.Open(WB, ReadOnly=True)
    dash = wb.Worksheets("Dashboard")
    export(dash, "1_dashboard_all_data")

    piv = wb.Worksheets("Pivot Tables")
    base = [piv.Cells(20 + i, 2).Value for i in range(6)]

    # filtered example: young patients (13-30) without SMS
    sc = wb.SlicerCaches("Slicer_Age_Group")
    for it in sc.SlicerItems:
        it.Selected = it.Name in ("02. Teen (13-18)", "03. Young Adult (19-30)")
    sms = wb.SlicerCaches("Slicer_SMS_Received")
    for it in sms.SlicerItems:
        it.Selected = it.Caption == "No SMS"
    xl.CalculateFull()
    filt = [piv.Cells(20 + i, 2).Value for i in range(6)]
    export(dash, "2_filtered_age13-30_no_sms")
    print("unfiltered:", base)
    print("filtered  :", filt)
    print(piv.Range("B30").Value)
    wb.Close(False)
finally:
    xl.Quit()
