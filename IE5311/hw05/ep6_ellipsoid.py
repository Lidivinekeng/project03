import numpy as np

A = np.array([[1.0, 0.0, 0.0], [1.0, 1.0, 0.0], [1.0, 1.0, 1.0]])
b = np.array([4.0, 8.0, 12.0])
c = np.array([3.0, 2.0, 1.0])
ZSTAR = 24.0
MAXIT = 200000


def oracle(z, target):
    v = A @ z - b
    k = int(np.argmax(v))
    if v[k] > 1e-12:
        return A[k]
    k = int(np.argmin(z))
    if z[k] < -1e-12:
        return -np.eye(len(z))[k]
    if c @ z < target - 1e-12:
        return -c
    return None


def ellipsoid(target, z0, r0):
    n = len(z0)
    z = z0.astype(float).copy()
    Q = (r0 ** 2) * np.eye(n)
    logdet0 = n * np.log(r0 ** 2)
    for k in range(1, MAXIT + 1):
        d = oracle(z, target)
        if d is None:
            s = np.linalg.slogdet(Q)[1]
            return k, z, np.exp((s - logdet0) / (2 * (k - 1)))
        q = Q @ d
        den = np.sqrt(d @ q)
        if den <= 0 or not np.isfinite(den):
            return -k, z, float("nan")
        g = q / den
        z = z - g / (n + 1)
        Q = (n ** 2 / (n ** 2 - 1)) * (Q - (2.0 / (n + 1)) * np.outer(g, g))
        Q = (Q + Q.T) / 2
    return -MAXIT, z, float("nan")


if __name__ == "__main__":
    n = 3
    print("=" * 74)
    print("EP6: the ellipsoid method on the Problem 1 LP")
    print("=" * 74)
    bound = np.exp(-1 / (2 * (n + 1)))
    exact = ((n ** 2 / (n ** 2 - 1)) ** n * (n - 1) / (n + 1)) ** 0.5
    print(f"standard bound  exp(-1/(2(n+1)))        = {bound:.6f}")
    print(f"exact ratio     [(n^2/(n^2-1))^n (n-1)/(n+1)]^(1/2) "
          f"= {exact:.6f}   (n = {n})")
    print("the update is deterministic in volume, so the exact ratio is")
    print("attained at every step, whatever the cut; the bound is loose.")
    print("\nfinding a point with c'x >= z* - delta, from a ball of radius 20")
    print(f"{'delta':>8} {'oracle calls':>13} {'c^T x found':>13} "
          f"{'obs. ratio/step':>16}")
    for delta in [1.0, 1e-1, 1e-2, 1e-3, 1e-4]:
        k, z, ratio = ellipsoid(ZSTAR - delta, np.full(n, 6.0), 20.0)
        tag = str(k) if k > 0 else f"FAILED@{-k}"
        print(f"{delta:>8.0e} {tag:>13} {c @ z:>13.6f} {ratio:>16.6f}")
    print("\ncalls per decade of delta: vol(K) ~ delta^n, so one decade")
    print(f"costs a factor 10^{n} of volume, needing "
          f"{n * np.log(10) / -np.log(exact):.1f} steps at the exact rate")
    print(f"against {n * np.log(10) / -np.log(bound):.1f} at the bound rate.")
    print("\nfor comparison, the revised simplex of Part 2 reached the exact")
    print("optimum x* = (4,4,4), z* = 24, in 3 pivots.")
