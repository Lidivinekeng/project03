# IE 5311-001 (D01) Principles of Optimization, Fall 2026

Instructor: Ningji Wei, Industrial, Manufacturing and Systems Engineering.

## Scope rule

All work traces to lecture material the student supplies. Do not import
problems, notation or textbook examples from outside the course decks.
Cite slide numbers.

## Formulation convention (binding on every model)

Present every formulation in general indexed form. Never write separate
constraints for specific numerical values.

Every formulation states, in this order:

1. **Sets**, with an index symbol. Example: `I` = set of foods, indexed
   by `i`.
2. **Parameters**, indexed over those sets, with units. Example:
   `c_i` = cost per unit of food `i`, in dollars.
3. **Decision variables**, indexed, with domain and units. Example:
   `x_i >= 0` = units of food `i` purchased per day.
4. **Objective**, written as a sum over an index set.
5. **Constraints**, each written once with a `for all i in I` quantifier.
6. **Domain restrictions** stated separately from structural constraints.

Rejected: a constraint list enumerating `3*x1 + 2*x2 <= 18` style rows
for named numeric data. Accepted: `sum_{i in I} a_{ij} x_i <= b_j` for
all `j in J`, with the numbers living in the parameter table.

Give the compact matrix form alongside the indexed form where one exists.

Classify every formulation on the taxonomy from slides 8 through 10:
constrained or not, variable type and size, objective and constraint
type and size, deterministic or stochastic parameters, decision stages,
number of players.

## Solver policy

The LaTeX write-up is the graded deliverable and contains no solver code.
Every formulation must be readable and checkable without running
anything.

Code is a verification step only. Default to PuLP with the bundled CBC
solver, which needs no license and no registration. Gurobi is optional.
Reach for it only where CBC genuinely falls short, chiefly lazy
constraint callbacks for DFJ subtour elimination (slides 29 to 34).

Where both are written, they must agree on objective value, solution and
shadow prices.

## Writing conventions

- LaTeX preamble limited to geometry, amsmath, amssymb, amsthm so files
  build on a base TeX install.
- Documents are black text only. No color, no icons.
- Prove results by hand first. Code verifies, it does not substitute.
  Slide 6 weights deep method understanding at 60 percent.

## Confirmed by graded feedback (HW1 returned 128 + 2 of 135)

These are not style preferences. Each one cost marks, and each was then
checked against the official solution.

### Define every derived set by formula, never by name

HW1 Problem 4 lost 5 of 30. The block constraint used `cells(b)`, named in
the symbol table and glossed in prose. The grader wrote "How do you define
this" and, next to the sub-block set, "How define it".

The official solution never introduces such a set. It indexes the blocks by
a pair and writes the ranges out:

    P = Q = {0,1,2}
    sum_{i=3p+1}^{3p+3} sum_{j=3q+1}^{3q+3} x_ijk = 1   for all p in P, q in Q, k in K

So: if a set is derived rather than given, write the formula that produces
it. A name plus a sentence is not a definition.

### In a stochastic model, let every variable depend on the scenario

HW1 Problem 3 lost 2 of 45. The two-stage program bounded the first stage by
`x_ij <= 0.99 u_ij`, the worst-case capacity. The grader wrote "this is for
robust optimization not stochastic. you may consider all variables depend to
uncertainty."

The official solution confirms the reading: it makes the shipment itself
scenario-indexed, `x^w_ij`, with `0 <= x^w_ij <= u^w_ij`, on the stated
assumption that shipments can be adjusted once the scenario is observed. A
wait-and-see model, not a here-and-now one with a robust bound bolted on.

So: a bound that must hold in every realization is a robust constraint. It
does not belong in an average-case model unless the problem asks for it.
Where feasibility under uncertainty is genuinely wanted, the two legitimate
devices are a chance constraint or second-stage recourse.

### Constraint generation for CVaR runs over the risk envelope

Noted from the HW2 official solution, not from a deduction. Asked for a
master-subproblem procedure for CVaR, the course generates cuts over the
risk envelope

    Q_beta = { q >= 0 : sum_j q_j = 1,  q_j <= p_j/(1-beta) }

with the master holding `t >= sum_j q_j f(x,xi^j)` for the q generated so
far, and the separation an LP in q at fixed x. Every scenario stays in the
master, so the master is always bounded.

Generating over scenarios instead is a different algorithm. It converges,
but dropping scenarios makes the master unbounded below until the working
set carries `1-beta` of the probability mass, which has to be repaired with
a valid bound such as `eta >= 0`. Prefer the envelope version unless the
question asks otherwise.

### Hedging a performance claim is acceptable when the hedge is true

HW2 Problem 2 part 6 asks which of two reformulations is more efficient. The
official solution answers that the smaller one is likely faster "however, for
such small LPs, the actual difference in computational time may be
negligible". Measuring and reporting that the difference is below timing
noise is the expected answer, not a dodge.
