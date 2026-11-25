import time

import cvxpy as cp
import numpy as np

XBAR = np.array([0.7, 0.2, 0.1])
SIG = np.diag([4.0, 1.0, 1.0])
D = np.diag([2.0, 1.0, 1.0])
N = 3
REPS = 9
SOLVERS = ["CLARABEL", "SCS"]


def qp():
    x = cp.Variable(N, nonneg=True)
    con = [cp.sum(x) == 1, cp.quad_form(x, SIG) <= 1]
    pr = cp.Problem(cp.Minimize(cp.sum_squares(x - XBAR)), con)
    pr.solve(solver=cp.CLARABEL)
    return x.value, pr.value


def socp(solver):
    x = cp.Variable(N, nonneg=True)
    t = cp.Variable()
    con = [cp.SOC(t, x - XBAR), cp.SOC(np.array(1.0), D @ x), cp.sum(x) == 1]
    pr = cp.Problem(cp.Minimize(t), con)
    best = []
    for _ in range(REPS):
        t0 = time.perf_counter()
        pr.solve(solver=solver)
        best.append(time.perf_counter() - t0)
    return x.value, pr.value, float(np.median(best))


def sdp(solver):
    x = cp.Variable(N, nonneg=True)
    tau = cp.Variable()
    r = cp.reshape(x - XBAR, (N, 1), order="C")
    s = cp.reshape(D @ x, (N, 1), order="C")
    M1 = cp.bmat([[cp.reshape(tau, (1, 1), order="C"), r.T],
                  [r, np.eye(N)]])
    M2 = cp.bmat([[np.ones((1, 1)), s.T], [s, np.eye(N)]])
    con = [M1 >> 0, M2 >> 0, cp.sum(x) == 1]
    pr = cp.Problem(cp.Minimize(tau), con)
    best = []
    for _ in range(REPS):
        t0 = time.perf_counter()
        pr.solve(solver=solver)
        best.append(time.perf_counter() - t0)
    return x.value, pr.value, float(np.median(best))


def socp_dual():
    u = cp.Variable(N)
    w = cp.Variable(N)
    nu = cp.Variable()
    con = [cp.norm(u, 2) <= 1, u + D @ w + nu * np.ones(N) <= 0]
    pr = cp.Problem(cp.Maximize(XBAR @ u + nu - cp.norm(w, 2)), con)
    pr.solve(solver=cp.CLARABEL)
    return pr.value


def sdp_dual():
    a = cp.Variable(N)
    w = cp.Variable(N)
    nu = cp.Variable()
    con = [a + D @ w + nu * np.ones(N) <= 0]
    obj = XBAR @ a - cp.sum_squares(a) / 4 - cp.norm(w, 2) + nu
    pr = cp.Problem(cp.Maximize(obj), con)
    pr.solve(solver=cp.CLARABEL)
    return pr.value


if __name__ == "__main__":
    print("=" * 76)
    print("PROBLEM 4: tracking-error portfolio as QP, SOCP and SDP")
    print("=" * 76)
    print(f"xbar = {XBAR},  Sigma = diag(4,1,1)")
    v = XBAR @ SIG @ XBAR
    print(f"benchmark risk xbar'Sigma xbar = {v:.4f} > 1, "
          f"so the risk constraint binds")

    xq, fq = qp()
    print(f"\nQP   x* = {np.round(xq, 8)}   ||x-xbar||^2 = {fq:.10f}")

    print(f"\n{'form':>5} {'solver':>9} {'objective':>14} {'x1':>10} "
          f"{'x2':>10} {'x3':>10} {'time (ms)':>10}")
    res = {}
    for s in SOLVERS:
        x, f, t = socp(s)
        res[("socp", s)] = (x, f)
        print(f"{'SOCP':>5} {s:>9} {f:>14.10f} {x[0]:>10.6f} {x[1]:>10.6f} "
              f"{x[2]:>10.6f} {1e3*t:>10.3f}")
    for s in SOLVERS:
        x, f, t = sdp(s)
        res[("sdp", s)] = (x, f)
        print(f"{'SDP':>5} {s:>9} {f:>14.10f} {x[0]:>10.6f} {x[1]:>10.6f} "
              f"{x[2]:>10.6f} {1e3*t:>10.3f}")

    xs, fs = res[("socp", "CLARABEL")]
    xd, fd = res[("sdp", "CLARABEL")]
    print(f"\nSOCP minimises the norm, SDP the squared norm:")
    print(f"   t*^2        = {fs**2:.10f}")
    print(f"   tau*        = {fd:.10f}")
    print(f"   QP value    = {fq:.10f}")
    print(f"   |t*^2 - tau*| = {abs(fs**2 - fd):.3e}")
    print(f"   max |x_socp - x_sdp| = {np.abs(xs - xd).max():.3e}")
    print(f"   risk at x*  = {xs @ SIG @ xs:.10f}   (bound 1)")
    print(f"   sum x*      = {xs.sum():.10f}")

    print(f"\nhand-derived duals:")
    print(f"   SOCP dual value = {socp_dual():.10f}  vs primal "
          f"{fs:.10f}   gap {abs(socp_dual()-fs):.3e}")
    print(f"   SDP  dual value = {sdp_dual():.10f}  vs primal "
          f"{fd:.10f}   gap {abs(sdp_dual()-fd):.3e}")


def scaled(n, seed=5311):
    rng = np.random.default_rng(seed)
    xb = rng.dirichlet(np.ones(n))
    sig = np.diag(rng.uniform(0.5, 4.0, n))
    return xb, sig, np.diag(np.sqrt(np.diag(sig)))


def socp_n(xb, sig, d, solver):
    n = len(xb)
    x = cp.Variable(n, nonneg=True)
    t = cp.Variable()
    pr = cp.Problem(cp.Minimize(t),
                    [cp.SOC(t, x - xb), cp.SOC(np.array(1.0), d @ x),
                     cp.sum(x) == 1])
    pr.solve(solver=solver)
    return pr.value, pr.solver_stats.solve_time


def sdp_n(xb, sig, d, solver):
    n = len(xb)
    x = cp.Variable(n, nonneg=True)
    tau = cp.Variable()
    r = cp.reshape(x - xb, (n, 1), order="C")
    s = cp.reshape(d @ x, (n, 1), order="C")
    M1 = cp.bmat([[cp.reshape(tau, (1, 1), order="C"), r.T], [r, np.eye(n)]])
    M2 = cp.bmat([[np.ones((1, 1)), s.T], [s, np.eye(n)]])
    pr = cp.Problem(cp.Minimize(tau), [M1 >> 0, M2 >> 0, cp.sum(x) == 1])
    pr.solve(solver=solver)
    return pr.value, pr.solver_stats.solve_time


if __name__ == "__main__":
    print("\n" + "-" * 76)
    print("how the two forms scale: n assets, solver time only (Clarabel)")
    print("-" * 76)
    print(f"{'n':>5} {'SOCP cone':>12} {'SDP blocks':>14} "
          f"{'SOCP (ms)':>11} {'SDP (ms)':>11} {'ratio':>8} {'|gap|':>10}")
    for n in [3, 10, 30, 60, 100]:
        xb, sig, d = scaled(n)
        fs, ts = socp_n(xb, sig, d, "CLARABEL")
        fd, td = sdp_n(xb, sig, d, "CLARABEL")
        print(f"{n:>5} {f'2 x {n+1}':>12} {f'2 x {n+1}^2':>14} "
              f"{1e3*ts:>11.2f} {1e3*td:>11.2f} {td/ts:>8.1f}x "
              f"{abs(fs**2 - fd):>10.2e}")
    print("the SDP carries two (n+1)x(n+1) blocks where the SOCP carries two")
    print("cones of length n+1, so its interior-point work grows far faster")
    print("while both return the same portfolio.")
