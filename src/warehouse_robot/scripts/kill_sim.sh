#!/usr/bin/env bash
# kill_sim.sh — forcibly terminate every process involved in a Gazebo/ROS
# simulation session for this project. Run this whenever `ros2 launch` has
# left zombies behind (symptoms: duplicate /clock publishers, "Detected jump
# back in time" RViz spam, multiple nodes with the same name in
# `ros2 node list`).

set -u

patterns=(
  'ros2 launch warehouse_robot'
  'gz sim'
  'ruby.*gz'
  'parameter_bridge'
  'robot_state_publisher'
  'rviz2'
  'static_transform_publisher'
  'teleop_twist_keyboard'
  'slam_toolbox'
  'nav2_amcl'
  'nav2_map_server'
  'lifecycle_manager'
)

echo "[kill_sim] sending SIGKILL to sim processes..."
for p in "${patterns[@]}"; do
  pkill -9 -f "$p" 2>/dev/null || true
done

sleep 2

echo "[kill_sim] survivor check:"
if pgrep -fa 'gz sim|ruby.*gz|parameter_bridge|robot_state_publisher|rviz2|check1.launch|slam.launch|localization.launch|static_transform_publisher|teleop_twist_keyboard|slam_toolbox|nav2_amcl|nav2_map_server|lifecycle_manager' 2>/dev/null | grep -v -E "pgrep|kill_sim\\.sh"; then
  echo "[kill_sim] WARNING: some processes survived. Try:  kill -9 <PID>  manually."
  exit 1
else
  echo "[kill_sim] all clean."
fi
