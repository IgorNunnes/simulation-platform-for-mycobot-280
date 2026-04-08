# simulation-platform-for-mycobot-280

Simulation platform for the `myCobot 280 M5` with Gazebo Sim, ROS 2 Humble, MoveIt 2, and a fixed RGB-D camera.

This repository is published as `simulation-platform-for-mycobot-280`, but the internal ROS 2 package name remains `mycobot_realsense_pick_sim`.

## Manual for Use

The detailed guided manual for reproducing the environment and using each workflow lives in:

- [MANUAL_FOR_USE.md](MANUAL_FOR_USE.md)

Use that document for:

- step-by-step environment bringup
- how to use standard `ros2 launch`, `ros2 run`, and `ros2 topic` commands inside the container
- explanation of what each launch does
- joint-space control
- Cartesian pose control
- slider control
- troubleshooting and workflow examples

## Recommended Host Setup

Use:

- Ubuntu Linux
- Docker Engine
- Docker Compose v2
- `xhost`
- an X11-capable desktop session for Gazebo and RViz windows

The recommended branch for this project is `humble`.

## Ubuntu Host Requirements

You do not need ROS 2 installed on the host if you use Docker. You only need:

- Docker Engine
- Docker Compose v2
- `xhost`
- a running graphical session that exposes `/tmp/.X11-unix`

Check the required tools:

```bash
docker --version
docker compose version
xhost
```

If `xhost` is missing on Ubuntu:

```bash
sudo apt update
sudo apt install -y x11-xserver-utils
```

## Install Docker on Ubuntu

If Docker is not installed yet, the simplest Ubuntu route is:

```bash
sudo apt update
sudo apt install -y docker.io docker-compose-plugin
sudo usermod -aG docker "$USER"
newgrp docker
```

Then verify:

```bash
docker run --rm hello-world
docker compose version
```

## First-Time Docker Bringup

Clone the repository:

```bash
git clone -b humble https://github.com/IgorNunnes/simulation-platform-for-mycobot-280.git
cd simulation-platform-for-mycobot-280
```

Allow local Docker containers to use your X server:

```bash
xhost +local:docker
```

Export the Docker variables used by the compose file:

```bash
export DOCKER_UID="$(id -u)"
export DOCKER_GID="$(id -g)"
export DOCKER_USER="${USER}"
export ROS_DISTRO=humble
export ELEPHANT_BRANCH=humble
export DISPLAY="${DISPLAY:-:0}"
export XAUTHORITY_PATH="${XAUTHORITY:-$HOME/.Xauthority}"
export XAUTHORITY_CONTAINER=/tmp/.Xauthority
```

Build the Docker image:

```bash
docker compose -f docker/docker-compose.yml build
```

Open a shell inside the container:

```bash
docker compose -f docker/docker-compose.yml run --rm sim bash
```

Inside the container, build the workspace:

```bash
cd /workspaces/mycobot_realsense_pick_sim
colcon build --symlink-install
source install/setup.bash
```

Then launch the main simulation:

```bash
ros2 launch mycobot_realsense_pick_sim sim_bringup.launch.py rviz:=false
```
