import os
from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import (
    IncludeLaunchDescription,
    ExecuteProcess,
    DeclareLaunchArgument,
    TimerAction,
    OpaqueFunction,
)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, LaunchConfiguration

from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def _build_nodes(context, *args, **kwargs):
    pkg_path = get_package_share_directory('warehouse_robot')

    use_sim_time = LaunchConfiguration('use_sim_time').perform(context)
    headless = LaunchConfiguration('headless').perform(context).lower() == 'true'
    want_rviz = LaunchConfiguration('rviz').perform(context).lower() == 'true'
    static_map_odom = LaunchConfiguration('static_map_odom').perform(context).lower() == 'true'

    world_path = os.path.join(pkg_path, 'worlds', 'warehouse_v1.sdf')
    gz_args = f'-r -v 3 {world_path}'
    if headless:
        gz_args = f'-r -s -v 3 {world_path}'

    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            os.path.join(
                get_package_share_directory('ros_gz_sim'),
                'launch',
                'gz_sim.launch.py'
            )
        ]),
        launch_arguments={'gz_args': gz_args}.items()
    )

    urdf_file = os.path.join(pkg_path, 'urdf', 'robot.urdf.xacro')
    robot_description = ParameterValue(Command(['xacro ', urdf_file]), value_type=str)

    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{
            'robot_description': robot_description,
            'use_sim_time': use_sim_time == 'true',
        }],
        output='screen'
    )

    spawn_robot = TimerAction(
        period=3.0,
        actions=[
            ExecuteProcess(
                cmd=[
                    'ros2', 'run', 'ros_gz_sim', 'create',
                    '-name', 'warehouse_bot',
                    '-topic', 'robot_description',
                    '-x', '2', '-y', '2', '-z', '0.15',
                ],
                output='screen'
            )
        ]
    )

    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=[
            '/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock',
            '/cmd_vel@geometry_msgs/msg/Twist]gz.msgs.Twist',
            '/odom@nav_msgs/msg/Odometry[gz.msgs.Odometry',
            '/tf@tf2_msgs/msg/TFMessage[gz.msgs.Pose_V',
            '/joint_states@sensor_msgs/msg/JointState[gz.msgs.Model',
            '/scan@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan',
        ],
        parameters=[{'use_sim_time': use_sim_time == 'true'}],
        output='screen'
    )

    static_map_to_odom = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='static_map_to_odom',
        arguments=['0', '0', '0', '0', '0', '0', 'map', 'odom'],
        parameters=[{'use_sim_time': use_sim_time == 'true'}],
        output='screen'
    )

    actions = [
        gazebo,
        robot_state_publisher,
        bridge,
        spawn_robot,
    ]

    if static_map_odom:
        actions.append(static_map_to_odom)

    if want_rviz:
        rviz_config = os.path.join(pkg_path, 'config', 'view_robot.rviz')
        actions.append(
            Node(
                package='rviz2',
                executable='rviz2',
                arguments=['-d', rviz_config],
                parameters=[{'use_sim_time': use_sim_time == 'true'}],
                output='screen'
            )
        )

    return actions


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument(
            'use_sim_time', default_value='true',
            description='Use Gazebo simulation clock for all ROS nodes.'
        ),
        DeclareLaunchArgument(
            'headless', default_value='false',
            description='If true, run Gazebo without the GUI client.'
        ),
        DeclareLaunchArgument(
            'rviz', default_value='true',
            description='Launch RViz2 alongside Gazebo.'
        ),
        DeclareLaunchArgument(
            'static_map_odom', default_value='true',
            description=(
                'Publish identity map->odom. Set to false when SLAM Toolbox '
                'or AMCL is running - they own map->odom and a second '
                'publisher causes pose jitter.'
            )
        ),
        OpaqueFunction(function=_build_nodes),
    ])
