# bridges.launch.py — AMR final project Phase 3
#
# Starts ros_gz_bridge::parameter_bridge with the YAML config that maps
# every Gazebo topic we need into ROS 2 with canonical names.
#
# This file only handles the bridge. Gazebo itself, robot_state_publisher,
# and RViz are composed by full_robot.launch.py (Phase 3 Session 2).

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, LogInfo
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():

    # ----- Launch arguments -----
    use_sim_time = LaunchConfiguration("use_sim_time")

    declare_use_sim_time = DeclareLaunchArgument(
        "use_sim_time",
        default_value="true",
        description="Use /clock from Gazebo as the ROS 2 time source.",
    )

    # ----- Resolve path to the bridge YAML inside the installed share directory -----
    bridge_config = PathJoinSubstitution([
        FindPackageShare("amr_bringup"),
        "config",
        "ros_gz_bridge.yaml",
    ])

    # ----- The bridge node itself -----
    bridge_node = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        name="ros_gz_bridge",
        output="screen",
        parameters=[{
            "config_file": bridge_config,
            "use_sim_time": use_sim_time,
        }],
    )

    return LaunchDescription([
        declare_use_sim_time,
        LogInfo(msg=["Loading ros_gz_bridge with config: ", bridge_config]),
        bridge_node,
    ])
