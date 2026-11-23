import numpy as np
from scipy.optimize import minimize

N = 6
I = np.arange(1, N + 1)
CASES = [("fair", 3.5, 91 / 6), ("skewed", 4.0, 18.0), ("tight", 4.5, 21.0)]


def slater(m1, m2, n=N):
    if not (1 < m1 < n):
        return False, "m1 outside (1, n)"
    j = int(np.floor(m1))
    lo = (2 * j + 1) * m1 - j * (j + 1)
    hi = (n + 1) * m1 - n
    if not (lo < m2 < hi):
        return False, f"m2 outside ({lo:.4f}, {hi:.4f})"
    return True, f"lower {lo:.4f} < m2 = {m2:.4f} < upper {hi:.4f}"


def dual_obj(nu, m1, m2):
    z = np.exp(-nu[0] * I - nu[1] * I ** 2)
    return np.log(z.sum()) + nu[0] * m1 + nu[1] * m2


def solve_dual(m1, m2):
    r = minimize(dual_obj, np.zeros(2), args=(m1, m2), method="BFGS",
                 options={"gtol": 1e-12, "maxiter": 10000})
    nu = r.x
    w = np.exp(-nu[0] * I - nu[1] * I ** 2)
    return nu, w / w.sum(), -r.fun


def solve_primal(m1, m2):
    import cvxpy as cp
    p = cp.Variable(N, nonneg=True)
    cons = [cp.sum(p) == 1, I @ p == m1, (I ** 2) @ p == m2]
    prob = cp.Problem(cp.Minimize(-cp.sum(cp.entr(p))), cons)
    prob.solve(solver=cp.CLARABEL)
    return p.value, prob.value, [c.dual_value for c in cons]


if __name__ == "__main__":
    print("=" * 74)
    print("PROBLEM 1: maximum entropy with two moment constraints")
    print("=" * 74)
    print(f"n = {N}, faces {I.tolist()}")
    for name, m1, m2 in CASES:
        ok, why = slater(m1, m2)
        print(f"\n--- {name}: m1 = {m1}, m2 = {m2} ---")
        print(f"Slater: {ok}   ({why})")
        if not ok:
            continue
        nu, p_dual, g = solve_dual(m1, m2)
        p_pr, f, duals = solve_primal(m1, m2)
        gibbs = np.exp(-nu[0] * I - nu[1] * I ** 2)
        gibbs /= gibbs.sum()
        print(f"nu1 = {nu[0]:+.8f}   nu2 = {nu[1]:+.8f}")
        print(f"p (primal, Clarabel) = {np.round(p_pr, 8)}")
        print(f"p (Gibbs from dual)  = {np.round(gibbs, 8)}")
        print(f"max |difference|     = {np.abs(p_pr - gibbs).max():.3e}")
        print(f"primal  -H(p*) = {f:+.10f}")
        print(f"dual    g(nu*) = {g:+.10f}")
        print(f"duality gap    = {abs(f - g):.3e}")
        print(f"moments met    : sum p = {p_pr.sum():.10f}, "
              f"sum i p = {I @ p_pr:.8f}, sum i^2 p = {(I ** 2) @ p_pr:.8f}")

    print("\n--- Slater failure: m2 on the upper boundary ---")
    m1 = 4.0
    m2 = (N + 1) * m1 - N
    ok, why = slater(m1, m2)
    print(f"m1 = {m1}, m2 = {m2} (upper chord)  Slater: {ok}  ({why})")
    print("the only feasible p is supported on faces 1 and n, so some")
    print("p_i = 0, no strictly positive feasible point exists, and the")
    print("dual optimum recedes to infinity.")
    import cvxpy as cp
    p = cp.Variable(N, nonneg=True)
    pr = cp.Problem(cp.Minimize(-cp.sum(cp.entr(p))),
                    [cp.sum(p) == 1, I @ p == m1, (I ** 2) @ p == m2])
    pr.solve(solver=cp.CLARABEL)
    print(f"solver value {pr.value:.8f}, p = {np.round(p.value, 8)}")
