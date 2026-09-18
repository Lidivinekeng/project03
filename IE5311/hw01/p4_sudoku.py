import gurobipy as gp
from gurobipy import GRB

N = 9
BLK = 3
R = C = V = range(1, N + 1)

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


def show(grid):
    line = "+-------+-------+-------+"
    print(line)
    for r in range(N):
        row = "|"
        for c in range(N):
            row += f" {grid[r][c]}"
            if c % 3 == 2:
                row += " |"
        print(row)
        if r % 3 == 2:
            print(line)


if __name__ == "__main__":
    clues = [(r + 1, c + 1, PUZZLE[r][c])
             for r in range(N) for c in range(N) if PUZZLE[r][c]]

    print(f"given clues: {len(clues)}")
    print("(17 is the proven minimum for a uniquely solvable Sudoku;")
    print(" McGuire, Tugemann and Civario, 2012)\n")
    print("the instance as given:")
    show(PUZZLE)

    sol = solve(clues)
    assert sol is not None, "the given instance is infeasible"
    print("\nsolution:")
    show(sol)

    second = solve(clues, forbid=[sol])
    print(f"a second distinct solution exists: {second is not None}")
    print(f"the instance is uniquely solvable: {second is None}")

    m, _ = build(clues)
    m.update()
    print(f"\nmodel size: {m.NumVars} binary variables, "
          f"{m.NumConstrs} constraints")
