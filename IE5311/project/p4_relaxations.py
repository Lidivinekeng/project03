"""Problem 4: LP relaxation of the original MIP against the DW bound.

z_LP^orig is the LP relaxation of the vehicle-indexed formulation of
Problem 2(a), which includes the subtour constraints. Those are
exponential, so they are separated: for each vehicle k and each
customer l, the least cut separating l from the depot under capacities
x_ijk must be at least the visit variable y_lk, and any violated cut
is added and the LP re-solved.
"""
import time

import gurobipy as gp
import networkx as nx
from gurobipy import GRB

from cvrp_data import Instance

TOL = 1e-6


def lp_original(ins, K=4, Q=None, with_sec=True, max_rounds=200):
    Q = ins.Q if Q is None else Q
    N, C, dep = ins.nodes, ins.customers, ins.depot
    m = gp.Model()
    m.setParam("OutputFlag", 0)
    x = m.addVars([(i, j, k) for i in N for j in N if i != j
                   for k in range(K)], lb=0.0, ub=1.0)
    vis = {(h, k): gp.quicksum(x[i, h, k] for i in N if i != h)
           for h in C for k in range(K)}
    m.setObjective(gp.quicksum(ins.c[i, j] * x[i, j, k]
                               for (i, j, k) in x), GRB.MINIMIZE)
    for j in C:
        m.addConstr(gp.quicksum(vis[j, k] for k in range(K)) == 1)
    for k in range(K):
        for h in N:
            m.addConstr(gp.quicksum(x[i, h, k] for i in N if i != h)
                        == gp.quicksum(x[h, j, k] for j in N if j != h))
        m.addConstr(gp.quicksum(x[dep, j, k] for j in C) == 1)
        m.addConstr(gp.quicksum(ins.demand[h] * vis[h, k] for h in C) <= Q)

    rounds, cuts = 0, 0
    while True:
        m.optimize()
        if m.Status != GRB.OPTIMAL:
            return None, rounds, cuts
        if not with_sec:
            return m.ObjVal, rounds, cuts
        rounds += 1
        xv = m.getAttr("X", x)
        added = 0
        for k in range(K):
            G = nx.DiGraph()
            for i in N:
                for j in N:
                    if i != j and xv[i, j, k] > TOL:
                        G.add_edge(i, j, capacity=xv[i, j, k])
            if dep not in G:
                continue
            for l in C:
                if l not in G:
                    continue
                yl = sum(xv[i, l, k] for i in N if i != l)
                if yl <= TOL:
                    continue
                cut, (_, Sbar) = nx.minimum_cut(G, dep, l)
                if cut < yl - 1e-6:
                    S = [v for v in Sbar if v != dep]
                    if len(S) >= 2 and l in S:
                        m.addConstr(
                            gp.quicksum(x[i, j, k] for i in S for j in N
                                        if j not in S and i != j)
                            >= vis[l, k])
                        added += 1
                        cuts += 1
        if added == 0 or rounds >= max_rounds:
            return m.ObjVal, rounds, cuts


if __name__ == "__main__":
    ins = Instance()
    print("=" * 74)
    print("PROBLEM 4: LP relaxation strength")
    print("=" * 74)
    t0 = time.perf_counter()
    z_nosec, _, _ = lp_original(ins, with_sec=False)
    t_nosec = time.perf_counter() - t0
    print(f"LP of the original MIP, subtour constraints dropped : "
          f"{z_nosec:.6f}   ({t_nosec:.2f} s)")
    t0 = time.perf_counter()
    z_orig, rounds, cuts = lp_original(ins, with_sec=True)
    t_sec = time.perf_counter() - t0
    print(f"LP of the original MIP, subtour constraints separated:"
          f" {z_orig:.6f}   ({t_sec:.2f} s)")
    print(f"   separation rounds {rounds}, cuts added {cuts}")
    print(f"   the subtour constraints are worth "
          f"{z_orig - z_nosec:.6f} of bound")
    print(f"\nz_LP^orig = {z_orig:.6f}")
    print(f"z_LP^DW   = 373.875000   (certified by column generation)")
    print(f"integer optimum z* = 375")
    print(f"\n   z_LP^orig <= z_LP^DW <= z* : "
          f"{z_orig <= 373.875 + 1e-6 <= 375 + 1e-6}")
    print(f"   DW closes {(373.875 - z_orig) / (375 - z_orig):.1%} of the "
          f"gap the original LP leaves")
