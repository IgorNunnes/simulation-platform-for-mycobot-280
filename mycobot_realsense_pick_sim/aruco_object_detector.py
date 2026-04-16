import json
from typing import Dict, List, Tuple

import cv2
import numpy as np
import rclpy
from cv_bridge import CvBridge
from geometry_msgs.msg import Pose, PoseArray, PoseStamped
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.qos import QoSPresetProfiles
from rclpy.duration import Duration
from sensor_msgs.msg import CameraInfo, Image
from std_msgs.msg import String
from tf2_geometry_msgs import do_transform_pose_stamped
from tf2_ros import Buffer, TransformListener
from visualization_msgs.msg import Marker, MarkerArray


DEFAULT_MARKER_ID_TO_NAME = {
    "0": "red_block",
    "1": "green_block",
    "2": "blue_block",
    "3": "yellow_block",
    "4": "orange_block",
}

DISPLAY_COLORS = {
    "red_block": (0.85, 0.15, 0.15),
    "green_block": (0.15, 0.75, 0.2),
    "blue_block": (0.15, 0.25, 0.85),
    "yellow_block": (0.85, 0.78, 0.15),
    "orange_block": (0.90, 0.45, 0.15),
}


def _rotation_matrix_to_quaternion(rotation: np.ndarray) -> Tuple[float, float, float, float]:
    trace = float(rotation[0, 0] + rotation[1, 1] + rotation[2, 2])
    if trace > 0.0:
        scale = 0.5 / np.sqrt(trace + 1.0)
        qw = 0.25 / scale
        qx = (rotation[2, 1] - rotation[1, 2]) * scale
        qy = (rotation[0, 2] - rotation[2, 0]) * scale
        qz = (rotation[1, 0] - rotation[0, 1]) * scale
        return qx, qy, qz, qw

    if rotation[0, 0] > rotation[1, 1] and rotation[0, 0] > rotation[2, 2]:
        scale = 2.0 * np.sqrt(1.0 + rotation[0, 0] - rotation[1, 1] - rotation[2, 2])
        qw = (rotation[2, 1] - rotation[1, 2]) / scale
        qx = 0.25 * scale
        qy = (rotation[0, 1] + rotation[1, 0]) / scale
        qz = (rotation[0, 2] + rotation[2, 0]) / scale
        return qx, qy, qz, qw

    if rotation[1, 1] > rotation[2, 2]:
        scale = 2.0 * np.sqrt(1.0 + rotation[1, 1] - rotation[0, 0] - rotation[2, 2])
        qw = (rotation[0, 2] - rotation[2, 0]) / scale
        qx = (rotation[0, 1] + rotation[1, 0]) / scale
        qy = 0.25 * scale
        qz = (rotation[1, 2] + rotation[2, 1]) / scale
        return qx, qy, qz, qw

    scale = 2.0 * np.sqrt(1.0 + rotation[2, 2] - rotation[0, 0] - rotation[1, 1])
    qw = (rotation[1, 0] - rotation[0, 1]) / scale
    qx = (rotation[0, 2] + rotation[2, 0]) / scale
    qy = (rotation[1, 2] + rotation[2, 1]) / scale
    qz = 0.25 * scale
    return qx, qy, qz, qw


class ArucoObjectDetector(Node):
    def __init__(self) -> None:
        super().__init__("aruco_object_detector")
        if not hasattr(cv2, "aruco"):
            raise RuntimeError("OpenCV ArUco module is not available in this environment")

        qos = QoSPresetProfiles.SENSOR_DATA.value
        self.bridge = CvBridge()
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)
        self.camera_info = None
        self.camera_matrix = None
        self.dist_coeffs = None

        self.declare_parameter("image_topic", "/camera/color/image_raw")
        self.declare_parameter("camera_info_topic", "/camera/color/camera_info")
        self.declare_parameter("world_frame", "world")
        self.declare_parameter("camera_frame", "camera_color_optical_frame")
        self.declare_parameter("aruco_dictionary", "DICT_4X4_50")
        self.declare_parameter("marker_size_m", 0.032)
        self.declare_parameter("object_center_offset_m", -0.02)
        self.declare_parameter(
            "marker_id_to_name_json",
            json.dumps(DEFAULT_MARKER_ID_TO_NAME),
        )
        self.declare_parameter("publish_debug_image", True)
        self.declare_parameter("debug_image_topic", "/detected_objects/debug_image")

        self.pose_pub = self.create_publisher(PoseArray, "/detected_objects/poses", 10)
        self.marker_pub = self.create_publisher(MarkerArray, "/detected_objects/markers", 10)
        self.json_pub = self.create_publisher(String, "/detected_objects/json", 10)
        self.debug_pub = self.create_publisher(
            Image,
            self.get_parameter("debug_image_topic").value,
            10,
        )

        self.marker_id_to_name = self._parse_marker_map(
            self.get_parameter("marker_id_to_name_json").value
        )
        self.dictionary = self._make_dictionary(self.get_parameter("aruco_dictionary").value)
        self.detector_params = self._make_detector_parameters()
        self.detector = self._make_detector()

        self.create_subscription(
            CameraInfo,
            self.get_parameter("camera_info_topic").value,
            self._on_camera_info,
            qos,
        )
        self.create_subscription(
            Image,
            self.get_parameter("image_topic").value,
            self._on_image,
            qos,
        )
        self.get_logger().info(
            "Listening for ArUco markers on "
            f"{self.get_parameter('image_topic').value} and publishing detections in "
            f"{self.get_parameter('world_frame').value}"
        )

    def _parse_marker_map(self, raw: str) -> Dict[int, str]:
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid marker_id_to_name_json parameter: {exc}") from exc
        return {int(key): str(value) for key, value in parsed.items()}

    def _make_dictionary(self, dictionary_name: str):
        if not hasattr(cv2.aruco, dictionary_name):
            raise ValueError(f"Unknown ArUco dictionary: {dictionary_name}")
        dictionary_id = getattr(cv2.aruco, dictionary_name)
        if hasattr(cv2.aruco, "getPredefinedDictionary"):
            return cv2.aruco.getPredefinedDictionary(dictionary_id)
        return cv2.aruco.Dictionary_get(dictionary_id)

    def _make_detector_parameters(self):
        if hasattr(cv2.aruco, "DetectorParameters"):
            return cv2.aruco.DetectorParameters()
        return cv2.aruco.DetectorParameters_create()

    def _make_detector(self):
        if hasattr(cv2.aruco, "ArucoDetector"):
            return cv2.aruco.ArucoDetector(self.dictionary, self.detector_params)
        return None

    def _detect_markers(self, image: np.ndarray):
        if self.detector is not None:
            return self.detector.detectMarkers(image)
        return cv2.aruco.detectMarkers(image, self.dictionary, parameters=self.detector_params)

    def _on_camera_info(self, msg: CameraInfo) -> None:
        self.camera_info = msg
        self.camera_matrix = np.array(msg.k, dtype=np.float64).reshape(3, 3)
        self.dist_coeffs = np.array(msg.d, dtype=np.float64)

    def _make_pose_stamped(
        self,
        rotation_matrix: np.ndarray,
        translation_vector: np.ndarray,
        frame_id: str,
        stamp,
    ) -> PoseStamped:
        pose = PoseStamped()
        pose.header.frame_id = frame_id or self.get_parameter("camera_frame").value
        pose.header.stamp = stamp
        pose.pose.position.x = float(translation_vector[0])
        pose.pose.position.y = float(translation_vector[1])
        pose.pose.position.z = float(translation_vector[2])
        qx, qy, qz, qw = _rotation_matrix_to_quaternion(rotation_matrix)
        pose.pose.orientation.x = qx
        pose.pose.orientation.y = qy
        pose.pose.orientation.z = qz
        pose.pose.orientation.w = qw
        return pose

    def _world_pose_from_marker(
        self,
        rvec: np.ndarray,
        tvec: np.ndarray,
        frame_id: str,
        stamp,
    ) -> Pose:
        rotation_matrix, _ = cv2.Rodrigues(rvec)
        marker_translation = tvec.reshape(3)
        center_offset = np.array(
            [0.0, 0.0, float(self.get_parameter("object_center_offset_m").value)],
            dtype=np.float64,
        )
        object_center_camera = marker_translation + rotation_matrix @ center_offset

        pose = self._make_pose_stamped(rotation_matrix, object_center_camera, frame_id, stamp)
        transform = self.tf_buffer.lookup_transform(
            self.get_parameter("world_frame").value,
            pose.header.frame_id,
            rclpy.time.Time(),
            timeout=Duration(seconds=0.2),
        )
        return do_transform_pose_stamped(pose, transform).pose

    def _estimate_marker_poses(self, corners, marker_size: float):
        if hasattr(cv2.aruco, "estimatePoseSingleMarkers"):
            return cv2.aruco.estimatePoseSingleMarkers(
                corners,
                marker_size,
                self.camera_matrix,
                self.dist_coeffs,
            )

        half_size = marker_size * 0.5
        object_points = np.array(
            [
                [-half_size, half_size, 0.0],
                [half_size, half_size, 0.0],
                [half_size, -half_size, 0.0],
                [-half_size, -half_size, 0.0],
            ],
            dtype=np.float32,
        )

        rvecs = []
        tvecs = []
        for marker_corners in corners:
            image_points = marker_corners.reshape(4, 2).astype(np.float32)
            success, rvec, tvec = cv2.solvePnP(
                object_points,
                image_points,
                self.camera_matrix,
                self.dist_coeffs,
                flags=getattr(cv2, "SOLVEPNP_IPPE_SQUARE", cv2.SOLVEPNP_ITERATIVE),
            )
            if not success:
                raise RuntimeError("solvePnP failed for one or more markers")
            rvecs.append(rvec)
            tvecs.append(tvec)
        return np.array(rvecs), np.array(tvecs), None

    def _publish_empty(self) -> None:
        pose_array = PoseArray()
        pose_array.header.frame_id = self.get_parameter("world_frame").value
        pose_array.header.stamp = self.get_clock().now().to_msg()
        self.pose_pub.publish(pose_array)
        delete_all = Marker()
        delete_all.header = pose_array.header
        delete_all.action = Marker.DELETEALL
        self.marker_pub.publish(MarkerArray(markers=[delete_all]))
        self.json_pub.publish(String(data="[]"))

    def _on_image(self, msg: Image) -> None:
        if self.camera_matrix is None or self.dist_coeffs is None:
            return

        try:
            bgr = self.bridge.imgmsg_to_cv2(msg, desired_encoding="bgr8")
        except Exception as exc:
            self.get_logger().warn(f"Failed to decode RGB image: {exc}")
            return

        corners, ids, _ = self._detect_markers(bgr)
        if ids is None or len(ids) == 0:
            self._publish_empty()
            if self.get_parameter("publish_debug_image").value:
                self.debug_pub.publish(self.bridge.cv2_to_imgmsg(bgr, encoding="bgr8"))
            return

        marker_size = float(self.get_parameter("marker_size_m").value)
        try:
            rvecs, tvecs, _ = self._estimate_marker_poses(corners, marker_size)
        except Exception as exc:
            self.get_logger().warn(f"ArUco pose estimation failed: {exc}")
            return

        pose_array = PoseArray()
        pose_array.header.frame_id = self.get_parameter("world_frame").value
        pose_array.header.stamp = msg.header.stamp
        marker_array = MarkerArray()
        payload: List[Dict] = []

        debug = bgr.copy()
        cv2.aruco.drawDetectedMarkers(debug, corners, ids)

        for index, marker_id in enumerate(ids.flatten().tolist()):
            marker_name = self.marker_id_to_name.get(marker_id, f"aruco_{marker_id}")
            rvec = rvecs[index].reshape(3, 1)
            tvec = tvecs[index].reshape(3, 1)
            try:
                world_pose = self._world_pose_from_marker(
                    rvec,
                    tvec,
                    msg.header.frame_id,
                    msg.header.stamp,
                )
            except Exception as exc:
                self.get_logger().warn(f"Failed to transform marker {marker_id} to world: {exc}")
                continue

            pose_array.poses.append(world_pose)

            marker = Marker()
            marker.header = pose_array.header
            marker.ns = "detected_objects"
            marker.id = int(marker_id)
            marker.type = Marker.CUBE
            marker.action = Marker.ADD
            marker.pose = world_pose
            marker.scale.x = 0.04
            marker.scale.y = 0.04
            marker.scale.z = 0.04
            color = DISPLAY_COLORS.get(marker_name, (0.2, 0.9, 0.4))
            marker.color.a = 0.85
            marker.color.r = float(color[0])
            marker.color.g = float(color[1])
            marker.color.b = float(color[2])
            marker_array.markers.append(marker)

            payload.append(
                {
                    "id": int(marker_id),
                    "name": marker_name,
                    "position": {
                        "x": world_pose.position.x,
                        "y": world_pose.position.y,
                        "z": world_pose.position.z,
                    },
                    "orientation": {
                        "x": world_pose.orientation.x,
                        "y": world_pose.orientation.y,
                        "z": world_pose.orientation.z,
                        "w": world_pose.orientation.w,
                    },
                }
            )

            if self.get_parameter("publish_debug_image").value:
                cv2.drawFrameAxes(
                    debug,
                    self.camera_matrix,
                    self.dist_coeffs,
                    rvec,
                    tvec,
                    marker_size * 0.5,
                )
                corner_set = corners[index].reshape(-1, 2)
                center = tuple(np.mean(corner_set, axis=0).astype(int))
                cv2.putText(
                    debug,
                    f"{marker_name} ({marker_id})",
                    (center[0] - 60, center[1] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (0, 255, 0),
                    1,
                    cv2.LINE_AA,
                )

        self.pose_pub.publish(pose_array)
        self.marker_pub.publish(marker_array)
        self.json_pub.publish(String(data=json.dumps(payload)))
        if self.get_parameter("publish_debug_image").value:
            debug_msg = self.bridge.cv2_to_imgmsg(debug, encoding="bgr8")
            debug_msg.header = msg.header
            self.debug_pub.publish(debug_msg)


def main() -> None:
    rclpy.init()
    node = None
    try:
        node = ArucoObjectDetector()
        try:
            rclpy.spin(node)
        except (KeyboardInterrupt, ExternalShutdownException):
            pass
    finally:
        if node is not None:
            node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
