#!/usr/bin/env bash
set -e

source "/opt/ros/${ROS_DISTRO}/setup.bash"

if [ -f "/opt/elephant_ws/install/setup.bash" ]; then
  source "/opt/elephant_ws/install/setup.bash"
fi

if [ -f "/workspaces/mycobot_realsense_pick_sim/install/setup.bash" ]; then
  source "/workspaces/mycobot_realsense_pick_sim/install/setup.bash"
fi

exec "$@"
