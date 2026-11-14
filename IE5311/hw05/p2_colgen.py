import itertools

import gurobipy as gp
import numpy as np
from gurobipy import GRB

SEED = 5311
N, M = 7, 3
BIGM = 1e4


def make_instance():
    rng = np.random.default_rng(SEED)
    a = rng.integers(2, 7, N).astype(float)
    b = float(np.ceil(a.sum() / M * 1.25))
    c = rng.integers(1, 20, (N, M)).astype(float)
    return a, b, c


def patterns(a, b):
    out = []
    for bits in itertools.product([0, 1], repeat=N):
        v = np.array(bits, dtype=float)
        if a @ v <= b + 1e-9:
            out.append(v)
    return out


def original_ip(a, b, c, relax=False):
    m = gp.Model()
    m.setParam("OutputFlag", 0)
    vt = GRB.CONTINUOUS if relax else GRB.BINARY
    x = m.addVars(N, M, vtype=vt, lb=0.0, ub=1.0)
    m.setObjective(gp.quicksum(c[i, j] * x[i, j] for i in range(N)
                               for j in range(M)), GRB.MINIMIZE)
    for i in range(N):
        m.addConstr(gp.quicksum(x[i, j] for j in range(M)) == 1)
    for j in range(M):
        m.addConstr(gp.quicksum(a[i] * x[i, j] for i in range(N)) <= b)
    m.optimize()
    return m.ObjVal


def master(cols, a, b, c, artificials=True):
    m = gp.Model()
    m.setParam("OutputFlag", 0)
    lam = {}
    for (j, k) in cols:
        lam[j, k] = m.addVar(lb=0.0)
    s = [m.addVar(lb=0.0) for _ in range(N)] if artificials else None

    cost = gp.quicksum(
        float(c[:, j] @ cols[j, k]) * lam[j, k] for (j, k) in cols)
    if artificials:
        cost = cost + BIGM * gp.quicksum(s)
    m.setObjective(cost, GRB.MINIMIZE)

    cover = []
    for i in range(N):
        e = gp.quicksum(float(cols[j, k][i]) * lam[j, k] for (j, k) in cols)
        if artificials:
            e = e + s[i]
        cover.append(m.addConstr(e == 1))
    conv = []
    for j in range(M):
        e = gp.quicksum(lam[j, k] for (jj, k) in cols if jj == j)
        conv.append(m.addConstr(e == 1))

    m.optimize()
    if m.Status != GRB.OPTIMAL:
        return None, None, None, None
    pi = np.array([ct.Pi for ct in cover])
    mu = np.array([ct.Pi for ct in conv])
    art = float(sum(v.X for v in s)) if artificials else 0.0
    return m.ObjVal, pi, mu, art


def price(j, pi, mu, a, b, c):
    m = gp.Model()
    m.setParam("OutputFlag", 0)
    x = m.addVars(N, vtype=GRB.BINARY)
    m.setObjective(gp.quicksum((c[i, j] - pi[i]) * x[i]
                               for i in range(N)), GRB.MINIMIZE)
    m.addConstr(gp.quicksum(a[i] * x[i] for i in range(N)) <= b)
    m.optimize()
    patt = np.array([x[i].X for i in range(N)]).round()
    return m.ObjVal - mu[j], patt


if __name__ == "__main__":
    a, b, c = make_instance()
    print("=" * 74)
    print("PROBLEM 2: verification of the DW reformulation and pricing")
    print("=" * 74)
    print(f"{N} jobs, {M} agents, identical a_i and b (the Part 3 structure)")
    print(f"a = {a}")
    print(f"b = {b}")

    X = patterns(a, b)
    print(f"\n|X| = {len(X)} feasible patterns out of 2^{N} = {2**N} subsets")
    print("one shared pattern set serves all three agents")

    z_ip = original_ip(a, b, c)
    z_lp = original_ip(a, b, c, relax=True)

    full = {(j, k): X[k] for j in range(M) for k in range(len(X))}
    z_master, _, _, _ = master(full, a, b, c, artificials=False)

    print(f"\noriginal IP optimum          z_IP  = {z_ip:.6f}")
    print(f"original LP relaxation       z_LPR = {z_lp:.6f}")
    print(f"full DW master LP            z_MLP = {z_master:.6f}")
    print(f"z_LPR <= z_MLP <= z_IP ?     "
          f"{z_lp <= z_master + 1e-6 <= z_ip + 1e-6}")

    print("\n" + "-" * 74)
    print("COLUMN GENERATION from artificials only (Part 7 strategy a)")
    print("-" * 74)
    cols = {(j, 0): np.zeros(N) for j in range(M)}
    nxt = {j: 1 for j in range(M)}
    print(f"{'iter':>5} {'RMP obj':>14} {'artificial':>11} "
          f"{'min red cost':>13} {'cols added':>11}")
    for t in range(60):
        z, pi, mu, art = master(cols, a, b, c)
        added, worst = 0, 0.0
        new = []
        for j in range(M):
            rc, patt = price(j, pi, mu, a, b, c)
            worst = min(worst, rc)
            if rc < -1e-7:
                if not any(np.array_equal(patt, cols[j, k])
                           for (jj, k) in cols if jj == j):
                    new.append((j, patt))
                    added += 1
        print(f"{t:>5} {z:>14.6f} {art:>11.4f} {worst:>13.6f} {added:>11}")
        if added == 0:
            break
        for j, patt in new:
            cols[j, nxt[j]] = patt
            nxt[j] += 1

    print(f"\ncolumn generation optimum    = {z:.6f}")
    print(f"full enumeration master LP   = {z_master:.6f}")
    print(f"they agree                   : {abs(z - z_master) < 1e-6}")
    print(f"columns used {len(cols)} of {M * len(X)} in the full master")
    print(f"artificials driven to zero   : {art < 1e-9}")
