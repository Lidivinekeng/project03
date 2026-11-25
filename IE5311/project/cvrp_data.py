import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
INSTANCE = os.path.join(HERE, "data", "E-n22-k4.vrp")


def read_vrp(path=INSTANCE):
    coord, dem, meta, sec = {}, {}, {}, None
    with open(path) as fh:
        for raw in fh:
            line = raw.strip()
            if not line or line == "EOF":
                continue
            if line.endswith("SECTION"):
                sec = line
                continue
            if ":" in line and sec is None:
                k, v = line.split(":", 1)
                meta[k.strip()] = v.strip()
                continue
            p = line.split()
            if sec == "NODE_COORD_SECTION":
                coord[int(p[0])] = (float(p[1]), float(p[2]))
            elif sec == "DEMAND_SECTION":
                dem[int(p[0])] = int(p[1])
            elif sec == "DEPOT_SECTION":
                if int(p[0]) > 0:
                    meta["DEPOT"] = int(p[0])
    return coord, dem, meta


def euc2d(a, b):
    """TSPLIB EUC_2D: nearest integer, nint(x) = floor(x + 0.5)."""
    return int(math.floor(math.hypot(a[0] - b[0], a[1] - b[1]) + 0.5))


class Instance:
    def __init__(self, path=INSTANCE):
        coord, dem, meta = read_vrp(path)
        self.name = meta["NAME"]
        self.n = int(meta["DIMENSION"])
        self.Q = int(meta["CAPACITY"])
        self.depot = meta.get("DEPOT", 1)
        self.nodes = sorted(coord)
        self.coord = coord
        self.demand = dem
        self.customers = [i for i in self.nodes if i != self.depot]
        self.c = {(i, j): euc2d(coord[i], coord[j])
                  for i in self.nodes for j in self.nodes if i != j}
        self.D = sum(dem[i] for i in self.customers)
        self.comment = meta.get("COMMENT", "")

    def cost(self, route):
        """route is a node sequence starting and ending at the depot."""
        return sum(self.c[route[k], route[k + 1]]
                   for k in range(len(route) - 1))

    def load(self, route):
        return sum(self.demand[i] for i in route if i != self.depot)


if __name__ == "__main__":
    ins = Instance()
    print("=" * 72)
    print("PROBLEM 1: data and preliminary analysis")
    print("=" * 72)
    print(f"instance            : {ins.name}")
    print(f"comment             : {ins.comment}")
    print(f"dimension n         : {ins.n}  (1 depot + {len(ins.customers)} customers)")
    print(f"depot node          : {ins.depot}")
    print(f"vehicle capacity Q  : {ins.Q}")
    print(f"edge weight type    : EUC_2D, nint(sqrt(dx^2+dy^2))")

    print(f"\n(b) total demand D = sum_i d_i = {ins.D}")
    lb = -(-ins.D // ins.Q)
    print(f"    lower bound on vehicles = ceil(D/Q) = ceil({ins.D}/{ins.Q})"
          f" = ceil({ins.D/ins.Q:.4f}) = {lb}")
    print(f"    K given by the instance name = 4, so the bound is tight")
    print(f"    total fleet capacity K*Q = {4*ins.Q}, slack = {4*ins.Q-ins.D}")

    print("\n(c) travel costs for the data check "
          "(CVRPLIB numbering, node 1 = depot):")
    for (i, j) in [(1, 2), (1, 3), (2, 3)]:
        a, b = ins.coord[i], ins.coord[j]
        raw = math.hypot(a[0] - b[0], a[1] - b[1])
        print(f"    c_{i},{j} : {a} -> {b},  exact {raw:.6f},  "
              f"rounded {ins.c[i, j]}")

    print(f"\n    demand range  : {min(ins.demand[i] for i in ins.customers)}"
          f" .. {max(ins.demand[i] for i in ins.customers)}")
    print(f"    largest demand: {max(ins.demand[i] for i in ins.customers)}"
          f" <= Q = {ins.Q}, so every customer is individually servable")
    print(f"    cost matrix   : {len(ins.c)} ordered pairs, "
          f"symmetric = {all(ins.c[i,j] == ins.c[j,i] for i,j in ins.c)}")
