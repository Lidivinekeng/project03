import gurobipy as gp
import numpy as np
from gurobipy import GRB

CAP, DEM = 4.0, 4.0
CX, CY2 = 0.8, 2.0
M_PRIM, M_MULT = 4.0, 8.0


def follower(x):
    y1 = min(x, 8.0 / 3.0)
    return y1, DEM - y1


def leader_cost(x):
    y1, y2 = follower(x)
    return CX * x + CY2 * y2


def mpcc(m_mult=M_MULT, m_prim=M_PRIM, fix_x=None):
    m = gp.Model()
    m.setParam("OutputFlag", 0)
    x = m.addVar(lb=0.0, ub=CAP)
    y1 = m.addVar(lb=0.0)
    y2 = m.addVar(lb=0.0)
    lam = m.addVar(lb=-GRB.INFINITY)
    mu = m.addVar(lb=0.0)
    a1 = m.addVar(lb=0.0)
    a2 = m.addVar(lb=0.0)
    zm, z1, z2 = (m.addVar(vtype=GRB.BINARY) for _ in range(3))
    if fix_x is not None:
        m.addConstr(x == fix_x)
    m.addConstr(y1 + lam + mu - a1 == 0)
    m.addConstr(2 * y2 + lam - a2 == 0)
    m.addConstr(y1 + y2 == DEM)
    m.addConstr(y1 <= x)
    m.addConstr(mu <= m_mult * zm)
    m.addConstr(x - y1 <= m_prim * (1 - zm))
    m.addConstr(a1 <= m_mult * z1)
    m.addConstr(y1 <= m_prim * (1 - z1))
    m.addConstr(a2 <= m_mult * z2)
    m.addConstr(y2 <= m_prim * (1 - z2))
    m.setObjective(CX * x + CY2 * y2, GRB.MINIMIZE)
    m.optimize()
    if m.Status != GRB.OPTIMAL:
        return None
    return dict(x=x.X, y1=y1.X, y2=y2.X, lam=lam.X, mu=mu.X,
                a1=a1.X, a2=a2.X, obj=m.ObjVal)


if __name__ == "__main__":
    print("=" * 74)
    print("PROBLEM 2: bilevel capacity / production")
    print("=" * 74)
    grid = np.linspace(0, CAP, 400001)
    costs = np.array([leader_cost(v) for v in grid])
    kb = int(costs.argmin())
    print(f"grid search over x in [0,4]: x* = {grid[kb]:.6f}, "
          f"cost = {costs[kb]:.6f}")
    print(f"exact            : x* = 8/3 = {8/3:.6f}, cost = 4.8")

    r = mpcc()
    print(f"\nbig-M MPCC (M_prim = {M_PRIM}, M_mult = {M_MULT}):")
    for k in ("x", "y1", "y2", "lam", "mu", "a1", "a2", "obj"):
        print(f"   {k:4s} = {r[k]:+.8f}")
    print(f"matches exact    : {abs(r['obj'] - 4.8) < 1e-6}")

    print("\nmultiplier mu along the leader's range (follower KKT):")
    print(f"{'x':>6} {'y1':>8} {'y2':>8} {'mu':>8} {'lam':>8}")
    for xv in [0.0, 1.0, 2.0, 8 / 3, 3.0, 4.0]:
        y1, y2 = follower(xv)
        lam = -2 * y2
        mu = max(0.0, -y1 - lam)
        print(f"{xv:>6.3f} {y1:>8.4f} {y2:>8.4f} {mu:>8.4f} {lam:>8.4f}")
    print("mu attains 8 at x = 0, so any M_mult < 8 is invalid.")

    print("\neffect of an invalid bound, M_mult = 2, with x fixed:")
    print(f"{'x':>6} {'M=8 feasible':>14} {'M=2 feasible':>14}")
    for xv in [0.0, 1.0, 1.9, 2.0, 2.5, 8 / 3, 3.0]:
        a = mpcc(fix_x=xv)
        b = mpcc(m_mult=2.0, fix_x=xv)
        print(f"{xv:>6.3f} {str(a is not None):>14} {str(b is not None):>14}")
    bad = mpcc(m_mult=2.0)
    print(f"\nM_mult = 2 still returns obj = {bad['obj']:.6f} at "
          f"x = {bad['x']:.6f}:")
    print("the cut-off region x < 2 does not contain the optimum here, so")
    print("the wrong bound happens to be harmless on this instance while")
    print("still describing the wrong follower problem.")
