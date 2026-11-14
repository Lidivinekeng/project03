import numpy as np

TOL = 1e-9


def simplex(A, b, c, log=False, max_iter=10000):
    A = np.asarray(A, dtype=float)
    b = np.asarray(b, dtype=float)
    c = np.asarray(c, dtype=float)
    m, n = A.shape

    T = np.hstack([A, np.eye(m)])
    cost = np.concatenate([c, np.zeros(m)])
    basis = list(range(n, n + m))
    nonbasis = list(range(n))

    it = 0
    while it < max_iter:
        AB = T[:, basis]
        xB = np.linalg.solve(AB, b)
        y = np.linalg.solve(AB.T, cost[basis])
        red = {j: cost[j] - y @ T[:, j] for j in nonbasis}
        obj = cost[basis] @ xB

        if log:
            report(it, basis, nonbasis, AB, xB, red, obj, n, m)

        pos = [j for j in nonbasis if red[j] > TOL]
        if not pos:
            if log:
                print("    all reduced costs <= 0: OPTIMAL\n")
            x = np.zeros(n + m)
            x[basis] = xB
            return x[:n], obj, it, "optimal"

        best = max(red[j] for j in pos)
        q = min(j for j in pos if red[j] > best - TOL)

        d = np.linalg.solve(AB, T[:, q])
        if np.all(d <= TOL):
            return None, np.inf, it, "unbounded"

        ratios = [(xB[i] / d[i], basis[i], i) for i in range(m) if d[i] > TOL]
        theta, leaving, r = min(ratios)

        if log:
            print(f"    entering  : {name(q, n)}  (reduced cost "
                  f"{red[q]:+.4f})")
            print(f"    direction : {np.round(d, 4)}")
            print("    ratio test:", ", ".join(
                f"{name(basis[i], n)}: {xB[i]:.4f}/{d[i]:.4f}"
                f" = {xB[i]/d[i]:.4f}"
                for i in range(m) if d[i] > TOL))
            print(f"    leaving   : {name(leaving, n)}   step size "
                  f"theta = {theta:.4f}")
            nxt = list(basis)
            nxt[r] = q
            print(f"    new basis : {[name(j, n) for j in sorted(nxt)]}\n")

        basis[r] = q
        nonbasis = sorted(set(range(n + m)) - set(basis))
        it += 1

    return None, np.nan, it, "iteration limit"


def name(j, n):
    return f"x{j + 1}"


def report(it, basis, nonbasis, AB, xB, red, obj, n, m):
    print(f"--- iteration {it} " + "-" * 52)
    print(f"    B = {[name(j, n) for j in basis]}   "
          f"N = {[name(j, n) for j in nonbasis]}")
    print("    A_B =")
    for row in AB:
        print("        [" + "  ".join(f"{v:5.2f}" for v in row) + "]")
    print("    x_B = " + ", ".join(
        f"{name(j, n)} = {v:.4f}" for j, v in zip(basis, xB)))
    print("    x_N = " + ", ".join(f"{name(j, n)} = 0" for j in nonbasis))
    print(f"    objective = {obj:.4f}")
    print("    reduced costs: " + ", ".join(
        f"{name(j, n)}: {red[j]:+.4f}" for j in nonbasis))


if __name__ == "__main__":
    A = [[1, 0, 0],
         [1, 1, 0],
         [1, 1, 1]]
    b = [4, 8, 12]
    c = [3, 2, 1]

    print("=" * 70)
    print("PROBLEM 1 PART 1: manual simplex, verified")
    print("=" * 70)
    print("max  3x1 + 2x2 + x3")
    print("s.t. x1            <= 4")
    print("     x1 + x2       <= 8")
    print("     x1 + x2 + x3  <= 12")
    print("     x >= 0        slacks x4, x5, x6\n")

    x, obj, iters, status = simplex(A, b, c, log=True)
    print("=" * 70)
    print(f"status    : {status}")
    print(f"iterations: {iters}")
    print(f"x*        : {np.round(x, 6)}")
    print(f"objective : {obj:.6f}")
