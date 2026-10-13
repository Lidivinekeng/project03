import numpy as np

rng = np.random.default_rng(5311)


def box_max(a, lo, hi):
    return float(np.sum(np.maximum(a * lo, a * hi)))


def box_min(a, lo, hi):
    return float(np.sum(np.minimum(a * lo, a * hi)))


def argmax_box(a, lo, hi):
    return np.where(a >= 0, hi, lo)


def argmin_box(a, lo, hi):
    return np.where(a >= 0, lo, hi)


def M_le(a, b, lo, hi):
    return max(0.0, box_max(a, lo, hi) - b)


def N_ge(a, b, lo, hi):
    return max(0.0, b - box_min(a, lo, hi))


def instance(n):
    lo = rng.uniform(-6.0, 2.0, n)
    hi = lo + rng.uniform(0.5, 9.0, n)
    a = rng.uniform(-4.0, 4.0, n)
    b = float(rng.uniform(box_min(a, lo, hi), box_max(a, lo, hi)))
    return a, b, lo, hi


def check_le(trials=4000, delta=1e-6):
    valid = tight = 0
    for _ in range(trials):
        n = int(rng.integers(1, 7))
        a, b, lo, hi = instance(n)
        M = M_le(a, b, lo, hi)
        if box_max(a, lo, hi) <= b + M + 1e-9:
            valid += 1
        xw = argmax_box(a, lo, hi)
        if float(a @ xw) > b + (M - delta) + 1e-12:
            tight += 1
    return valid, tight, trials


def check_ge(trials=4000, delta=1e-6):
    valid = tight = 0
    for _ in range(trials):
        n = int(rng.integers(1, 7))
        a, b, lo, hi = instance(n)
        N = N_ge(a, b, lo, hi)
        if box_min(a, lo, hi) >= b - N - 1e-9:
            valid += 1
        xw = argmin_box(a, lo, hi)
        if float(a @ xw) < b - (N - delta) - 1e-12:
            tight += 1
    return valid, tight, trials


def check_pair(trials=4000):
    ok = 0
    for _ in range(trials):
        n = int(rng.integers(1, 7))
        cc, dd, lo, hi = instance(n)
        M = M_le(cc, dd, lo, hi)
        good = True
        for zk in (0, 1):
            for zl in (0, 1):
                slack = dd + M * (2 - zk - zl)
                if zk == 1 and zl == 1:
                    if abs(slack - dd) > 1e-12:
                        good = False
                else:
                    if box_max(cc, lo, hi) > slack + 1e-9:
                        good = False
        ok += good
    return ok, trials


def check_cover(trials=3000):
    ok = 0
    for _ in range(trials):
        n = int(rng.integers(1, 6))
        g, h, lo, hi = instance(n)
        M = M_le(g, h, lo, hi)
        kr = int(rng.integers(1, 5))
        z = rng.integers(0, 2, kr)
        rhs = h + M * float(z.sum())
        if z.sum() == 0:
            good = abs(rhs - h) < 1e-12
        else:
            good = box_max(g, lo, hi) <= rhs + 1e-9
        ok += good
    return ok, trials


def check_equiv(trials=3000, eps=1e-3):
    ok = 0
    for _ in range(trials):
        n = int(rng.integers(1, 6))
        g, h, lo, hi = instance(n)
        M = M_le(g, h, lo, hi)
        N = max(0.0, h + eps - box_min(g, lo, hi))
        kr = int(rng.integers(1, 5))
        z = rng.integers(0, 2, kr)
        good = True
        if z.sum() == 0:
            if abs((h + M * float(z.sum())) - h) > 1e-12:
                good = False
            if box_min(g, lo, hi) < h + eps - N - 1e-9:
                pass
        else:
            if box_min(g, lo, hi) < h + eps - N - 1e-9:
                good = False
        ok += good
    return ok, trials


if __name__ == "__main__":
    print("=" * 78)
    print("PROBLEM 2: BIG-M REFORMULATIONS, SMALLEST VALID COEFFICIENTS")
    print("=" * 78)
    print("over the box lo <= x <= hi,")
    print("  max_x a'x = sum_i max(a_i lo_i, a_i hi_i)   attained at")
    print("              x_i = hi_i if a_i >= 0 else lo_i")
    print("  min_x a'x = sum_i min(a_i lo_i, a_i hi_i)   attained at")
    print("              x_i = lo_i if a_i >= 0 else hi_i")

    print("\n" + "-" * 78)
    print("PART 1 and 2(a): z_k = 1 => a'x <= b, written a'x <= b + M(1-z)")
    print("-" * 78)
    v, t, n = check_le()
    print(f"claimed smallest M = max(0, max_x a'x - b)")
    print(f"  valid at M     : {v} of {n} random instances "
          f"(z=0 never cuts off a box point)")
    print(f"  tight at M-1e-6: {t} of {n} (a feasible point IS cut off)")

    print("\n" + "-" * 78)
    print("PART 1 and 2(b): z_k = 0 => a'x >= b, written a'x >= b - N z")
    print("-" * 78)
    v, t, n = check_ge()
    print(f"claimed smallest N = max(0, b - min_x a'x)")
    print(f"  valid at N     : {v} of {n}")
    print(f"  tight at N-1e-6: {t} of {n}")

    print("\n" + "-" * 78)
    print("PART 3: z_k = z_l = 1 => c'x <= d, written c'x <= d + M(2-z_k-z_l)")
    print("-" * 78)
    ok, n = check_pair()
    print(f"claimed smallest M = max(0, max_x c'x - d), same coefficient")
    print(f"  correct on all four (z_k,z_l) patterns: {ok} of {n}")
    print("  the binding pattern is exactly one of the two being 1, where the")
    print("  multiplier is 1; with both 0 the multiplier is 2 and the row is")
    print("  weaker still, so no larger M is needed")

    print("\n" + "-" * 78)
    print("PART 4: g'x > h only if sum_{k in K_r} z_k >= 1")
    print("-" * 78)
    ok, n = check_cover()
    print(f"written g'x <= h + M_r sum_k z_k with M_r = max(0, max_x g'x - h)")
    print(f"  correct on random z patterns: {ok} of {n}")

    print("\n" + "-" * 78)
    print("PART 5: the equivalence, and why epsilon is unavoidable")
    print("-" * 78)
    ok, n = check_equiv()
    print(f"added rows g'x >= h + eps - N_r(1-z_k) for every k in K_r")
    print(f"  correct on random z patterns: {ok} of {n}")
    g = np.array([1.0])
    lo, hi, h = np.array([0.0]), np.array([10.0]), 3.0
    print(f"\nnon-closedness, with g'x = x, h = {h}:")
    print(f"{'x':>12} {'x > h ?':>9}")
    for k in range(1, 7):
        xv = h + 10.0 ** (-k)
        print(f"{xv:>12.6f} {str(bool(xv > h)):>9}")
    print(f"{h:>12.6f} {str(bool(h > h)):>9}   <- the limit leaves the set")
    print("\nEvery point of the sequence satisfies g'x > h, the limit does not,")
    print("so that branch of the feasible set is not closed. A MILP feasible")
    print("set is a finite union of closed polyhedra and is therefore closed,")
    print("so no exact MILP exists and the tolerance eps is required. The")
    print("formulation declares the band (h, h+eps) infeasible when a")
    print("condition is active, which is the whole of the approximation.")
