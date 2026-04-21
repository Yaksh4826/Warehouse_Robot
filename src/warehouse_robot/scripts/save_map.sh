#!/usr/bin/env bash
# =============================================================
# save_map.sh — save the /map currently published by slam_toolbox
# Produces   <outdir>/<name>.pgm  and  <outdir>/<name>.yaml
# Usage:
#   src/warehouse_robot/scripts/save_map.sh                    # defaults
#   src/warehouse_robot/scripts/save_map.sh my_map             # custom name
#   src/warehouse_robot/scripts/save_map.sh my_map /some/dir   # + outdir
# =============================================================
set -euo pipefail

NAME="${1:-warehouse_v1}"
OUTDIR="${2:-$(ros2 pkg prefix warehouse_robot --share 2>/dev/null || echo .)/maps}"

mkdir -p "$OUTDIR"
cd "$OUTDIR"

echo "[save_map] Saving /map as ${OUTDIR}/${NAME}.{pgm,yaml}"

# nav2 map_saver_cli blocks until it has received a /map and written both files.
ros2 run nav2_map_server map_saver_cli \
    -f "$NAME" \
    --ros-args -p save_map_timeout:=10.0 -p use_sim_time:=true

# map_saver_cli writes to CWD, so we are already in OUTDIR.
echo "[save_map] Done:"
ls -la "${OUTDIR}/${NAME}.pgm" "${OUTDIR}/${NAME}.yaml"
