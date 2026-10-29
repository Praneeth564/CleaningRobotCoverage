
import random
import time
import numpy as np
from collections import deque
from d7_layouts import create_room

# ==========================================
# D6: CLEANING ROBOT METRICS
# ==========================================

WIDTH = 40
HEIGHT = 25
RADIUS = 2
MAX_STEPS = 737
RANDOM_SEED = 42

room = create_room(1)

# 0 = free floor, 1 = obstacle
free_floor = room == 0
total_floor = int(np.count_nonzero(free_floor))

DIRECTIONS = [(1, 0), (0, 1), (-1, 0), (0, -1)]


# ==========================================
# 1. CLEANING FOOTPRINT
# ==========================================

def clean_area(coverage, x, y):
    for dy in range(-RADIUS, RADIUS + 1):
        for dx in range(-RADIUS, RADIUS + 1):

            if dx * dx + dy * dy > RADIUS * RADIUS:
                continue

            nx, ny = x + dx, y + dy

            if 0 <= nx < WIDTH and 0 <= ny < HEIGHT:
                if free_floor[ny, nx]:
                    coverage[ny, nx] += 1


def is_free(x, y):
    return (
        0 < x < WIDTH - 1
        and 0 < y < HEIGHT - 1
        and room[y, x] == 0
    )


# ==========================================
# 2. BFS PATHFINDING
# ==========================================

def bfs(start, goal):
    queue = deque([start])
    previous = {start: None}

    while queue:
        current = queue.popleft()

        if current == goal:
            break

        x, y = current

        for dx, dy in DIRECTIONS:
            nx, ny = x + dx, y + dy
            nxt = (nx, ny)

            if not is_free(nx, ny) or nxt in previous:
                continue

            previous[nxt] = current
            queue.append(nxt)

    if goal not in previous:
        return []

    result = []
    current = goal

    while current is not None:
        result.append(current)
        current = previous[current]

    return result[::-1]


# ==========================================
# 3. SWEEP STRATEGY
# ==========================================

def make_sweep_path():
    path = [(3, 3)]
    targets = []

    for y in range(1, HEIGHT - 1):

        if y % 2 == 0:
            xs = range(WIDTH - 2, 0, -1)
        else:
            xs = range(1, WIDTH - 1)

        for x in xs:
            if is_free(x, y):
                targets.append((x, y))

    current = path[-1]

    for target in targets:
        route = bfs(current, target)

        if not route:
            continue

        for position in route[1:]:
            if len(path) >= MAX_STEPS:
                return path

            path.append(position)

        current = target

        if len(path) >= MAX_STEPS:
            break

    return path


# ==========================================
# 4. SPIRAL + BFS STRATEGY
# ==========================================

def make_spiral_path():
    path = [(3, 3)]
    planned = np.zeros((HEIGHT, WIDTH), dtype=int)

    x, y = path[0]
    clean_area(planned, x, y)

    direction_index = 0
    segment_length = 1
    segment_progress = 0
    segments_completed = 0

    while len(path) < MAX_STEPS:

        if np.all(planned[free_floor] > 0):
            break

        if segment_progress >= segment_length:
            direction_index = (direction_index + 1) % 4
            segments_completed += 1

            if segments_completed % 2 == 0:
                segment_length += 1

            segment_progress = 0
            continue

        dx, dy = DIRECTIONS[direction_index]
        nx, ny = x + dx, y + dy

        if is_free(nx, ny):
            x, y = nx, ny
            path.append((x, y))
            clean_area(planned, x, y)
            segment_progress += 1

        else:
            queue = deque([(x, y)])
            previous = {(x, y): None}
            target = None

            while queue:
                cx, cy = queue.popleft()
                has_new_area = False

                for fy in range(-RADIUS, RADIUS + 1):
                    for fx in range(-RADIUS, RADIUS + 1):

                        if fx * fx + fy * fy > RADIUS * RADIUS:
                            continue

                        tx, ty = cx + fx, cy + fy

                        if (
                            0 <= tx < WIDTH
                            and 0 <= ty < HEIGHT
                            and free_floor[ty, tx]
                            and planned[ty, tx] == 0
                        ):
                            has_new_area = True
                            break

                    if has_new_area:
                        break

                if has_new_area:
                    target = (cx, cy)
                    break

                for fx, fy in DIRECTIONS:
                    nx2, ny2 = cx + fx, cy + fy
                    nxt = (nx2, ny2)

                    if is_free(nx2, ny2) and nxt not in previous:
                        previous[nxt] = (cx, cy)
                        queue.append(nxt)

            if target is None:
                break

            route = []
            current = target

            while current is not None:
                route.append(current)
                current = previous[current]

            route.reverse()

            for position in route[1:]:
                if len(path) >= MAX_STEPS:
                    break

                x, y = position
                path.append(position)
                clean_area(planned, x, y)

            segment_progress = segment_length

    return path


# ==========================================
# 5. RANDOM BOUNCE STRATEGY
# ==========================================

def make_random_path():
    rng = random.Random(RANDOM_SEED)

    x, y = 3, 3
    direction = rng.choice(DIRECTIONS)
    path = [(x, y)]

    for _ in range(MAX_STEPS - 1):
        dx, dy = direction
        nx, ny = x + dx, y + dy

        if not is_free(nx, ny):
            safe = []

            for ndx, ndy in DIRECTIONS:
                if is_free(x + ndx, y + ndy):
                    safe.append((ndx, ndy))

            if not safe:
                break

            direction = rng.choice(safe)
            dx, dy = direction
            nx, ny = x + dx, y + dy

        if is_free(nx, ny):
            x, y = nx, ny
            path.append((x, y))

    return path


# ==========================================
# 6. CALCULATE METRICS
# ==========================================

def calculate_metrics(path):
    visits = np.zeros((HEIGHT, WIDTH), dtype=int)

    for x, y in path:
        clean_area(visits, x, y)

    floor_visits = visits[free_floor]

    cleaned_cells = int(np.count_nonzero(floor_visits > 0))

    # Distinct floor cells cleaned at least twice
    repeated_cells = int(np.count_nonzero(floor_visits > 1))

    coverage = (
        100 * cleaned_cells / total_floor
        if total_floor else 0
    )

    # Count changes in movement direction
    turns = 0
    previous_direction = None

    for i in range(1, len(path)):
        dx = path[i][0] - path[i - 1][0]
        dy = path[i][1] - path[i - 1][1]

        current_direction = (dx, dy)

        if previous_direction is not None:
            if current_direction != previous_direction:
                turns += 1

        previous_direction = current_direction

    # Total movement distance in grid units
    path_length = sum(
        abs(path[i][0] - path[i - 1][0])
        + abs(path[i][1] - path[i - 1][1])
        for i in range(1, len(path))
    )

    total_visits = int(np.sum(floor_visits))

    # Percentage of cleaning visits beyond first visits
    repeated_visits = total_visits - cleaned_cells

    repeat_rate = (
        100 * repeated_visits / total_visits
        if total_visits else 0
    )

    # Illustrative energy estimate
    battery_units = path_length + 0.2 * turns

    return {
        "steps": len(path),
        "coverage": coverage,
        "repeat_rate": repeat_rate,
        "repeated_cells": repeated_cells,
        "turns": turns,
        "path_length": path_length,
        "battery": battery_units,
        "uncleaned": total_floor - cleaned_cells
    }


# ==========================================
# 7. RUN STRATEGIES AND MEASURE TIME
# ==========================================

strategy_functions = {
    "Sweep": make_sweep_path,
    "Spiral + BFS": make_spiral_path,
    "Random Bounce": make_random_path
}

results = {}

for name, strategy_function in strategy_functions.items():

    # Include path generation and metric calculation
    start_time = time.perf_counter()

    path = strategy_function()
    metrics = calculate_metrics(path)

    end_time = time.perf_counter()

    # Convert elapsed seconds into minutes
    metrics["execution_time"] = round(
        (end_time - start_time) / 60, 4
    )

    results[name] = metrics


# ==========================================
# 8. DISPLAY COMPARISON MATRIX
# ==========================================

print("\n========== D6: METRICS COMPARISON ==========")
print("Room: 40 x 25")
print("Layout: 1")
print("Free floor cells:", total_floor)
print("Maximum planned positions:", MAX_STEPS)
print("Random seed:", RANDOM_SEED)

header = (
    f"{'Strategy':<16}"
    f"{'Steps':>8}"
    f"{'Coverage %':>12}"
    f"{'Repeat %':>11}"
    f"{'Repeated':>11}"
    f"{'Turns':>8}"
    f"{'Path':>8}"
    f"{'Battery':>10}"
    f"{'Uncleaned':>12}"
    f"{'Time (min)':>13}"
)

print("\n" + header)
print("-" * len(header))

for name, result in results.items():

    print(
        f"{name:<16}"
        f"{result['steps']:>8}"
        f"{result['coverage']:>11.2f}%"
        f"{result['repeat_rate']:>10.2f}%"
        f"{result['repeated_cells']:>11}"
        f"{result['turns']:>8}"
        f"{result['path_length']:>8}"
        f"{result['battery']:>10.1f}"
        f"{result['uncleaned']:>12}"
        f"{result['execution_time']:>13.4f}"
    )

print("\nMetric definitions:")
print("Repeated = distinct floor cells cleaned at least twice.")
print("Repeat % = extra cleaning visits / total cleaning visits.")
print("Time (min) = path generation + metric calculation time.")
print("Battery = path length + 0.2 per turn (simulated estimate).")
print("Execution times vary with computer load and Python environment.")
