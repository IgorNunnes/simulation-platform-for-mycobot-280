import json
from typing import Dict, List

import cv2
import numpy as np
import rclpy
from cv_bridge import CvBridge
from geometry_msgs.msg import Pose, PoseArray, PoseStamped
from image_geometry import PinholeCameraModel
from rclpy.node import Node
from rclpy.qos import QoSPresetProfiles
from sensor_msgs.msg import CameraInfo, Image
from std_msgs.msg import String
from tf2_geometry_msgs import do_transform_pose_stamped
from tf2_ros import Buffer, TransformListener
from visualization_msgs.msg import Marker, MarkerArray


COLOR_RANGES = {
    "red_block": [((0, 100, 50), (10, 255, 255)), ((170, 100, 50), (180, 255, 255))],
    "green_block": [((35, 80, 50), (90, 255, 255))],
    "blue_block": [((95, 80, 40), (130, 255, 255))],
    "yellow_block": [((18, 80, 60), (35, 255, 255))],
    "orange_block": [((8, 120, 60), (18, 255, 255))],
}


class ObjectDetector(Node):
    def __init__(self) -> None:
        super().__init__("object_detector")
        qos = QoSPresetProfiles.SENSOR_DATA.value
        self.bridge = CvBridge()
        self.model = PinholeCameraModel()
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)
        self.rgb = None
        self.depth = None
        self.camera_info = None

        self.declare_parameter("world_frame", "world")
        self.declare_parameter("camera_frame", "camera_color_optical_frame")
        self.declare_parameter("table_height", 0.39)
        self.declare_parameter("depth_scale", 1.0)
        self.declare_parameter("min_contour_area", 300.0)

        self.pose_pub = self.create_publisher(PoseArray, "/detected_objects/poses", 10)
        self.marker_pub = self.create_publisher(MarkerArray, "/detected_objects/markers", 10)
        self.json_pub = self.create_publisher(String, "/detected_objects/json", 10)

        self.create_subscription(Image, "/camera/color/image_raw", self._on_rgb, qos)
        self.create_subscription(Image, "/camera/depth/image_rect_raw", self._on_depth, qos)
        self.create_subscription(CameraInfo, "/camera/color/camera_info", self._on_camera_info, qos)

        self.timer = self.create_timer(0.25, self._process)

    def _on_rgb(self, msg: Image) -> None:
        self.rgb = msg

    def _on_depth(self, msg: Image) -> None:
        self.depth = msg

    def _on_camera_info(self, msg: CameraInfo) -> None:
        self.camera_info = msg
        self.model.fromCameraInfo(msg)

    def _read_depth(self, image: np.ndarray, u: int, v: int) -> float:
        patch = image[max(v - 2, 0):v + 3, max(u - 2, 0):u + 3]
        valid = patch[np.isfinite(patch)]
        if valid.size == 0:
            return float("nan")
        depth = float(np.median(valid))
        if image.dtype == np.uint16:
            depth *= 0.001
        return depth * float(self.get_parameter("depth_scale").value)

    def _camera_point_to_world(self, u: int, v: int, depth: float) -> PoseStamped:
        ray = self.model.projectPixelTo3dRay((u, v))
        point = np.array(ray) * depth
        pose = PoseStamped()
        pose.header.frame_id = self.get_parameter("camera_frame").value
        pose.header.stamp = self.get_clock().now().to_msg()
        pose.pose.position.x = float(point[0])
        pose.pose.position.y = float(point[1])
        pose.pose.position.z = float(point[2])
        pose.pose.orientation.w = 1.0
        transform = self.tf_buffer.lookup_transform(
            self.get_parameter("world_frame").value,
            pose.header.frame_id,
            rclpy.time.Time(),
            timeout=rclpy.duration.Duration(seconds=0.2),
        )
        return do_transform_pose_stamped(pose, transform)

    def _process(self) -> None:
        if self.rgb is None or self.depth is None or self.camera_info is None:
            return

        try:
            rgb = self.bridge.imgmsg_to_cv2(self.rgb, desired_encoding="bgr8")
            depth = self.bridge.imgmsg_to_cv2(self.depth)
        except Exception as exc:
            self.get_logger().warn(f"Failed to decode images: {exc}")
            return

        hsv = cv2.cvtColor(rgb, cv2.COLOR_BGR2HSV)
        detections: List[Dict] = []

        for name, ranges in COLOR_RANGES.items():
            mask = None
            for lower, upper in ranges:
                part = cv2.inRange(hsv, np.array(lower, dtype=np.uint8), np.array(upper, dtype=np.uint8))
                mask = part if mask is None else cv2.bitwise_or(mask, part)
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            for contour in contours:
                area = cv2.contourArea(contour)
                if area < float(self.get_parameter("min_contour_area").value):
                    continue
                epsilon = 0.03 * cv2.arcLength(contour, True)
                approx = cv2.approxPolyDP(contour, epsilon, True)
                if len(approx) < 4 or len(approx) > 8:
                    continue
                moments = cv2.moments(contour)
                if moments["m00"] == 0.0:
                    continue
                u = int(moments["m10"] / moments["m00"])
                v = int(moments["m01"] / moments["m00"])
                depth_value = self._read_depth(depth, u, v)
                if not np.isfinite(depth_value) or depth_value <= 0.02 or depth_value > 2.0:
                    continue
                try:
                    world_pose = self._camera_point_to_world(u, v, depth_value)
                except Exception:
                    continue
                world_pose.pose.position.z = float(self.get_parameter("table_height").value) + 0.02
                detections.append(
                    {
                        "name": name,
                        "color": name.replace("_block", ""),
                        "pose": world_pose.pose,
                    }
                )
                break

        pose_array = PoseArray()
        pose_array.header.frame_id = self.get_parameter("world_frame").value
        pose_array.header.stamp = self.get_clock().now().to_msg()
        marker_array = MarkerArray()
        payload = []

        for index, detection in enumerate(detections):
            pose = detection["pose"]
            pose_array.poses.append(pose)
            marker = Marker()
            marker.header = pose_array.header
            marker.ns = "detected_objects"
            marker.id = index
            marker.type = Marker.CUBE
            marker.action = Marker.ADD
            marker.pose = pose
            marker.scale.x = 0.04
            marker.scale.y = 0.04
            marker.scale.z = 0.04
            marker.color.a = 0.8
            marker.color.r = 0.2
            marker.color.g = 0.9
            marker.color.b = 0.4
            marker_array.markers.append(marker)
            payload.append(
                {
                    "name": detection["name"],
                    "color": detection["color"],
                    "position": {
                        "x": pose.position.x,
                        "y": pose.position.y,
                        "z": pose.position.z,
                    },
                }
            )

        self.pose_pub.publish(pose_array)
        self.marker_pub.publish(marker_array)
        self.json_pub.publish(String(data=json.dumps(payload)))


def main() -> None:
    rclpy.init()
    node = ObjectDetector()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
