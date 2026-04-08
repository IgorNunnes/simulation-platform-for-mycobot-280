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

The simplest day-to-day workflow is:

1. Build the workspace after changes.
2. Launch the main simulation stack.
3. Choose the control mode you want to use.
4. Validate that controllers, robot state, and camera topics are alive.

In practice, that usually means:

```bash
./run.sh build-ws
./run.sh sim-bringup rviz:=false
```

Then choose one of:

```bash
./run.sh joint-topic
./run.sh topic-pose
./run.sh slider
./run.sh pick-place
```

## 3. Build and Environment Commands

### `./run.sh build-image`

Builds the Docker image used by the project.

Use it when:

- you are setting up the repository for the first time
- the `docker/Dockerfile` changed
- the base ROS or dependency stack changed

### `./run.sh build-ws`

Runs `colcon build --symlink-install` inside the project container.

Use it when:

- Python nodes changed
- launch files changed
- configuration files changed
- you added a new executable

### `./run.sh shell`

Opens an interactive shell inside the configured container.

Use it when:

- you want to run `ros2` commands manually
- you want to inspect topics, nodes, services, or actions
- you want to debug inside the container

## 4. Main Simulation Launches

### `./run.sh sim-world`

Launches only the Gazebo world.

Use this when:

- you want to inspect the scene alone
- you do not need the robot control stack yet

Do not use this when you expect the arm to be controllable.

### `./run.sh sim-bringup rviz:=false`

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

## 5. Choose a Control Mode

### `./run.sh joint-topic`

This is the most direct and script-friendly way to move the robot.

It starts the simulation and a topic-based joint commander that listens on:

- `/arm_joint_goal`

Use this when:

- you want to send exact joint targets
- you want repeatable tests
- you want a simple homing command
- you want to script movements without MoveIt

### `./run.sh topic-pose`

This starts the Cartesian pose workflow.

It listens on:

- `/arm_goal_pose`

Use this when:

- you want to move the end-effector to a pose in space
- you want MoveIt to solve IK and execute the path
- you want a higher-level control workflow than raw joints

### `./run.sh slider`

This launches the slider-based manual interface.

Use this when:

- you want an interactive GUI
- you want to manually inspect reachable joint ranges
- you want quick human-in-the-loop tests

### `./run.sh pick-place`

This launches the higher-level manipulation flow.

Use this when:

- you want to validate the perception and manipulation pipeline
- you want to test the system closer to the pick-and-place objective

## 6. Joint-Space Control

The `topic_joint_commander` node accepts `sensor_msgs/msg/JointState` messages on:

- `/arm_joint_goal`

It supports:

- full arm commands
- partial arm updates
- gripper-only commands
- combined arm + gripper commands

If you send a new command while the current one is still executing, the node keeps the latest command queued and executes it next.

### 6.1 Start the Joint Workflow

```bash
./run.sh joint-topic
```

### 6.2 Send a Full Arm Goal

```bash
ros2 topic pub --once /arm_joint_goal sensor_msgs/msg/JointState "{name: ['joint2_to_joint1', 'joint3_to_joint2', 'joint4_to_joint3', 'joint5_to_joint4', 'joint6_to_joint5', 'joint6output_to_joint6'], position: [0.0, -0.6, 0.9, -0.3, 0.2, 0.0]}"
```

Use this when you want to place all arm joints at a known configuration.

### 6.3 Send a Partial Joint Update

```bash
ros2 topic pub --once /arm_joint_goal sensor_msgs/msg/JointState "{name: ['joint3_to_joint2'], position: [-0.9]}"
```

Use this when you only want to change one joint and keep the others where they are.

### 6.4 Return to the Neutral Home Pose

```bash
ros2 topic pub --once /arm_joint_goal sensor_msgs/msg/JointState "{name: ['joint2_to_joint1', 'joint3_to_joint2', 'joint4_to_joint3', 'joint5_to_joint4', 'joint6_to_joint5', 'joint6output_to_joint6'], position: [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]}"
```

Use this when you want the arm back in the neutral reference pose.

### 6.5 Move Only the Gripper

```bash
ros2 topic pub --once /arm_joint_goal sensor_msgs/msg/JointState "{name: ['gripper_controller'], position: [-0.4]}"
```

Use this when:

- you want to test the gripper alone
- you want to open or close the fingers without moving the arm

### 6.6 Move Arm and Gripper Together

```bash
ros2 topic pub --once /arm_joint_goal sensor_msgs/msg/JointState "{name: ['joint2_to_joint1', 'joint3_to_joint2', 'joint4_to_joint3', 'joint5_to_joint4', 'joint6_to_joint5', 'joint6output_to_joint6', 'gripper_controller'], position: [0.2, -0.8, 1.0, -0.4, 0.1, 0.0, -0.35]}"
```

Use this when you want a combined pose-and-gripper state in one command.

## 7. Cartesian Pose Control

The `topic_pose_commander` node accepts `geometry_msgs/msg/PoseStamped` on:

- `/arm_goal_pose`

It computes IK with MoveIt and executes the resulting path.

### 7.1 Start the Pose Workflow

```bash
./run.sh topic-pose
```

### 7.2 Send a Test Cartesian Goal

```bash
ros2 topic pub --once /arm_goal_pose geometry_msgs/msg/PoseStamped "{header: {frame_id: 'world'}, pose: {position: {x: 0.18, y: 0.00, z: 0.62}, orientation: {x: 1.0, y: 0.0, z: 0.0, w: 0.0}}}"
```

Use this when you want a fixed end-effector orientation and a target position in the workspace.

### 7.3 Send a Goal with Default Orientation

```bash
ros2 topic pub --once /arm_goal_pose geometry_msgs/msg/PoseStamped "{header: {frame_id: 'world'}, pose: {position: {x: 0.20, y: -0.08, z: 0.58}, orientation: {x: 0.0, y: 0.0, z: 0.0, w: 0.0}}}"
```

If you send a zero quaternion, the node applies its default grasp orientation.

## 8. Slider Control

The slider workflow is meant to emulate the interactive manual control experience.

Start it with:

```bash
./run.sh slider
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

## 9. Step-By-Step Guided Examples

### Example A: Verify the Environment

1. Build the workspace.

```bash
./run.sh build-ws
```

2. Launch the main simulation stack.

```bash
./run.sh sim-bringup rviz:=false
```

3. In another terminal, check the main topics.

```bash
ros2 topic list | grep camera
ros2 topic echo --once /joint_states
```

### Example B: Move the Arm and Return Home

1. Start the joint workflow.

```bash
./run.sh joint-topic
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
./run.sh topic-pose
```

2. Send a Cartesian pose goal.

```bash
ros2 topic pub --once /arm_goal_pose geometry_msgs/msg/PoseStamped "{header: {frame_id: 'world'}, pose: {position: {x: 0.18, y: 0.00, z: 0.62}, orientation: {x: 1.0, y: 0.0, z: 0.0, w: 0.0}}}"
```

3. Send another goal elsewhere in the workspace.

```bash
ros2 topic pub --once /arm_goal_pose geometry_msgs/msg/PoseStamped "{header: {frame_id: 'world'}, pose: {position: {x: 0.20, y: -0.08, z: 0.58}, orientation: {x: 0.0, y: 0.0, z: 0.0, w: 0.0}}}"
```

## 10. Main Topics

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

## 11. Troubleshooting

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
./run.sh sim-bringup rviz:=false
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

## 12. What To Update When the Project Evolves

When a workflow changes, update:

- this manual
- the PR description
- the command examples that users are expected to run

This file should remain the main guided document for anyone trying to reproduce the environment and use the project features.
