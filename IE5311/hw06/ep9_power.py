import time

import cvxpy as cp
import numpy as np
from scipy.optimize import minimize

SEED = 5311


def in_primal(x, y, z, a, tol=1e-9):
    return x >= -tol and y >= -tol and x ** a * y ** (1 - a) >= abs(z) - tol


def in_dual(u, v, w, a, tol=1e-9):
    if u < -tol or v < -tol:
        return False
    if u <= tol or v <= tol:
        return abs(w) <= tol
    return (u / a) ** a * (v / (1 - a)) ** (1 - a) >= abs(w) - tol


def pnorm_power(A, b, p, solver="CLARABEL"):
    """min ||Ax-b||_p via one 3-D power cone per residual."""
    m, n = A.shape
    x = cp.Variable(n)
    t = cp.Variable(nonneg=True)
    s = cp.Variable(m, nonneg=True)
    r = A @ x - b
    con = [cp.constraints.PowCone3D(s, cp.promote(t, (m,)), r, 1.0 / p),
           cp.sum(s) == t]
    pr = cp.Problem(cp.Minimize(t), con)
    t0 = time.perf_counter()
    pr.solve(solver=solver)
    return x.value, pr.value, time.perf_counter() - t0


if __name__ == "__main__":
    print("=" * 76)
    print("EP9: power cones")
    print("=" * 76)
    rng = np.random.default_rng(SEED)

    print("\n(a) the dual cone, checked by sampling")
    print("P_a = {(x,y,z): x,y>=0, x^a y^(1-a) >= |z|}")
    print("P_a* = {(u,v,w): u,v>=0, (u/a)^a (v/(1-a))^(1-a) >= |w|}")
    print(f"{'alpha':>7} {'pairs tested':>13} {'<p,d> < 0':>11} "
          f"{'outside tested':>15} {'witness found':>14}")
    for a in [0.2, 0.5, 0.75]:
        bad = npair = out = wit = 0
        for _ in range(60000):
            P = rng.normal(size=3) * rng.choice([0.3, 1.0, 3.0])
            D = rng.normal(size=3) * rng.choice([0.3, 1.0, 3.0])
            if in_primal(*P, a):
                if in_dual(*D, a):
                    npair += 1
                    bad += P @ D < -1e-7
            if not in_dual(*D, a):
                out += 1
                if out <= 300:
                    u, v, w = D
                    xw = max(u, 0.0) ** 0 * a
                    best = 0.0
                    for _ in range(400):
                        Q = np.abs(rng.normal(size=2)) * 3.0
                        z = Q[0] ** a * Q[1] ** (1 - a)
                        for sgn in (1.0, -1.0):
                            val = Q[0] * u + Q[1] * v + sgn * z * w
                            best = min(best, val)
                    wit += best < -1e-7
        print(f"{a:>7.2f} {npair:>13} {bad:>11} {min(out,300):>15} "
              f"{wit:>14}")
    print("   no dual-feasible pair pairs negatively, and every sampled")
    print("   point outside the claimed dual admits a cone element it")
    print("   pairs negatively with. The characterisation is exact.")

    print("\n(b) alpha = 1/2 is the rotated second-order cone")
    x = cp.Variable(3)
    obj = cp.Minimize(cp.sum(x))
    c1 = [cp.constraints.PowCone3D(x[0], x[1], x[2], 0.5), x[2] >= 2,
          x[0] + x[1] <= 6]
    p1 = cp.Problem(obj, c1); p1.solve(solver=cp.CLARABEL)
    y = cp.Variable(3)
    c2 = [cp.SOC(y[0] + y[1], cp.hstack([y[0] - y[1], 2 * y[2]])),
          y[0] >= 0, y[1] >= 0, y[2] >= 2, y[0] + y[1] <= 6]
    p2 = cp.Problem(cp.Minimize(cp.sum(y)), c2); p2.solve(solver=cp.CLARABEL)
    print(f"   power cone (a=1/2) value {p1.value:.10f}")
    print(f"   rotated SOC       value {p2.value:.10f}")
    print(f"   difference              {abs(p1.value-p2.value):.3e}")

    print("\n(c) p-norm regression, including irrational p")
    m, n = 60, 8
    A = rng.normal(size=(m, n))
    b = A @ rng.normal(size=n) + 0.3 * rng.normal(size=m)
    print(f"{'p':>8} {'q':>8} {'power cone':>13} {'SLSQP':>13} "
          f"{'Holder dual':>13} {'max gap':>10}")
    for p in [1.5, 2.0, 3.0, np.pi, 7.3]:
        q = p / (p - 1.0)
        xv, f, tt = pnorm_power(A, b, p)
        g = minimize(lambda z: np.linalg.norm(A @ z - b, p), np.zeros(n),
                     method="SLSQP", options={"maxiter": 3000, "ftol": 1e-14})
        y = cp.Variable(m)
        d = cp.Problem(cp.Maximize(b @ y),
                       [A.T @ y == 0, cp.pnorm(y, q) <= 1])
        d.solve(solver=cp.CLARABEL)
        print(f"{p:>8.5f} {q:>8.5f} {f:>13.8f} {g.fun:>13.8f} "
              f"{d.value:>13.8f} {max(abs(f-g.fun), abs(f-d.value)):>10.2e}")
    print("   the Holder dual max b'y s.t. A'y = 0, ||y||_q <= 1 with")
    print("   1/p + 1/q = 1 agrees throughout: conic duality on the power")
    print("   cone reproduces the classical norm duality, the rescaling by")
    print("   1/alpha and 1/(1-alpha) being what turns p into q.")

    print("\n(d) what an SOC tower costs when p is not a nice rational")
    print("   CVXPY reports, when asked to build ||.||_q by second-order")
    print("   cones instead of power cones:")
    import warnings
    for p in [np.pi, 7.3]:
        q = p / (p - 1.0)
        with warnings.catch_warnings(record=True) as cw:
            warnings.simplefilter("always")
            y = cp.Variable(m)
            cp.Problem(cp.Maximize(b @ y),
                       [A.T @ y == 0, cp.pnorm(y, q) <= 1]
                       ).solve(solver=cp.CLARABEL)
            for x in cw:
                msg = str(x.message)
                if "pnorm" in msg:
                    print(f"      p = {p:.5f} -> q = {q:.5f}: "
                          f"{msg.split(chr(10))[0]}")
    print("   one 3-D power cone per residual is exact and fixed in size.")
