import argparse
import csv
import random
import sys

INF = float("inf")

class Result:
    def __init__(self, cost, flights, cities, flights_used, coupons_used):
        self.cost = cost
        self.flights = flights
        self.cities = cities
        self.flights_used = flights_used
        self.coupons_used = coupons_used


def validate(n, edges, k, c):
    if not isinstance(n, int) or n < 1:
        raise ValueError("N must be an integer >= 1")
    if k < 0:
        raise ValueError("K (max stops) must be >= 0")
    if c < 0:
        raise ValueError("C (coupons) must be >= 0")
    for (u, v, p) in edges:
        if not (1 <= u <= n and 1 <= v <= n):
            raise ValueError(f"Flight ({u}->{v}) has a city outside 1..{n}")
        if p < 0:
            raise ValueError(f"Flight ({u}->{v}) has a negative price {p}")


def solve(n, edges, k, c):
    validate(n, edges, k, c)

    if n == 1:
        return Result(0, [], [1], 0, 0)

    F = min(k + 1, n - 1)
    C = min(c, F)

    work = [(i, u, v, p) for i, (u, v, p) in enumerate(edges) if u != v]

    dp = [[[INF] * (C + 1) for _ in range(n + 1)] for _ in range(F + 1)]
    par = [[[None] * (C + 1) for _ in range(n + 1)] for _ in range(F + 1)]
    dp[0][1][0] = 0

    last_layer = 0
    for f in range(F):
        cur, nxt, npar = dp[f], dp[f + 1], par[f + 1]
        progressed = False
        for (idx, u, v, p) in work:
            row = cur[u]
            for cc in range(C + 1):
                d = row[cc]
                if d == INF:
                    continue
                nd = d + p
                if nd < nxt[v][cc]:
                    nxt[v][cc] = nd
                    npar[v][cc] = (idx, cc, False)
                    progressed = True
                if cc < C and p > 0:
                    nd = d + p // 2
                    if nd < nxt[v][cc + 1]:
                        nxt[v][cc + 1] = nd
                        npar[v][cc + 1] = (idx, cc, True)
                        progressed = True
        last_layer = f + 1
        if not progressed:
            break

    best, bf, bc = INF, -1, -1
    for f in range(last_layer + 1):
        for cc in range(C + 1):
            if dp[f][n][cc] < best:
                best, bf, bc = dp[f][n][cc], f, cc
    if best == INF:
        return Result(-1, [], [], 0, 0)

    steps = []
    f, v, cc = bf, n, bc
    while f > 0:
        idx, pc, used = par[f][v][cc]
        steps.append((idx, used))
        v = edges[idx][0]
        cc = pc
        f -= 1
    steps.reverse()
    cities = [1] + [edges[i][1] for i, _ in steps]
    return Result(int(best), steps, cities, bf, bc)


def to_int(tok, what):
    try:
        return int(tok)
    except ValueError:
        raise ValueError(f"{what} must be an integer, got '{tok}'")


def read_option1(stream):
    def tokens():
        for line in stream:
            for t in line.split():
                yield t
    it = tokens()

    def nxt(what):
        try:
            return to_int(next(it), what)
        except StopIteration:
            raise ValueError(f"Input ended early while reading {what}")

    n, m = nxt("N"), nxt("M")
    k, c = nxt("K"), nxt("C")
    if m < 0:
        raise ValueError("M must be >= 0")
    edges = [(nxt("u"), nxt("v"), nxt("price")) for _ in range(m)]
    return n, edges, k, c


def read_graph_csv(path):
    edges, n_decl = [], None
    with open(path, newline="") as fh:
        for row in csv.reader(fh):
            row = [x.strip() for x in row if x is not None]
            if not row or all(x == "" for x in row) or row[0].startswith("#"):
                continue
            if row[0].lower() in ("n", "cities") and len(row) >= 2:
                n_decl = to_int(row[1], "N")
                continue
            if row[0].lower() in ("u", "from", "src", "source"):
                continue
            if row[0].lower() in ("total_cost", "route", "flights_used", "coupons_used"):
                continue
            if len(row) < 3:
                raise ValueError(f"Bad CSV row (need u,v,price): {row}")
            edges.append((to_int(row[0], "u"), to_int(row[1], "v"),
                          to_int(row[2], "price")))
    n = n_decl if n_decl is not None else max([max(u, v) for u, v, _ in edges] + [1])
    return n, edges


def generate_graph(n, m, k, max_price, rng):
    edges = []
    if n >= 2:
        F = min(k + 1, n - 1)
        L = rng.randint(1, F)
        mids = rng.sample(range(2, n), L - 1) if L > 1 else []
        route = [1] + mids + [n]
        for a, b in zip(route, route[1:]):
            edges.append((a, b, rng.randint(1, max_price)))
        extra = max(0, m - len(edges))
        for _ in range(extra):
            if n < 2:
                break
            u, v = rng.sample(range(1, n + 1), 2)
            edges.append((u, v, rng.randint(1, max_price)))
        rng.shuffle(edges)
    return edges


def write_output_csv(path, n, edges, res):
    on_path = {idx: used for idx, used in res.flights}
    with open(path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["N", n])
        w.writerow(["u", "v", "price", "on_path", "coupon_used", "paid"])
        for i, (u, v, p) in enumerate(edges):
            if i in on_path:
                used = on_path[i]
                w.writerow([u, v, p, "x", "x" if used else "", p // 2 if used else p])
            else:
                w.writerow([u, v, p, "", "", ""])
        w.writerow([])
        w.writerow(["total_cost", res.cost])
        if res.cost != -1:
            w.writerow(["route", "->".join(map(str, res.cities))])
            w.writerow(["flights_used", res.flights_used])
            w.writerow(["coupons_used", res.coupons_used])


def describe(res, edges):
    if res.cost == -1:
        return "No valid route within the given stops limit."
    lines = [f"Route   : {' -> '.join(map(str, res.cities))}",
             f"Stops   : {max(0, res.flights_used - 1)}",
             f"Coupons : {res.coupons_used}"]
    for idx, used in res.flights:
        u, v, p = edges[idx]
        lines.append(f"  {u} -> {v}: {p}" + (f" -> {p//2} (coupon)" if used else ""))
    return "\n".join(lines)


def visualize(n, edges, res, k, c, save=None, show=True):
    try:
        import matplotlib
        if save and not show:
            matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from matplotlib.animation import FuncAnimation
        from matplotlib.patches import FancyArrowPatch
    except ImportError:
        print("matplotlib not installed - skipping visualization "
              "(pip install matplotlib)", file=sys.stderr)
        return

    import math
    try:
        import networkx as nx
        g = nx.Graph()
        g.add_nodes_from(range(1, n + 1))
        g.add_edges_from((u, v) for u, v, _ in edges)
        pos = nx.spring_layout(g, seed=3, k=1.5 / math.sqrt(max(n, 1)))
    except Exception:
        pos = {i: (math.cos(2*math.pi*(i-1)/n), math.sin(2*math.pi*(i-1)/n))
               for i in range(1, n + 1)}

    path_edges = {idx: used for idx, used in res.flights}
    route_nodes = set(res.cities)

    def node_color(i):
        if i == 1:
            return "limegreen"
        if i == n:
            return "red"
        if i in route_nodes and res.cost != -1:
            return "orange"
        return "lightgrey"

    seen = {}
    rads = []
    for (u, v, _) in edges:
        key = (u, v)
        seen[key] = seen.get(key, 0) + 1
        base = 0.15 + 0.12 * (seen[key] - 1)
        rads.append(base)

    fig, ax = plt.subplots(figsize=(9, 7))
    panel = fig.text(0.02, 0.02, "", fontsize=11, family="monospace")

    def draw(upto):
        ax.clear()
        ax.set_axis_off()
        flown = [idx for idx, _ in res.flights[:upto]]
        cost = 0
        coupons = 0
        for idx in flown:
            p = edges[idx][2]
            if path_edges[idx]:
                cost += p // 2
                coupons += 1
            else:
                cost += p
        for i, (u, v, p) in enumerate(edges):
            if u == v:
                continue
            on = i in path_edges
            flown_now = i in flown
            coupon = on and path_edges[i]
            if flown_now:
                col = "gold" if coupon else "royalblue"
                lw = 3.5
            elif on and res.cost != -1:
                col, lw = "lightsteelblue", 2
            else:
                col, lw = "#bbbbbb", 1
            arr = FancyArrowPatch(pos[u], pos[v], arrowstyle="-|>", mutation_scale=16,
                                  connectionstyle=f"arc3,rad={rads[i]}", color=col,
                                  lw=lw, shrinkA=14, shrinkB=14, zorder=1)
            ax.add_patch(arr)
            (x1, y1), (x2, y2) = pos[u], pos[v]
            mx, my = (x1 + x2) / 2, (y1 + y2) / 2
            dx, dy = x2 - x1, y2 - y1
            off = rads[i] * 0.5
            lx, ly = mx - dy * off, my + dx * off
            label = f"{p}->{p//2}" if (coupon and flown_now) else str(p)
            ax.text(lx, ly, label, fontsize=9, ha="center", va="center",
                    color="darkgoldenrod" if (coupon and flown_now) else "black",
                    bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.8),
                    zorder=3)
        for i in range(1, n + 1):
            ax.scatter(*pos[i], s=700, c=node_color(i), edgecolors="black", zorder=2)
            ax.text(*pos[i], str(i), ha="center", va="center", fontweight="bold", zorder=4)
        xs = [p_[0] for p_ in pos.values()]
        ys = [p_[1] for p_ in pos.values()]
        ax.set_xlim(min(xs) - .4, max(xs) + .4)
        ax.set_ylim(min(ys) - .4, max(ys) + .4)
        if res.cost == -1:
            ax.set_title(f"Budget Traveller (K={k}, C={c})  -  NO ROUTE (-1)")
        else:
            ax.set_title(f"Budget Traveller (K={k}, C={c})  -  optimal cost {res.cost}")
        stops = max(0, upto - 1)
        panel.set_text(f"Running cost: {cost}    Flights: {upto}/{res.flights_used}    "
                       f"Stops used: {stops}/{k}    Coupons used: {coupons}/{c}")

    total = len(res.flights)
    frames = list(range(0, total + 1)) + [total] * 2
    anim = FuncAnimation(fig, lambda f: draw(f), frames=frames, interval=1200,
                         repeat=False)
    fig.subplots_adjust(bottom=0.08)
    if save:
        try:
            anim.save(save, writer="pillow", fps=1)
            print(f"Animation saved to {save}")
        except Exception as e:
            print(f"Could not save animation ({e}). Install pillow.", file=sys.stderr)
    if show:
        plt.show()
    plt.close(fig)


def brute_force(n, edges, k, c):
    if n == 1:
        return 0
    best = INF
    out = {}
    for (u, v, p) in edges:
        out.setdefault(u, []).append((v, p))
    max_flights = k + 1

    def dfs(city, flights, coupons_left, cost):
        nonlocal best
        if city == n:
            best = min(best, cost)
        if flights == max_flights:
            return
        for (v, p) in out.get(city, []):
            dfs(v, flights + 1, coupons_left, cost + p)
            if coupons_left > 0:
                dfs(v, flights + 1, coupons_left - 1, cost + p // 2)

    dfs(1, 0, c, 0)
    return -1 if best == INF else int(best)


def selftest(trials=4000):
    rng = random.Random(2026)
    fixed = [
        (1, [], 0, 0, 0),
        (2, [], 3, 2, -1),
        (2, [(1, 2, 10)], 0, 0, 10),
        (2, [(1, 2, 10)], 0, 1, 5),
        (2, [(1, 2, 9)], 0, 1, 4),
        (2, [(1, 2, 1)], 0, 1, 0),
        (2, [(2, 1, 5)], 3, 3, -1),
        (3, [(1, 2, 5), (2, 3, 5)], 0, 5, -1),
        (3, [(1, 2, 5), (2, 3, 5)], 1, 0, 10),
        (3, [(1, 2, 5), (2, 3, 5)], 1, 5, 4),
        (3, [(1, 3, 100), (1, 2, 1), (2, 3, 1)], 0, 0, 100),
        (3, [(1, 3, 100), (1, 2, 1), (2, 3, 1)], 1, 0, 2),
        (3, [(1, 3, 100), (1, 2, 1), (2, 3, 1)], 0, 1, 50),
        (3, [(1, 2, 0), (2, 3, 0)], 1, 1, 0),
        (3, [(1, 1, 1), (1, 2, 4), (2, 3, 4)], 5, 1, 6),
        (3, [(1, 2, 4), (1, 2, 2), (2, 3, 8)], 1, 1, 6),
        (4, [(1, 2, 1), (2, 1, 1), (2, 4, 1)], 10, 0, 2),
        (4, [(1, 2, 1), (2, 3, 1), (3, 4, 1)], 1, 9, -1),
        (5, [(1, 5, 10**9)], 0, 1, 5 * 10**8),
    ]
    for i, (n, e, k, c, exp) in enumerate(fixed):
        got = solve(n, e, k, c).cost
        assert got == exp, f"fixed case {i}: expected {exp}, got {got}"
    print(f"fixed edge cases     : {len(fixed)} passed")

    for t in range(trials):
        n = rng.randint(1, 7)
        m = rng.randint(0, 12)
        edges = [(rng.randint(1, n), rng.randint(1, n), rng.randint(0, 20))
                 for _ in range(m)]
        k, c = rng.randint(0, 5), rng.randint(0, 5)
        r = solve(n, edges, k, c)
        assert r.cost == brute_force(n, edges, k, c), (n, edges, k, c)
        if r.cost != -1 and n > 1:
            assert r.cities[0] == 1 and r.cities[-1] == n
            assert len(r.flights) <= k + 1 and r.coupons_used <= c
            tot, cu, cur = 0, 0, 1
            for idx, used in r.flights:
                u, v, p = edges[idx]
                assert u == cur
                cur = v
                tot += p // 2 if used else p
                cu += used
            assert tot == r.cost and cu == r.coupons_used and cur == n
    print(f"random vs brute force: {trials} passed")

    for t in range(500):
        n = rng.randint(2, 15)
        k = rng.randint(0, 6)
        e = generate_graph(n, rng.randint(0, 40), k, 50, rng)
        assert solve(n, e, k, rng.randint(0, 3)).cost != -1
    print("generator validity   : 500 passed")
    print("ALL TESTS PASSED")


def main():
    ap = argparse.ArgumentParser(description="Problem 3 - Budget Traveller with Coupons")
    ap.add_argument("--mode", type=int, choices=[1, 2, 3],
                    help="1=stdin  2=CSV file  3=random graph")
    ap.add_argument("--csv", help="graph CSV (mode 2)")
    ap.add_argument("--K", type=int, help="max stops (modes 2,3)")
    ap.add_argument("--C", type=int, help="coupons (modes 2,3)")
    ap.add_argument("--N", type=int, help="cities (mode 3)")
    ap.add_argument("--M", type=int, help="flights (mode 3)")
    ap.add_argument("--maxprice", type=int, default=100)
    ap.add_argument("--seed", type=int)
    ap.add_argument("--out", default="output_graph.csv")
    ap.add_argument("--viz", action="store_true")
    ap.add_argument("--save-viz")
    ap.add_argument("--verbose", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()

    if a.selftest:
        selftest()
        return

    try:
        mode = a.mode
        if mode is None:
            if sys.stdin.isatty():
                print("=== Budget Traveller with Coupons ===")
                print("1) Type the graph here (N M / K C / M lines of u v p)")
                print("2) Read graph from a CSV file")
                print("3) Generate a random graph")
                mode = int(input("Choose option (1/2/3): "))
                if mode == 1:
                    print("Enter:  N M   then   K C   then M lines of  u v p")
            else:
                mode = 1

        if mode == 1:
            n, edges, k, c = read_option1(sys.stdin)
        elif mode == 2:
            if a.K is None or a.C is None:
                a.K, a.C = (int(x) for x in input("K C: ").split())
            path = a.csv or input("CSV path: ").strip()
            n, edges = read_graph_csv(path)
            k, c = a.K, a.C
        else:
            if a.K is None or a.C is None:
                a.K, a.C = (int(x) for x in input("K C: ").split())
            n = a.N if a.N is not None else int(input("Number of cities N: "))
            m = a.M if a.M is not None else int(input("Number of flights M: "))
            if n < 1 or m < 0:
                raise ValueError("N must be >= 1 and M >= 0")
            rng = random.Random(a.seed)
            k, c = a.K, a.C
            edges = generate_graph(n, m, k, max(1, a.maxprice), rng)
            print(f"Generated graph: N={n}, M={len(edges)}, K={k}, C={c}")
            for u, v, p in edges:
                print(u, v, p)

        res = solve(n, edges, k, c)
    except (ValueError, OSError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    print(res.cost)
    if a.verbose:
        print(describe(res, edges))
    write_output_csv(a.out, n, edges, res)
    print(f"(output CSV written to {a.out})")
    if sys.stdin.isatty() and not (a.viz or a.save_viz):
        if input("Show animation? (y/n): ").strip().lower().startswith("y"):
            a.viz = True
    if a.viz or a.save_viz:
        visualize(n, edges, res, k, c, save=a.save_viz, show=a.viz)


if __name__ == "__main__":
    main()