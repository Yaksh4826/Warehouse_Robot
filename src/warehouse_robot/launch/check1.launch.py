import os
from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, ExecuteProcess
from launch.launch_description_sources import PythonLaunchDescriptionSource

from launch_ros.actions import Node
from launch.substitutions import Command
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    pkg_path = get_package_share_directory('warehouse_robot')

    # ================= WORLD =================
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            os.path.join(
                get_package_share_directory('ros_gz_sim'),
                'launch',
                'gz_sim.launch.py'
            )
        ]),
        launch_arguments={
            'gz_args': '-r -s ' + os.path.join(pkg_path, 'worlds', 'warehouse_v1.sdf')
        }.items()
    )

    # ================= ROBOT DESCRIPTION =================
    urdf_file = os.path.join(pkg_path, 'urdf', 'robot.urdf.xacro')

    robot_description = ParameterValue(
        Command(['xacro ', urdf_file]),
        value_type=str
    )

    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{'robot_description': robot_description}],
        output='screen'
    )

    # ================= SPAWN ROBOT =================
    spawn_robot = ExecuteProcess(
        cmd=[
    'ros2', 'run', 'ros_gz_sim', 'create',
    '-name', 'warehouse_bot',
    '-topic', 'robot_description',
    '-x', '0', '-y', '0', '-z', '0.5'
],
        output='screen'
    )

    # ================= BRIDGE =================
    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=[
            '/scan@sensor_msgs/msg/LaserScan@gz.msgs.LaserScan'
        ],
        output='screen'
    )
    print("URDF FILE PATH:", urdf_file)

    return LaunchDescription([
        gazebo,
        robot_state_publisher,
        spawn_robot,
        bridge
    ])