"""Generate the SVG graphics used by the repository README.

Run after finishing a task: add it to TASKS (and to TOOL_USE / SKILLS if needed), then
    python assets/make_assets.py
Outputs: assets/banner.svg, assets/stats.svg, assets/skills.svg, assets/headers/taskNN.svg
"""
from pathlib import Path

OUT = Path(__file__).parent
FONT = "Segoe UI, Helvetica, Arial, sans-serif"
TOTAL_TASKS = 12

# number, title, dataset line, colour, tools
TASKS = [
    (1, "Basic Sales Analysis", "Superstore · 9,994 orders", "#2E86AB", ["Python", "Excel", "PDF"]),
    (2, "Sales Performance Dashboard", "FactSale · 26,397 line items", "#1B998B", ["Python", "HTML", "PDF"]),
    (3, "HR Employee Attrition", "IBM HR · 1,470 employees", "#E0A030", ["Python", "HTML", "Power BI"]),
    (4, "Excel Skills", "7 practical exercises", "#217346", ["Excel"]),
    (5, "Titanic Survival", "418 passengers", "#C84C3C", ["Python", "Plotly"]),
    (6, "Weather & Climate Patterns", "3,271 daily records", "#3D5A80", ["Python", "Plotly", "Tableau"]),
    (7, "Hospital Analytics", "247 admissions · Arabic source", "#8E5572", ["Python", "Excel", "Tableau", "Power BI"]),
    (8, "Healthcare No-Shows", "106,987 appointments", "#E4572E", ["Excel", "Pivots", "Slicers", "Python"]),
]
DONE = len(TASKS)
ROWS_CLEANED = 9994 + 26397 + 1470 + 418 + 3271 + 247 + 106987
DASHBOARDS = 11  # T1 report, T2, T3 html + pbix, T5, T6 html + twbx, T7 html + twbx + pbix, T8 xlsb

TOOL_COLORS = {"Python": "#3776AB", "Excel": "#217346", "Power BI": "#C9A000", "Tableau": "#E97627",
               "Plotly / HTML": "#7B61FF", "PDF reports": "#B03A2E"}
TOOL_USE = {"Python": 7, "Excel": 4, "Plotly / HTML": 6, "Power BI": 2, "Tableau": 2, "PDF reports": 2}
SKILLS = [("Data visualization", 8), ("Data cleaning & validation", 7), ("KPI design", 7),
          ("Automation with Python scripts", 7), ("Interactive dashboards", 6),
          ("Data-quality detective work", 5), ("Excel formulas, pivots & slicers", 4),
          ("BI tools (Power BI / Tableau)", 3)]
SKILL_COLORS = ["#2E86AB", "#1B998B", "#E0A030", "#3D5A80", "#E4572E", "#8E5572", "#217346", "#E97627"]


def svg(w, h, body, label):
    body = body.replace(" & ", " &amp; ")
    label = label.replace("&", "&amp;")
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
            f'role="img" aria-label="{label}">\n{body}\n</svg>\n')


def banner():
    cells = []
    for i in range(TOTAL_TASKS):
        x = 56 + i * 50
        if i < DONE:
            cells.append(f'<rect x="{x}" y="228" width="44" height="18" rx="5" fill="url(#bar)"/>'
                         f'<text x="{x + 22}" y="241" fill="#0F2438" font-size="11" font-weight="700" '
                         f'text-anchor="middle">{i + 1}</text>')
        else:
            cells.append(f'<rect x="{x}" y="228" width="44" height="18" rx="5" fill="none" stroke="#5A7A96" '
                         f'stroke-width="1.5" stroke-dasharray="4 3"/><text x="{x + 22}" y="241" fill="#5A7A96" '
                         f'font-size="11" font-weight="700" text-anchor="middle">{i + 1}</text>')
    bars = [(820, 170, 90), (866, 140, 120), (912, 185, 75), (958, 110, 150), (1004, 130, 130), (1050, 80, 180), (1096, 60, 200)]
    line = [(837, 150), (883, 120), (929, 160), (975, 92), (1021, 108), (1067, 62), (1113, 40)]
    body = f'''<defs>
  <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#0F2438"/><stop offset="0.6" stop-color="#1F3B57"/><stop offset="1" stop-color="#155E63"/></linearGradient>
  <linearGradient id="bar" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#1B998B"/><stop offset="1" stop-color="#7FD1C7"/></linearGradient>
</defs>
<rect width="1200" height="300" rx="18" fill="url(#bg)"/>
<g opacity="0.16" fill="#9BC4E2">{"".join(f'<rect x="{x}" y="{y}" width="34" height="{h}" rx="4"/>' for x, y, h in bars)}</g>
<polyline points="{" ".join(f"{x},{y}" for x, y in line)}" fill="none" stroke="#E4572E" stroke-width="4" stroke-linecap="round" stroke-linejoin="round" opacity="0.85"/>
<g fill="#E4572E">{"".join(f'<circle cx="{x}" cy="{y}" r="5"/>' for x, y in line)}</g>
<g font-family="{FONT}">
  <text x="56" y="70" fill="#7FD1C7" font-size="16" font-weight="700" letter-spacing="4">VOLTIX · DATA ANALYST TRACK</text>
  <text x="56" y="122" fill="#FFFFFF" font-size="44" font-weight="800">Data Analyst Internship</text>
  <text x="56" y="160" fill="#D6E4F0" font-size="20">Nahla Nabil · raw data → clean data → KPIs → dashboards → insights</text>
  <text x="56" y="214" fill="#D6E4F0" font-size="14" font-weight="700" letter-spacing="2">PROGRESS · {DONE} / {TOTAL_TASKS} TASKS</text>
  {"".join(cells)}
</g>'''
    (OUT / "banner.svg").write_text(svg(1200, 300, body, f"Data Analyst Internship at VOLTIX - Nahla Nabil - {DONE} of {TOTAL_TASKS} tasks complete"), encoding="utf-8")


def stats():
    tiles = [(f"{DONE}/{TOTAL_TASKS}", "tasks completed", "#1F3B57"),
             (f"{ROWS_CLEANED / 1000:.0f}K+", "rows cleaned & validated", "#1B998B"),
             (f"{DASHBOARDS}", "dashboards & reports", "#E4572E"),
             ("4", "core tools mastered", "#E0A030")]
    w, gap = 285, 20
    parts = []
    for i, (big, small, col) in enumerate(tiles):
        x = i * (w + gap)
        parts.append(f'''<g transform="translate({x},0)">
  <rect width="{w}" height="110" rx="14" fill="{col}"/>
  <rect width="{w}" height="110" rx="14" fill="url(#shine)"/>
  <text x="24" y="58" fill="#FFFFFF" font-size="38" font-weight="800">{big}</text>
  <text x="24" y="88" fill="#FFFFFF" fill-opacity="0.9" font-size="14.5">{small}</text>
</g>''')
    body = f'''<defs><linearGradient id="shine" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#FFFFFF" stop-opacity="0.18"/><stop offset="1" stop-color="#000000" stop-opacity="0.12"/></linearGradient></defs>
<g font-family="{FONT}">{"".join(parts)}</g>'''
    (OUT / "stats.svg").write_text(svg(4 * w + 3 * gap, 110, body, "Internship statistics"), encoding="utf-8")


def skills():
    W, H = 1200, 400
    p = [f'<rect width="{W}" height="{H}" rx="16" fill="#F6F8FB" stroke="#E1E7EF"/>']
    # left: tools
    p.append(f'<text x="36" y="48" fill="#1F3B57" font-size="18" font-weight="800">TOOLS I USED</text>')
    p.append(f'<text x="36" y="70" fill="#5A6B7B" font-size="13">number of tasks (out of {DONE})</text>')
    for i, (tool, n) in enumerate(sorted(TOOL_USE.items(), key=lambda kv: -kv[1])):
        y = 98 + i * 46
        col = TOOL_COLORS[tool]
        p.append(f'<rect x="36" y="{y}" width="130" height="32" rx="16" fill="{col}"/>'
                 f'<text x="101" y="{y + 21}" fill="#fff" font-size="14" font-weight="700" text-anchor="middle">{tool}</text>')
        for k in range(DONE):
            cx = 190 + k * 42
            fill = col if k < n else "#E1E7EF"
            p.append(f'<rect x="{cx}" y="{y + 6}" width="34" height="20" rx="6" fill="{fill}"/>')
        p.append(f'<text x="{190 + DONE * 42 + 6}" y="{y + 21}" fill="#22313F" font-size="14" font-weight="700">{n}</text>')
    # right: skills
    X = 620
    p.append(f'<line x1="{X - 30}" y1="30" x2="{X - 30}" y2="{H - 30}" stroke="#E1E7EF" stroke-width="2"/>')
    p.append(f'<text x="{X}" y="48" fill="#1F3B57" font-size="18" font-weight="800">SKILLS PRACTISED</text>')
    p.append(f'<text x="{X}" y="70" fill="#5A6B7B" font-size="13">tasks where the skill was used</text>')
    bw = 430
    for i, ((name, n), col) in enumerate(zip(SKILLS, SKILL_COLORS)):
        y = 96 + i * 36
        p.append(f'<text x="{X}" y="{y + 12}" fill="#22313F" font-size="15" font-weight="600">{name}</text>')
        p.append(f'<rect x="{X}" y="{y + 18}" width="{bw}" height="9" rx="4.5" fill="#E1E7EF"/>'
                 f'<rect x="{X}" y="{y + 18}" width="{bw * n / DONE:.0f}" height="9" rx="4.5" fill="{col}"/>')
        p.append(f'<text x="{X + bw + 14}" y="{y + 27}" fill="{col}" font-size="13" font-weight="800">{n}/{DONE}</text>')
    body = f'<g font-family="{FONT}">' + "\n".join(p) + "</g>"
    (OUT / "skills.svg").write_text(svg(W, H, body, "Tools and skills used across the tasks"), encoding="utf-8")


def headers():
    d = OUT / "headers"
    d.mkdir(exist_ok=True)
    for n, title, sub, col, tools in TASKS:
        chips, x = [], 1164
        for t in reversed(tools):
            w = 18 + 8.2 * len(t)
            x -= w
            chips.append(f'<rect x="{x:.0f}" y="34" width="{w:.0f}" height="30" rx="15" fill="#FFFFFF" fill-opacity="0.28"/>'
                         f'<text x="{x + w / 2:.0f}" y="54" fill="#FFFFFF" font-size="13" font-weight="700" text-anchor="middle">{t}</text>')
            x -= 8
        body = f'''<defs><linearGradient id="g{n}" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{col}"/><stop offset="1" stop-color="{col}" stop-opacity="0.72"/></linearGradient></defs>
<rect width="1200" height="98" rx="16" fill="url(#g{n})"/>
<g font-family="{FONT}">
  <text x="30" y="70" fill="#FFFFFF" fill-opacity="0.35" font-size="58" font-weight="900">{n:02d}</text>
  <text x="122" y="46" fill="#FFFFFF" font-size="26" font-weight="800">{title}</text>
  <text x="122" y="74" fill="#FFFFFF" fill-opacity="0.88" font-size="15">TASK {n} · {sub}</text>
  {"".join(chips)}
</g>'''
        (d / f"task{n:02d}.svg").write_text(svg(1200, 98, body, f"Task {n}: {title}"), encoding="utf-8")


def chips():
    d = OUT / "chips"
    d.mkdir(exist_ok=True)
    colors = {n: col for n, _, _, col, _ in TASKS}
    for n in range(1, TOTAL_TASKS + 1):
        col = colors.get(n, "#D0D7DE")
        fg = "#FFFFFF" if n in colors else "#5A6B7B"
        body = (f'<rect width="56" height="32" rx="9" fill="{col}"/>'
                f'<text x="28" y="22" fill="{fg}" font-family="{FONT}" font-size="16" font-weight="800" '
                f'text-anchor="middle">{n:02d}</text>')
        (d / f"{n:02d}.svg").write_text(svg(56, 32, body, f"Task {n}"), encoding="utf-8")


if __name__ == "__main__":
    chips()
    banner()
    stats()
    skills()
    headers()
    print("assets written for", DONE, "tasks")
