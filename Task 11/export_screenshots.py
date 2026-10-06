"""Step 6: export the Dashboard to PNG (unfiltered and with a slicer selection)
to check the layout and to prove that the slicers drive every KPI and chart."""
import os
import time

import pythoncom
import win32com.client as win32
from PIL import ImageGrab

HERE = os.path.dirname(os.path.abspath(__file__))
WB = os.path.join(HERE, "GameSales_Dashboard.xlsx")
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
xl.WindowState = -4137
xl.DisplayAlerts = False
try:
    wb = xl.Workbooks.Open(WB, ReadOnly=True)
    dash = wb.Worksheets("Dashboard")
    export(dash, "1_dashboard_all_data")

    piv = wb.Worksheets("Pivot Tables")
    base = [piv.Cells(62 + i, 2).Value for i in range(7)]

    # filtered example: Nintendo platform family, shooter genre, 2010s
    fam = wb.SlicerCaches("Slicer_Platform_Family")
    for it in fam.SlicerItems:
        it.Selected = it.Caption == "Nintendo"
    gen = wb.SlicerCaches("Slicer_Genre")
    for it in gen.SlicerItems:
        it.Selected = it.Caption in ("Shooter", "Action")
    dec = wb.SlicerCaches("Slicer_Decade")
    for it in dec.SlicerItems:
        it.Selected = it.Caption == "2010s"
    xl.CalculateFull()
    filt = [piv.Cells(62 + i, 2).Value for i in range(7)]
    export(dash, "2_filtered_nintendo_action_shooter_2010s")
    print("unfiltered:", base)
    print("filtered  :", filt)
    print("header:", piv.Range("B78").Value)
    wb.Close(False)
finally:
    xl.Quit()
