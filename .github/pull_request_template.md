# Summary

Describe the main purpose of the PR in 2-5 bullets.

- 
- 

# Motivation

Explain why this change is needed.

- 

# What Changed

Group the changes by area so the PR can keep evolving as the branch grows.

## Simulation and Robot Model

- 

## Control and Teleoperation

- 

## Perception and Planning

- 

## Documentation and Developer Workflow

- 

# How To Run

Document the current recommended procedure to bring up the environment and test the PR.

## Docker Setup

```bash
git clone -b humble https://github.com/IgorNunnes/simulation-platform-for-mycobot-280.git
cd simulation-platform-for-mycobot-280
xhost +local:docker
./run.sh build-image
./run.sh build-ws
```

## Main Bringup

```bash
./run.sh sim-bringup rviz:=false
```

## Joint Topic Control

```bash
./run.sh joint-topic
ros2 topic pub --once /arm_joint_goal sensor_msgs/msg/JointState "{name: ['joint2_to_joint1', 'joint3_to_joint2', 'joint4_to_joint3', 'joint5_to_joint4', 'joint6_to_joint5', 'joint6output_to_joint6'], position: [0.0, -0.6, 0.9, -0.3, 0.2, 0.0]}"
```

## Pose Topic Control

```bash
./run.sh topic-pose
ros2 topic pub --once /arm_goal_pose geometry_msgs/msg/PoseStamped "{header: {frame_id: 'world'}, pose: {position: {x: 0.18, y: 0.00, z: 0.62}, orientation: {x: 1.0, y: 0.0, z: 0.0, w: 0.0}}}"
```

# Validation

Keep this checklist updated while the PR grows.

- [ ] Docker image builds successfully
- [ ] Workspace builds successfully with `colcon build --symlink-install`
- [ ] Gazebo world launches
- [ ] Robot spawns correctly
- [ ] Camera topics are available
- [ ] Joint topic control works
- [ ] Pose topic control works
- [ ] Slider control works
- [ ] Pick-and-place flow still works
- [ ] README reflects the latest workflow

# Known Limitations

Track anything still open or not yet production-ready.

- 

# Next Steps

Use this section as an evolving backlog for follow-up work.

- 
