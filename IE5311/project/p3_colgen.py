"""Method II: column generation on the route-based master.

The RMP and the pricing subproblem are each solved by Gurobi; the
column generation loop itself is implemented here, as the project
requires. Pricing is an exact elementary capacitated shortest-path MIP
with DFJ subtour elimination added lazily.
"""
import time

import gurobipy as gp
from gurobipy import GRB

from cvrp_data import Instance
from route_enum import rebuild_sequence

EPS = 1e-7


def initial_routes(ins, K=4, Q=None):
    """Greedy first-fit-decreasing bin packing, then an exact TSP per bin."""
    Q = ins.Q if Q is None else Q
    bins = [[] for _ in range(K)]
    loads = [0] * K
    for c in sorted(ins.customers, key=lambda i: -ins.demand[i]):
        k = min((k for k in range(K) if loads[k] + ins.demand[c] <= Q),
                key=lambda k: loads[k], default=None)
        if k is None:
            raise RuntimeError("greedy packing failed")
        bins[k].append(c)
        loads[k] += ins.demand[c]
    out = []
    for b in bins:
        seq = rebuild_sequence(ins, tuple(sorted(b)), Q)
        out.append((tuple(sorted(b)), ins.cost(seq), sum(ins.demand[i]
                                                         for i in b)))
    return out


def solve_rmp(ins, cols, K):
    m = gp.Model()
    m.setParam("OutputFlag", 0)
    lam = m.addVars(len(cols), lb=0.0)
    m.setObjective(gp.quicksum(cols[r][1] * lam[r]
                               for r in range(len(cols))), GRB.MINIMIZE)
    cov = {}
    for c in ins.customers:
        cov[c] = m.addConstr(
            gp.quicksum(lam[r] for r in range(len(cols))
                        if c in cols[r][0]) == 1)
    fleet = m.addConstr(gp.quicksum(lam[r] for r in range(len(cols))) == K)
    m.optimize()
    if m.Status != GRB.OPTIMAL:
        return None, None, None, None
    pi = {c: cov[c].Pi for c in ins.customers}
    return m.ObjVal, pi, fleet.Pi, [lam[r].X for r in range(len(cols))]


def price(ins, pi, sigma, Q=None, pool=1):
    """Exact ESPPRC as a MIP: least reduced-cost feasible route."""
    Q = ins.Q if Q is None else Q
    N, C, dep = ins.nodes, ins.customers, ins.depot
    m = gp.Model()
    m.setParam("OutputFlag", 0)
    m.setParam("LazyConstraints", 1)
    if pool > 1:
        m.setParam("PoolSearchMode", 2)
        m.setParam("PoolSolutions", pool)
    x = m.addVars([(i, j) for i in N for j in N if i != j],
                  vtype=GRB.BINARY)
    vis = {h: gp.quicksum(x[i, h] for i in N if i != h) for h in C}
    m.addConstr(gp.quicksum(x[dep, j] for j in C) == 1)
    m.addConstr(gp.quicksum(x[i, dep] for i in C) == 1)
    for h in C:
        m.addConstr(vis[h] == gp.quicksum(x[h, j] for j in N if j != h))
        m.addConstr(vis[h] <= 1)
    m.addConstr(gp.quicksum(ins.demand[h] * vis[h] for h in C) <= Q)
    m.setObjective(
        gp.quicksum(ins.c[i, j] * x[i, j] for (i, j) in x)
        - gp.quicksum(pi[h] * vis[h] for h in C), GRB.MINIMIZE)
    m._x, m._N, m._dep = x, N, dep

    def cb(mod, where):
        if where != GRB.Callback.MIPSOL:
            return
        val = mod.cbGetSolution(mod._x)
        used = [(i, j) for (i, j) in mod._x if val[i, j] > 0.5]
        adj = {}
        for (i, j) in used:
            adj.setdefault(i, set()).add(j)
            adj.setdefault(j, set()).add(i)
        seen = set()
        for s in adj:
            if s in seen:
                continue
            stack, comp = [s], set()
            while stack:
                v = stack.pop()
                if v in comp:
                    continue
                comp.add(v)
                stack.extend(adj[v] - comp)
            seen |= comp
            if mod._dep not in comp and len(comp) >= 2:
                mod.cbLazy(gp.quicksum(
                    mod._x[i, j] for i in comp for j in comp if i != j)
                    <= len(comp) - 1)
    m.optimize(cb)
    if m.SolCount == 0:
        return []
    out = []
    for s in range(min(pool, m.SolCount)):
        m.setParam("SolutionNumber", s)
        xv = {k: v for k, v in zip(x.keys(), m.getAttr("Xn", x).values())}
        mem = tuple(sorted(h for h in C
                           if sum(xv[i, h] for i in N if i != h) > 0.5))
        if not mem:
            continue
        cost = sum(ins.c[i, j] for (i, j) in xv if xv[i, j] > 0.5)
        rc = cost - sum(pi[h] for h in mem) - sigma
        out.append((mem, cost, sum(ins.demand[h] for h in mem), rc))
    return out


def column_generation(ins, K=4, Q=None, pool=4, max_iter=200,
                      verbose=True, harvest=0):
    """Run column generation. `harvest` > 0 asks the pricer for that many
    additional solutions at the final duals; those extra routes change
    nothing about the certified LP value but enrich the pool the
    integer restricted master of Problem 3(e) may choose from."""
    Q = ins.Q if Q is None else Q
    cols = initial_routes(ins, K, Q)
    seen = {c[0] for c in cols}
    log = []
    t0 = time.perf_counter()
    for it in range(1, max_iter + 1):
        z, pi, sigma, lam = solve_rmp(ins, cols, K)
        found = price(ins, pi, sigma, Q, pool)
        best_rc = min((r[3] for r in found), default=0.0)
        added = 0
        for mem, cost, ld, rc in found:
            if rc < -EPS and mem not in seen:
                cols.append((mem, cost, ld))
                seen.add(mem)
                added += 1
        log.append((it, z, best_rc, added, len(cols)))
        if verbose:
            print(f"{it:>5} {z:>13.6f} {best_rc:>14.6f} {added:>7} "
                  f"{len(cols):>8}")
        if added == 0:
            break
    dt = time.perf_counter() - t0
    z, pi, sigma, lam = solve_rmp(ins, cols, K)
    n_cg = len(cols)
    t1 = time.perf_counter()
    if harvest:
        for mem, cost, ld, rc in price(ins, pi, sigma, Q, harvest):
            if mem not in seen:
                cols.append((mem, cost, ld))
                seen.add(mem)
    t_harvest = time.perf_counter() - t1
    return dict(z=z, pi=pi, sigma=sigma, lam=lam, cols=cols, log=log,
                time=dt, iters=len(log), min_rc=best_rc, n_cg=n_cg,
                t_harvest=t_harvest)


if __name__ == "__main__":
    ins = Instance()
    print("=" * 74)
    print("PROBLEM 3, METHOD II: column generation on the master LP")
    print("=" * 74)
    init = initial_routes(ins)
    print("initial RMP from first-fit-decreasing packing + exact TSP:")
    for mem, cost, ld in init:
        print(f"   load {ld:>5} cost {cost:>4}  {mem}")
    print(f"   initial cost {sum(c for _, c, _ in init)}")
    print(f"\n{'iter':>5} {'RMP obj':>13} {'min red cost':>14} "
          f"{'added':>7} {'columns':>8}")
    res = column_generation(ins)
    print(f"\ncolumn generation iterations : {res['iters']}")
    print(f"routes generated             : {len(res['cols'])} "
          f"({len(res['cols']) - 4} beyond the 4 initial)")
    print(f"final LP objective           : {res['z']:.6f}")
    print(f"min reduced cost at the end  : {res['min_rc']:.6e}")
    print(f"total solution time          : {res['time']:.2f} s")
