
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.colors import ListedColormap
from matplotlib.patches import FancyBboxPatch, Circle, Rectangle
from collections import deque

from d7_layouts import create_room

# =====================================
# 1. CREATE THE ROOM
# =====================================
WIDTH = 40
HEIGHT = 25
CLEANING_RADIUS = 2
MAX_STEPS = 4000

room = create_room(1)

# Robot starting position (x, y)
start = (3, 3)

# Charging dock position (x, y)
CHARGING_DOCK = (3, 3)

# Directions: right, up, left, down
directions = [(1, 0), (0, 1), (-1, 0), (0, -1)]

total_floor = int(np.count_nonzero(room == 0))

if room[start[1], start[0]] != 0:
    raise ValueError("Robot starting position must be on free floor.")

if room[CHARGING_DOCK[1], CHARGING_DOCK[0]] != 0:
    raise ValueError("Charging dock must be on free floor.")


# =====================================
# 2. CLEANING FUNCTIONS
# =====================================
def clean_area(coverage, x, y):
    for dy in range(-CLEANING_RADIUS, CLEANING_RADIUS + 1):
        for dx in range(-CLEANING_RADIUS, CLEANING_RADIUS + 1):

            if dx * dx + dy * dy > CLEANING_RADIUS ** 2:
                continue

            nx, ny = x + dx, y + dy

            if 0 <= nx < WIDTH and 0 <= ny < HEIGHT:
                if room[ny, nx] == 0:
                    coverage[ny, nx] = True


def has_new_area(coverage, x, y):
    for dy in range(-CLEANING_RADIUS, CLEANING_RADIUS + 1):
        for dx in range(-CLEANING_RADIUS, CLEANING_RADIUS + 1):

            if dx * dx + dy * dy > CLEANING_RADIUS ** 2:
                continue

            nx, ny = x + dx, y + dy

            if not (0 <= nx < WIDTH and 0 <= ny < HEIGHT):
                continue

            if room[ny, nx] == 0 and not coverage[ny, nx]:
                return True

    return False


# Count how many times each floor cell is cleaned.
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


# =====================================
# 3. SAFE MOVEMENT
# =====================================
def is_free(x, y):
    return (
        0 < x < WIDTH - 1
        and 0 < y < HEIGHT - 1
        and room[y, x] == 0
    )


# =====================================
# 4. BFS FALLBACK
# =====================================
def find_fallback_path(start_position, coverage):
    queue = deque([start_position])
    previous = {start_position: None}
    target = None

    while queue:
        current = queue.popleft()
        x, y = current

        if has_new_area(coverage, x, y):
            target = current
            break

        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            neighbor = (nx, ny)

            if not is_free(nx, ny):
                continue

            if neighbor in previous:
                continue

            previous[neighbor] = current
            queue.append(neighbor)

    if target is None:
        return []

    result = []
    current = target

    while current is not None:
        result.append(current)
        current = previous[current]

    result.reverse()
    return result


# General BFS path to a specific destination.
def find_path(start_position, target):
    queue = deque([start_position])
    previous = {start_position: None}

    while queue:
        current = queue.popleft()

        if current == target:
            break

        x, y = current

        for dx, dy in directions:
            nx, ny = x + dx, y + dy
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

    result.reverse()
    return result


# =====================================
# 5. BUILD SPIRAL + BFS ROUTE
# =====================================
planned_coverage = np.zeros((HEIGHT, WIDTH), dtype=bool)

path = [start]
x, y = start
clean_area(planned_coverage, x, y)

direction_index = 0
segment_length = 1
segment_progress = 0
segments_completed = 0

while len(path) < MAX_STEPS:

    free_floor = room == 0

    if np.all(planned_coverage[free_floor]):
        break

    if segment_progress >= segment_length:
        direction_index = (direction_index + 1) % 4
        segments_completed += 1

        if segments_completed % 2 == 0:
            segment_length += 1

        segment_progress = 0
        continue

    dx, dy = directions[direction_index]
    nx, ny = x + dx, y + dy

    if is_free(nx, ny):
        x, y = nx, ny
        path.append((x, y))
        clean_area(planned_coverage, x, y)
        segment_progress += 1

    else:
        fallback = find_fallback_path((x, y), planned_coverage)

        if not fallback:
            break

        for fx, fy in fallback[1:]:
            if len(path) >= MAX_STEPS:
                break

            x, y = fx, fy
            path.append((x, y))
            clean_area(planned_coverage, x, y)

        segment_progress = segment_length


# =====================================
# 6. ADD RETURN TO CHARGING DOCK
# =====================================
return_path = find_path(path[-1], CHARGING_DOCK)

# Add the return journey if it fits within the step limit.
if return_path and len(path) + len(return_path) - 1 <= MAX_STEPS:
    path.extend(return_path[1:])
    print("Return route to charging dock added.")
else:
    print("Return route not added (no path or step limit reached).")

print("Charging dock:", CHARGING_DOCK)
print("Total planned robot positions:", len(path))


# =====================================
# 7. ROBOT ANIMATION
# =====================================
fig, ax = plt.subplots(figsize=(12, 7))

DIRTY_COLOR = "#E9EDF2"
CLEAN_COLOR = "#7EDC9A"
OBSTACLE_COLOR = "#394150"
ROBOT_COLOR = "#1687F8"
TRAIL_COLOR = "#00B8D9"

cmap = ListedColormap([
    DIRTY_COLOR,
    OBSTACLE_COLOR,
    CLEAN_COLOR
])

fig.patch.set_facecolor("#F5F7FA")

# Records the last animation frame actually displayed.
last_frame = -1


def update(frame):
    global last_frame

    last_frame = frame

    x, y = path[frame]

    # Count cleaning only up to the current frame.
    counts = calculate_clean_counts(path[:frame + 1])

    cleaned = (counts > 0) & (room == 0)
    repeated = (counts > 1) & (room == 0)

    total = total_floor
    cleaned_floor = int(np.count_nonzero(cleaned))
    uncleaned_floor = total - cleaned_floor
    repeated_floor = int(np.count_nonzero(repeated))

    coverage = 100 * cleaned_floor / total if total else 0

    display = room.copy()
    display[cleaned] = 2
    display[room == 1] = 1

    ax.clear()
    ax.set_facecolor("#FFFFFF")

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
    trail = path[:frame + 1]

    if len(trail) > 1:
        ax.plot(
            [p[0] for p in trail],
            [p[1] for p in trail],
            color=TRAIL_COLOR,
            linewidth=1.8,
            alpha=0.85,
            zorder=3
        )

    # Movement direction
    if frame > 0:
        previous_x, previous_y = path[frame - 1]
        dx = x - previous_x
        dy = y - previous_y
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
        (x, y),
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
        (x - 0.42, y - 0.32),
        0.84,
        0.64,
        boxstyle="round,pad=0.04,rounding_size=0.15",
        facecolor=ROBOT_COLOR,
        edgecolor="white",
        linewidth=1.5,
        zorder=6
    ))

    # Robot wheels
    for wheel_x in [x - 0.43, x + 0.30]:
        ax.add_patch(Rectangle(
            (wheel_x, y - 0.21),
            0.13,
            0.42,
            facecolor="#202938",
            edgecolor="white",
            linewidth=0.5,
            zorder=7
        ))

    # Robot sensor
    ax.add_patch(Circle(
        (x, y),
        0.10,
        facecolor="#FFFFFF",
        edgecolor="#0755A8",
        linewidth=1,
        zorder=8
    ))

    # Direction arrow
    ax.annotate(
        "",
        xy=(x + dx * 0.75, y + dy * 0.75),
        xytext=(x + dx * 0.20, y + dy * 0.20),
        arrowprops=dict(
            arrowstyle="-|>",
            color="#0755A8",
            linewidth=2
        ),
        zorder=9
    )

    # Room and grid
    ax.set_xlim(-0.5, WIDTH - 0.5)
    ax.set_ylim(-0.5, HEIGHT - 0.5)
    ax.set_aspect("equal")

    ax.set_xticks(np.arange(0, WIDTH, 1))
    ax.set_yticks(np.arange(0, HEIGHT, 1))

    ax.grid(color="white", linewidth=0.6, alpha=0.75)
    ax.tick_params(labelsize=8, length=0)

    ax.set_title(
        "CLEANING ROBOT SIMULATOR | SPIRAL + BFS",
        fontsize=15,
        fontweight="bold",
        color="#202938",
        pad=16
    )

    ax.set_xlabel("Room X", fontsize=10)
    ax.set_ylabel("Room Y", fontsize=10)

    # Live statistics
    status = (
        f"Step: {frame + 1}/{len(path)}\n"
        f"Coverage: {coverage:.1f}%\n"
        f"Position: ({x}, {y})\n"
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
# 8. RESULTS AT THE LAST DISPLAYED FRAME
# =====================================
# Never use the full planned route here unless the
# animation actually reached its final frame.

if last_frame >= 0:
    actual_path = path[:last_frame + 1]
else:
    actual_path = []

final_counts = calculate_clean_counts(actual_path)

free_floor = room == 0

cleaned_floor = int(np.count_nonzero(
    (final_counts > 0) & free_floor
))

uncleaned_floor = total_floor - cleaned_floor

repeated_floor = int(np.count_nonzero(
    (final_counts > 1) & free_floor
))

coverage_percent = (
    100 * cleaned_floor / total_floor
    if total_floor else 0
)

final_position = actual_path[-1] if actual_path else None

completed = last_frame == len(path) - 1

print("\n--- D4 Spiral Planner Results ---")
print("Process status:", "Completed" if completed else "Stopped early")
print("Robot positions visited:", len(actual_path))
print("Last robot position:", final_position)
print("Charging dock:", CHARGING_DOCK)
print("Robot at charging dock:", final_position == CHARGING_DOCK)
print("Total free floor cells:", total_floor)
print("Cleaned floor cells:", cleaned_floor)
print("Uncleaned floor cells:", uncleaned_floor)
print("Repeatedly cleaned floor cells:", repeated_floor)
print(f"Coverage: {coverage_percent:.2f}%")

if completed and uncleaned_floor == 0:
    print("Result: All free floor cells were cleaned.")
elif completed:
    print("Result: Route completed; some floor cells remain uncleaned.")
else:
    print("Result: Cleaning stopped before the planned route finished.")
