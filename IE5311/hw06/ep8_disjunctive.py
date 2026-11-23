import gurobipy as gp
import numpy as np
from gurobipy import GRB

UA, UB = 8.0, 4.0
PARAMS = {"OutputFlag": 0, "Presolve": 0, "Cuts": 0,
          "Heuristics": 0.0, "Threads": 1}


def complementarity_relaxation(m_a, m_b, n=2000001):
    """Area of the big-M LP relaxation of a.b=0 projected onto (a,b).

    Eliminating z from a <= m_a z, b <= m_b (1-z), z in [0,1] leaves
    a/m_a + b/m_b <= 1, intersected with the variable box."""
    a = np.linspace(0, UA, n)
    b = np.clip(m_b * (1.0 - a / m_a), 0.0, UB)
    return float(np.trapezoid(b, a))


def boxes(k, seed):
    rng = np.random.default_rng(seed)
    out = []
    for _ in range(k):
        lo = rng.uniform(0, 8, 2)
        out.append((lo, lo + rng.uniform(0.3, 1.2, 2)))
    return out


def bigM(P, c, relax):
    m = gp.Model()
    for k, v in PARAMS.items():
        m.setParam(k, v)
    L = np.min([p[0] for p in P], axis=0)
    U = np.max([p[1] for p in P], axis=0)
    M = U - L
    x = m.addMVar(2, lb=L, ub=U)
    vt = GRB.CONTINUOUS if relax else GRB.BINARY
    z = m.addMVar(len(P), lb=0, ub=1, vtype=vt)
    m.addConstr(z.sum() == 1)
    for k, (lo, hi) in enumerate(P):
        m.addConstr(x >= lo - M * (1 - z[k]))
        m.addConstr(x <= hi + M * (1 - z[k]))
    m.setObjective(c @ x, GRB.MINIMIZE)
    m.optimize()
    return m.ObjVal, (0 if relax else m.NodeCount)


def hull(P, c, relax):
    m = gp.Model()
    for k, v in PARAMS.items():
        m.setParam(k, v)
    K = len(P)
    x = m.addMVar(2, lb=-GRB.INFINITY)
    xk = [m.addMVar(2, lb=-GRB.INFINITY) for _ in range(K)]
    vt = GRB.CONTINUOUS if relax else GRB.BINARY
    z = m.addMVar(K, lb=0, ub=1, vtype=vt)
    m.addConstr(z.sum() == 1)
    m.addConstr(x == sum(xk))
    for k, (lo, hi) in enumerate(P):
        m.addConstr(xk[k] >= lo * z[k])
        m.addConstr(xk[k] <= hi * z[k])
    m.setObjective(c @ x, GRB.MINIMIZE)
    m.optimize()
    return m.ObjVal, (0 if relax else m.NodeCount)


if __name__ == "__main__":
    print("=" * 76)
    print("EP8: big-M versus hull reformulation")
    print("=" * 76)
    print("\n(a) two-term complementarity a.b = 0, 0<=a<=8, 0<=b<=4")
    print("the big-M relaxation projects to {a/Ma + b/Mb <= 1}, a triangle.")
    print("with tight bounds that triangle IS conv(D1 u D2), so the two")
    print("reformulations coincide. inflating M strictly enlarges it:")
    base = 0.5 * UA * UB
    box = UA * UB
    print(f"{'M_a':>7} {'M_b':>7} {'area':>9} {'/ hull':>8} {'/ box':>8}")
    for f in [1.0, 1.25, 1.5, 2.0, 4.0]:
        ar = complementarity_relaxation(UA * f, UB * f)
        print(f"{UA*f:>7.1f} {UB*f:>7.1f} {ar:>9.4f} "
              f"{ar/base:>7.2f}x {ar/box:>7.2f}")
    print(f"hull (exact) = {base:.4f}, full variable box = {box:.4f}")
    print("at twice the tight bound the relaxation is the whole box: the")
    print("complementarity has stopped constraining the relaxation at all.")

    print("\n(b) a disjunction where they differ: min c'x over a union of")
    print("    K disjoint boxes in R^2")
    print(f"{'K':>4} {'optimum':>10} {'bigM LP':>10} {'hull LP':>10} "
          f"{'bigM gap':>10} {'hull gap':>10} {'bigM nodes':>11} "
          f"{'hull nodes':>11}")
    for K in [3, 5, 8, 12, 20]:
        P = boxes(K, 5311 + K)
        c = np.array([1.0, 1.0])
        opt, _ = bigM(P, c, False)
        lb, nb = bigM(P, c, True)[0], bigM(P, c, False)[1]
        lh, nh = hull(P, c, True)[0], hull(P, c, False)[1]
        print(f"{K:>4} {opt:>10.4f} {lb:>10.4f} {lh:>10.4f} "
              f"{opt-lb:>10.4f} {opt-lh:>10.4f} {nb:>11.0f} {nh:>11.0f}")
    print("\nthe hull relaxation is exact (zero gap) by Balas' theorem;")
    print("big-M leaves a gap that branch and bound must close.")
