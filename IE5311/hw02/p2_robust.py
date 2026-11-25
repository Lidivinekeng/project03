import itertools
import time

import numpy as np
import pulp

SOLVER = pulp.PULP_CBC_CMD(msg=0)

N = 3
h = [1.0, 2.0, 1.5]
b = [4.0, 3.0, 5.0]
lo = [10.0, 5.0, 8.0]
hi = [30.0, 25.0, 20.0]
TOTAL_LO = 45.0
TOTAL_HI = 60.0


def halfspaces(lo_, hi_, total_lo=None, total_hi=None):
    n = len(lo_)
    A, c = [], []
    for i in range(n):
        r = [0.0] * n
        r[i] = -1.0
        A.append(r)
        c.append(-lo_[i])
        r = [0.0] * n
        r[i] = 1.0
        A.append(r)
        c.append(hi_[i])
    if total_hi is not None:
        A.append([1.0] * n)
        c.append(total_hi)
    if total_lo is not None:
        A.append([-1.0] * n)
        c.append(-total_lo)
    return np.array(A), np.array(c)


def vertices(A, c):
    n = A.shape[1]
    out = []
    for idx in itertools.combinations(range(A.shape[0]), n):
        M = A[list(idx)]
        if abs(np.linalg.det(M)) < 1e-9:
            continue
        v = np.linalg.solve(M, c[list(idx)])
        if np.all(A @ v <= c + 1e-7):
            if not any(np.allclose(v, w, atol=1e-7) for w in out):
                out.append(v)
    return out


def cost(x, xi, hv=None, bv=None):
    hv = hv or h
    bv = bv or b
    return sum(max(hv[i] * (x[i] - xi[i]), bv[i] * (xi[i] - x[i]))
               for i in range(len(x)))


def robust_vertex_lp(V, n=N, hv=None, bv=None, band=None):
    hv = hv or h
    bv = bv or b
    M = pulp.LpProblem("robust_vertex", pulp.LpMinimize)
    x = [pulp.LpVariable(f"x_{i}", 0) for i in range(n)]
    tau = pulp.LpVariable("tau")
    t = {(k, i): pulp.LpVariable(f"t_{k}_{i}")
         for k in range(len(V)) for i in range(n)}
    M += tau
    for k, v in enumerate(V):
        M += tau >= pulp.lpSum(t[k, i] for i in range(n))
        for i in range(n):
            M += t[k, i] >= hv[i] * (x[i] - v[i])
            M += t[k, i] >= bv[i] * (v[i] - x[i])
    if band is not None:
        for i in range(n):
            M += x[i] <= (1.0 + band) * min(v[i] for v in V)
            M += x[i] >= (1.0 - band) * max(v[i] for v in V)
    t0 = time.perf_counter()
    M.solve(SOLVER)
    dt = time.perf_counter() - t0
    st = pulp.LpStatus[M.status]
    if st != "Optimal":
        return None, None, dt, st, len(M.constraints), len(M.variables())
    return (pulp.value(M.objective), [v.value() for v in x], dt, st,
            len(M.constraints), len(M.variables()))


def separate(x, A, c, n=N):
    best_val, best_v = -np.inf, None
    for sigma in itertools.product((0, 1), repeat=n):
        M = pulp.LpProblem("sep", pulp.LpMaximize)
        xi = [pulp.LpVariable(f"xi_{i}") for i in range(n)]
        M += pulp.lpSum(b[i] * (xi[i] - x[i]) if sigma[i]
                        else h[i] * (x[i] - xi[i]) for i in range(n))
        for r in range(A.shape[0]):
            M += pulp.lpSum(A[r, i] * xi[i] for i in range(n)) <= c[r]
        M.solve(SOLVER)
        if pulp.LpStatus[M.status] != "Optimal":
            continue
        v = np.array([u.value() for u in xi])
        val = cost(x, v)
        if val > best_val:
            best_val, best_v = val, v
    return best_val, best_v


def constraint_generation(A, c, start, n=N, max_rounds=200):
    W = [np.array(start)]
    t0 = time.perf_counter()
    trace = []
    for r in range(1, max_rounds + 1):
        val, x, _, st, _, _ = robust_vertex_lp(W, n)
        if st != "Optimal":
            raise RuntimeError(st)
        ub, v = separate(x, A, c, n)
        trace.append((r, len(W), val, ub))
        if ub <= val + 1e-6:
            return val, x, r, len(W), time.perf_counter() - t0, trace
        if any(np.allclose(v, w, atol=1e-7) for w in W):
            return val, x, r, len(W), time.perf_counter() - t0, trace
        W.append(v)
    raise RuntimeError("constraint generation hit the round limit")


def box_closed_form(n, hv, bv, lo_, hi_):
    x = [(hv[i] * lo_[i] + bv[i] * hi_[i]) / (hv[i] + bv[i]) for i in range(n)]
    val = sum(hv[i] * bv[i] * (hi_[i] - lo_[i]) / (hv[i] + bv[i])
              for i in range(n))
    return val, x


def box_identity_lp(n, hv, bv, lo_, hi_):
    M = pulp.LpProblem("robust_identity", pulp.LpMinimize)
    x = [pulp.LpVariable(f"x_{i}", 0) for i in range(n)]
    tau = [pulp.LpVariable(f"tau_{i}") for i in range(n)]
    M += pulp.lpSum(tau)
    for i in range(n):
        M += tau[i] >= hv[i] * (x[i] - lo_[i])
        M += tau[i] >= bv[i] * (hi_[i] - x[i])
    t0 = time.perf_counter()
    M.solve(SOLVER)
    dt = time.perf_counter() - t0
    return (pulp.value(M.objective), [v.value() for v in x], dt,
            len(M.constraints), len(M.variables()))


if __name__ == "__main__":
    A, c = halfspaces(lo, hi, TOTAL_LO, TOTAL_HI)
    V = vertices(A, c)
    xi_min = [min(v[i] for v in V) for i in range(N)]
    xi_max = [max(v[i] for v in V) for i in range(N)]

    print("=" * 74)
    print("PROBLEM 2: ROBUST MULTIDIMENSIONAL NEWSVENDOR")
    print("=" * 74)
    print(f"Xi = {{lo <= xi <= hi, {TOTAL_LO:.0f} <= sum_i xi_i <= "
          f"{TOTAL_HI:.0f}}}")
    print(f"sum lo = {sum(lo):.0f}, sum hi = {sum(hi):.0f}, so both total rows")
    print("are active somewhere and the coordinates are genuinely coupled.")
    print(f"\nextreme points: {len(V)}")
    for k, v in enumerate(V):
        print(f"  v^{k+1:<2} = {np.round(v, 3)}   sum = {v.sum():.1f}")

    print("\n" + "-" * 74)
    print("PARTS 1 and 2: THE FINITE EXTREME-POINT LP")
    print("-" * 74)
    val, x, dt, st, nc, nv = robust_vertex_lp(V)
    print(f"worst-case cost         : {val:.6f}")
    print(f"robust order quantity   : {[round(u, 4) for u in x]}")
    print(f"LP size                 : {nc} rows, {nv} columns "
          f"(K(2n+1) = {len(V)*(2*N+1)})")
    print(f"solve time              : {dt:.4f} s")
    print(f"max over vertices at x  : "
          f"{max(cost(x, v) for v in V):.6f}")

    box_bound, box_x = box_closed_form(N, h, b, xi_min, xi_max)
    print(f"\nbox bound on the coordinate ranges : {box_bound:.6f}")
    print(f"coupling is worth                  : {box_bound - val:.6f}")
    print("The coordinate ranges alone overstate the worst case, because no")
    print("single demand vector in Xi can sit at every coordinate's own worst")
    print("extreme at once. That is what the budget rows buy.")

    A_up, c_up = halfspaces(lo, hi, None, TOTAL_HI)
    V_up = vertices(A_up, c_up)
    v_up, x_up, _, _, _, _ = robust_vertex_lp(V_up)
    m_up = [min(v[i] for v in V_up) for i in range(N)]
    M_up = [max(v[i] for v in V_up) for i in range(N)]
    bb_up, _ = box_closed_form(N, h, b, m_up, M_up)
    print(f"\nFor contrast, drop the lower total row and keep only "
          f"sum xi <= {TOTAL_HI:.0f}:")
    print(f"  robust {v_up:.6f} against box bound {bb_up:.6f}, "
          f"identical: {abs(v_up - bb_up) < 1e-6}")
    print(f"  componentwise minimum {[float(v) for v in m_up]} lies in Xi: "
          f"{sum(m_up) <= TOTAL_HI}")
    print("  An upper total row never binds at the optimum, because the")
    print("  adversary can always retreat to the componentwise minimum and")
    print("  that point still satisfies it. Only a lower total row, which")
    print("  forbids that retreat, makes the coupling bite.")

    print("\n" + "-" * 74)
    print("PART 3: CONSTRAINT GENERATION WHEN THE VERTICES ARE TOO MANY")
    print("-" * 74)
    cg_val, cg_x, rounds, used, cg_dt, trace = constraint_generation(
        A, c, V[0])
    print(f"{'round':>6} {'|W|':>5} {'master (LB)':>13} {'separation (UB)':>16}")
    for r, w, lb, ub in trace:
        print(f"{r:>6} {w:>5} {lb:>13.6f} {ub:>16.6f}")
    print(f"\nrounds                  : {rounds}")
    print(f"vertices ever added     : {used} of {len(V)}")
    print(f"objective               : {cg_val:.6f}")
    print(f"matches the full LP     : {abs(cg_val - val) < 1e-6}")
    print(f"time                    : {cg_dt:.4f} s "
          f"(full LP {dt:.4f} s)")
    bad_val, _, bad_r, bad_w, _, _ = constraint_generation(A, c, xi_min)
    print(f"\nSeeded instead at the componentwise minimum, which is NOT in Xi:")
    print(f"  converges in {bad_r} rounds to {bad_val:.6f}, which is ABOVE the")
    print(f"  true optimum {val:.6f}. A master that is not a relaxation.")
    print("\nThe working set must be seeded with a point of Xi. The")
    print(f"componentwise minimum {[float(round(u,1)) for u in xi_min]} is not one: total "
          f"{sum(xi_min):.0f}, below the")
    print(f"lower total row {TOTAL_LO:.0f}. Seeding there adds a row that is not valid")
    print("for the true problem and the master stops being a relaxation.")
    print("\nThe separation problem maximises a convex function over Xi, which")
    print(f"is NP-hard in general. Here it splits into 2^n = {2**N} sign")
    print("patterns, each an LP, because the cost separates by product.")

    print("\n" + "-" * 74)
    print("PART 4: THE IDENTITY, GUARDED NUMERICALLY")
    print("-" * 74)
    rng = np.random.default_rng(11)
    worst = 0.0
    for _ in range(200000):
        hh, bb = rng.uniform(0, 5, 2)
        xx, ss = rng.uniform(-20, 20, 2)
        lhs = hh * max(xx - ss, 0.0) + bb * max(ss - xx, 0.0)
        rhs = max(hh * (xx - ss), bb * (ss - xx))
        worst = max(worst, abs(lhs - rhs))
    print("200,000 random (h, b, x, xi) with h, b >= 0")
    print(f"worst |LHS - RHS| = {worst:.3e}")
    print("The proof is by cases on the sign of x - xi. This only guards the")
    print("algebra against a transcription slip.")

    print("\n" + "-" * 74)
    print("PARTS 5 and 6: n = 1, THE TWO REFORMULATIONS")
    print("-" * 74)
    h1, b1, l1, u1 = [h[0]], [b[0]], [lo[0]], [hi[0]]
    V1 = [np.array([l1[0]]), np.array([u1[0]])]
    cv, cx, cdt, _, cnc, cnv = robust_vertex_lp(V1, 1, h1, b1)
    av, ax, adt, anc, anv = box_identity_lp(1, h1, b1, l1, u1)
    fv, fx = box_closed_form(1, h1, b1, l1, u1)
    print(f"interval [{l1[0]:.0f}, {u1[0]:.0f}], h = {h1[0]}, b = {b1[0]}")
    print(f"{'formulation':>24} {'rows':>6} {'cols':>6} {'value':>12} "
          f"{'x':>10} {'solve s':>9}")
    print(f"{'extreme point (class)':>24} {cnc:>6} {cnv:>6} {cv:>12.6f} "
          f"{cx[0]:>10.4f} {cdt:>9.4f}")
    print(f"{'identity based':>24} {anc:>6} {anv:>6} {av:>12.6f} "
          f"{ax[0]:>10.4f} {adt:>9.4f}")
    print(f"{'closed form':>24} {'--':>6} {'--':>6} {fv:>12.6f} "
          f"{fx[0]:>10.4f} {'--':>9}")
    print("\nclosed form  x* = (h lo + b hi)/(h+b),  value = h b (hi-lo)/(h+b)")
    print(f"all three agree : {abs(cv - av) < 1e-6 and abs(av - fv) < 1e-6}")
    print("At n = 1 the row counts differ but both solve far below timing")
    print("noise. The honest claim is structural, not a measured speedup.")

    print("\n" + "-" * 74)
    print("WHERE THE GAP BITES: Xi A BOX, n GROWING")
    print("-" * 74)
    print("On a box the inner maximum separates by product, so the identity")
    print("gives 2n rows where extreme-point enumeration gives 2^n vertices.")
    print(f"\n{'n':>3} {'vertices':>9} {'vtx rows':>10} {'vtx s':>9} "
          f"{'id rows':>8} {'id s':>8} {'agree':>7}")
    rng = np.random.default_rng(5311)
    spent, budget_s = 0.0, 40.0
    for n in (2, 4, 6, 8, 10, 12, 14, 16):
        hv = list(np.round(rng.uniform(0.5, 3.0, n), 3))
        bv = list(np.round(rng.uniform(1.0, 6.0, n), 3))
        lv = list(np.round(rng.uniform(5.0, 15.0, n), 3))
        uv = [lv[i] + float(np.round(rng.uniform(5.0, 20.0), 3))
              for i in range(n)]
        iv, ix, idt, inc, _ = box_identity_lp(n, hv, bv, lv, uv)
        fvv, _ = box_closed_form(n, hv, bv, lv, uv)
        assert abs(iv - fvv) < 1e-5, (iv, fvv)
        if spent < budget_s:
            Vb = [np.array(p) for p in
                  itertools.product(*[(lv[i], uv[i]) for i in range(n)])]
            cv2, _, cdt2, _, cnc2, _ = robust_vertex_lp(Vb, n, hv, bv)
            spent += cdt2
            print(f"{n:>3} {len(Vb):>9} {cnc2:>10} {cdt2:>9.3f} {inc:>8} "
                  f"{idt:>8.3f} {str(abs(cv2 - iv) < 1e-5):>7}")
        else:
            print(f"{n:>3} {2**n:>9} {'not built':>10} {'--':>9} {inc:>8} "
                  f"{idt:>8.3f} {'vs closed':>7}")
    print("\nThe identity formulation stays linear in n. Extreme-point")
    print("enumeration doubles every time n increases by one.")

    print("\n" + "-" * 74)
    print("PARTS 7 and 8: THE BAND CONSTRAINT, ROBUST VERSION")
    print("-" * 74)
    print(f"{'i':>3} {'min_Xi xi_i':>12} {'max_Xi xi_i':>12} {'rho*_i':>9}")
    rs = []
    for i in range(N):
        r = (xi_max[i] - xi_min[i]) / (xi_max[i] + xi_min[i])
        rs.append(r)
        print(f"{i+1:>3} {xi_min[i]:>12.4f} {xi_max[i]:>12.4f} {r:>9.4f}")
    print(f"\nthe band needs only 2n = {2*N} extra rows, and it is feasible")
    print(f"iff rho >= max_i rho*_i = {max(rs):.4f}")
    print(f"\n{'rho':>8} {'status':>12} {'worst-case cost':>16}  x")
    for rho in (0.40, max(rs) - 1e-4, max(rs) + 1e-4, 0.70, 0.85, 1.00):
        rv, rx, _, rst, _, _ = robust_vertex_lp(V, band=rho)
        if rv is None:
            print(f"{rho:>8.4f} {rst:>12} {'--':>16}")
        else:
            print(f"{rho:>8.4f} {rst:>12} {rv:>16.6f}  "
                  f"{[round(u, 3) for u in rx]}")
    print(f"\nunconstrained robust cost for reference: {val:.6f}")
