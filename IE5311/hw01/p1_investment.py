"""
IE 5311 Homework, Problem 1 [20 pts]: Maya's investment plan.

    Maya has $5,000 to invest over five years. At the beginning of each
    year she may place money into one-year or two-year time deposits at
    Frontier Bank. One-year deposits earn 4% per year; two-year deposits
    pay 9% total over their two-year term. Starting at the beginning of
    Year 2, Pioneer Finance offers a three-year certificate paying 15%
    total over three years. Maya reinvests any funds that mature each
    year. Maximize cash on hand at the end of Year 5.

TIME CONVENTION
    Period t = 1..5 indexes the BEGINNING of year t. t = 6 is the end of
    Year 5, which is when the objective is measured. An instrument of
    term L started at t matures at t + L, and is available only if
    t + L <= 6.

SETS
    T  = {1,...,5}          decision epochs (beginnings of years)
    K  = {1, 2, 3}          instrument terms in years
    A  = {(t,k) : instrument of term k may be started at epoch t}

PARAMETERS
    L_k     term of instrument k, in years
    r_k     total return multiplier of instrument k over its full term
              r_1 = 1.04, r_2 = 1.09, r_3 = 1.15
    a_k     first epoch at which instrument k may be started
              a_1 = a_2 = 1, a_3 = 2   (Pioneer opens at the start of Yr 2)
    B       initial endowment, $5,000
    H       horizon epoch, 6

DECISION VARIABLES
    x_{t,k} >= 0   dollars placed at epoch t into an instrument of term k
    w_t     >= 0   dollars held idle from epoch t to epoch t+1

MODEL
    max   sum over (t,k) with t + L_k = H of  r_k x_{t,k}   +  w_5
    s.t.  sum_k x_{1,k} + w_1 = B
          sum_k x_{t,k} + w_t
              = sum over (s,k) with s + L_k = t of r_k x_{s,k} + w_{t-1}
                                                          for t = 2..5
          x_{t,k} >= 0,  w_t >= 0

The idle-cash variables w_t are included so the model does not assume
full reinvestment. Every instrument earns a positive return, so I expect
them all to be zero; leaving them in makes that a result rather than an
assumption.
"""

import gurobipy as gp
from gurobipy import GRB

B = 5000.0
H = 6                                   # end of Year 5
TERM = {1: 1, 2: 2, 3: 3}               # L_k
RET = {1: 1.04, 2: 1.09, 3: 1.15}       # r_k, total over the full term
FIRST = {1: 1, 2: 1, 3: 2}              # a_k
EPOCHS = range(1, 6)                    # t = 1..5

# A = feasible (epoch, instrument) pairs
A = [(t, k) for t in EPOCHS for k in TERM
     if t >= FIRST[k] and t + TERM[k] <= H]


def solve(verbose=True):
    m = gp.Model("investment")
    m.setParam("OutputFlag", 0)

    x = m.addVars(A, lb=0.0, name="x")
    w = m.addVars(EPOCHS, lb=0.0, name="w")

    # objective: everything maturing exactly at the horizon, plus idle cash
    m.setObjective(
        gp.quicksum(RET[k] * x[t, k] for (t, k) in A if t + TERM[k] == H)
        + w[5], GRB.MAXIMIZE)

    # epoch 1: the endowment is allocated
    m.addConstr(gp.quicksum(x[1, k] for (t, k) in A if t == 1) + w[1] == B,
                name="balance_1")

    # epochs 2..5: what matures now, plus carried cash, is reallocated
    for t in range(2, 6):
        matured = gp.quicksum(RET[k] * x[s, k] for (s, k) in A
                              if s + TERM[k] == t)
        m.addConstr(gp.quicksum(x[t, k] for (u, k) in A if u == t) + w[t]
                    == matured + w[t - 1], name=f"balance_{t}")

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


def enumerate_plans():
    """
    Independent check. Enumerate every sequence of terms that exactly
    tiles epochs 1..6, respecting the Pioneer start date, and take the
    best compounded multiplier. This bypasses the LP entirely.
    """
    best = []

    def walk(t, factor, path):
        if t == H:
            best.append((factor, tuple(path)))
            return
        for k in TERM:
            if t >= FIRST[k] and t + TERM[k] <= H:
                walk(t + TERM[k], factor * RET[k], path + [(t, TERM[k])])

    walk(1, 1.0, [])
    best.sort(reverse=True)
    return best


if __name__ == "__main__":
    obj, sol = solve()

    print("\n" + "-" * 62)
    print("INDEPENDENT CHECK: enumerate every admissible term sequence")
    print("-" * 62)
    plans = enumerate_plans()
    print(f"{'multiplier':>11}  {'final value':>13}   plan (epoch, term)")
    for factor, path in plans[:6]:
        print(f"{factor:>11.6f}  ${B*factor:>12,.2f}   {list(path)}")
    print(f"... {len(plans)} admissible plans in total")
    top = plans[0][0] * B
    print(f"\nbest enumerated plan : ${top:,.2f}")
    print(f"LP optimal value     : ${obj:,.2f}")
    print(f"agreement            : {abs(top - obj) < 1e-6}")
