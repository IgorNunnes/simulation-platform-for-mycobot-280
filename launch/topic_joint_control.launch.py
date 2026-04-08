import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node


def generate_launch_description():
    pkg_share = get_package_share_directory("mycobot_realsense_pick_sim")

    sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(pkg_share, "launch", "sim_bringup.launch.py")),
        launch_arguments={"rviz": "false"}.items(),
    )

    commander = Node(
        package="mycobot_realsense_pick_sim",
        executable="topic_joint_commander",
        output="screen",
    )

    return LaunchDescription([sim, commander])
