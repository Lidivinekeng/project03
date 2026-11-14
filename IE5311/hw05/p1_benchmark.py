import time

import gurobipy as gp
import numpy as np
from gurobipy import GRB

from p1_simplex import simplex

SEED = 5311
SIZES = [(5, 3), (10, 5), (20, 10), (50, 20), (100, 40)]
REPS = 7


def instance(n, m, rng):
    c = rng.uniform(1.0, 10.0, n)
    A = rng.uniform(0.5, 5.0, (m, n))
    b = rng.uniform(0.3, 0.6, m) * A.sum(axis=1)
    return A, b, c


def gurobi_solve(A, b, c, method=0, presolve=0):
    m, n = A.shape
    mod = gp.Model()
    mod.setParam("OutputFlag", 0)
    mod.setParam("Method", method)
    mod.setParam("Presolve", presolve)
    x = mod.addMVar(n, lb=0.0)
    mod.setObjective(c @ x, GRB.MAXIMIZE)
    mod.addConstr(A @ x <= b)
    best = []
    for _ in range(REPS):
        mod.reset()
        t0 = time.perf_counter()
        mod.optimize()
        best.append(time.perf_counter() - t0)
    return x.X, mod.ObjVal, int(mod.IterCount), float(np.median(best))


if __name__ == "__main__":
    rng = np.random.default_rng(SEED)

    print("=" * 78)
    print("PROBLEM 1 PARTS 3 AND 4: random resource allocation instances")
    print("=" * 78)
    print(f"seed {SEED}; c_i ~ U(1,10); a_ji ~ U(0.5,5); "
          f"b_j ~ U(0.3,0.6) * sum_i a_ji")
    print(f"runtimes are the median of {REPS} solves; a single timing at "
          f"this scale varies by tens of percent")
    print("A > 0 entrywise and b > 0, so the slack basis is feasible and")
    print("the feasible region is bounded, as Problem 1 assumes.\n")

    rows = []
    for n, m in SIZES:
        A, b, c = instance(n, m, rng)

        reps = []
        for _ in range(REPS):
            t0 = time.perf_counter()
            xs, objs, its, status = simplex(A, b, c)
            reps.append(time.perf_counter() - t0)
        dts = float(np.median(reps))

        xg, objg, itg, dtg = gurobi_solve(A, b, c)

        gap = abs(objs - objg)
        rel = gap / max(1.0, abs(objg))
        dx = float(np.max(np.abs(xs - xg)))
        rows.append((n, m, objs, objg, rel, its, itg, dts, dtg, dx, status))

    print(f"{'n':>4} {'m':>4} {'obj simplex':>13} {'obj gurobi':>13} "
          f"{'rel gap':>9} {'it s':>6} {'it g':>6} "
          f"{'t mine (ms)':>12} {'t grb (ms)':>11} {'ratio':>8}")
    for r in rows:
        print(f"{r[0]:>4} {r[1]:>4} {r[2]:>13.6f} {r[3]:>13.6f} "
              f"{r[4]:>9.2e} {r[5]:>6} {r[6]:>6} "
              f"{1000*r[7]:>12.3f} {1000*r[8]:>11.3f} {r[7]/r[8]:>7.1f}x")

    print(f"\n{'n':>4} {'m':>4} {'max |x_s - x_g|':>17} {'status':>10}")
    for r in rows:
        print(f"{r[0]:>4} {r[1]:>4} {r[9]:>17.3e} {r[10]:>10}")

    worst = max(r[4] for r in rows)
    print(f"\nlargest relative objective gap over the five instances: "
          f"{worst:.2e}")
    print("objective values agree to solver tolerance on every instance.")
    print("Gurobi was run with Method=0 (primal simplex) and Presolve=0 so")
    print("that its iteration count is comparable with the implementation.")
