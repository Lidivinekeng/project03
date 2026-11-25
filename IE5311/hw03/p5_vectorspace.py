import numpy as np

NAMES_B = ["1", "sin x", "cos x"]
NAMES_BP = ["1 + sin x", "sin x + cos x", "1 + cos x"]


def evaluate(coef, xs):
    a, b, c = coef
    return a + b * np.sin(xs) + c * np.cos(xs)


def eval_matrix(xs):
    return np.column_stack([np.ones_like(xs), np.sin(xs), np.cos(xs)])


M_BP = np.array([[1.0, 0.0, 1.0],
                 [1.0, 1.0, 0.0],
                 [0.0, 1.0, 1.0]])

T_B = np.array([[0.0, 0.0, 0.0],
                [0.0, 0.0, -1.0],
                [0.0, 1.0, 0.0]])


if __name__ == "__main__":
    print("=" * 78)
    print("PROBLEM 5: THE FUNCTION SPACE V = span{1, sin x, cos x}")
    print("=" * 78)

    print("\n" + "-" * 78)
    print("PART 1: B = {1, sin x, cos x} IS A BASIS, dim V = 3")
    print("-" * 78)
    pts = np.array([0.0, np.pi / 2, np.pi])
    E = eval_matrix(pts)
    print("evaluation at x = 0, pi/2, pi gives the matrix")
    for r, x in zip(E, pts):
        print(f"  x = {x:7.4f} -> {np.round(r, 6)}")
    print(f"determinant = {np.linalg.det(E):.6f}, nonzero, so a vanishing")
    print("combination must have zero coefficients: B is independent")
    print("spanning holds by the definition of V, so dim(V) = 3")
    rng = np.random.default_rng(5311)
    worst = 0.0
    for _ in range(20000):
        co = rng.uniform(-5, 5, 3)
        sol = np.linalg.solve(E, evaluate(co, pts))
        worst = max(worst, float(np.abs(sol - co).max()))
    print(f"recovering coefficients from three evaluations, worst error "
          f"{worst:.2e}")

    print("\n" + "-" * 78)
    print("PART 2: IS B' A BASIS?")
    print("-" * 78)
    print("columns are the B-coordinates of 1+sin, sin+cos, 1+cos")
    for r in M_BP:
        print("  " + str(np.round(r, 3)))
    det = float(np.linalg.det(M_BP))
    print(f"determinant = {det:.6f}")
    print(f"independent : {abs(det) > 1e-12}")
    print(f"three independent vectors in a 3-dimensional space also span,")
    print(f"so B' is a basis : {abs(det) > 1e-12}")

    print("\n" + "-" * 78)
    print("PART 3: COORDINATES OF f(x) = 2 + 3 sin x - cos x")
    print("-" * 78)
    f_B = np.array([2.0, 3.0, -1.0])
    f_BP = np.linalg.solve(M_BP, f_B)
    print(f"[f]_B  = {np.round(f_B, 6)}   over {NAMES_B}")
    print(f"[f]_B' = {np.round(f_BP, 6)}   over {NAMES_BP}")
    xs = np.linspace(-2 * np.pi, 2 * np.pi, 4001)
    lhs = evaluate(f_B, xs)
    rhs = (f_BP[0] * (1 + np.sin(xs)) + f_BP[1] * (np.sin(xs) + np.cos(xs))
           + f_BP[2] * (1 + np.cos(xs)))
    print(f"the two expansions agree pointwise, worst gap over 4001 values "
          f"of x: {float(np.abs(lhs - rhs).max()):.2e}")

    print("\n" + "-" * 78)
    print("PART 4: T(f) = f' IS LINEAR, AND MAPS V INTO V")
    print("-" * 78)
    print("matrix of T in the basis B, columns are T(1), T(sin), T(cos)")
    for r in T_B:
        print("  " + str(np.round(r, 3)))
    print("so T(1) = 0, T(sin x) = cos x, T(cos x) = -sin x, all in V")
    worst = 0.0
    for _ in range(20000):
        f, g = rng.uniform(-5, 5, 3), rng.uniform(-5, 5, 3)
        lam, mu = rng.uniform(-3, 3, 2)
        worst = max(worst, float(np.abs(
            T_B @ (lam * f + mu * g) - (lam * (T_B @ f) + mu * (T_B @ g))
        ).max()))
    print(f"T(lam f + mu g) = lam T(f) + mu T(g), worst error over 20000 "
          f"random cases: {worst:.2e}")
    h = 1e-6
    num = 0.0
    for _ in range(2000):
        co = rng.uniform(-5, 5, 3)
        x0 = float(rng.uniform(-np.pi, np.pi))
        fd = (evaluate(co, np.array([x0 + h])) - evaluate(
            co, np.array([x0 - h]))) / (2 * h)
        num = max(num, abs(float(fd[0]) - float(evaluate(T_B @ co,
                                                         np.array([x0]))[0])))
    print(f"the matrix really is differentiation, worst gap against a central "
          f"difference: {num:.2e}")

    print("\n" + "-" * 78)
    print("PART 5: ker(T) AND range(T)")
    print("-" * 78)
    U, sv, Vt = np.linalg.svd(T_B)
    rank = int((sv > 1e-10).sum())
    ker = Vt[rank:].T
    print(f"singular values {np.round(sv, 6)}, rank {rank}, nullity "
          f"{3 - rank}")
    print(f"ker(T) = {{f : f' = 0}} = constants = span{{1}}")
    print(f"  basis {{1}}, dim ker(T) = {3 - rank}")
    print(f"  null space direction from the SVD: "
          f"{np.round(np.abs(ker[:, 0]), 6)}  (the 1-coordinate)")
    print(f"range(T) = span{{sin x, cos x}}")
    print(f"  basis {{sin x, cos x}}, dim range(T) = {rank}")
    print(f"  T(sin) = cos and T(cos) = -sin, so both are attained")

    print("\n" + "-" * 78)
    print("PART 6: RANK-NULLITY")
    print("-" * 78)
    print(f"dim V = 3,  dim ker(T) = {3 - rank},  dim range(T) = {rank}")
    print(f"{3 - rank} + {rank} = {3 - rank + rank}, equals dim V : "
          f"{3 - rank + rank == 3}")
