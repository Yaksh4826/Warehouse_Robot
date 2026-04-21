import os
from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import (
    IncludeLaunchDescription,
    DeclareLaunchArgument,
    TimerAction,
)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration

from launch_ros.actions import Node


def generate_launch_description():
    pkg_path = get_package_share_directory('warehouse_robot')
    slam_params = os.path.join(pkg_path, 'config', 'slam_toolbox.yaml')

    use_sim_time = LaunchConfiguration('use_sim_time')
    headless = LaunchConfiguration('headless')
    rviz = LaunchConfiguration('rviz')

    declare_sim_time = DeclareLaunchArgument(
        'use_sim_time', default_value='true'
    )
    declare_headless = DeclareLaunchArgument(
        'headless', default_value='false'
    )
    declare_rviz = DeclareLaunchArgument(
        'rviz', default_value='true'
    )

    # ========== BRING UP SIM + ROBOT (no static map->odom) ==========
    # static_map_odom:=false is critical here — slam_toolbox will own
    # map -> odom. Two publishers on that edge cause pose jitter.
    bringup = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_path, 'launch', 'check1.launch.py')
        ),
        launch_arguments={
            'use_sim_time': use_sim_time,
            'headless': headless,
            'rviz': rviz,
            'static_map_odom': 'false',
        }.items()
    )

    # ========== SLAM TOOLBOX (async online mapping) ==========
    # async_slam_toolbox_node is a lifecycle node. In Jazzy it does NOT
    # auto-transition to "active" — it needs to be configured + activated
    # by a nav2 lifecycle_manager.
    # Delay a bit so /scan, /odom and TF (odom->base_link) are flowing
    # before the scan-matcher initialises.
    slam_node = Node(
        package='slam_toolbox',
        executable='async_slam_toolbox_node',
        name='slam_toolbox',
        output='screen',
        parameters=[
            slam_params,
            {'use_sim_time': use_sim_time},
        ],
    )

    slam = TimerAction(period=5.0, actions=[slam_node])

    slam_lifecycle_mgr = TimerAction(
        period=8.0,
        actions=[
            Node(
                package='nav2_lifecycle_manager',
                executable='lifecycle_manager',
                name='lifecycle_manager_slam',
                output='screen',
                parameters=[{
                    'use_sim_time': use_sim_time,
                    'autostart': True,
                    'bond_timeout': 0.0,  # slam_toolbox doesn't create a bond
                    'node_names': ['slam_toolbox'],
                }],
            )
        ]
    )

    return LaunchDescription([
        declare_sim_time,
        declare_headless,
        declare_rviz,
        bringup,
        slam,
        slam_lifecycle_mgr,
    ])
