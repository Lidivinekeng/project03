"""Build the IE 5311 optimization-homework method cheatsheet as a PDF.

Black text only. No colour, no icons, no rules other than plain hairlines.
All mathematical symbols are written in ASCII (<=, >=, "for all", "in") so the
file renders identically on any viewer and needs no embedded font.
"""

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (BaseDocTemplate, Frame, KeepTogether,
                                PageTemplate, Paragraph, Spacer, Table,
                                TableStyle)

OUT = "/home/user/project03/IE5311/how_to_do_the_homework.pdf"

PAGE_W, PAGE_H = letter
LM = RM = 0.9 * inch
TM = 0.85 * inch
BM = 0.85 * inch

BLACK = colors.black

ss = getSampleStyleSheet()

title = ParagraphStyle(
    "title", parent=ss["Normal"], fontName="Times-Bold", fontSize=19,
    leading=23, spaceAfter=4, textColor=BLACK)

subtitle = ParagraphStyle(
    "subtitle", parent=ss["Normal"], fontName="Times-Roman", fontSize=10.5,
    leading=14, spaceAfter=2, textColor=BLACK)

h1 = ParagraphStyle(
    "h1", parent=ss["Normal"], fontName="Times-Bold", fontSize=13.5,
    leading=17, spaceBefore=16, spaceAfter=6, textColor=BLACK,
    keepWithNext=1)

h2 = ParagraphStyle(
    "h2", parent=ss["Normal"], fontName="Times-Bold", fontSize=11,
    leading=14, spaceBefore=10, spaceAfter=4, textColor=BLACK,
    keepWithNext=1)

body = ParagraphStyle(
    "body", parent=ss["Normal"], fontName="Times-Roman", fontSize=10,
    leading=13.6, spaceAfter=6, alignment=TA_LEFT, textColor=BLACK)

bullet = ParagraphStyle(
    "bullet", parent=body, leftIndent=16, bulletIndent=5, spaceAfter=3)

mono = ParagraphStyle(
    "mono", parent=ss["Normal"], fontName="Courier", fontSize=8.8,
    leading=12, leftIndent=16, spaceBefore=3, spaceAfter=7, textColor=BLACK)

cell = ParagraphStyle(
    "cell", parent=ss["Normal"], fontName="Times-Roman", fontSize=9,
    leading=11.5, textColor=BLACK)

cellb = ParagraphStyle(
    "cellb", parent=cell, fontName="Times-Bold")

quote = ParagraphStyle(
    "quote", parent=body, fontName="Times-Italic", leftIndent=18,
    rightIndent=12, spaceBefore=4, spaceAfter=8)


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
    cmds = [
        ("GRID", (0, 0), (-1, -1), 0.4, BLACK),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]
    t.setStyle(TableStyle(cmds))
    return t


def rule_after_heading(canvas, doc):
    pass


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Times-Roman", 8.5)
    canvas.setFillColor(BLACK)
    canvas.drawString(LM, BM - 24,
                      "IE 5311-001 Principles of Optimization, Fall 2026")
    canvas.drawRightString(PAGE_W - RM, BM - 24, "Page %d" % doc.page)
    canvas.setLineWidth(0.4)
    canvas.setStrokeColor(BLACK)
    canvas.line(LM, BM - 16, PAGE_W - RM, BM - 16)
    canvas.restoreState()


AVAIL = PAGE_W - LM - RM

story = []

# ---------------------------------------------------------------- front matter
story.append(P("How to Do an Optimization Homework", title))
story.append(P("A working method, step by step. IE 5311-001 (D01) Principles "
                "of Optimization, Fall 2026. Instructor: Ningji Wei.", subtitle))
story.append(Spacer(1, 3))
story.append(Table([[""]], colWidths=[AVAIL], rowHeights=[1],
                   style=TableStyle([("LINEABOVE", (0, 0), (-1, 0), 1.0, BLACK)])))
story.append(Spacer(1, 10))

story.append(P(
    "This is the machine. The same seven moves every time, whatever the story "
    "is. Work through it with the sheet open beside you. After about five "
    "problems you will not need it any more.", body))

# ---------------------------------------------------------------- the idea
story.append(P("The thing nobody tells you first", h1))
story.append(P(
    "An optimization problem is always the same three questions wearing a "
    "costume:", body))
story.append(N("What am I allowed to choose?", 1))
story.append(N("What am I trying to make big, or small?", 2))
story.append(N("What stops me from cheating?", 3))
story.append(Spacer(1, 4))
story.append(P(
    "Investment planning, shortest path, a warehouse network, Sudoku. All four "
    "of our homework problems are that. The story changes. The machine does "
    "not.", body))

# ---------------------------------------------------------------- step 1
story.append(P("Step 1. Find the decision", h1))
story.append(P(
    "Read the problem once for the story. Then read it again asking one "
    "question only: what could I change, if I were in charge?", body))
story.append(P(
    "The test that never fails: <b>if I handed you these numbers on paper, "
    "could you walk out and execute it?</b>", body))
story.append(B('"Put $3,000 into the two-year deposit at the start of Year 1" '
               '&mdash; yes, executable, so it is a <b>decision</b>.'))
story.append(B('"The two-year deposit pays 9%" &mdash; you cannot change that, '
               'so it is a <b>parameter</b>.'))
story.append(B('"I end Year 5 with $6,267.50" &mdash; that is what <i>happens</i>, '
               'not what you <i>choose</i>. A <b>result</b>, not a variable.'))
story.append(Spacer(1, 4))
story.append(P(
    "That last one is where most people lose marks. The quantity the problem "
    "asks you to maximize is usually <b>not</b> a variable. It is a consequence "
    "of your variables.", body))
story.append(Spacer(1, 4))
story.append(grid([
    ["Problem", "The decision is", "Not"],
    ["P1 Investment", "dollars into each instrument at each epoch",
     "the final balance"],
    ["P2 Path", "which arcs you walk on", "the path length"],
    ["P3 Network", "units shipped on each lane", "total cost"],
    ["P4 Sudoku", "which digit sits in which cell", "&quot;solving the puzzle&quot;"],
], [1.1 * inch, 2.9 * inch, 1.7 * inch]))

# ---------------------------------------------------------------- step 2
story.append(P("Step 2. Index before you write anything", h1))
story.append(P(
    "This is the class rule and it is not decoration. Never write x1, x2, x3.", body))
story.append(P(
    "Ask: what does this decision vary over? Count the answers. That is your "
    "number of subscripts.", body))
story.append(B("Varies over <i>time</i> and <i>which instrument</i>, so two "
               "things, so x_{t,k}"))
story.append(B("Varies over <i>which arc</i>, so one thing (though an arc is a "
               "pair), so x_{ij}"))
story.append(B("Varies over <i>row</i>, <i>column</i>, <i>digit</i>, so three, "
               "so x_{r,c,v}"))
story.append(Spacer(1, 4))
story.append(KeepTogether([
    P("Then name the set each subscript lives in, before the variable exists:",
      body),
    P("T = {1,...,5}&nbsp;&nbsp;&nbsp;&nbsp;epochs, indexed by t<br/>"
      "K = {1,2,3}&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;instrument terms, "
      "indexed by k", mono)]))
story.append(P(
    "I assume this feels like extra paperwork the first time. It is not. The "
    "moment the professor says &quot;now do it with 40 foods instead of 6&quot;, "
    "the indexed model needs zero edits. The x1, x2, x3 model needs a rewrite.", body))

# ---------------------------------------------------------------- step 3
story.append(P("Step 3. Fill the table before you write any math", h1))
story.append(P("Four blocks, in this order, always.", body))
story.append(grid([
    ["Block", "What goes in it"],
    ["Sets", "with the index letter"],
    ["Parameters", "with units. c_i = cost per unit of food i, <b>dollars per unit</b>"],
    ["Decision variables",
     "with domain and units. x_i &gt;= 0 = units of food i per day, "
     "<b>units per day</b>"],
    ["Then the model", "objective, constraints, domains"],
], [1.4 * inch, 4.3 * inch]))
story.append(Spacer(1, 6))
story.append(P(
    "The units rule is the cheapest error-catcher you own. If you cannot write "
    "the unit, you do not yet understand the quantity. And when you multiply "
    "c_i times x_i you should get dollars per day. If you get dollars per unit "
    "squared, something upstream is wrong.", body))

# ---------------------------------------------------------------- step 4
story.append(P("Step 4. The objective is one line", h1))
story.append(KeepTogether([
    P("It is always a sum over an index set.", body),
    P("min&nbsp;&nbsp;sum_{i in I} c_i x_i", mono)]))
story.append(P(
    "<b>If a specific number appears in your objective, you have made a "
    "mistake.</b> Numbers live in the parameter table. The objective mentions "
    "symbols only.", body))

# ---------------------------------------------------------------- step 5
story.append(P("Step 5. Constraints, or English into mathematics", h1))
story.append(P(
    "This is the part that feels like magic until you see that it is a lookup "
    "table. Go through the problem text sentence by sentence. Every sentence "
    "that restricts you becomes a row.", body))
story.append(Spacer(1, 4))
story.append(grid([
    ["What the problem says", "What you write"],
    ['&quot;at most&quot;, &quot;no more than&quot;, &quot;capacity of&quot;, '
     '&quot;budget&quot;', "&lt;="],
    ['&quot;at least&quot;, &quot;minimum&quot;, &quot;must cover&quot;, '
     '&quot;required&quot;', "&gt;="],
    ['&quot;exactly&quot;, &quot;all of it&quot;, &quot;must equal&quot;, '
     '&quot;one per&quot;', "="],
    ['&quot;each&quot;, &quot;every&quot;, &quot;for all&quot;',
     "the quantifier: for all i in I"],
    ['&quot;either / or&quot;, &quot;if we open, then&quot;, &quot;yes or '
     'no&quot;', "a binary variable"],
    ['&quot;what arrives must leave&quot;',
     "flow balance: out(i) - in(i) = b_i"],
    ['&quot;visit at most once&quot;', "degree constraint: &lt;= 1"],
], [3.3 * inch, 2.4 * inch]))
story.append(Spacer(1, 7))
story.append(KeepTogether([
    P("Three questions that sweep the problem for anything you missed:", h2),
    N("<b>What is limited?</b> Capacity, supply, budget, hours. These give "
      "&lt;= rows.", 1),
    N("<b>What must be met exactly?</b> Demand, balance, &quot;exactly one "
      "digit per cell&quot;. These give = rows.", 2),
    N("<b>What is a floor?</b> Nutrition minimums, service levels. These give "
      "&gt;= rows.", 3)]))
story.append(Spacer(1, 5))
story.append(KeepTogether([
    P("Write each <i>family</i> once, with a quantifier:", body),
    P("sum_{i in I} a_ij x_i &lt;= b_j&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
      "for all j in J", mono)]))
story.append(P(
    "Not eleven separate rows with numbers inside them. One row, with a "
    "&quot;for all&quot;.", body))

# ---------------------------------------------------------------- step 6
story.append(P("Step 6. Domains go on their own line", h1))
story.append(P(
    "x_i &gt;= 0, or x_ij in {0,1}, or y_i integer. Kept separate from the "
    "structural constraints. The class wants them split, and it also lets you "
    "see at a glance whether you are holding a linear program or an integer "
    "program.", body))

# ---------------------------------------------------------------- step 7
story.append(P("Step 7. Classify it, on the slide 8 to 10 taxonomy", h1))
story.append(P("Six questions, every model, no exceptions. This is where the "
               "deep-understanding marks live.", body))
story.append(N("Constrained or unconstrained?", 1))
story.append(N("Variable type and size. Continuous, integer, binary? How many?", 2))
story.append(N("Objective type and size. Linear? Convex?", 3))
story.append(N("Constraint type and size. Linear? How many rows?", 4))
story.append(N("Parameters deterministic or stochastic?", 5))
story.append(N("How many decision stages? How many players?", 6))
story.append(Spacer(1, 4))
story.append(P(
    "Questions 5 and 6 are the ones people skip, and they are exactly what "
    "separated the three parts of Problem 3 from one another.", body))

# ---------------------------------------------------------------- sanity
story.append(P("Before you touch a solver: four sanity checks", h1))

story.append(P("1. Check the arithmetic of the setup", h2))
story.append(P(
    "In Problem 3, total supply is 120 and total demand is 120. Had those not "
    "matched, no model on earth would be feasible. Two minutes of adding saves "
    "an hour of debugging.", body))

story.append(P("2. Find one feasible point by hand", h2))
story.append(P(
    "Can you produce <i>any</i> legal answer? If you cannot, either the problem "
    "is genuinely infeasible or you have mis-translated a constraint.", body))

story.append(P("3. Look for the free lunch", h2))
story.append(P(
    "This is the one that bites hardest. Ask: can my model do something absurd "
    "and be rewarded for it?", body))
story.append(P(
    "In the longest-path problem the answer was yes. Maximize the sum of arc "
    "weights and the model happily returns a path <b>plus a pile of "
    "disconnected loops</b>, because every extra loop adds weight for free. "
    "Nothing in flow balance forbids it. That is why subtour elimination "
    "exists.", body))
story.append(P(
    "Under <b>minimization</b> with positive costs, a stray loop only adds "
    "cost, so it never appears and you never need those constraints. Under "
    "<b>maximization</b> they are mandatory. Same constraint set, opposite "
    "verdict, purely because the direction flipped.", body))
story.append(P(
    "Whenever you maximize, hunt for the free lunch before you solve.", body))

story.append(P("4. Watch for the trivially-optimal trap", h2))
story.append(P(
    "If your answer is &quot;do nothing&quot;, or &quot;one facility serves "
    "everybody&quot;, your instance may be too easy to demonstrate anything. "
    "That happened to us once and the data had to be replaced.", body))

# ---------------------------------------------------------------- solving
story.append(P("Then, and only then, solve", h1))
story.append(P(
    "Solve a tiny version first. Three nodes, two foods, whatever. You can "
    "verify a tiny answer in your head. Scale up once the small one is right.", body))
story.append(P("When the answer comes back, read it as an English sentence:", body))
story.append(P(
    "&quot;Put all $5,000 in the two-year deposit for Years 1 and 2, then roll "
    "everything into the Pioneer three-year certificate. Hold no idle cash. End "
    "with $6,267.50.&quot;", quote))
story.append(P(
    "If that sentence sounds insane, the model is wrong, not the world.", body))
story.append(P(
    "Then check the <b>shadow prices</b>. In Problem 1 the dual on the Year-1 "
    "balance came out at 1.2535, which is exactly the compounded multiplier of "
    "the winning plan. When the dual tells the same story as the primal, you "
    "have real confirmation. When it does not, go looking.", body))

# ---------------------------------------------------------------- write-up
story.append(P("Writing it up", h1))
story.append(P("Same order as your thinking, every time.", body))
for i, line in enumerate([
        "Restate the problem in your own words, two or three sentences",
        "Sets",
        "Parameters, with units",
        "Decision variables, with domain and units",
        "Objective",
        "Constraints, each family once, quantified",
        "Domain restrictions",
        "The slide 8 to 10 classification",
        "Result, stated as a sentence, with the reasoning that confirms it"], 1):
    story.append(N(line, i))
story.append(Spacer(1, 5))
story.append(P(
    "Code is a <b>check</b>, not the deliverable. Slide 6 puts 60 percent on "
    "method understanding. A perfect script with a hand-waved formulation "
    "scores badly. A correct formulation with no code at all scores well.", body))

# ---------------------------------------------------------------- shapes
story.append(KeepTogether([
    P("The four shapes you will keep meeting", h1),
    P("Once you recognize these, most problems stop being new.", body),
    Spacer(1, 3),
    grid([
    ["Shape", "Signature", "Where we met it"],
    ["Allocation over time",
     "a balance equation per period: what you hold equals what matured plus "
     "what you carried",
     "P1 Investment"],
    ["Network flow",
     "out(i) - in(i) = b_i, with b positive at sources, negative at sinks, "
     "zero in the middle",
     "P2 Paths, P3 Network"],
    ["Assignment and covering",
     "binary variables, and rows that sum to exactly 1",
     "P4 Sudoku"],
    ["Selection with a fixed charge",
     "binary y_i for &quot;open&quot;, continuous x_ij for &quot;use&quot;, "
     "and the link x_ij &lt;= y_i chaining them",
     "facility location, class 01"],
], [1.5 * inch, 2.9 * inch, 1.3 * inch])]))
story.append(Spacer(1, 6))
story.append(P(
    "On that last shape: write the link <b>disaggregated</b>, one row per pair. "
    "It gives a tighter LP bound than the lumped version, and we measured it. "
    "45.0 against 28.0, with an integer optimum of 46.0.", body))

# ---------------------------------------------------------------- mistakes
story.append(P("The five mistakes that cost the most marks", h1))
story.append(N("<b>Numbers inside constraints.</b> Writing 3x1 + 2x2 &lt;= 18 "
               "instead of sum_i a_ij x_i &lt;= b_j for all j. An automatic "
               "deduction in this class.", 1))
story.append(N("<b>Maximizing without checking for the free lunch.</b>", 2))
story.append(N("<b>Confusing the result with the decision.</b>", 3))
story.append(N("<b>Forgetting units</b>, then multiplying two things that "
               "should never have been multiplied.", 4))
story.append(N("<b>Skipping the classification.</b> It is worth marks and takes "
               "ninety seconds.", 5))

# ---------------------------------------------------------------- limits
story.append(P("Where this recipe honestly stops", h1))
story.append(P(
    "I will not pretend the whole thing is mechanical. Steps 3 through 7 are "
    "genuinely a checklist, and you can run them half asleep.", body))
story.append(P(
    "<b>Steps 1 and 2 are judgment</b>, and no recipe removes that. Deciding "
    "that the Problem 3 stochastic model splits into &quot;factory shipments "
    "committed before you see the capacity&quot; and &quot;store deliveries "
    "chosen after&quot; is a modelling choice. Reverse it and the whole problem "
    "collapses into a set of independent deterministic problems with nothing "
    "stochastic about them. The checklist does not make that call for you.", body))
story.append(P(
    "What the checklist does do is make sure that once you have made the call, "
    "nothing downstream gets fumbled. That is the eighty percent. The remaining "
    "twenty comes from working problems until the four shapes above become "
    "recognition rather than derivation.", body))
story.append(Spacer(1, 8))
story.append(Table([[""]], colWidths=[AVAIL], rowHeights=[1],
                   style=TableStyle([("LINEABOVE", (0, 0), (-1, 0), 0.6, BLACK)])))
story.append(Spacer(1, 5))
story.append(P(
    "Do five problems with this sheet open in front of you. By the sixth you "
    "will not need it.", body))


doc = BaseDocTemplate(OUT, pagesize=letter,
                      leftMargin=LM, rightMargin=RM,
                      topMargin=TM, bottomMargin=BM,
                      title="How to Do an Optimization Homework",
                      author="IE 5311-001 Principles of Optimization, Fall 2026",
                      subject="A step-by-step working method for formulating and "
                              "solving optimization problems")

frame = Frame(LM, BM, PAGE_W - LM - RM, PAGE_H - TM - BM, id="body",
              leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
doc.addPageTemplates([PageTemplate(id="all", frames=[frame], onPage=footer)])
doc.build(story)
print("written:", OUT)
