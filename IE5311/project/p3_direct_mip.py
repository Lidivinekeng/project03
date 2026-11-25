import time
from itertools import combinations

import gurobipy as gp
from gurobipy import GRB

from cvrp_data import Instance


def components(arcs, depot):
    """Connected components of the undirected graph induced by arcs."""
    adj = {}
    for (i, j) in arcs:
        adj.setdefault(i, set()).add(j)
        adj.setdefault(j, set()).add(i)
    seen, out = set(), []
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
        out.append(comp)
    return [c for c in out if depot not in c]


def solve(ins, K=4, Q=None, limit=3600, verbose=False, seed=0):
    Q = ins.Q if Q is None else Q
    N, C, dep = ins.nodes, ins.customers, ins.depot
    m = gp.Model("cvrp_direct")
    m.setParam("OutputFlag", 1 if verbose else 0)
    m.setParam("TimeLimit", limit)
    m.setParam("Seed", seed)
    m.setParam("LazyConstraints", 1)

    x = m.addVars([(i, j, k) for i in N for j in N if i != j
                   for k in range(K)], vtype=GRB.BINARY, name="x")
    m.setObjective(gp.quicksum(ins.c[i, j] * x[i, j, k]
                               for (i, j, k) in x), GRB.MINIMIZE)
    # every customer entered exactly once, by exactly one vehicle
    for j in C:
        m.addConstr(gp.quicksum(x[i, j, k] for i in N if i != j
                                for k in range(K)) == 1, f"visit[{j}]")
    # flow conservation for every vehicle at every node
    for k in range(K):
        for h in N:
            m.addConstr(gp.quicksum(x[i, h, k] for i in N if i != h)
                        == gp.quicksum(x[h, j, k] for j in N if j != h),
                        f"flow[{h},{k}]")
        # each vehicle leaves the depot exactly once: K nonempty routes
        m.addConstr(gp.quicksum(x[dep, j, k] for j in C) == 1, f"depart[{k}]")
        # capacity
        m.addConstr(gp.quicksum(ins.demand[j] * x[i, j, k]
                                for j in C for i in N if i != j) <= Q,
                    f"cap[{k}]")
    # symmetry breaking: lowest-index customer of vehicle k increases with k
    srt = sorted(C)
    for k in range(1, K):
        for idx, j in enumerate(srt):
            m.addConstr(
                gp.quicksum(x[i, j, k] for i in N if i != j)
                <= gp.quicksum(x[i, jj, k - 1] for jj in srt[:idx]
                               for i in N if i != jj),
                f"sym[{j},{k}]")

    m._x, m._K, m._N, m._dep = x, K, N, dep
    m._cuts = 0

    def cb(mod, where):
        if where != GRB.Callback.MIPSOL:
            return
        val = mod.cbGetSolution(mod._x)
        for k in range(mod._K):
            arcs = [(i, j) for i in mod._N for j in mod._N
                    if i != j and val[i, j, k] > 0.5]
            for S in components(arcs, mod._dep):
                if len(S) >= 2:
                    mod.cbLazy(gp.quicksum(
                        mod._x[i, j, k] for i in S for j in S if i != j)
                        <= len(S) - 1)
                    mod._cuts += 1

    t0 = time.perf_counter()
    m.optimize(cb)
    dt = time.perf_counter() - t0

    routes = []
    if m.SolCount > 0:
        xv = m.getAttr("X", x)
        for k in range(K):
            succ = {i: j for i in N for j in N
                    if i != j and xv[i, j, k] > 0.5}
            r, cur = [dep], dep
            while True:
                cur = succ[cur]
                r.append(cur)
                if cur == dep:
                    break
            routes.append(r)
    return m, routes, dt


if __name__ == "__main__":
    ins = Instance()
    print("=" * 74)
    print("PROBLEM 3, METHOD I: direct vehicle-indexed MIP, DFJ lazy cuts")
    print("=" * 74)
    m, routes, dt = solve(ins, K=4, limit=3600)
    st = {GRB.OPTIMAL: "OPTIMAL", GRB.TIME_LIMIT: "TIME_LIMIT"}.get(
        m.Status, str(m.Status))
    print(f"variables {m.NumVars}, constraints {m.NumConstrs}, "
          f"lazy cuts added {m._cuts}")
    print(f"status      : {st}")
    print(f"objective   : {m.ObjVal:.0f}")
    print(f"best bound  : {m.ObjBound:.4f}")
    print(f"MIP gap     : {m.MIPGap:.6%}")
    print(f"solve time  : {dt:.2f} s")
    print(f"B&B nodes   : {m.NodeCount:.0f}")

    print(f"\n{'veh':>4} {'load':>7} {'cost':>6}  route")
    tot = 0
    for k, r in enumerate(routes, 1):
        tot += ins.cost(r)
        print(f"{k:>4} {ins.load(r):>7} {ins.cost(r):>6}  "
              f"{' -> '.join(map(str, r))}")
    served = sorted(i for r in routes for i in r if i != ins.depot)
    print(f"\ntotal cost from routes  : {tot}")
    print(f"customers served        : {len(served)} "
          f"(all once: {served == sorted(ins.customers)})")
    print(f"every load <= Q = {ins.Q}  : "
          f"{all(ins.load(r) <= ins.Q for r in routes)}")
    print(f"number of routes        : {len(routes)}")
