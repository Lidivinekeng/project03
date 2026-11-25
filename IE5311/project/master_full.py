"""Full route-based master over every feasible route, solved with HiGHS.

This is the reference the column generation of Method II is checked
against: because every feasible column is present, its LP value is
z_LP^DW exactly and its integer value is the true set-partitioning
optimum. Gurobi's restricted licence caps at 2000 variables, so this
uses scipy/HiGHS instead.
"""
import time

import numpy as np
from scipy.optimize import linprog, milp, LinearConstraint, Bounds
from scipy.sparse import csc_matrix

from cvrp_data import Instance
from route_enum import enumerate_routes


def build(ins, routes, K=4):
    cust = ins.customers
    idx = {c: r for r, c in enumerate(cust)}
    m, nR = len(cust), len(routes)
    rows, cols = [], []
    for j, (mem, _, _) in enumerate(routes):
        for c in mem:
            rows.append(idx[c])
            cols.append(j)
    rows += [m] * nR
    cols += list(range(nR))
    data = np.ones(len(rows))
    A = csc_matrix((data, (rows, cols)), shape=(m + 1, nR))
    b = np.ones(m + 1)
    b[m] = K
    cvec = np.array([r[1] for r in routes], dtype=float)
    return A, b, cvec


def solve_lp(A, b, c):
    t0 = time.perf_counter()
    r = linprog(c, A_eq=A, b_eq=b, bounds=(0, None), method="highs")
    return r, time.perf_counter() - t0


def solve_ip(A, b, c):
    t0 = time.perf_counter()
    r = milp(c, constraints=LinearConstraint(A, b, b),
             integrality=np.ones(len(c)), bounds=Bounds(0, 1))
    return r, time.perf_counter() - t0


if __name__ == "__main__":
    ins = Instance()
    print("=" * 74)
    print("Full route-based master (all feasible columns), HiGHS")
    print("=" * 74)
    for Q, K in [(ins.Q, 4), (7500, 4)]:
        R = enumerate_routes(ins, Q)
        A, b, c = build(ins, R, K)
        lp, tl = solve_lp(A, b, c)
        ip, ti = solve_ip(A, b, c)
        print(f"\nQ = {Q}, K = {K}:  {len(R)} columns, {A.shape[0]} rows")
        print(f"   LP relaxation z_LP^DW = {lp.fun:.6f}   ({tl:.2f} s)")
        print(f"   integer optimum       = {ip.fun:.0f}   ({ti:.2f} s)")
        print(f"   integrality gap       = {ip.fun - lp.fun:.6f}")
        sel = [R[j] for j in range(len(R)) if ip.x[j] > 0.5]
        print(f"   routes chosen         = {len(sel)}")
        tot = 0
        for mem, cost, ld in sorted(sel, key=lambda r: -r[2]):
            tot += cost
            print(f"      load {ld:>5}  cost {cost:>4}  {mem}")
        allc = sorted(i for mem, _, _ in sel for i in mem)
        print(f"   cost check {tot}, customers {len(allc)} "
              f"all once={allc == sorted(ins.customers)}, "
              f"loads<=Q={all(l <= Q for _, _, l in sel)}")
