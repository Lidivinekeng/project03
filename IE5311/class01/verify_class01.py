"""
IE 5311-001 Principles of Optimization, Fall 2026, Ningji Wei.
Numerical verification of the two self-check problems on slide 7.

The code checks the hand solutions written in notes_class01.txt.
Code does not replace the proofs. This course weights deep method
understanding at 60 percent (slide 6), so the proof is the deliverable
and this file is the safety net.
"""

import numpy as np

TOL = 1e-12


# ----------------------------------------------------------------------
# Slide 7, problem 1.
# Vector space: real polynomials of degree at most 2.
# B1 = {1, x, x^2}           B2 = {1+x, x+x^2, 1+x^2}
# p(x) = 3 + 5x + 4x^2
# Hand answer: [p]_B1 = (3, 5, 4),  [p]_B2 = (2, 3, 1)
#
# Representation: a polynomial a0 + a1*x + a2*x^2 is stored as the
# array [a0, a1, a2], which is precisely its B1 coordinate vector.
# ----------------------------------------------------------------------
def problem_1():
    p_in_B1 = np.array([3.0, 5.0, 4.0])

    # Columns of M are the B2 basis polynomials written in B1 coordinates.
    M = np.array([[1.0, 0.0, 1.0],    # constant terms of 1+x, x+x^2, 1+x^2
                  [1.0, 1.0, 0.0],    # x terms
                  [0.0, 1.0, 1.0]])   # x^2 terms

    det = np.linalg.det(M)
    # A nonzero determinant proves B2 is a basis, not merely a spanning set.
    assert abs(det) > TOL, "B2 is not a basis"

    # M @ [p]_B2 = [p]_B1, so solve for the B2 coordinates.
    p_in_B2 = np.linalg.solve(M, p_in_B1)

    print("PROBLEM 1, coordinates under two bases")
    print("-" * 58)
    print(f"  det(M) = {det:.4f}  (nonzero, so B2 is a basis)")
    print(f"  [p]_B1 = ({p_in_B1[0]:.0f}, {p_in_B1[1]:.0f}, {p_in_B1[2]:.0f})")
    print(f"  [p]_B2 = ({p_in_B2[0]:.0f}, {p_in_B2[1]:.0f}, {p_in_B2[2]:.0f})")

    # Independent check: rebuild p by expanding the B2 combination.
    B2 = {"1+x": np.array([1.0, 1.0, 0.0]),
          "x+x^2": np.array([0.0, 1.0, 1.0]),
          "1+x^2": np.array([1.0, 0.0, 1.0])}
    rebuilt = sum(c * v for c, v in zip(p_in_B2, B2.values()))
    print(f"  expansion rebuilds p: {np.allclose(rebuilt, p_in_B1)}")

    # Third check: evaluate both forms at several points of x.
    def evaluate(coeffs, x):
        return coeffs[0] + coeffs[1] * x + coeffs[2] * x ** 2

    xs = np.linspace(-3, 3, 13)
    direct = evaluate(p_in_B1, xs)
    via_B2 = (p_in_B2[0] * (1 + xs)
              + p_in_B2[1] * (xs + xs ** 2)
              + p_in_B2[2] * (1 + xs ** 2))
    print(f"  both forms agree at 13 values of x: {np.allclose(direct, via_B2)}")

    assert np.allclose(p_in_B2, [2.0, 3.0, 1.0])
    print("  matches the hand answer (2, 3, 1)\n")


# ----------------------------------------------------------------------
# Slide 7, problem 2.
# Claim: for any real matrix A,  ker(A^T A) = ker(A).
#
# A proof appears in the notes. Here the claim is stress tested on
# random matrices of assorted shapes and ranks, including rank
# deficient ones, by comparing kernel dimensions and kernel bases.
# Equal dimension alone is weak evidence, so the test also confirms
# every basis vector of ker(A^T A) lies in ker(A).
# ----------------------------------------------------------------------
def kernel_basis(matrix, tol=1e-9):
    """Orthonormal basis of the null space, from the SVD."""
    _, singular, vt = np.linalg.svd(matrix)
    rank = int((singular > tol * max(matrix.shape) * max(singular.max(), 1)).sum())
    return vt[rank:].T


def problem_2():
    print("PROBLEM 2, ker(A^T A) = ker(A) over the reals")
    print("-" * 58)
    rng = np.random.default_rng(5311)
    shapes = [(3, 3), (5, 3), (3, 5), (8, 4), (2, 7), (6, 6)]
    all_ok = True

    print(f"  {'shape':>8}  {'rank A':>7}  {'dim ker A':>10}"
          f"  {'dim ker AtA':>12}  {'bases agree':>12}")
    for m, n in shapes:
        A = rng.standard_normal((m, n))
        if m >= 3 and n >= 3:
            A[:, -1] = A[:, 0] + A[:, 1]      # force a rank deficiency

        AtA = A.T @ A
        kA = kernel_basis(A)
        kAtA = kernel_basis(AtA)

        # Every vector in ker(A^T A) must be killed by A as well.
        agree = (kA.shape[1] == kAtA.shape[1]
                 and (kAtA.shape[1] == 0 or np.allclose(A @ kAtA, 0, atol=1e-8)))
        all_ok &= agree
        print(f"  {str((m, n)):>8}  {np.linalg.matrix_rank(A):>7}"
              f"  {kA.shape[1]:>10}  {kAtA.shape[1]:>12}  {str(agree):>12}")

    print(f"\n  identity holds on every real test case: {all_ok}")
    assert all_ok

    # The complex case, with the plain transpose, breaks the identity.
    A = np.array([[1 + 0j], [0 + 1j]])        # 2 by 1
    AtA = A.T @ A                             # plain transpose on purpose
    x = np.array([1 + 0j])
    print("\n  complex counterexample, A = [1, i]^T, plain transpose:")
    print(f"    A^T A       = {AtA.ravel()[0]}  (zero)")
    print(f"    A x         = {(A @ x).ravel()}  (nonzero)")
    print(f"    so ker(A^T A) = C while ker(A) = {{0}}: identity fails")
    print(f"    conjugate transpose repairs it, A* A = "
          f"{(A.conj().T @ A).ravel()[0]}\n")
    assert np.allclose(AtA, 0) and not np.allclose(A @ x, 0)


if __name__ == "__main__":
    problem_1()
    problem_2()
    print("All checks passed.")
