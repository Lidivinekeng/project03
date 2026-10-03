import time

import numpy as np
import pulp

SOLVER = pulp.PULP_CBC_CMD(msg=0)

N = 3
h = [1.0, 2.0, 1.5]
b = [4.0, 3.0, 5.0]
lo = [10.0, 5.0, 8.0]
hi = [30.0, 25.0, 20.0]
TOTAL_LO = 45.0
TOTAL_HI = 60.0
BETA = 0.95


def scenarios(S, seed=5311):
    rng = np.random.default_rng(seed)
    out = []
    while len(out) < S:
        v = rng.uniform(lo, hi)
        if TOTAL_LO <= v.sum() <= TOTAL_HI:
            out.append(v)
    return np.array(out), np.full(S, 1.0 / S)


def cost(x, xi):
    return sum(max(h[i] * (x[i] - xi[i]), b[i] * (xi[i] - x[i]))
               for i in range(len(x)))


def cvar_of(values, p, beta):
    best = np.inf
    for eta in np.unique(values):
        v = eta + np.sum(p * np.maximum(values - eta, 0.0)) / (1.0 - beta)
        best = min(best, v)
    return best


def ru_lp(xi, p, beta, W=None, band=None, eta_lb=None):
    S, n = xi.shape
    idx = list(range(S)) if W is None else sorted(W)
    M = pulp.LpProblem("cvar_ru", pulp.LpMinimize)
    x = [pulp.LpVariable(f"x_{i}", 0) for i in range(n)]
    eta = pulp.LpVariable("eta") if eta_lb is None \
        else pulp.LpVariable("eta", eta_lb)
    u = {s: pulp.LpVariable(f"u_{s}", 0) for s in idx}
    t = {(s, i): pulp.LpVariable(f"t_{s}_{i}") for s in idx for i in range(n)}
    M += eta + pulp.lpSum(p[s] * u[s] for s in idx) / (1.0 - beta)
    for s in idx:
        M += u[s] >= pulp.lpSum(t[s, i] for i in range(n)) - eta
        for i in range(n):
            M += t[s, i] >= h[i] * (x[i] - xi[s, i])
            M += t[s, i] >= b[i] * (xi[s, i] - x[i])
    if band is not None:
        for i in range(n):
            M += x[i] <= (1.0 + band) * xi[:, i].min()
            M += x[i] >= (1.0 - band) * xi[:, i].max()
    t0 = time.perf_counter()
    M.solve(SOLVER)
    dt = time.perf_counter() - t0
    st = pulp.LpStatus[M.status]
    if st != "Optimal":
        return None, None, None, dt, st, len(M.constraints)
    return (pulp.value(M.objective), [v.value() for v in x], eta.value(), dt,
            st, len(M.constraints))


def expectation_lp(xi, p):
    S, n = xi.shape
    M = pulp.LpProblem("expected", pulp.LpMinimize)
    x = [pulp.LpVariable(f"x_{i}", 0) for i in range(n)]
    t = {(s, i): pulp.LpVariable(f"t_{s}_{i}")
         for s in range(S) for i in range(n)}
    M += pulp.lpSum(p[s] * t[s, i] for s in range(S) for i in range(n))
    for s in range(S):
        for i in range(n):
            M += t[s, i] >= h[i] * (x[i] - xi[s, i])
            M += t[s, i] >= b[i] * (xi[s, i] - x[i])
    M.solve(SOLVER)
    return pulp.value(M.objective), [v.value() for v in x]


def worst_case_lp(xi):
    S, n = xi.shape
    M = pulp.LpProblem("worst", pulp.LpMinimize)
    x = [pulp.LpVariable(f"x_{i}", 0) for i in range(n)]
    tau = pulp.LpVariable("tau")
    t = {(s, i): pulp.LpVariable(f"t_{s}_{i}")
         for s in range(S) for i in range(n)}
    M += tau
    for s in range(S):
        M += tau >= pulp.lpSum(t[s, i] for i in range(n))
        for i in range(n):
            M += t[s, i] >= h[i] * (x[i] - xi[s, i])
            M += t[s, i] >= b[i] * (xi[s, i] - x[i])
    M.solve(SOLVER)
    return pulp.value(M.objective), [v.value() for v in x]


def risk_envelope_lp(values, p, beta):
    S = len(values)
    M = pulp.LpProblem("envelope", pulp.LpMaximize)
    q = [pulp.LpVariable(f"q_{s}", 0, p[s] / (1.0 - beta)) for s in range(S)]
    M += pulp.lpSum(values[s] * q[s] for s in range(S))
    M += pulp.lpSum(q) == 1
    M.solve(SOLVER)
    return pulp.value(M.objective), [v.value() for v in q]


def master_subproblem(xi, p, beta, seed_size=10, tol=1e-6, max_rounds=100):
    S = xi.shape[0]
    rng = np.random.default_rng(3)
    W = set(rng.choice(S, size=seed_size, replace=False).tolist())
    trace = []
    t0 = time.perf_counter()
    for r in range(1, max_rounds + 1):
        lb, x, eta, _, st, _ = ru_lp(xi, p, beta, W=W, eta_lb=0.0)
        if st != "Optimal":
            raise RuntimeError(st)
        vals = np.array([cost(x, xi[s]) for s in range(S)])
        ub = eta + float(np.sum(p * np.maximum(vals - eta, 0.0))) / (1.0 - beta)
        viol = np.maximum(vals - eta, 0.0)
        trace.append((r, len(W), lb, ub))
        if ub - lb <= tol:
            return lb, x, r, len(W), time.perf_counter() - t0, trace
        add = [s for s in np.argsort(-viol) if s not in W and viol[s] > 0][:10]
        if not add:
            return lb, x, r, len(W), time.perf_counter() - t0, trace
        W.update(add)
    raise RuntimeError("master-subproblem hit the round limit")


if __name__ == "__main__":
    S = 400
    xi, p = scenarios(S)
    print("=" * 74)
    print("PROBLEM 3: CVaR MULTIDIMENSIONAL NEWSVENDOR")
    print("=" * 74)
    print(f"finite support, S = {S} equally likely scenarios drawn from Xi")
    print(f"beta = {BETA}, so CVaR averages the worst "
          f"{100*(1-BETA):.0f}% of outcomes")
    print(f"scenario totals range over "
          f"[{xi.sum(1).min():.2f}, {xi.sum(1).max():.2f}]")

    print("\n" + "-" * 74)
    print("PARTS 1 and 2: THE EPIGRAPH (ROCKAFELLAR-URYASEV) LP")
    print("-" * 74)
    val, x, eta, dt, st, nc = ru_lp(xi, p, BETA)
    print(f"optimal CVaR            : {val:.6f}")
    print(f"order quantity x        : {[round(u, 4) for u in x]}")
    print(f"eta at the optimum      : {eta:.6f}   (this is VaR_beta)")
    print(f"LP size                 : {nc} rows")
    print(f"solve time              : {dt:.4f} s")

    vals = np.array([cost(x, xi[s]) for s in range(S)])
    print(f"\nCVaR recomputed from the scenario costs at that x : "
          f"{cvar_of(vals, p, BETA):.6f}")
    print(f"scenarios strictly above eta : {(vals > eta + 1e-9).sum()} "
          f"of {S}  (expected about {(1-BETA)*S:.0f})")

    print("\nordering check, each model at its own optimum")
    e_val, e_x = expectation_lp(xi, p)
    w_val, w_x = worst_case_lp(xi)
    print(f"  min expectation : {e_val:.6f}   x = "
          f"{[round(u, 3) for u in e_x]}")
    print(f"  min CVaR        : {val:.6f}   x = {[round(u, 3) for u in x]}")
    print(f"  min worst case  : {w_val:.6f}   x = "
          f"{[round(u, 3) for u in w_x]}")
    print(f"  expectation <= CVaR <= worst case : "
          f"{e_val <= val + 1e-6 <= w_val + 1e-6}")

    print("\n" + "-" * 74)
    print("PART 2: MASTER-SUBPROBLEM ON THE SCENARIO SET")
    print("-" * 74)
    print(f"{'round':>6} {'|W|':>5} {'master (LB)':>13} {'true CVaR (UB)':>15} "
          f"{'gap':>12}")
    mval, mx, rounds, used, mdt, trace = master_subproblem(xi, p, BETA)
    for r, w, lb, ub in trace:
        print(f"{r:>6} {w:>5} {lb:>13.6f} {ub:>15.6f} {ub-lb:>12.3e}")
    print(f"\nrounds                  : {rounds}")
    print(f"scenarios ever in W     : {used} of {S} "
          f"({100*used/S:.1f}%)")
    print(f"objective               : {mval:.6f}")
    print(f"matches the full LP     : {abs(mval - val) < 1e-5}")
    print(f"time                    : {mdt:.4f} s (full LP {dt:.4f} s)")
    print("\nOnly the tail matters. At the optimum every scenario below eta")
    print("has u_s = 0 and contributes nothing, so a working set of roughly")
    print("the tail size reproduces the full answer.")

    print("\n" + "-" * 74)
    print("PART 3 (EXTRA CREDIT): DUALISING THE INNER PROBLEM")
    print("-" * 74)
    env_val, q = risk_envelope_lp(vals, p, BETA)
    nz = sum(1 for v in q if v > 1e-9)
    cap = p[0] / (1.0 - BETA)
    at_cap = sum(1 for v in q if v > cap - 1e-9)
    print("risk envelope  Q = {q >= 0 : sum_s q_s = 1, q_s <= p_s/(1-beta)}")
    print(f"max_q E_q[f(x,xi)]      : {env_val:.6f}")
    print(f"CVaR at the same x      : {cvar_of(vals, p, BETA):.6f}")
    print(f"the two agree           : "
          f"{abs(env_val - cvar_of(vals, p, BETA)) < 1e-6}")
    print(f"q has {nz} nonzeros, {at_cap} of them at the cap "
          f"p_s/(1-beta) = {cap:.6f}")
    print("\nThe LP dual of that inner maximisation has variables eta (for the")
    print("equality) and lambda_s >= 0 (for the caps), objective")
    print("eta + sum_s p_s lambda_s/(1-beta) and rows eta + lambda_s >= f_s.")
    print("Substituting lambda_s = (f_s - eta)^+ returns the formulation in")
    print("part 2 exactly, so the epigraph model IS the dual of the envelope.")

    print("\n" + "-" * 74)
    print("PART 4: THE BAND CONSTRAINT")
    print("-" * 74)
    smin = xi.min(axis=0)
    smax = xi.max(axis=0)
    print("with finite support every atom carries positive mass, so P-a.e.")
    print("means at every scenario, and the reduction needs no limit argument")
    print(f"\n{'i':>3} {'min_s xi_i':>12} {'max_s xi_i':>12} {'rho*_i':>9}")
    rs = []
    for i in range(N):
        r = (smax[i] - smin[i]) / (smax[i] + smin[i])
        rs.append(r)
        print(f"{i+1:>3} {smin[i]:>12.4f} {smax[i]:>12.4f} {r:>9.4f}")
    print(f"\nfeasible iff rho >= {max(rs):.4f}")
    print(f"\n{'rho':>8} {'status':>12} {'CVaR':>12}  x")
    for rho in (0.40, max(rs) - 1e-3, max(rs) + 1e-3, 0.75, 0.90, 1.00):
        rv, rx, _, _, rst, _ = ru_lp(xi, p, BETA, band=rho)
        if rv is None:
            print(f"{rho:>8.4f} {rst:>12} {'--':>12}")
        else:
            print(f"{rho:>8.4f} {rst:>12} {rv:>12.6f}  "
                  f"{[round(u, 3) for u in rx]}")
    print(f"\nunconstrained CVaR for reference: {val:.6f}")
