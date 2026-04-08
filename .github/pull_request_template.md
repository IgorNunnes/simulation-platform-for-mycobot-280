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

- 

## Perception and Planning

- 

## Documentation and Developer Workflow

- 

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
./run.sh build-image
./run.sh build-ws
```

## 3. Start the Main Simulation

```bash
./run.sh sim-bringup rviz:=false
```

Expected result:

- Gazebo opens
- the robot spawns
- the camera topics are available
- ros2_control controllers are active

## 4. Validate Joint-Space Control

Start the joint-topic workflow:

```bash
./run.sh joint-topic
```

Send a test arm configuration:

```bash
ros2 topic pub --once /arm_joint_goal sensor_msgs/msg/JointState "{name: ['joint2_to_joint1', 'joint3_to_joint2', 'joint4_to_joint3', 'joint5_to_joint4', 'joint6_to_joint5', 'joint6output_to_joint6'], position: [0.0, -0.6, 0.9, -0.3, 0.2, 0.0]}"
```

Return to home:

```bash
ros2 topic pub --once /arm_joint_goal sensor_msgs/msg/JointState "{name: ['joint2_to_joint1', 'joint3_to_joint2', 'joint4_to_joint3', 'joint5_to_joint4', 'joint6_to_joint5', 'joint6output_to_joint6'], position: [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]}"
```

## 5. Validate Cartesian Pose Control

Start the pose-topic workflow:

```bash
./run.sh topic-pose
```

Send a Cartesian goal:

```bash
ros2 topic pub --once /arm_goal_pose geometry_msgs/msg/PoseStamped "{header: {frame_id: 'world'}, pose: {position: {x: 0.18, y: 0.00, z: 0.62}, orientation: {x: 1.0, y: 0.0, z: 0.0, w: 0.0}}}"
```

## 6. Validate Slider Control

```bash
./run.sh slider
```

Expected result:

- the slider GUI opens
- slider changes trigger trajectory execution

# Validation Checklist

Keep this checklist updated as the branch grows.

- [ ] Docker image builds successfully
- [ ] Workspace builds successfully with `colcon build --symlink-install`
- [ ] Gazebo world launches
- [ ] Robot spawns correctly
- [ ] Camera topics are available
- [ ] Joint topic control works
- [ ] Pose topic control works
- [ ] Slider control works
- [ ] Pick-and-place flow still works
- [ ] `MANUAL_FOR_USE.md` reflects the latest workflow
- [ ] `README.md` remains focused on host requirements and Docker bringup

# Known Limitations

Document anything that still needs improvement or that users should know before reproducing the branch.

- 

# Next Steps

Use this section as the evolving backlog for follow-up work.

- 
