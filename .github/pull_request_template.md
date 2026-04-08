# Summary

Describe the PR in a way that someone new to the repository can understand what changed and why it matters.

- 
- 

# Why This PR Exists

Explain the problem that this PR solves and the workflow it improves.

- 

# Guided Reproduction Notes

This PR description should be treated as a living guide for the branch while the work is in progress.

The canonical user guide in the repository is:

- `MANUAL_FOR_USE.md`

Whenever the workflow changes:

- update `MANUAL_FOR_USE.md`
- update this PR description with the relevant deltas
- keep the validation steps below aligned with the current code

# What Changed

Group the changes by area and explain the practical effect of each one.

## Simulation and Robot Model

- 

## Control and Teleoperation

- the branch is centered on the topic-based joint workflow because it is the currently reliable control path
- `topic_joint_control.launch.py` is the main supported launcher for simulation plus arm actuation
- obsolete launch entry points were removed so the public workflow surface matches what is currently supported

## Documentation and Developer Workflow

- README remains focused on Ubuntu host requirements, Docker setup, and first bringup
- `MANUAL_FOR_USE.md` includes a dedicated section for running standard `ros2` commands inside the container
- the manual now treats Docker plus raw `ros2 launch`, `ros2 run`, and `ros2 topic` as the canonical workflow
- the manual makes it explicit that each terminal used for ROS 2 commands should start from `docker compose -f docker/docker-compose.yml run --rm sim bash` and `source install/setup.bash`
- new workflow documentation should prefer Docker and ROS 2 commands directly instead of adding new `run.sh` wrappers

# How To Reproduce the Current Branch

Use this section as a branch-specific manual that complements `MANUAL_FOR_USE.md`.

## 1. Prepare Docker on Ubuntu

```bash
sudo apt update
sudo apt install -y docker.io docker-compose-plugin x11-xserver-utils
sudo usermod -aG docker "$USER"
newgrp docker
docker run --rm hello-world
docker compose version
```

## 2. Clone the Branch and Build the Environment

```bash
git clone -b humble https://github.com/IgorNunnes/simulation-platform-for-mycobot-280.git
cd simulation-platform-for-mycobot-280
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

Inside the container:

```bash
cd /workspaces/mycobot_realsense_pick_sim
colcon build --symlink-install
source install/setup.bash
```

## 3. Start the Supported Workflow

```bash
ros2 launch mycobot_realsense_pick_sim topic_joint_control.launch.py
```

Expected result:

- Gazebo opens
- the robot spawns
- the camera topics are available
- ros2_control controllers are active
- the topic joint commander is available

## 4. Validate Manual ROS 2 Usage Inside the Container

Open a shell inside the container:

```bash
docker compose -f docker/docker-compose.yml run --rm sim bash
```

Inside the container:

```bash
cd /workspaces/mycobot_realsense_pick_sim
source install/setup.bash
```

Launch the joint-topic workflow manually with `ros2 launch`:

```bash
ros2 launch mycobot_realsense_pick_sim topic_joint_control.launch.py
```

In a second terminal, enter the container again and source the workspace:

```bash
docker compose -f docker/docker-compose.yml run --rm sim bash
cd /workspaces/mycobot_realsense_pick_sim
source install/setup.bash
```

Inspect the ROS graph:

```bash
ros2 node list
ros2 topic list
ros2 action list
```

This validates that the branch supports the Docker-based shell workflow with standard ROS 2 commands inside the container.

## 5. Validate Joint-Space Control

Start the joint-topic workflow:

```bash
ros2 launch mycobot_realsense_pick_sim topic_joint_control.launch.py
```

Send a test arm configuration:

```bash
ros2 topic pub --once /arm_joint_goal sensor_msgs/msg/JointState "{name: ['joint2_to_joint1', 'joint3_to_joint2', 'joint4_to_joint3', 'joint5_to_joint4', 'joint6_to_joint5', 'joint6output_to_joint6'], position: [0.0, -0.6, 0.9, -0.3, 0.2, 0.0]}"
```

Return to home:

```bash
ros2 topic pub --once /arm_joint_goal sensor_msgs/msg/JointState "{name: ['joint2_to_joint1', 'joint3_to_joint2', 'joint4_to_joint3', 'joint5_to_joint4', 'joint6_to_joint5', 'joint6output_to_joint6'], position: [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]}"
```

Important:

- the `ros2 topic pub` commands above should be executed from a terminal that is already inside the container
- for each new terminal, run `docker compose -f docker/docker-compose.yml run --rm sim bash` and `source install/setup.bash` before publishing commands

# Validation Checklist

Keep this checklist updated as the branch grows.

- [ ] Docker image builds successfully
- [ ] Workspace builds successfully with `colcon build --symlink-install`
- [ ] Gazebo world launches
- [ ] Robot spawns correctly
- [ ] Camera topics are available
- [ ] Manual `ros2 launch` / `ros2 run` / `ros2 topic` workflows work inside the container
- [ ] Joint topic control works
- [ ] `MANUAL_FOR_USE.md` reflects the latest workflow
- [ ] `README.md` remains focused on host requirements and Docker bringup

# Known Limitations

Document anything that still needs improvement or that users should know before reproducing the branch.

- 

# Next Steps

Use this section as the evolving backlog for follow-up work.

- 
