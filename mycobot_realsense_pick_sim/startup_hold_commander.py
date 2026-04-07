from typing import List

import rclpy
from control_msgs.action import FollowJointTrajectory
from rclpy.action import ActionClient
from rclpy.duration import Duration
from rclpy.node import Node
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint


class StartupHoldCommander(Node):
    def __init__(self) -> None:
        super().__init__("startup_hold_commander")

        self.declare_parameter(
            "arm_joint_names",
            [
                "joint2_to_joint1",
                "joint3_to_joint2",
                "joint4_to_joint3",
                "joint5_to_joint4",
                "joint6_to_joint5",
                "joint6output_to_joint6",
            ],
        )
        self.declare_parameter("arm_positions", [0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
        self.declare_parameter("gripper_joint_names", ["gripper_controller"])
        self.declare_parameter("gripper_positions", [0.0])
        self.declare_parameter("trajectory_time_sec", 1.5)

        self.arm_client = ActionClient(
            self,
            FollowJointTrajectory,
            "/arm_controller/follow_joint_trajectory",
        )
        self.gripper_client = ActionClient(
            self,
            FollowJointTrajectory,
            "/gripper_trajectory_controller/follow_joint_trajectory",
        )

        self.timer = self.create_timer(0.5, self._run_once)
        self.sent = False

    def _goal(self, joint_names: List[str], positions: List[float]) -> FollowJointTrajectory.Goal:
        goal = FollowJointTrajectory.Goal()
        goal.trajectory = JointTrajectory()
        goal.trajectory.joint_names = joint_names

        point = JointTrajectoryPoint()
        point.positions = positions
        point.time_from_start = Duration(
            seconds=float(self.get_parameter("trajectory_time_sec").value)
        ).to_msg()
        goal.trajectory.points = [point]
        return goal

    def _run_once(self) -> None:
        if self.sent:
            return

        if not self.arm_client.wait_for_server(timeout_sec=0.1):
            self.get_logger().info("Waiting for arm trajectory action server...")
            return

        if not self.gripper_client.wait_for_server(timeout_sec=0.1):
            self.get_logger().info("Waiting for gripper trajectory action server...")
            return

        arm_joint_names = list(self.get_parameter("arm_joint_names").value)
        arm_positions = [float(v) for v in self.get_parameter("arm_positions").value]
        gripper_joint_names = list(self.get_parameter("gripper_joint_names").value)
        gripper_positions = [float(v) for v in self.get_parameter("gripper_positions").value]

        self.arm_client.send_goal_async(self._goal(arm_joint_names, arm_positions))
        self.gripper_client.send_goal_async(self._goal(gripper_joint_names, gripper_positions))
        self.get_logger().info("Sent startup hold trajectory to arm and gripper")
        self.sent = True
        self.timer.cancel()


def main() -> None:
    rclpy.init()
    node = StartupHoldCommander()
    start_time = node.get_clock().now()
    timeout = Duration(seconds=10.0)
    while rclpy.ok() and not node.sent:
      rclpy.spin_once(node, timeout_sec=0.2)
      if node.get_clock().now() - start_time > timeout:
          node.get_logger().warn("Timed out waiting to send startup hold trajectory")
          break
    node.destroy_node()
    rclpy.shutdown()
