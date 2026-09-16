"""
IE 5311-001 Principles of Optimization, Fall 2026, Ningji Wei.
Part 1: Problems 1 to 4, plus the total unimodularity exploration.

Every model is written in general indexed form per the course
convention. Data lives in tables; the model functions mention no
specific node, food, city or facility. Solver is PuLP with CBC, which
needs no license.
"""

import itertools
import math

import numpy as np
import pulp

TOL = 1e-6
SOLVER = pulp.PULP_CBC_CMD(msg=0)


def rule(title):
    print("\n" + "=" * 66)
    print(title)
    print("=" * 66)


# ======================================================================
# PROBLEM 2: SHORTEST PATH  (slides 20 to 27)
#
#   Sets        V nodes, A arcs (i,j)
#   Parameters  c_ij arc cost, s source, t sink
#   Variables   x_ij in {0,1}, 1 if arc (i,j) is traversed
#
#   min  sum_{(i,j) in A} c_ij x_ij
#   s.t. sum_{j in out(i)} x_ij - sum_{j in in(i)} x_ji = b_i  for i in V
#        with b_s = 1, b_t = -1, b_i = 0 otherwise
#        x_ij in {0,1}
# ======================================================================
SP_ARCS = {
    ("s", "a"): 4.0, ("s", "b"): 2.0,
    ("a", "b"): 5.0, ("a", "c"): 10.0,
    ("b", "d"): 3.0,
    ("d", "a"): 4.0, ("d", "c"): 11.0,
    ("c", "t"): 4.0,
    ("d", "t"): 9.0,
}
SP_NODES = sorted({n for arc in SP_ARCS for n in arc})


def shortest_path(nodes, arcs, source, sink, relax=False):
    """Arc-based formulation. relax=True drops integrality."""
    cat = pulp.LpContinuous if relax else pulp.LpBinary
    m = pulp.LpProblem("shortest_path", pulp.LpMinimize)
    x = {a: pulp.LpVariable(f"x_{a[0]}_{a[1]}", lowBound=0, upBound=1, cat=cat)
         for a in arcs}

    m += pulp.lpSum(arcs[a] * x[a] for a in arcs), "total_cost"

    for i in nodes:
        b = 1 if i == source else (-1 if i == sink else 0)
        out = pulp.lpSum(x[a] for a in arcs if a[0] == i)
        inn = pulp.lpSum(x[a] for a in arcs if a[1] == i)
        m += out - inn == b, f"balance_{i}"

    m.solve(SOLVER)
    assert pulp.LpStatus[m.status] == "Optimal", pulp.LpStatus[m.status]
    used = [a for a in arcs if x[a].value() > 0.5]
    values = {a: x[a].value() for a in arcs if x[a].value() > TOL}
    return pulp.value(m.objective), used, values


def incidence_matrix(nodes, arcs):
    """Node-arc incidence matrix: +1 at the tail, -1 at the head."""
    A = np.zeros((len(nodes), len(arcs)))
    idx = {n: k for k, n in enumerate(nodes)}
    for col, (i, j) in enumerate(arcs):
        A[idx[i], col] = 1.0
        A[idx[j], col] = -1.0
    return A


def is_totally_unimodular(A, max_order=4):
    """
    Exhaustive check on every square submatrix up to max_order.
    A matrix is totally unimodular when every square submatrix has
    determinant in {0, +1, -1}.
    """
    rows, cols = A.shape
    bad = []
    checked = 0
    for k in range(1, min(max_order, rows, cols) + 1):
        for rs in itertools.combinations(range(rows), k):
            for cs in itertools.combinations(range(cols), k):
                d = np.linalg.det(A[np.ix_(rs, cs)])
                checked += 1
                if min(abs(d), abs(d - 1), abs(d + 1)) > 1e-7:
                    bad.append((rs, cs, d))
    return len(bad) == 0, checked, bad


# ======================================================================
# PROBLEM 3: TRAVELLING SALESMAN, DFJ  (slides 28 to 34)
#
#   Sets        V cities, E = {{i,j} : i < j} edges
#   Parameters  c_ij distance
#   Variables   x_ij in {0,1}, 1 if edge {i,j} is on the tour
#
#   min  sum_{{i,j} in E} c_ij x_ij
#   s.t. sum_{j != i} x_ij = 2                       for all i in V
#        sum_{{i,j} subset S} x_ij <= |S| - 1        for all S, 2<=|S|<=n-1
#        x_ij in {0,1}
#
#   The second family has 2^n - O(n) members, so it is generated on
#   demand: master problem, then a separation subproblem (slides 33-34).
# ======================================================================
TSP_COORDS = {
    1: (0.0, 0.0), 2: (4.0, 1.0), 3: (5.0, 4.0),
    4: (2.0, 5.0), 5: (-1.0, 3.0), 6: (1.0, 2.0),
}


def euclidean(coords):
    return {(i, j): math.dist(coords[i], coords[j])
            for i in coords for j in coords if i < j}


def components(cities, chosen):
    """Connected components of the selected-edge graph."""
    adj = {i: set() for i in cities}
    for (i, j) in chosen:
        adj[i].add(j)
        adj[j].add(i)
    seen, comps = set(), []
    for start in cities:
        if start in seen:
            continue
        stack, comp = [start], set()
        while stack:
            v = stack.pop()
            if v in comp:
                continue
            comp.add(v)
            stack.extend(adj[v] - comp)
        seen |= comp
        comps.append(comp)
    return comps


def tsp_dfj(cities, dist, verbose=True):
    """Master problem plus subtour separation. Returns tour and rounds."""
    m = pulp.LpProblem("tsp_dfj", pulp.LpMinimize)
    x = {(i, j): pulp.LpVariable(f"x_{i}_{j}", cat=pulp.LpBinary)
         for (i, j) in dist}

    def var(i, j):
        return x[(i, j)] if i < j else x[(j, i)]

    m += pulp.lpSum(dist[e] * x[e] for e in dist), "tour_length"

    # degree: every city touched by exactly two tour edges
    for i in cities:
        m += pulp.lpSum(var(i, j) for j in cities if j != i) == 2, f"degree_{i}"

    rounds, cuts = 0, 0
    while True:
        m.solve(SOLVER)
        assert pulp.LpStatus[m.status] == "Optimal"
        rounds += 1
        chosen = [e for e in dist if x[e].value() > 0.5]
        comps = components(cities, chosen)
        if verbose:
            print(f"  round {rounds}: length {pulp.value(m.objective):7.4f}, "
                  f"{len(comps)} component(s) {[sorted(c) for c in comps]}")
        if len(comps) == 1:
            return pulp.value(m.objective), chosen, rounds, cuts
        # separation subproblem: each component gives a violated constraint
        for S in comps:
            inside = [(i, j) for (i, j) in dist if i in S and j in S]
            m += pulp.lpSum(x[e] for e in inside) <= len(S) - 1, \
                 f"subtour_{cuts}"
            cuts += 1


def tsp_lp_relaxation(cities, dist):
    """Degree constraints only, integrality dropped. Gives the DFJ bound."""
    m = pulp.LpProblem("tsp_lp", pulp.LpMinimize)
    x = {e: pulp.LpVariable(f"y_{e[0]}_{e[1]}", lowBound=0, upBound=1)
         for e in dist}

    def var(i, j):
        return x[(i, j)] if i < j else x[(j, i)]

    m += pulp.lpSum(dist[e] * x[e] for e in dist)
    for i in cities:
        m += pulp.lpSum(var(i, j) for j in cities if j != i) == 2
    m.solve(SOLVER)
    frac = {e: x[e].value() for e in dist
            if TOL < x[e].value() < 1 - TOL}
    return pulp.value(m.objective), frac


# ======================================================================
# PROBLEM 4: FACILITY LOCATION  (slides 36 to 38)
#
#   Sets        F facilities (i), C customers (j)
#   Parameters  f_i opening cost, c_ij cost of serving j from i
#   Variables   y_i in {0,1} open facility i
#               x_ij >= 0 fraction of customer j served by facility i
#
#   min  sum_i f_i y_i + sum_i sum_j c_ij x_ij
#   s.t. sum_i x_ij = 1            for all j in C
#        x_ij <= y_i               for all i in F, j in C
#        x_ij >= 0, y_i in {0,1}
# ======================================================================
FL_OPEN = {"F1": 14.0, "F2": 13.0, "F3": 8.0, "F4": 17.0}
FL_SERVE = {
    ("F1", "C1"): 12.0, ("F1", "C2"): 3.0, ("F1", "C3"): 4.0,
    ("F1", "C4"): 6.0, ("F1", "C5"): 9.0,
    ("F2", "C1"): 4.0, ("F2", "C2"): 11.0, ("F2", "C3"): 9.0,
    ("F2", "C4"): 7.0, ("F2", "C5"): 2.0,
    ("F3", "C1"): 6.0, ("F3", "C2"): 10.0, ("F3", "C3"): 12.0,
    ("F3", "C4"): 3.0, ("F3", "C5"): 8.0,
    ("F4", "C1"): 12.0, ("F4", "C2"): 2.0, ("F4", "C3"): 9.0,
    ("F4", "C4"): 3.0, ("F4", "C5"): 8.0,
}


def facility_location(facilities, customers, open_cost, serve_cost,
                      strong=True):
    """strong=True uses x_ij <= y_i; strong=False uses the aggregated cut."""
    m = pulp.LpProblem("facility_location", pulp.LpMinimize)
    y = {i: pulp.LpVariable(f"y_{i}", cat=pulp.LpBinary) for i in facilities}
    x = {(i, j): pulp.LpVariable(f"x_{i}_{j}", lowBound=0, upBound=1)
         for i in facilities for j in customers}

    m += (pulp.lpSum(open_cost[i] * y[i] for i in facilities)
          + pulp.lpSum(serve_cost[i, j] * x[i, j]
                       for i in facilities for j in customers))

    for j in customers:
        m += pulp.lpSum(x[i, j] for i in facilities) == 1, f"demand_{j}"

    if strong:
        for i in facilities:
            for j in customers:
                m += x[i, j] <= y[i], f"link_{i}_{j}"
    else:
        for i in facilities:
            m += pulp.lpSum(x[i, j] for j in customers) <= len(customers) * y[i]

    m.solve(SOLVER)
    assert pulp.LpStatus[m.status] == "Optimal"
    opened = [i for i in facilities if y[i].value() > 0.5]
    assign = {j: i for i in facilities for j in customers
              if x[i, j].value() > 0.5}
    return pulp.value(m.objective), opened, assign, m, y, x


def facility_location_lp_bound(facilities, customers, open_cost, serve_cost,
                               strong=True):
    """Same model with integrality dropped, to compare relaxation strength."""
    m = pulp.LpProblem("fl_lp", pulp.LpMinimize)
    y = {i: pulp.LpVariable(f"y_{i}", lowBound=0, upBound=1) for i in facilities}
    x = {(i, j): pulp.LpVariable(f"x_{i}_{j}", lowBound=0, upBound=1)
         for i in facilities for j in customers}
    m += (pulp.lpSum(open_cost[i] * y[i] for i in facilities)
          + pulp.lpSum(serve_cost[i, j] * x[i, j]
                       for i in facilities for j in customers))
    for j in customers:
        m += pulp.lpSum(x[i, j] for i in facilities) == 1
    if strong:
        for i in facilities:
            for j in customers:
                m += x[i, j] <= y[i]
    else:
        for i in facilities:
            m += pulp.lpSum(x[i, j] for j in customers) <= len(customers) * y[i]
    m.solve(SOLVER)
    return pulp.value(m.objective)


def facility_two_player(facilities, customers, open_cost, serve_cost):
    """
    Two-player reading (slide 38). The leader chooses which facilities to
    open. Each customer then picks the cheapest open facility on its own.
    Enumerating every leader choice evaluates the follower exactly, so
    this brute force is the ground truth for the single-level MIP.

    Returns the optimal value and EVERY leader choice attaining it.
    Ties are common here, so reporting one arbitrary winner would hide
    the fact that the MIP may legitimately return a different set.
    """
    results = []
    for k in range(1, len(facilities) + 1):
        for S in itertools.combinations(facilities, k):
            total = sum(open_cost[i] for i in S)
            pick = {}
            for j in customers:
                i_star = min(S, key=lambda i: serve_cost[i, j])
                pick[j] = i_star
                total += serve_cost[i_star, j]
            results.append((total, list(S), pick))
    best_val = min(r[0] for r in results)
    optima = [(S, pick) for val, S, pick in results
              if abs(val - best_val) < 1e-9]
    return best_val, optima


# ======================================================================
if __name__ == "__main__":
    # ---------------- Problem 2 ----------------
    rule("PROBLEM 2: SHORTEST PATH (slides 20-27)")
    cost_ip, path_ip, _ = shortest_path(SP_NODES, SP_ARCS, "s", "t")
    print(f"integer program : cost {cost_ip:.1f}, arcs {sorted(path_ip)}")

    cost_lp, path_lp, vals_lp = shortest_path(SP_NODES, SP_ARCS, "s", "t",
                                              relax=True)
    integral = all(min(abs(v), abs(v - 1)) < TOL for v in vals_lp.values())
    print(f"LP relaxation   : cost {cost_lp:.1f}, arcs {sorted(path_lp)}")
    print(f"LP solution is integral without being asked : {integral}")
    print(f"integrality gap : {cost_lp - cost_ip:.6f}")

    # ---------------- Exploration: total unimodularity ----------------
    rule("EXPLORATION: TOTAL UNIMODULARITY (slide 26)")
    A = incidence_matrix(SP_NODES, list(SP_ARCS))
    print(f"node-arc incidence matrix: {A.shape[0]} nodes x {A.shape[1]} arcs")
    print(f"every column has one +1 and one -1: "
          f"{all(sorted(A[:, k]).count(1.0) == 1 for k in range(A.shape[1]))}")
    tu, checked, bad = is_totally_unimodular(A, max_order=4)
    print(f"square submatrices checked up to order 4 : {checked}")
    print(f"all determinants in {{0, +1, -1}}          : {tu}")

    # A matrix that is NOT TU, for contrast: the TSP subtour system
    print("\ncontrast, a matrix that is not totally unimodular:")
    B = np.array([[1.0, 1.0, 0.0], [0.0, 1.0, 1.0], [1.0, 0.0, 1.0]])
    print(f"  odd cycle incidence matrix, det = {np.linalg.det(B):.1f} "
          f"-> outside {{0, +1, -1}}, so not TU")

    # ---------------- Problem 3 ----------------
    rule("PROBLEM 3: TRAVELLING SALESMAN, DFJ (slides 28-34)")
    cities = sorted(TSP_COORDS)
    dist = euclidean(TSP_COORDS)
    length, tour, rounds, cuts = tsp_dfj(cities, dist)
    print(f"optimal tour length {length:.4f} after {rounds} master solves "
          f"and {cuts} subtour cuts")
    print(f"tour edges: {sorted(tour)}")

    lp_bound, frac = tsp_lp_relaxation(cities, dist)
    print(f"\ndegree-only LP bound {lp_bound:.4f} "
          f"({100 * (length - lp_bound) / length:.2f}% below the optimum)")
    print(f"fractional edge values in that LP: "
          f"{ {k: round(v, 3) for k, v in frac.items()} or 'none'}")

    # ---------------- Problem 4 ----------------
    rule("PROBLEM 4: FACILITY LOCATION (slides 36-38)")
    F, C = sorted(FL_OPEN), sorted({j for (_, j) in FL_SERVE})
    obj, opened, assign, *_ = facility_location(F, C, FL_OPEN, FL_SERVE)
    print(f"single-level MIP : cost {obj:.1f}, open {opened}")
    print(f"assignment       : {assign}")

    tp_cost, tp_optima = facility_two_player(F, C, FL_OPEN, FL_SERVE)
    print(f"\ntwo-player brute force : optimal value {tp_cost:.1f}")
    print(f"leader choices attaining it : {[S for S, _ in tp_optima]}")
    print(f"optimal VALUES agree        : {abs(obj - tp_cost) < 1e-6}")
    mip_set = sorted(opened)
    matches = any(sorted(S) == mip_set for S, _ in tp_optima)
    print(f"the MIP's set is among them : {matches}")
    if len(tp_optima) > 1:
        print("  note: alternative optima. The single-level MIP is exact in")
        print("  VALUE, not in which optimal solution it returns.")

    strong = facility_location_lp_bound(F, C, FL_OPEN, FL_SERVE, strong=True)
    weak = facility_location_lp_bound(F, C, FL_OPEN, FL_SERVE, strong=False)
    print(f"\nLP bound, disaggregated links x_ij <= y_i : {strong:.4f}")
    print(f"LP bound, aggregated link                 : {weak:.4f}")
    print(f"integer optimum                           : {obj:.4f}")
    print(f"the disaggregated form is tighter         : {strong > weak + 1e-9}")
