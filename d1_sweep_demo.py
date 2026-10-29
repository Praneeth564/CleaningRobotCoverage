import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

# ==========================================
# D1: PYTHONROBOTICS SWEEP DEMO (STANDALONE)
# ==========================================

# Define grid size and resolution
GRID_SIZE = 1.0
ROBOT_RADIUS = 1.0
WIDTH = 30
HEIGHT = 20

# Create boundaries (0 = free, 1 = obstacle)
ox, oy = [], []
for i in range(WIDTH):
    ox.append(i)
    oy.append(0)
    ox.append(i)
    oy.append(HEIGHT - 1)
for i in range(HEIGHT):
    ox.append(0)
    oy.append(i)
    ox.append(WIDTH - 1)
    oy.append(i)

# Generate a basic back-and-forth sweep path
px, py = [], []
sweep_direction = 1
for x in range(1, WIDTH - 1, int(ROBOT_RADIUS * 2)):
    y_range = range(1, HEIGHT - 1) if sweep_direction == 1 else range(HEIGHT - 2, 0, -1)
    for y in y_range:
        px.append(x)
        py.append(y)
    sweep_direction *= -1

# Animation setup
fig, ax = plt.subplots(figsize=(8, 6))
ax.plot(ox, oy, ".k", markersize=10, label="Obstacles")
ax.set_xlim(-1, WIDTH)
ax.set_ylim(-1, HEIGHT)
ax.set_title("D1: Sweep Coverage Path Planning Demo")
ax.grid(True)
ax.set_aspect("equal")

path_line, = ax.plot([], [], "-b", label="Sweep Path")
robot, = ax.plot([], [], "ro", markersize=8, label="Robot")
ax.legend(loc="upper right")

def update(frame):
    path_line.set_data(px[:frame+1], py[:frame+1])
    robot.set_data([px[frame]], [py[frame]])
    return path_line, robot

ani = FuncAnimation(fig, update, frames=len(px), interval=50, repeat=False)
plt.show()