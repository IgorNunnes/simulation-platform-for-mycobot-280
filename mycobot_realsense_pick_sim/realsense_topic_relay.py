from copy import deepcopy

import rclpy
from cv_bridge import CvBridge
from rclpy.node import Node
from rclpy.qos import QoSPresetProfiles
from sensor_msgs.msg import CameraInfo, Image


class RealSenseTopicRelay(Node):
    def __init__(self) -> None:
        super().__init__("realsense_topic_relay")
        qos = QoSPresetProfiles.SENSOR_DATA.value
        self.bridge = CvBridge()

        self.declare_parameter("raw_color_topic", "/realsense_rgbd/image")
        self.declare_parameter("raw_camera_info_topic", "/realsense_rgbd/camera_info")
        self.declare_parameter("raw_depth_topic", "/realsense_rgbd/depth_image")
        self.declare_parameter("color_frame_id", "camera_color_optical_frame")
        self.declare_parameter("depth_frame_id", "camera_depth_optical_frame")

        self.color_pub = self.create_publisher(Image, "/camera/color/image_raw", qos)
        self.color_info_pub = self.create_publisher(CameraInfo, "/camera/color/camera_info", qos)
        self.depth_pub = self.create_publisher(Image, "/camera/depth/image_rect_raw", qos)
        self.depth_info_pub = self.create_publisher(CameraInfo, "/camera/depth/camera_info", qos)

        self.last_camera_info = None

        self.create_subscription(
            Image,
            self.get_parameter("raw_color_topic").value,
            self._on_color,
            qos,
        )
        self.create_subscription(
            CameraInfo,
            self.get_parameter("raw_camera_info_topic").value,
            self._on_camera_info,
            qos,
        )
        self.create_subscription(
            Image,
            self.get_parameter("raw_depth_topic").value,
            self._on_depth,
            qos,
        )

    def _on_camera_info(self, msg: CameraInfo) -> None:
        self.last_camera_info = msg
        color_info = deepcopy(msg)
        color_info.header.frame_id = self.get_parameter("color_frame_id").value
        depth_info = deepcopy(msg)
        depth_info.header.frame_id = self.get_parameter("depth_frame_id").value
        self.color_info_pub.publish(color_info)
        self.depth_info_pub.publish(depth_info)

    def _on_color(self, msg: Image) -> None:
        relay = deepcopy(msg)
        relay.header.frame_id = self.get_parameter("color_frame_id").value
        self.color_pub.publish(relay)

    def _on_depth(self, msg: Image) -> None:
        relay = deepcopy(msg)
        relay.header.frame_id = self.get_parameter("depth_frame_id").value
        self.depth_pub.publish(relay)
        if self.last_camera_info is not None:
            depth_info = deepcopy(self.last_camera_info)
            depth_info.header = relay.header
            depth_info.header.frame_id = self.get_parameter("depth_frame_id").value
            self.depth_info_pub.publish(depth_info)


def main() -> None:
    rclpy.init()
    node = RealSenseTopicRelay()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
