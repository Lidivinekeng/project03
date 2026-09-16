"""Audit of two unverified claims in part1_formulations.docx."""
import itertools, math
import numpy as np, pulp
S = pulp.PULP_CBC_CMD(msg=0)
COORDS = {1:(0.,0.), 2:(4.,1.), 3:(5.,4.), 4:(2.,5.), 5:(-1.,3.), 6:(1.,2.)}
V = sorted(COORDS); n = len(V)
c = {(i,j): math.dist(COORDS[i], COORDS[j]) for i in V for j in V if i != j}

def degree_constraints(m, x):
    for i in V:
        m += pulp.lpSum(x[i,j] for j in V if j != i) == 1
        m += pulp.lpSum(x[j,i] for j in V if j != i) == 1

def dfj_lp():
    """Directed DFJ with EVERY subtour constraint, integrality dropped."""
    m = pulp.LpProblem("dfj_lp", pulp.LpMinimize)
    x = {k: pulp.LpVariable(f"x{k}", 0, 1) for k in c}
    m += pulp.lpSum(c[k]*x[k] for k in c)
    degree_constraints(m, x)
    cnt = 0
    for size in range(2, n):
        for Sset in itertools.combinations(V, size):
            inside = [(i,j) for i in Sset for j in Sset if i != j]
            m += pulp.lpSum(x[k] for k in inside) <= len(Sset) - 1
            cnt += 1
    m.solve(S); return pulp.value(m.objective), cnt

def mtz_lp():
    """Directed MTZ, integrality dropped."""
    m = pulp.LpProblem("mtz_lp", pulp.LpMinimize)
    x = {k: pulp.LpVariable(f"x{k}", 0, 1) for k in c}
    u = {i: pulp.LpVariable(f"u{i}", 2, n) for i in V if i != 1}
    m += pulp.lpSum(c[k]*x[k] for k in c)
    degree_constraints(m, x)
    cnt = 0
    for i in V:
        for j in V:
            if i != j and i != 1 and j != 1:
                m += u[i] - u[j] + n*x[i,j] <= n - 1
                cnt += 1
    m.solve(S); return pulp.value(m.objective), cnt

def tsp_exact():
    m = pulp.LpProblem("tsp", pulp.LpMinimize)
    x = {k: pulp.LpVariable(f"x{k}", cat=pulp.LpBinary) for k in c}
    m += pulp.lpSum(c[k]*x[k] for k in c)
    degree_constraints(m, x)
    for size in range(2, n):
        for Sset in itertools.combinations(V, size):
            inside = [(i,j) for i in Sset for j in Sset if i != j]
            m += pulp.lpSum(x[k] for k in inside) <= len(Sset) - 1
    m.solve(S); return pulp.value(m.objective)

print("CLAIM A: 'the DFJ relaxation is tighter than the MTZ relaxation'")
print("-"*64)
opt = tsp_exact()
dfj, ndfj = dfj_lp()
mtz, nmtz = mtz_lp()
print(f"  integer optimum (directed)        : {opt:.4f}")
print(f"  DFJ LP bound  ({ndfj:3d} subtour rows): {dfj:.4f}   gap {opt-dfj:.4f}")
print(f"  MTZ LP bound  ({nmtz:3d} order rows)  : {mtz:.4f}   gap {opt-mtz:.4f}")
print(f"  DFJ bound is higher (tighter)     : {dfj > mtz + 1e-9}")
print(f"  MTZ rows {nmtz} vs DFJ rows {ndfj}: MTZ is the smaller model: {nmtz < ndfj}")

print("\nCLAIM B: 'the node-arc incidence matrix is totally unimodular'")
print("-"*64)
ARCS = [("s","a"),("s","b"),("a","b"),("a","c"),("b","d"),
        ("d","a"),("d","c"),("c","t"),("d","t")]
NODES = sorted({x for a in ARCS for x in a})
A = np.zeros((len(NODES), len(ARCS))); idx = {v:k for k,v in enumerate(NODES)}
for col,(i,j) in enumerate(ARCS):
    A[idx[i],col], A[idx[j],col] = 1., -1.
worst, total = 0.0, 0
for k in range(1, min(A.shape)+1):
    cnt = 0
    for rs in itertools.combinations(range(A.shape[0]), k):
        for cs in itertools.combinations(range(A.shape[1]), k):
            d = np.linalg.det(A[np.ix_(rs,cs)])
            worst = max(worst, min(abs(d), abs(d-1), abs(d+1)))
            cnt += 1
    total += cnt
    print(f"  order {k}: {cnt:5d} submatrices checked")
print(f"  TOTAL checked (all orders 1..6)   : {total}")
print(f"  worst deviation from {{0,+1,-1}}    : {worst:.2e}")
print(f"  exhaustive check passes           : {worst < 1e-7}")
print(f"  (the document quoted 4164, which is orders 1..4 only)")
