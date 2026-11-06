from fractions import Fraction

from ppl import Variable, Constraint_System, C_Polyhedron, MIP_Problem

CX = (3, 2)
CY = (4, 1)
AX = (2, 1)
AY = (1, 2)
RHS = 8


def solve(dim, rows, objective, scale=1):
    cs = Constraint_System()
    for r in rows:
        cs.insert(r)
    mip = MIP_Problem(dim, cs, objective)
    mip.set_optimization_mode("minimization")
    mip.solve()
    val = Fraction(int(mip.optimal_value()), scale)
    pt = mip.optimizing_point()
    d = int(pt.divisor())
    return val, tuple(Fraction(int(c), d) for c in pt.coefficients())


def generators(rows, dim):
    cs = Constraint_System()
    for r in rows:
        cs.insert(r)
    poly = C_Polyhedron(cs)
    pts, rays = [], []
    for g in poly.minimized_generators():
        c = [int(k) for k in g.coefficients()]
        if g.is_point():
            d = int(g.divisor())
            pts.append(tuple(Fraction(k, d) for k in c))
        elif g.is_ray():
            rays.append(tuple(c))
    return sorted(pts), sorted(rays)


def dot(a, b):
    return sum(ai * bi for ai, bi in zip(a, b))


def fmt(t):
    return "(" + ", ".join(str(k) for k in t) + ")"


x1, x2, y1, y2 = (Variable(i) for i in range(4))
ORIGINAL = (2 * x1 + x2 + y1 + 2 * y2 >= 8,
            x1 + 2 * x2 <= 6,
            2 * x1 + x2 <= 8,
            y1 - y2 <= 3,
            y1 <= 5,
            x1 >= 0, x2 >= 0, y1 >= 0, y2 >= 0)

print("=" * 64)
print("PROBLEM 7: Dantzig-Wolfe reformulation")
print("=" * 64)

a, b = Variable(0), Variable(1)
PX, RX = generators((a >= 0, b >= 0, a + 2 * b <= 6, 2 * a + b <= 8), 2)
PY, RY = generators((a >= 0, b >= 0, a - b <= 3, a <= 5), 2)

print("\nPART 1")
print("    linking constraint: 2x1 + x2 + y1 + 2y2 >= 8")
print("    X = {x >= 0 : x1 + 2x2 <= 6, 2x1 + x2 <= 8}")
print("    Y = {y >= 0 : y1 - y2 <= 3, y1 <= 5}")

print("\nPART 2")
print("    X extreme points:", ", ".join(fmt(p) for p in PX))
print("    X extreme rays  :", RX if RX else "none, X is bounded")
print("    Y extreme points:", ", ".join(fmt(p) for p in PY))
print("    Y extreme rays  :", ", ".join(fmt(r) for r in RY))

print("\nPART 3: master coefficients")
print(f"    {'generator':>14} {'cost':>8} {'linking':>9}")
for p in PX:
    print(f"    x point {fmt(p):>18} {str(dot(CX, p)):>8} {str(dot(AX, p)):>9}")
for q in PY:
    print(f"    y point {fmt(q):>18} {str(dot(CY, q)):>8} {str(dot(AY, q)):>9}")
for r in RY:
    print(f"    y ray   {fmt(r):>18} {str(dot(CY, r)):>8} {str(dot(AY, r)):>9}")

nL, nM, nN = len(PX), len(PY), len(RY)
dim = nL + nM + nN
V = [Variable(i) for i in range(dim)]
lam, mu, nu = V[:nL], V[nL:nL + nM], V[nL + nM:]

S = 3
obj = (sum(int(S * dot(CX, p)) * lam[i] for i, p in enumerate(PX))
       + sum(int(S * dot(CY, q)) * mu[i] for i, q in enumerate(PY))
       + sum(int(S * dot(CY, r)) * nu[i] for i, r in enumerate(RY)))
link = (sum(int(dot(AX, p)) * lam[i] for i, p in enumerate(PX))
        + sum(int(dot(AY, q)) * mu[i] for i, q in enumerate(PY))
        + sum(int(dot(AY, r)) * nu[i] for i, r in enumerate(RY)))
MASTER = ([link >= RHS,
           sum(lam) == 1,
           sum(mu) == 1]
          + [w >= 0 for w in V])

vo, so = solve(4, ORIGINAL, 3 * (3 * x1 + 2 * x2 + 4 * y1 + y2), scale=3)
vm, sm = solve(dim, MASTER, obj, scale=S)

print("\nPART 3: verification")
print(f"    original LP optimum : {vo}  at (x1,x2,y1,y2) = {fmt(so)}")
print(f"    master LP optimum   : {vm}  at weights {fmt(sm)}")
print(f"    the two agree       : {vo == vm}")

xr = tuple(sum(sm[i] * PX[i][k] for i in range(nL)) for k in (0, 1))
yr = tuple(sum(sm[nL + i] * PY[i][k] for i in range(nM))
           + sum(sm[nL + nM + i] * RY[i][k] for i in range(nN))
           for k in (0, 1))
print(f"    recovered x = {fmt(xr)},  y = {fmt(yr)}")
print(f"    recovered cost      : {dot(CX, xr) + dot(CY, yr)}")
print(f"    linking row value   : {dot(AX, xr) + dot(AY, yr)} >= {RHS}")
