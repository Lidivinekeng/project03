import numpy as np
import gurobipy as gp
from gurobipy import GRB
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

I = range(3)
J = range(4)
S = range(10)

c = [18.0, 21.0, 19.0]
xbar = [120.0, 100.0, 110.0]
BUDGET = 6000.0

p = [0.12, 0.10, 0.10, 0.10, 0.10, 0.10, 0.10, 0.10, 0.10, 0.08]

d = [[30, 35, 40, 30],
     [45, 30, 35, 45],
     [35, 55, 40, 35],
     [50, 45, 55, 40],
     [40, 40, 65, 55],
     [55, 50, 45, 65],
     [60, 55, 70, 45],
     [50, 75, 60, 65],
     [70, 65, 75, 60],
     [80, 75, 85, 70]]

a = [[1.00, 1.00, 1.00],
     [1.00, 0.85, 1.00],
     [0.80, 1.00, 1.00],
     [1.00, 1.00, 0.75],
     [0.70, 1.00, 0.90],
     [1.00, 0.65, 0.85],
     [0.75, 0.80, 1.00],
     [0.60, 1.00, 0.75],
     [0.95, 0.90, 0.95],
     [0.70, 0.70, 0.75]]

q = [[4.0, 6.0, 9.0, 11.0],
     [7.0, 4.0, 5.0, 8.0],
     [10.0, 7.0, 4.0, 3.0]]

kappa = [45.0, 50.0, 55.0, 60.0]
w = [1.0, 1.0, 1.5, 2.0]

THETA = 0.90
GAMMA = 0.90
ALPHA = 0.90
LAMBDA = 75.0


def smallest_M(j, s):
    return THETA * d[s][j]


def build(chance=False, cvar=False, name="model"):
    m = gp.Model(name)
    m.setParam("OutputFlag", 0)

    x = m.addVars(I, lb=0.0, ub=xbar, name="x")
    y = m.addVars(I, J, S, lb=0.0, name="y")
    u = m.addVars(J, S, lb=0.0, name="u")

    first = gp.quicksum(c[i] * x[i] for i in I)
    second = gp.quicksum(
        p[s] * (gp.quicksum(q[i][j] * y[i, j, s] for i in I for j in J)
                + gp.quicksum(kappa[j] * u[j, s] for j in J)) for s in S)
    m.setObjective(first + second, GRB.MINIMIZE)

    m.addConstr(first <= BUDGET, name="budget")
    for s in S:
        for i in I:
            m.addConstr(gp.quicksum(y[i, j, s] for j in J) <= a[s][i] * x[i],
                        name=f"avail_{i}_{s}")
        for j in J:
            m.addConstr(gp.quicksum(y[i, j, s] for i in I) + u[j, s] == d[s][j],
                        name=f"demand_{j}_{s}")

    z = None
    if chance:
        z = m.addVars(S, vtype=GRB.BINARY, name="z")
        for s in S:
            for j in J:
                m.addConstr(
                    u[j, s] <= (1.0 - THETA) * d[s][j]
                    + smallest_M(j, s) * (1 - z[s]), name=f"serve_{j}_{s}")
        m.addConstr(gp.quicksum(p[s] * z[s] for s in S) >= GAMMA, name="chance")

    eta = None
    if cvar:
        eta = m.addVar(lb=-GRB.INFINITY, name="eta")
        v = m.addVars(S, lb=0.0, name="v")
        for s in S:
            m.addConstr(
                v[s] >= gp.quicksum(w[j] * u[j, s] for j in J) - eta,
                name=f"cvar_epi_{s}")
        m.addConstr(
            eta + gp.quicksum(p[s] * v[s] for s in S) / (1.0 - ALPHA) <= LAMBDA,
            name="cvar")

    m.optimize()
    if m.Status != GRB.OPTIMAL:
        return None
    return {
        "name": name,
        "obj": m.ObjVal,
        "x": [x[i].X for i in I],
        "z": [z[s].X for s in S] if chance else None,
        "eta": eta.X if cvar else None,
        "u": [[u[j, s].X for j in J] for s in S],
        "nvars": m.NumVars,
        "ncons": m.NumConstrs,
        "nbin": m.NumBinVars,
    }


def recourse(xsol, s):
    m = gp.Model("recourse")
    m.setParam("OutputFlag", 0)
    y = m.addVars(I, J, lb=0.0)
    u = m.addVars(J, lb=0.0)
    m.setObjective(
        gp.quicksum(q[i][j] * y[i, j] for i in I for j in J)
        + gp.quicksum(kappa[j] * u[j] for j in J), GRB.MINIMIZE)
    for i in I:
        m.addConstr(gp.quicksum(y[i, j] for j in J) <= a[s][i] * xsol[i])
    for j in J:
        m.addConstr(gp.quicksum(y[i, j] for i in I) + u[j] == d[s][j])
    m.optimize()
    assert m.Status == GRB.OPTIMAL
    uu = [u[j].X for j in J]
    return (m.ObjVal, uu,
            sum(w[j] * uu[j] for j in J),
            all(uu[j] <= (1.0 - THETA) * d[s][j] + 1e-6 for j in J))


def cvar_of(vals, probs, alpha):
    best = np.inf
    for eta in np.unique(vals):
        best = min(best, eta + float(np.sum(probs * np.maximum(vals - eta, 0.0)))
                   / (1.0 - alpha))
    return best


if __name__ == "__main__":
    print("=" * 78)
    print("PROBLEM 1: EMERGENCY RELIEF PLANNING UNDER UNCERTAINTY")
    print("=" * 78)
    print(f"|I| = {len(I)} centers, |J| = {len(J)} regions, |S| = {len(S)} "
          f"scenarios, sum p = {sum(p):.2f}")
    print(f"budget {BUDGET:.0f}; filling every center to capacity would cost "
          f"{sum(c[i]*xbar[i] for i in I):.0f}, so the budget binds first")

    print("\nsmallest valid big-M is M_js = (1 - theta) d_js subtracted from")
    print("d_js, that is M_js = theta d_js, since 0 <= u_js <= d_js:")
    print(f"{'j':>3}" + "".join(f"{'s'+str(s+1):>7}" for s in S))
    for j in J:
        print(f"{j+1:>3}" + "".join(f"{smallest_M(j, s):>7.1f}" for s in S))

    models = []
    for tag, ch, cv in (("risk-neutral", False, False),
                        ("chance-constrained", True, False),
                        ("chance + CVaR", True, True)):
        r = build(chance=ch, cvar=cv, name=tag)
        if r is None:
            print(f"\n{tag}: INFEASIBLE")
            continue
        models.append(r)
        print("\n" + "-" * 78)
        print(f"MODEL: {tag}")
        print("-" * 78)
        print(f"size              : {r['nvars']} vars "
              f"({r['nbin']} binary), {r['ncons']} constraints")
        print(f"optimal objective : {r['obj']:.4f}")
        print(f"first stage x     : "
              f"{[round(v, 4) for v in r['x']]}")
        print(f"pre-positioning   : {sum(c[i]*r['x'][i] for i in I):.2f} "
              f"of {BUDGET:.0f} budget, {sum(r['x']):.2f} units total")
        if r["z"] is not None:
            served = [s + 1 for s in S if r["z"][s] > 0.5]
            failed = [s + 1 for s in S if r["z"][s] <= 0.5]
            print(f"scenarios served  : {served}")
            print(f"scenarios exempt  : {failed}  "
                  f"(probability {sum(p[s-1] for s in failed):.2f} <= "
                  f"{1-GAMMA:.2f})")
        if r["eta"] is not None:
            L = np.array([sum(w[j] * r["u"][s][j] for j in J) for s in S])
            print(f"eta (VaR level)   : {r['eta']:.4f}")
            print(f"CVaR_0.90 of L    : "
                  f"{cvar_of(L, np.array(p), ALPHA):.4f}  (cap {LAMBDA:.0f})")

    print("\n" + "=" * 78)
    print("PART 7: OUT-OF-SAMPLE EVALUATION ON 5,000 DRAWS")
    print("=" * 78)
    rng = np.random.default_rng(5311)
    draws = rng.choice(len(S), size=5000, p=p)
    print(f"empirical scenario frequencies vs p:")
    print(f"{'s':>3} {'p_s':>8} {'freq':>8}")
    for s in S:
        print(f"{s+1:>3} {p[s]:>8.3f} {np.mean(draws == s):>8.3f}")

    curves, stats = {}, {}
    for r in models:
        per = [recourse(r["x"], s) for s in S]
        tot = np.array([sum(c[i] * r["x"][i] for i in I) + per[s][0] for s in S])
        Ls = np.array([per[s][2] for s in S])
        ok = np.array([per[s][3] for s in S])
        sample = tot[draws]
        curves[r["name"]] = sample
        planned = sum(p[s] for s in S
                      if all(r["u"][s][j] <= (1.0 - THETA) * d[s][j] + 1e-6
                             for j in J))
        stats[r["name"]] = {
            "planned": planned,
            "mean": float(sample.mean()),
            "sd": float(sample.std()),
            "p90": float(np.quantile(sample, 0.90)),
            "cvar": cvar_of(tot, np.array(p), ALPHA),
            "max": float(sample.max()),
            "served": float(np.sum([p[s] for s in S if ok[s]])),
            "cvarL": cvar_of(Ls, np.array(p), ALPHA),
            "tot": tot,
        }

    print(f"\n{'model':>20} {'E[cost]':>10} {'sd':>9} {'90% q':>10} "
          f"{'CVaR.90':>10} {'max':>10} {'CVaR.90(L)':>11}")
    for r in models:
        t = stats[r["name"]]
        print(f"{r['name']:>20} {t['mean']:>10.2f} {t['sd']:>9.2f} "
              f"{t['p90']:>10.2f} {t['cvar']:>10.2f} {t['max']:>10.2f} "
              f"{t['cvarL']:>11.2f}")

    print(f"\nservice adequacy, planned by the model against realised when the")
    print(f"operator re-optimises cost scenario by scenario")
    print(f"{'model':>20} {'planned':>10} {'realised':>10}")
    for r in models:
        t = stats[r["name"]]
        print(f"{r['name']:>20} {t['planned']:>10.2f} {t['served']:>10.2f}")
    print("\nThe chance constraint only guarantees that a recourse achieving")
    print("90 percent service EXISTS with probability 0.90. If the operator")
    print("then minimises realised cost instead, paying the penalty can beat")
    print("shipping, and the realised rate falls below the planned one.")

    print(f"\nper-scenario total cost")
    print(f"{'s':>3} {'p_s':>6}" + "".join(f"{r['name'][:14]:>16}"
                                           for r in models))
    for s in S:
        print(f"{s+1:>3} {p[s]:>6.2f}"
              + "".join(f"{stats[r['name']]['tot'][s]:>16.2f}"
                        for r in models))

    styles = ["-", "--", ":"]
    fig, ax = plt.subplots(figsize=(7.0, 4.4))
    for k, r in enumerate(models):
        v = np.sort(curves[r["name"]])
        f = np.arange(1, len(v) + 1) / len(v)
        ax.step(v, f, where="post", color="black", linestyle=styles[k],
                linewidth=1.3, label=r["name"])
    ax.set_xlabel("total cost (first stage plus realised recourse)")
    ax.set_ylabel("empirical cumulative probability")
    ax.set_ylim(0, 1.02)
    ax.grid(True, color="0.85", linewidth=0.5)
    ax.legend(loc="lower right", frameon=True, edgecolor="black")
    fig.tight_layout()
    fig.savefig("p1_cost_distributions.pdf")
    fig.savefig("p1_cost_distributions.png", dpi=160)
    print("\nwrote p1_cost_distributions.pdf and .png")
    print("The distribution has only 10 atoms, so each curve is a staircase")
    print("whose risers sit at the per-scenario costs above.")
