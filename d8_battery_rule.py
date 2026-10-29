import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.colors import ListedColormap
from matplotlib.patches import Rectangle, Circle
from collections import deque


# ============================================================
# D8: PROFESSIONAL BATTERY-AWARE CLEANING ROBOT
# ============================================================

# Room configuration
WIDTH = 40
HEIGHT = 25
MAX_STEPS = 4000

# Cleaning configuration
CLEANING_RADIUS = 2

# Increased battery capacity
MAX_BATTERY = 300.0
INITIAL_BATTERY = 300.0

# Battery consumption and charging
MOVEMENT_COST = 1.0
TURN_COST = 0.2
CHARGING_RATE = 10.0
BATTERY_RESERVE = 30.0

# Animation speed in milliseconds
ANIMATION_INTERVAL = 30


# ============================================================
# 1. DASHBOARD COLORS
# ============================================================

BG = "#0B1220"
PANEL = "#151F30"
PANEL_EDGE = "#293B52"

WHITE = "#EAF2FF"
MUTED = "#8DA4C0"

GREEN = "#27DDA0"
BLUE = "#38BDF8"
CYAN = "#00D9FF"
ORANGE = "#FFB454"
RED = "#FF5263"

DIRTY_COLOR = "#E8EDF4"
OBSTACLE_COLOR = "#303B4F"
CLEAN_COLOR = "#55D99A"
ROBOT_COLOR = "#38BDF8"
TRAIL_COLOR = "#00D9FF"


# ============================================================
# 2. CREATE ROOM
# ============================================================

# 0 = free floor
# 1 = wall or furniture
# 2 = cleaned floor, used for display

room = np.zeros((HEIGHT, WIDTH), dtype=int)

# Outer walls
room[0, :] = 1
room[-1, :] = 1
room[:, 0] = 1
room[:, -1] = 1

# Furniture
room[6:11, 7:13] = 1
room[15:20, 22:30] = 1
room[3:8, 31:35] = 1

# Charging dock and starting position
DOCK = (2, 2)
start = DOCK

free_floor = room == 0
total_floor = int(np.count_nonzero(free_floor))

DIRECTIONS = [
    (1, 0),
    (0, 1),
    (-1, 0),
    (0, -1)
]


# ============================================================
# 3. CLEANING FUNCTIONS
# ============================================================

cleaned = np.zeros((HEIGHT, WIDTH), dtype=bool)


def clean_area(x, y):
    """Clean the circular area around the robot."""

    for dy in range(-CLEANING_RADIUS, CLEANING_RADIUS + 1):
        for dx in range(-CLEANING_RADIUS, CLEANING_RADIUS + 1):

            if dx * dx + dy * dy > CLEANING_RADIUS ** 2:
                continue

            nx = x + dx
            ny = y + dy

            if not (0 <= nx < WIDTH and 0 <= ny < HEIGHT):
                continue

            if free_floor[ny, nx]:
                cleaned[ny, nx] = True


def has_new_area(x, y):
    """Check whether the robot can clean new floor."""

    for dy in range(-CLEANING_RADIUS, CLEANING_RADIUS + 1):
        for dx in range(-CLEANING_RADIUS, CLEANING_RADIUS + 1):

            if dx * dx + dy * dy > CLEANING_RADIUS ** 2:
                continue

            nx = x + dx
            ny = y + dy

            if not (0 <= nx < WIDTH and 0 <= ny < HEIGHT):
                continue

            if free_floor[ny, nx] and not cleaned[ny, nx]:
                return True

    return False


# ============================================================
# 4. SAFE MOVEMENT AND BFS
# ============================================================

def is_free(x, y):
    return (
        0 < x < WIDTH - 1
        and 0 < y < HEIGHT - 1
        and room[y, x] == 0
    )


def bfs(start_position, target):
    """Find the shortest safe path to a target."""

    queue = deque([start_position])
    previous = {start_position: None}

    while queue:
        current = queue.popleft()

        if current == target:
            break

        x, y = current

        for dx, dy in DIRECTIONS:
            nx = x + dx
            ny = y + dy
            neighbor = (nx, ny)

            if not is_free(nx, ny):
                continue

            if neighbor in previous:
                continue

            previous[neighbor] = current
            queue.append(neighbor)

    if target not in previous:
        return []

    path = []
    current = target

    while current is not None:
        path.append(current)
        current = previous[current]

    return path[::-1]


def find_nearest_cleaning_path(start_position):
    """Find the nearest reachable position that cleans new floor."""

    queue = deque([start_position])
    previous = {start_position: None}
    target = None

    while queue:
        current = queue.popleft()
        x, y = current

        if has_new_area(x, y):
            target = current
            break

        for dx, dy in DIRECTIONS:
            nx = x + dx
            ny = y + dy
            neighbor = (nx, ny)

            if not is_free(nx, ny):
                continue

            if neighbor in previous:
                continue

            previous[neighbor] = current
            queue.append(neighbor)

    if target is None:
        return []

    path = []
    current = target

    while current is not None:
        path.append(current)
        current = previous[current]

    return path[::-1]


# ============================================================
# 5. SIMULATION DATA
# ============================================================

frames = []
trail = []

robot_x, robot_y = start

battery = INITIAL_BATTERY
simulation_time = 0
total_moves = 0
total_turns = 0
charging_cycles = 0
previous_direction = None


def record_frame(status):
    """Save the current simulation state for animation."""

    coverage_count = int(np.count_nonzero(cleaned & free_floor))

    coverage_percent = (
        100 * coverage_count / total_floor
        if total_floor else 0
    )

    frames.append({
        "x": robot_x,
        "y": robot_y,
        "battery": battery,
        "time": simulation_time,
        "moves": total_moves,
        "turns": total_turns,
        "cycles": charging_cycles,
        "coverage": coverage_percent,
        "status": status,
        "cleaned": cleaned.copy(),
        "trail": trail[-100:].copy()
    })


def move_robot(position, status="CLEANING"):
    """Move one cell and update battery consumption."""

    global robot_x, robot_y
    global battery, simulation_time
    global total_moves, total_turns, previous_direction

    nx, ny = position

    dx = nx - robot_x
    dy = ny - robot_y

    direction = (dx, dy)

    # Consume battery for direction changes
    if previous_direction is not None:
        if direction != previous_direction:
            total_turns += 1
            battery -= TURN_COST

    # Consume battery for movement
    battery -= MOVEMENT_COST
    battery = max(0.0, battery)

    robot_x, robot_y = nx, ny

    total_moves += 1
    simulation_time += 1
    previous_direction = direction

    trail.append((robot_x, robot_y))

    clean_area(robot_x, robot_y)
    record_frame(status)


# ============================================================
# 6. BATTERY-AWARE CLEANING
# ============================================================

clean_area(robot_x, robot_y)
trail.append((robot_x, robot_y))
record_frame("CLEANING")

while total_moves < MAX_STEPS:

    # Stop the cleaning loop once all free floor is cleaned.
    # The final return to the dock is handled after this loop.
    if np.all(cleaned[free_floor]):
        break

    # Find a route to the charging dock
    dock_path = bfs(
        (robot_x, robot_y),
        DOCK
    )

    if not dock_path:
        record_frame("DOCK UNREACHABLE")
        break

    distance_to_dock = len(dock_path) - 1

    # Estimate battery needed to return to dock
    estimated_return_cost = (
        distance_to_dock * MOVEMENT_COST
        + BATTERY_RESERVE
    )

    # Return when battery reaches the safety threshold
    must_charge = (
        battery < MAX_BATTERY
        and battery <= estimated_return_cost
    )

    if must_charge:

        record_frame("RETURNING TO DOCK")

        for position in dock_path[1:]:

            if total_moves >= MAX_STEPS:
                break

            move_robot(position, "RETURNING TO DOCK")

        # Recharge only after reaching the dock
        if (robot_x, robot_y) == DOCK:

            charging_cycles += 1
            record_frame("CHARGING")

            while battery < MAX_BATTERY:

                battery = min(
                    MAX_BATTERY,
                    battery + CHARGING_RATE
                )

                simulation_time += 1
                record_frame("CHARGING")

            record_frame("CHARGE COMPLETE")

        else:
            record_frame("BATTERY LIMIT")
            break

        continue

    # Find the nearest location with new floor to clean
    cleaning_path = find_nearest_cleaning_path(
        (robot_x, robot_y)
    )

    if not cleaning_path:
        record_frame("CLEANING COMPLETE")
        break

    # Move one cell at a time
    if len(cleaning_path) > 1:

        next_position = cleaning_path[1]

        # Avoid a move if there is insufficient battery
        next_x, next_y = next_position

        next_direction = (
            next_x - robot_x,
            next_y - robot_y
        )

        next_cost = MOVEMENT_COST

        if (
            previous_direction is not None
            and next_direction != previous_direction
        ):
            next_cost += TURN_COST

        if battery < next_cost:
            record_frame("BATTERY LIMIT")
            break

        move_robot(next_position, "CLEANING")

    else:
        clean_area(robot_x, robot_y)

        if not has_new_area(robot_x, robot_y):
            break


# ============================================================
# 7. RETURN TO DOCK AFTER CLEANING IS COMPLETE
# ============================================================

if np.all(cleaned[free_floor]):
    # The room is clean. Now send the robot back to its charging station.
    if (robot_x, robot_y) != DOCK:
        final_dock_path = bfs((robot_x, robot_y), DOCK)

        if final_dock_path:
            record_frame("ROOM CLEANED - RETURNING TO DOCK")

            for position in final_dock_path[1:]:
                # Keep the existing battery model and never move with
                # insufficient battery. The normal reserve rule should
                # leave enough power for this trip.
                next_x, next_y = position
                next_direction = (next_x - robot_x, next_y - robot_y)
                required_cost = MOVEMENT_COST

                if (
                    previous_direction is not None
                    and next_direction != previous_direction
                ):
                    required_cost += TURN_COST

                if battery < required_cost:
                    record_frame("BATTERY TOO LOW TO RETURN")
                    break

                move_robot(position, "RETURNING TO DOCK")

        else:
            record_frame("DOCK UNREACHABLE")

    if (robot_x, robot_y) == DOCK:
        record_frame("DOCKED - CLEANING COMPLETE")
    elif np.all(cleaned[free_floor]):
        record_frame("CLEANING COMPLETE - RETURN INCOMPLETE")


# ============================================================
# 7. CREATE PROFESSIONAL DASHBOARD
# ============================================================

cmap = ListedColormap([
    DIRTY_COLOR,
    OBSTACLE_COLOR,
    CLEAN_COLOR
])

fig = plt.figure(
    figsize=(11.5, 7),
    facecolor=BG
)

gs = fig.add_gridspec(
    1, 2,
    width_ratios=[3.5, 1.2],
    left=0.065,
    right=0.96,
    top=0.84,
    bottom=0.10,
    wspace=0.12
)

ax = fig.add_subplot(gs[0, 0])
panel = fig.add_subplot(gs[0, 1])

ax.set_facecolor(BG)
panel.set_facecolor(BG)

fig.text(
    0.5, 0.955,
    "AUTONOMOUS CLEANING ROBOT  /  BATTERY MONITOR",
    ha="center",
    color=WHITE,
    fontsize=15,
    fontweight="bold"
)

fig.text(
    0.5, 0.920,
    "D8  |  Coverage planning  |  Battery-aware navigation",
    ha="center",
    color=MUTED,
    fontsize=9
)


# ============================================================
# 8. ROOM MAP
# ============================================================

display = room.copy()

image = ax.imshow(
    display,
    cmap=cmap,
    vmin=0,
    vmax=2,
    origin="lower",
    interpolation="nearest"
)

ax.set_xlim(-0.5, WIDTH - 0.5)
ax.set_ylim(-0.5, HEIGHT - 0.5)
ax.set_aspect("equal")

ax.set_xlabel("Room X", color=MUTED, labelpad=7)
ax.set_ylabel("Room Y", color=MUTED, labelpad=7)

ax.set_xticks(np.arange(0, WIDTH, 5))
ax.set_yticks(np.arange(0, HEIGHT, 5))

ax.set_xticks(np.arange(-0.5, WIDTH, 1), minor=True)
ax.set_yticks(np.arange(-0.5, HEIGHT, 1), minor=True)

ax.grid(
    which="minor",
    color="#FFFFFF",
    linewidth=0.35,
    alpha=0.55
)

ax.tick_params(colors=MUTED, labelsize=8)

for spine in ax.spines.values():
    spine.set_color(PANEL_EDGE)


# Charging dock
dock_marker = Rectangle(
    (DOCK[0] - 0.35, DOCK[1] - 0.35),
    0.7, 0.7,
    facecolor=ORANGE,
    edgecolor=WHITE,
    linewidth=1.1,
    zorder=6
)

ax.add_patch(dock_marker)

ax.text(
    DOCK[0] + 0.65,
    DOCK[1] + 0.35,
    "DOCK",
    color=ORANGE,
    fontsize=7,
    fontweight="bold"
)


# Movement trail
trail_line, = ax.plot(
    [],
    [],
    color=TRAIL_COLOR,
    linewidth=1.5,
    alpha=0.8,
    zorder=4
)


# Robot cleaning radius
robot_ring = Circle(
    (robot_x, robot_y),
    CLEANING_RADIUS,
    fill=False,
    edgecolor=BLUE,
    linewidth=1.6,
    linestyle="--",
    alpha=0.8,
    zorder=5
)

ax.add_patch(robot_ring)


# Robot glow
robot_glow = ax.scatter(
    [robot_x],
    [robot_y],
    s=280,
    color=BLUE,
    alpha=0.14,
    edgecolors="none",
    zorder=6
)


# Robot body
robot_marker = ax.scatter(
    [robot_x],
    [robot_y],
    s=75,
    marker="o",
    color=ROBOT_COLOR,
    edgecolors=WHITE,
    linewidths=1.1,
    zorder=7
)


# Legend
legend_handles = [
    Rectangle((0, 0), 1, 1, facecolor=CLEAN_COLOR, label="Cleaned"),
    Rectangle((0, 0), 1, 1, facecolor=DIRTY_COLOR, label="Dirty floor"),
    Rectangle((0, 0), 1, 1, facecolor=OBSTACLE_COLOR, label="Obstacle"),
    Rectangle((0, 0), 1, 1, facecolor=ORANGE, label="Charging dock")
]

legend = ax.legend(
    handles=legend_handles,
    loc="upper right",
    fontsize=7,
    framealpha=0.92
)

legend.get_frame().set_facecolor(PANEL)
legend.get_frame().set_edgecolor(PANEL_EDGE)

for legend_text in legend.get_texts():
    legend_text.set_color(WHITE)


# ============================================================
# 9. DASHBOARD PANEL
# ============================================================

panel.set_xlim(0, 1)
panel.set_ylim(0, 1)
panel.axis("off")


def add_card(y, height):
    card = Rectangle(
        (0.02, y),
        0.96,
        height,
        facecolor=PANEL,
        edgecolor=PANEL_EDGE,
        linewidth=1.0,
        transform=panel.transAxes,
        zorder=1
    )

    panel.add_patch(card)


# Battery card
add_card(0.69, 0.25)

panel.text(
    0.09, 0.89, "BATTERY",
    color=MUTED,
    fontsize=9,
    fontweight="bold",
    transform=panel.transAxes
)

battery_text = panel.text(
    0.09, 0.825, "",
    color=GREEN,
    fontsize=21,
    fontweight="bold",
    transform=panel.transAxes
)

battery_status = panel.text(
    0.09, 0.785, "",
    color=GREEN,
    fontsize=8,
    fontweight="bold",
    transform=panel.transAxes
)

battery_outline = Rectangle(
    (0.09, 0.715),
    0.78, 0.045,
    facecolor="#202E41",
    edgecolor=MUTED,
    linewidth=1.0,
    transform=panel.transAxes
)

panel.add_patch(battery_outline)

# Battery terminal
panel.add_patch(
    Rectangle(
        (0.875, 0.727),
        0.025, 0.020,
        facecolor=MUTED,
        edgecolor="none",
        transform=panel.transAxes
    )
)

battery_fill = Rectangle(
    (0.098, 0.723),
    0.0, 0.029,
    facecolor=GREEN,
    edgecolor="none",
    transform=panel.transAxes
)

panel.add_patch(battery_fill)


# Live telemetry card
add_card(0.37, 0.28)

panel.text(
    0.09, 0.615, "LIVE TELEMETRY",
    color=MUTED,
    fontsize=9,
    fontweight="bold",
    transform=panel.transAxes
)

coverage_text = panel.text(
    0.09, 0.555, "",
    color=GREEN,
    fontsize=20,
    fontweight="bold",
    transform=panel.transAxes
)

panel.text(
    0.09, 0.515, "FLOOR COVERAGE",
    color=MUTED,
    fontsize=7,
    transform=panel.transAxes
)

coverage_bg = Rectangle(
    (0.09, 0.475),
    0.78, 0.018,
    facecolor="#26364B",
    edgecolor="none",
    transform=panel.transAxes
)

panel.add_patch(coverage_bg)

coverage_fill = Rectangle(
    (0.09, 0.475),
    0.0, 0.018,
    facecolor=GREEN,
    edgecolor="none",
    transform=panel.transAxes
)

panel.add_patch(coverage_fill)

step_text = panel.text(
    0.09, 0.435, "",
    color=WHITE,
    fontsize=8,
    transform=panel.transAxes
)

position_text = panel.text(
    0.09, 0.395, "",
    color=WHITE,
    fontsize=8,
    transform=panel.transAxes
)


# Robot status card
add_card(0.06, 0.26)

panel.text(
    0.09, 0.275, "ROBOT STATUS",
    color=MUTED,
    fontsize=9,
    fontweight="bold",
    transform=panel.transAxes
)

status_text = panel.text(
    0.09, 0.225, "",
    color=GREEN,
    fontsize=9,
    fontweight="bold",
    transform=panel.transAxes
)

time_text = panel.text(
    0.09, 0.185, "",
    color=MUTED,
    fontsize=8,
    transform=panel.transAxes
)

moves_text = panel.text(
    0.09, 0.145, "",
    color=MUTED,
    fontsize=8,
    transform=panel.transAxes
)

cycles_text = panel.text(
    0.09, 0.105, "",
    color=MUTED,
    fontsize=8,
    transform=panel.transAxes
)


# ============================================================
# 10. ANIMATION UPDATE
# ============================================================

def update(frame_number):
    data = frames[frame_number]

    rx = data["x"]
    ry = data["y"]

    battery_level = data["battery"]
    coverage_percent = data["coverage"]
    status = data["status"]

    # Update floor colors
    display = room.copy()
    display[data["cleaned"]] = 2
    display[room == 1] = 1

    image.set_data(display)

    # Robot glow pulse
    pulse = 1 + 0.18 * np.sin(frame_number * 0.18)

    robot_glow.set_offsets([[rx, ry]])
    robot_glow.set_sizes([280 * pulse])

    robot_marker.set_offsets([[rx, ry]])

    # Animated cleaning radius
    robot_ring.center = (rx, ry)

    robot_ring.set_alpha(
        0.55 + 0.35 * abs(np.sin(frame_number * 0.10))
    )

    # Movement trail
    robot_trail = data["trail"]

    if robot_trail:
        trail_x = [p[0] for p in robot_trail]
        trail_y = [p[1] for p in robot_trail]

        trail_line.set_data(trail_x, trail_y)

    # Battery percentage
    battery_fraction = max(
        0.0,
        min(1.0, battery_level / MAX_BATTERY)
    )

    battery_fill.set_width(0.764 * battery_fraction)

    if battery_level <= 20:
        battery_color = RED
        battery_label = "LOW POWER"
    elif status == "CHARGING":
        battery_color = ORANGE
        battery_label = "RECHARGING"
    else:
        battery_color = GREEN
        battery_label = "POWER NORMAL"

    battery_fill.set_facecolor(battery_color)
    battery_text.set_color(battery_color)
    battery_text.set_text(f"{battery_fraction * 100:.0f}%")

    battery_status.set_text(battery_label)
    battery_status.set_color(battery_color)

    # Coverage progress bar
    coverage_fraction = max(
        0.0,
        min(1.0, coverage_percent / 100)
    )

    coverage_fill.set_width(0.78 * coverage_fraction)
    coverage_text.set_text(f"{coverage_percent:.1f}%")

    if coverage_percent >= 100:
        coverage_text.set_color(GREEN)
    else:
        coverage_text.set_color(BLUE)

    # Telemetry
    step_text.set_text(
        f"Step       {frame_number + 1} / {len(frames)}"
    )

    position_text.set_text(
        f"Position   ({rx}, {ry})"
    )

    # Status colors
    status_text.set_text(status)

    if status == "CHARGING":
        status_text.set_color(ORANGE)
    elif status == "RETURNING TO DOCK":
        status_text.set_color(BLUE)
    elif status in ("CLEANING COMPLETE", "DOCKED - CLEANING COMPLETE"):
        status_text.set_color(GREEN)
    elif status in ("BATTERY LIMIT", "BATTERY TOO LOW TO RETURN", "CLEANING COMPLETE - RETURN INCOMPLETE"):
        status_text.set_color(RED)
    else:
        status_text.set_color(GREEN)

    time_text.set_text(
        f"Sim time   {data['time']}"
    )

    moves_text.set_text(
        f"Moves      {data['moves']}"
    )

    cycles_text.set_text(
        f"Charge cycles   {data['cycles']}"
    )

    ax.set_title(
        "ROOM COVERAGE MAP   |   "
        f"FRAME {frame_number + 1} / {len(frames)}",
        color=WHITE,
        fontsize=10,
        fontweight="bold",
        pad=12
    )

    return (
        image,
        trail_line,
        robot_ring,
        robot_glow,
        robot_marker,
        battery_fill,
        battery_text,
        battery_status,
        coverage_fill,
        coverage_text,
        step_text,
        position_text,
        status_text,
        time_text,
        moves_text,
        cycles_text
    )


# ============================================================
# 11. RUN ANIMATION
# ============================================================

animation = FuncAnimation(
    fig,
    update,
    frames=len(frames),
    interval=ANIMATION_INTERVAL,
    repeat=False,
    blit=False,
    cache_frame_data=False
)

plt.show()


# ============================================================
# 12. FINAL RESULTS
# ============================================================

cleaned_floor = int(np.count_nonzero(cleaned & free_floor))
uncleaned_floor = total_floor - cleaned_floor
returned_to_dock = (robot_x, robot_y) == DOCK

coverage_percent = (
    100 * cleaned_floor / total_floor
    if total_floor else 0
)

print("\n" + "=" * 45)
print("       D8 BATTERY ROBOT RESULTS")
print("=" * 45)

print(f"Room size:              {WIDTH} x {HEIGHT}")
print(f"Cleaning radius:        {CLEANING_RADIUS}")
print(f"Maximum battery:        {MAX_BATTERY:.1f}")
print(f"Total free floor cells: {total_floor}")
print(f"Cleaned floor cells:    {cleaned_floor}")
print(f"Uncleaned floor cells:  {uncleaned_floor}")
print(f"Coverage:               {coverage_percent:.2f}%")
print(f"Returned to dock:       {'YES' if returned_to_dock else 'NO'}")
print(f"Final robot position:   ({robot_x}, {robot_y})")

print(f"\nTotal movement steps:   {total_moves}")
print(f"Total turns:            {total_turns}")
print(f"Charging cycles:        {charging_cycles}")
print(f"Final battery:          {battery:.1f}")
print(f"Elapsed simulated time: {simulation_time}")

print("\nBattery model:")
print(f"Movement cost:          {MOVEMENT_COST}")
print(f"Turn cost:              {TURN_COST}")
print(f"Charging rate:          {CHARGING_RATE} units per time step")
print(f"Battery reserve:        {BATTERY_RESERVE}")

print("\nThese are simulated values, not physical")
print("robot measurements.")
print("=" * 45)
# ============================================================
# 13. COVERAGE OVER TIME PLOT (D8 DELIVERABLE)
# ============================================================

times = [frame_data["time"] for frame_data in frames]
coverages = [frame_data["coverage"] for frame_data in frames]

plt.figure(figsize=(9, 5), facecolor="#F5F7FA")
plt.plot(times, coverages, color="#38BDF8", linewidth=2.5)

plt.title("D8: Floor Coverage Over Time", fontsize=14, fontweight="bold", pad=15)
plt.xlabel("Simulated Time Steps", fontsize=11)
plt.ylabel("Coverage (%)", fontsize=11)

plt.grid(True, linestyle="--", alpha=0.6)
plt.ylim(0, 105)
plt.xlim(0, max(times) if times else 1)

plt.tight_layout()
plt.show()