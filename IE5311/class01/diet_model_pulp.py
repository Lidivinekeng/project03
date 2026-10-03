import pulp

FOODS = ["tomatoes", "potatoes", "beef", "chicken", "noodle", "rice"]
NUTRIENTS = ["protein", "fat", "carbs"]

cost = {
    "tomatoes": 0.40, "potatoes": 0.20, "beef": 2.50,
    "chicken": 1.60, "noodle": 0.35, "rice": 0.25,
}

nutrition = {
    ("tomatoes", "protein"): 0.9, ("tomatoes", "fat"): 0.2, ("tomatoes", "carbs"): 3.9,
    ("potatoes", "protein"): 2.0, ("potatoes", "fat"): 0.1, ("potatoes", "carbs"): 17.0,
    ("beef", "protein"): 26.0, ("beef", "fat"): 15.0, ("beef", "carbs"): 0.0,
    ("chicken", "protein"): 27.0, ("chicken", "fat"): 3.6, ("chicken", "carbs"): 0.0,
    ("noodle", "protein"): 13.0, ("noodle", "fat"): 1.5, ("noodle", "carbs"): 71.0,
    ("rice", "protein"): 7.1, ("rice", "fat"): 0.7, ("rice", "carbs"): 80.0,
}

lower = {"protein": 56.0, "fat": 45.0, "carbs": 225.0}
upper = {"protein": 120.0, "fat": 80.0, "carbs": 325.0}
max_servings = {i: 10.0 for i in FOODS}


def _binding(value, bound, rel=1e-6):
    return abs(value - bound) <= rel * max(1.0, abs(bound))


def build_and_solve(foods, nutrients, c, a, l, u, f, verbose=True):
    m = pulp.LpProblem("diet", pulp.LpMinimize)

    x = {i: pulp.LpVariable(f"x_{i}", lowBound=0, upBound=f[i]) for i in foods}

    m += pulp.lpSum(c[i] * x[i] for i in foods), "total_cost"

    for j in nutrients:
        intake = pulp.lpSum(a[i, j] * x[i] for i in foods)
        m += intake >= l[j], f"min_intake_{j}"
        m += intake <= u[j], f"max_intake_{j}"

    m.solve(pulp.PULP_CBC_CMD(msg=0))
    status = pulp.LpStatus[m.status]

    if status == "Infeasible":
        return None, None, status
    if status != "Optimal":
        raise RuntimeError(f"unexpected solver status: {status}")

    obj = pulp.value(m.objective)

    if verbose:
        print(f"minimum daily cost: ${obj:.4f}\n")
        print(f"{'food':>10}  {'units/day':>10}  {'grams/day':>10}  {'cost':>8}")
        for i in foods:
            if x[i].value() > 1e-6:
                print(f"{i:>10}  {x[i].value():>10.3f}  {100 * x[i].value():>10.1f}"
                      f"  {c[i] * x[i].value():>8.3f}")

        print(f"\n{'nutrient':>10}  {'lower':>8}  {'achieved':>9}  {'upper':>8}"
              f"  {'binding':>9}")
        for j in nutrients:
            got = sum(a[i, j] * x[i].value() for i in foods)
            tag = ("lower" if _binding(got, l[j])
                   else "upper" if _binding(got, u[j]) else "slack")
            print(f"{j:>10}  {l[j]:>8.1f}  {got:>9.2f}  {u[j]:>8.1f}  {tag:>9}")

        print(f"\n{'constraint':>16}  {'shadow price':>13}")
        for name, con in m.constraints.items():
            if con.pi is not None and abs(con.pi) > 1e-9:
                print(f"{name:>16}  {con.pi:>13.5f}")

    return m, x, status


if __name__ == "__main__":
    model, x, _ = build_and_solve(FOODS, NUTRIENTS, cost, nutrition,
                                  lower, upper, max_servings)
    base = pulp.value(model.objective)

    print("\n" + "-" * 58)
    print("dropping one food at a time from I (model code unchanged):")
    print(f"{'removed':>10}  {'new cost':>10}  {'outcome':>14}")
    for drop in FOODS:
        reduced = [i for i in FOODS if i != drop]
        m2, _, status = build_and_solve(reduced, NUTRIENTS, cost, nutrition,
                                        lower, upper, max_servings, verbose=False)
        if m2 is None:
            print(f"{drop:>10}  {'--':>10}  {'infeasible':>14}")
        else:
            val = pulp.value(m2.objective)
            assert val >= base - 1e-9, "cost fell, impossible"
            print(f"{drop:>10}  {val:>10.4f}  "
                  f"{'+' + format(val - base, '.4f'):>14}")
