"""Regenerate every number quoted in the report, in one sequential run.

The project grades any part of the report that disagrees with the code
at zero, so this is the single source for the reported figures. Nothing
runs concurrently, so the timings are not distorted by contention.
"""
import math
import time

from gurobipy import GRB

from cvrp_data import Instance
from p3_colgen import column_generation, initial_routes
from p3_compare import integer_rmp, verify
from p3_direct_mip import solve as solve_direct
from p4_relaxations import lp_original
from route_enum import enumerate_routes


def rule(t):
    print("\n" + "=" * 74)
    print(t)
    print("=" * 74)


if __name__ == "__main__":
    T0 = time.perf_counter()
    ins = Instance()
    K = 4

    rule("PROBLEM 1  data and preliminary analysis")
    print(f"instance {ins.name}, n = {ins.n}, Q = {ins.Q}, depot = "
          f"{ins.depot}, customers = {len(ins.customers)}")
    print(f"(b) D = {ins.D}, ceil(D/Q) = {-(-ins.D // ins.Q)}, "
          f"K*Q - D = {K * ins.Q - ins.D}")
    for (i, j) in [(1, 2), (1, 3), (2, 3)]:
        a, b = ins.coord[i], ins.coord[j]
        print(f"(c) c_{i},{j} = {ins.c[i, j]}   "
              f"(exact {math.hypot(a[0]-b[0], a[1]-b[1]):.6f})")

    rule("PROBLEM 3  Method I, direct MIP")
    m1, routes1, t1 = solve_direct(ins, K=K, limit=3600)
    print(f"variables {m1.NumVars}, rows {m1.NumConstrs}, lazy cuts "
          f"{m1._cuts}")
    print(f"status {'OPTIMAL' if m1.Status == GRB.OPTIMAL else m1.Status}, "
          f"objective {m1.ObjVal:.0f}, bound {m1.ObjBound:.4f}, "
          f"gap {m1.MIPGap:.6%}")
    print(f"nodes {m1.NodeCount:.0f}, TIME {t1:.2f} s")
    for k, r in enumerate(routes1, 1):
        print(f"   veh {k}: load {ins.load(r):>5} cost {ins.cost(r):>4}  "
              f"{' -> '.join(map(str, r))}")
    print(f"   sum of route costs {sum(ins.cost(r) for r in routes1)}, "
          f"all customers once "
          f"{sorted(i for r in routes1 for i in r if i != ins.depot) == sorted(ins.customers)}"
          f", loads<=Q {all(ins.load(r) <= ins.Q for r in routes1)}")

    rule("PROBLEM 3  Method II, column generation")
    init = initial_routes(ins, K)
    print("pricing pool = 10 solutions per iteration")
    print(f"initial RMP cost {sum(c for _, c, _ in init)} from "
          f"{[tuple(m) for m, _, _ in init]}")
    res = column_generation(ins, K=K, pool=10, verbose=False)
    print(f"iterations {res['iters']}, routes generated "
          f"{len(res['cols'])}, LP {res['z']:.6f}, "
          f"min reduced cost {res['min_rc']:.6f}, TIME {res['time']:.2f} s")
    frac = sum(1 for v in res["lam"] if 1e-6 < v < 1 - 1e-6)
    big = max(res["lam"])
    print(f"fractional weights {frac}, largest weight {big:.4f}")
    R = enumerate_routes(ins)
    print(f"feasible routes in the full master {len(R)}, "
          f"priced in {len(res['cols']) / len(R):.4%}")

    rule("PROBLEM 3(e)  integer restricted master over generated routes")
    zi, chosen, ti = integer_rmp(ins, res["cols"], K, ins.Q)
    print(f"objective {zi:.0f}, TIME {ti:.3f} s")
    for mem, cost, ld in sorted(chosen, key=lambda r: -r[2]):
        print(f"   load {ld:>5} cost {cost:>4}  {mem}")
    for k, v in verify(ins, chosen, K, ins.Q).items():
        print(f"   {k:<22} {v}")
    opt = {tuple(sorted(r[1:-1])) for r in routes1}
    pool = {c[0] for c in res["cols"]}
    print(f"   optimal routes present in the pool: "
          f"{sum(1 for o in opt if o in pool)}/4")
    for o in sorted(opt):
        print(f"      {o}: {'in pool' if o in pool else 'MISSING'}")

    rule("PROBLEM 3(e)  sensitivity of the integer solution to the pool")
    print(f"{'pool':>5} {'iters':>6} {'columns':>8} {'LP':>11} "
          f"{'integer':>8} {'opt in pool':>12}")
    for pl in [4, 10, 25]:
        r2 = column_generation(ins, K=K, pool=pl, verbose=False)
        z2, ch2, _ = integer_rmp(ins, r2["cols"], K, ins.Q)
        have = sum(1 for o in opt if o in {c[0] for c in r2["cols"]})
        print(f"{pl:>5} {r2['iters']:>6} {len(r2['cols']):>8} "
              f"{r2['z']:>11.6f} {z2:>8.0f} {have:>10}/4")

    rule("PROBLEM 4  LP relaxation strength")
    z_no, _, _ = lp_original(ins, K=K, with_sec=False)
    z_or, rounds, cuts = lp_original(ins, K=K, with_sec=True)
    print(f"LP without subtour constraints {z_no:.6f}")
    print(f"z_LP^orig with separation      {z_or:.6f}  "
          f"({rounds} rounds, {cuts} cuts)")
    print(f"z_LP^DW                        {res['z']:.6f}")
    print(f"z*                             {m1.ObjVal:.0f}")
    print(f"chain holds: {z_no <= z_or + 1e-6 <= res['z'] + 1e-6 <= m1.ObjVal + 1e-6}")
    print(f"DW closes {(res['z'] - z_or) / (m1.ObjVal - z_or):.1%} of the "
          f"remaining gap")

    rule("PROBLEM 5  capacity sensitivity")
    m7, routes7, t7 = solve_direct(ins, K=K, Q=7500, limit=3600)
    print(f"Q = 6000: z* = {m1.ObjVal:.0f}, loads "
          f"{sorted(ins.load(r) for r in routes1)}")
    print(f"Q = 7500: z* = {m7.ObjVal:.0f}, loads "
          f"{sorted(ins.load(r) for r in routes7)}, "
          f"gap {m7.MIPGap:.4%}, TIME {t7:.2f} s")
    for k, r in enumerate(routes7, 1):
        print(f"   veh {k}: load {ins.load(r):>5} cost {ins.cost(r):>4}  "
              f"{' -> '.join(map(str, r))}")
    p6 = {tuple(sorted(r[1:-1])) for r in routes1}
    p7 = {tuple(sorted(r[1:-1])) for r in routes7}
    print(f"   change {m7.ObjVal - m1.ObjVal:+.0f} "
          f"({(m7.ObjVal - m1.ObjVal) / m1.ObjVal:+.2%}), "
          f"routes in common {len(p6 & p7)}")

    rule(f"total wall clock {time.perf_counter() - T0:.1f} s")
