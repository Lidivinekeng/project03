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
    A = np.zeros((len(nodes), len(arcs)))
    idx = {n: k for k, n in enumerate(nodes)}
    for col, (i, j) in enumerate(arcs):
        A[idx[i], col] = 1.0
        A[idx[j], col] = -1.0
    return A


def is_totally_unimodular(A, max_order=4):
    rows, cols = A.shape
    bad = 0
    checked = 0
    for k in range(1, min(max_order, rows, cols) + 1):
        for rs in itertools.combinations(range(rows), k):
            for cs in itertools.combinations(range(cols), k):
                d = np.linalg.det(A[np.ix_(rs, cs)])
                checked += 1
                if min(abs(d), abs(d - 1), abs(d + 1)) > 1e-7:
                    bad += 1
    return bad == 0, checked


TSP_COORDS = {
    1: (0.0, 0.0), 2: (4.0, 1.0), 3: (5.0, 4.0),
    4: (2.0, 5.0), 5: (-1.0, 3.0), 6: (1.0, 2.0),
}


def euclidean(coords):
    return {(i, j): math.dist(coords[i], coords[j])
            for i in coords for j in coords if i < j}


def edge_var(x, i, j):
    return x[(i, j)] if i < j else x[(j, i)]


def components(cities, chosen):
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
    m = pulp.LpProblem("tsp_dfj", pulp.LpMinimize)
    x = {(i, j): pulp.LpVariable(f"x_{i}_{j}", cat=pulp.LpBinary)
         for (i, j) in dist}

    m += pulp.lpSum(dist[e] * x[e] for e in dist), "tour_length"

    for i in cities:
        m += pulp.lpSum(edge_var(x, i, j) for j in cities if j != i) == 2, \
             f"degree_{i}"

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
        for S in comps:
            inside = [(i, j) for (i, j) in dist if i in S and j in S]
            m += pulp.lpSum(x[e] for e in inside) <= len(S) - 1, \
                 f"subtour_{cuts}"
            cuts += 1


def tsp_lp_relaxation(cities, dist):
    m = pulp.LpProblem("tsp_lp", pulp.LpMinimize)
    x = {e: pulp.LpVariable(f"y_{e[0]}_{e[1]}", lowBound=0, upBound=1)
         for e in dist}

    m += pulp.lpSum(dist[e] * x[e] for e in dist)
    for i in cities:
        m += pulp.lpSum(edge_var(x, i, j) for j in cities if j != i) == 2
    m.solve(SOLVER)
    frac = {e: x[e].value() for e in dist
            if TOL < x[e].value() < 1 - TOL}
    return pulp.value(m.objective), frac


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
                      strong=True, relax=False):
    m = pulp.LpProblem("facility_location", pulp.LpMinimize)
    if relax:
        y = {i: pulp.LpVariable(f"y_{i}", lowBound=0, upBound=1)
             for i in facilities}
    else:
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
    return pulp.value(m.objective), opened, assign


def facility_two_player(facilities, customers, open_cost, serve_cost):
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


if __name__ == "__main__":
    rule("PROBLEM 2: SHORTEST PATH (slides 20-27)")
    cost_ip, path_ip, _ = shortest_path(SP_NODES, SP_ARCS, "s", "t")
    print(f"integer program : cost {cost_ip:.1f}, arcs {sorted(path_ip)}")

    cost_lp, path_lp, vals_lp = shortest_path(SP_NODES, SP_ARCS, "s", "t",
                                              relax=True)
    integral = all(min(abs(v), abs(v - 1)) < TOL for v in vals_lp.values())
    print(f"LP relaxation   : cost {cost_lp:.1f}, arcs {sorted(path_lp)}")
    print(f"LP solution is integral without being asked : {integral}")
    print(f"integrality gap : {cost_lp - cost_ip:.6f}")

    rule("EXPLORATION: TOTAL UNIMODULARITY (slide 26)")
    A = incidence_matrix(SP_NODES, list(SP_ARCS))
    print(f"node-arc incidence matrix: {A.shape[0]} nodes x {A.shape[1]} arcs")
    print(f"every column has one +1 and one -1: "
          f"{all(sorted(A[:, k]).count(1.0) == 1 for k in range(A.shape[1]))}")
    tu, checked = is_totally_unimodular(A, max_order=4)
    print(f"square submatrices checked up to order 4 : {checked}")
    print(f"all determinants in {{0, +1, -1}}          : {tu}")

    print("\ncontrast, a matrix that is not totally unimodular:")
    B = np.array([[1.0, 1.0, 0.0], [0.0, 1.0, 1.0], [1.0, 0.0, 1.0]])
    print(f"  odd cycle incidence matrix, det = {np.linalg.det(B):.1f} "
          f"-> outside {{0, +1, -1}}, so not TU")

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

    rule("PROBLEM 4: FACILITY LOCATION (slides 36-38)")
    F, C = sorted(FL_OPEN), sorted({j for (_, j) in FL_SERVE})
    obj, opened, assign = facility_location(F, C, FL_OPEN, FL_SERVE)
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

    strong = facility_location(F, C, FL_OPEN, FL_SERVE, strong=True, relax=True)[0]
    weak = facility_location(F, C, FL_OPEN, FL_SERVE, strong=False, relax=True)[0]
    print(f"\nLP bound, disaggregated links x_ij <= y_i : {strong:.4f}")
    print(f"LP bound, aggregated link                 : {weak:.4f}")
    print(f"integer optimum                           : {obj:.4f}")
    print(f"the disaggregated form is tighter         : {strong > weak + 1e-9}")
