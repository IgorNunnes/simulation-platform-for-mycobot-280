from glob import glob
import os

from setuptools import setup


package_name = "mycobot_realsense_pick_sim"


setup(
    name=package_name,
    version="0.1.0",
    packages=[package_name],
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml", ".setup_assistant", "README.md"]),
        (os.path.join("share", package_name, "launch"), glob("launch/*.py")),
        (os.path.join("share", package_name, "config"), glob("config/*")),
        (os.path.join("share", package_name, "worlds"), glob("worlds/*")),
        (os.path.join("share", package_name, "rviz"), glob("rviz/*")),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="Igor",
    maintainer_email="igor@local",
    description="Isolated myCobot 280 M5 Gazebo Sim + MoveIt2 pick and place demo.",
    license="MIT",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": [
            "realsense_topic_relay = mycobot_realsense_pick_sim.realsense_topic_relay:main",
            "aruco_object_detector = mycobot_realsense_pick_sim.aruco_object_detector:main",
            "object_detector = mycobot_realsense_pick_sim.object_detector:main",
            "pick_place_executor = mycobot_realsense_pick_sim.pick_place_executor:main",
            "topic_joint_commander = mycobot_realsense_pick_sim.topic_joint_commander:main",
            "topic_pose_commander = mycobot_realsense_pick_sim.topic_pose_commander:main",
            "startup_hold_commander = mycobot_realsense_pick_sim.startup_hold_commander:main",
        ],
    },
)
