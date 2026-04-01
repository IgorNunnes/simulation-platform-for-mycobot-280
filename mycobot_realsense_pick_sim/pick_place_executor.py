import json
from typing import Dict, List, Optional

import rclpy
from control_msgs.action import FollowJointTrajectory
from geometry_msgs.msg import Pose
from moveit_msgs.action import MoveGroup
from moveit_msgs.msg import Constraints, JointConstraint, MotionPlanRequest, PlanningOptions, RobotState
from moveit_msgs.srv import GetPositionIK
from rclpy.action import ActionClient
from rclpy.duration import Duration
from rclpy.node import Node
from rclpy.qos import QoSProfile
from ros_gz_interfaces.msg import Entity
from ros_gz_interfaces.srv import SetEntityPose
from sensor_msgs.msg import JointState
from std_msgs.msg import String
from tf2_ros import Buffer, TransformListener
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint


ARM_JOINTS = [
    "joint2_to_joint1",
    "joint3_to_joint2",
    "joint4_to_joint3",
    "joint5_to_joint4",
    "joint6_to_joint5",
    "joint6output_to_joint6",
]


class PickPlaceExecutor(Node):
    def __init__(self) -> None:
        super().__init__("pick_place_executor")
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)
        self.current_joint_state: Dict[str, float] = {}
        self.detected_objects: List[Dict] = []
        self.completed_objects = set()
        self.active = False
        self.attached_entity: Optional[str] = None

        self.declare_parameter("world_frame", "world")
        self.declare_parameter("tool_frame", "gripper_base")
        self.declare_parameter("group_name", "arm_group")
        self.declare_parameter("ik_link_name", "joint6_flange")
        self.declare_parameter("grasp_height_offset", 0.10)
        self.declare_parameter("approach_height_offset", 0.18)
        self.declare_parameter("place_pose", [0.34, -0.18, 0.44])
        self.declare_parameter("attach_service", "/world/mycobot_pick_world/set_pose")

        qos = QoSProfile(depth=10)
        self.create_subscription(JointState, "/joint_states", self._on_joint_state, qos)
        self.create_subscription(String, "/detected_objects/json", self._on_detections, qos)

        self.move_group_client = ActionClient(self, MoveGroup, "/move_action")
        self.gripper_client = ActionClient(self, FollowJointTrajectory, "/gripper_trajectory_controller/follow_joint_trajectory")
        self.ik_client = self.create_client(GetPositionIK, "/compute_ik")
        self.set_pose_client = self.create_client(SetEntityPose, self.get_parameter("attach_service").value)

        self.pick_timer = self.create_timer(2.0, self._maybe_pick)
        self.attach_timer = self.create_timer(0.1, self._update_attached_object)

    def _on_joint_state(self, msg: JointState) -> None:
        for name, position in zip(msg.name, msg.position):
            self.current_joint_state[name] = position

    def _on_detections(self, msg: String) -> None:
        try:
            self.detected_objects = json.loads(msg.data)
        except json.JSONDecodeError:
            self.detected_objects = []

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

    def _send_move_group_goal(self, joint_positions: Dict[str, float]) -> bool:
        goal = MoveGroup.Goal()
        request = MotionPlanRequest()
        request.group_name = self.get_parameter("group_name").value
        request.goal_constraints = [self._joint_constraints(joint_positions)]
        request.allowed_planning_time = 5.0
        request.num_planning_attempts = 5
        request.max_velocity_scaling_factor = 0.3
        request.max_acceleration_scaling_factor = 0.3
        goal.request = request

        planning_options = PlanningOptions()
        planning_options.plan_only = False
        planning_options.look_around = False
        planning_options.replan = True
        planning_options.replan_attempts = 2
        goal.planning_options = planning_options

        if not self.move_group_client.wait_for_server(timeout_sec=5.0):
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

    def _command_gripper(self, position: float) -> bool:
        if not self.gripper_client.wait_for_server(timeout_sec=5.0):
            return False
        goal = FollowJointTrajectory.Goal()
        goal.trajectory = JointTrajectory()
        goal.trajectory.joint_names = ["gripper_controller"]
        point = JointTrajectoryPoint()
        point.positions = [position]
        point.time_from_start = Duration(seconds=1.0).to_msg()
        goal.trajectory.points = [point]
        future = self.gripper_client.send_goal_async(goal)
        rclpy.spin_until_future_complete(self, future)
        handle = future.result()
        if handle is None or not handle.accepted:
            return False
        result_future = handle.get_result_async()
        rclpy.spin_until_future_complete(self, result_future)
        return True

    def _compute_ik(self, pose: Pose) -> Optional[Dict[str, float]]:
        if not self.ik_client.wait_for_service(timeout_sec=3.0):
            return None
        request = GetPositionIK.Request()
        request.ik_request.group_name = self.get_parameter("group_name").value
        request.ik_request.ik_link_name = self.get_parameter("ik_link_name").value
        request.ik_request.avoid_collisions = True
        request.ik_request.pose_stamped.header.frame_id = self.get_parameter("world_frame").value
        request.ik_request.pose_stamped.pose = pose
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
        return {name: value for name, value in zip(response.solution.joint_state.name, response.solution.joint_state.position)}

    def _pose(self, x: float, y: float, z: float) -> Pose:
        pose = Pose()
        pose.position.x = x
        pose.position.y = y
        pose.position.z = z
        pose.orientation.x = 1.0
        pose.orientation.y = 0.0
        pose.orientation.z = 0.0
        pose.orientation.w = 0.0
        return pose

    def _set_entity_pose(self, entity_name: str, pose: Pose) -> bool:
        if not self.set_pose_client.wait_for_service(timeout_sec=2.0):
            return False
        request = SetEntityPose.Request()
        request.entity = Entity(name=entity_name, type=Entity.MODEL)
        request.pose = pose
        future = self.set_pose_client.call_async(request)
        rclpy.spin_until_future_complete(self, future)
        response = future.result()
        return response is not None and response.success

    def _update_attached_object(self) -> None:
        if not self.attached_entity:
            return
        try:
            transform = self.tf_buffer.lookup_transform(
                self.get_parameter("world_frame").value,
                self.get_parameter("tool_frame").value,
                rclpy.time.Time(),
                timeout=Duration(seconds=0.1),
            )
        except Exception:
            return
        pose = Pose()
        pose.position.x = transform.transform.translation.x
        pose.position.y = transform.transform.translation.y
        pose.position.z = transform.transform.translation.z - 0.03
        pose.orientation.w = 1.0
        self._set_entity_pose(self.attached_entity, pose)

    def _maybe_pick(self) -> None:
        if self.active or not self.detected_objects:
            return
        if not all(name in self.current_joint_state for name in ARM_JOINTS):
            return
        pending = [item for item in self.detected_objects if item["name"] not in self.completed_objects]
        if not pending:
            return
        target = pending[0]
        self.active = True
        try:
            self._run_cycle(target)
        finally:
            self.active = False

    def _run_cycle(self, target: Dict) -> None:
        self._command_gripper(-0.35)

        px = float(target["position"]["x"])
        py = float(target["position"]["y"])
        pz = float(target["position"]["z"])

        approach_pose = self._pose(
            px,
            py,
            pz + float(self.get_parameter("approach_height_offset").value),
        )
        grasp_pose = self._pose(
            px,
            py,
            pz + float(self.get_parameter("grasp_height_offset").value),
        )
        place_xyz = self.get_parameter("place_pose").value
        place_pose = self._pose(place_xyz[0], place_xyz[1], place_xyz[2])

        for pose in [approach_pose, grasp_pose]:
            ik_solution = self._compute_ik(pose)
            if ik_solution is None or not self._send_move_group_goal(ik_solution):
                self.get_logger().warn("MoveIt planning failed for pick trajectory")
                return

        self._command_gripper(0.03)
        self.attached_entity = target["name"]
        self._update_attached_object()

        for pose in [approach_pose, place_pose]:
            ik_solution = self._compute_ik(pose)
            if ik_solution is None or not self._send_move_group_goal(ik_solution):
                self.get_logger().warn("MoveIt planning failed for place trajectory")
                self.attached_entity = None
                return

        placed_pose = Pose()
        placed_pose.position.x = float(place_xyz[0])
        placed_pose.position.y = float(place_xyz[1])
        placed_pose.position.z = 0.417
        placed_pose.orientation.w = 1.0
        self._set_entity_pose(target["name"], placed_pose)
        self.attached_entity = None
        self.completed_objects.add(target["name"])
        self._command_gripper(-0.35)


def main() -> None:
    rclpy.init()
    node = PickPlaceExecutor()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
