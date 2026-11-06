"""Build the Problem 1 walkthrough as a PDF.

Companion to how_to_do_the_homework.pdf: the same seven-step method, applied
end to end to Maya's investment problem. Black text only, no colour, no icons.
All mathematics is written in ASCII so the file needs no embedded font.
"""

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (BaseDocTemplate, Frame, KeepTogether,
                                PageTemplate, Paragraph, Spacer, Table,
                                TableStyle)

OUT = "/home/user/project03/IE5311/problem1_walkthrough.pdf"

PAGE_W, PAGE_H = letter
LM = RM = 0.9 * inch
TM = 0.85 * inch
BM = 0.85 * inch
BLACK = colors.black
AVAIL = PAGE_W - LM - RM

ss = getSampleStyleSheet()

title = ParagraphStyle("title", parent=ss["Normal"], fontName="Times-Bold",
                       fontSize=19, leading=23, spaceAfter=4, textColor=BLACK)
subtitle = ParagraphStyle("subtitle", parent=ss["Normal"],
                          fontName="Times-Roman", fontSize=10.5, leading=14,
                          spaceAfter=2, textColor=BLACK)
h1 = ParagraphStyle("h1", parent=ss["Normal"], fontName="Times-Bold",
                    fontSize=13.5, leading=17, spaceBefore=16, spaceAfter=6,
                    textColor=BLACK, keepWithNext=1)
h2 = ParagraphStyle("h2", parent=ss["Normal"], fontName="Times-Bold",
                    fontSize=11, leading=14, spaceBefore=10, spaceAfter=4,
                    textColor=BLACK, keepWithNext=1)
body = ParagraphStyle("body", parent=ss["Normal"], fontName="Times-Roman",
                      fontSize=10, leading=13.6, spaceAfter=6,
                      alignment=TA_LEFT, textColor=BLACK)
bullet = ParagraphStyle("bullet", parent=body, leftIndent=16, bulletIndent=5,
                        spaceAfter=3)
mono = ParagraphStyle("mono", parent=ss["Normal"], fontName="Courier",
                      fontSize=8.8, leading=12, leftIndent=16, spaceBefore=3,
                      spaceAfter=7, textColor=BLACK)
cell = ParagraphStyle("cell", parent=ss["Normal"], fontName="Times-Roman",
                      fontSize=9, leading=11.5, textColor=BLACK)
cellb = ParagraphStyle("cellb", parent=cell, fontName="Times-Bold")
quote = ParagraphStyle("quote", parent=body, fontName="Times-Italic",
                       leftIndent=18, rightIndent=12, spaceBefore=4,
                       spaceAfter=8)


def P(text, style=body):
    return Paragraph(text, style)


def B(text):
    return Paragraph(text, bullet, bulletText="–")


def N(text, n):
    return Paragraph(text, bullet, bulletText=f"{n}.")


def grid(rows, widths, header=True):
    data = []
    for r_i, row in enumerate(rows):
        style = cellb if (header and r_i == 0) else cell
        data.append([Paragraph(c, style) for c in row])
    t = Table(data, colWidths=widths, hAlign="LEFT",
              repeatRows=1 if header else 0)
    t.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.4, BLACK),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return t


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Times-Roman", 8.5)
    canvas.setFillColor(BLACK)
    canvas.drawString(LM, BM - 24,
                      "IE 5311-001, Homework 1, Problem 1 [20 pts]")
    canvas.drawRightString(PAGE_W - RM, BM - 24, "Page %d" % doc.page)
    canvas.setLineWidth(0.4)
    canvas.setStrokeColor(BLACK)
    canvas.line(LM, BM - 16, PAGE_W - RM, BM - 16)
    canvas.restoreState()


story = []

story.append(P("Problem 1, Start to Finish", title))
story.append(P("Maya's investment plan, worked through the seven-step method. "
               "IE 5311-001 (D01) Principles of Optimization, Fall 2026.",
               subtitle))
story.append(Spacer(1, 3))
story.append(Table([[""]], colWidths=[AVAIL], rowHeights=[1],
                   style=TableStyle([("LINEABOVE", (0, 0), (-1, 0), 1.0,
                                      BLACK)])))
story.append(Spacer(1, 10))
story.append(P(
    "Companion to the method sheet. Every step below is one of the seven "
    "moves, applied to a real problem, with the reasoning left in rather than "
    "cleaned away.", body))

# ------------------------------------------------------------------ the story
story.append(P("The story, in plain words", h1))
story.append(P(
    "Maya has $5,000 and five years. At the start of each year she may place "
    "money into a deposit that locks for 1, 2 or 3 years. When a deposit "
    "matures the money comes back and she may reinvest it. She wants the most "
    "cash possible at the end of Year 5.", body))
story.append(Spacer(1, 3))
story.append(grid([
    ["Instrument", "Term", "Total return over the term", "Available from"],
    ["Frontier 1-year", "1 yr", "1.04", "start of Year 1"],
    ["Frontier 2-year", "2 yr", "1.09", "start of Year 1"],
    ["Pioneer 3-year", "3 yr", "1.15", "<b>start of Year 2</b>"],
], [1.5 * inch, 0.6 * inch, 2.1 * inch, 1.5 * inch]))
story.append(Spacer(1, 6))
story.append(P(
    "That last cell is the whole problem hiding in plain sight. Hold the "
    "thought.", body))

# ------------------------------------------------------------------ step 0
story.append(P("Step 0. Fix the time convention first", h1))
story.append(P(
    "This step is not in the generic checklist, because it only appears in "
    "problems that move through time. When it does appear, do it before "
    "anything else, because every later decision depends on it.", body))
story.append(P(
    "The question: does &quot;period 3&quot; mean the <i>start</i> of Year 3 "
    "or the <i>end</i> of Year 3?", body))
story.append(P(
    "We chose: <b>epoch t is the beginning of Year t</b>. So t runs 1 to 5, "
    "and we add t = 6 to mean the end of Year 5, which is the moment the "
    "answer is measured. Everything then follows mechanically:", body))
story.append(P(
    "An instrument of term L started at epoch t matures at epoch t + L, and is "
    "admissible only if t + L &lt;= 6.", quote))
story.append(P(
    "That one line does all the filtering. A 3-year deposit started at epoch 4 "
    "would mature at epoch 7, and there is no epoch 7, so Maya's money would "
    "still be locked when the horizon arrives. Not admissible. You never have "
    "to reason about it case by case; the inequality handles it.", body))
story.append(P(
    "<b>Get this convention wrong and every number after it is wrong</b>, with "
    "nothing in the solver to warn you. Write it down explicitly in your "
    "answer. Two sentences is enough.", body))

# ------------------------------------------------------------------ step 1
story.append(P("Step 1. Find the decision", h1))
story.append(P(
    "Apply the test: if I handed you these numbers, could you walk into the "
    "bank and do it?", body))
story.append(B('"Put $5,000 into the two-year deposit at the start of Year 1" '
               '&mdash; yes &mdash; <b>decision</b>'))
story.append(B('"The two-year deposit returns 9%" &mdash; you cannot negotiate '
               'it &mdash; <b>parameter</b>'))
story.append(B('"End Year 5 with $6,267.50" &mdash; that is the consequence '
               '&mdash; <b>result, not a variable</b>'))
story.append(Spacer(1, 4))
story.append(P(
    "So the decision is: how many dollars go into which instrument, at which "
    "epoch.", body))

story.append(P("The second decision most people miss", h2))
story.append(P(
    "What if Maya simply holds cash, and does nothing with some of it for a "
    "year? You could argue she never would, because every instrument pays a "
    "positive return. The argument is correct. Do not bake it into the model "
    "anyway. Put in a variable for it:", body))
story.append(P("w_t = dollars held idle from epoch t to epoch t+1", mono))
story.append(P(
    "Then when the solver returns w_t = 0 at every epoch, &quot;she reinvests "
    "everything&quot; is a <b>result you proved</b> rather than an assumption "
    "you smuggled in. That distinction is worth marks and costs one extra "
    "variable.", body))

# ------------------------------------------------------------------ step 2
story.append(P("Step 2. Index it", h1))
story.append(P(
    "What does the decision vary over? Two things: which epoch, and which "
    "instrument. Two things means two subscripts.", body))
story.append(P("x_{t,k} = dollars placed at epoch t into an instrument of "
               "term k", mono))
story.append(P(
    "The idle-cash decision varies over one thing, the epoch, so it takes one "
    "subscript: w_t.", body))
story.append(P(
    "Notice what we did not write: x1, x2, ... x11. There are eleven "
    "admissible combinations here. Naming them one by one would work, would be "
    "unreadable, and would break the moment a fourth instrument appeared.",
    body))

# ------------------------------------------------------------------ step 3
story.append(P("Step 3. The tables, before any math", h1))
story.append(P("Sets", h2))
story.append(grid([
    ["Symbol", "Definition"],
    ["T = {1,...,5}", "decision epochs, the beginning of each year"],
    ["K = {1,2,3}", "instrument types, indexed by term in years"],
    ["A", "the admissible pairs (t,k) with t &gt;= a_k <b>and</b> t + L_k &lt;= 6"],
], [1.3 * inch, 4.4 * inch]))
story.append(Spacer(1, 5))
story.append(P(
    "The set A is doing real work. It is where the time convention gets "
    "enforced, once, instead of being scattered through the constraints.",
    body))

story.append(P("Parameters", h2))
story.append(grid([
    ["Symbol", "Definition", "Value"],
    ["L_k", "term of instrument k, <b>years</b>", "1, 2, 3"],
    ["r_k", "total return multiplier over the full term", "1.04, 1.09, 1.15"],
    ["a_k", "first epoch instrument k is available", "1, 1, <b>2</b>"],
    ["B", "initial endowment, <b>dollars</b>", "5,000"],
    ["H", "horizon epoch", "6"],
], [0.7 * inch, 3.3 * inch, 1.7 * inch]))
story.append(Spacer(1, 5))
story.append(P(
    "a_3 = 2 is how &quot;Pioneer opens at the start of Year 2&quot; becomes "
    "mathematics. One number in a table.", body))

story.append(P("Decision variables", h2))
story.append(P("x_{t,k} &gt;= 0&nbsp;&nbsp;&nbsp;&nbsp;dollars, for all (t,k) "
               "in A<br/>"
               "w_t&nbsp;&nbsp;&nbsp;&nbsp; &gt;= 0&nbsp;&nbsp;&nbsp;&nbsp;"
               "dollars, for all t in T", mono))

story.append(KeepTogether([
    P("Now count what A actually contains", h2),
    P("A two-minute hand check that catches convention errors.", body),
    Spacer(1, 3),
    grid([
        ["k", "condition", "admissible t", "count"],
        ["1 (1-yr)", "t + 1 &lt;= 6", "1, 2, 3, 4, 5", "5"],
        ["2 (2-yr)", "t + 2 &lt;= 6", "1, 2, 3, 4", "4"],
        ["3 (3-yr)", "t &gt;= 2 and t + 3 &lt;= 6", "<b>2, 3 only</b>", "2"],
    ], [0.9 * inch, 1.8 * inch, 1.9 * inch, 0.6 * inch])]))
story.append(Spacer(1, 6))
story.append(P(
    "Eleven pairs. And look at the last row. The Pioneer certificate has "
    "<b>exactly two possible start dates in the entire problem</b>. It cannot "
    "start at epoch 1, because it is not open yet, and it cannot start at "
    "epoch 4 or later, because it would not mature in time. So before solving "
    "anything you already know the interesting question is roughly &quot;epoch "
    "2, epoch 3, or not at all&quot;.", body))

# ------------------------------------------------------------------ step 4
story.append(P("Step 4. The objective", h1))
story.append(P(
    "What is the final cash? Everything that matures <i>exactly</i> at the "
    "horizon, plus any cash sitting idle at the end.", body))
story.append(P("max&nbsp;&nbsp;sum over (t,k) in A with t + L_k = H of "
               "r_k x_{t,k}&nbsp;&nbsp;+&nbsp;&nbsp;w_5", mono))
story.append(P(
    "The condition t + L_k = H is the whole trick. Only deposits maturing "
    "precisely at epoch 6 pay into the final total. A deposit maturing at "
    "epoch 4 does not appear in the objective at all. It appears in the "
    "balance constraint at epoch 4, gets reinvested, and reaches the horizon "
    "through whatever it was reinvested into.", body))
story.append(P(
    "That is the part that confuses people. <b>Money reaches the objective "
    "only through the last hop.</b> Everything earlier is bookkeeping.", body))

# ------------------------------------------------------------------ step 5
story.append(P("Step 5. The constraints", h1))
story.append(P(
    "There is only one idea here, said five times. In words: at every epoch, "
    "the money you put out equals the money you have available.", body))
story.append(P("At epoch 1 the money available is just the endowment.", body))
story.append(P("sum_k x_{1,k} + w_1 = B", mono))
story.append(P(
    "At epochs 2 through 5 it is whatever matured just now plus whatever you "
    "carried forward.", body))
story.append(P("sum_k x_{t,k} + w_t  =  sum over (s,k) with s + L_k = t of "
               "r_k x_{s,k}  +  w_{t-1}", mono))
story.append(P(
    "Read it left to right: what I allocate now, plus what I hold back, equals "
    "what just matured, plus what I carried in.", body))
story.append(P(
    "This is <b>flow conservation on a timeline</b>. Structurally it is the "
    "same equation as the network flow constraint in Problems 2 and 3, "
    "out minus in equals b, where b is +$5,000 at epoch 1 and zero everywhere "
    "after. Once you see that, three of the four homework problems are the "
    "same object.", body))

story.append(KeepTogether([
    P("Trace it with the actual answer, so it stops being abstract", h2),
    Spacer(1, 3),
    grid([
        ["Epoch", "What matured", "Carried in", "Available", "Allocated",
         "Idle"],
        ["1", "&mdash;", "&mdash;", "$5,000 endowment", "$5,000 into 2-yr",
         "0"],
        ["2", "nothing", "0", "0", "0", "0"],
        ["3", "5,000 x 1.09 = <b>$5,450</b>", "0", "$5,450",
         "$5,450 into 3-yr", "0"],
        ["4", "nothing", "0", "0", "0", "0"],
        ["5", "nothing", "0", "0", "0", "0"],
        ["6", "5,450 x 1.15 = <b>$6,267.50</b>", "&mdash;", "<i>horizon</i>",
         "&mdash;", "&mdash;"],
    ], [0.5 * inch, 1.75 * inch, 0.65 * inch, 1.1 * inch, 1.15 * inch,
        0.45 * inch])]))
story.append(Spacer(1, 6))
story.append(P(
    "Every row balances. Epoch 2 looks empty, and that is correct. The money "
    "is locked inside the two-year deposit, so there is genuinely nothing to "
    "decide that year.", body))

# ------------------------------------------------------------------ step 6
story.append(P("Step 6. Domains", h1))
story.append(P("x_{t,k} &gt;= 0&nbsp;&nbsp;&nbsp;&nbsp;for all (t,k) in A<br/>"
               "w_t&nbsp;&nbsp;&nbsp;&nbsp; &gt;= 0&nbsp;&nbsp;&nbsp;&nbsp;"
               "for all t in T", mono))
story.append(P(
    "Continuous, not integer. Money is divisible: you can deposit $5,450.00 or "
    "$3,217.63. <b>Nothing here needs to be a whole number</b>, so do not make "
    "it one. Forcing integrality would be a modelling error that also makes "
    "the problem harder to solve, for nothing.", body))

# ------------------------------------------------------------------ step 7
story.append(P("Step 7. Classify it, on the slide 8 to 10 taxonomy", h1))
story.append(grid([
    ["Question", "Answer"],
    ["Constrained?", "Yes"],
    ["Variable type and size",
     "continuous, 11 x variables plus 5 w variables, <b>16 in total</b>"],
    ["Objective type", "linear"],
    ["Constraint type and size",
     "linear, <b>5 equality rows</b> plus nonnegativity"],
    ["Parameters", "<b>deterministic</b>, every rate known up front"],
    ["Stages and players", "<b>single stage, one player</b>"],
], [1.7 * inch, 4.0 * inch]))
story.append(Spacer(1, 6))
story.append(P(
    "So it is a plain linear program, the smallest and friendliest object in "
    "this course. Compare with Problem 3, where the same six questions answer "
    "&quot;stochastic, two-stage&quot; and the whole solution method changes.",
    body))

# ------------------------------------------------------------------ sanity
story.append(P("Sanity check before solving", h1))
story.append(KeepTogether([
    P("Every admissible plan is a way of tiling the five years with blocks of "
      "length 1, 2 and 3, where no 3-block may start at epoch 1. So the value "
      "of a plan is the product of its multipliers, times $5,000. There are "
      "only a handful, and you can check the answer by hand.", body),
    Spacer(1, 3),
    grid([
        ["Plan, terms in order", "Multiplier", "Final"],
        ["1,1,1,1,1", "1.04<super>5</super> = 1.2167", "$6,083.26"],
        ["1,1,1,2 in any order", "1.04<super>3</super> x 1.09 = 1.2261",
         "$6,130.51"],
        ["1,2,2 in any order", "1.04 x 1.09<super>2</super> = 1.2356",
         "$6,178.12"],
        ["1,1,3 or 1,3,1", "1.04<super>2</super> x 1.15 = 1.2438",
         "$6,219.20"],
        ["<b>2 then 3</b>", "<b>1.09 x 1.15 = 1.2535</b>",
         "<b>$6,267.50</b>"],
        ["3 then 2", "&mdash;",
         "<b>not allowed</b>, the 3-year cannot start at epoch 1"],
    ], [1.6 * inch, 2.0 * inch, 2.1 * inch])]))
story.append(Spacer(1, 6))
story.append(P(
    "The winner is two-year then three-year. Notice the row underneath it. "
    "Three-then-two would give the same 1.2535 multiplier, but Pioneer is not "
    "open at epoch 1. The availability date is not decoration: it removes one "
    "of only two ways to reach the best multiplier, and it is exactly the kind "
    "of detail a problem statement buries in a subordinate clause.", body))
story.append(P(
    "<b>Doing this table by hand before you solve is not wasted time.</b> It "
    "is how you find out your model is wrong when it returns $6,219.20 instead "
    "of $6,267.50.", body))

# ------------------------------------------------------------------ result
story.append(P("Reading the answer properly", h1))
story.append(P("The solver returns $6,267.50, with this plan:", body))
story.append(Spacer(1, 3))
story.append(grid([
    ["Epoch", "Term", "Amount", "Matures at"],
    ["1", "2 years", "$5,000.00", "epoch 3"],
    ["3", "3 years", "$5,450.00", "epoch 6"],
], [0.8 * inch, 1.1 * inch, 1.2 * inch, 1.2 * inch]))
story.append(Spacer(1, 6))
story.append(P(
    "No idle cash at any epoch, which confirms what we predicted but did not "
    "assume.", body))
story.append(P(
    "Now check the <b>shadow price</b> on the epoch-1 balance constraint. It "
    "comes back at <b>1.2535</b>, which is 1.09 times 1.15: the compounded "
    "multiplier of the winning plan, exactly. The economic reading is that one "
    "extra dollar handed to Maya at the start of Year 1 becomes $1.2535 at the "
    "horizon, because she would route it through the same best chain.", body))
story.append(P(
    "When the dual independently reproduces a number you can derive by hand "
    "from the primal, you have genuine confirmation rather than a solver you "
    "are trusting on faith. That is what shadow prices are for, and it is the "
    "kind of thing an oral exam asks about.", body))

# ------------------------------------------------------------------ transfer
story.append(KeepTogether([
    P("What transfers to any problem like this", h1),
    P("Anything with money, inventory or stock moving through time is this "
      "same problem in a costume. The pattern:", body),
    N("<b>Fix the time convention first</b>, and write it down. Start "
      "of period or end of period. Everything downstream depends on it.", 1),
    N("<b>One balance equation per period.</b> What I use now equals what "
      "became available now plus what I carried in.", 2),
    N("<b>Availability windows and term lengths live in the set "
      "definition</b>, not in the constraints.", 3),
    N("<b>Only the final hop enters the objective.</b> Everything else flows "
      "through balance.", 4),
    N("<b>Put in a &quot;do nothing&quot; variable</b> and let the solver "
      "prove it stays at zero.", 5),
    Spacer(1, 8),
    Table([[""]], colWidths=[AVAIL], rowHeights=[1],
          style=TableStyle([("LINEABOVE", (0, 0), (-1, 0), 0.6, BLACK)])),
    Spacer(1, 5),
    P("Swap deposits for warehouse inventory, and the return multiplier for a "
      "spoilage rate. Same five moves, same model, a different table of "
      "numbers.", body)]))


doc = BaseDocTemplate(OUT, pagesize=letter,
                      leftMargin=LM, rightMargin=RM,
                      topMargin=TM, bottomMargin=BM,
                      title="Problem 1, Start to Finish",
                      author="IE 5311-001 Principles of Optimization, Fall 2026",
                      subject="Maya's investment plan worked through the "
                              "seven-step formulation method")
frame = Frame(LM, BM, PAGE_W - LM - RM, PAGE_H - TM - BM, id="body",
              leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
doc.addPageTemplates([PageTemplate(id="all", frames=[frame], onPage=footer)])
doc.build(story)
print("written:", OUT)
