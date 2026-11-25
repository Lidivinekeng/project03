"""Independent check that column generation certified the master LP.

The pricing MIP reports a nonnegative minimum reduced cost, but that is
the same solver that generated the columns. Here the final duals are
tested against *every* feasible route from the exhaustive enumeration,
which never passes through the pricer.
"""
import numpy as np

from cvrp_data import Instance
from p3_colgen import column_generation
from master_full import build, solve_lp
from route_enum import enumerate_routes


if __name__ == "__main__":
    ins = Instance()
    K = 4
    print("=" * 74)
    print("Independent verification of the column generation optimum")
    print("=" * 74)

    res = column_generation(ins, K=K, verbose=False)
    pi, sigma = res["pi"], res["sigma"]
    print(f"column generation LP value : {res['z']:.6f}")
    print(f"columns used               : {len(res['cols'])}")

    R = enumerate_routes(ins)
    print(f"\ntesting the final duals against all {len(R)} feasible routes")
    rc = np.array([cost - sum(pi[i] for i in mem) - sigma
                   for mem, cost, _ in R])
    print(f"   minimum reduced cost over the full route set : {rc.min():.10f}")
    print(f"   routes with reduced cost < -1e-6             : "
          f"{int((rc < -1e-6).sum())}")
    print(f"   routes with reduced cost < -1e-9             : "
          f"{int((rc < -1e-9).sum())}")

    A, b, c = build(ins, R, K)
    lp, t = solve_lp(A, b, c)
    print(f"\nfull master LP solved directly by HiGHS : {lp.fun:.6f}")
    print(f"column generation value                 : {res['z']:.6f}")
    print(f"difference                              : "
          f"{abs(lp.fun - res['z']):.3e}")
    ok = abs(lp.fun - res["z"]) < 1e-6 and rc.min() > -1e-6
    print(f"\noptimality of the full master LP established : {ok}")
