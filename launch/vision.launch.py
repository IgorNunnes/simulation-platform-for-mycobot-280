from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription(
        [
            Node(
                package="mycobot_realsense_pick_sim",
                executable="object_detector",
                output="screen",
            )
        ]
    )
