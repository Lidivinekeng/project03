import itertools

import numpy as np

from p2_colgen import M, N, make_instance, master, price


def knapsack(value, weight, cap):
    n = len(value)
    f = np.zeros((n + 1, cap + 1))
    for i in range(1, n + 1):
        w, v = weight[i - 1], value[i - 1]
        for cpt in range(cap + 1):
            f[i, cpt] = f[i - 1, cpt]
            if w <= cpt:
                f[i, cpt] = max(f[i, cpt], v + f[i - 1, cpt - w])
    take = np.zeros(n)
    cpt = cap
    for i in range(n, 0, -1):
        if f[i, cpt] != f[i - 1, cpt]:
            take[i - 1] = 1.0
            cpt -= weight[i - 1]
    return f, take


def price_dp(j, pi, mu, a, b, c):
    value = pi - c[:, j]
    f, take = knapsack(value, a.astype(int), int(b))
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
    print(f"table size (n+1)(W+1) = {(N + 1) * (int(b) + 1)} cells"
          f"   vs 2^{N} = {2 ** N} subsets by enumeration")

    cols = {(j, 0): np.zeros(N) for j in range(M)}
    nxt = {j: 1 for j in range(M)}
    agree = mismatch = 0
    shown = False
    for t in range(60):
        z, pi, mu, art = master(cols, a, b, c)
        new, added = [], 0
        for j in range(M):
            rc_g, patt_g = price(j, pi, mu, a, b, c)
            rc_d, patt_d, f = price_dp(j, pi, mu, a, b, c)
            rc_b, _ = brute(pi - c[:, j], a, b)
            ok = abs(rc_g - rc_d) < 1e-7 and abs(-rc_b - mu[j] - rc_d) < 1e-7
            agree += ok
            mismatch += not ok
            if not shown and t == 4 and j == 0:
                print(f"\nDP table at iteration {t}, agent {j}")
                print("values  pi_i - c_i0 =",
                      np.round(pi - c[:, j], 3))
                print("weights a_i         =", a.astype(int))
                print("\n  i\\c " + "".join(f"{x:>7}"
                                           for x in range(int(b) + 1)))
                for i in range(N + 1):
                    print(f"{i:>5} " + "".join(f"{f[i, x]:>7.2f}"
                                               for x in range(int(b) + 1)))
                print("backtracked pattern =", patt_d.astype(int))
                print("Gurobi  pattern     =", patt_g.astype(int))
                shown = True
            if rc_d < -1e-7:
                if not any(np.array_equal(patt_d, cols[j, k])
                           for (jj, k) in cols if jj == j):
                    new.append((j, patt_d))
                    added += 1
        if added == 0:
            break
        for j, patt in new:
            cols[j, nxt[j]] = patt
            nxt[j] += 1

    z_final, _, _, art = master(cols, a, b, c)
    print(f"\npricing calls checked        : {agree + mismatch}")
    print(f"DP = Gurobi = brute force    : {agree}")
    print(f"disagreements                : {mismatch}")
    print(f"column generation optimum    = {z_final:.6f}")
    print(f"artificials driven to zero   : {art < 1e-7}")
