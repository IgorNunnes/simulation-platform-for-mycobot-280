# Manual for Use

This document is the main guided reference for reproducing and using the current working workflow in this repository.

At the moment, the documented and supported control path is:

- Docker on the host
- standard ROS 2 commands inside the container
- `ros2 launch mycobot_realsense_pick_sim topic_joint_control.launch.py`
- joint commands sent on `/arm_joint_goal`

If the project behavior changes, this file should be updated together with the code.

## 1. What This Repository Provides

This project builds a reproducible simulation cell for the `myCobot 280 M5` with:

- Gazebo Sim
- ROS 2 Humble
- a fixed RGB-D camera
- a simulated adaptive gripper
- ros2_control-based joint actuation
- a topic-based joint commander

The repository still contains other nodes and experiments, but the workflow documented here is intentionally focused on the joint-topic path because it is the most stable one right now.

## 2. Canonical Workflow

The canonical day-to-day workflow is:

1. Prepare Docker and X11 on the host.
2. Open a shell inside the container.
3. Build the workspace.
4. Launch the joint-control workflow.
5. Open extra container terminals as needed.
6. Publish joint commands with `ros2 topic pub`.

In practice, that means:

```bash
xhost +local:docker
export DOCKER_UID="$(id -u)"
export DOCKER_GID="$(id -g)"
export DOCKER_USER="${USER}"
export ROS_DISTRO=humble
export ELEPHANT_BRANCH=humble
export DISPLAY="${DISPLAY:-:0}"
export XAUTHORITY_PATH="${XAUTHORITY:-$HOME/.Xauthority}"
export XAUTHORITY_CONTAINER=/tmp/.Xauthority
docker compose -f docker/docker-compose.yml build
docker compose -f docker/docker-compose.yml run --rm sim bash
```

Then inside the container:

```bash
cd /workspaces/mycobot_realsense_pick_sim
colcon build --symlink-install
source install/setup.bash
ros2 launch mycobot_realsense_pick_sim topic_joint_control.launch.py
```

From that point on, the preferred way to work is to keep using normal ROS 2 commands inside the container.

The `run.sh` helper still exists for compatibility, but it is not the canonical documented workflow and it should not receive new wrapper commands.

## 3. Docker and Environment Commands

### `xhost +local:docker`

Allows local Docker containers to use the host X server.

Use it when:

- you want Gazebo windows to open from inside the container
- you are starting a new desktop session

### Exporting the Docker Compose Variables

The compose file expects the user, display, and Xauthority values to be available from the host shell.

Recommended exports:

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

### `docker compose -f docker/docker-compose.yml build`

Builds the Docker image used by the project.

Use it when:

- you are setting up the repository for the first time
- the `docker/Dockerfile` changed
- the base ROS or dependency stack changed

### `docker compose -f docker/docker-compose.yml run --rm sim bash`

Opens an interactive shell inside the configured container.

Use it when:

- you want to run `ros2` commands manually
- you want to inspect topics, nodes, services, or actions
- you want to debug inside the container

## 4. Using Standard ROS 2 Commands Inside the Container

This section explains the preferred way to use this repository: open the Docker container and use normal `ros2` commands directly.

Important:

- the standard `ros2` commands in this project are expected to run inside the Docker container
- if you run `ros2 launch`, `ros2 run`, or `ros2 topic` directly on the host, they may fail unless you separately installed the full ROS 2 environment on the host
- each new terminal that will use ROS 2 commands should start with `docker compose -f docker/docker-compose.yml run --rm sim bash`
- from this point forward, the documented workflow for this repository is Docker plus raw `ros2` commands, not new `run.sh` wrappers

### 4.1 Enter the Container Shell

From the repository root on the host:

```bash
docker compose -f docker/docker-compose.yml run --rm sim bash
```

This opens a shell inside the configured Docker container.

The container entrypoint already sources:

- `/opt/ros/${ROS_DISTRO}/setup.bash`
- the Elephant workspace, if available
- this repository workspace, if `install/setup.bash` already exists

### 4.2 Build and Source the Workspace

Inside the container:

```bash
cd /workspaces/mycobot_realsense_pick_sim
colcon build --symlink-install
source install/setup.bash
```

Even if the shell usually starts with the environment sourced, it is a good habit to run:

```bash
source install/setup.bash
```

after a fresh build or before running manual ROS 2 commands in a new terminal.

### 4.3 Launch the Working Workflow

The only documented launcher you should rely on right now is:

```bash
ros2 launch mycobot_realsense_pick_sim topic_joint_control.launch.py
```

This launch is self-contained. It starts:

- Gazebo Sim with the project world
- the robot model
- `robot_state_publisher`
- the Gazebo / ROS bridges
- the camera relay
- the TF publishers for the camera frames
- the joint state broadcaster
- the arm trajectory controller
- the gripper trajectory controller
- the startup hold commander
- the `topic_joint_commander` node

Use this launch when:

- you want the simulation to start in the currently supported way
- you want the arm to accept joint commands
- you want the camera topics to be present
- you want the simplest reproducible workflow in this branch

After launching, wait until the startup sequence finishes before sending the first motion command.

The most useful signs in the launch terminal are:

- `Configured and activated arm_controller`
- `Configured and activated gripper_trajectory_controller`
- `Listening for joint goals on /arm_joint_goal`
- `Sent startup hold trajectory to arm and gripper`

If you publish a joint goal too early, the startup sequence may still be activating controllers or sending the initial hold command.

You can also enable the ArUco detector directly in the same launcher:

```bash
ros2 launch mycobot_realsense_pick_sim topic_joint_control.launch.py aruco_detector:=true
```

### 4.4 Open More Than One Terminal

For most ROS 2 workflows, you should use more than one terminal.

Typical pattern:

1. Terminal 1: launch `topic_joint_control.launch.py`
2. Terminal 2: publish commands with `ros2 topic pub`
3. Terminal 3: inspect state with `ros2 topic echo`, `ros2 node list`, or `ros2 action list`

For each extra terminal, open a new shell in the container:

```bash
docker compose -f docker/docker-compose.yml run --rm sim bash
```

Then inside it:

```bash
cd /workspaces/mycobot_realsense_pick_sim
source install/setup.bash
```

This avoids the common mistake of publishing from a terminal that is not in the correct ROS environment.

### 4.5 Inspect the Running ROS Graph

These commands are useful when something does not behave as expected.

List nodes:

```bash
ros2 node list
```

List topics:

```bash
ros2 topic list
```

Inspect one topic:

```bash
ros2 topic info /arm_joint_goal
ros2 topic info /joint_states
ros2 topic info /camera/color/image_raw
```

Echo one message:

```bash
ros2 topic echo --once /joint_states
```

List actions:

```bash
ros2 action list
```

List services:

```bash
ros2 service list
```

### 4.6 ArUco Pose Estimation

The current perception path uses single ArUco markers because it is the safest fit for this branch:

- it is deterministic
- it does not depend on color thresholds or learned models
- it gives a direct pose estimate from the RGB image plus camera intrinsics
- it already matches the current simulated blocks one-to-one

For future real-hardware calibration work, a ChArUco board is still a good complementary tool, but the object-detection path documented here is based on ArUco markers on the pickable objects.

The repository now includes a dedicated ArUco detector node:

```bash
ros2 run mycobot_realsense_pick_sim aruco_object_detector
```

In the supported workflow, the easiest way to use it is through the main launcher:

```bash
ros2 launch mycobot_realsense_pick_sim topic_joint_control.launch.py aruco_detector:=true
```

This detector uses:

- `/camera/color/image_raw`
- `/camera/color/camera_info`
- the TF from `camera_color_optical_frame` to `world`

It publishes:

- `/detected_objects/poses`
- `/detected_objects/markers`
- `/detected_objects/json`
- `/detected_objects/debug_image`

The detector is configured for the current simulation world with these default marker mappings:

- marker `0` -> `red_block`
- marker `1` -> `green_block`
- marker `2` -> `blue_block`
- marker `3` -> `yellow_block`
- marker `4` -> `orange_block`

The simulated blocks now include ArUco markers on their top faces so the detector can estimate their pose from the RGB camera image.

Useful checks:

```bash
ros2 topic echo --once /detected_objects/json
ros2 topic echo --once /detected_objects/poses
ros2 topic info /detected_objects/debug_image
```

If you want to visualize the debug image:

```bash
ros2 run image_view image_view --ros-args -r image:=/detected_objects/debug_image
```

## 5. Joint-Space Control

The `topic_joint_commander` node accepts `sensor_msgs/msg/JointState` messages on:

- `/arm_joint_goal`

It supports:

- full arm commands
- partial arm updates
- gripper-only commands
- combined arm + gripper commands

If you send a new command while the current one is still executing, the node keeps the latest command queued and executes it next.

### 5.1 Start the Joint Workflow

```bash
ros2 launch mycobot_realsense_pick_sim topic_joint_control.launch.py
```

### 5.2 Send a Full Arm Goal

```bash
ros2 topic pub --once /arm_joint_goal sensor_msgs/msg/JointState "{name: ['joint2_to_joint1', 'joint3_to_joint2', 'joint4_to_joint3', 'joint5_to_joint4', 'joint6_to_joint5', 'joint6output_to_joint6'], position: [0.0, -0.6, 0.9, -0.3, 0.2, 0.0]}"
```

Use this when you want to place all arm joints at a known configuration.

### 5.3 Send a Partial Joint Update

```bash
ros2 topic pub --once /arm_joint_goal sensor_msgs/msg/JointState "{name: ['joint3_to_joint2'], position: [-0.9]}"
```

Use this when you only want to change one joint and keep the others where they are.

### 5.4 Return to the Neutral Home Pose

```bash
ros2 topic pub --once /arm_joint_goal sensor_msgs/msg/JointState "{name: ['joint2_to_joint1', 'joint3_to_joint2', 'joint4_to_joint3', 'joint5_to_joint4', 'joint6_to_joint5', 'joint6output_to_joint6'], position: [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]}"
```

Use this when you want the arm back in the neutral reference pose.

### 5.5 Move Only the Gripper

```bash
ros2 topic pub --once /arm_joint_goal sensor_msgs/msg/JointState "{name: ['gripper_controller'], position: [-0.4]}"
```

Use this when:

- you want to test the gripper alone
- you want to open or close the fingers without moving the arm

### 5.6 Move Arm and Gripper Together

```bash
ros2 topic pub --once /arm_joint_goal sensor_msgs/msg/JointState "{name: ['joint2_to_joint1', 'joint3_to_joint2', 'joint4_to_joint3', 'joint5_to_joint4', 'joint6_to_joint5', 'joint6output_to_joint6', 'gripper_controller'], position: [0.2, -0.8, 1.0, -0.4, 0.1, 0.0, -0.35]}"
```

Use this when you want a combined pose-and-gripper state in one command.

## 6. Step-By-Step Guided Examples

### Example A: Bring Up the Working Simulation

1. Open the container shell.

```bash
docker compose -f docker/docker-compose.yml run --rm sim bash
```

2. Build and source the workspace.

```bash
cd /workspaces/mycobot_realsense_pick_sim
colcon build --symlink-install
source install/setup.bash
```

3. Launch the working workflow.

```bash
ros2 launch mycobot_realsense_pick_sim topic_joint_control.launch.py
```

4. Wait until the launch terminal shows that the controllers are activated and the startup hold has been sent.

5. In another terminal, inspect the main topics.

```bash
docker compose -f docker/docker-compose.yml run --rm sim bash
cd /workspaces/mycobot_realsense_pick_sim
source install/setup.bash
ros2 topic list | grep camera
ros2 topic echo --once /joint_states
```

### Example B: Move the Arm and Return Home

1. Start the working workflow.

```bash
ros2 launch mycobot_realsense_pick_sim topic_joint_control.launch.py
```

2. Wait until the launch terminal shows:

```text
Configured and activated arm_controller
Configured and activated gripper_trajectory_controller
Listening for joint goals on /arm_joint_goal
Sent startup hold trajectory to arm and gripper
```

3. Send a test arm configuration.

```bash
ros2 topic pub --once /arm_joint_goal sensor_msgs/msg/JointState "{name: ['joint2_to_joint1', 'joint3_to_joint2', 'joint4_to_joint3', 'joint5_to_joint4', 'joint6_to_joint5', 'joint6output_to_joint6'], position: [0.0, -0.6, 0.9, -0.3, 0.2, 0.0]}"
```

4. Return to the neutral home pose.

```bash
ros2 topic pub --once /arm_joint_goal sensor_msgs/msg/JointState "{name: ['joint2_to_joint1', 'joint3_to_joint2', 'joint4_to_joint3', 'joint5_to_joint4', 'joint6_to_joint5', 'joint6output_to_joint6'], position: [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]}"
```

## 7. Main Topics

Important topics you are likely to inspect first:

- `/joint_states`
- `/arm_joint_goal`
- `/camera/color/image_raw`
- `/camera/color/camera_info`
- `/camera/depth/image_rect_raw`
- `/camera/depth/camera_info`

## 8. Troubleshooting

### Gazebo Does Not Open

Check X11 access:

```bash
xhost +local:docker
echo $DISPLAY
ls /tmp/.X11-unix
```

### The First Build Is Slow

That is expected. The image installs the full ROS 2 simulation stack and compiles external robot packages.

### The Simulation Is Slow

Software rendering may be active. You can try:

```bash
export LIBGL_ALWAYS_SOFTWARE=1
ros2 launch mycobot_realsense_pick_sim topic_joint_control.launch.py
```

### A Topic Command Does Not Seem To Move the Robot

Check whether the working workflow is actually running:

```bash
ros2 node list
ros2 action list
ros2 topic info /arm_joint_goal
ros2 topic info /joint_states
```

### A New Joint Command Does Not Interrupt the Previous One

The joint commander keeps the latest command queued and runs it next. It does not cancel the current action in the middle.

## 9. What To Update When the Project Evolves

When the working workflow changes, update:

- this manual
- the PR description
- the command examples that users are expected to run

This file should remain the main guided document for anyone trying to reproduce the environment and use the supported joint-control path.
