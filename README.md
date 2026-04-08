# Warehouse_Robot
# 🤖 Warehouse Autonomous Robot Project 
### **ROS 2 Jazzy | Gazebo Harmonic**

This repository contains the development of an autonomous warehouse robot. This project is part of our university course, focused on modular robotics and autonomous navigation using the latest ROS 2 distribution.

---

## 👥 Team & Progress Track

| Task | Owner | Status |
| :--- | :--- | :--- |
| **Workspace & Repo Architecture** | Member 1 (Lead) | ✅ Complete |
| **Warehouse Environment Design (SDF)** | Member 2 | ✅ Complete |
| **Robot URDF Modeling** | Member 3 | 🚧 In Progress |
| **Sensor Integration & Bridge** | Member 4 | ✅ Complete |
| **Navigation & Mapping** | Member 5 | 📅 Scheduled |

---

## 🛠️ Project Evolution (Log)

### **Phase 1: Environment & Architecture**

1. **System Setup (Member 1):**
   * Initialized the `warehouse_ws` workspace on **Ubuntu 24.04**.
   * Configured the `warehouse_robot` package using `ament_python`.
   * Resolved **WSL2/ARM** graphics compatibility issues by configuring headless server modes and software rendering overrides to ensure simulation stability.

2. **World Design (Member 2):**
   * Created a **30m x 20m** fully enclosed warehouse world (`warehouse_v1.sdf`).
   * Designed a complex navigation layout including:
     * Full perimeter containment walls for safety.
     * Strategic internal shelving units to create realistic aisles.
     * Static obstacles (crates and pallets) strategically placed to test local avoidance.
   * Validated world coordinates and model placement via `gz model --list`.

3. **Launch & Bridge Integration (Member 1):**
   * Developed `check1.launch.py` to automate the simulation startup and model spawning.
   * Integrated `ros_gz_bridge` to translate Gazebo `LaserScan` data to ROS 2 `/scan` topics.
   * Configured `robot_state_publisher` to manage the robot's Transform (TF) tree for accurate sensor visualization.

---

## 🚀 Getting Started

### **Prerequisites**
* **ROS 2 Jazzy Jalisco**
* **Gazebo Harmonic**
* **ros-jazzy-ros-gz-bridge**

### **Installation**
```bash
# Clone the repository
cd ~/your_workspace/src
git clone <your-repo-link>

# Build the project
cd ..
colcon build --symlink-install
source install/setup.bash
