import os

import xacro
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node


def generate_launch_description():
    pkg_share = get_package_share_directory("mycobot_realsense_pick_sim")
    mycobot_share = get_package_share_directory("mycobot_description")
    mycobot_280_share = get_package_share_directory("mycobot_280")
    model_path = os.path.join(
        mycobot_share,
        "urdf",
        "mycobot_280_m5",
        "mycobot_280_m5_adaptive_gripper.urdf",
    )
    robot_description = xacro.process_file(model_path).toxml()

    sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(pkg_share, "launch", "sim_bringup.launch.py")),
        launch_arguments={"rviz": "false"}.items(),
    )

    gui = Node(
        package="joint_state_publisher_gui",
        executable="joint_state_publisher_gui",
        output="screen",
        parameters=[{"robot_description": robot_description}],
        remappings=[("joint_states", "/slider_joint_states")],
    )

    rviz = Node(
        package="rviz2",
        executable="rviz2",
        output="screen",
        arguments=["-d", os.path.join(mycobot_280_share, "config", "mycobot.rviz")],
    )

    slider_bridge = Node(
        package="mycobot_280",
        executable="slider_control_adaptive_gripper_sim",
        output="screen",
        parameters=[{"input_topic": "/slider_joint_states"}],
    )

    return LaunchDescription([sim, gui, rviz, slider_bridge])
