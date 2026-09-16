"""
IE 5311 Homework, Problem 3 [45 pts]: GlobalLogix distribution network.

Part 1 : deterministic minimum-cost flow.
Part 2 : robust (worst-case) and stochastic (average-case) formulations
         under +/- 1% variation in capacity and cost, equally likely.
Part 3 : multicommodity extension (formulated; see the write-up).

SETS
    N = F  u  D  u  S      nodes
        F = {f1, f2}       factories
        D = {d1, d2}       distribution centres (pure transshipment)
        S = {s1, s2, s3}   stores
    A subset N x N         directed arcs, split as
        A1 = F x D         factory-to-DC arcs
        A2 = D x S         DC-to-store arcs

PARAMETERS
    b_i     net supply at node i: +supply at factories, -demand at
            stores, 0 at DCs                                 [units]
    u_ij    capacity of arc (i,j)                            [units]
    c_ij    cost per unit shipped on arc (i,j)               [$/unit]

DECISION VARIABLES
    x_ij >= 0   units shipped on arc (i,j)                   [units]

DETERMINISTIC MODEL
    min   sum_{(i,j) in A} c_ij x_ij
    s.t.  sum_{j: (i,j) in A} x_ij - sum_{j: (j,i) in A} x_ji = b_i
                                                   for all i in N
          0 <= x_ij <= u_ij                        for all (i,j) in A
"""

import itertools

import gurobipy as gp
import numpy as np
from gurobipy import GRB

# ----------------------------------------------------------------------
# DATA, transcribed from the assignment table
# ----------------------------------------------------------------------
F = ["f1", "f2"]
D = ["d1", "d2"]
S = ["s1", "s2", "s3"]
N = F + D + S

SUPPLY = {"f1": 70.0, "f2": 50.0}
DEMAND = {"s1": 40.0, "s2": 45.0, "s3": 35.0}
b = {i: SUPPLY.get(i, 0.0) - DEMAND.get(i, 0.0) for i in N}

#                       capacity, cost
ARC = {
    ("f1", "d1"): (60.0, 2.0),
    ("f1", "d2"): (50.0, 4.0),
    ("f2", "d1"): (40.0, 3.0),
    ("f2", "d2"): (60.0, 1.0),
    ("d1", "s1"): (40.0, 3.0),
    ("d1", "s2"): (40.0, 1.0),
    ("d1", "s3"): (40.0, 2.0),
    ("d2", "s1"): (40.0, 2.0),
    ("d2", "s2"): (40.0, 3.0),
    ("d2", "s3"): (40.0, 2.0),
}
A = list(ARC)
A1 = [(i, j) for (i, j) in A if i in F]     # committed first
A2 = [(i, j) for (i, j) in A if i in D]     # recourse
u = {a: ARC[a][0] for a in A}
c = {a: ARC[a][1] for a in A}

DEV = 0.01          # +/- 1%
PENALTY = 50.0      # $/unit of unmet demand in the recourse stage


def check_data():
    tot_s, tot_d = sum(SUPPLY.values()), sum(DEMAND.values())
    print(f"total supply {tot_s:.0f}, total demand {tot_d:.0f}, "
          f"balanced: {abs(tot_s - tot_d) < 1e-9}")
    print(f"sum of b_i = {sum(b.values()):.0f} (must be 0 for feasibility)")
    for j in D:
        inn = sum(u[a] for a in A if a[1] == j)
        out = sum(u[a] for a in A if a[0] == j)
        print(f"  {j}: inbound capacity {inn:.0f}, outbound capacity {out:.0f}")
    for k in S:
        cap = sum(u[a] for a in A if a[1] == k)
        print(f"  {k}: inbound capacity {cap:.0f} vs demand {DEMAND[k]:.0f}"
              f"  -> reachable: {cap >= DEMAND[k]}")


# ----------------------------------------------------------------------
# PART 1: deterministic
# ----------------------------------------------------------------------
def deterministic(cost=None, cap=None, verbose=True, tag="deterministic"):
    cost = cost or c
    cap = cap or u
    m = gp.Model(tag)
    m.setParam("OutputFlag", 0)
    x = m.addVars(A, lb=0.0, name="x")
    for a in A:
        x[a].UB = cap[a]
    m.setObjective(gp.quicksum(cost[a] * x[a] for a in A), GRB.MINIMIZE)
    for i in N:
        m.addConstr(
            gp.quicksum(x[a] for a in A if a[0] == i)
            - gp.quicksum(x[a] for a in A if a[1] == i) == b[i],
            name=f"balance_{i}")
    m.optimize()
    if m.Status != GRB.OPTIMAL:
        return None, None
    if verbose:
        print(f"\n{tag}: total cost ${m.ObjVal:,.2f}")
        print(f"{'arc':>12}  {'flow':>7}  {'cap':>6}  {'cost/unit':>9}  {'$':>8}")
        for a in A:
            if x[a].X > 1e-6:
                mark = " (at cap)" if abs(x[a].X - cap[a]) < 1e-6 else ""
                print(f"{str(a):>12}  {x[a].X:>7.1f}  {cap[a]:>6.1f}"
                      f"  {cost[a]:>9.2f}  {cost[a]*x[a].X:>8.1f}{mark}")
    return m.ObjVal, {a: x[a].X for a in A}


# ----------------------------------------------------------------------
# PART 2a: ROBUST, worst case over the box
#
#   The uncertainty set is U = { (c,u) : c_ij in [0.99 c, 1.01 c],
#                                        u_ij in [0.99 u, 1.01 u] }.
#   Cost enters the objective with a positive coefficient and x >= 0, so
#   the inner maximum is attained at c_ij = 1.01 c_ij.
#   The capacity constraint must hold for EVERY realization, so the
#   binding bound is the smallest, u_ij = 0.99 u_ij.
#   The worst case therefore has a closed form and needs no inner model.
# ----------------------------------------------------------------------
def robust(verbose=True):
    c_hi = {a: c[a] * (1 + DEV) for a in A}
    u_lo = {a: u[a] * (1 - DEV) for a in A}
    return deterministic(c_hi, u_lo, verbose, tag="robust (worst case)")


# ----------------------------------------------------------------------
# PART 2b: TWO-STAGE STOCHASTIC PROGRAM
#
#   Split by when the decision is made. Long-haul factory-to-DC shipments
#   are committed before the realization is known (first stage). Local
#   DC-to-store deliveries are chosen after it is observed (recourse).
#   Unmet demand is penalised, so the recourse problem is always feasible.
#
#   min   sum_{(i,j) in A1} c_ij x_ij
#         + sum_w pi_w [ sum_{(j,k) in A2} c^w_jk y^w_jk
#                        + p sum_{k in S} v^w_k ]
#   s.t.  sum_{j} x_ij <= S_i                        for i in F
#         x_ij <= (1 - DEV) u_ij                     for (i,j) in A1
#              (committed before u is seen, so it must fit every case)
#         sum_i x_ij = sum_k y^w_jk                  for j in D, all w
#         sum_j y^w_jk + v^w_k = D_k                 for k in S, all w
#         0 <= y^w_jk <= u^w_jk,  v^w_k >= 0
# ----------------------------------------------------------------------
def make_scenarios(n_scen, seed=5311):
    """Each parameter independently +DEV or -DEV with probability 1/2."""
    rng = np.random.default_rng(seed)
    scen = []
    for _ in range(n_scen):
        sc = rng.choice([-DEV, DEV], size=len(A))
        su = rng.choice([-DEV, DEV], size=len(A))
        scen.append(({a: c[a] * (1 + sc[k]) for k, a in enumerate(A)},
                     {a: u[a] * (1 + su[k]) for k, a in enumerate(A)}))
    return scen


def stochastic(scenarios, verbose=True):
    W = range(len(scenarios))
    pi = 1.0 / len(scenarios)

    m = gp.Model("two_stage_sp")
    m.setParam("OutputFlag", 0)

    x = m.addVars(A1, lb=0.0, name="x")                  # first stage
    # addVars(W, A2) would flatten the arc tuple into two index slots,
    # so build the (scenario, tail, head) keys explicitly.
    YK = [(w, i, j) for w in W for (i, j) in A2]
    y = m.addVars(YK, lb=0.0, name="y")                  # recourse
    v = m.addVars(W, S, lb=0.0, name="v")                # unmet demand

    for a in A1:
        x[a].UB = u[a] * (1 - DEV)

    m.setObjective(
        gp.quicksum(c[a] * x[a] for a in A1)
        + pi * gp.quicksum(scenarios[w][0][(i, j)] * y[w, i, j]
                           for w in W for (i, j) in A2)
        + pi * PENALTY * gp.quicksum(v[w, k] for w in W for k in S),
        GRB.MINIMIZE)

    for i in F:
        m.addConstr(gp.quicksum(x[a] for a in A1 if a[0] == i) <= SUPPLY[i],
                    name=f"supply_{i}")

    for w in W:
        for j in D:
            m.addConstr(gp.quicksum(x[a] for a in A1 if a[1] == j)
                        == gp.quicksum(y[w, i, k] for (i, k) in A2 if i == j),
                        name=f"dc_{j}_{w}")
        for k in S:
            m.addConstr(gp.quicksum(y[w, i, j] for (i, j) in A2 if j == k)
                        + v[w, k] == DEMAND[k], name=f"demand_{k}_{w}")
        for (i, j) in A2:
            m.addConstr(y[w, i, j] <= scenarios[w][1][(i, j)],
                        name=f"cap_{i}_{j}_{w}")

    m.optimize()
    assert m.Status == GRB.OPTIMAL, m.Status

    unmet = sum(v[w, k].X for w in W for k in S) * pi
    if verbose:
        print(f"\ntwo-stage SP over {len(scenarios)} scenarios: "
              f"expected cost ${m.ObjVal:,.2f}")
        print("first-stage commitments (factory -> DC), fixed before the draw:")
        for a in A1:
            if x[a].X > 1e-6:
                print(f"  {str(a):>12}  {x[a].X:>7.2f}  (cap floor "
                      f"{u[a]*(1-DEV):.1f})")
        print(f"expected unmet demand across scenarios: {unmet:.4f} units")
    return m.ObjVal, {a: x[a].X for a in A1}, unmet



def stochastic_cbc(scenarios, verbose=False):
    """
    Same two-stage model under PuLP/CBC. Needed because the Gurobi
    size-limited licence caps a model at 2000 variables and 2000
    constraints, and this SP uses 4 + 9|W| variables and 2 + 11|W|
    constraints, so it exceeds the cap beyond |W| = 181.
    """
    import pulp
    W = range(len(scenarios))
    pi = 1.0 / len(scenarios)

    m = pulp.LpProblem("two_stage_sp", pulp.LpMinimize)
    x = {a: pulp.LpVariable(f"x_{a[0]}_{a[1]}", 0, u[a] * (1 - DEV)) for a in A1}
    y = {(w, i, j): pulp.LpVariable(f"y_{w}_{i}_{j}", 0) for w in W for (i, j) in A2}
    v = {(w, k): pulp.LpVariable(f"v_{w}_{k}", 0) for w in W for k in S}

    m += (pulp.lpSum(c[a] * x[a] for a in A1)
          + pi * pulp.lpSum(scenarios[w][0][(i, j)] * y[w, i, j]
                            for w in W for (i, j) in A2)
          + pi * PENALTY * pulp.lpSum(v[w, k] for w in W for k in S))

    for i in F:
        m += pulp.lpSum(x[a] for a in A1 if a[0] == i) <= SUPPLY[i]
    for w in W:
        for j in D:
            m += (pulp.lpSum(x[a] for a in A1 if a[1] == j)
                  == pulp.lpSum(y[w, i, k] for (i, k) in A2 if i == j))
        for k in S:
            m += (pulp.lpSum(y[w, i, j] for (i, j) in A2 if j == k)
                  + v[w, k] == DEMAND[k])
        for (i, j) in A2:
            m += y[w, i, j] <= scenarios[w][1][(i, j)]

    m.solve(pulp.PULP_CBC_CMD(msg=0))
    assert pulp.LpStatus[m.status] == "Optimal", pulp.LpStatus[m.status]
    unmet = sum(v[w, k].value() for w in W for k in S) * pi
    return pulp.value(m.objective), {a: x[a].value() for a in A1}, unmet


def gurobi_fits(n_scen):
    """4 + 9n variables, 2 + 11n constraints, against a 2000 cap each."""
    return (4 + 9 * n_scen <= 2000) and (2 + 11 * n_scen <= 2000)


if __name__ == "__main__":
    print("=" * 68); print("DATA CHECK"); print("=" * 68)
    check_data()

    print("\n" + "=" * 68); print("PART 1: DETERMINISTIC"); print("=" * 68)
    det_obj, det_x = deterministic()

    print("\n" + "=" * 68); print("PART 2a: ROBUST (WORST CASE)"); print("=" * 68)
    rob_obj, rob_x = robust()
    print(f"\nrobust premium over deterministic: "
          f"${rob_obj - det_obj:,.2f}  ({100*(rob_obj-det_obj)/det_obj:.2f}%)")
    same = all(abs(det_x[a] - rob_x[a]) < 1e-6 for a in A)
    print(f"robust routing identical to deterministic routing: {same}")

    print("\n" + "=" * 68); print("PART 2b: STOCHASTIC (AVERAGE CASE)"); print("=" * 68)
    print("solver choice is driven by the Gurobi size-limited licence:")
    print(f"{'scenarios':>10}  {'vars':>6}  {'cons':>6}  {'fits Gurobi':>12}")
    for n in (1, 50, 150, 500, 2000):
        print(f"{n:>10}  {4+9*n:>6}  {2+11*n:>6}  {str(gurobi_fits(n)):>12}")

    print("\ncross-check at 50 scenarios, where both solvers fit:")
    g_obj, _, _ = stochastic(make_scenarios(50), verbose=False)
    c_obj, _, _ = stochastic_cbc(make_scenarios(50))
    print(f"  Gurobi ${g_obj:,.4f}   CBC ${c_obj:,.4f}   "
          f"agree: {abs(g_obj - c_obj) < 1e-6}")

    print("\nexpected cost as the sample grows:")
    print(f"{'scenarios':>10}  {'solver':>7}  {'expected cost':>14}  {'E[unmet]':>9}")
    for n in (1, 10, 50, 150, 500, 2000):
        if gurobi_fits(n):
            obj, xs, unmet = stochastic(make_scenarios(n), verbose=False)
            tag = "Gurobi"
        else:
            obj, xs, unmet = stochastic_cbc(make_scenarios(n))
            tag = "CBC"
        print(f"{n:>10}  {tag:>7}  ${obj:>13,.2f}  {unmet:>9.4f}")
        if n == 2000:
            print("\n  first-stage commitments at 2000 scenarios "
                  "(fixed before the draw):")
            for a in A1:
                if xs[a] > 1e-6:
                    print(f"    {str(a):>12}  {xs[a]:>7.2f}  "
                          f"(cap floor {u[a]*(1-DEV):.1f})")

    print("\n" + "-" * 68)
    print("WHY THE COST PERTURBATION ALONE CHANGES NOTHING")
    print("-" * 68)
    print("E[c_ij] = 0.5(0.99 c_ij) + 0.5(1.01 c_ij) = c_ij, so expectation")
    print("is linear and the mean cost equals the nominal cost exactly.")
    mean_c = {a: 0.5 * c[a] * 0.99 + 0.5 * c[a] * 1.01 for a in A}
    print(f"max |E[c_ij] - c_ij| over all arcs = "
          f"{max(abs(mean_c[a] - c[a]) for a in A):.2e}")
    mc_obj, _ = deterministic(mean_c, u, verbose=False, tag="mean-cost")
    print(f"deterministic with mean costs : ${mc_obj:,.2f}")
    print(f"deterministic with nominal    : ${det_obj:,.2f}")
    print(f"identical: {abs(mc_obj - det_obj) < 1e-6}")
    print("Only the CAPACITY randomness makes the stochastic model differ")
    print("from the nominal one, and only because the first-stage shipment")
    print("is committed before the capacity is observed.")
