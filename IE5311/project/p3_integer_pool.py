"""Problem 3(e): how the column pool affects the integer solution.

Column generation stops as soon as the master LP is certified, so the
pool it leaves behind need not contain the columns an integer solution
requires. Asking the pricer for several solutions per iteration, rather
than only the best one, costs almost nothing and enlarges the pool with
routes that came out of the same pricing problems.
"""
import sys

from cvrp_data import Instance
from p3_colgen import column_generation
from p3_compare import integer_rmp, verify

OPT = [(2, 3, 6, 7, 8, 10), (4, 5, 9, 11, 12, 14),
       (13, 16, 18, 19, 21), (15, 17, 20, 22)]

if __name__ == "__main__":
    ins = Instance()
    print("=" * 74)
    print("PROBLEM 3(e): integer restricted master over the generated pool")
    print("=" * 74)
    print(f"{'pool/iter':>10} {'harvest':>8} {'iters':>6} {'columns':>8} "
          f"{'LP':>11} {'integer':>8} {'opt routes':>11} {'CG s':>7}")
    best = None
    for pool, harvest in [(4, 0), (10, 0), (25, 0), (25, 150), (50, 300)]:
        res = column_generation(ins, pool=pool, harvest=harvest,
                                verbose=False)
        zi, chosen, ti = integer_rmp(ins, res["cols"], 4, ins.Q)
        have = sum(1 for o in OPT if o in {c[0] for c in res["cols"]})
        print(f"{pool:>10} {harvest:>8} {res['iters']:>6} "
              f"{len(res['cols']):>8} {res['z']:>11.6f} {zi:>8.0f} "
              f"{have:>7}/4 {res['time']:>7.1f}", flush=True)
        if best is None or zi < best[0]:
            best = (zi, chosen, res)
    zi, chosen, res = best
    print(f"\nbest integer solution from generated routes: {zi:.0f}")
    print(f"{'load':>7} {'cost':>6}  members")
    for mem, cost, ld in sorted(chosen, key=lambda r: -r[2]):
        print(f"{ld:>7} {cost:>6}  {mem}")
    for k, v in verify(ins, chosen, 4, ins.Q).items():
        print(f"   {k:<22} {v}")
