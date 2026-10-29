
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.colors import ListedColormap

# 1. Create the room
WIDTH = 40
HEIGHT = 25

# Cell meanings:
# 0 = dirty floor
# 1 = wall or furniture
# 2 = cleaned floor
room = np.zeros((HEIGHT, WIDTH), dtype=int)

# 2. Add outer walls
room[0, :] = 1
room[-1, :] = 1
room[:, 0] = 1
room[:, -1] = 1

# 3. Add furniture
room[6:11, 7:13] = 1
room[15:20, 22:30] = 1
room[3:8, 31:35] = 1

# 4. Set the robot's starting position
robot_x = 2
robot_y = 2

# Robot footprint: cleans nearby floor cells
CLEANING_RADIUS = 2

# 5. Create a simple test route
path = []

# Move horizontally across the room
for x in range(2, WIDTH - 2):
    path.append((x, 2))

# Move upwards
for y in range(2, HEIGHT - 2):
    path.append((WIDTH - 3, y))

# Move back across the room
for x in range(WIDTH - 3, 2, -1):
    path.append((x, HEIGHT - 3))


# 6. Clean the cells around the robot
def clean_area(x, y):
    for dy in range(-CLEANING_RADIUS, CLEANING_RADIUS + 1):
        for dx in range(-CLEANING_RADIUS, CLEANING_RADIUS + 1):
            nx = x + dx
            ny = y + dy

            # Circular cleaning footprint
            if dx * dx + dy * dy > CLEANING_RADIUS ** 2:
                continue

            # Stay inside the room
            if not (0 <= nx < WIDTH and 0 <= ny < HEIGHT):
                continue

            # Do not clean walls or furniture
            if room[ny, nx] == 1:
                continue

            room[ny, nx] = 2


# 7. Set up the animation
fig, ax = plt.subplots(figsize=(10, 6))

colors = ["#e8e8e8", "#444444", "#79d279"]
cmap = ListedColormap(colors)

robot_dot, = ax.plot([], [], "ro", markersize=12)

ax.set_title("D2 - Cleaning Robot Room Simulator")
ax.set_xlabel("Room X")
ax.set_ylabel("Room Y")
ax.set_xlim(-0.5, WIDTH - 0.5)
ax.set_ylim(-0.5, HEIGHT - 0.5)
ax.set_aspect("equal")
ax.set_xticks(np.arange(-0.5, WIDTH, 1), minor=True)
ax.set_yticks(np.arange(-0.5, HEIGHT, 1), minor=True)
ax.grid(which="minor", color="white", linewidth=0.5)


def update(frame):
    global robot_x, robot_y

    robot_x, robot_y = path[frame]

    clean_area(robot_x, robot_y)

    ax.clear()
    ax.imshow(
        room,
        cmap=cmap,
        vmin=0,
        vmax=2,
        origin="lower",
        interpolation="nearest"
    )

    # Draw the robot
    circle = plt.Circle(
        (robot_x, robot_y),
        CLEANING_RADIUS,
        color="red",
        fill=False,
        linewidth=2
    )
    ax.add_patch(circle)
    ax.plot(robot_x, robot_y, "ro", markersize=7)

    ax.set_title(
        f"D2 - Room Simulator | Step {frame + 1}/{len(path)}"
    )
    ax.set_xlabel("Room X")
    ax.set_ylabel("Room Y")
    ax.set_xlim(-0.5, WIDTH - 0.5)
    ax.set_ylim(-0.5, HEIGHT - 0.5)
    ax.set_aspect("equal")
    ax.set_xticks(np.arange(-0.5, WIDTH, 1), minor=True)
    ax.set_yticks(np.arange(-0.5, HEIGHT, 1), minor=True)
    ax.grid(which="minor", color="white", linewidth=0.5)


animation = FuncAnimation(
    fig,
    update,
    frames=len(path),
    interval=100,
    repeat=False
)

plt.tight_layout()
plt.show()
