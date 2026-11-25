import gurobipy as gp
import numpy as np
from gurobipy import GRB

C = np.array([0.004, 0.006, 0.003])
P = np.array([0.3, 0.4, 0.3])
G = np.array([[1.06, 1.01, 0.98],
              [0.95, 1.03, 1.02],
              [1.10, 0.97, 0.96]])
L = np.array([1.01, 1.00, 1.02])
K = np.array([0.08, 0.09, 0.10])
NS, NI = G.shape
TOL = 1e-9


def extensive_form():
    m = gp.Model()
    m.setParam("OutputFlag", 0)
    x = m.addMVar(NI, lb=0.0)
    b = m.addMVar(NS, lb=0.0)
    m.addConstr(x.sum() == 1)
    rows = m.addConstr(G @ x + b >= L)
    m.setObjective(C @ x + (P * K) @ b, GRB.MINIMIZE)
    m.optimize()
    return x.X, b.X, m.ObjVal, rows.Pi


def subproblem(x, tie=1.0, eps=1e-12):
    short = L - G @ x
    pi = np.where(short > eps, K, np.where(short < -eps, 0.0, tie * K))
    q = K * np.maximum(short, 0.0)
    return pi, q


def benders(max_iter=50, tie=1.0):
    m = gp.Model()
    m.setParam("OutputFlag", 0)
    x = m.addMVar(NI, lb=0.0)
    th = m.addVar(lb=0.0)
    m.addConstr(x.sum() == 1)
    m.setObjective(C @ x + th, GRB.MINIMIZE)
    ub, log = np.inf, []
    for t in range(1, max_iter + 1):
        m.optimize()
        xv, lb = x.X.copy(), m.ObjVal
        pi, q = subproblem(xv, tie)
        true = C @ xv + P @ q
        ub = min(ub, true)
        log.append((t, lb, ub, ub - lb, xv.copy()))
        if ub - lb <= TOL:
            return xv, ub, log, t
        alpha = float(P @ (pi * L))
        beta = (P * pi) @ G
        m.addConstr(th >= alpha - beta @ x)
    return x.X, ub, log, max_iter


if __name__ == "__main__":
    print("=" * 74)
    print("PROBLEM 3: two-stage stochastic LP by Benders decomposition")
    print("=" * 74)
    xe, be, ze, duals = extensive_form()
    print(f"extensive form  x* = {np.round(xe, 8)}")
    print(f"                b* = {np.round(be, 8)}")
    print(f"                z* = {ze:.10f}")

    xb, zb, log, nit = benders()
    print(f"\nBenders convergence criterion: UB - LB <= {TOL:g}")
    print(f"{'iter':>5} {'lower bound':>14} {'upper bound':>14} {'gap':>12}")
    for t, lb, ub, gap, _ in log:
        print(f"{t:>5} {lb:>14.10f} {ub:>14.10f} {gap:>12.3e}")
    print(f"\nBenders        x* = {np.round(xb, 8)}")
    print(f"               z* = {zb:.10f}")
    print(f"iterations        = {nit}")
    print(f"|z_benders - z_ef|= {abs(zb - ze):.3e}")
    print(f"max |x diff|      = {np.abs(xb - xe).max():.3e}")

    pi, q = subproblem(xb)
    short = L - G @ xb
    print(f"\n{'scen':>5} {'wealth':>10} {'liability':>10} {'shortfall':>11}"
          f" {'b_s':>9} {'pi_s':>7} {'k_s':>6}")
    for s in range(NS):
        print(f"{s+1:>5} {(G @ xb)[s]:>10.6f} {L[s]:>10.4f} "
              f"{short[s]:>11.3e} {max(short[s],0):>9.6f} "
              f"{pi[s]:>7.2f} {K[s]:>6.2f}")

    print("\nscenario 3 is tight with b_3 = 0, so its subproblem dual is")
    print("any pi_3 in [0, k_3]. Every such choice gives a valid cut, since")
    print("Q_s(x) = max over that box dominates each member. Effect of the")
    print("tie-break on the run:")
    print(f"{'pi_3 / k_3':>11} {'iterations':>11} {'objective':>14}")
    for tie in [0.0, 0.25, 0.5, 0.838, 1.0]:
        _, zt, _, nt = benders(tie=tie)
        print(f"{tie:>11.3f} {nt:>11} {zt:>14.10f}")
    print("the extensive form reports pi_3 = 0.083810, strictly interior.")
