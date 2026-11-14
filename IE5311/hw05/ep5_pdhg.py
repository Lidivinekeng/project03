import numpy as np

from p1_benchmark import SEED, instance
from p1_simplex import simplex

TOLS = [1e-4, 1e-6, 1e-8]
MAXIT = 400000


def residuals(A, b, c, x, y):
    px = np.linalg.norm(np.maximum(A @ x - b, 0)) / (1 + np.linalg.norm(b))
    dy = np.linalg.norm(np.maximum(c - A.T @ y, 0)) / (1 + np.linalg.norm(c))
    p, d = c @ x, b @ y
    gap = abs(p - d) / (1 + abs(p) + abs(d))
    return max(px, dy, gap)


def pdhg(A, b, c, restart=0):
    m, n = A.shape
    eta = 0.9 / np.linalg.norm(A, 2)
    tau = sigma = eta
    x = np.zeros(n)
    y = np.zeros(m)
    sx = np.zeros(n)
    sy = np.zeros(m)
    cyc = 0
    hit = {}
    for k in range(1, MAXIT + 1):
        xn = np.maximum(x - tau * (-c + A.T @ y), 0.0)
        y = np.maximum(y + sigma * (A @ (2 * xn - x) - b), 0.0)
        x = xn
        sx += x
        sy += y
        cyc += 1
        if restart and cyc >= restart:
            x = sx / cyc
            y = sy / cyc
            sx = np.zeros(n)
            sy = np.zeros(m)
            cyc = 0
        if k % 25 == 0 or k == 1:
            r = residuals(A, b, c, sx / cyc if cyc else x, sy / cyc if cyc else y)
            for t in TOLS:
                if t not in hit and r <= t:
                    hit[t] = k
            if len(hit) == len(TOLS):
                break
    return hit


if __name__ == "__main__":
    rng = np.random.default_rng(SEED)
    print("=" * 78)
    print("EP5: PDHG on the Problem 1 benchmark instances")
    print("=" * 78)
    print("iterations to reach max(primal res, dual res, rel gap) <= tol")
    print(f"{'n':>4} {'m':>4} {'simplex':>8} | "
          f"{'plain 1e-4':>11} {'1e-6':>8} {'1e-8':>8} | "
          f"{'rs 1e-4':>9} {'1e-6':>8} {'1e-8':>8}")
    for (n, m) in [(5, 3), (10, 5), (20, 10), (50, 20), (100, 40)]:
        A, b, c = instance(n, m, rng)
        _, obj, it, st = simplex(A, b, c)
        pl = pdhg(A, b, c, restart=0)
        rs = pdhg(A, b, c, restart=100)
        def f(d, t):
            return str(d[t]) if t in d else ">" + str(MAXIT)
        print(f"{n:>4} {m:>4} {it:>8} | "
              f"{f(pl,1e-4):>11} {f(pl,1e-6):>8} {f(pl,1e-8):>8} | "
              f"{f(rs,1e-4):>9} {f(rs,1e-6):>8} {f(rs,1e-8):>8}")
