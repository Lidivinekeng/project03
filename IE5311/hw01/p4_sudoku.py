"""
IE 5311 Homework, Problem 4 [30 pts]: Sudoku as a binary program.

SETS
    R = C = V = {1,...,9}     rows, columns, digit values
    B = {1,...,9}             the nine 3x3 sub-blocks
    cells(b) subset R x C     the nine cells belonging to block b
    G subset R x C x V        the given clues: (r,c,v) in G means cell
                              (r,c) is pre-filled with digit v

DECISION VARIABLES
    x_{r,c,v} in {0,1}        1 if cell (r,c) holds digit v

MODEL (pure feasibility: every constraint is an equality, so any
feasible point is a completed puzzle. A constant objective is used.)

    sum_{v in V} x_{r,c,v} = 1                  for all r in R, c in C
    sum_{c in C} x_{r,c,v} = 1                  for all r in R, v in V
    sum_{r in R} x_{r,c,v} = 1                  for all c in C, v in V
    sum_{(r,c) in cells(b)} x_{r,c,v} = 1       for all b in B, v in V
    x_{r,c,v} = 1                               for all (r,c,v) in G

Sizes: 729 binary variables, 324 structural equalities plus |G| clue
fixings. Each of the four families says the same thing in a different
direction, which is why all four are needed: the first assigns one digit
per cell, the other three enforce the three uniqueness rules.
"""

import gurobipy as gp
from gurobipy import GRB

N = 9
BLK = 3
R = C = V = range(1, N + 1)

# The instance from the assignment, transcribed from the document table.
# 0 marks an empty cell.
PUZZLE = [
    [0, 0, 2, 0, 0, 5, 0, 0, 0],
    [0, 0, 1, 6, 0, 2, 0, 0, 0],
    [9, 3, 8, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 7, 4, 0, 6, 0],
    [0, 7, 0, 0, 0, 0, 2, 0, 0],
    [3, 0, 0, 0, 0, 0, 0, 1, 0],
    [0, 0, 0, 9, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 2, 0, 9, 0, 8],
    [0, 1, 0, 8, 0, 0, 0, 0, 3],
]


def block_cells(b):
    """Cells of block b, numbered 1..9 left to right then top to bottom."""
    br, bc = divmod(b - 1, BLK)
    return [(br * BLK + i + 1, bc * BLK + j + 1)
            for i in range(BLK) for j in range(BLK)]


def build(clues, forbid=()):
    m = gp.Model("sudoku")
    m.setParam("OutputFlag", 0)
    x = m.addVars(R, C, V, vtype=GRB.BINARY, name="x")
    m.setObjective(0, GRB.MINIMIZE)

    m.addConstrs((x.sum(r, c, "*") == 1 for r in R for c in C), name="cell")
    m.addConstrs((x.sum(r, "*", v) == 1 for r in R for v in V), name="row")
    m.addConstrs((x.sum("*", c, v) == 1 for c in C for v in V), name="col")
    for b in range(1, N + 1):
        cells = block_cells(b)
        m.addConstrs((gp.quicksum(x[r, c, v] for (r, c) in cells) == 1
                      for v in V), name=f"block{b}")

    for (r, c, v) in clues:
        m.addConstr(x[r, c, v] == 1, name=f"clue_{r}_{c}")

    # no-good cuts, used only for the uniqueness test below
    for sol in forbid:
        m.addConstr(gp.quicksum(x[r, c, sol[r - 1][c - 1]]
                                for r in R for c in C) <= N * N - 1)
    return m, x


def solve(clues, forbid=()):
    m, x = build(clues, forbid)
    m.optimize()
    if m.Status == GRB.INFEASIBLE:
        return None
    assert m.Status == GRB.OPTIMAL, m.Status
    return [[next(v for v in V if x[r, c, v].X > 0.5) for c in C] for r in R]


def show(grid, given):
    line = "+-------+-------+-------+"
    print(line)
    for r in range(N):
        row = "|"
        for c in range(N):
            d = grid[r][c]
            mark = str(d) if given[r][c] else f"{d}"
            row += f" {mark}"
            if c % 3 == 2:
                row += " |"
        print(row)
        if r % 3 == 2:
            print(line)


def valid(grid):
    """Independent check, not using the solver."""
    ok = True
    full = set(range(1, N + 1))
    for r in range(N):
        ok &= set(grid[r]) == full
    for c in range(N):
        ok &= {grid[r][c] for r in range(N)} == full
    for b in range(1, N + 1):
        ok &= {grid[r - 1][c - 1] for (r, c) in block_cells(b)} == full
    return bool(ok)


if __name__ == "__main__":
    clues = [(r + 1, c + 1, PUZZLE[r][c])
             for r in range(N) for c in range(N) if PUZZLE[r][c]]
    given = [[bool(PUZZLE[r][c]) for c in range(N)] for r in range(N)]

    print(f"given clues: {len(clues)}")
    print("(17 is the proven minimum for a uniquely solvable Sudoku;")
    print(" McGuire, Tugemann and Civario, 2012)\n")
    print("the instance as given:")
    show([[PUZZLE[r][c] if PUZZLE[r][c] else 0 for c in range(N)]
          for r in range(N)], given)

    sol = solve(clues)
    assert sol is not None, "the given instance is infeasible"
    print("\nsolution:")
    show(sol, given)

    print(f"\nall rows, columns and blocks are permutations of 1..9: "
          f"{valid(sol)}")
    agree = all(PUZZLE[r][c] == 0 or PUZZLE[r][c] == sol[r][c]
                for r in range(N) for c in range(N))
    print(f"every given clue is preserved: {agree}")

    # uniqueness: forbid the solution just found and re-solve
    second = solve(clues, forbid=[sol])
    print(f"a second distinct solution exists: {second is not None}")
    print(f"the instance is uniquely solvable: {second is None}")

    m, _ = build(clues)
    m.update()
    print(f"\nmodel size: {m.NumVars} binary variables, "
          f"{m.NumConstrs} constraints")
