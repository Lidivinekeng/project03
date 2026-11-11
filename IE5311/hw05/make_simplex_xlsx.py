from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, Side

OUT = "p1_simplex_tableau.xlsx"
FONT = "Times New Roman"
COLS = "BCDEFGH"
LABELS = ["x1", "x2", "x3", "x4", "x5", "x6", "RHS"]

BODY = Font(name=FONT, size=11)
HEAD = Font(name=FONT, size=11, bold=True)
TITLE = Font(name=FONT, size=13, bold=True)
NOTE = Font(name=FONT, size=10, italic=True)
IN = Font(name=FONT, size=11, color="0000FF")
RULE = Border(bottom=Side(style="thin", color="000000"))
TOP = Border(top=Side(style="thin", color="000000"))
MID = Alignment(horizontal="center")

T0 = [["x4", 1, 0, 0, 1, 0, 0, 4],
      ["x5", 1, 1, 0, 0, 1, 0, 8],
      ["x6", 1, 1, 1, 0, 0, 1, 12],
      ["c-bar", 3, 2, 1, 0, 0, 0, 0]]

BLOCKS = [10, 18, 26, 34]
PIVOT = [("B", 0, "x1", "x4"), ("C", 1, "x2", "x5"), ("D", 2, "x3", "x6")]

wb = Workbook()
ws = wb.active
ws.title = "Simplex"

ws["A1"] = "IE 5311 Homework 5, Problem 1 Part 1"
ws["A1"].font = TITLE
ws["A2"] = ("Simplex by tableau. Every tableau below is computed from the "
            "one above by row operations.")
ws["A2"].font = NOTE
for r, t in enumerate([
        "max  3x1 + 2x2 + x3",
        "s.t. x1                <= 4",
        "     x1 + x2           <= 8",
        "     x1 + x2 + x3      <= 12",
        "     x1, x2, x3 >= 0        slacks x4, x5, x6"], start=4):
    ws.cell(row=r, column=1, value=t).font = BODY


def header(row, pivot_col):
    ws.cell(row=row, column=1, value="Basis").font = HEAD
    ws.cell(row=row, column=1).border = RULE
    for c, lab in zip(COLS, LABELS):
        cell = ws[f"{c}{row}"]
        cell.value = lab
        cell.font = HEAD
        cell.alignment = MID
        cell.border = RULE
    cell = ws[f"I{row}"]
    cell.value = "Ratio" if pivot_col else ""
    cell.font = HEAD
    cell.alignment = MID
    cell.border = RULE


for k, top in enumerate(BLOCKS):
    d0 = top + 2
    ws.cell(row=top, column=1, value=f"Tableau {k}").font = HEAD
    header(top + 1, PIVOT[k][0] if k < 3 else None)

    if k == 0:
        for i, row in enumerate(T0):
            r = d0 + i
            ws.cell(row=r, column=1, value=row[0]).font = HEAD
            for c, v in zip(COLS, row[1:]):
                cell = ws[f"{c}{r}"]
                cell.value = v
                cell.font = IN
                cell.number_format = "0.00"
    else:
        pc, pr, ent, _ = PIVOT[k - 1]
        src = BLOCKS[k - 1] + 2
        newp = d0 + pr
        basis = [PIVOT[j][2] for j in range(k)]
        names = ["x4", "x5", "x6"]
        for j in range(k):
            names[PIVOT[j][1]] = PIVOT[j][2]
        for i in range(4):
            r = d0 + i
            ws.cell(row=r, column=1,
                    value=(names[i] if i < 3 else "c-bar")).font = HEAD
            for c in COLS:
                cell = ws[f"{c}{r}"]
                if i == pr:
                    cell.value = f"={c}{src + pr}/${pc}${src + pr}"
                else:
                    cell.value = (f"={c}{src + i}-${pc}{src + i}"
                                  f"*{c}${newp}")
                cell.font = BODY
                cell.number_format = "0.00"

    if k < 3:
        pc = PIVOT[k][0]
        for i in range(3):
            r = d0 + i
            ws[f"I{r}"] = f'=IF({pc}{r}>0,$H{r}/{pc}{r},"")'
            ws[f"I{r}"].font = BODY
            ws[f"I{r}"].number_format = "0.00"

    cb = d0 + 3
    ws.cell(row=cb, column=10, value=f"=-H{cb}").font = HEAD
    ws.cell(row=cb, column=10).number_format = "0.00"
    ws.cell(row=cb, column=11, value="= objective z").font = NOTE
    for c in range(1, 9):
        ws.cell(row=cb, column=c).border = TOP

    note = ws.cell(row=d0 + 4, column=1)
    if k < 3:
        _, _, ent, leave = PIVOT[k]
        note.value = (f"entering {ent} (largest positive c-bar); "
                      f"ratio test gives leaving {leave}; "
                      f"pivot on the {ent} column, {leave} row")
    else:
        note.value = ("all c-bar entries are <= 0, so the optimality "
                      "condition holds and the method stops")
    note.font = NOTE

f = BLOCKS[3] + 2
s = BLOCKS[3] + 8
ws.cell(row=s, column=1, value="Optimal solution").font = HEAD
rows = [("x1", f"=H{f}"), ("x2", f"=H{f+1}"), ("x3", f"=H{f+2}"),
        ("z", f"=-H{f+3}"),
        ("y1", f"=-E{f+3}"), ("y2", f"=-F{f+3}"), ("y3", f"=-G{f+3}")]
for i, (lab, formula) in enumerate(rows, start=1):
    ws.cell(row=s + i, column=1, value=lab).font = BODY
    cell = ws.cell(row=s + i, column=2, value=formula)
    cell.font = BODY
    cell.number_format = "0.00"
ws.cell(row=s + 5, column=3,
        value="duals read off the slack columns x4, x5, x6").font = NOTE

c = s + 9
ws.cell(row=c, column=1, value="Feasibility check").font = HEAD
checks = [("x1 <= 4", f"=B{s+1}", 4),
          ("x1 + x2 <= 8", f"=B{s+1}+B{s+2}", 8),
          ("x1 + x2 + x3 <= 12", f"=B{s+1}+B{s+2}+B{s+3}", 12)]
for i, (lab, formula, rhs) in enumerate(checks, start=1):
    ws.cell(row=c + i, column=1, value=lab).font = BODY
    ws.cell(row=c + i, column=2, value=formula).font = BODY
    ws.cell(row=c + i, column=2).number_format = "0.00"
    ws.cell(row=c + i, column=3, value=rhs).font = BODY
    ws.cell(row=c + i, column=4,
            value=f'=IF(B{c+i}<={rhs}+0.000001,"ok","VIOLATED")').font = BODY

ws.column_dimensions["A"].width = 12
for col in "BCDEFGHIJ":
    ws.column_dimensions[col].width = 9
ws.column_dimensions["K"].width = 16
ws.sheet_view.showGridLines = False
wb.calculation.fullCalcOnLoad = True
wb.save(OUT)
print(f"wrote {OUT}")
