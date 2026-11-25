import numpy as np
from scipy.optimize import fsolve, linprog, minimize

OK = []


def chk(name, cond, detail=""):
    OK.append(bool(cond))
    print(f"  [{'PASS' if cond else 'FAIL'}] {name}  {detail}")


print("=" * 76)
print("INDEPENDENT AUDIT: different method for every reported number")
print("=" * 76)

print("\nP1  KKT system solved as a root-find, not an optimisation")
n = 6
I = np.arange(1, n + 1)
for m1, m2, ref in [(4.0, 18.0, -1.6965357595), (4.5, 21.0, -1.2665057255)]:
    def F(v):
        p = np.exp(-1 - v[0] - v[1] * I - v[2] * I ** 2)
        return [p.sum() - 1, I @ p - m1, (I ** 2) @ p - m2]
    v = fsolve(F, [0.0, 0.0, 0.0], full_output=False, xtol=1e-14)
    p = np.exp(-1 - v[0] - v[1] * I - v[2] * I ** 2)
    negH = float(p @ np.log(p))
    chk(f"m1={m1}, m2={m2}: -H matches", abs(negH - ref) < 1e-8,
        f"root-find {negH:.10f} vs reported {ref}")
    chk("   moments satisfied", max(abs(np.array(F(v)))) < 1e-10,
        f"max residual {max(abs(np.array(F(v)))):.2e}")

print("\nP2  follower QP re-solved by SLSQP at the reported x*")
xs = 8.0 / 3.0
r = minimize(lambda y: 0.5 * y[0] ** 2 + y[1] ** 2, [1.0, 3.0],
             constraints=[{"type": "eq", "fun": lambda y: y[0] + y[1] - 4},
                          {"type": "ineq", "fun": lambda y: xs - y[0]}],
             bounds=[(0, None), (0, None)], tol=1e-14)
chk("follower response y* = (8/3, 4/3)", np.abs(r.x - [8/3, 4/3]).max() < 1e-6,
    f"SLSQP {np.round(r.x, 8)}")
chk("leader cost 4.8", abs(0.8 * xs + 2 * r.x[1] - 4.8) < 1e-6,
    f"{0.8*xs + 2*r.x[1]:.8f}")
alt = [0.8 * x + 2 * (4 - min(x, 8/3)) for x in np.linspace(0, 4, 4001)]
chk("no better x on a coarse independent sweep", min(alt) >= 4.8 - 1e-6,
    f"min {min(alt):.8f}")

print("\nP3  extensive form re-solved by HiGHS via scipy.linprog")
C = np.array([0.004, 0.006, 0.003])
P = np.array([0.3, 0.4, 0.3])
G = np.array([[1.06, 1.01, 0.98], [0.95, 1.03, 1.02], [1.10, 0.97, 0.96]])
L = np.array([1.01, 1.00, 1.02])
K = np.array([0.08, 0.09, 0.10])
c = np.concatenate([C, P * K])
Aub = np.hstack([-G, -np.eye(3)])
res = linprog(c, A_ub=Aub, b_ub=-L,
              A_eq=np.array([[1, 1, 1, 0, 0, 0.0]]), b_eq=[1.0],
              bounds=[(0, None)] * 6, method="highs")
chk("objective 0.0037885714", abs(res.fun - 0.0037885714) < 1e-10,
    f"HiGHS {res.fun:.10f}")
chk("x* = (3/7, 0, 4/7)",
    np.abs(res.x[:3] - [3/7, 0, 4/7]).max() < 1e-8,
    f"{np.round(res.x[:3], 8)}")
chk("b* = (0, 0.01, 0)", np.abs(res.x[3:] - [0, 0.01, 0]).max() < 1e-8,
    f"{np.round(res.x[3:], 8)}")

print("\nP4  QP re-solved by SLSQP, and KKT checked at the reported x*")
xb = np.array([0.7, 0.2, 0.1])
Sig = np.diag([4.0, 1.0, 1.0])
r = minimize(lambda x: ((x - xb) ** 2).sum(), np.ones(3) / 3,
             constraints=[{"type": "eq", "fun": lambda x: x.sum() - 1},
                          {"type": "ineq", "fun": lambda x: 1 - x @ Sig @ x}],
             bounds=[(0, None)] * 3, tol=1e-14)
xstar = np.array([0.461424, 0.310037, 0.228539])
chk("x* agrees with SLSQP", np.abs(r.x - xstar).max() < 1e-5,
    f"SLSQP {np.round(r.x, 6)}")
chk("objective 0.08554925", abs(r.fun - 0.0855492535) < 1e-7,
    f"SLSQP {r.fun:.10f}")
chk("risk constraint active", abs(r.x @ Sig @ r.x - 1) < 1e-6,
    f"x'Sigma x = {r.x @ Sig @ r.x:.10f}")
g = 2 * (r.x - xb)
A = 2 * Sig @ r.x
M = np.column_stack([A, np.ones(3)])
coef, *_ = np.linalg.lstsq(M, -g, rcond=None)
resid = np.linalg.norm(M @ coef + g)
chk("stationarity 2(x-xbar) + eta*2*Sigma*x + nu*1 = 0 (x>0 so z=0)",
    resid < 1e-4 and coef[0] > 0,
    f"eta={coef[0]:.6f} >= 0, nu={coef[1]:.6f}, residual {resid:.2e}")

print("\n" + "=" * 76)
print(f"{sum(OK)}/{len(OK)} independent checks passed")
print("=" * 76)
