"""
IE 5311-001 Principles of Optimization, Fall 2026, Ningji Wei.
Part 1, Problem 1: the diet problem (Stigler diet), slides 14 to 19.

Written in general indexed form per the course formulation convention.
The model below never mentions a specific food or a specific number.
All data lives in the parameter tables at the top. Swapping in Stigler's
full 77 foods and 9 nutrients requires editing data only, not the model.

    Sets
        I   foods,     indexed by i
        J   nutrients, indexed by j

    Parameters
        c_i    cost per unit of food i                   [dollars/unit]
        a_ij   amount of nutrient j per unit of food i   [grams/unit]
        l_j    minimum required level of nutrient j      [grams/day]
        u_j    maximum allowed level of nutrient j       [grams/day]
        f_i    maximum servings of food i per day        [units/day]

    Decision variables
        x_i >= 0   units of food i consumed per day      [units/day]

    Model
        min   sum_{i in I} c_i x_i
        s.t.  l_j <= sum_{i in I} a_ij x_i <= u_j    for all j in J
              0 <= x_i <= f_i                        for all i in I

Numbers are illustrative, following the simplified food and nutrient
lists on slide 15. One unit is 100 grams.
"""

import gurobipy as gp
from gurobipy import GRB

# ----------------------------------------------------------------------
# DATA. Edit this block only. The model below reads it generically.
# ----------------------------------------------------------------------
FOODS = ["tomatoes", "potatoes", "beef", "chicken", "noodle", "rice"]
NUTRIENTS = ["protein", "fat", "carbs"]

# c_i : cost per unit
cost = {
    "tomatoes": 0.40, "potatoes": 0.20, "beef": 2.50,
    "chicken": 1.60, "noodle": 0.35, "rice": 0.25,
}

# a_ij : grams of nutrient j per unit of food i
nutrition = {
    ("tomatoes", "protein"): 0.9, ("tomatoes", "fat"): 0.2, ("tomatoes", "carbs"): 3.9,
    ("potatoes", "protein"): 2.0, ("potatoes", "fat"): 0.1, ("potatoes", "carbs"): 17.0,
    ("beef", "protein"): 26.0, ("beef", "fat"): 15.0, ("beef", "carbs"): 0.0,
    ("chicken", "protein"): 27.0, ("chicken", "fat"): 3.6, ("chicken", "carbs"): 0.0,
    ("noodle", "protein"): 13.0, ("noodle", "fat"): 1.5, ("noodle", "carbs"): 71.0,
    ("rice", "protein"): 7.1, ("rice", "fat"): 0.7, ("rice", "carbs"): 80.0,
}

# l_j and u_j : recommended level bounds per day
lower = {"protein": 56.0, "fat": 45.0, "carbs": 225.0}
upper = {"protein": 120.0, "fat": 80.0, "carbs": 325.0}

# f_i : servings cap, the guard Stigler's original model lacked
max_servings = {i: 10.0 for i in FOODS}


# ----------------------------------------------------------------------
# MODEL. Generic over the sets. No food name and no number appears here.
# ----------------------------------------------------------------------
def build_and_solve(foods, nutrients, c, a, l, u, f, verbose=True):
    m = gp.Model("diet")
    m.setParam("OutputFlag", 0)

    # x_i >= 0, bounded above by f_i
    x = m.addVars(foods, lb=0.0, ub=f, vtype=GRB.CONTINUOUS, name="x")

    # min sum_{i in I} c_i x_i
    m.setObjective(gp.quicksum(c[i] * x[i] for i in foods), GRB.MINIMIZE)

    # l_j <= sum_{i in I} a_ij x_i <= u_j   for all j in J
    intake = {j: gp.quicksum(a[i, j] * x[i] for i in foods) for j in nutrients}
    m.addConstrs((intake[j] >= l[j] for j in nutrients), name="min_intake")
    m.addConstrs((intake[j] <= u[j] for j in nutrients), name="max_intake")

    m.optimize()

    if m.Status == GRB.INFEASIBLE:
        return None, None
    if m.Status != GRB.OPTIMAL:
        raise RuntimeError(f"model not solved to optimality, status {m.Status}")

    if verbose:
        print(f"minimum daily cost: ${m.ObjVal:.4f}\n")
        print(f"{'food':>10}  {'units/day':>10}  {'grams/day':>10}  {'cost':>8}")
        for i in foods:
            if x[i].X > 1e-6:
                print(f"{i:>10}  {x[i].X:>10.3f}  {100 * x[i].X:>10.1f}"
                      f"  {c[i] * x[i].X:>8.3f}")

        print(f"\n{'nutrient':>10}  {'lower':>8}  {'achieved':>9}  {'upper':>8}"
              f"  {'binding':>9}")
        for j in nutrients:
            got = sum(a[i, j] * x[i].X for i in foods)
            tag = ("lower" if abs(got - l[j]) < 1e-6
                   else "upper" if abs(got - u[j]) < 1e-6 else "slack")
            print(f"{j:>10}  {l[j]:>8.1f}  {got:>9.2f}  {u[j]:>8.1f}  {tag:>9}")

        # Shadow price of a nutrient bound: the marginal cost of one more
        # gram required. This is the dual information slide 52 later
        # generalizes as dual pairing.
        print(f"\n{'constraint':>16}  {'shadow price':>13}")
        for con in m.getConstrs():
            if abs(con.Pi) > 1e-9:
                print(f"{con.ConstrName:>16}  {con.Pi:>13.5f}")

    return m, x


if __name__ == "__main__":
    model, x = build_and_solve(FOODS, NUTRIENTS, cost, nutrition,
                               lower, upper, max_servings)

    # Structural check: the model is generic over I and J, so shrinking
    # the food set requires no edit to build_and_solve. Dropping a food
    # can only remove options, so the cost cannot fall. It can also
    # destroy feasibility outright, which is the more interesting case.
    print("\n" + "-" * 58)
    print("dropping one food at a time from I (model code unchanged):")
    print(f"{'removed':>10}  {'new cost':>10}  {'outcome':>14}")
    for drop in FOODS:
        reduced = [i for i in FOODS if i != drop]
        m2, _ = build_and_solve(reduced, NUTRIENTS, cost, nutrition,
                                lower, upper, max_servings, verbose=False)
        if m2 is None:
            print(f"{drop:>10}  {'--':>10}  {'infeasible':>14}")
        else:
            assert m2.ObjVal >= model.ObjVal - 1e-9, "cost fell, impossible"
            print(f"{drop:>10}  {m2.ObjVal:>10.4f}  "
                  f"{'+' + format(m2.ObjVal - model.ObjVal, '.4f'):>14}")
