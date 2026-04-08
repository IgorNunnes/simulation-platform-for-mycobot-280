from typing import Dict, List, Optional

import rclpy
from control_msgs.action import FollowJointTrajectory
from rclpy.action import ActionClient
from rclpy.duration import Duration
from rclpy.node import Node
from rclpy.qos import QoSProfile, QoSPresetProfiles
from sensor_msgs.msg import JointState
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint


ARM_JOINTS = [
    "joint2_to_joint1",
    "joint3_to_joint2",
    "joint4_to_joint3",
    "joint5_to_joint4",
    "joint6_to_joint5",
    "joint6output_to_joint6",
]
GRIPPER_JOINT = "gripper_controller"


class TopicJointCommander(Node):
    def __init__(self) -> None:
        super().__init__("topic_joint_commander")
        self.current_joint_state: Dict[str, float] = {}
        self.executing = False
        self.pending_joint_goal: Optional[JointState] = None
        self.pending_gripper_position: Optional[List[float]] = None

        self.declare_parameter("joint_goal_topic", "/arm_joint_goal")
        self.declare_parameter("trajectory_time_sec", 2.0)

        state_qos = QoSPresetProfiles.SENSOR_DATA.value
        command_qos = QoSProfile(depth=10)
        self.create_subscription(JointState, "/joint_states", self._on_joint_state, state_qos)
        self.create_subscription(
            JointState,
            self.get_parameter("joint_goal_topic").value,
            self._on_joint_goal,
            command_qos,
        )

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

        self.get_logger().info(
            f"Listening for joint goals on {self.get_parameter('joint_goal_topic').value}"
        )

    def _on_joint_state(self, msg: JointState) -> None:
        for name, position in zip(msg.name, msg.position):
            self.current_joint_state[name] = position

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

    def _dispatch_pending_goal(self) -> None:
        if self.pending_joint_goal is None:
            return

        next_goal = self.pending_joint_goal
        self.pending_joint_goal = None
        self.get_logger().info("Executing queued joint goal")
        self._on_joint_goal(next_goal)

    def _send_goal_async(
        self,
        client: ActionClient,
        joint_names: List[str],
        positions: List[float],
        label: str,
        result_callback,
    ) -> None:
        if not client.wait_for_server(timeout_sec=3.0):
            self.get_logger().warn(f"{label} action server is not available")
            self.executing = False
            self.pending_gripper_position = None
            self._dispatch_pending_goal()
            return

        future = client.send_goal_async(self._goal(joint_names, positions))
        future.add_done_callback(
            lambda done_future: self._on_goal_response(done_future, label, result_callback)
        )

    def _on_goal_response(self, future, label: str, result_callback) -> None:
        goal_handle = future.result()
        if goal_handle is None or not goal_handle.accepted:
            self.get_logger().warn(f"{label} goal was rejected")
            self.executing = False
            self.pending_gripper_position = None
            self._dispatch_pending_goal()
            return

        result_future = goal_handle.get_result_async()
        result_future.add_done_callback(result_callback)

    def _on_arm_result(self, future) -> None:
        result = future.result()
        ok = result is not None and result.result.error_code == 0
        if not ok:
            self.get_logger().warn("Arm goal execution failed")
            self.executing = False
            self.pending_gripper_position = None
            self._dispatch_pending_goal()
            return

        if self.pending_gripper_position is not None:
            gripper_position = self.pending_gripper_position
            self.pending_gripper_position = None
            self._send_goal_async(
                self.gripper_client,
                [GRIPPER_JOINT],
                gripper_position,
                "Gripper",
                self._on_gripper_result,
            )
            return

        self.get_logger().info("Joint goal executed successfully")
        self.executing = False
        self._dispatch_pending_goal()

    def _on_gripper_result(self, future) -> None:
        result = future.result()
        ok = result is not None and result.result.error_code == 0
        if not ok:
            self.get_logger().warn("Gripper goal execution failed")
        else:
            self.get_logger().info("Joint goal executed successfully")

        self.executing = False
        self._dispatch_pending_goal()

    def _merged_joint_targets(self, msg: JointState) -> Dict[str, float]:
        if len(msg.name) != len(msg.position):
            raise ValueError("JointState name and position arrays must have the same length")

        merged = {name: 0.0 for name in ARM_JOINTS}
        merged[GRIPPER_JOINT] = 0.0
        merged.update(self.current_joint_state)
        for name, position in zip(msg.name, msg.position):
            merged[name] = float(position)
        return merged

    def _copy_joint_state(self, msg: JointState) -> JointState:
        copied = JointState()
        copied.header = msg.header
        copied.name = list(msg.name)
        copied.position = list(msg.position)
        copied.velocity = list(msg.velocity)
        copied.effort = list(msg.effort)
        return copied

    def _on_joint_goal(self, msg: JointState) -> None:
        if self.executing:
            self.pending_joint_goal = self._copy_joint_state(msg)
            self.get_logger().warn(
                "Another joint goal is executing; queued the latest goal to run next"
            )
            return

        if not msg.name:
            self.get_logger().warn("Received an empty joint goal")
            return

        self.executing = True
        try:
            merged = self._merged_joint_targets(msg)
            arm_requested = any(name in ARM_JOINTS for name in msg.name)
            gripper_requested = GRIPPER_JOINT in msg.name

            if not self.current_joint_state:
                self.get_logger().warn(
                    "Joint state not received yet; using zero defaults for unspecified joints"
                )

            if arm_requested:
                arm_positions = [merged[name] for name in ARM_JOINTS]
                self.pending_gripper_position = (
                    [merged[GRIPPER_JOINT]] if gripper_requested else None
                )
                self._send_goal_async(
                    self.arm_client,
                    ARM_JOINTS,
                    arm_positions,
                    "Arm",
                    self._on_arm_result,
                )
                return

            if gripper_requested:
                gripper_position = [merged[GRIPPER_JOINT]]
                self._send_goal_async(
                    self.gripper_client,
                    [GRIPPER_JOINT],
                    gripper_position,
                    "Gripper",
                    self._on_gripper_result,
                )
                return

            self.get_logger().warn("Joint goal did not reference any controllable joint")
            self.executing = False
        except ValueError as exc:
            self.get_logger().warn(str(exc))
            self.executing = False
            self.pending_gripper_position = None
            self._dispatch_pending_goal()


def main() -> None:
    rclpy.init()
    node = TopicJointCommander()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
