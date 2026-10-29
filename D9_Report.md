# D9: Cleaning Robot Coverage — Sweep, Spiral and Random Bounce

## 1. Abstract

This project develops a grid-based cleaning robot simulator using Python. It implements and compares three cleaning strategies: Sweep, Spiral with Breadth-First Search (BFS), and Random Bounce. The simulation uses a 40 × 25 room containing walls and furniture obstacles. A circular cleaning radius of 2 grid cells is used to determine the floor covered by the robot.

The performance of each strategy is evaluated using coverage percentage, repeated coverage, movement steps, turns, path length, and uncleaned floor cells. A battery-aware cleaning strategy is also implemented, allowing the robot to return to its charging station, recharge, resume cleaning, and return to the dock after completing the room.

In the D6 comparison, Spiral + BFS achieved 100% coverage, Sweep achieved 87.88%, and Random Bounce achieved 50.38%. The D8 battery-aware simulation cleaned all 784 free floor cells and returned to the charging station successfully.

## 2. Introduction

Cleaning robots must navigate a room, avoid obstacles, and cover as much floor as possible without wasting time or battery power. Coverage Path Planning (CPP) determines the route a robot follows to clean or inspect a specified area.

Different planning strategies perform differently depending on room geometry, furniture placement, and battery constraints. This project compares three approaches in a simulated environment and evaluates their advantages and limitations.

## 3. Objectives

- Develop a grid-based room simulator.
- Implement Sweep, Spiral + BFS, and Random Bounce algorithms.
- Evaluate cleaning coverage and repeated coverage.
- Compare algorithms using movement, turns, path length, and uncleaned cells.
- Test the algorithms across five room layouts.
- Implement battery monitoring and automatic return-to-dock behaviour.
- Recommend suitable strategies for different room types.

## 4. System Configuration

- Programming language: Python
- Libraries: NumPy and Matplotlib
- Room dimensions: 40 × 25 grid cells
- Cleaning radius: 2 grid cells
- Number of layouts: 5
- Battery capacity: 300 units
- Movement cost: 1.0 unit per grid move
- Turn cost: 0.2 units per turn
- Charging rate: 10 units per simulated time step
- Battery reserve: 30 units
- Charging dock: (2, 2)

The room contains outer walls and furniture obstacles. Free floor cells are tracked separately from obstacles and cleaned cells.

## 5. Algorithms

### 5.1 Sweep Strategy

The Sweep algorithm follows systematic back-and-forth passes across the room. It is easy to understand and works well in open rooms with regular geometry.

Advantages:
- Systematic coverage pattern.
- Easy to implement and visualise.
- Suitable for open and rectangular spaces.

Limitations:
- Obstacles may interrupt straight passes.
- Extra movement may be required around furniture.
- Difficult room geometries may result in incomplete coverage.

### 5.2 Spiral + BFS Strategy

The Spiral strategy follows a spiral-style path. Breadth-First Search (BFS) is used to find a route toward reachable positions where additional floor can be cleaned.

Advantages:
- Combines structured movement with pathfinding.
- Can navigate around static obstacles.
- Achieved strong coverage in the tested layouts.

Limitations:
- May require extra movement when obstacles interrupt the spiral.
- Complete coverage is not guaranteed for every room configuration.

### 5.3 Random Bounce Strategy

Random Bounce changes direction when it encounters an obstacle. It provides a simple reactive movement strategy without requiring a complete systematic cleaning path.

Advantages:
- Simple implementation.
- Reactive obstacle handling.
- Useful as a baseline for comparison.

Limitations:
- Frequently revisits already-cleaned regions.
- May leave large areas uncleaned.
- Less reliable when complete coverage is required.

## 6. D6: Metrics Comparison

Room size: 40 × 25 grid cells  
Layout: 1  
Free floor cells: 784  
Maximum planned positions: 737  
Random seed: 42

| Metric | Sweep | Spiral + BFS | Random Bounce |
|---|---:|---:|---:|
| Steps | 737 | 737 | 737 |
| Coverage | 87.88% | 100.00% | 50.38% |
| Repeat coverage | 91.91% | 90.52% | 94.15% |
| Turns | 92 | 106 | 25 |
| Path length | 736 | 736 | 736 |
| Estimated battery use | 754.4 | 757.2 | 741.0 |
| Uncleaned cells | 95 | 0 | 389 |

### Analysis

Spiral + BFS achieved the highest coverage in this comparison, cleaning all 784 free floor cells. Sweep achieved 87.88% coverage and left 95 cells uncleaned. Random Bounce achieved 50.38% coverage and left 389 cells uncleaned.

Random Bounce made fewer turns in this run, but its low coverage demonstrates that fewer turns do not necessarily mean better cleaning performance.

The battery figures are simulated estimates based on movement and turn costs. They are not measurements from a physical robot.

## 7. Standalone Algorithm Results

The individual D3, D4, and D5 simulations produced the following results.

| Algorithm | Movement steps/positions | Cleaned cells | Coverage | Uncleaned cells |
|---|---:|---:|---:|---:|
| D3 Sweep | 964 | 784 | 100.00% | 0 |
| D4 Spiral | 737 | 784 | 100.00% | 0 |
| D5 Random Bounce | 737 | 395 | 50.38% | 389 |

The standalone Sweep simulation achieved 100% coverage using 964 movement positions. However, the D6 comparison evaluated Sweep with a limit of 737 planned positions, producing 87.88% coverage.

These results use different movement budgets or evaluation procedures and should not be treated as identical experiments.

## 8. D7: Five-Layout Benchmark

The D7 benchmark uses five room layouts, a maximum of 4,000 steps, and 10 Random Bounce repetitions per layout.

| Layout | Free cells | Sweep coverage | Spiral + BFS coverage | Random Bounce average coverage |
|---|---:|---:|---:|---:|
| 1 | 784 | 100.00% | 100.00% | 47.39% |
| 2 | 736 | 100.00% | 100.00% | 50.52% |
| 3 | 811 | 100.00% | 100.00% | 44.78% |
| 4 | 776 | 100.00% | 100.00% | 47.65% |
| 5 | 706 | 83.43% | 83.43% | 49.94% |

### Analysis

Sweep and Spiral + BFS achieved 100% coverage in layouts 1–4. In layout 5, both achieved 83.43% coverage and left 117 cells uncleaned.

Random Bounce achieved average coverage between 44.78% and 50.52% across the five layouts. This shows that the current Random Bounce implementation is less suitable when complete coverage is important.

The incomplete results for layout 5 also show why the final number of uncleaned cells must be checked after every simulation.

## 9. D8: Battery-Aware Cleaning Robot

The battery-aware robot monitors its remaining battery and uses BFS to navigate to the charging dock when required. After charging, it resumes cleaning. Once cleaning is complete, it returns to the dock.

### Results

| Measure | Observed result |
|---|---|
| Room dimensions | 40 × 25 |
| Cleaning radius | 2 |
| Maximum battery | 300.0 units |
| Total free floor cells | 784 |
| Cleaned floor cells | 784 |
| Uncleaned floor cells | 0 |
| Coverage | 100.00% |
| Returned to dock | Yes |
| Final robot position | (2, 2) |
| Movement steps | 466 |
| Turns | 84 |
| Charging cycles | 1 |
| Final battery | 89.2 units |
| Simulated elapsed time | 494 |

### Analysis

The D8 simulation achieved complete coverage and returned the robot to the charging dock at coordinate (2, 2). The robot completed one charging cycle and finished with 89.2 battery units.

These values come from a simulated battery model. They do not represent measured electrical consumption or real-world battery performance.

## 10. Which Strategy Suits Which Room?

### Open and rectangular rooms — Sweep

Sweep is suitable for open spaces with few obstacles and regular geometry. Its systematic back-and-forth movement makes the coverage pattern easy to understand and verify.

### Rooms with multiple static obstacles — Spiral + BFS

Spiral + BFS is a strong candidate for rooms containing furniture and obstacles. BFS helps the robot find routes toward reachable uncleaned areas. In the current benchmark, it achieved complete coverage in four layouts.

### Simple environments where implementation simplicity matters — Random Bounce

Random Bounce is easy to implement and provides reactive movement. However, the experimental results show substantial repeated coverage and many uncleaned cells. It is not recommended when complete coverage is essential.

### Rooms with limited battery — Battery-aware navigation

A battery-aware planner is suitable when the robot must return to a charging dock, recharge, and resume cleaning. It should be combined with a coverage strategy and a safe return-distance estimate.

### Complex rooms with narrow or difficult passages — Coverage planning with reachability checks

The incomplete coverage in layout 5 demonstrates that planners must verify whether any floor remains uncleaned. Future improvements should investigate room partitioning, unreachable areas, and recovery routes.

### Overall recommendation

Based on the current simulations, Spiral + BFS is a strong default for rooms with obstacles, Sweep is a good option for regular open rooms, and Random Bounce is best treated as a simple baseline. Battery-aware navigation should be added when automatic recharging and safe docking are required.

These recommendations are based on the tested layouts and are not guarantees for all room geometries.

## 11. Recent Research Paper — CVPR 2025

### Paper title

“RoboSense: Large-scale Dataset and Benchmark for Egocentric Robot Perception and Navigation in Crowded and Unstructured Environments”

Authors: Haisheng Su, Feixiang Song, Cong Ma, Wei Wu, and Junchi Yan.

Conference: IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR), 2025.

Official paper link:

https://openaccess.thecvf.com/content/CVPR2025/html/Su_RoboSense_Large-scale_Dataset_and_Benchmark_for_Egocentric_Robot_Perception_and_Navigation_in_Crowded_and_Unstructured_Environments_CVPR_2025_paper.html

PDF link:

https://openaccess.thecvf.com/content/CVPR2025/papers/Su_RoboSense_Large-scale_Dataset_and_Benchmark_for_Egocentric_Robot_Perception_and_Navigation_in_Crowded_and_Unstructured_Environments_CVPR_2025_paper.pdf

### Research discussion

RoboSense is a dataset and benchmark designed to support robot perception and navigation in crowded and unstructured environments. Such environments present challenges because robots must perceive their surroundings, identify obstacles, and navigate safely.

The current cleaning robot project assumes a known grid map containing static furniture and walls. This makes it possible to compare coverage algorithms under controlled conditions, but it does not fully represent a real environment where obstacles may move or sensor readings may be imperfect.

The RoboSense research is relevant as background for future extensions to this project. A camera or range sensor could be used to detect obstacles and update the room map while the robot is moving. The updated map could then be used by Sweep or Spiral + BFS to plan safer coverage paths. Battery-aware navigation could also be combined with this approach so that the robot returns to its charging dock when required.

The paper does not directly evaluate the three cleaning strategies implemented in this project. Instead, it provides research context for extending the simulator toward perception-driven navigation in more realistic environments.

## 12. Limitations

- The project uses a grid-based simulated environment rather than a physical robot.
- Furniture and obstacles remain static during each simulation.
- The circular cleaning footprint is an idealised model.
- Battery use is estimated using assumed movement and turn costs.
- Coverage depends on the room layout and movement budget.
- Layout 5 shows that the current deterministic planners do not achieve complete coverage in every tested environment.
- Real-world sensor noise, wheel slip, and dynamic obstacles are not modelled.

## 13. Future Scope

- Test the algorithms in a physical cleaning robot.
- Add camera or range-sensor obstacle detection.
- Support dynamic room maps.
- Improve recovery planning for uncleaned regions.
- Compare actual battery consumption with the simulated estimates.
- Investigate room partitioning and more advanced coverage path planning.
- Extend the simulator to include moving obstacles and uncertain sensor readings.

## 14. Conclusion

This project implemented and evaluated Sweep, Spiral + BFS, and Random Bounce for grid-based cleaning robot coverage. The D6 results showed that Spiral + BFS achieved 100% coverage under the 737-position comparison budget, while Sweep achieved 87.88% and Random Bounce achieved 50.38%.

The D7 benchmark showed that Sweep and Spiral + BFS achieved complete coverage in layouts 1–4, but both reached only 83.43% in layout 5. Random Bounce consistently produced lower average coverage.

The D8 battery-aware simulation cleaned all 784 free floor cells, completed one charging cycle, and returned to the charging dock. Overall, the results support systematic coverage planning with BFS fallback and battery-aware docking, while highlighting the importance of verifying uncleaned areas for difficult room layouts.

## References

[1] H. Su, F. Song, C. Ma, W. Wu, and J. Yan, “RoboSense: Large-scale Dataset and Benchmark for Egocentric Robot Perception and Navigation in Crowded and Unstructured Environments,” CVPR, 2025.

Available: https://openaccess.thecvf.com/content/CVPR2025/html/Su_RoboSense_Large-scale_Dataset_and_Benchmark_for_Egocentric_Robot_Perception_and_Navigation_in_Crowded_and_Unstructured_Environments_CVPR_2025_paper.html

[2] P34 Cleaning Robot Coverage project simulation outputs: D3 Sweep, D4 Spiral, D5 Random Bounce, D6 Metrics Comparison, D7 Five-Layout Benchmark, and D8 Battery-Aware Robot, 2026.