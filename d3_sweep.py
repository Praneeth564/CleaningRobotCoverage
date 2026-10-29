
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.colors import ListedColormap
from matplotlib.patches import Circle, Rectangle
from collections import deque

from d7_layouts import create_room

# =========================
# ROOM SETTINGS
# =========================
WIDTH = 40
HEIGHT = 25
CLEANING_RADIUS = 2

room = create_room(1)

start = (2, 2)
CHARGING_DOCK = (2, 2)

if room[start[1], start[0]] != 0:
    raise ValueError("Starting position must be free floor.")

if room[CHARGING_DOCK[1], CHARGING_DOCK[0]] != 0:
    raise ValueError("Charging dock must be on free floor.")

total_floor = int(np.count_nonzero(room == 0))


# =========================
# BFS PATH PLANNING
# =========================
def find_path(start_pos, target):
    queue = deque([start_pos])
    previous = {start_pos: None}

    while queue:
        x, y = queue.popleft()

        if (x, y) == target:
            break

        for nx, ny in [
            (x + 1, y), (x - 1, y),
            (x, y + 1), (x, y - 1)
        ]:
            if not (0 <= nx < WIDTH and 0 <= ny < HEIGHT):
                continue

            if room[ny, nx] == 1:
                continue

            if (nx, ny) not in previous:
                previous[(nx, ny)] = (x, y)
                queue.append((nx, ny))

    if target not in previous:
        return []

    path = []
    current = target

    while current is not None:
        path.append(current)
        current = previous[current]

    return path[::-1]


# =========================
# GENERATE SWEEP TARGETS
# =========================
targets = []

for y in range(1, HEIGHT - 1):
    xs = (
        range(1, WIDTH - 1)
        if y % 2 == 0
        else range(WIDTH - 2, 0, -1)
    )

    for x in xs:
        if room[y, x] == 0:
            targets.append((x, y))


# =========================
# BUILD PLANNED ROUTE
# =========================
route = [start]
current = start

for target in targets:
    path = find_path(current, target)

    if path:
        route.extend(path[1:])
        current = target

# Plan the return to the charging dock.
# The robot follows this path only if the animation reaches it.
return_path = find_path(current, CHARGING_DOCK)

if return_path:
    route.extend(return_path[1:])
else:
    raise RuntimeError("No return path to charging dock.")

print("Charging dock:", CHARGING_DOCK)
print("Planned route positions:", len(route))


# =========================
# CLEANING COUNTERS
# =========================
def calculate_clean_counts(positions):
    counts = np.zeros((HEIGHT, WIDTH), dtype=np.int32)

    for x, y in positions:
        for dy in range(-CLEANING_RADIUS, CLEANING_RADIUS + 1):
            for dx in range(-CLEANING_RADIUS, CLEANING_RADIUS + 1):

                if dx * dx + dy * dy > CLEANING_RADIUS ** 2:
                    continue

                nx, ny = x + dx, y + dy

                if not (0 <= nx < WIDTH and 0 <= ny < HEIGHT):
                    continue

                if room[ny, nx] == 0:
                    counts[ny, nx] += 1

    return counts


# =========================
# ANIMATION SETUP
# =========================
fig, ax = plt.subplots(figsize=(13, 8))

cmap = ListedColormap([
    "#E9EDF2",  # Uncleaned floor
    "#394150",  # Obstacles
    "#7EDC9A"   # Cleaned floor
])

# IMPORTANT:
# Record the last frame actually displayed.
last_frame = -1


# =========================
# ANIMATION UPDATE
# =========================
def update(frame):
    global last_frame

    # Record actual animation progress.
    last_frame = frame

    x, y = route[frame]

    # Count cleaning only up to the current frame.
    counts = calculate_clean_counts(route[:frame + 1])

    cleaned = (counts > 0) & (room == 0)
    repeated = (counts > 1) & (room == 0)

    cleaned_cells = int(np.count_nonzero(cleaned))
    uncleaned_cells = total_floor - cleaned_cells
    repeated_cells = int(np.count_nonzero(repeated))

    coverage = (
        100 * cleaned_cells / total_floor
        if total_floor else 0
    )

    display = room.copy()
    display[cleaned] = 2
    display[room == 1] = 1

    ax.clear()

    ax.imshow(
        display,
        cmap=cmap,
        vmin=0,
        vmax=2,
        origin="lower",
        interpolation="nearest"
    )

    # Robot trail up to the current frame only.
    trail = route[:frame + 1]

    if len(trail) > 1:
        ax.plot(
            [p[0] for p in trail],
            [p[1] for p in trail],
            color="#00B8D9",
            linewidth=1.2,
            alpha=0.7
        )

    # Charging dock
    dx, dy = CHARGING_DOCK

    ax.add_patch(Rectangle(
        (dx - 0.45, dy - 0.45),
        0.9, 0.9,
        facecolor="gold",
        edgecolor="black",
        linewidth=1.5,
        zorder=5
    ))

    ax.text(
        dx + 0.55, dy + 0.45,
        "CHARGING DOCK",
        fontsize=8,
        fontweight="bold",
        color="black",
        zorder=6
    )

    # Cleaning radius
    ax.add_patch(Circle(
        (x, y),
        CLEANING_RADIUS,
        fill=False,
        edgecolor="blue",
        linestyle="--",
        linewidth=1.5
    ))

    # Robot body
    ax.add_patch(Rectangle(
        (x - 0.30, y - 0.30),
        0.6, 0.6,
        facecolor="#1687F8",
        edgecolor="white",
        zorder=7
    ))

    ax.set_xlim(-0.5, WIDTH - 0.5)
    ax.set_ylim(-0.5, HEIGHT - 0.5)
    ax.set_aspect("equal")

    ax.set_xticks(np.arange(0, WIDTH, 1))
    ax.set_yticks(np.arange(0, HEIGHT, 1))
    ax.grid(color="white", linewidth=0.5)

    ax.set_title(
        "CLEANING ROBOT - SWEEP PLANNER\n"
        f"Step: {frame + 1}/{len(route)} | "
        f"Coverage: {coverage:.2f}% | "
        f"Position: ({x}, {y})\n"
        f"Cleaned cells: {cleaned_cells} | "
        f"Uncleaned: {uncleaned_cells} | "
        f"Repeatedly cleaned cells: {repeated_cells}"
    )

    ax.set_xlabel("Room X")
    ax.set_ylabel("Room Y")


# =========================
# RUN ANIMATION
# =========================
animation = FuncAnimation(
    fig,
    update,
    frames=len(route),
    interval=40,
    repeat=False,
    cache_frame_data=False
)

plt.tight_layout()
plt.show()


# =========================
# RESULTS AT STOPPED FRAME
# =========================

# Use only positions actually displayed, never the
# unvisited remainder of the planned route.
if last_frame >= 0:
    actual_route = route[:last_frame + 1]
else:
    actual_route = []

final_counts = calculate_clean_counts(actual_route)

cleaned_cells = int(np.count_nonzero(
    (final_counts > 0) & (room == 0)
))

uncleaned_cells = total_floor - cleaned_cells

repeated_cells = int(np.count_nonzero(
    (final_counts > 1) & (room == 0)
))

coverage = (
    100 * cleaned_cells / total_floor
    if total_floor else 0
)

final_position = (
    actual_route[-1]
    if actual_route
    else None
)

returned_to_dock = final_position == CHARGING_DOCK

completed = last_frame == len(route) - 1

print("\n--- D3 Sweep Planner Results ---")
print("Process status:", "Completed" if completed else "Stopped early")
print("Robot positions visited:", len(actual_route))
print("Last robot position:", final_position)
print("Charging dock:", CHARGING_DOCK)
print("Total free floor cells:", total_floor)
print("Cleaned floor cells:", cleaned_cells)
print("Uncleaned floor cells:", uncleaned_cells)
print("Repeatedly cleaned floor cells:", repeated_cells)
print(f"Coverage: {coverage:.2f}%")
print("Robot at charging dock:", returned_to_dock)
