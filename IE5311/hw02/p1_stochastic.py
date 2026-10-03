import time

import numpy as np
import pulp

SOLVER = pulp.PULP_CBC_CMD(msg=0)

N = 3
h = [1.0, 2.0, 1.5]
b = [4.0, 3.0, 5.0]
lo = [10.0, 5.0, 8.0]
hi = [30.0, 25.0, 20.0]
RHO = 0.4


def critical_fractile():
    return [lo[i] + (hi[i] - lo[i]) * b[i] / (b[i] + h[i]) for i in range(N)]


def closed_form_cost():
    return sum((hi[i] - lo[i]) * h[i] * b[i] / (2.0 * (h[i] + b[i]))
               for i in range(N))


def exact_cost(x):
    return sum(h[i] * (x[i] - lo[i]) ** 2 / (2.0 * (hi[i] - lo[i]))
               + b[i] * (hi[i] - x[i]) ** 2 / (2.0 * (hi[i] - lo[i]))
               for i in range(N))


def draw(m, seed):
    rng = np.random.default_rng(seed)
    return rng.uniform(lo, hi, size=(m, N))


def saa(xi, band=None):
    m = xi.shape[0]
    M = pulp.LpProblem("saa", pulp.LpMinimize)
    x = [pulp.LpVariable(f"x_{i}", 0) for i in range(N)]
    t = {(j, i): pulp.LpVariable(f"t_{j}_{i}", 0)
         for j in range(m) for i in range(N)}
    M += pulp.lpSum(t.values()) / m
    for j in range(m):
        for i in range(N):
            M += t[j, i] >= h[i] * (x[i] - xi[j, i])
            M += t[j, i] >= b[i] * (xi[j, i] - x[i])
    if band is not None:
        rho, xmin, xmax = band
        for i in range(N):
            M += x[i] <= (1.0 + rho) * xmin[i]
            M += x[i] >= (1.0 - rho) * xmax[i]
    status = M.solve(SOLVER)
    if pulp.LpStatus[M.status] != "Optimal":
        return None, None, pulp.LpStatus[M.status]
    return (pulp.value(M.objective), [v.value() for v in x],
            pulp.LpStatus[M.status])


def rho_star():
    return [(hi[i] - lo[i]) / (hi[i] + lo[i]) for i in range(N)]


if __name__ == "__main__":
    print("=" * 74)
    print("PROBLEM 1: STOCHASTIC MULTIDIMENSIONAL NEWSVENDOR")
    print("=" * 74)
    print(f"n = {N}, zero purchase cost")
    print(f"{'i':>3} {'h_i':>6} {'b_i':>6} {'lo_i':>7} {'hi_i':>7} "
          f"{'b/(b+h)':>9}")
    for i in range(N):
        print(f"{i+1:>3} {h[i]:>6.2f} {b[i]:>6.2f} {lo[i]:>7.1f} {hi[i]:>7.1f} "
              f"{b[i]/(b[i]+h[i]):>9.4f}")

    star = critical_fractile()
    print("\nclosed-form optimum, independent uniform marginals")
    print("  x*_i = lo_i + (hi_i - lo_i) b_i/(b_i+h_i)")
    print(f"  x*            = {[round(v, 4) for v in star]}")
    print(f"  E[f(x*,xi)]   = {closed_form_cost():.6f}")

    print("\n" + "-" * 74)
    print("PART 2: SAA CONVERGENCE AS THE SAMPLE GROWS")
    print("-" * 74)
    print(f"{'m':>7} {'SAA value':>12} {'true E[f] at x_m':>18} "
          f"{'max_i |x_i - x*_i|':>19} {'solve s':>9}")
    for m in (50, 200, 1000, 3000):
        xi = draw(m, 7000 + m)
        t0 = time.perf_counter()
        val, xm, _ = saa(xi)
        dt = time.perf_counter() - t0
        gap = max(abs(xm[i] - star[i]) for i in range(N))
        print(f"{m:>7} {val:>12.6f} {exact_cost(xm):>18.6f} {gap:>19.6f} "
              f"{dt:>9.3f}")
    print("\nSAA value is the in-sample average and is optimistically biased;")
    print("the third column evaluates the SAA order quantity against the true")
    print("expectation, which is the honest out-of-sample number.")

    print("\n" + "-" * 74)
    print("PART 3: THE BAND CONSTRAINT (1-rho) xi_i <= x_i <= (1+rho) xi_i")
    print("-" * 74)
    rs = rho_star()
    print("support is the box, so min_xi xi_i = lo_i and max_xi xi_i = hi_i")
    print("robust reduction gives (1-rho) hi_i <= x_i <= (1+rho) lo_i")
    print("which is nonempty only if rho >= (hi_i - lo_i)/(hi_i + lo_i)")
    print(f"\n{'i':>3} {'lo_i':>7} {'hi_i':>7} {'rho*_i':>9}")
    for i in range(N):
        print(f"{i+1:>3} {lo[i]:>7.1f} {hi[i]:>7.1f} {rs[i]:>9.4f}")
    print(f"\nbinding threshold rho* = max_i rho*_i = {max(rs):.4f} "
          f"(product {int(np.argmax(rs))+1})")

    xi = draw(1000, 991)
    print(f"\n{'rho':>6} {'status':>12} {'SAA value':>12}  x")
    for rho in (0.30, max(rs) - 1e-4, max(rs) + 1e-4, 0.45, 0.60, 0.90):
        val, xv, st = saa(xi, band=(rho, lo, hi))
        if val is None:
            print(f"{rho:>6.4f} {st:>12} {'--':>12}")
        else:
            print(f"{rho:>6.4f} {st:>12} {val:>12.6f}  "
                  f"{[round(v, 3) for v in xv]}")
    print("\nBelow rho* the feasible set is empty, which is the model telling")
    print("you the band is narrower than the spread of demand it must cover.")
