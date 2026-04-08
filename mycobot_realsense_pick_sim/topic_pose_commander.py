from typing import Dict, Optional

import rclpy
from geometry_msgs.msg import Pose, PoseStamped
from moveit_msgs.action import MoveGroup
from moveit_msgs.msg import Constraints, JointConstraint, MotionPlanRequest, PlanningOptions, RobotState
from moveit_msgs.srv import GetPositionIK
from rclpy.action import ActionClient
from rclpy.duration import Duration
from rclpy.node import Node
from rclpy.qos import QoSProfile, QoSPresetProfiles
from sensor_msgs.msg import JointState


ARM_JOINTS = [
    "joint2_to_joint1",
    "joint3_to_joint2",
    "joint4_to_joint3",
    "joint5_to_joint4",
    "joint6_to_joint5",
    "joint6output_to_joint6",
]


class TopicPoseCommander(Node):
    def __init__(self) -> None:
        super().__init__("topic_pose_commander")
        self.current_joint_state: Dict[str, float] = {}
        self.executing = False

        self.declare_parameter("pose_topic", "/arm_goal_pose")
        self.declare_parameter("world_frame", "world")
        self.declare_parameter("group_name", "arm_group")
        self.declare_parameter("ik_link_name", "joint6_flange")
        self.declare_parameter("max_velocity_scaling", 0.3)
        self.declare_parameter("max_acceleration_scaling", 0.3)
        self.declare_parameter("allowed_planning_time", 5.0)

        state_qos = QoSPresetProfiles.SENSOR_DATA.value
        command_qos = QoSProfile(depth=10)
        self.create_subscription(JointState, "/joint_states", self._on_joint_state, state_qos)
        self.create_subscription(
            PoseStamped,
            self.get_parameter("pose_topic").value,
            self._on_pose_goal,
            command_qos,
        )

        self.move_group_client = ActionClient(self, MoveGroup, "/move_action")
        self.ik_client = self.create_client(GetPositionIK, "/compute_ik")

        self.get_logger().info(
            f"Listening for target poses on {self.get_parameter('pose_topic').value}"
        )

    def _on_joint_state(self, msg: JointState) -> None:
        for name, position in zip(msg.name, msg.position):
            self.current_joint_state[name] = position

    def _joint_constraints(self, joint_positions: Dict[str, float]) -> Constraints:
        constraints = Constraints()
        for joint_name in ARM_JOINTS:
            jc = JointConstraint()
            jc.joint_name = joint_name
            jc.position = float(joint_positions[joint_name])
            jc.tolerance_above = 0.01
            jc.tolerance_below = 0.01
            jc.weight = 1.0
            constraints.joint_constraints.append(jc)
        return constraints

    def _compute_ik(self, pose_stamped: PoseStamped) -> Optional[Dict[str, float]]:
        if not self.ik_client.wait_for_service(timeout_sec=3.0):
            self.get_logger().warn("compute_ik service is not available")
            return None
        request = GetPositionIK.Request()
        request.ik_request.group_name = self.get_parameter("group_name").value
        request.ik_request.ik_link_name = self.get_parameter("ik_link_name").value
        request.ik_request.avoid_collisions = True
        request.ik_request.pose_stamped = pose_stamped
        request.ik_request.timeout = Duration(seconds=0.5).to_msg()
        seed = RobotState()
        seed.joint_state.name = ARM_JOINTS
        seed.joint_state.position = [self.current_joint_state.get(name, 0.0) for name in ARM_JOINTS]
        request.ik_request.robot_state = seed
        future = self.ik_client.call_async(request)
        rclpy.spin_until_future_complete(self, future)
        response = future.result()
        if response is None or response.error_code.val != 1:
            return None
        return {
            name: value
            for name, value in zip(response.solution.joint_state.name, response.solution.joint_state.position)
            if name in ARM_JOINTS
        }

    def _send_move_group_goal(self, joint_positions: Dict[str, float]) -> bool:
        goal = MoveGroup.Goal()
        request = MotionPlanRequest()
        request.group_name = self.get_parameter("group_name").value
        request.goal_constraints = [self._joint_constraints(joint_positions)]
        request.allowed_planning_time = float(self.get_parameter("allowed_planning_time").value)
        request.num_planning_attempts = 5
        request.max_velocity_scaling_factor = float(self.get_parameter("max_velocity_scaling").value)
        request.max_acceleration_scaling_factor = float(self.get_parameter("max_acceleration_scaling").value)
        goal.request = request

        planning_options = PlanningOptions()
        planning_options.plan_only = False
        planning_options.look_around = False
        planning_options.replan = True
        planning_options.replan_attempts = 2
        goal.planning_options = planning_options

        if not self.move_group_client.wait_for_server(timeout_sec=5.0):
            self.get_logger().warn("move_action server is not available")
            return False
        goal_future = self.move_group_client.send_goal_async(goal)
        rclpy.spin_until_future_complete(self, goal_future)
        goal_handle = goal_future.result()
        if goal_handle is None or not goal_handle.accepted:
            return False
        result_future = goal_handle.get_result_async()
        rclpy.spin_until_future_complete(self, result_future)
        result = result_future.result()
        return result is not None and result.result.error_code.val == 1

    def _normalize_goal(self, msg: PoseStamped) -> PoseStamped:
        goal = PoseStamped()
        goal.header = msg.header
        if not goal.header.frame_id:
            goal.header.frame_id = self.get_parameter("world_frame").value
        goal.pose = Pose()
        goal.pose.position = msg.pose.position
        goal.pose.orientation = msg.pose.orientation
        if (
            goal.pose.orientation.x == 0.0
            and goal.pose.orientation.y == 0.0
            and goal.pose.orientation.z == 0.0
            and goal.pose.orientation.w == 0.0
        ):
            goal.pose.orientation.x = 1.0
            goal.pose.orientation.y = 0.0
            goal.pose.orientation.z = 0.0
            goal.pose.orientation.w = 0.0
        return goal

    def _on_pose_goal(self, msg: PoseStamped) -> None:
        if self.executing:
            self.get_logger().warn("Ignoring pose goal because another goal is executing")
            return
        goal = self._normalize_goal(msg)
        self.executing = True
        try:
            if not all(name in self.current_joint_state for name in ARM_JOINTS):
                self.get_logger().warn(
                    "Joint state not fully received yet; using zero defaults as IK seed"
                )
            ik_solution = self._compute_ik(goal)
            if ik_solution is None:
                self.get_logger().warn("Failed to compute IK for requested pose")
                return
            if self._send_move_group_goal(ik_solution):
                self.get_logger().info("Target pose executed successfully")
            else:
                self.get_logger().warn("MoveIt failed to execute the requested pose")
        finally:
            self.executing = False


def main() -> None:
    rclpy.init()
    node = TopicPoseCommander()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
