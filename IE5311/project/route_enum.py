"""Exact enumeration of every capacity-feasible elementary route.

Held--Karp over capacity-feasible customer subsets: dp[mask][last] is the
least cost of a path leaving the depot, visiting exactly the customers in
mask, and ending at customer `last`. The optimal route cost for a mask is
min over last of dp[mask][last] + c[last, depot], so each feasible subset
contributes exactly one column, with its true optimal visiting sequence.
"""
import time

from cvrp_data import Instance


def enumerate_routes(ins, Q=None):
    Q = ins.Q if Q is None else Q
    cust = ins.customers
    n = len(cust)
    dep = ins.depot
    d = [ins.demand[i] for i in cust]
    cc = [[ins.c[cust[i], cust[j]] if i != j else 0 for j in range(n)]
          for i in range(n)]
    c0 = [ins.c[dep, cust[i]] for i in range(n)]
    cback = [ins.c[cust[i], dep] for i in range(n)]

    dp = {}
    load = {}
    for i in range(n):
        if d[i] <= Q:
            dp[1 << i] = {i: c0[i]}
            load[1 << i] = d[i]

    frontier = list(dp)
    while frontier:
        nxt = []
        for mask in frontier:
            lm, ends = load[mask], dp[mask]
            for j in range(n):
                b = 1 << j
                if mask & b or lm + d[j] > Q:
                    continue
                nm = mask | b
                best = min(ends[last] + cc[last][j] for last in ends)
                tgt = dp.get(nm)
                if tgt is None:
                    dp[nm] = {j: best}
                    load[nm] = lm + d[j]
                    nxt.append(nm)
                elif j not in tgt or best < tgt[j]:
                    tgt[j] = best
        frontier = nxt

    routes = []
    for mask, ends in dp.items():
        best, arg = None, None
        for last, v in ends.items():
            t = v + cback[last]
            if best is None or t < best:
                best, arg = t, last
        members = tuple(cust[i] for i in range(n) if mask >> i & 1)
        routes.append((members, best, load[mask]))
    return routes


def rebuild_sequence(ins, members, Q=None):
    """Optimal visiting order for one customer set (small exact TSP)."""
    Q = ins.Q if Q is None else Q
    dep = ins.depot
    m = list(members)
    n = len(m)
    dp = {(1 << i, i): ins.c[dep, m[i]] for i in range(n)}
    par = {}
    for size in range(1, n):
        for (mask, last), v in list(dp.items()):
            if bin(mask).count("1") != size:
                continue
            for j in range(n):
                if mask >> j & 1:
                    continue
                nm, nv = mask | 1 << j, v + ins.c[m[last], m[j]]
                if dp.get((nm, j), 1e18) > nv:
                    dp[(nm, j)] = nv
                    par[(nm, j)] = last
    full = (1 << n) - 1
    last = min(range(n), key=lambda i: dp[(full, i)] + ins.c[m[i], dep])
    seq, mask = [], full
    while True:
        seq.append(m[last])
        p = par.get((mask, last))
        if p is None:
            break
        mask, last = mask ^ (1 << last), p
    return [dep] + seq[::-1] + [dep]


if __name__ == "__main__":
    ins = Instance()
    print("=" * 74)
    print("Exact enumeration of all capacity-feasible routes")
    print("=" * 74)
    for Q in (ins.Q, 7500):
        t0 = time.perf_counter()
        R = enumerate_routes(ins, Q)
        dt = time.perf_counter() - t0
        sz = {}
        for mem, _, _ in R:
            sz[len(mem)] = sz.get(len(mem), 0) + 1
        print(f"\nQ = {Q}: {len(R)} feasible routes in {dt:.1f} s")
        print(f"   by size: {dict(sorted(sz.items()))}")
        cheap = min(R, key=lambda r: r[1])
        print(f"   cheapest route cost {cheap[1]} over {cheap[0]}")
    R = enumerate_routes(ins)
    chk = [r for r in R if len(r[0]) <= 3][:3]
    print("\nsequence rebuild check:")
    for mem, cost, ld in chk:
        seq = rebuild_sequence(ins, mem)
        print(f"   {mem} cost {cost} load {ld} -> {seq} "
              f"recomputed {ins.cost(seq)} match={ins.cost(seq) == cost}")
