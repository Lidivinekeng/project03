"""
IE 5311 Homework, Problem 2 [40 pts]: shortest and longest s-t paths.

Ten random directed graphs, |V| = 20, arc weights c_ij ~ U[1,10],
each graph connected and containing at least one s-t path.

COMMON SETS AND PARAMETERS
    V           nodes, |V| = 20, with source s and terminal t
    A subset V x V   directed arcs
    out(i)      {j : (i,j) in A},  in(i) = {j : (j,i) in A}
    c_ij        weight of arc (i,j),  c_ij ~ U[1,10]
    b_i         +1 at s, -1 at t, 0 otherwise

DECISION VARIABLES (both problems)
    x_ij in {0,1}   1 if arc (i,j) is used

-- 1. SHORTEST PATH ---------------------------------------------------
    min   sum_{(i,j) in A} c_ij x_ij
    s.t.  sum_{j in out(i)} x_ij - sum_{j in in(i)} x_ji = b_i   for i in V
          x_ij in {0,1}

    The LP relaxation replaces the last line by 0 <= x_ij <= 1. The
    constraint matrix is the node-arc incidence matrix, which is totally
    unimodular, and the right-hand side is integral, so every vertex of
    the relaxed polytope is integral. I therefore expect the relaxation
    to return the same objective value on every instance, with no
    branching.

-- 2. LONGEST SIMPLE PATH ---------------------------------------------
    max   sum_{(i,j) in A} c_ij x_ij
    s.t.  sum_{j in out(i)} x_ij - sum_{j in in(i)} x_ji = b_i   for i in V
          sum_{j in out(i)} x_ij <= 1                            for i in V
          sum_{(i,j) in A(S)} x_ij <= |S| - 1
                          for all S subset V\\{s,t} with |S| >= 2
          x_ij in {0,1}

    The degree restriction enforces "each location at most once". The
    third family is subtour elimination and is NOT optional here. Under
    minimization with positive weights a stray cycle only adds cost, so
    it never appears in an optimum. Under MAXIMIZATION every cycle adds
    weight for free, so without that family the model is unbounded in
    structure: it returns an s-t path plus as many disjoint cycles as it
    can fit. The family has exponentially many members, so it is
    generated on demand, two ways:

      (b) constraint generation: solve the master to optimality, inspect
          the solution, add violated constraints, re-solve. Each round is
          a complete branch-and-bound run.
      (c) lazy constraints: one branch-and-bound run, with a callback
          that rejects any incumbent containing a cycle and adds the
          corresponding constraint from inside the search.
"""

import time

import gurobipy as gp
import networkx as nx
import numpy as np
from gurobipy import GRB

N_NODES = 20
N_INSTANCES = 10
SRC, SINK = 0, 19
W_LO, W_HI = 1.0, 10.0


# ----------------------------------------------------------------------
# Instance generation
# ----------------------------------------------------------------------
def make_graph(seed, p=0.18):
    """
    Directed G(n,p) that is weakly connected and has at least one s-t
    path. p is raised until both hold, so generation always terminates.
    """
    rng = np.random.default_rng(seed)
    while True:
        G = nx.gnp_random_graph(N_NODES, p, seed=int(rng.integers(1 << 30)),
                                directed=True)
        if nx.is_weakly_connected(G) and nx.has_path(G, SRC, SINK):
            for (i, j) in G.edges():
                G[i][j]["c"] = float(rng.uniform(W_LO, W_HI))
            return G
        p = min(0.9, p * 1.15)


def arcs_of(G):
    return list(G.edges())


def balance(i):
    return 1 if i == SRC else (-1 if i == SINK else 0)


def flow_constraints(m, x, G):
    for i in G.nodes():
        m.addConstr(
            gp.quicksum(x[i, j] for j in G.successors(i))
            - gp.quicksum(x[j, i] for j in G.predecessors(i)) == balance(i),
            name=f"bal_{i}")


# ----------------------------------------------------------------------
# 1. Shortest path, integer and relaxed
# ----------------------------------------------------------------------
def shortest_path(G, relax=False):
    m = gp.Model("sp")
    m.setParam("OutputFlag", 0)
    vt = GRB.CONTINUOUS if relax else GRB.BINARY
    x = m.addVars(arcs_of(G), lb=0.0, ub=1.0, vtype=vt, name="x")
    m.setObjective(gp.quicksum(G[i][j]["c"] * x[i, j] for (i, j) in G.edges()),
                   GRB.MINIMIZE)
    flow_constraints(m, x, G)
    t0 = time.perf_counter()
    m.optimize()
    dt = time.perf_counter() - t0
    assert m.Status == GRB.OPTIMAL
    vals = {a: x[a].X for a in arcs_of(G) if x[a].X > 1e-9}
    fractional = [v for v in vals.values() if 1e-6 < v < 1 - 1e-6]
    return m.ObjVal, dt, len(fractional), m.NodeCount if not relax else 0


# ----------------------------------------------------------------------
# 2. Longest simple path
# ----------------------------------------------------------------------
def cycles_in(selected):
    """Simple directed cycles among the chosen arcs."""
    H = nx.DiGraph()
    H.add_edges_from(selected)
    return [c for c in nx.simple_cycles(H)]


def longest_master(G, add_degree=True):
    m = gp.Model("lp_master")
    m.setParam("OutputFlag", 0)
    x = m.addVars(arcs_of(G), vtype=GRB.BINARY, name="x")
    m.setObjective(gp.quicksum(G[i][j]["c"] * x[i, j] for (i, j) in G.edges()),
                   GRB.MAXIMIZE)
    flow_constraints(m, x, G)
    if add_degree:
        for i in G.nodes():
            m.addConstr(gp.quicksum(x[i, j] for j in G.successors(i)) <= 1,
                        name=f"deg_{i}")
    return m, x


def cycle_cut(cycle, G):
    """Arcs with both endpoints in the cycle's node set."""
    Sset = set(cycle)
    return [(i, j) for (i, j) in G.edges() if i in Sset and j in Sset], len(Sset)


def longest_constraint_generation(G, max_rounds=3000):
    m, x = longest_master(G)
    rounds, cuts = 0, 0
    t0 = time.perf_counter()
    while rounds < max_rounds:
        m.optimize()
        rounds += 1
        if m.Status != GRB.OPTIMAL:
            return None, time.perf_counter() - t0, rounds, cuts
        chosen = [a for a in arcs_of(G) if x[a].X > 0.5]
        cyc = cycles_in(chosen)
        if not cyc:
            return m.ObjVal, time.perf_counter() - t0, rounds, cuts
        for cycle in cyc:
            inside, size = cycle_cut(cycle, G)
            m.addConstr(gp.quicksum(x[a] for a in inside) <= size - 1)
            cuts += 1
    raise RuntimeError("constraint generation hit the round limit")


def longest_lazy(G):
    m, x = longest_master(G)
    m.setParam("LazyConstraints", 1)
    m._x, m._G, m._cuts = x, G, 0

    def callback(model, where):
        if where != GRB.Callback.MIPSOL:
            return
        vals = model.cbGetSolution(model._x)
        chosen = [a for a in model._G.edges() if vals[a] > 0.5]
        for cycle in cycles_in(chosen):
            inside, size = cycle_cut(cycle, model._G)
            model.cbLazy(gp.quicksum(model._x[a] for a in inside) <= size - 1)
            model._cuts += 1

    t0 = time.perf_counter()
    m.optimize(callback)
    dt = time.perf_counter() - t0
    assert m.Status == GRB.OPTIMAL, m.Status
    return m.ObjVal, dt, m._cuts, m.NodeCount


def path_from(G, arcs_used):
    """Walk s to t, so the reported path can be checked independently."""
    nxt = {i: j for (i, j) in arcs_used}
    node, seq = SRC, [SRC]
    while node != SINK:
        if node not in nxt:
            return None
        node = nxt[node]
        if node in seq:
            return None
        seq.append(node)
    return seq


if __name__ == "__main__":
    graphs = [make_graph(1000 + k) for k in range(N_INSTANCES)]

    print("=" * 78)
    print("PART 1: SHORTEST PATH, BINARY MODEL vs LP RELAXATION")
    print("=" * 78)
    print(f"{'inst':>4} {'|V|':>4} {'|A|':>5} {'MIP obj':>10} {'LP obj':>10} "
          f"{'gap':>9} {'MIP s':>8} {'LP s':>8} {'frac':>5} {'B&B nodes':>9}")
    sp_rows = []
    for k, G in enumerate(graphs):
        mo, mt, _, nodes = shortest_path(G, relax=False)
        lo, lt, nfrac, _ = shortest_path(G, relax=True)
        sp_rows.append((k + 1, G.number_of_nodes(), G.number_of_edges(),
                        mo, lo, mo - lo, mt, lt, nfrac, nodes))
        print(f"{k+1:>4} {G.number_of_nodes():>4} {G.number_of_edges():>5} "
              f"{mo:>10.4f} {lo:>10.4f} {mo-lo:>9.2e} {mt:>8.4f} {lt:>8.4f} "
              f"{nfrac:>5} {nodes:>9.0f}")
    gaps = [r[5] for r in sp_rows]
    print(f"\nmax integrality gap over the 10 instances : {max(gaps):.3e}")
    print(f"instances with any fractional arc value   : "
          f"{sum(1 for r in sp_rows if r[8] > 0)} of {N_INSTANCES}")
    print(f"mean MIP time {np.mean([r[6] for r in sp_rows]):.4f} s, "
          f"mean LP time {np.mean([r[7] for r in sp_rows]):.4f} s, "
          f"ratio {np.mean([r[6] for r in sp_rows])/np.mean([r[7] for r in sp_rows]):.2f}x")

    print("\n" + "=" * 78)
    print("PART 2: LONGEST SIMPLE PATH, CONSTRAINT GENERATION vs LAZY")
    print("=" * 78)
    print(f"{'inst':>4} {'CG obj':>10} {'Lazy obj':>10} {'match':>6} "
          f"{'CG s':>8} {'Lazy s':>8} {'CG rnds':>8} {'CG cuts':>8} "
          f"{'Lazy cuts':>10}")
    lp_rows = []
    for k, G in enumerate(graphs):
        co, ct, rounds, ccuts = longest_constraint_generation(G)
        lo, lt, lcuts, nodes = longest_lazy(G)
        match = abs(co - lo) < 1e-6
        lp_rows.append((k + 1, co, lo, match, ct, lt, rounds, ccuts, lcuts))
        print(f"{k+1:>4} {co:>10.4f} {lo:>10.4f} {str(match):>6} "
              f"{ct:>8.4f} {lt:>8.4f} {rounds:>8} {ccuts:>8} {lcuts:>10}")
    print(f"\nboth methods agree on every instance : "
          f"{all(r[3] for r in lp_rows)}")
    print(f"mean CG time {np.mean([r[4] for r in lp_rows]):.4f} s, "
          f"mean lazy time {np.mean([r[5] for r in lp_rows]):.4f} s, "
          f"speedup {np.mean([r[4] for r in lp_rows])/np.mean([r[5] for r in lp_rows]):.2f}x")
    print(f"total master re-solves under CG : {sum(r[6] for r in lp_rows)}")

    print("\n" + "-" * 78)
    print("CHECK: is subtour elimination actually needed?")
    print("-" * 78)
    G = graphs[0]
    m, x = longest_master(G)
    m.optimize()
    chosen = [a for a in arcs_of(G) if x[a].X > 0.5]
    cyc = cycles_in(chosen)
    print(f"instance 1, master WITHOUT any subtour constraint:")
    print(f"  objective {m.ObjVal:.4f}, arcs selected {len(chosen)}")
    print(f"  cycles present in that solution : {len(cyc)} -> {cyc}")
    print(f"  so the unconstrained master overstates the true optimum "
          f"{lp_rows[0][1]:.4f} by {m.ObjVal - lp_rows[0][1]:.4f}")
