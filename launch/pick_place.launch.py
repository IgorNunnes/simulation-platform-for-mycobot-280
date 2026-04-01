import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from moveit_configs_utils import MoveItConfigsBuilder
from moveit_configs_utils.launches import generate_move_group_launch, generate_moveit_rviz_launch


def generate_launch_description():
    pkg_share = get_package_share_directory("mycobot_realsense_pick_sim")
    moveit_config = (
        MoveItConfigsBuilder("mycobot_280_pick", package_name="mycobot_realsense_pick_sim")
        .robot_description(file_path="config/mycobot_280_pick.urdf.xacro")
        .robot_description_semantic(file_path="config/mycobot_280_pick.srdf")
        .trajectory_execution(file_path="config/moveit_controllers.yaml")
        .robot_description_kinematics(file_path="config/kinematics.yaml")
        .joint_limits(file_path="config/joint_limits.yaml")
        .pilz_cartesian_limits(file_path="config/pilz_cartesian_limits.yaml")
        .to_moveit_configs()
    )

    vision = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(pkg_share, "launch", "vision.launch.py"))
    )

    executor = Node(
        package="mycobot_realsense_pick_sim",
        executable="pick_place_executor",
        output="screen",
        parameters=[moveit_config.to_dict()],
    )

    ld = LaunchDescription()
    for entity in generate_move_group_launch(moveit_config).entities:
        ld.add_action(entity)
    for entity in generate_moveit_rviz_launch(moveit_config).entities:
        ld.add_action(entity)
    ld.add_action(vision)
    ld.add_action(executor)
    return ld
