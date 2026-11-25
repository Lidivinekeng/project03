"""Problem 5(c) support: z*(Q) as capacity grows.

z*(Q) is nonincreasing because enlarging Q only relaxes the capacity
rows, so the feasible set grows. It is also piecewise constant: once Q
exceeds the largest load of some capacity-unconstrained optimal
K-route partition, further increases buy nothing. These runs locate
that flat region, which is what makes the inequality non-strict in
general.
"""
import gurobipy as gp
from gurobipy import GRB

from cvrp_data import Instance
from p3_direct_mip import solve as solve_direct

if __name__ == "__main__":
    ins = Instance()
    print("=" * 66)
    print("z*(Q) for the direct MIP with exactly K = 4 vehicles")
    print("=" * 66)
    print(f"{'Q':>7} {'z*(Q)':>8} {'status':>10} {'max load':>9} "
          f"{'slack':>7} {'time (s)':>9}")
    prev = None
    for Q in [5900, 6000, 6500, 7000, 7500, 9000, 12000, 22500]:
        m, routes, dt = solve_direct(ins, K=4, Q=Q, limit=900)
        if m.SolCount == 0:
            print(f"{Q:>7} {'--':>8} {'no sol':>10}")
            continue
        st = "optimal" if m.Status == GRB.OPTIMAL else f"gap {m.MIPGap:.2%}"
        ml = max(ins.load(r) for r in routes)
        flag = ""
        if prev is not None and abs(m.ObjVal - prev) < 1e-9:
            flag = "   <- unchanged"
        print(f"{Q:>7} {m.ObjVal:>8.0f} {st:>10} {ml:>9} {Q - ml:>7} "
              f"{dt:>9.1f}{flag}")
        prev = m.ObjVal
