# simulation-platform-for-mycobot-280

Simulation platform for the `myCobot 280 M5` with a fixed RGB-D camera, Gazebo Sim, ROS 2 Humble, and a first vision-guided pick-and-place pipeline using MoveIt 2.

This repository is published as `simulation-platform-for-mycobot-280`, but the internal ROS 2 package name remains `mycobot_realsense_pick_sim`.

## Overview

This project provides a self-contained simulation cell with:

- a `myCobot 280 M5` robot model with adaptive gripper
- a fixed RGB-D camera with RealSense-style topics
- a simplified pick area and place area
- colored cube objects for robust first-pass perception
- Gazebo Sim world and ROS 2 bridges
- MoveIt 2 planning for manipulation
- OpenCV-based object detection
- manual pose control and slider-based control modes

The recommended way to run the project is through Docker. That avoids having to install the full ROS 2, Gazebo Sim, MoveIt 2, and Elephant Robotics stack directly on the host.

## Repository Contents

- `docker/Dockerfile`: full simulation image
- `docker/docker-compose.yml`: local development container setup
- `docker/entrypoint.sh`: container ROS environment bootstrap
- `run.sh`: helper script for build and launch commands
- `launch/`: ROS 2 launch files
- `config/`: robot, controller, MoveIt, and simulation configuration
- `worlds/`: Gazebo Sim world description
- `mycobot_realsense_pick_sim/`: Python nodes

## Recommended Setup

Use:

- Ubuntu Linux
- Docker Engine
- Docker Compose v2
- an X11-capable desktop session for Gazebo and RViz windows

The repository branch intended for this project is `humble`.

## Quick Start

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

Start the full simulation bringup:

```bash
./run.sh sim-bringup rviz:=false
```

If you want a shell inside the container:

```bash
./run.sh shell
```

## Host Requirements

You do not need ROS 2 installed on the host if you use Docker, but you do need the following host-side tools:

- Docker Engine
- Docker Compose v2
- `xhost`
- a running graphical session that exposes `/tmp/.X11-unix`

Check whether Docker is available:

```bash
docker --version
docker compose version
```

Check whether `xhost` is available:

```bash
xhost
```

If `xhost` is missing on Ubuntu:

```bash
sudo apt update
sudo apt install -y x11-xserver-utils
```

## Installing Docker on Ubuntu

If Docker is not installed yet, install Docker Engine and the Compose plugin using the method you prefer.

Common Ubuntu package route:

```bash
sudo apt update
sudo apt install -y docker.io docker-compose-plugin
sudo usermod -aG docker "$USER"
newgrp docker
```

After installation, verify:

```bash
docker run --rm hello-world
docker compose version
```

If your machine uses another Docker installation method, that is also fine as long as `docker` and `docker compose` work from the terminal.

## What the Docker Image Includes

The Docker image is based on `osrf/ros:humble-desktop` and installs:

- ROS 2 Humble desktop tools
- `ros_gz`
- `gz_ros2_control`
- MoveIt 2
- `cv_bridge`
- `image_geometry`
- `image_view`
- `joint_state_broadcaster`
- `joint_trajectory_controller`
- `joint_state_publisher_gui`
- `xacro`
- OpenCV
- `colcon`
- `rosdep`
- X11 GUI support packages

It also clones the Elephant Robotics ROS 2 repository and builds:

- `mycobot_description`
- `mycobot_280`

That means the container carries the external robot packages required by this simulation.

## First-Time Setup

From the repository root:

```bash
cd simulation-platform-for-mycobot-280
```

Allow X11 access for Docker:

```bash
xhost +local:docker
```

Build the image:

```bash
./run.sh build-image
```

This first build may take several minutes because it:

- downloads the ROS base image
- installs simulation and planning dependencies
- clones Elephant Robotics packages
- builds the external robot workspace in `/opt/elephant_ws`

Then build this repository workspace inside the container:

```bash
./run.sh build-ws
```

## Daily Usage

### 1. Open a shell in the container

```bash
./run.sh shell
```

Inside the container, the ROS environment is sourced automatically by `docker/entrypoint.sh`.

### 2. Build the workspace again after code changes

```bash
./run.sh build-ws
```

### 3. Launch only the world

```bash
./run.sh sim-world
```

### 4. Launch Gazebo, robot, camera, bridges, and controllers

```bash
./run.sh sim-bringup rviz:=false
```

### 5. Launch manual pose control

```bash
./run.sh topic-pose
```

### 6. Launch pick and place

```bash
./run.sh pick-place
```

### 7. Launch slider-based manual control

```bash
./run.sh slider
```

## Helper Script Reference

The repository ships with `run.sh` to keep the workflow simple.

Available commands:

```bash
./run.sh build-image
./run.sh build-ws
./run.sh shell
./run.sh sim-world
./run.sh sim-bringup rviz:=false
./run.sh topic-pose
./run.sh pick-place
./run.sh slider
```

What each command does:

- `build-image`: builds the Docker image defined in `docker/Dockerfile`
- `build-ws`: runs `colcon build --symlink-install` inside the container
- `shell`: opens an interactive shell in the configured container
- `sim-world`: launches the simulation world only
- `sim-bringup`: launches the main robot + camera + bridge + controller stack
- `topic-pose`: launches the pose-command workflow
- `pick-place`: launches the perception + manipulation flow
- `slider`: launches the slider control workflow

## Running Without Docker

Docker is recommended. If you decide to run natively, you need a working ROS 2 Humble environment plus the Elephant Robotics packages in the same parent workspace.

Core dependencies:

```bash
sudo apt update
sudo apt install -y \
  ros-humble-ros-gz \
  ros-humble-gz-ros2-control \
  ros-humble-moveit \
  ros-humble-cv-bridge \
  ros-humble-image-geometry \
  ros-humble-image-view \
  ros-humble-joint-state-broadcaster \
  ros-humble-joint-state-publisher-gui \
  ros-humble-joint-trajectory-controller \
  ros-humble-controller-manager \
  ros-humble-ros2controlcli \
  ros-humble-tf2-geometry-msgs \
  ros-humble-xacro \
  python3-opencv \
  python3-colcon-common-extensions
```

External Elephant Robotics packages required:

- `mycobot_description`
- `mycobot_280`

Build locally:

```bash
source /opt/ros/humble/setup.bash
colcon build
source install/setup.bash
```

## Main ROS 2 Launches

World only:

```bash
ros2 launch mycobot_realsense_pick_sim sim_world.launch.py
```

Gazebo, robot, camera, bridges, and controllers:

```bash
ros2 launch mycobot_realsense_pick_sim sim_bringup.launch.py rviz:=false
```

Perception only:

```bash
ros2 launch mycobot_realsense_pick_sim vision.launch.py
```

Perception plus MoveIt 2 executor:

```bash
ros2 launch mycobot_realsense_pick_sim pick_place.launch.py
```

Full demo:

```bash
ros2 launch mycobot_realsense_pick_sim demo_full.launch.py
```

Slider-based manual control:

```bash
ros2 launch mycobot_realsense_pick_sim slider_control_sim.launch.py
```

Pose-topic control:

```bash
ros2 launch mycobot_realsense_pick_sim topic_pose_control.launch.py
```

## Pose Control Usage

The `topic_pose_commander` node subscribes to `geometry_msgs/msg/PoseStamped` on `/arm_goal_pose` and uses IK plus MoveIt 2 to move the end-effector to the requested pose.

Start the environment:

```bash
./run.sh topic-pose
```

Then publish a test pose:

```bash
ros2 topic pub --once /arm_goal_pose geometry_msgs/msg/PoseStamped "{header: {frame_id: 'world'}, pose: {position: {x: 0.18, y: 0.00, z: 0.62}, orientation: {x: 1.0, y: 0.0, z: 0.0, w: 0.0}}}"
```

If you want to send a pose without manually setting orientation, publish a zero quaternion and the node will apply a default vertical grasp orientation:

```bash
ros2 topic pub --once /arm_goal_pose geometry_msgs/msg/PoseStamped "{header: {frame_id: 'world'}, pose: {position: {x: 0.20, y: -0.08, z: 0.58}, orientation: {x: 0.0, y: 0.0, z: 0.0, w: 0.0}}}"
```

## Slider Control Usage

To mimic the Elephant Robotics slider control experience, this project includes a simulation adapter based on the `mycobot_280` package.

Run:

```bash
./run.sh slider
```

This launch brings up:

- Gazebo Sim
- the robot and camera
- RViz
- `joint_state_publisher_gui`
- `mycobot_280/slider_control_adaptive_gripper_sim`

Control flow:

- the GUI publishes to `/slider_joint_states`
- `slider_control_adaptive_gripper_sim` converts slider states into trajectories
- `/arm_controller/follow_joint_trajectory` and `/gripper_trajectory_controller/follow_joint_trajectory` execute the motion

## Main Topics

- `/camera/color/image_raw`
- `/camera/color/camera_info`
- `/camera/depth/image_rect_raw`
- `/camera/depth/camera_info`
- `/joint_states`
- `/detected_objects/poses`
- `/detected_objects/json`
- `/arm_goal_pose`

## Expected TF Frames

- `world`
- `g_base`
- robot links from `joint1` to `joint6_flange`
- `gripper_base`
- `camera_link`
- `camera_color_optical_frame`
- `camera_depth_optical_frame`

## Quick Validation

Check camera topics:

```bash
ros2 topic list | grep camera
ros2 topic info /camera/color/image_raw
ros2 topic info /camera/depth/image_rect_raw
```

Check detection output:

```bash
ros2 topic echo /detected_objects/json --once
```

Check controllers:

```bash
ros2 control list_controller_types
ros2 param list /controller_manager
```

## Troubleshooting

### Gazebo or RViz window does not open

Check that X11 access was enabled:

```bash
xhost +local:docker
```

Check that `DISPLAY` is exported:

```bash
echo $DISPLAY
```

Check that the X11 socket exists:

```bash
ls /tmp/.X11-unix
```

### You are on Wayland

This setup is written for X11. On Wayland-only sessions, GUI forwarding may fail unless XWayland is active. If windows do not appear, start an X11-compatible session or adapt the compose setup for your desktop environment.

### Docker permission denied

Add your user to the Docker group and start a new shell:

```bash
sudo usermod -aG docker "$USER"
newgrp docker
```

### The first image build is slow

That is expected. The image installs a full ROS 2 simulation stack and compiles external robot packages. Later rebuilds should be faster unless the Docker cache is invalidated.

### Simulation is slow

If no GPU acceleration is available inside the container, Gazebo and RViz may fall back to software rendering. The simulation can still run, but with lower performance.

You can also try:

```bash
export LIBGL_ALWAYS_SOFTWARE=1
./run.sh sim-bringup rviz:=false
```

### You want to use a real camera or a real robot later

You will likely need to extend `docker/docker-compose.yml` with:

- `devices:`
- USB access rules
- additional ROS interfaces

## Perception Strategy

- pragmatic HSV color segmentation
- contour extraction with simple square filtering
- depth lookup at the object centroid to recover 3D position
- transform to `world` using `tf2`

The table and base remain white, while the blocks are intentionally colored to keep the first version of the pipeline robust and easy to validate. The perception node can later be replaced by a classical detector, segmentation model, or YOLO-based pipeline.

## Manipulation Strategy

- MoveIt 2 for IK and planning
- gripper control via `FollowJointTrajectory`
- simulated attach and detach via `ros_gz_interfaces/srv/SetEntityPose`

## Known Limitations

- the RGB-D sensor is fixed in the environment, not mounted on the wrist
- perception is color-based and not robust to strong lighting variation
- object attachment is simulated by controlled teleportation, not physical contact dynamics
- native host execution still depends on external Elephant Robotics packages being present in the same ROS 2 workspace

## GitHub and Container Publishing

The repository includes:

- `.gitignore` for ROS build artifacts and Python caches
- `.github/workflows/docker-publish.yml` for GitHub Actions image publishing

The workflow:

- validates Docker builds on pull requests to `humble`
- publishes the image on pushes to `humble`
- publishes versioned images for `v*` tags

Expected image paths:

```bash
ghcr.io/igornunnes/simulation-platform-for-mycobot-280:latest
ghcr.io/igornunnes/simulation-platform-for-mycobot-280:humble
ghcr.io/igornunnes/simulation-platform-for-mycobot-280:sha-<commit>
```

Pull the published image:

```bash
docker pull ghcr.io/igornunnes/simulation-platform-for-mycobot-280:latest
```
