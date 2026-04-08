# Manual for Use

This document is the guided manual for reproducing, running, and extending the workflows in this repository.

Use it as the main reference for:

- building the workspace
- starting the simulation
- understanding which launch to use
- moving the robot in joint space
- moving the robot in Cartesian space
- using the slider interface
- validating the environment after changes

If the project behavior changes, this file should be updated together with the code.

## 1. What This Repository Provides

This project builds a reproducible simulation cell for the `myCobot 280 M5` with:

- Gazebo Sim
- ROS 2 Humble
- MoveIt 2
- a fixed RGB-D camera
- a simulated adaptive gripper
- basic pick-and-place support
- joint-space and Cartesian control workflows

The recommended way to use the project is with Docker.

## 2. Recommended Workflow

The canonical day-to-day workflow is:

1. Prepare the Docker environment on the host.
2. Open a shell inside the container.
3. Build the workspace after changes.
4. Launch the ROS 2 workflow you want to use.
5. Validate that controllers, robot state, and camera topics are alive.

In practice, that usually means:

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
ros2 launch mycobot_realsense_pick_sim sim_bringup.launch.py rviz:=false
```

From that point on, the preferred way to work is to keep using normal `ros2` commands inside the container.

The `run.sh` helper still exists for compatibility, but it is no longer the canonical documented workflow and it should not receive new wrapper commands.

## 3. Docker and Environment Commands

### `xhost +local:docker`

Allows local Docker containers to use the host X server.

Use it when:

- you want Gazebo or RViz windows to open from inside the container
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

This is the expected starting point for manual ROS 2 usage in this repository.

The container entrypoint already sources:

- `/opt/ros/${ROS_DISTRO}/setup.bash`
- the Elephant workspace, if available
- this repository workspace, if `install/setup.bash` already exists

### 4.2 Rebuild and Source the Workspace

If you changed code, rebuild first:

```bash
cd /workspaces/mycobot_realsense_pick_sim
colcon build --symlink-install
source install/setup.bash
```

Even if the shell usually starts with the environment sourced, it is a good habit to run:

```bash
source install/setup.bash
```

after a fresh build or before running manual `ros2` commands in a new terminal.

Recommended manual workflow for any new terminal:

```bash
docker compose -f docker/docker-compose.yml run --rm sim bash
cd /workspaces/mycobot_realsense_pick_sim
source install/setup.bash
```

### 4.3 Run `ros2 launch`

Use `ros2 launch` when you want to start a launch file directly.

Examples:

Launch the main simulation stack:

```bash
ros2 launch mycobot_realsense_pick_sim sim_bringup.launch.py rviz:=false
```

Launch the joint-topic workflow:

```bash
ros2 launch mycobot_realsense_pick_sim topic_joint_control.launch.py
```

Launch the pose-topic workflow:

```bash
ros2 launch mycobot_realsense_pick_sim topic_pose_control.launch.py
```

Launch the slider workflow:

```bash
ros2 launch mycobot_realsense_pick_sim slider_control_sim.launch.py
```

### 4.4 Run `ros2 run`

Use `ros2 run` when you want to start one node directly instead of a whole launch file.

Examples:

Run the joint commander alone:

```bash
ros2 run mycobot_realsense_pick_sim topic_joint_commander
```

Run the pose commander alone:

```bash
ros2 run mycobot_realsense_pick_sim topic_pose_commander
```

Run the camera relay alone:

```bash
ros2 run mycobot_realsense_pick_sim realsense_topic_relay
```

This is useful when:

- the simulation is already running from another launch
- you only want to restart one node
- you want to isolate a problem in one component

### 4.5 Open More Than One Terminal

For most ROS 2 workflows, you should use more than one terminal.

Typical pattern:

1. Terminal 1: launch the simulation or the main workflow.
2. Terminal 2: publish commands with `ros2 topic pub`.
3. Terminal 3: inspect state with `ros2 topic echo`, `ros2 node list`, or `ros2 action list`.

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

### 4.6 Publish Commands Manually with `ros2 topic`

Once the correct workflow is running, you can publish commands directly.

Joint-space example:

```bash
ros2 topic pub --once /arm_joint_goal sensor_msgs/msg/JointState "{name: ['joint2_to_joint1', 'joint3_to_joint2', 'joint4_to_joint3', 'joint5_to_joint4', 'joint6_to_joint5', 'joint6output_to_joint6'], position: [0.0, -0.6, 0.9, -0.3, 0.2, 0.0]}"
```

Cartesian pose example:

```bash
ros2 topic pub --once /arm_goal_pose geometry_msgs/msg/PoseStamped "{header: {frame_id: 'world'}, pose: {position: {x: 0.18, y: 0.00, z: 0.62}, orientation: {x: 1.0, y: 0.0, z: 0.0, w: 0.0}}}"
```

### 4.7 Inspect the Running ROS Graph

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
ros2 topic info /arm_goal_pose
ros2 topic info /joint_states
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

### 4.8 Canonical Workflow Rule

For this repository, the preferred workflow is:

- host commands with `docker compose`
- runtime commands with `ros2 launch`, `ros2 run`, and `ros2 topic` inside the container

When writing documentation or PR reproduction steps, prefer:

- `docker compose -f docker/docker-compose.yml ...`
- `ros2 launch ...`
- `ros2 run ...`
- `ros2 topic ...`

Do not add new `run.sh` wrapper commands for new workflows.

## 5. Main Simulation Launches

### `ros2 launch mycobot_realsense_pick_sim sim_world.launch.py`

Launches only the Gazebo world.

Use this when:

- you want to inspect the scene alone
- you do not need the robot control stack yet

Do not use this when you expect the arm to be controllable.

### `ros2 launch mycobot_realsense_pick_sim sim_bringup.launch.py rviz:=false`

Launches the main runtime stack.

This is the base launch for most workflows. It brings up:

- Gazebo Sim
- the robot model
- the camera bridge
- robot state publisher
- ros_gz bridges
- ros2_control controllers

Use this when:

- you want to confirm the robot spawns correctly
- you want to validate controllers
- you want the camera topics available
- you want the simulation ready for higher-level control

## 6. Choose a Control Mode

### `ros2 launch mycobot_realsense_pick_sim topic_joint_control.launch.py`

This is the most direct and script-friendly way to move the robot.

It starts the simulation and a topic-based joint commander that listens on:

- `/arm_joint_goal`

Use this when:

- you want to send exact joint targets
- you want repeatable tests
- you want a simple homing command
- you want to script movements without MoveIt

### `ros2 launch mycobot_realsense_pick_sim topic_pose_control.launch.py`

This starts the Cartesian pose workflow.

It listens on:

- `/arm_goal_pose`

Use this when:

- you want to move the end-effector to a pose in space
- you want MoveIt to solve IK and execute the path
- you want a higher-level control workflow than raw joints

### `ros2 launch mycobot_realsense_pick_sim slider_control_sim.launch.py`

This launches the slider-based manual interface.

Use this when:

- you want an interactive GUI
- you want to manually inspect reachable joint ranges
- you want quick human-in-the-loop tests

### `ros2 launch mycobot_realsense_pick_sim pick_place.launch.py`

This launches the higher-level manipulation flow.

Use this when:

- you want to validate the perception and manipulation pipeline
- you want to test the system closer to the pick-and-place objective

## 7. Joint-Space Control

The `topic_joint_commander` node accepts `sensor_msgs/msg/JointState` messages on:

- `/arm_joint_goal`

It supports:

- full arm commands
- partial arm updates
- gripper-only commands
- combined arm + gripper commands

If you send a new command while the current one is still executing, the node keeps the latest command queued and executes it next.

### 7.1 Start the Joint Workflow

```bash
ros2 launch mycobot_realsense_pick_sim topic_joint_control.launch.py
```

### 7.2 Send a Full Arm Goal

```bash
ros2 topic pub --once /arm_joint_goal sensor_msgs/msg/JointState "{name: ['joint2_to_joint1', 'joint3_to_joint2', 'joint4_to_joint3', 'joint5_to_joint4', 'joint6_to_joint5', 'joint6output_to_joint6'], position: [0.0, -0.6, 0.9, -0.3, 0.2, 0.0]}"
```

Use this when you want to place all arm joints at a known configuration.

### 7.3 Send a Partial Joint Update

```bash
ros2 topic pub --once /arm_joint_goal sensor_msgs/msg/JointState "{name: ['joint3_to_joint2'], position: [-0.9]}"
```

Use this when you only want to change one joint and keep the others where they are.

### 7.4 Return to the Neutral Home Pose

```bash
ros2 topic pub --once /arm_joint_goal sensor_msgs/msg/JointState "{name: ['joint2_to_joint1', 'joint3_to_joint2', 'joint4_to_joint3', 'joint5_to_joint4', 'joint6_to_joint5', 'joint6output_to_joint6'], position: [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]}"
```

Use this when you want the arm back in the neutral reference pose.

### 7.5 Move Only the Gripper

```bash
ros2 topic pub --once /arm_joint_goal sensor_msgs/msg/JointState "{name: ['gripper_controller'], position: [-0.4]}"
```

Use this when:

- you want to test the gripper alone
- you want to open or close the fingers without moving the arm

### 7.6 Move Arm and Gripper Together

```bash
ros2 topic pub --once /arm_joint_goal sensor_msgs/msg/JointState "{name: ['joint2_to_joint1', 'joint3_to_joint2', 'joint4_to_joint3', 'joint5_to_joint4', 'joint6_to_joint5', 'joint6output_to_joint6', 'gripper_controller'], position: [0.2, -0.8, 1.0, -0.4, 0.1, 0.0, -0.35]}"
```

Use this when you want a combined pose-and-gripper state in one command.

## 8. Cartesian Pose Control

The `topic_pose_commander` node accepts `geometry_msgs/msg/PoseStamped` on:

- `/arm_goal_pose`

It computes IK with MoveIt and executes the resulting path.

### 8.1 Start the Pose Workflow

```bash
ros2 launch mycobot_realsense_pick_sim topic_pose_control.launch.py
```

### 8.2 Send a Test Cartesian Goal

```bash
ros2 topic pub --once /arm_goal_pose geometry_msgs/msg/PoseStamped "{header: {frame_id: 'world'}, pose: {position: {x: 0.18, y: 0.00, z: 0.62}, orientation: {x: 1.0, y: 0.0, z: 0.0, w: 0.0}}}"
```

Use this when you want a fixed end-effector orientation and a target position in the workspace.

### 8.3 Send a Goal with Default Orientation

```bash
ros2 topic pub --once /arm_goal_pose geometry_msgs/msg/PoseStamped "{header: {frame_id: 'world'}, pose: {position: {x: 0.20, y: -0.08, z: 0.58}, orientation: {x: 0.0, y: 0.0, z: 0.0, w: 0.0}}}"
```

If you send a zero quaternion, the node applies its default grasp orientation.

## 9. Slider Control

The slider workflow is meant to emulate the interactive manual control experience.

Start it with:

```bash
ros2 launch mycobot_realsense_pick_sim slider_control_sim.launch.py
```

This brings up:

- Gazebo
- the robot and camera
- RViz
- `joint_state_publisher_gui`
- the adapter node from `mycobot_280`

Control flow:

- the GUI publishes to `/slider_joint_states`
- the adapter translates the slider state into trajectories
- the arm and gripper trajectory controllers execute the motion

## 10. Step-By-Step Guided Examples

### Example A: Verify the Environment

1. Build the workspace.

```bash
docker compose -f docker/docker-compose.yml run --rm sim bash
```

Inside the container:

```bash
cd /workspaces/mycobot_realsense_pick_sim
colcon build --symlink-install
source install/setup.bash
```

2. Launch the main simulation stack.

```bash
ros2 launch mycobot_realsense_pick_sim sim_bringup.launch.py rviz:=false
```

3. In another terminal, check the main topics.

```bash
docker compose -f docker/docker-compose.yml run --rm sim bash
cd /workspaces/mycobot_realsense_pick_sim
source install/setup.bash
ros2 topic list | grep camera
ros2 topic echo --once /joint_states
```

### Example B: Move the Arm and Return Home

1. Start the joint workflow.

```bash
ros2 launch mycobot_realsense_pick_sim topic_joint_control.launch.py
```

2. Send a test arm configuration.

```bash
ros2 topic pub --once /arm_joint_goal sensor_msgs/msg/JointState "{name: ['joint2_to_joint1', 'joint3_to_joint2', 'joint4_to_joint3', 'joint5_to_joint4', 'joint6_to_joint5', 'joint6output_to_joint6'], position: [0.0, -0.6, 0.9, -0.3, 0.2, 0.0]}"
```

3. Return to the neutral home pose.

```bash
ros2 topic pub --once /arm_joint_goal sensor_msgs/msg/JointState "{name: ['joint2_to_joint1', 'joint3_to_joint2', 'joint4_to_joint3', 'joint5_to_joint4', 'joint6_to_joint5', 'joint6output_to_joint6'], position: [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]}"
```

### Example C: Move the Arm in Cartesian Space

1. Start the pose workflow.

```bash
ros2 launch mycobot_realsense_pick_sim topic_pose_control.launch.py
```

2. Send a Cartesian pose goal.

```bash
ros2 topic pub --once /arm_goal_pose geometry_msgs/msg/PoseStamped "{header: {frame_id: 'world'}, pose: {position: {x: 0.18, y: 0.00, z: 0.62}, orientation: {x: 1.0, y: 0.0, z: 0.0, w: 0.0}}}"
```

3. Send another goal elsewhere in the workspace.

```bash
ros2 topic pub --once /arm_goal_pose geometry_msgs/msg/PoseStamped "{header: {frame_id: 'world'}, pose: {position: {x: 0.20, y: -0.08, z: 0.58}, orientation: {x: 0.0, y: 0.0, z: 0.0, w: 0.0}}}"
```

## 11. Main Topics

Important topics you are likely to inspect first:

- `/joint_states`
- `/arm_joint_goal`
- `/arm_goal_pose`
- `/camera/color/image_raw`
- `/camera/color/camera_info`
- `/camera/depth/image_rect_raw`
- `/camera/depth/camera_info`
- `/detected_objects/poses`
- `/detected_objects/json`

## 12. Troubleshooting

### Gazebo or RViz Does Not Open

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
ros2 launch mycobot_realsense_pick_sim sim_bringup.launch.py rviz:=false
```

### A Topic Command Does Not Seem To Move the Robot

Check whether the relevant workflow is actually running:

```bash
ros2 node list
ros2 action list
ros2 topic info /arm_joint_goal
ros2 topic info /arm_goal_pose
```

### A New Joint Command Does Not Interrupt the Previous One

The joint commander keeps the latest command queued and runs it next. It does not cancel the current action in the middle.

## 13. What To Update When the Project Evolves

When a workflow changes, update:

- this manual
- the PR description
- the command examples that users are expected to run

This file should remain the main guided document for anyone trying to reproduce the environment and use the project features.
