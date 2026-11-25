import time

import cvxpy as cp
import numpy as np
from scipy.optimize import minimize

SEED = 5311


def in_primal(x, y, z, tol=1e-9):
    if y > tol:
        r = x / y
        return r < 700 and y * np.exp(r) <= z + tol
    return y >= -tol and x <= tol and z >= -tol


def in_dual(u, v, w, tol=1e-9):
    if u < -tol:
        r = v / u - 1.0
        return w >= -tol and r < 700 and -u * np.exp(r) <= w + tol
    return abs(u) <= tol and v >= -tol and w >= -tol


def entropy_expcone(n, m1, m2, solver="CLARABEL"):
    i = np.arange(1, n + 1)
    p = cp.Variable(n, nonneg=True)
    u = cp.Variable(n)
    con = [cp.constraints.ExpCone(u, p, np.ones(n)),
           cp.sum(p) == 1, i @ p == m1, (i ** 2) @ p == m2]
    pr = cp.Problem(cp.Minimize(-cp.sum(u)), con)
    t0 = time.perf_counter()
    pr.solve(solver=solver)
    return p.value, pr.value, time.perf_counter() - t0


def entropy_dual(n, m1, m2, scale=False):
    i = np.arange(1, n + 1)
    f1, f2 = (i / n, (i / n) ** 2) if scale else (i, i ** 2)
    t1, t2 = (m1 / n, m2 / n ** 2) if scale else (m1, m2)

    def f(v):
        a = -v[0] * f1 - v[1] * f2
        c = a.max()
        return np.log(np.exp(a - c).sum()) + c + v[0] * t1 + v[1] * t2
    t0 = time.perf_counter()
    r = minimize(f, np.zeros(2), method="BFGS",
                 options={"gtol": 1e-12, "maxiter": 20000})
    dt = time.perf_counter() - t0
    a = -r.x[0] * f1 - r.x[1] * f2
    w = np.exp(a - a.max())
    return w / w.sum(), -r.fun, dt


def moments(n, tilt=0.3):
    i = np.arange(1, n + 1)
    q = np.exp(-tilt * i / n)
    q /= q.sum()
    return float(i @ q), float((i ** 2) @ q)


if __name__ == "__main__":
    print("=" * 76)
    print("EP10: exponential cones")
    print("=" * 76)
    rng = np.random.default_rng(SEED)

    print("\n(a) the dual cone, checked in both directions")
    print("K     = cl{(x,y,z): y>0, y exp(x/y) <= z}")
    print("K*    = cl{(u,v,w): u<0, w>=0, -u exp(v/u - 1) <= w}")
    npair = bad = out = wit = 0
    for _ in range(120000):
        P = rng.normal(size=3) * rng.choice([0.3, 1.0, 3.0])
        D = rng.normal(size=3) * rng.choice([0.3, 1.0, 3.0])
        if in_primal(*P) and in_dual(*D):
            npair += 1
            bad += P @ D < -1e-7
        if not in_dual(*D) and out < 300:
            out += 1
            best = 0.0
            for _ in range(4000):
                y = abs(rng.normal()) * 2 + 1e-3
                x = rng.normal() * rng.choice([3.0, 1e3, 1e6])
                r = x / y
                if r > 700:
                    continue
                z = y * np.exp(r)
                best = min(best, x * D[0] + y * D[1] + z * D[2])
            wit += best < -1e-7
    print(f"   dual-feasible pairs tested : {npair},  with <p,d> < 0 : {bad}")
    print(f"   points outside K* tested   : {out},  witness found : {wit}")
    print("   the witness search spans |x| up to 1e6, which is needed for")
    print("   points with u just above 0: there the pairing only turns")
    print("   negative once x u dominates y v, i.e. for very negative x.")

    print("\n(b) Problem 1 of this homework as an exponential cone program")
    print("    -H(p) = sum p_i ln p_i;  u_i <= -p_i ln p_i  is")
    print("    p_i exp(u_i / p_i) <= 1, i.e. (u_i, p_i, 1) in K.")
    n = 6
    for m1, m2, ref in [(4.0, 18.0, -1.6965357595),
                        (4.5, 21.0, -1.2665057255)]:
        pv, f, _ = entropy_expcone(n, m1, m2)
        pd, g, _ = entropy_dual(n, m1, m2)
        print(f"   m1={m1}, m2={m2}: expcone {f:+.10f}, "
              f"2-var dual {g:+.10f}, HW6 {ref:+.10f}")
        print(f"      max |p_expcone - p_gibbs| = "
              f"{np.abs(pv - pd).max():.2e}")

    print("\n(c) when the conic form is worth it: n faces")
    print(f"{'n':>7} {'cone (ms)':>10} {'dual (ms)':>10} "
          f"{'cone resid':>11} {'dual resid':>11} {'scaled resid':>13}")
    for n in [6, 50, 500, 5000, 50000, 200000]:
        m1, m2 = moments(n)
        pd, g, td = entropy_dual(n, m1, m2)
        ps, gs, ts = entropy_dual(n, m1, m2, scale=True)
        ii = np.arange(1, n + 1)
        rs = max(abs(ps.sum() - 1), abs(ii @ ps - m1),
                 abs((ii ** 2) @ ps - m2) / max(1.0, m2))
        rd = max(abs(pd.sum() - 1), abs(ii @ pd - m1),
                 abs((ii ** 2) @ pd - m2) / max(1.0, m2))
        if n <= 5000:
            pv, f, tc = entropy_expcone(n, m1, m2)
            i = np.arange(1, n + 1)
            rc = max(abs(pv.sum() - 1), abs(i @ pv - m1),
                     abs((i ** 2) @ pv - m2) / max(1.0, m2))
            print(f"{n:>7} {1e3*tc:>10.1f} {1e3*td:>10.1f} "
                  f"{rc:>11.1e} {rd:>11.1e} {rs:>13.1e}")
        else:
            print(f"{n:>7} {'--':>10} {1e3*td:>10.1f} "
                  f"{'--':>11} {rd:>11.1e} {rs:>13.1e}")
    print("   the conic program carries 2n variables and n exponential")
    print("   cones; the dual of Problem 1 carries two, whatever n.")
    print("   residuals are the largest moment violation. The conic form")
    print("   holds 1e-11 throughout; the two-variable dual degrades,")
    print("   because i and i^2 differ by a factor n in scale and the")
    print("   Hessian conditions badly. Rescaling to i/n recovers four to")
    print("   five orders but does not remove the trend. Beyond n = 5e4 the")
    print("   unscaled dual does not move off nu = 0 at all.")
