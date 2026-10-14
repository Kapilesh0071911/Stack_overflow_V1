
import csv
from collections import deque
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

KEYS = "abcdef"
DOORS = "ABCDEF"

COLORS = {
    "#": "black",
    ".": "white",
    "S": "green",
    "E": "red",
    "a": "gold", "A": "gold",
    "b": "violet", "B": "violet",
    "c": "deepskyblue", "C": "deepskyblue",
    "d": "orange", "D": "orange",
    "e": "pink", "f": "cyan",
    "F": "cyan"
}


def read_maze(filename, T):
    with open(filename, newline="") as f:
        grid = [
            [cell.strip() for cell in row]
            for row in csv.reader(f)
        ]

    if not grid or any(len(row) != len(grid) for row in grid):
        raise ValueError("Maze must be a non-empty square grid")

    allowed = set(".#SEabcdefABCDEF")
    if any(cell not in allowed for row in grid for cell in row):
        raise ValueError("Invalid character found in maze.csv")

    starts = [
        (r, c)
        for r in range(len(grid))
        for c in range(len(grid))
        if grid[r][c] == "S"
    ]
    ends = [
        (r, c)
        for r in range(len(grid))
        for c in range(len(grid))
        if grid[r][c] == "E"
    ]

    if len(starts) != 1 or len(ends) != 1:
        raise ValueError("Maze must contain exactly one S and one E")

    present_keys = {
        cell for row in grid for cell in row if cell in KEYS
    }
    present_doors = {
    cell.lower()
    for row in grid
    for cell in row
    if cell in "ABCDF"
    }

    print("Keys found:", sorted(present_keys))
    print("Doors found:", sorted(present_doors))

    if len(present_keys) != T:
        raise ValueError(
            f"T={T}, but maze contains {len(present_keys)} distinct keys"
        )

    if not present_doors.issubset(present_keys):
        raise ValueError("Every door must have its matching key")

    return grid, starts[0], ends[0]



def bfs(grid, start, end):
    n = len(grid)
    initial = (start[0], start[1], 0)
    queue = deque([(start[0], start[1], 0, 0)])
    visited = {initial}
    parent = {initial: None}
    distances = {initial: 0}
    target = None

    directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]

    while queue:
        r, c, mask, dist = queue.popleft()
        state = (r, c, mask)

        if (r, c) == end:
            target = state
            break

        for dr, dc in directions:
            nr, nc = r + dr, c + dc

            if not (0 <= nr < n and 0 <= nc < n):
                continue

            cell = grid[nr][nc]

            if cell == "#":
                continue

            if cell in "ABCDF":
                bit = 1 << (ord(cell.lower()) - ord("a"))
                if not (mask & bit):
                    continue

            new_mask = mask

            if cell in KEYS:
                new_mask |= 1 << (ord(cell) - ord("a"))

            nxt = (nr, nc, new_mask)

            if nxt not in visited:
                visited.add(nxt)
                parent[nxt] = state
                distances[nxt] = dist + 1
                queue.append((nr, nc, new_mask, dist + 1))

    if target is None:
        return -1, [], []

    path_states = []
    cur = target

    while cur is not None:
        r, c, mask = cur
        path_states.append((r, c, mask, distances[cur]))
        cur = parent[cur]

    path_states.reverse()
    path = [(r, c) for r, c, mask, dist in path_states]

    return distances[target], path, path_states


def save_solution(grid, path):
    marked = [row[:] for row in grid]

    for r, c in path:
        if marked[r][c] == ".":
            marked[r][c] = "x"

    with open("maze_solution.csv", "w", newline="") as f:
        csv.writer(f).writerows(marked)

    print("Solution saved to maze_solution.csv")


def visualize(grid, path_states):
    n = len(grid)
    plt.ion()
    fig, ax = plt.subplots(figsize=(7, 7))

    for step, (r_now, c_now, mask, dist) in enumerate(path_states):
        ax.clear()

        inventory = [
            key for key in KEYS
            if mask & (1 << (ord(key) - ord("a")))
        ]

        for r in range(n):
            for c in range(n):
                cell = grid[r][c]
                face = COLORS.get(cell, "white")
                label = cell

                if cell in KEYS and cell in inventory:
                    face, label = "white", ""

                if cell in "ABCDF" and cell.lower() in inventory:
                    face, label = "white", "✓"

                rect = Rectangle(
                    (c, n - 1 - r), 1, 1,
                    facecolor=face, edgecolor="gray"
                )
                ax.add_patch(rect)

                if label:
                    ax.text(
                        c + 0.5, n - 0.5 - r, label,
                        ha="center", va="center",
                        fontsize=14, fontweight="bold",
                        color="white" if face == "black" else "black"
                    )

        route = [
            (c + 0.5, n - 0.5 - r)
            for r, c, _, _ in path_states[:step + 1]
        ]

        if route:
            ax.plot(
                [p[0] for p in route],
                [p[1] for p in route],
                "b-o", linewidth=2, markersize=5
            )

        ax.set_xlim(0, n)
        ax.set_ylim(0, n)
        ax.set_aspect("equal")
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_title(
            f"Shortest Path | Moves: {dist} | "
            f"Keys: {', '.join(inventory) if inventory else 'None'}"
        )

        plt.pause(0.5)

    plt.ioff()
    plt.show()


def main():
    try:
        T = int(input("Enter number of key types (1-6): "))

        if not 1 <= T <= 6:
            print("T must be between 1 and 6")
            return

        grid, start, end = read_maze("maze.csv", T)
        distance, path, path_states = bfs(grid, start, end)

        print("Shortest path length:", distance)

        if distance == -1:
            print("No valid path exists.")
            return

        print("Path coordinates:", path)
        save_solution(grid, path)
        visualize(grid, path_states)

    except (ValueError, FileNotFoundError) as error:
        print("Error:", error)


if __name__ == "__main__":
    main()
