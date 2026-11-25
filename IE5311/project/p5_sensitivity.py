"""Problem 5: capacity sensitivity, Q = 6000 against Q' = 7500,
using the direct MIP of Problem 2(a) with exactly four vehicles."""
import time

from gurobipy import GRB

from cvrp_data import Instance
from p3_direct_mip import solve as solve_direct


def report(tag, ins, m, routes, dt):
    st = "OPTIMAL" if m.Status == GRB.OPTIMAL else str(m.Status)
    print(f"\n--- {tag} ---")
    print(f"status {st}, objective {m.ObjVal:.0f}, bound {m.ObjBound:.4f}, "
          f"gap {m.MIPGap:.4%}, time {dt:.1f} s, nodes {m.NodeCount:.0f}")
    print(f"{'veh':>4} {'load':>7} {'cost':>6}  route")
    for k, r in enumerate(routes, 1):
        print(f"{k:>4} {ins.load(r):>7} {ins.cost(r):>6}  "
              f"{' -> '.join(map(str, r))}")
    return {tuple(sorted(r[1:-1])): ins.cost(r) for r in routes}


if __name__ == "__main__":
    ins = Instance()
    print("=" * 74)
    print("PROBLEM 5: sensitivity to vehicle capacity")
    print("=" * 74)
    m6, r6, t6 = solve_direct(ins, K=4, Q=6000, limit=3600)
    s6 = report("Q = 6000", ins, m6, r6, t6)
    m7, r7, t7 = solve_direct(ins, K=4, Q=7500, limit=3600)
    s7 = report("Q' = 7500", ins, m7, r7, t7)

    print("\n--- 5(b): comparison ---")
    print(f"travel cost        : {m6.ObjVal:.0f} -> {m7.ObjVal:.0f}"
          f"   (change {m7.ObjVal - m6.ObjVal:+.0f})")
    print(f"loads at Q=6000    : {sorted(ins.load(r) for r in r6)}"
          f"  (max {max(ins.load(r) for r in r6)}, slack "
          f"{6000 - max(ins.load(r) for r in r6)})")
    print(f"loads at Q=7500    : {sorted(ins.load(r) for r in r7)}"
          f"  (max {max(ins.load(r) for r in r7)}, slack "
          f"{7500 - max(ins.load(r) for r in r7)})")
    same = set(s6) == set(s7)
    print(f"same customer partition : {same}")
    if not same:
        print(f"   only at Q=6000 : {sorted(set(s6) - set(s7))}")
        print(f"   only at Q=7500 : {sorted(set(s7) - set(s6))}")
    else:
        seq6 = [tuple(r) for r in r6]
        seq7 = [tuple(r) for r in r7]
        print(f"   identical visiting sequences : "
              f"{sorted(seq6) == sorted(seq7)}")
    print(f"\n   binding at Q=6000 : "
          f"{any(ins.load(r) > 7500 - 1e-9 for r in r6)} "
          f"(a route exceeding 7500 would be needed to exploit Q')")
