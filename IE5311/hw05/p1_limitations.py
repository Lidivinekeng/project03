import gurobipy as gp
import numpy as np
from gurobipy import GRB

from p1_simplex import simplex

print("=" * 74)
print("PROBLEM 1 PART 5: limitations, demonstrated rather than asserted")
print("=" * 74)

print("\n1. NO PHASE I. The code starts from the slack basis, which is")
print("   feasible only when b >= 0. With a negative right-hand side it")
print("   starts infeasible and reports a meaningless answer.")
A = np.array([[1.0], [-1.0]])
b = np.array([1.0, -3.0])
c = np.array([1.0])
print("   max x1  s.t.  x1 <= 1,  -x1 <= -3  (x1 >= 3),  x1 >= 0")
print("   x1 <= 1 and x1 >= 3 cannot both hold: this LP is INFEASIBLE")
x, obj, it, status = simplex(A, b, c)
res = A @ x - b
print(f"   my simplex returns status '{status}', x = {x}, obj = {obj}")
print(f"   row residuals Ax - b = {res}   (feasibility needs <= 0)")
print(f"   feasible? {bool(np.all(res <= 1e-9))}  "
      f"row 2 is violated by {res[1]:.1f}")
m = gp.Model()
m.setParam("OutputFlag", 0)
m.setParam("DualReductions", 0)
v = m.addMVar(1, lb=0.0)
m.setObjective(c @ v, GRB.MAXIMIZE)
m.addConstr(A @ v <= b)
m.optimize()
print(f"   gurobi correctly reports: "
      f"{ {2: 'OPTIMAL', 3: 'INFEASIBLE', 5: 'UNBOUNDED'}.get(m.Status, m.Status) }")
print("   so the failure is silent: an infeasible problem is reported")
print("   optimal. A Phase I would detect it.")

print("\n2. DEGENERACY AND CYCLING. Dantzig's rule has no anti-cycling")
print("   guarantee. Beale's classic example:")
A = [[0.25, -60.0, -0.04, 9.0],
     [0.50, -90.0, -0.02, 3.0],
     [0.00, 0.0, 1.0, 0.0]]
b = [0.0, 0.0, 1.0]
c = [0.75, -150.0, 0.02, -6.0]
x, obj, it, status = simplex(A, b, c, max_iter=200)
print(f"   status {status} after {it} iterations, obj = {obj}")
if status == "iteration limit":
    print("   the implementation cycles and never terminates")
else:
    print(f"   x = {np.round(x, 6)}")
    print("   it terminated here, but the tie-breaking that saved it is")
    print("   incidental, not a proof: only Bland's rule or a")
    print("   lexicographic ratio test guarantees termination")

print("\n3. FORM RESTRICTION. Only max c'x s.t. Ax <= b, x >= 0 is")
print("   accepted. Equalities, >= rows, free variables and general")
print("   bounds l <= x <= u must be converted by hand first, and each")
print("   conversion adds variables or rows that a real solver handles")
print("   natively.")

print("\n4. DENSE REFACTORIZATION. Every iteration solves two dense")
print("   systems with A_B from scratch:")
for m in (40, 100, 200):
    AB = np.random.default_rng(0).uniform(1, 2, (m, m)) + m * np.eye(m)
    import time
    t0 = time.perf_counter()
    for _ in range(50):
        np.linalg.solve(AB, np.ones(m))
    dt = (time.perf_counter() - t0) / 50
    print(f"   m = {m:>3}: one dense solve ~ {dt*1e6:7.1f} microseconds, "
          f"cost O(m^3)")
print("   A revised simplex keeps an LU factorization and updates it in")
print("   O(m^2), and stores A sparsely. That is the main reason the")
print("   runtime gap to Gurobi widens with size.")

print("\n5. NUMERICS. One fixed tolerance 1e-9 regardless of problem")
print("   scale, no scaling, no Harris ratio test, no basis repair.")
print("   Ill-conditioned bases can give wrong pivots silently.")

print("\n6. NO PRESOLVE, NO WARM START, NO DUAL SIMPLEX. Redundant rows")
print("   and fixed variables are never removed, and the solve cannot be")
print("   restarted from a previous basis after a bound change, which is")
print("   what branch-and-bound needs.")
