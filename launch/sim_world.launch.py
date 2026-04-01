import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    pkg_share = get_package_share_directory("mycobot_realsense_pick_sim")
    ros_gz_sim = get_package_share_directory("ros_gz_sim")
    default_world = os.path.join(pkg_share, "worlds", "pick_place_world.sdf")

    gz_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(ros_gz_sim, "launch", "gz_sim.launch.py")
        ),
        launch_arguments={"gz_args": ["-r ", LaunchConfiguration("world")]}.items(),
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument("world", default_value=default_world),
            gz_launch,
        ]
    )
