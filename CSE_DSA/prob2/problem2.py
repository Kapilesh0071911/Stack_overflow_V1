
import math
import random
import time
import matplotlib.pyplot as plt


def distance(p1, p2):
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1])


def brute_force(points):
    n = len(points)

    if n < 2:
        return None, None

    best_distance = float("inf")
    best_pair = None

    for i in range(n):
        for j in range(i + 1, n):
            d = distance(points[i], points[j])

            if d < best_distance:
                best_distance = d
                best_pair = (points[i], points[j])

    return best_distance, best_pair


def closest_pair_dc(points):
    if len(points) < 2:
        return None, None

    indexed = [(x, y, i) for i, (x, y) in enumerate(points)]
    by_x = sorted(indexed, key=lambda p: (p[0], p[1], p[2]))
    by_y = sorted(indexed, key=lambda p: (p[1], p[0], p[2]))

    def solve(px, py):
        n = len(px)

        if n <= 3:
            best_d = float("inf")
            best_pair = None

            for i in range(n):
                for j in range(i + 1, n):
                    p = (px[i][0], px[i][1])
                    q = (px[j][0], px[j][1])
                    d = distance(p, q)

                    if d < best_d:
                        best_d = d
                        best_pair = (p, q)

            return best_d, best_pair

        mid = n // 2
        left_x = px[:mid]
        right_x = px[mid:]
        left_ids = {p[2] for p in left_x}

        left_y = [p for p in py if p[2] in left_ids]
        right_y = [p for p in py if p[2] not in left_ids]

        dl, pair_l = solve(left_x, left_y)
        dr, pair_r = solve(right_x, right_y)

        if dl <= dr:
            best_d, best_pair = dl, pair_l
        else:
            best_d, best_pair = dr, pair_r

        mid_x = px[mid][0]
        strip = [p for p in py if abs(p[0] - mid_x) < best_d]

        for i in range(len(strip)):
            j = i + 1

            while j < len(strip) and strip[j][1] - strip[i][1] < best_d:
                p = (strip[i][0], strip[i][1])
                q = (strip[j][0], strip[j][1])
                d = distance(p, q)

                if d < best_d:
                    best_d = d
                    best_pair = (p, q)

                j += 1

        return best_d, best_pair

    return solve(by_x, by_y)


def timed_run(function, points):
    start = time.perf_counter()
    result = function(points)
    elapsed_ms = (time.perf_counter() - start) * 1000
    return result, elapsed_ms


def visualize(points, pair, brute_ms, dc_ms, sizes, brute_times, dc_times):
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    ax = axes[0]
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]

    ax.scatter(xs, ys, color="royalblue", label="Points", zorder=2)

    if pair:
        p1, p2 = pair
        ax.plot(
            [p1[0], p2[0]],
            [p1[1], p2[1]],
            "r-o",
            linewidth=2,
            markersize=6,
            label="Closest pair",
            zorder=3
        )

    ax.set_title("Closest Pair of Points")
    ax.set_xlabel("X coordinate")
    ax.set_ylabel("Y coordinate")
    ax.grid(True, alpha=0.3)
    ax.legend()

    axes[1].plot(sizes, brute_times, "o-", label="Brute Force")
    axes[1].plot(sizes, dc_times, "s-", label="Divide and Conquer")
    axes[1].set_title("Execution Time Comparison")
    axes[1].set_xlabel("Number of Points (N)")
    axes[1].set_ylabel("Execution Time (ms)")
    axes[1].grid(True, alpha=0.3)
    axes[1].legend()

    plt.tight_layout()
    plt.show()


def benchmark():
    sizes = [50, 100, 200, 400, 800, 1200]
    brute_times = []
    dc_times = []

    for n in sizes:
        points = [
            (random.randint(0, 10000), random.randint(0, 10000))
            for _ in range(n)
        ]

        _, brute_ms = timed_run(brute_force, points)
        _, dc_ms = timed_run(closest_pair_dc, points)

        brute_times.append(brute_ms)
        dc_times.append(dc_ms)

    return sizes, brute_times, dc_times


def main():
    try:
        n = int(input("Enter number of points (N): "))

        if n < 2:
            print("At least 2 points are required.")
            return

        random.seed()
        points = [
            (random.randint(0, 1000), random.randint(0, 1000))
            for _ in range(n)
        ]

        print("\nGenerated points:")
        for i, point in enumerate(points, start=1):
            print(f"P{i}: {point}")

        (brute_result, brute_ms) = timed_run(brute_force, points)
        (dc_result, dc_ms) = timed_run(closest_pair_dc, points)

        brute_dist, brute_pair = brute_result
        dc_dist, dc_pair = dc_result

        print("\n--- Brute Force ---")
        print(f"Closest pair: {brute_pair}")
        print(f"Minimum distance: {brute_dist:.6f}")
        print(f"Execution time: {brute_ms:.6f} ms")

        print("\n--- Divide and Conquer ---")
        print(f"Closest pair: {dc_pair}")
        print(f"Minimum distance: {dc_dist:.6f}")
        print(f"Execution time: {dc_ms:.6f} ms")

        if math.isclose(brute_dist, dc_dist, rel_tol=1e-9, abs_tol=1e-9):
            print("\nVerification: Both algorithms agree.")
        else:
            print("\nVerification FAILED: Results differ.")

        print("\nRunning performance benchmark...")
        sizes, brute_times, dc_times = benchmark()

        print("\n--- Benchmark Results ---")
        print(f"{'N':>8} {'Brute Force (ms)':>20} {'Divide & Conquer (ms)':>24}")

        for size, bt, dt in zip(sizes, brute_times, dc_times):
            print(f"{size:>8} {bt:>20.6f} {dt:>24.6f}")

        visualize(
            points, brute_pair, brute_ms, dc_ms,
            sizes, brute_times, dc_times
        )

    except ValueError:
        print("Please enter a valid integer.")


if __name__ == "__main__":
    main()
