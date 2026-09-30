# Power BI verification tools

These are development helpers, not part of the submission. They load a generated PBIP in Power BI Desktop, refresh it, capture each page and query the model, all without using the mouse or keyboard.

| Script | What it does |
|---|---|
| `win.ps1` | Win32 helpers (dot-sourced by the others): list window titles per process, resize without focusing, `PrintWindow` capture. DPI-aware, so captures are not cropped at 125% scaling |
| `open_refresh.ps1 -Pbip <path>` | Starts Power BI Desktop with the project, polls window titles every second (load-error dialogs close themselves within seconds), then presses **Refresh now** through UI Automation |
| `capture_pages.ps1 -Title <window> -Pages <tab names>` | Selects each page tab through UI Automation and saves a window capture |
| `dax_check.ps1 -Query <DAX>` | Finds the port of the local `msmdsrv` process and runs DAX queries through the ADOMD client that ships with Power BI Desktop |

At 1920×1080 the report canvas sits at about x 60–1226 and y 252–898 of the capture (the side panes stay open). Task 9 cropped the page screenshots to that box.
