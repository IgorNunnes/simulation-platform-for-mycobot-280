#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_FILE="${ROOT_DIR}/docker/docker-compose.yml"
SERVICE_NAME="sim"

export DOCKER_UID="${DOCKER_UID:-$(id -u)}"
export DOCKER_GID="${DOCKER_GID:-$(id -g)}"
export DOCKER_USER="${DOCKER_USER:-ros}"
export ROS_DISTRO="${ROS_DISTRO:-humble}"
export ELEPHANT_BRANCH="${ELEPHANT_BRANCH:-humble}"
export DISPLAY="${DISPLAY:-:0}"
export XAUTHORITY_PATH="${XAUTHORITY_PATH:-${XAUTHORITY:-${HOME}/.Xauthority}}"
export XAUTHORITY_CONTAINER="${XAUTHORITY_CONTAINER:-/tmp/.Xauthority}"

compose() {
  docker compose -f "${COMPOSE_FILE}" "$@"
}

quoted_args() {
  local quoted=""
  if [ "$#" -gt 0 ]; then
    printf -v quoted '%q ' "$@"
  fi
  printf '%s' "${quoted}"
}

run_container() {
  compose run --rm "${SERVICE_NAME}" "$@"
}

ensure_xhost() {
  if command -v xhost >/dev/null 2>&1; then
    xhost +local:docker >/dev/null 2>&1 || true
  fi
}

build_workspace() {
  run_container bash -lc "cd /workspaces/mycobot_realsense_pick_sim && colcon build --symlink-install"
}

run_launch() {
  local launch_file="$1"
  shift || true
  local extra_args
  extra_args="$(quoted_args "$@")"
  run_container bash -lc "cd /workspaces/mycobot_realsense_pick_sim && \
    if [ ! -f install/setup.bash ]; then colcon build --symlink-install; fi && \
    source install/setup.bash && \
    ros2 launch mycobot_realsense_pick_sim ${launch_file} ${extra_args}"
}

usage() {
  cat <<'EOF'
Uso:
  ./run.sh build-image
  ./run.sh build-ws
  ./run.sh shell
  ./run.sh sim-world [args...]
  ./run.sh sim-bringup [args...]
  ./run.sh topic-pose [args...]
  ./run.sh pick-place [args...]
  ./run.sh slider [args...]

Exemplos:
  ./run.sh build-image
  ./run.sh build-ws
  ./run.sh sim-world
  ./run.sh sim-bringup rviz:=false
  ./run.sh topic-pose
EOF
}

cmd="${1:-help}"
shift || true

case "${cmd}" in
  build-image)
    compose build
    ;;
  build-ws)
    ensure_xhost
    build_workspace
    ;;
  shell)
    ensure_xhost
    run_container bash
    ;;
  sim-world)
    ensure_xhost
    run_launch sim_world.launch.py "$@"
    ;;
  sim-bringup)
    ensure_xhost
    run_launch sim_bringup.launch.py "$@"
    ;;
  topic-pose)
    ensure_xhost
    run_launch topic_pose_control.launch.py "$@"
    ;;
  pick-place)
    ensure_xhost
    run_launch pick_place.launch.py "$@"
    ;;
  slider)
    ensure_xhost
    run_launch slider_control_sim.launch.py "$@"
    ;;
  help|-h|--help)
    usage
    ;;
  *)
    echo "Comando desconhecido: ${cmd}" >&2
    usage
    exit 1
    ;;
esac
