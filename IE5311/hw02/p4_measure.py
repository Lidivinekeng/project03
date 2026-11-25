import itertools

import numpy as np

OMEGA = frozenset({1, 2, 3, 4})
F0 = [frozenset({1}), frozenset({3, 4})]


def generated_sigma_algebra(omega, gens):
    F = {frozenset(), frozenset(omega)}
    F.update(gens)
    while True:
        new = set(F)
        for A in F:
            new.add(frozenset(omega) - A)
        for A, B in itertools.combinations(F, 2):
            new.add(A | B)
        if new == F:
            return F
        F = new


def is_sigma_algebra(F, omega):
    F = set(F)
    if frozenset() not in F:
        return False, "empty set missing"
    for A in F:
        if frozenset(omega) - A not in F:
            return False, f"complement of {sorted(A)} missing"
    for A, B in itertools.combinations(F, 2):
        if A | B not in F:
            return False, f"union {sorted(A)} u {sorted(B)} missing"
    return True, "closed under complement and finite union"


def atoms_of(F, omega):
    out = []
    for w in sorted(omega):
        cell = frozenset(omega)
        for A in F:
            if w in A:
                cell = cell & A
        if cell not in out:
            out.append(cell)
    return out


def show(F):
    return sorted((sorted(A) for A in F), key=lambda s: (len(s), s))


if __name__ == "__main__":
    print("=" * 74)
    print("PROBLEM 4: SIGMA-ALGEBRAS AND PUSHFORWARD MEASURES")
    print("=" * 74)

    print("\n" + "-" * 74)
    print("PART 2: THE SMALLEST SIGMA-ALGEBRA CONTAINING F0")
    print("-" * 74)
    print(f"Omega = {sorted(OMEGA)}")
    print(f"F0    = {[sorted(A) for A in F0]}")
    F = generated_sigma_algebra(OMEGA, F0)
    print(f"\nsigma(F0) has {len(F)} members:")
    for A in show(F):
        print(f"   {A}")
    ok, why = is_sigma_algebra(F, OMEGA)
    print(f"\nclosure check : {ok} ({why})")
    print(f"atoms         : {[sorted(a) for a in atoms_of(F, OMEGA)]}")
    print(f"size is 2^(number of atoms) : "
          f"{len(F) == 2 ** len(atoms_of(F, OMEGA))}")
    print("\n{3} is not a member, so F0 cannot tell 3 and 4 apart. The atoms")
    print("are the finest distinctions the generators can make, and every")
    print("member of sigma(F0) is a union of them.")

    print("\n" + "-" * 74)
    print("PART 3: CLOSURE UNDER COUNTABLE INTERSECTIONS")
    print("-" * 74)
    bad = [(sorted(A), sorted(B)) for A, B in itertools.combinations(F, 2)
           if (A & B) not in F]
    print("the proof is De Morgan: inter_k A_k = (union_k A_k^c)^c")
    print(f"pairwise intersections outside sigma(F0) : {len(bad)}")
    comp = {A: frozenset(OMEGA) - A for A in F}
    manual = all((frozenset(OMEGA) - (comp[A] | comp[B])) == (A & B)
                 for A, B in itertools.combinations(F, 2))
    print(f"De Morgan verified on every pair in sigma(F0) : {manual}")

    print("\n" + "-" * 74)
    print("PART 4: PUSHFORWARD OF Unif[-1,1] UNDER X(xi) = xi^2")
    print("-" * 74)
    rng = np.random.default_rng(5311)
    M = 4_000_000
    xi = rng.uniform(-1.0, 1.0, M)
    X = xi ** 2

    print(f"support of P_X should be [0,1]; sample range "
          f"[{X.min():.6f}, {X.max():.6f}]")

    grid = np.linspace(0.0, 1.0, 21)
    print(f"\n{'t':>6} {'empirical F(t)':>16} {'sqrt(t)':>10} {'abs diff':>10}")
    worst = 0.0
    for t in grid:
        emp = float((X <= t).mean())
        th = float(np.sqrt(t))
        worst = max(worst, abs(emp - th))
        print(f"{t:>6.2f} {emp:>16.6f} {th:>10.6f} {abs(emp-th):>10.6f}")
    print(f"\nworst deviation over the grid : {worst:.6f} "
          f"(Monte Carlo error at M = {M:,} is about "
          f"{1/np.sqrt(M):.6f})")

    print("\npre-image check, X^-1([0,t]) = [-sqrt(t), sqrt(t)]")
    for t in (0.25, 0.49, 0.81):
        lhs = float((X <= t).mean())
        rhs = float(((xi >= -np.sqrt(t)) & (xi <= np.sqrt(t))).mean())
        print(f"  t = {t:.2f} : P(X <= t) = {lhs:.6f}, "
              f"P(-sqrt t <= xi <= sqrt t) = {rhs:.6f}, equal: "
              f"{abs(lhs-rhs) < 1e-12}")

    print("\ndensity f_X(t) = 1/(2 sqrt(t)) on (0,1), checked by moments")
    for k, exact, name in ((1, 1 / 3, "E[X]"), (2, 1 / 5, "E[X^2]"),
                           (3, 1 / 7, "E[X^3]")):
        emp = float((X ** k).mean())
        print(f"  {name:>7} : empirical {emp:.6f}, exact "
              f"{exact:.6f}, diff {abs(emp-exact):.6f}")
    print("  exact values are integral_0^1 t^k /(2 sqrt t) dt = 1/(2k+1)")

    edges = np.linspace(0.02, 1.0, 15)
    print(f"\n{'bin':>14} {'empirical density':>18} {'1/(2 sqrt t)':>14}")
    for a, bb in zip(edges[:-1], edges[1:]):
        mid = 0.5 * (a + bb)
        dens = float(((X >= a) & (X < bb)).mean()) / (bb - a)
        print(f"[{a:.3f},{bb:.3f}) {dens:>18.4f} {1/(2*np.sqrt(mid)):>14.4f}")
    print("\nThe density is unbounded as t -> 0 but integrable, which is why")
    print("the CDF sqrt(t) has infinite slope at the origin.")
