import numpy as np
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
from openpyxl.chart import ScatterChart, Reference, Series
from openpyxl.chart.axis import ChartLines
from openpyxl.utils import get_column_letter
from openpyxl.comments import Comment

import p1_relief as m

ALPHA = m.ALPHA
NDRAW = 5000
SEED = 5311

rng = np.random.default_rng(SEED)
draws = rng.choice(len(m.S), size=NDRAW, p=m.p)
counts = [int(np.sum(draws == s)) for s in m.S]

MODELS = (("risk-neutral", False, False),
          ("chance-constrained", True, False),
          ("chance + CVaR", True, True))

cost = {}
obj = {}
for tag, ch, cv in MODELS:
    r = m.build(chance=ch, cvar=cv, name=tag)
    per = [m.recourse(r["x"], s) for s in m.S]
    cost[tag] = [sum(m.c[i] * r["x"][i] for i in m.I) + per[s][0] for s in m.S]
    obj[tag] = r["obj"]

ARIAL = "Arial"
H1 = Font(name=ARIAL, size=13, bold=True)
H2 = Font(name=ARIAL, size=11, bold=True)
TXT = Font(name=ARIAL, size=10)
NOTE = Font(name=ARIAL, size=9, italic=True)
INPUT = Font(name=ARIAL, size=10, color="0000FF")
LINKED = Font(name=ARIAL, size=10, color="008000")
thin = Side(style="thin", color="000000")
TOP = Border(top=thin)
BOT = Border(bottom=thin)
CENTER = Alignment(horizontal="center")

wb = Workbook()

# ----------------------------------------------------------------- Data sheet
ws = wb.active
ws.title = "Data"

ws["A1"] = "IE 5311 Homework 3, Problem 1 Part 7"
ws["A1"].font = H1
ws["A2"] = ("Total cost by scenario under each first-stage plan, and the "
            "5,000-draw sample used to evaluate them")
ws["A2"].font = TXT

ws["A4"] = "Inputs"
ws["A4"].font = H2
ws["A5"] = ("Blue cells are inputs. Scenario probabilities are given in the "
            "assignment; costs and draw counts are produced by "
            "p1_relief.py (Gurobi, seed 5311). Black cells are formulas.")
ws["A5"].font = NOTE

hdr = ["Scenario", "Probability p_s", "Draw count", "Sample frequency",
       "Risk neutral", "Chance constrained", "Chance + CVaR"]
hdr += ["p_s x cost, risk neutral", "p_s x cost, chance",
        "p_s x cost, chance + CVaR"]
for c, h in enumerate(hdr, 1):
    cell = ws.cell(row=7, column=c, value=h)
    cell.font = H2
    cell.alignment = Alignment(horizontal="center", wrap_text=True)
    cell.border = BOT
ws.row_dimensions[7].height = 30

R0 = 7
RT = R0 + len(m.S) + 1
for s in m.S:
    r = R0 + 1 + s
    ws.cell(row=r, column=1, value=s + 1).font = TXT
    ws.cell(row=r, column=1).alignment = CENTER
    ws.cell(row=r, column=2, value=m.p[s]).font = INPUT
    ws.cell(row=r, column=3, value=counts[s]).font = INPUT
    ws.cell(row=r, column=4, value=f"=C{r}/$C${RT}").font = TXT
    for k, (tag, _, _) in enumerate(MODELS):
        ws.cell(row=r, column=5 + k, value=cost[tag][s]).font = INPUT
        pc = ws.cell(row=r, column=8 + k,
                     value=f"=$B{r}*{get_column_letter(5+k)}{r}")
        pc.font = TXT
        pc.number_format = "#,##0.0000"
    ws.cell(row=r, column=2).number_format = "0.00"
    ws.cell(row=r, column=3).number_format = "#,##0"
    ws.cell(row=r, column=4).number_format = "0.000"
    for c in (5, 6, 7):
        ws.cell(row=r, column=c).number_format = "#,##0.00"

ws.cell(row=RT, column=1, value="Total").font = H2
ws.cell(row=RT, column=2, value=f"=SUM(B{R0+1}:B{RT-1})").font = TXT
ws.cell(row=RT, column=3, value=f"=SUM(C{R0+1}:C{RT-1})").font = TXT
ws.cell(row=RT, column=4, value=f"=SUM(D{R0+1}:D{RT-1})").font = TXT
ws.cell(row=RT, column=2).number_format = "0.00"
ws.cell(row=RT, column=3).number_format = "#,##0"
ws.cell(row=RT, column=4).number_format = "0.000"
for c in range(1, 8):
    ws.cell(row=RT, column=c).border = TOP
ws.cell(row=RT, column=3).comment = Comment(
    "Draws total 5,000 by construction; the sample frequency column "
    "divides by this cell, so both totals must read 5,000 and 1.000.",
    "IE 5311")

# ------------------------------------------------------------- summary block
SR = RT + 2
ws.cell(row=SR, column=1, value="Summary statistics").font = H2
ws.cell(row=SR + 1, column=1, value=(
    "Every figure below is a formula over the table above. Expectation, "
    "standard deviation, the 90% quantile and the maximum use the sample; "
    "CVaR uses the true probabilities p_s, matching p1_relief.py.")).font = NOTE

srows = [
    ("Model objective (from Gurobi)", None),
    ("Expectation under free recourse", "exact"),
    ("Recourse relaxation", "relax"),
    ("Sample mean", "mean"),
    ("Sampling noise", "noise"),
    ("Sample standard deviation", "sd"),
    ("Sample 90% quantile", "p90"),
    ("CVaR 0.90 of total cost", "cvar"),
    ("Sample maximum", "max"),
]
HB = SR + 3
ws.cell(row=HB, column=1, value="Statistic").font = H2
ws.cell(row=HB, column=1).border = BOT
for k, (tag, _, _) in enumerate(MODELS):
    cell = ws.cell(row=HB, column=2 + k, value=tag)
    cell.font = H2
    cell.alignment = Alignment(horizontal="center", wrap_text=True)
    cell.border = BOT
ws.row_dimensions[HB].height = 30

lo, hi = R0 + 1, RT - 1
for i, (label, key) in enumerate(srows):
    r = HB + 1 + i
    ws.cell(row=r, column=1, value=label).font = TXT
    for k, (tag, _, _) in enumerate(MODELS):
        col = get_column_letter(5 + k)
        cc = ws.cell(row=r, column=2 + k)
        cc.number_format = "#,##0.0000"
        if key is None:
            cc.value = obj[tag]
            cc.font = INPUT
        elif key == "exact":
            cc.value = f"=SUMPRODUCT($B${lo}:$B${hi},{col}{lo}:{col}{hi})"
            cc.font = TXT
        elif key == "relax":
            cc.value = f"={get_column_letter(2+k)}{HB+1}" \
                       f"-{get_column_letter(2+k)}{HB+2}"
            cc.font = TXT
        elif key == "mean":
            cc.value = (f"=SUMPRODUCT($C${lo}:$C${hi},{col}{lo}:{col}{hi})"
                        f"/$C${RT}")
            cc.font = TXT
        elif key == "noise":
            cc.value = f"={get_column_letter(2+k)}{HB+2}" \
                       f"-{get_column_letter(2+k)}{HB+4}"
            cc.font = TXT
        elif key == "sd":
            cc.value = (f"=SQRT(SUMPRODUCT($C${lo}:$C${hi},"
                        f"({col}{lo}:{col}{hi}"
                        f"-{get_column_letter(2+k)}{HB+4})^2)/$C${RT})")
            cc.font = TXT
        elif key == "p90":
            cl = get_column_letter(3 + 6 * k)
            cc.value = (f"=INDEX(CDF!${cl}$4:${cl}$13,"
                        f"MATCH(0.9,CDF!${get_column_letter(5+6*k)}$4:"
                        f"${get_column_letter(5+6*k)}$13,1)+1)")
            cc.font = LINKED
        elif key == "cvar":
            cl = get_column_letter(3 + 4 * k)
            cc.value = f"=MIN(CVaR!{cl}4:{cl}13)"
            cc.font = LINKED
        elif key == "max":
            cc.value = f"=MAX({col}{lo}:{col}{hi})"
            cc.font = TXT

ws.cell(row=HB + 1, column=1).comment = Comment(
    "Optimal objective reported by Gurobi for each model. For the "
    "risk-neutral model this equals the exact expectation, because that "
    "model already minimises expected cost with free recourse. The two "
    "constrained models sit above it: their own recourse must satisfy the "
    "service rows and the CVaR cap, which the evaluation drops.", "IE 5311")

for col, w in (("A", 34), ("B", 17), ("C", 17), ("D", 17),
               ("E", 15), ("F", 15), ("G", 15),
               ("H", 17), ("I", 17), ("J", 17)):
    ws.column_dimensions[col].width = w

ws.cell(row=7, column=8).comment = Comment(
    "Columns H to J hold p_s times the scenario cost. The CVaR sheet needs "
    "the conditional sum of p_s*cost over the scenarios above a candidate "
    "eta, and SUMIF cannot multiply two ranges, so the product is formed "
    "here first. This keeps the CVaR formulas to SUMIF, which every version "
    "of Excel evaluates the same way.", "IE 5311")

# ------------------------------------------------------------------ CDF sheet
cs = wb.create_sheet("CDF")
cs["A1"] = "Empirical CDF of total cost, one block per first-stage plan"
cs["A1"].font = H1
cs["A2"] = ("Scenarios sorted by cost within each block, so the cumulative "
            "column is the empirical CDF evaluated at each of the ten atoms. "
            "Cost and frequency are pulled from the Data sheet by INDEX/MATCH.")
cs["A2"].font = NOTE

order = {}
for k, (tag, _, _) in enumerate(MODELS):
    order[tag] = sorted(m.S, key=lambda s: cost[tag][s])
    off = 6 * k
    dcol = get_column_letter(5 + k)
    for c, h in enumerate(("Rank", "Scenario", "Total cost",
                           "Sample freq.", "Cumulative"), 1):
        cell = cs.cell(row=3, column=off + c, value=h)
        cell.font = H2
        cell.alignment = Alignment(horizontal="center", wrap_text=True)
        cell.border = BOT
    cs.cell(row=2, column=off + 1)
    t = cs.cell(row=2, column=off + 3, value=tag)
    for i, s in enumerate(order[tag], 1):
        r = 3 + i
        cs.cell(row=r, column=off + 1, value=i).font = TXT
        cs.cell(row=r, column=off + 1).alignment = CENTER
        cs.cell(row=r, column=off + 2, value=s + 1).font = INPUT
        cs.cell(row=r, column=off + 2).alignment = CENTER
        sc = get_column_letter(off + 2)
        cs.cell(row=r, column=off + 3, value=(
            f"=INDEX(Data!${dcol}${lo}:${dcol}${hi},"
            f"MATCH(${sc}{r},Data!$A${lo}:$A${hi},0))")).font = LINKED
        cs.cell(row=r, column=off + 4, value=(
            f"=INDEX(Data!$D${lo}:$D${hi},"
            f"MATCH(${sc}{r},Data!$A${lo}:$A${hi},0))")).font = LINKED
        fc = get_column_letter(off + 4)
        cum = get_column_letter(off + 5)
        cs.cell(row=r, column=off + 5, value=(
            f"={fc}{r}" if i == 1 else f"={cum}{r-1}+{fc}{r}")).font = TXT
        cs.cell(row=r, column=off + 3).number_format = "#,##0.00"
        cs.cell(row=r, column=off + 4).number_format = "0.0000"
        cs.cell(row=r, column=off + 5).number_format = "0.0000"
    t.font = H2
    t.alignment = CENTER
    for c in range(1, 6):
        cs.cell(row=14, column=off + c).border = TOP
    cs.cell(row=14, column=off + 1, value="Total").font = H2
    cs.cell(row=14, column=off + 4,
            value=f"=SUM({fc}4:{fc}13)").font = TXT
    cs.cell(row=14, column=off + 4).number_format = "0.0000"
    for c, w in ((1, 7), (2, 10), (3, 13), (4, 13), (5, 13), (6, 3)):
        cs.column_dimensions[get_column_letter(off + c)].width = w

cs.cell(row=16, column=1, value=(
    "The Data sheet's 90% quantile formula reads the first cost in each "
    "block whose cumulative frequency exceeds 0.90. That is the standard "
    "definition and here it also matches linear interpolation over the "
    "5,000 sorted draws, because 0.90 falls strictly inside an atom.")
).font = NOTE

# ----------------------------------------------------------------- CVaR sheet
vs = wb.create_sheet("CVaR")
vs["A1"] = "CVaR 0.90 of total cost, by minimising the Rockafellar-Uryasev form"
vs["A1"].font = H1
vs["A2"] = ("CVaR(L) = min over eta of eta + E[(L-eta)+]/(1-alpha). The "
            "minimum over eta is attained at one of the atoms, so each block "
            "evaluates the bracket at all ten and the Data sheet takes the "
            "MIN. True probabilities p_s are used here, not sample "
            "frequencies, matching p1_relief.py.")
vs["A2"].font = NOTE
# alpha lives below the blocks: row 3 is the blocks' header row, so a
# parameter there would be overwritten by the first block's headers.
vs["A15"] = "alpha"
vs["A15"].font = H2
vs["B15"] = ALPHA
vs["B15"].font = INPUT
vs["B15"].number_format = "0.00"
vs["C15"] = "CVaR confidence level, referenced by every bracket formula above"
vs["C15"].font = NOTE

for k, (tag, _, _) in enumerate(MODELS):
    off = 4 * k
    dcol = get_column_letter(5 + k)
    vs.cell(row=2, column=off + 2, value=tag).font = H2
    for c, h in enumerate(("Candidate eta", "E[(L-eta)+]",
                           "eta + E/(1-alpha)"), 1):
        cell = vs.cell(row=3, column=off + c, value=h)
        cell.font = H2
        cell.alignment = Alignment(horizontal="center", wrap_text=True)
        cell.border = BOT
    ec = get_column_letter(off + 1)
    xc = get_column_letter(off + 2)
    for i, s in enumerate(order[tag], 1):
        r = 3 + i
        vs.cell(row=r, column=off + 1, value=(
            f"=CDF!{get_column_letter(6*k+3)}{r}")).font = LINKED
        pcol = get_column_letter(8 + k)
        vs.cell(row=r, column=off + 2, value=(
            f'=SUMIF(Data!${dcol}${lo}:${dcol}${hi},">"&{ec}{r},'
            f"Data!${pcol}${lo}:${pcol}${hi})"
            f'-{ec}{r}*SUMIF(Data!${dcol}${lo}:${dcol}${hi},">"&{ec}{r},'
            f"Data!$B${lo}:$B${hi})")).font = TXT
        vs.cell(row=r, column=off + 3, value=(
            f"={ec}{r}+{xc}{r}/(1-$B$15)")).font = TXT
        for c in (1, 2, 3):
            vs.cell(row=r, column=off + c).number_format = "#,##0.0000"
    for c, w in ((1, 15), (2, 15), (3, 18), (4, 3)):
        vs.column_dimensions[get_column_letter(off + c)].width = w

# ------------------------------------------------------------ ChartData sheet
ds = wb.create_sheet("ChartData")
ds["A1"] = "Step-expanded series for the chart"
ds["A1"].font = H1
ds["A2"] = ("A CDF over ten atoms is a staircase, so each atom contributes "
            "two points: one at the cumulative level it rises from, one at "
            "the level it rises to. Both read the CDF sheet; nothing here is "
            "typed in.")
ds["A2"].font = NOTE

NSTEP = 2 * len(m.S)
for k, (tag, _, _) in enumerate(MODELS):
    off = 3 * k
    ccol = get_column_letter(6 * k + 3)
    ucol = get_column_letter(6 * k + 5)
    ds.cell(row=2, column=off + 1, value=tag).font = H2
    for c, h in enumerate(("Total cost", "Cumulative"), 1):
        cell = ds.cell(row=3, column=off + c, value=h)
        cell.font = H2
        cell.alignment = Alignment(horizontal="center", wrap_text=True)
        cell.border = BOT
    for i in range(1, len(m.S) + 1):
        ra, rb = 2 + 2 * i, 3 + 2 * i
        src = 3 + i
        ds.cell(row=ra, column=off + 1,
                value=f"=CDF!${ccol}${src}").font = LINKED
        ds.cell(row=rb, column=off + 1,
                value=f"=CDF!${ccol}${src}").font = LINKED
        ds.cell(row=ra, column=off + 2,
                value=0 if i == 1 else f"=CDF!${ucol}${src-1}").font = LINKED
        ds.cell(row=rb, column=off + 2,
                value=f"=CDF!${ucol}${src}").font = LINKED
        for r in (ra, rb):
            ds.cell(row=r, column=off + 1).number_format = "#,##0.00"
            ds.cell(row=r, column=off + 2).number_format = "0.0000"
    for c, w in ((1, 13), (2, 13), (3, 3)):
        ds.column_dimensions[get_column_letter(off + c)].width = w

# ----------------------------------------------------------------- the figure
chart = ScatterChart()
chart.scatterStyle = "line"
chart.title = "Distribution of total cost over 5,000 draws"
chart.x_axis.title = "Total cost (first stage plus realised recourse), $"
chart.y_axis.title = "Empirical cumulative probability"
chart.height = 11.5
chart.width = 19.5
chart.x_axis.delete = False
chart.y_axis.delete = False
chart.x_axis.scaling.min = 4500
chart.x_axis.scaling.max = 12500
chart.y_axis.scaling.min = 0
chart.y_axis.scaling.max = 1
chart.x_axis.numFmt = "#,##0"
chart.y_axis.numFmt = "0.0"
chart.y_axis.majorGridlines = ChartLines()
chart.legend.position = "b"

DASH = ("solid", "dash", "sysDot")
for k, (tag, _, _) in enumerate(MODELS):
    off = 3 * k
    xref = Reference(ds, min_col=off + 1, min_row=4, max_row=3 + NSTEP)
    yref = Reference(ds, min_col=off + 2, min_row=4, max_row=3 + NSTEP)
    ser = Series(yref, xref, title=tag)
    ser.marker.symbol = "none"
    ser.smooth = False
    ser.graphicalProperties.line.solidFill = "000000"
    ser.graphicalProperties.line.width = 19050
    ser.graphicalProperties.line.dashStyle = DASH[k]
    chart.series.append(ser)

fig = wb.create_chartsheet("Figure")
fig.add_chart(chart)
wb.move_sheet("Figure", offset=-4)

for sheet in wb.worksheets:
    sheet.sheet_view.showGridLines = False

# Excel recomputes every formula when the file opens, so the workbook is
# correct even though it carries no cached values of its own.
wb.calculation.fullCalcOnLoad = True

OUT = "p1_cost_distributions.xlsx"
wb.save(OUT)
print(f"wrote {OUT}")
print(f"sheets: {wb.sheetnames}")
