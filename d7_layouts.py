
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap

# =====================================
# D7: FIVE ROOM LAYOUTS
# =====================================
WIDTH = 40
HEIGHT = 25

def create_room(layout_number):
    # 0 = free floor, 1 = wall or furniture
    room = np.zeros((HEIGHT, WIDTH), dtype=int)

    # Outer walls
    room[0, :] = 1
    room[-1, :] = 1
    room[:, 0] = 1
    room[:, -1] = 1

    if layout_number == 1:
        # Layout 1: Three separate furniture blocks
        room[6:11, 7:13] = 1
        room[15:20, 22:30] = 1
        room[3:8, 31:35] = 1

    elif layout_number == 2:
        # Layout 2: Furniture along the sides
        room[5:19, 8:11] = 1
        room[5:19, 29:32] = 1
        room[15:18, 11:29] = 1

    elif layout_number == 3:
        # Layout 3: Small scattered furniture
        room[4:7, 5:9] = 1
        room[10:14, 16:20] = 1
        room[18:22, 27:32] = 1
        room[5:10, 33:36] = 1

    elif layout_number == 4:
        # Layout 4: Long central obstacle
        room[11:14, 9:31] = 1
        room[4:8, 19:23] = 1
        room[17:21, 5:9] = 1

    elif layout_number == 5:
        # Layout 5: Narrow passages and blocks
        room[4:19, 10:13] = 1
        room[4:19, 26:29] = 1
        room[4:7, 13:26] = 1
        room[16:19, 13:26] = 1

    return room


# =====================================
# DISPLAY ALL FIVE LAYOUTS
# =====================================
fig, axes = plt.subplots(2, 3, figsize=(14, 8))
axes = axes.flatten()

cmap = ListedColormap(["#e8e8e8", "#444444"])

for number in range(1, 6):
    room = create_room(number)
    ax = axes[number - 1]

    ax.imshow(
        room,
        cmap=cmap,
        vmin=0,
        vmax=1,
        origin="lower",
        interpolation="nearest"
    )

    # Same starting point for every room
    ax.plot(3, 3, "ro", markersize=6)

    ax.set_title(f"Layout {number}")
    ax.set_xlabel("Room X")
    ax.set_ylabel("Room Y")
    ax.set_aspect("equal")

# Remove the unused sixth panel
fig.delaxes(axes[5])

plt.suptitle("D7: Five Cleaning Robot Room Layouts")
plt.tight_layout()
plt.show()

print("D7: Five room layouts created successfully.")

for number in range(1, 6):
    room = create_room(number)
    free_cells = np.count_nonzero(room == 0)
    print(f"Layout {number}: {free_cells} free floor cells")
