import os
import yaml

import xacro
from ament_index_python.packages import PackageNotFoundError, get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, SetEnvironmentVariable, TimerAction
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    pkg_share = get_package_share_directory("mycobot_realsense_pick_sim")
    ros_gz_sim_share = get_package_share_directory("ros_gz_sim")
    mycobot_share = get_package_share_directory("mycobot_description")

    controllers_file = os.path.join(pkg_share, "config", "ros2_controllers.yaml")
    initial_positions_file = os.path.join(pkg_share, "config", "initial_positions.yaml")
    urdf_path = os.path.join(pkg_share, "config", "mycobot_280_pick.urdf.xacro")
    world_path = os.path.join(pkg_share, "worlds", "pick_place_world.sdf")

    robot_description = {"robot_description": xacro.process_file(urdf_path).toxml()}

    with open(initial_positions_file, "r", encoding="utf-8") as stream:
        initial_positions = yaml.safe_load(stream)["initial_positions"]

    resource_entries = [
        mycobot_share,
        os.path.dirname(mycobot_share),
        os.environ.get("IGN_GAZEBO_RESOURCE_PATH", ""),
        os.environ.get("GZ_SIM_RESOURCE_PATH", ""),
        os.environ.get("GAZEBO_MODEL_PATH", ""),
    ]
    gz_resource_path = os.pathsep.join(entry for entry in resource_entries if entry)

    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(ros_gz_sim_share, "launch", "gz_sim.launch.py")
        ),
        launch_arguments={"gz_args": ["-r ", LaunchConfiguration("world")]}.items(),
    )

    rsp = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        name="robot_state_publisher",
        output="screen",
        parameters=[robot_description, {"publish_frequency": 30.0}],
    )

    spawn_robot = Node(
        package="ros_gz_sim",
        executable="create",
        output="screen",
        arguments=[
            "-name",
            "mycobot_280",
            "-topic",
            "robot_description",
            "-x",
            "-0.18",
            "-y",
            "0.0",
            "-z",
            "0.48",
        ],
    )

    bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        output="screen",
        arguments=[
            "/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock",
            "/world/mycobot_pick_world/model/mycobot_280/joint_state@sensor_msgs/msg/JointState[gz.msgs.Model",
            "/realsense_rgbd/image@sensor_msgs/msg/Image@gz.msgs.Image",
            "/realsense_rgbd/camera_info@sensor_msgs/msg/CameraInfo@gz.msgs.CameraInfo",
            "/realsense_rgbd/depth_image@sensor_msgs/msg/Image@gz.msgs.Image",
            "/world/mycobot_pick_world/set_pose@ros_gz_interfaces/srv/SetEntityPose",
        ],
        remappings=[
            ("/world/mycobot_pick_world/model/mycobot_280/joint_state", "/joint_states"),
        ],
    )

    camera_relay = Node(
        package="mycobot_realsense_pick_sim",
        executable="realsense_topic_relay",
        output="screen",
    )

    camera_mount_tf = Node(
        package="tf2_ros",
        executable="static_transform_publisher",
        arguments=["0.16", "0.0", "1.18", "3.14159", "1.12", "0.0", "world", "camera_link"],
    )

    color_optical_tf = Node(
        package="tf2_ros",
        executable="static_transform_publisher",
        arguments=["0", "0", "0", "-1.5708", "0", "-1.5708", "camera_link", "camera_color_optical_frame"],
    )

    depth_optical_tf = Node(
        package="tf2_ros",
        executable="static_transform_publisher",
        arguments=["0", "0", "0", "-1.5708", "0", "-1.5708", "camera_link", "camera_depth_optical_frame"],
    )

    joint_state_broadcaster = TimerAction(
        period=0.2,
        actions=[
            Node(
                package="controller_manager",
                executable="spawner",
                arguments=[
                    "joint_state_broadcaster",
                    "--controller-manager",
                    "/controller_manager",
                    "--param-file",
                    controllers_file,
                ],
                output="screen",
            )
        ],
    )

    arm_controller = TimerAction(
        period=0.4,
        actions=[
            Node(
                package="controller_manager",
                executable="spawner",
                arguments=[
                    "arm_controller",
                    "--controller-manager",
                    "/controller_manager",
                    "--param-file",
                    controllers_file,
                ],
                output="screen",
            )
        ],
    )

    gripper_controller = TimerAction(
        period=0.6,
        actions=[
            Node(
                package="controller_manager",
                executable="spawner",
                arguments=[
                    "gripper_trajectory_controller",
                    "--controller-manager",
                    "/controller_manager",
                    "--param-file",
                    controllers_file,
                ],
                output="screen",
            )
        ],
    )

    startup_hold = TimerAction(
        period=0.8,
        actions=[
            Node(
                package="mycobot_realsense_pick_sim",
                executable="startup_hold_commander",
                output="screen",
                parameters=[
                    {
                        "arm_positions": [
                            float(initial_positions["joint2_to_joint1"]),
                            float(initial_positions["joint3_to_joint2"]),
                            float(initial_positions["joint4_to_joint3"]),
                            float(initial_positions["joint5_to_joint4"]),
                            float(initial_positions["joint6_to_joint5"]),
                            float(initial_positions["joint6output_to_joint6"]),
                        ],
                        "gripper_positions": [float(initial_positions["gripper_controller"])],
                    }
                ],
            )
        ],
    )

    rviz = Node(
        package="rviz2",
        executable="rviz2",
        output="screen",
        arguments=["-d", os.path.join(pkg_share, "config", "moveit.rviz")],
        condition=IfCondition(LaunchConfiguration("rviz")),
    )

    image_view_action = []
    try:
        get_package_share_directory("image_view")
        image_view_action.append(
            Node(
                package="image_view",
                executable="image_view",
                output="screen",
                remappings=[("image", "/camera/color/image_raw")],
                condition=IfCondition(LaunchConfiguration("image_view")),
            )
        )
    except PackageNotFoundError:
        pass

    commander = Node(
        package="mycobot_realsense_pick_sim",
        executable="topic_joint_commander",
        output="screen",
    )

    actions = [
        DeclareLaunchArgument("world", default_value=world_path),
        DeclareLaunchArgument("rviz", default_value="false"),
        DeclareLaunchArgument("image_view", default_value="false"),
        SetEnvironmentVariable("IGN_GAZEBO_RESOURCE_PATH", gz_resource_path),
        SetEnvironmentVariable("GZ_SIM_RESOURCE_PATH", gz_resource_path),
        SetEnvironmentVariable("GAZEBO_MODEL_PATH", gz_resource_path),
        gazebo,
        rsp,
        spawn_robot,
        bridge,
        camera_relay,
        camera_mount_tf,
        color_optical_tf,
        depth_optical_tf,
        joint_state_broadcaster,
        arm_controller,
        gripper_controller,
        startup_hold,
        rviz,
        commander,
    ]
    actions.extend(image_view_action)
    return LaunchDescription(actions)
