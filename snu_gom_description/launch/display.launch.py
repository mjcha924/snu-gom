"""ROS 2 kinematic display only: no physics, controller or hardware connection."""
from pathlib import Path
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    share = Path(get_package_share_directory('snu_gom_description'))
    description = (share / 'urdf/snu_gom_preview.urdf').read_text()
    return LaunchDescription([
        Node(package='robot_state_publisher', executable='robot_state_publisher',
             parameters=[{'robot_description': description}], output='screen'),
        Node(package='joint_state_publisher_gui', executable='joint_state_publisher_gui',
             parameters=[{'robot_description': description}], output='screen'),
        Node(package='rviz2', executable='rviz2',
             arguments=['-d', str(share / 'config/snu_gom.rviz')], output='screen'),
    ])
