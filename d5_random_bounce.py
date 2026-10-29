
import random
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.colors import ListedColormap
from matplotlib.patches import FancyBboxPatch, Circle, Rectangle
from collections import deque

from d7_layouts import create_room

# =====================================
# 1. ROOM CONFIGURATION
# =====================================
WIDTH = 40
HEIGHT = 25
CLEANING_RADIUS = 2
SIMULATION_STEPS = 737

random.seed(42)

room = create_room(1)

# Robot starting position
start = (3, 3)
x, y = start

# Charging dock
CHARGING_DOCK = (3, 3)

directions = [(1, 0), (0, 1), (-1, 0), (0, -1)]
direction = random.choice(directions)

path = [(x, y)]
turns = 0

total_floor = int(np.count_nonzero(room == 0))

if room[start[1], start[0]] != 0:
    raise ValueError("Robot starting position must be on free floor.")

if room[CHARGING_DOCK[1], CHARGING_DOCK[0]] != 0:
    raise ValueError("Charging dock must be on free floor.")


# =====================================
# 2. CHECK SAFE MOVEMENT
# =====================================
def is_free(nx, ny):
    return (
        0 < nx < WIDTH - 1
        and 0 < ny < HEIGHT - 1
        and room[ny, nx] == 0
    )


# =====================================
# 3. CLEANING COUNTERS
# =====================================
def calculate_clean_counts(positions):
    # Each cell stores the number of times it is covered.
    counts = np.zeros((HEIGHT, WIDTH), dtype=np.int32)

    for cx, cy in positions:
        for dy in range(-CLEANING_RADIUS, CLEANING_RADIUS + 1):
            for dx in range(-CLEANING_RADIUS, CLEANING_RADIUS + 1):

                if dx * dx + dy * dy > CLEANING_RADIUS ** 2:
                    continue

                nx, ny = cx + dx, cy + dy

                if not (0 <= nx < WIDTH and 0 <= ny < HEIGHT):
                    continue

                if room[ny, nx] == 0:
                    counts[ny, nx] += 1

    return counts


# =====================================
# 4. BFS PATH TO CHARGING DOCK
# =====================================
def find_path_to_dock(start_position, target):
    queue = deque([start_position])
    previous = {start_position: None}

    while queue:
        current = queue.popleft()

        if current == target:
            break

        cx, cy = current

        for dx, dy in directions:
            nx, ny = cx + dx, cy + dy
            neighbor = (nx, ny)

            if not is_free(nx, ny):
                continue

            if neighbor in previous:
                continue

            previous[neighbor] = current
            queue.append(neighbor)

    if target not in previous:
        return []

    result = []
    current = target

    while current is not None:
        result.append(current)
        current = previous[current]

    return result[::-1]


# =====================================
# 5. GENERATE RANDOM BOUNCE ROUTE
# =====================================
for step in range(SIMULATION_STEPS - 1):
    dx, dy = direction
    nx, ny = x + dx, y + dy

    if is_free(nx, ny):
        x, y = nx, ny

    else:
        safe_directions = []

        for ndx, ndy in directions:
            tx, ty = x + ndx, y + ndy

            if is_free(tx, ty):
                safe_directions.append((ndx, ndy))

        if not safe_directions:
            break

        direction = random.choice(safe_directions)
        turns += 1

        # Immediately try the newly selected direction.
        dx, dy = direction
        nx, ny = x + dx, y + dy

        if is_free(nx, ny):
            x, y = nx, ny

    path.append((x, y))


# =====================================
# 6. PLAN RETURN TO CHARGING DOCK
# =====================================
return_path = find_path_to_dock(path[-1], CHARGING_DOCK)

if return_path:
    path.extend(return_path[1:])
    print("Return route to charging dock added.")
else:
    print("Warning: No safe return path to charging dock.")

print("Charging dock:", CHARGING_DOCK)
print("Planned robot positions:", len(path))


# =====================================
# 7. ANIMATION CONFIGURATION
# =====================================
fig, ax = plt.subplots(figsize=(12, 7))
fig.patch.set_facecolor("#F5F7FA")

DIRTY_COLOR = "#E9EDF2"
OBSTACLE_COLOR = "#394150"
CLEAN_COLOR = "#7EDC9A"
ROBOT_COLOR = "#1687F8"
TRAIL_COLOR = "#00B8D9"

cmap = ListedColormap([
    DIRTY_COLOR,
    OBSTACLE_COLOR,
    CLEAN_COLOR
])

# Last frame actually displayed by Matplotlib.
last_frame = -1


# =====================================
# 8. ANIMATE THE ROBOT
# =====================================
def update(frame):
    global last_frame

    last_frame = frame

    rx, ry = path[frame]

    # Only count positions visited up to this frame.
    actual_path = path[:frame + 1]
    counts = calculate_clean_counts(actual_path)

    cleaned = (counts > 0) & (room == 0)
    repeated = (counts > 1) & (room == 0)

    cleaned_floor = int(np.count_nonzero(cleaned))
    uncleaned_floor = total_floor - cleaned_floor
    repeated_floor = int(np.count_nonzero(repeated))

    percentage = (
        100 * cleaned_floor / total_floor
        if total_floor else 0
    )

    # Reconstruct the map for the current frame.
    display = room.copy()
    display[cleaned] = 2
    display[room == 1] = 1

    ax.clear()
    ax.set_facecolor("white")

    ax.imshow(
        display,
        cmap=cmap,
        vmin=0,
        vmax=2,
        origin="lower",
        interpolation="nearest",
        zorder=1
    )

    # Robot trail
    if len(actual_path) > 1:
        ax.plot(
            [p[0] for p in actual_path],
            [p[1] for p in actual_path],
            color=TRAIL_COLOR,
            linewidth=1.0,
            alpha=0.45,
            zorder=3
        )

    # Current movement direction
    if frame > 0:
        prev_x, prev_y = path[frame - 1]
        dx = rx - prev_x
        dy = ry - prev_y
    else:
        dx, dy = 1, 0

    # Charging dock
    dock_x, dock_y = CHARGING_DOCK

    ax.add_patch(Rectangle(
        (dock_x - 0.45, dock_y - 0.45),
        0.9,
        0.9,
        facecolor="gold",
        edgecolor="black",
        linewidth=1.5,
        zorder=5
    ))

    ax.text(
        dock_x + 0.55,
        dock_y + 0.45,
        "CHARGING DOCK",
        fontsize=8,
        fontweight="bold",
        color="black",
        zorder=6
    )

    # Cleaning radius
    ax.add_patch(Circle(
        (rx, ry),
        CLEANING_RADIUS,
        fill=False,
        edgecolor=ROBOT_COLOR,
        linewidth=1.8,
        linestyle="--",
        alpha=0.9,
        zorder=4
    ))

    # Robot body
    ax.add_patch(FancyBboxPatch(
        (rx - 0.38, ry - 0.30),
        0.76,
        0.60,
        boxstyle="round,pad=0.04,rounding_size=0.15",
        facecolor=ROBOT_COLOR,
        edgecolor="white",
        linewidth=1.5,
        zorder=6
    ))

    # Wheels
    for wheel_x in (rx - 0.43, rx + 0.30):
        ax.add_patch(Rectangle(
            (wheel_x, ry - 0.20),
            0.13,
            0.40,
            facecolor="#202938",
            edgecolor="white",
            linewidth=0.5,
            zorder=7
        ))

    # Front sensor
    ax.add_patch(Circle(
        (rx, ry),
        0.09,
        facecolor="white",
        edgecolor="#0755A8",
        linewidth=1,
        zorder=8
    ))

    # Direction arrow
    if dx != 0 or dy != 0:
        ax.annotate(
            "",
            xy=(rx + dx * 0.75, ry + dy * 0.75),
            xytext=(rx + dx * 0.20, ry + dy * 0.20),
            arrowprops=dict(
                arrowstyle="-|>",
                color="#0755A8",
                linewidth=2
            ),
            zorder=9
        )

    # Room grid
    ax.set_xlim(-0.5, WIDTH - 0.5)
    ax.set_ylim(-0.5, HEIGHT - 0.5)
    ax.set_aspect("equal")

    ax.set_xticks(np.arange(0, WIDTH, 1))
    ax.set_yticks(np.arange(0, HEIGHT, 1))

    ax.grid(color="white", linewidth=0.6, alpha=0.75)
    ax.tick_params(labelsize=8, length=0)

    ax.set_title(
        "CLEANING ROBOT SIMULATOR | D5 RANDOM BOUNCE",
        fontsize=14,
        fontweight="bold",
        color="#202938",
        pad=14
    )

    ax.set_xlabel("Room X")
    ax.set_ylabel("Room Y")

    # Live statistics
    status = (
        f"Step: {frame + 1}/{len(path)}\n"
        f"Coverage: {percentage:.1f}%\n"
        f"Robot position: ({rx}, {ry})\n"
        f"Obstacle turns: {turns}\n"
        f"Cleaned cells: {cleaned_floor}\n"
        f"Uncleaned cells: {uncleaned_floor}\n"
        f"Repeatedly cleaned: {repeated_floor}"
    )

    ax.text(
        0.02, 0.97, status,
        transform=ax.transAxes,
        va="top",
        ha="left",
        fontsize=9,
        color="#202938",
        bbox=dict(
            boxstyle="round,pad=0.6",
            facecolor="white",
            edgecolor="#CBD5E1",
            alpha=0.95
        ),
        zorder=10
    )

    # Legend
    legend_items = [
        Rectangle(
            (0, 0), 1, 1,
            facecolor=CLEAN_COLOR,
            label="Cleaned floor"
        ),
        Rectangle(
            (0, 0), 1, 1,
            facecolor=DIRTY_COLOR,
            label="Dirty floor"
        ),
        Rectangle(
            (0, 0), 1, 1,
            facecolor=OBSTACLE_COLOR,
            label="Obstacle"
        ),
        Rectangle(
            (0, 0), 1, 1,
            facecolor=ROBOT_COLOR,
            label="Robot"
        ),
        Rectangle(
            (0, 0), 1, 1,
            facecolor="gold",
            edgecolor="black",
            label="Charging dock"
        )
    ]

    ax.legend(
        handles=legend_items,
        loc="upper right",
        fontsize=8,
        framealpha=0.95,
        ncol=2
    )


animation = FuncAnimation(
    fig,
    update,
    frames=len(path),
    interval=40,
    repeat=False,
    cache_frame_data=False
)

plt.tight_layout()
plt.show()


# =====================================
# 9. FINAL RESULTS AT LAST DISPLAYED FRAME
# =====================================
# Do not calculate results from the unvisited route.

if last_frame >= 0:
    actual_path = path[:last_frame + 1]
else:
    actual_path = []

final_counts = calculate_clean_counts(actual_path)

cleaned_floor = int(np.count_nonzero(
    (final_counts > 0) & (room == 0)
))

uncleaned_floor = total_floor - cleaned_floor

repeated_floor = int(np.count_nonzero(
    (final_counts > 1) & (room == 0)
))

coverage_percent = (
    100 * cleaned_floor / total_floor
    if total_floor else 0
)

final_position = actual_path[-1] if actual_path else None

completed = last_frame == len(path) - 1

print("\n--- D5 Random Bounce Results ---")
print("Process status:", "Completed" if completed else "Stopped early")
print("Robot positions visited:", len(actual_path))
print("Last robot position:", final_position)
print("Charging dock:", CHARGING_DOCK)
print("Robot at charging dock:", final_position == CHARGING_DOCK)
print("Obstacle-triggered turns:", turns)
print("Total free floor cells:", total_floor)
print("Cleaned floor cells:", cleaned_floor)
print("Uncleaned floor cells:", uncleaned_floor)
print("Repeatedly cleaned floor cells:", repeated_floor)
print(f"Coverage: {coverage_percent:.2f}%")
