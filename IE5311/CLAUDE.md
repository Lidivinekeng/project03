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
