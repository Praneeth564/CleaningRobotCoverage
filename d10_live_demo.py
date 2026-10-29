from collections import deque
import random

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation
from matplotlib.patches import Circle, Rectangle, FancyBboxPatch
from matplotlib.lines import Line2D


# ============================== CONFIGURATION ==============================

ROOM_ROWS, ROOM_COLS = 25, 40
CLEAN_RADIUS = 2

BATTERY_CAPACITY = 100.0
BATTERY_RESERVE = 22.0
CHARGE_PER_FRAME = 4.0
MOVE_COST = 0.20
TURN_COST = 0.06

RANDOM_STEPS = 1300
RANDOM_SEED = 19
FRAME_INTERVAL_MS = 45

START = (3, 3)
DOCK = START
DIRECTIONS = ((0, 1), (1, 0), (0, -1), (-1, 0))

STRATEGIES = ("Sweep", "Spiral + BFS", "Random Bounce")
COLORS = {
    "Random Bounce": "#d99025",
    "Sweep": "#2784d8",
    "Spiral + BFS": "#805ad5",
}


# ================================ FIVE ROOMS ================================

def build_layout(layout_id):
    """Use the same five obstacle arrangements shown in the user's screenshot."""
    room = np.zeros((ROOM_ROWS, ROOM_COLS), dtype=np.uint8)

    if layout_id == 1:
        # Three separated furniture blocks.
        room[6:11, 6:12] = 1
        room[14:20, 22:30] = 1
        room[3:8, 31:35] = 1

    elif layout_id == 2:
        # U-shaped obstacle arrangement.
        room[5:19, 8:10] = 1
        room[5:19, 28:30] = 1
        room[14:17, 8:30] = 1

    elif layout_id == 3:
        # Four separated furniture blocks.
        room[4:7, 5:9] = 1
        room[10:14, 16:20] = 1
        room[18:22, 27:32] = 1
        room[5:10, 33:36] = 1

    elif layout_id == 4:
        # One small block, one long horizontal block, one lower block.
        room[17:21, 5:9] = 1
        room[11:14, 9:31] = 1
        room[4:8, 18:22] = 1

    elif layout_id == 5:
        # Closed rectangular furniture ring with a floor island inside.
        room[4:19, 10:13] = 1
        room[4:19, 26:29] = 1
        room[4:7, 10:29] = 1
        room[16:19, 10:29] = 1

    # Keep the start/dock area free, matching the red starting dot.
    room[0:5, 0:6] = 0
    return room


# ============================== GRID UTILITIES ==============================

def free_cells(room):
    return set(map(tuple, np.argwhere(room == 0)))


def neighbors(position, room):
    row, col = position
    for dr, dc in DIRECTIONS:
        nxt = (row + dr, col + dc)
        r, c = nxt
        if 0 <= r < ROOM_ROWS and 0 <= c < ROOM_COLS and room[r, c] == 0:
            yield nxt


def bfs(start, goal, room):
    """Shortest four-directional route through free floor."""
    if start == goal:
        return [start]

    queue = deque([start])
    parent = {start: None}
    while queue:
        current = queue.popleft()
        if current == goal:
            break
        for nxt in neighbors(current, room):
            if nxt not in parent:
                parent[nxt] = current
                queue.append(nxt)

    if goal not in parent:
        return []

    route = []
    node = goal
    while node is not None:
        route.append(node)
        node = parent[node]
    return route[::-1]


def cleaning_footprint(position, room):
    row, col = position
    cells = []
    for r in range(max(0, row - CLEAN_RADIUS),
                   min(ROOM_ROWS, row + CLEAN_RADIUS + 1)):
        for c in range(max(0, col - CLEAN_RADIUS),
                       min(ROOM_COLS, col + CLEAN_RADIUS + 1)):
            if (r - row) ** 2 + (c - col) ** 2 <= CLEAN_RADIUS ** 2:
                if room[r, c] == 0:
                    cells.append((r, c))
    return cells


def join_route(path, segment):
    if segment:
        path.extend(segment[1:])


# =============================== THREE PLANNERS =============================

def make_sweep_path(room):
    """Sweep rows in alternating directions, using BFS around obstacles."""
    path = [START]
    direction = 1
    for row in range(ROOM_ROWS):
        columns = range(ROOM_COLS) if direction == 1 else range(ROOM_COLS - 1, -1, -1)
        for col in columns:
            target = (row, col)
            if room[target] != 0:
                continue
            segment = bfs(path[-1], target, room)
            join_route(path, segment)
        direction *= -1
    return path


def make_spiral_bfs_path(room):
    """
    Spiral + BFS hybrid:
    1. Generate a clockwise, outside-in spiral order of grid positions.
    2. Use BFS to reach each useful free-floor target while avoiding obstacles.
    3. Count the cleaning footprint at every position traversed, not just at
       the final target.
    4. If the spiral pass leaves any floor uncovered, use nearest-uncovered
       BFS as a fallback.
    """
    path = [START]
    floor = free_cells(room)
    cleaned = set(cleaning_footprint(START, room))

    # Build a clockwise, outside-in spiral over the room grid.
    spiral_order = []
    top, bottom = 0, ROOM_ROWS - 1
    left, right = 0, ROOM_COLS - 1

    while top <= bottom and left <= right:
        for col in range(left, right + 1):
            spiral_order.append((top, col))
        top += 1

        for row in range(top, bottom + 1):
            spiral_order.append((row, right))
        right -= 1

        if top <= bottom:
            for col in range(right, left - 1, -1):
                spiral_order.append((bottom, col))
            bottom -= 1

        if left <= right:
            for row in range(bottom, top - 1, -1):
                spiral_order.append((row, left))
            left += 1

    def visit_segment(segment):
        """Append a BFS segment and account for cleaning along the whole path."""
        if not segment:
            return
        join_route(path, segment)
        for position in segment[1:]:
            cleaned.update(cleaning_footprint(position, room))

    # Follow spiral-ordered free cells, using BFS to go around furniture.
    for target in spiral_order:
        if target not in floor:
            continue
        if not any(cell not in cleaned
                   for cell in cleaning_footprint(target, room)):
            continue

        segment = bfs(path[-1], target, room)
        if segment:
            visit_segment(segment)

        if floor <= cleaned:
            return path

    # Fallback: cover any remaining reachable floor with nearest-uncovered BFS.
    max_iterations = ROOM_ROWS * ROOM_COLS * 12
    iterations = 0

    while not floor <= cleaned and iterations < max_iterations:
        iterations += 1
        queue = deque([path[-1]])
        parent = {path[-1]: None}
        target = None

        while queue:
            current = queue.popleft()
            if any(cell not in cleaned
                   for cell in cleaning_footprint(current, room)):
                target = current
                break

            for nxt in neighbors(current, room):
                if nxt not in parent:
                    parent[nxt] = current
                    queue.append(nxt)

        if target is None:
            break

        segment = []
        node = target
        while node is not None:
            segment.append(node)
            node = parent[node]
        visit_segment(segment[::-1])

    return path


def make_random_bounce_path(room, seed):
    """Random legal movement; this is a baseline, not a coverage planner."""
    rng = random.Random(seed)
    path = [START]
    previous = None

    for _ in range(RANDOM_STEPS):
        options = list(neighbors(path[-1], room))
        if not options:
            break
        forward = [p for p in options if p != previous]
        if forward and rng.random() < 0.82:
            options = forward
        nxt = rng.choice(options)
        previous = path[-1]
        path.append(nxt)

    return path


# ================================ BATTERY ===================================

def route_energy(route, initial_direction=None):
    """Estimate energy needed to follow a route, including turns."""
    energy = 0.0
    previous_direction = initial_direction
    for i in range(1, len(route)):
        old, new = route[i - 1], route[i]
        if old == new:
            continue
        direction = (new[0] - old[0], new[1] - old[1])
        turned = previous_direction is not None and direction != previous_direction
        energy += MOVE_COST + (TURN_COST if turned else 0.0)
        previous_direction = direction
    return energy


def add_battery_and_docking(planned_path, room):
    """
    Follow the planned route while enforcing a safe return-to-dock rule.

    Before every movement, estimate the energy needed to return to the dock.
    If the next move would leave less than the return energy plus the reserve,
    go to the dock, recharge fully, and resume the interrupted target.
    After the planned route is complete, return to the dock without starting
    another charging cycle.
    """
    route = [START]
    battery_history = [BATTERY_CAPACITY]
    charging_history = [False]
    battery = BATTERY_CAPACITY
    previous_direction = None
    docking_cycles = 0

    def append_move(position):
        nonlocal battery, previous_direction
        old = route[-1]
        direction = (position[0] - old[0], position[1] - old[1])
        turned = previous_direction is not None and direction != previous_direction
        battery = max(0.0, battery - MOVE_COST - (TURN_COST if turned else 0.0))
        route.append(position)
        battery_history.append(battery)
        charging_history.append(False)
        previous_direction = direction

    def travel_to_dock():
        nonlocal battery, previous_direction, docking_cycles
        if route[-1] == DOCK:
            return True
        home_route = bfs(route[-1], DOCK, room)
        if not home_route:
            return False

        docking_cycles += 1
        for position in home_route[1:]:
            append_move(position)

        # Recharge while stationary at the dock. Each charging frame is
        # represented by a repeated dock position in the animation history.
        previous_direction = None
        while battery < BATTERY_CAPACITY:
            battery = min(BATTERY_CAPACITY, battery + CHARGE_PER_FRAME)
            route.append(DOCK)
            battery_history.append(battery)
            charging_history.append(True)
        return True

    for target in planned_path[1:]:
        safety_guard = 0
        while route[-1] != target and safety_guard < ROOM_ROWS * ROOM_COLS * 4:
            safety_guard += 1
            current = route[-1]
            segment = bfs(current, target, room)
            if len(segment) < 2:
                break

            next_position = segment[1]
            next_direction = (next_position[0] - current[0],
                              next_position[1] - current[1])
            next_turn = (previous_direction is not None
                         and next_direction != previous_direction)
            next_cost = MOVE_COST + (TURN_COST if next_turn else 0.0)

            home_route = bfs(current, DOCK, room)
            if not home_route:
                # There is no legal route to the dock; stop safely rather
                # than claiming that a return is possible.
                return route, battery_history, charging_history, docking_cycles

            home_cost = route_energy(home_route, previous_direction)

            # If the next move would leave insufficient energy to get home
            # while preserving the configured reserve, dock before moving.
            if (current != DOCK
                    and (battery - next_cost < BATTERY_RESERVE
                         or battery - next_cost < home_cost)):
                if not travel_to_dock():
                    return route, battery_history, charging_history, docking_cycles
                continue

            # At the dock, start with a full battery. A route target is
            # resumed only after charging has completed.
            if current == DOCK and battery < BATTERY_CAPACITY:
                while battery < BATTERY_CAPACITY:
                    battery = min(BATTERY_CAPACITY, battery + CHARGE_PER_FRAME)
                    route.append(DOCK)
                    battery_history.append(battery)
                    charging_history.append(True)
                previous_direction = None
                continue

            append_move(next_position)

    # Cleaning route is finished: return to the dock if not already there.
    if route[-1] != DOCK:
        home_route = bfs(route[-1], DOCK, room)
        if home_route:
            # End-of-task docking is mandatory. If the battery estimate is
            # insufficient, the simulation reports the remaining battery
            # honestly; it never silently recharges away from the dock.
            for position in home_route[1:]:
                append_move(position)

    return route, battery_history, charging_history, docking_cycles


# ================================ METRICS ===================================

def calculate_metrics(route, room, battery_history, charging_history, docking_cycles):
    floor = free_cells(room)
    cleaned = set()
    cell_visits = {}
    footprint_visits = 0

    for route_index, position in enumerate(route):
        # Repeated identical positions represent stationary charging frames,
        # not additional cleaning passes.
        if route_index > 0 and position == route[route_index - 1]:
            continue

        cells = cleaning_footprint(position, room)
        cleaned.update(cells)
        footprint_visits += len(cells)
        for cell in cells:
            cell_visits[cell] = cell_visits.get(cell, 0) + 1

    # Distinct floor cells whose cleaning footprint was reached at least twice.
    repeated_cells = sum(1 for count in cell_visits.values() if count >= 2)

    turns = 0
    previous_direction = None
    movement_steps = 0
    for index in range(1, len(route)):
        old, new = route[index - 1], route[index]
        if old == new:  # stationary charging frame
            continue
        movement_steps += 1
        direction = (new[0] - old[0], new[1] - old[1])
        if previous_direction is not None and direction != previous_direction:
            turns += 1
        previous_direction = direction

    return {
        "coverage": 100.0 * len(cleaned) / max(1, len(floor)),
        "path_length": movement_steps,
        "turns": turns,
        "uncleaned": len(floor - cleaned),
        "repeated_visits": max(0, footprint_visits - len(cleaned)),
        "repeated_cells": repeated_cells,
        "battery": battery_history,
        "charging": charging_history,
        "docking_cycles": docking_cycles,
    }


def prepare_run(layout_id, strategy):
    room = build_layout(layout_id)
    if strategy == "Sweep":
        planned = make_sweep_path(room)
    elif strategy == "Spiral + BFS":
        planned = make_spiral_bfs_path(room)
    else:
        planned = make_random_bounce_path(room, 19 + layout_id * 31)

    route, battery, charging, dock_cycles = add_battery_and_docking(planned, room)
    return {
        "layout": layout_id,
        "strategy": strategy,
        "room": room,
        "route": route,
        "metrics": calculate_metrics(route, room, battery, charging, dock_cycles),
    }


# Choose one layout to run (1 to 5).
while True:
    try:
        SELECTED_LAYOUT = int(input("Choose layout (1-5): "))
        if 1 <= SELECTED_LAYOUT <= 5:
            break
        print("Please enter a number from 1 to 5.")
    except ValueError:
        print("Invalid input. Please enter a number from 1 to 5.")

RUNS = {
    (SELECTED_LAYOUT, strategy): prepare_run(SELECTED_LAYOUT, strategy)
    for strategy in STRATEGIES
}


# ================================= RESULTS ==================================

print(f"\nD10 | SELECTED LAYOUT {SELECTED_LAYOUT} | THREE-STRATEGY COMPARISON")
print(f"Battery {BATTERY_CAPACITY:.0f}% | reserve {BATTERY_RESERVE:.0f}% | "
      f"charge rate {CHARGE_PER_FRAME:.0f}% per charging frame")
print("-" * 125)
print(f"{'Layout':<8}{'Strategy':<17}{'Coverage':>10}{'Path':>9}"
      f"{'Turns':>9}{'Uncleaned':>12}{'Repeated cells':>17}{'Dock cycles':>14}")
print("-" * 125)
for strategy in STRATEGIES:
    m = RUNS[(SELECTED_LAYOUT, strategy)]["metrics"]
    print(f"{SELECTED_LAYOUT:<8}{strategy:<17}{m['coverage']:>9.2f}%"
          f"{m['path_length']:>9}{m['turns']:>9}"
          f"{m['uncleaned']:>12}{m['repeated_cells']:>17}{m['docking_cycles']:>14}")
print("-" * 125)
print("Repeated cells = distinct floor cells cleaned at least twice.")


# ============================= PROFESSIONAL UI ==============================

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9})
fig = plt.figure(figsize=(15, 8), facecolor="#f3f6fa")
grid = fig.add_gridspec(
    2, 3, height_ratios=[4.5, 1.2],
    left=0.045, right=0.98, top=0.82, bottom=0.09,
    hspace=0.32, wspace=0.14,
)
axes = [fig.add_subplot(grid[0, i]) for i in range(3)]
summary_ax = fig.add_subplot(grid[1, :])
summary_ax.axis("off")

fig.suptitle("CLEANING ROBOT COVERAGE SYSTEM  |  SWEEP → SPIRAL + BFS → RANDOM BOUNCE", y=0.965,
             fontsize=18, fontweight="bold", color="#172b4d")
subtitle = fig.text(0.5, 0.92, "", ha="center", fontsize=10, color="#52647a")

panels = []
for axis, strategy in zip(axes, STRATEGIES):
    axis.set_facecolor("#edf2f7")
    axis.set_xticks([])
    axis.set_yticks([])
    axis.set_xlim(-0.5, ROOM_COLS - 0.5)
    axis.set_ylim(ROOM_ROWS - 0.5, -0.5)
    axis.set_aspect("equal")
    axis.set_facecolor("#eaf0f7")
    axis.set_xticks(np.arange(0, ROOM_COLS, 5), minor=True)
    axis.set_yticks(np.arange(0, ROOM_ROWS, 5), minor=True)
    axis.grid(which="minor", color="#d9e2ec", linewidth=0.45, alpha=0.7)
    axis.tick_params(which="minor", bottom=False, left=False)
    axis.set_title(strategy, fontsize=12, fontweight="bold", color=COLORS[strategy], pad=9)

    initial = np.zeros((ROOM_ROWS, ROOM_COLS, 3))
    initial[:] = (0.93, 0.95, 0.97)
    initial[build_layout(SELECTED_LAYOUT) == 1] = (0.27, 0.33, 0.41)
    image = axis.imshow(initial, interpolation="nearest", zorder=1)

    trail, = axis.plot([], [], color=COLORS[strategy], linewidth=1.2, alpha=0.85, zorder=3)
    footprint = Circle((START[1], START[0]), CLEAN_RADIUS, fill=False,
                       linestyle="--", linewidth=1.0, edgecolor=COLORS[strategy],
                       alpha=0.6, zorder=4)
    axis.add_patch(footprint)
    pulse = Circle((START[1], START[0]), 1.0, fill=False,
                   linewidth=1.5, edgecolor="#ffffff", alpha=0.75, zorder=5)
    axis.add_patch(pulse)
    robot, = axis.plot([START[1]], [START[0]], marker="o", markersize=8,
                       markerfacecolor="#e63946", markeredgecolor="white",
                       markeredgewidth=1.2, linestyle="None", zorder=6)
    axis.plot([DOCK[1]], [DOCK[0]], marker="s", markersize=8,
              markerfacecolor="#f6c445", markeredgecolor="#5b4a16",
              linestyle="None", zorder=5)

    # Compact battery label and short progress bar.
    axis.text(0.56, 1.055, "BAT", transform=axis.transAxes,
              fontsize=6, fontweight="bold", va="bottom", color="#26374a", clip_on=False)
    battery_label = axis.text(0.68, 1.055, "100%", transform=axis.transAxes,
                              fontsize=6, fontweight="bold", va="bottom",
                              color="#26374a", clip_on=False)
    # Rounded battery body + terminal. Fill width animates with battery level.
    battery_body = FancyBboxPatch(
        (0.80, 1.044), 0.15, 0.026, boxstyle="round,pad=0.002,rounding_size=0.008",
        transform=axis.transAxes, facecolor="#d6dee8", edgecolor="#8998aa",
        linewidth=0.65, clip_on=False, zorder=8
    )
    axis.add_patch(battery_body)
    axis.add_patch(Rectangle((0.951, 1.051), 0.012, 0.012, transform=axis.transAxes,
                             facecolor="#8998aa", edgecolor="none",
                             clip_on=False, zorder=8))
    battery_fill = FancyBboxPatch(
        (0.804, 1.048), 0.142, 0.018,
        boxstyle="round,pad=0.001,rounding_size=0.006",
        transform=axis.transAxes, facecolor="#2a9d68", edgecolor="none",
        clip_on=False, zorder=9
    )
    axis.add_patch(battery_fill)
    charge_icon = axis.text(0.875, 1.056, "", transform=axis.transAxes,
                            ha="center", va="center", fontsize=7,
                            fontweight="bold", color="white", clip_on=False, zorder=10)
    state_label = axis.text(0.03, 1.025, "READY", transform=axis.transAxes,
                            fontsize=6, fontweight="bold", va="bottom",
                            color="#52647a", clip_on=False)
    metric_label = axis.text(0.02, -0.08, "", transform=axis.transAxes,
                             ha="left", va="top", fontsize=8, color="#34445a")

    panels.append({
        "image": image, "trail": trail, "footprint": footprint, "pulse": pulse, "robot": robot,
        "battery_label": battery_label, "battery_fill": battery_fill, "charge_icon": charge_icon,
        "state_label": state_label, "metric_label": metric_label,
    })

legend_handles = [
    Line2D([0], [0], marker="o", color="none", markerfacecolor="#e63946",
           markeredgecolor="white", markersize=8, label="Robot"),
    Line2D([0], [0], marker="s", color="none", markerfacecolor="#f6c445",
           markeredgecolor="#5b4a16", markersize=8, label="Dock"),
    Line2D([0], [0], color="#6ecda0", linewidth=6, label="Cleaned floor"),
    Line2D([0], [0], color="#455468", linewidth=6, label="Furniture"),
]
fig.legend(handles=legend_handles, loc="upper center", bbox_to_anchor=(0.5, 0.885),
           ncol=4, frameon=False, fontsize=9)

summary_text = summary_ax.text(0.01, 0.96, "", transform=summary_ax.transAxes,
                               ha="left", va="top", fontsize=10, color="#25364a")


def get_frame_count():
    return max(
        len(RUNS[(SELECTED_LAYOUT, strategy)]["route"])
        for strategy in STRATEGIES
    )


FRAME_COUNT = get_frame_count()


def frame_to_layout(frame):
    return SELECTED_LAYOUT, frame


def update(frame):
    layout_id, local_frame = frame_to_layout(frame)
    summary = [
        f"LAYOUT {layout_id} / 5     |     BATTERY RESERVE {BATTERY_RESERVE:.0f}%"
        f"     |     AUTO-DOCK + RECHARGE ENABLED"
    ]

    for strategy, panel in zip(STRATEGIES, panels):
        run = RUNS[(layout_id, strategy)]
        room, route, m = run["room"], run["route"], run["metrics"]
        index = min(local_frame, len(route) - 1)
        position = route[index]
        battery = m["battery"][index]
        charging = m["charging"][index]

        cleaned = set()
        cell_visits_so_far = {}
        visible_route = route[:index + 1]
        for route_index, p in enumerate(visible_route):
            # Do not count stationary charging frames as extra cleaning visits.
            if route_index > 0 and p == visible_route[route_index - 1]:
                continue
            for cell in cleaning_footprint(p, room):
                cleaned.add(cell)
                cell_visits_so_far[cell] = cell_visits_so_far.get(cell, 0) + 1
        repeated_cells_so_far = sum(
            1 for count in cell_visits_so_far.values() if count >= 2
        )

        rgb = np.zeros((ROOM_ROWS, ROOM_COLS, 3), dtype=float)
        # Subtle animated cool-blue background, with a gentle green shimmer on cleaned tiles.
        ambience = 0.012 * (0.5 + 0.5 * np.sin(frame * 0.055))
        rgb[:] = (0.91 + ambience, 0.94 + ambience, 0.97)
        rgb[room == 1] = (0.25, 0.31, 0.40)
        clean_glow = 0.025 * (0.5 + 0.5 * np.sin(frame * 0.16))
        for r, c in cleaned:
            rgb[r, c] = (0.39, 0.76 + clean_glow, 0.58 + clean_glow)

        panel["image"].set_data(rgb)
        edge_pulse = 0.5 + 0.5 * np.sin(frame * 0.08)
        for spine in axes[STRATEGIES.index(strategy)].spines.values():
            spine.set_color(COLORS[strategy] if edge_pulse > 0.72 else "#d4deea")
            spine.set_linewidth(1.4 if edge_pulse > 0.72 else 0.7)
        panel["trail"].set_data([p[1] for p in route[:index + 1]],
                                [p[0] for p in route[:index + 1]])
        panel["robot"].set_data([position[1]], [position[0]])
        panel["footprint"].center = (position[1], position[0])
        panel["pulse"].center = (position[1], position[0])
        panel["pulse"].set_radius(0.65 + 0.45 * (0.5 + 0.5 * np.sin(frame * 0.22)))
        pulse_phase = 0.5 + 0.5 * np.sin(frame * 0.22)
        panel["pulse"].set_alpha(0.25 + 0.60 * pulse_phase)
        panel["pulse"].set_linewidth(1.0 + 1.2 * pulse_phase)
        panel["robot"].set_markersize(8 + 2.0 * pulse_phase)
        panel["trail"].set_linewidth(1.0 + 0.65 * pulse_phase)
        panel["trail"].set_alpha(0.60 + 0.30 * pulse_phase)

        panel["battery_label"].set_text(f"{battery:.0f}%")
        # A visible animated fill rather than a thin static-looking line.
        fill_fraction = max(0.015, battery / BATTERY_CAPACITY)
        panel["battery_fill"].set_bounds(0.804, 1.048, 0.142 * fill_fraction, 0.018)
        if battery <= 25:
            bar_color = "#d94841"
        elif battery <= 50:
            bar_color = "#e59a27"
        else:
            bar_color = "#2a9d68"
        panel["battery_fill"].set_facecolor(bar_color)

        if charging:
            state, color = "DOCKED • CHARGING", "#2a7b55"
        elif position == DOCK:
            state, color = "AT DOCK", "#8a6d1d"
        elif battery <= BATTERY_RESERVE + 8:
            state, color = "LOW BATTERY", "#c0392b"
        else:
            state, color = "CLEANING", "#52647a"
        panel["state_label"].set_text(state)
        panel["state_label"].set_color(color)

        current_coverage = 100 * len(cleaned) / max(1, len(free_cells(room)))
        steps_so_far = sum(route[j] != route[j - 1] for j in range(1, index + 1))
        panel["metric_label"].set_text(
            f"Coverage {current_coverage:5.1f}%    Steps {steps_so_far:4d}\n"
            f"Turns {m['turns']:3d}    Repeated cells {repeated_cells_so_far:4d}\n"
            f"Dock cycles {m['docking_cycles']:2d}"
        )

        summary.append(
            f"{strategy}: {m['coverage']:.1f}% coverage, "
            f"{m['repeated_cells']} repeated cells, "
            f"{m['path_length']} steps, {m['docking_cycles']} dock cycles"
        )

    subtitle.set_text(
        f"Selected layout {layout_id} of 5  |  Same room matrix for all three strategies  |  "
        "green = cleaned floor, gray = furniture, gold = dock"
    )
    summary_text.set_text("\n".join(summary))
    return []


animation = FuncAnimation(
    fig, update, frames=FRAME_COUNT, interval=FRAME_INTERVAL_MS,
    repeat=False, blit=False, cache_frame_data=False,
)
plt.show()