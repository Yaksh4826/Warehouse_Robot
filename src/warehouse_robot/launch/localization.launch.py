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
from launch.conditions import IfCondition

from launch_ros.actions import Node


def generate_launch_description():
    pkg_path = get_package_share_directory('warehouse_robot')
    amcl_params = os.path.join(pkg_path, 'config', 'amcl.yaml')
    default_map = os.path.join(pkg_path, 'maps', 'warehouse_v1.yaml')

    use_sim_time = LaunchConfiguration('use_sim_time')
    headless = LaunchConfiguration('headless')
    rviz = LaunchConfiguration('rviz')
    map_yaml = LaunchConfiguration('map')
    launch_bringup = LaunchConfiguration('bringup')

    declare_sim_time = DeclareLaunchArgument('use_sim_time', default_value='true')
    declare_headless = DeclareLaunchArgument('headless', default_value='false')
    declare_rviz = DeclareLaunchArgument('rviz', default_value='true')
    declare_map = DeclareLaunchArgument(
        'map', default_value=default_map,
        description='Full path to the .yaml map metadata produced by step 6 (save_map.sh).'
    )
    declare_bringup = DeclareLaunchArgument(
        'bringup', default_value='true',
        description='Also launch Gazebo + robot + bridges (set false if already running).'
    )

    # ========== BRINGUP (sim + robot + bridges) — no static map->odom ==========
    bringup = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_path, 'launch', 'check1.launch.py')
        ),
        launch_arguments={
            'use_sim_time': use_sim_time,
            'headless': headless,
            'rviz': rviz,
            'static_map_odom': 'false',  # AMCL owns map->odom
        }.items(),
        condition=IfCondition(launch_bringup),
    )

    # ========== MAP SERVER + AMCL ==========
    # Both are nav2 lifecycle nodes — they MUST be configured + activated
    # via lifecycle_manager or they'll sit idle.
    map_server = Node(
        package='nav2_map_server',
        executable='map_server',
        name='map_server',
        output='screen',
        parameters=[
            {'use_sim_time': use_sim_time},
            {'yaml_filename': map_yaml},
        ],
    )

    amcl = Node(
        package='nav2_amcl',
        executable='amcl',
        name='amcl',
        output='screen',
        parameters=[amcl_params, {'use_sim_time': use_sim_time}],
    )

    # Activate the two lifecycle nodes. Delay slightly so bringup + TF are ready.
    lifecycle_mgr = TimerAction(
        period=4.0,
        actions=[
            Node(
                package='nav2_lifecycle_manager',
                executable='lifecycle_manager',
                name='lifecycle_manager_localization',
                output='screen',
                parameters=[{
                    'use_sim_time': use_sim_time,
                    'autostart': True,
                    'node_names': ['map_server', 'amcl'],
                }],
            )
        ]
    )

    return LaunchDescription([
        declare_sim_time,
        declare_headless,
        declare_rviz,
        declare_map,
        declare_bringup,
        bringup,
        map_server,
        amcl,
        lifecycle_mgr,
    ])
