import gurobipy as gp
from gurobipy import GRB

B = 5000.0
H = 6
TERM = {1: 1, 2: 2, 3: 3}
RET = {1: 1.04, 2: 1.09, 3: 1.15}
FIRST = {1: 1, 2: 1, 3: 2}
EPOCHS = range(1, 6)

A = [(t, k) for t in EPOCHS for k in TERM
     if t >= FIRST[k] and t + TERM[k] <= H]


def solve(verbose=True):
    m = gp.Model("investment")
    m.setParam("OutputFlag", 0)

    x = m.addVars(A, lb=0.0, name="x")
    w = m.addVars(EPOCHS, lb=0.0, name="w")

    m.setObjective(
        gp.quicksum(RET[k] * x[t, k] for (t, k) in A if t + TERM[k] == H)
        + w[5], GRB.MAXIMIZE)

    m.addConstr(x.sum(1, "*") + w[1] == B, name="balance_1")

    for t in range(2, 6):
        matured = gp.quicksum(RET[k] * x[s, k] for (s, k) in A
                              if s + TERM[k] == t)
        m.addConstr(x.sum(t, "*") + w[t] == matured + w[t - 1],
                    name=f"balance_{t}")

    m.optimize()
    assert m.Status == GRB.OPTIMAL, m.Status

    if verbose:
        print("feasible (epoch, term) pairs:", A)
        print(f"\noptimal cash at end of Year 5 : ${m.ObjVal:,.2f}\n")
        print(f"{'epoch':>6}  {'term (yr)':>9}  {'amount':>12}  {'matures at':>10}")
        for (t, k) in A:
            if x[t, k].X > 1e-6:
                print(f"{t:>6}  {TERM[k]:>9}  ${x[t,k].X:>11,.2f}  {t+TERM[k]:>10}")
        idle = {t: w[t].X for t in EPOCHS if w[t].X > 1e-6}
        print(f"\nidle cash held: {idle if idle else 'none at any epoch'}")
        print("\nshadow price on each balance constraint")
        print("(value of one extra dollar available at that epoch):")
        for c in m.getConstrs():
            print(f"  {c.ConstrName:>12}  {c.Pi:.6f}")
    return m.ObjVal, {(t, k): x[t, k].X for (t, k) in A}


if __name__ == "__main__":
    solve()
