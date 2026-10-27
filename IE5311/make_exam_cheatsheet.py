"""IE 5311 one-page exam cheatsheet. Black text only, no colour, no icons.

Mathematics is written in ASCII so the file renders identically anywhere
and needs no embedded font. Content traces to the class 01 deck and to
homeworks 1 to 3; slide numbers are given as [n].
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (BaseDocTemplate, Frame, PageTemplate,
                                Paragraph, Spacer)

OUT = "/home/user/project03/IE5311/exam_cheatsheet.pdf"

PAGE_W, PAGE_H = letter
M = 0.4 * inch
GUT = 0.22 * inch
COL_W = (PAGE_W - 2 * M - GUT) / 2.0

BODY = ParagraphStyle(
    "body", fontName="Helvetica", fontSize=7.2, leading=8.5,
    textColor=colors.black, spaceBefore=0, spaceAfter=1.4)
HEAD = ParagraphStyle(
    "head", parent=BODY, fontName="Helvetica-Bold", fontSize=8.0,
    leading=9.2, spaceBefore=3.2, spaceAfter=1.6)
TITLE = ParagraphStyle(
    "title", parent=BODY, fontName="Helvetica-Bold", fontSize=9.5,
    leading=11, spaceAfter=0.5)
SUB = ParagraphStyle("sub", parent=BODY, fontSize=6.9, leading=8.0,
                     spaceAfter=3)
MONO = ParagraphStyle("mono", parent=BODY, fontName="Courier",
                      fontSize=6.7, leading=7.9, leftIndent=5,
                      spaceAfter=1.4)


def H(t):
    return Paragraph(t, HEAD)


def P(t):
    return Paragraph(t, BODY)


def C(t):
    return Paragraph(t, MONO)


S = []
S.append(Paragraph("IE 5311 Principles of Optimization &mdash; exam sheet",
                   TITLE))
S.append(Paragraph("Slide numbers in brackets. Grading [6]: 40% problem to "
                   "formulation to solution, 60% understand the method. "
                   "Theory is the bigger half.", SUB))

S.append(H("1. CLASSIFY FIRST [8-10]"))
S.append(P("Applied to diet [18], shortest path [27], DFJ [32]. Expect it "
           "on the exam. Nine axes:"))
S.append(C("1 constrained / unconstrained<br/>"
           "2 variables: continuous | discrete | mixed<br/>"
           "3 variable size: compact | huge finite | infinite-dim<br/>"
           "4 obj &amp; constr type: linear | convex | nonconvex<br/>"
           "5 constraint size: compact | huge finite | semi-infinite<br/>"
           "6 objective size: single | multi<br/>"
           "7 parameters: deterministic | stochastic<br/>"
           "8 stages: one | multi<br/>"
           "9 players: single | two | multi, simultaneous | sequential"))

S.append(H("2. WRITE EVERY MODEL IN THIS ORDER"))
S.append(P("Sets (with index) &rarr; Parameters (with units) &rarr; "
           "Variables (domain + units) &rarr; Objective as a sum &rarr; "
           "Constraints, each with a <i>for all</i> &rarr; Domains stated "
           "separately. Never enumerate numeric rows. "
           "<b>Define a derived set by its formula, never by a name.</b>"))

S.append(H("3. FIVE NOTIONS OF OPTIMAL, ONE NEWSVENDOR [39-59]"))
S.append(C("expectation  min E[f(x,xi)]            SAA over scenarios<br/>"
           "robust       min max_{xi in Xi} f      worst case [41,42]<br/>"
           "CVaR         min CVaR_beta(f)          tail average [58]<br/>"
           "chance       min c'x, P(feas) &gt;= gam   [59]<br/>"
           "DRO          min max_{P in Pset} E_P   change the measure [53]"))
S.append(P("Same word problem, five meanings of optimal. Closed form for "
           "the single-item newsvendor: q* = F^-1( b / (b+h) ), b underage, "
           "h overage. Wait-and-see (decide after xi) &le; here-and-now."))

S.append(H("4. RISK MEASURES [55-57]"))
S.append(C("VaR_b(Z)  = min{ t : P(Z &lt;= t) &gt;= b }<br/>"
           "CVaR_b(Z) = min over eta of  eta + (1/(1-b)) E[(Z-eta)+]"))
S.append(P("CVaR is an <b>infimum</b>, so to impose CVaR &le; Lambda you "
           "may let eta be a free decision variable: no inner minimisation "
           "needed, and the reformulation is exact."))
S.append(C("eta + (1/(1-b)) sum_s p_s u_s &lt;= Lambda<br/>"
           "u_s &gt;= Z_s - eta,   u_s &gt;= 0,   eta free"))
S.append(P("Dual / risk-envelope form, CVaR as a robust problem:"))
S.append(C("CVaR_b(Z) = max_{q in Q} sum_j q_j Z_j<br/>"
           "Q_b = { q &gt;= 0 : sum_j q_j = 1, q_j &lt;= p_j/(1-b) }"))
S.append(P("So constraint generation for CVaR runs over <b>Q</b>, not over "
           "scenarios: every scenario stays in the master, so the master "
           "stays bounded. Always VaR_b &le; CVaR_b and E[Z] &le; CVaR_b."))

S.append(H("5. PROBABILITY [43-57]"))
S.append(P("Space (Omega, F, P). F is a sigma-algebra: contains Omega, "
           "closed under complement and countable union. Pushforward of "
           "X: Omega &rarr; R is P_X(B) = P(X^-1(B)). Expectation as "
           "<b>dual pairing</b> &lt;P, Z&gt; [52] is the hinge: expectation, "
           "LP duality and conic duality are one idea in three settings."))

S.append(Spacer(1, 2))
S.append(H("6. INDICATOR AND BIG-M"))
S.append(P("Over a box l &le; x &le; u the extrema are separable:"))
S.append(C("Vmax(a) = sum_i max(a_i l_i, a_i u_i)   at x_i = u_i if a_i&gt;=0<br/>"
           "Vmin(a) = sum_i min(a_i l_i, a_i u_i)   at the other corner"))
S.append(C("z=1 =&gt; a'x&lt;=b : a'x &lt;= b + M(1-z), M = max{0, Vmax(a)-b}<br/>"
           "z=0 =&gt; a'x&gt;=b : a'x &gt;= b - N z,   N = max{0, b-Vmin(a)}<br/>"
           "z_k=z_l=1 =&gt; c'x&lt;=d : c'x &lt;= d + M(2 - z_k - z_l)<br/>"
           "violate only if active : g'x &lt;= h + M sum_k z_k"))
S.append(P("The pair and cover forms need <b>no extra binary</b>. Those M "
           "are smallest, and tight: the witness is the box corner above."))
S.append(P("A two-way equivalence needs a tolerance: add g'x &ge; h + eps "
           "&minus; N(1&minus;z_k) for all k. <b>Why eps cannot go:</b> "
           "{g'x &gt; h} is open, while a MILP feasible set is a finite "
           "union of closed polyhedra, hence closed. No exact MILP exists."))

S.append(H("7. CHANCE CONSTRAINTS"))
S.append(P("Joint, finite support, one binary per scenario:"))
S.append(C("u_js &lt;= (1-th) d_js + M_js (1 - z_s)   for all j, s<br/>"
           "sum_s p_s z_s &gt;= gamma<br/>"
           "smallest M_js = th * d_js   when 0 &lt;= u_js &lt;= d_js"))
S.append(P("M depends on <b>both</b> j and s; one global M is valid but "
           "loose. Joint &rArr; individual by monotonicity. The converse "
           "<b>fails</b>: the union bound gives only P(cap A_j) &ge; "
           "1 &minus; |J|(1&minus;gamma), and that is tight, so build the "
           "counterexample with disjoint failure events. Bonferroni fix: "
           "impose each region at level 1 &minus; (1&minus;gamma)/|J|."))

S.append(H("8. ROBUST AND CONSTRAINT GENERATION"))
S.append(P("A linear max over a polytope attains at an <b>extreme point</b>, "
           "so replace the inner max by one row per vertex. Too many "
           "vertices &rarr; master + separation subproblem [33,34], with "
           "finite convergence and correctness proofs. <b>Seed the master "
           "with a point inside Xi</b>: seeding outside makes the master a "
           "restriction, and it converges <i>above</i> the true optimum."))

S.append(H("9. EXACTNESS AND INTEGRALITY [25,26]"))
S.append(P("A is totally unimodular if every square submatrix has "
           "determinant in {0, +1, &minus;1}. TU with integer b makes every "
           "vertex of {Ax &le; b, x &ge; 0} integral, so the LP relaxation "
           "is exact &mdash; which is why shortest path needs no binaries. "
           "Node-arc incidence matrices of digraphs are TU. DFJ vs MTZ [30]: "
           "same feasible solutions, different strength; DFJ has "
           "exponentially many subtour rows."))

S.append(H("10. TWO-STAGE STOCHASTIC"))
S.append(C("min c'x + sum_s p_s Q(x, xi_s),  y_s chosen AFTER xi_s"))
S.append(P("<b>Scenario-index every second-stage variable.</b> A bound that "
           "must hold in every realisation is a <i>robust</i> constraint and "
           "does not belong in an average-case model. For feasibility under "
           "uncertainty use a chance constraint or recourse."))

S.append(H("11. LINEAR ALGEBRA GATE [7]"))
S.append(P("Basis = independent + spanning; dim = size of a basis. The "
           "vector is the object, the coordinate list [v]_B is not. "
           "Independence, two equivalent definitions: (i) no v_i lies in the "
           "span of the others; (ii) sum a_i v_i = 0 forces every a_i = 0. "
           "Prove the equivalence by <b>contraposition</b> both ways; "
           "invertibility of a nonzero scalar is the only thing used, so it "
           "needs a field. Change of basis: the columns of P are the new "
           "basis in old coordinates; B' is a basis iff det P &ne; 0; solve "
           "P a = [v]_B. T linear iff T(lf + mg) = l T(f) + m T(g); the "
           "columns of its matrix are the images of the basis. "
           "ker T = {v : Tv = 0}, range T = span of those images, and "
           "<b>dim ker + dim range = dim V</b>."))

S.append(H("12. GROUPS"))
S.append(P("Closure, associativity, identity, inverse. Commutativity is "
           "<b>not</b> required. Inverse is unique: b = be = b(ac) = (ba)c "
           "= ec = c, hence (a^-1)^-1 = a. GL_n(R) is a group since "
           "det(AB) = det A det B &ne; 0, non-abelian for n &ge; 2. The "
           "rotations of a square are Z/4Z, cyclic, generated by the "
           "quarter turn."))

S.append(H("13. WHAT HAS COST MARKS"))
S.append(P("Naming a derived set instead of writing its formula. A robust "
           "bound inside a stochastic model. Generating CVaR cuts over "
           "scenarios rather than over the risk envelope. Hedging a "
           "performance claim is fine when the hedge is true."))

S.append(H("14. THE PART 1 PROBLEM LIST [12-61]"))
S.append(P("Outline [12]: Part 1 classic problems, Part 2 linear "
           "programming, Part 3 conic programming. Topics marked ** are "
           "optional: write a short review for 1 point each, cap 10."))
S.append(C("diet [14-19]       continuous, LP, determ., 1-stage, 1-player<br/>"
           "shortest path [20-27] binary compact, linear, determ.<br/>"
           "TSP / DFJ [28-35]  huge but finite constraint set<br/>"
           "facility loc [36-38]  two-player<br/>"
           "newsvendor [39-59] five criteria, see box 3<br/>"
           "stoch. shortest path [60]"))
S.append(P("Stigler pruned 77 foods to 15 by hand and got $39.93; Dantzig "
           "solved it exactly at $39.69 by simplex seven years later. The "
           "24 cents started the field. Convex preview [61]: portfolio "
           "(convex, multi-objective), inventory (stochastic expectation), "
           "robust shortest path (worst case, semi-infinite), multi-period "
           "inventory (MDP), bilevel pricing (sequential two-player)."))

S.append(H("15. GRAPH VOCABULARY [20-24]"))
S.append(P("Undirected: neighbourhood, degree, cut, walk, trail, path, "
           "cycle. A walk repeats anything, a trail repeats no edge, a path "
           "repeats no vertex. Directed: in- and out-neighbourhood, in- and "
           "out-degree, in-cut and out-cut. Flow balance is written on the "
           "in-cut minus the out-cut at each node."))

S.append(H("16. PROOF MOVES THAT KEEP COMING BACK"))
S.append(P("<b>Contraposition</b> for an equivalence of two definitions: "
           "show each fails exactly when the other does. "
           "<b>Uniqueness</b> by writing one object two ways and collapsing "
           "the chain, as with the group inverse. <b>Monotonicity</b> of "
           "probability for one direction of joint versus individual. "
           "<b>Extreme point</b> arguments to turn an infinite max into "
           "finitely many rows. <b>Closedness</b> to prove no exact MILP "
           "exists. State what each step uses; the marks are in the reason, "
           "not the result."))

doc = BaseDocTemplate(OUT, pagesize=letter,
                      leftMargin=M, rightMargin=M,
                      topMargin=M, bottomMargin=M,
                      title="IE 5311 exam cheatsheet", author="")
fl = Frame(M, M, COL_W, PAGE_H - 2 * M, id="l",
           leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
fr = Frame(M + COL_W + GUT, M, COL_W, PAGE_H - 2 * M, id="r",
           leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
doc.addPageTemplates([PageTemplate(id="two", frames=[fl, fr])])
doc.build(S)
print(f"wrote {OUT}")
print(f"pages: {doc.page}")
if doc.page != 1:
    raise SystemExit(f"NOT ONE PAGE: {doc.page} pages; trim content or "
                     f"reduce fontSize/leading")
