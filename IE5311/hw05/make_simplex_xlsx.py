from openpyxl import Workbook

COLS = "BCDEFGH"
HEAD = ["x1", "x2", "x3", "x4", "x5", "x6", "RHS"]
T0 = [["x4", 1, 0, 0, 1, 0, 0, 4],
      ["x5", 1, 1, 0, 0, 1, 0, 8],
      ["x6", 1, 1, 1, 0, 0, 1, 12],
      ["z", 3, 2, 1, 0, 0, 0, 0]]
PIV = [("B", 0, "x1"), ("C", 1, "x2"), ("D", 2, "x3")]

wb = Workbook()
ws = wb.active
basis = ["x4", "x5", "x6"]
prev = 0

for k in range(4):
    h = 1 + 6 * k
    d = h + 1
    ws.cell(h, 1, "Basis")
    for c, lab in zip(COLS, HEAD):
        ws[f"{c}{h}"] = lab
    if k < 3:
        ws[f"I{h}"] = "Ratio"

    if k == 0:
        for i, row in enumerate(T0):
            ws.cell(d + i, 1, row[0])
            for c, v in zip(COLS, row[1:]):
                ws[f"{c}{d + i}"] = v
    else:
        pc, pr, ent = PIV[k - 1]
        basis[pr] = ent
        for i in range(4):
            ws.cell(d + i, 1, basis[i] if i < 3 else "z")
            for c in COLS:
                if i == pr:
                    ws[f"{c}{d + i}"] = f"={c}{prev + pr}/${pc}${prev + pr}"
                else:
                    ws[f"{c}{d + i}"] = (f"={c}{prev + i}-${pc}{prev + i}"
                                         f"*{c}${d + pr}")

    if k < 3:
        pc = PIV[k][0]
        for i in range(3):
            ws[f"I{d + i}"] = f'=IF({pc}{d+i}>0,$H{d+i}/{pc}{d+i},"")'

    for i in range(4):
        for c in COLS + "I":
            ws[f"{c}{d + i}"].number_format = "0.00"
    prev = d

ws.column_dimensions["A"].width = 8
for c in COLS + "I":
    ws.column_dimensions[c].width = 8
wb.calculation.fullCalcOnLoad = True
wb.save("p1_simplex_tableau.xlsx")
