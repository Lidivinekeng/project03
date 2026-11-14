import itertools
import time

import numpy as np

from p2_colgen import M, N, make_instance, master, price


def knapsack(value, weight, cap):
    n = len(value)
    f = np.zeros((n + 1, cap + 1))
    for i in range(1, n + 1):
        w, v = int(weight[i - 1]), value[i - 1]
        f[i] = f[i - 1]
        if w <= cap:
            f[i, w:] = np.maximum(f[i - 1, w:], v + f[i - 1, :cap + 1 - w])
    take = np.zeros(n)
    cpt = cap
    for i in range(n, 0, -1):
        if f[i, cpt] != f[i - 1, cpt]:
            take[i - 1] = 1.0
            cpt -= int(weight[i - 1])
    return f, take


def price_dp(j, pi, mu, a, b, c):
    f, take = knapsack(pi - c[:, j], a.astype(int), int(b))
    return -f[N, int(b)] - mu[j], take, f


def brute(value, weight, cap):
    best, arg = 0.0, np.zeros(len(value))
    for bits in itertools.product([0, 1], repeat=len(value)):
        y = np.array(bits, dtype=float)
        if weight @ y <= cap + 1e-9 and value @ y > best + 1e-12:
            best, arg = value @ y, y
    return best, arg


if __name__ == "__main__":
    a, b, c = make_instance()
    print("=" * 74)
    print("EP7: the pricing subproblem solved by dynamic programming")
    print("=" * 74)
    print(f"a = {a.astype(int)}   b = {int(b)}")
    print(f"table (n+1)(W+1) = {(N + 1) * (int(b) + 1)} cells"
          f"   vs 2^{N} = {2 ** N} subsets by enumeration")

    cols = {(j, 0): np.zeros(N) for j in range(M)}
    nxt = {j: 1 for j in range(M)}
    agree = mismatch = 0
    t_dp = t_gb = 0.0
    for t in range(60):
        z, pi, mu, art = master(cols, a, b, c)
        new, added = [], 0
        for j in range(M):
            t0 = time.perf_counter()
            rc_g, patt_g = price(j, pi, mu, a, b, c)
            t_gb += time.perf_counter() - t0
            t0 = time.perf_counter()
            rc_d, patt_d, _ = price_dp(j, pi, mu, a, b, c)
            t_dp += time.perf_counter() - t0
            rc_b, _ = brute(pi - c[:, j], a, b)
            ok = (abs(rc_g - rc_d) < 1e-7
                  and abs(-rc_b - mu[j] - rc_d) < 1e-7)
            agree += ok
            mismatch += not ok
            if rc_d < -1e-7 and not any(np.array_equal(patt_d, cols[j, k])
                                        for (jj, k) in cols if jj == j):
                new.append((j, patt_d))
                added += 1
        if added == 0:
            break
        for j, patt in new:
            cols[j, nxt[j]] = patt
            nxt[j] += 1

    z_final, _, _, art = master(cols, a, b, c)
    n_calls = agree + mismatch
    print(f"\npricing calls checked        : {n_calls}")
    print(f"DP = Gurobi = brute force    : {agree}")
    print(f"disagreements                : {mismatch}")
    print(f"column generation optimum    = {z_final:.6f}")
    print(f"artificials driven to zero   : {art < 1e-7}")
    print(f"\ntotal pricing time, Gurobi   : {1e3 * t_gb:8.1f} ms"
          f"  ({1e3 * t_gb / n_calls:.3f} ms per call)")
    print(f"total pricing time, DP       : {1e3 * t_dp:8.1f} ms"
          f"  ({1e3 * t_dp / n_calls:.3f} ms per call)")
    print(f"speedup                      : {t_gb / t_dp:8.1f}x")

    print("\n" + "-" * 74)
    print("where the DP stops winning: scale the weights and capacity")
    print("-" * 74)
    pi = np.array([21.667, -14.0, -1.333, -5.667, -0.333, 7.333, 7.667])
    print(f"{'scale':>7} {'W':>9} {'cells':>11} {'DP (ms)':>10} "
          f"{'Gurobi (ms)':>12}")
    for s in [1, 10, 100, 1000, 10000]:
        aa, bb = a * s, b * s
        t0 = time.perf_counter()
        for _ in range(5):
            knapsack(pi, aa.astype(int), int(bb))
        td = (time.perf_counter() - t0) / 5
        t0 = time.perf_counter()
        for _ in range(5):
            price(0, pi + c[:, 0], np.zeros(M), aa, bb, c)
        tg = (time.perf_counter() - t0) / 5
        print(f"{s:>7} {int(bb):>9} {(N + 1) * (int(bb) + 1):>11} "
              f"{1e3 * td:>10.2f} {1e3 * tg:>12.2f}")
