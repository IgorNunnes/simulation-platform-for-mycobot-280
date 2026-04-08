# simulation-platform-for-mycobot-280

Simulation platform for the `myCobot 280 M5` with Gazebo Sim, ROS 2 Humble, MoveIt 2, and a fixed RGB-D camera.

This repository is published as `simulation-platform-for-mycobot-280`, but the internal ROS 2 package name remains `mycobot_realsense_pick_sim`.

## Manual for Use

The detailed guided manual for reproducing the environment and using each workflow lives in:

- [MANUAL_FOR_USE.md](MANUAL_FOR_USE.md)

Use that document for:

- step-by-step environment bringup
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

Build the Docker image:

```bash
./run.sh build-image
```

Build the ROS 2 workspace inside the container:

```bash
./run.sh build-ws
```

Start the main simulation stack:

```bash
./run.sh sim-bringup rviz:=false
```

If you want a shell inside the container:

```bash
./run.sh shell
```
