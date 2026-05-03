# full_robot.launch.py — AMR final project Phase 3
#
# Master launch file: brings up the whole local simulation stack:
#   1. Gazebo Harmonic loading test_world.sdf
#   2. ros_gz_bridge (via bridges.launch.py) — Gazebo <-> ROS 2 topics
#   3. robot_state_publisher — emits TF for the robot structure
#   4. (optional) RViz with Phase 3 config
#
# Usage:
#   ros2 launch amr_bringup full_robot.launch.py
#   ros2 launch amr_bringup full_robot.launch.py rviz:=false

from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    SetEnvironmentVariable,
    LogInfo,
)
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import (
    Command,
    FindExecutable,
    LaunchConfiguration,
    PathJoinSubstitution,
)
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from launch_ros.descriptions import ParameterValue


def generate_launch_description():

    # ---------- Launch arguments ----------
    use_sim_time = LaunchConfiguration("use_sim_time")
    rviz         = LaunchConfiguration("rviz")
    world_file   = LaunchConfiguration("world")

    declare_use_sim_time = DeclareLaunchArgument(
        "use_sim_time", default_value="true",
        description="Use /clock from Gazebo as ROS 2 time source.",
    )
    declare_rviz = DeclareLaunchArgument(
        "rviz", default_value="true",
        description="Start RViz with the Phase 3 config.",
    )
    declare_world = DeclareLaunchArgument(
        "world",
        default_value=PathJoinSubstitution([
            FindPackageShare("amr_town_world"),
            "worlds", "test_world.sdf",
        ]),
        description="Absolute path to the Gazebo world SDF file.",
    )

    # ---------- Environment ----------
    # LIBGL_ALWAYS_SOFTWARE=1 is required for VirtualBox SVGA3D
    # compatibility with Gazebo Harmonic (handoff doc §3.5).
    set_libgl_software = SetEnvironmentVariable(
        "LIBGL_ALWAYS_SOFTWARE", "1"
    )

    # ---------- Gazebo (via ros_gz_sim launch) ----------
    gz_sim_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            PathJoinSubstitution([
                FindPackageShare("ros_gz_sim"),
                "launch", "gz_sim.launch.py",
            ])
        ]),
        launch_arguments={
            "gz_args": [world_file, " -r -v 3"],
        }.items(),
    )

    # ---------- ros_gz_bridge (include existing bridges.launch.py) ----------
    bridges_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            PathJoinSubstitution([
                FindPackageShare("amr_bringup"),
                "launch", "bridges.launch.py",
            ])
        ]),
        launch_arguments={
            "use_sim_time": use_sim_time,
        }.items(),
    )

    # ---------- robot_state_publisher ----------
    # Expand the xacro at launch time -> pass URDF string as parameter.
    urdf_xacro_path = PathJoinSubstitution([
        FindPackageShare("amr_robot_description"),
        "urdf", "service_robot.urdf.xacro",
    ])
    robot_description_content = Command([
        FindExecutable(name="xacro"), " ", urdf_xacro_path,
    ])
    robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        name="robot_state_publisher",
        output="screen",
        parameters=[{
            "robot_description": ParameterValue(robot_description_content, value_type=str),
            "use_sim_time": use_sim_time,
        }],
    )

    # ---------- RViz (conditional) ----------
    rviz_config = PathJoinSubstitution([
        FindPackageShare("amr_bringup"),
        "config", "rviz_phase3.rviz",
    ])
    rviz_node = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="screen",
        arguments=["-d", rviz_config],
        parameters=[{"use_sim_time": use_sim_time}],
        condition=IfCondition(rviz),
    )

    return LaunchDescription([
        declare_use_sim_time,
        declare_rviz,
        declare_world,
        set_libgl_software,
        LogInfo(msg=["Launching AMR full robot stack (Phase 3)..."]),
        gz_sim_launch,
        bridges_launch,
        robot_state_publisher,
        rviz_node,
    ])
