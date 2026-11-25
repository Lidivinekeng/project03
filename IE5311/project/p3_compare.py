"""Problem 3(e) and 3(f): integer solution from generated routes, and
the comparison of Method I against Method II."""
import time

import gurobipy as gp
from gurobipy import GRB

from cvrp_data import Instance
from p3_colgen import column_generation
from p3_direct_mip import solve as solve_direct
from route_enum import rebuild_sequence


def integer_rmp(ins, cols, K=4, Q=None):
    """Problem 3(e)(ii): integer restricted master over generated routes."""
    Q = ins.Q if Q is None else Q
    m = gp.Model()
    m.setParam("OutputFlag", 0)
    y = m.addVars(len(cols), vtype=GRB.BINARY)
    m.setObjective(gp.quicksum(cols[r][1] * y[r]
                               for r in range(len(cols))), GRB.MINIMIZE)
    for c in ins.customers:
        m.addConstr(gp.quicksum(y[r] for r in range(len(cols))
                                if c in cols[r][0]) == 1)
    m.addConstr(gp.quicksum(y[r] for r in range(len(cols))) == K)
    t0 = time.perf_counter()
    m.optimize()
    dt = time.perf_counter() - t0
    if m.Status != GRB.OPTIMAL:
        return None, None, dt
    chosen = [cols[r] for r in range(len(cols)) if y[r].X > 0.5]
    return m.ObjVal, chosen, dt


def verify(ins, chosen, K, Q):
    served = sorted(i for mem, _, _ in chosen for i in mem)
    return {
        "routes": len(chosen) == K,
        "all customers once": served == sorted(ins.customers),
        "capacity": all(ld <= Q for _, _, ld in chosen),
        "cost consistent": all(
            ins.cost(rebuild_sequence(ins, mem, Q)) == cost
            for mem, cost, _ in chosen),
    }


if __name__ == "__main__":
    ins = Instance()
    K, Q = 4, ins.Q
    print("=" * 74)
    print("PROBLEM 3(e)-(f): integer solution from generated routes")
    print("=" * 74)

    print("\n--- Method I: direct MIP ---")
    m1, routes1, t1 = solve_direct(ins, K=K, limit=3600)
    st1 = "OPTIMAL" if m1.Status == GRB.OPTIMAL else str(m1.Status)
    print(f"status {st1}, objective {m1.ObjVal:.0f}, bound "
          f"{m1.ObjBound:.4f}, gap {m1.MIPGap:.4%}, time {t1:.2f} s, "
          f"nodes {m1.NodeCount:.0f}")

    print("\n--- Method II: column generation ---")
    res = column_generation(ins, K=K, Q=Q, verbose=False)
    print(f"iterations {res['iters']}, routes generated "
          f"{len(res['cols'])}, LP {res['z']:.6f}, "
          f"min reduced cost {res['min_rc']:.3e}, time {res['time']:.2f} s")
    frac = sum(1 for v in res["lam"] if 1e-6 < v < 1 - 1e-6)
    print(f"fractional lambda components in the final LP : {frac}")

    print("\n--- 3(e): integer restricted master over generated routes ---")
    zi, chosen, ti = integer_rmp(ins, res["cols"], K, Q)
    print(f"objective {zi:.0f}, time {ti:.2f} s")
    print(f"\n{'load':>7} {'cost':>6}  route")
    for mem, cost, ld in sorted(chosen, key=lambda r: -r[2]):
        seq = rebuild_sequence(ins, mem, Q)
        print(f"{ld:>7} {cost:>6}  {' -> '.join(map(str, seq))}")
    v = verify(ins, chosen, K, Q)
    print("\nfeasibility of the integer solution:")
    for k, ok in v.items():
        print(f"   {k:<22} {ok}")

    print("\n" + "=" * 74)
    print("3(f): comparison")
    print("=" * 74)
    lb = res["z"]
    print(f"{'quantity':<46}{'value':>12}")
    print(f"{'Method I  direct MIP optimum':<46}{m1.ObjVal:>12.0f}")
    print(f"{'Method I  best bound':<46}{m1.ObjBound:>12.4f}")
    print(f"{'Method II LP relaxation z_LP^DW (certified)':<46}{lb:>12.6f}")
    print(f"{'Method II integer solution from its routes':<46}{zi:>12.0f}")
    print(f"{'gap between z_LP^DW and the integer optimum':<46}"
          f"{m1.ObjVal - lb:>12.6f}")
    print(f"{'Method I  time (s)':<46}{t1:>12.2f}")
    print(f"{'Method II time, CG + integer RMP (s)':<46}"
          f"{res['time'] + ti:>12.2f}")
    same = (sorted(tuple(sorted(mem)) for mem, _, _ in chosen)
            == sorted(tuple(sorted(r[1:-1])) for r in routes1))
    print(f"\nboth methods return the same partition : {same}")
