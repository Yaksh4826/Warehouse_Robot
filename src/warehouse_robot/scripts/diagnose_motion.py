#!/usr/bin/env python3
"""
diagnose_motion.py — a single, self-contained sanity check that answers
"is the robot actually being driven?" without looking at RViz at all.

It:
  1. Subscribes to /odom and /tf and /cmd_vel.
  2. Records the robot pose NOW.
  3. Publishes a steady /cmd_vel at 20 Hz for 4 s (linear=0.3, angular=0.0).
  4. Records the pose AFTER.
  5. Prints a human-readable verdict:
       - how far the robot moved according to /odom
       - how far according to TF (odom -> base_link)
       - whether /cmd_vel has a subscriber at all (= the bridge is wired)
       - whether the plugin echoed the command back via odom.twist

Run AFTER `ros2 launch warehouse_robot check1.launch.py` is already up.
"""
import math
import time
import sys
import rclpy
from rclpy.node import Node
from rclpy.duration import Duration
from nav_msgs.msg import Odometry
from geometry_msgs.msg import Twist
import tf2_ros


def main():
    rclpy.init()
    n = Node('diagnose_motion')

    odoms: list = []
    last_twist: list = [None]

    def odom_cb(msg: Odometry):
        odoms.append(msg)
        last_twist[0] = msg.twist.twist

    n.create_subscription(Odometry, '/odom', odom_cb, 50)
    cmd_pub = n.create_publisher(Twist, '/cmd_vel', 10)

    tf_buf = tf2_ros.Buffer()
    tf_listen = tf2_ros.TransformListener(tf_buf, n)

    # -------- 1. Wait for odom + TF to be flowing --------
    print("[1/5] Waiting up to 5s for first /odom message ...")
    t0 = time.time()
    while not odoms and time.time() - t0 < 5.0:
        rclpy.spin_once(n, timeout_sec=0.1)

    if not odoms:
        print("  ERROR: no /odom messages at all. Is the ros_gz_bridge running?")
        print("         Check:  ros2 topic info /odom")
        rclpy.shutdown(); sys.exit(2)
    print(f"  OK. /odom publishing (got {len(odoms)} msgs in warmup).")

    # -------- 2. Confirm /cmd_vel actually has a subscriber (= bridge alive) --------
    sub_count = cmd_pub.get_subscription_count()
    print(f"[2/5] /cmd_vel subscriber count = {sub_count}  "
          f"(expect 1 = the ros_gz_bridge)")
    if sub_count == 0:
        print("  WARNING: nothing in ROS is subscribed to /cmd_vel.")
        print("  The /cmd_vel ROS->GZ bridge is missing. Run the check1.launch.py")
        print("  from this workspace, NOT a bare gz_sim without the bridge node.")

    # -------- 3. Snapshot pose BEFORE --------
    before = odoms[-1]
    bx, by = before.pose.pose.position.x, before.pose.pose.position.y
    print(f"[3/5] Pose BEFORE:  x={bx:+.3f}  y={by:+.3f}")

    try:
        tf_before = tf_buf.lookup_transform('odom', 'base_link',
                                            rclpy.time.Time(),
                                            timeout=Duration(seconds=2.0))
        tb_x = tf_before.transform.translation.x
        tb_y = tf_before.transform.translation.y
        print(f"      TF odom->base_link BEFORE:  x={tb_x:+.3f}  y={tb_y:+.3f}")
    except Exception as e:
        print(f"      WARNING: no TF odom->base_link yet ({e})")
        tb_x = tb_y = None

    # -------- 4. Publish cmd_vel steadily for 4 seconds --------
    print("[4/5] Publishing  /cmd_vel { linear.x: 0.3 }  at 20 Hz for 4.0 s ...")
    msg = Twist(); msg.linear.x = 0.3
    end = time.time() + 4.0
    while time.time() < end:
        cmd_pub.publish(msg)
        rclpy.spin_once(n, timeout_sec=0.05)
    # stop
    cmd_pub.publish(Twist())
    for _ in range(10):
        rclpy.spin_once(n, timeout_sec=0.02)
    time.sleep(0.5)

    # -------- 5. Snapshot pose AFTER and report --------
    after = odoms[-1]
    ax, ay = after.pose.pose.position.x, after.pose.pose.position.y
    dist_odom = math.hypot(ax - bx, ay - by)

    if tb_x is not None:
        try:
            tf_after = tf_buf.lookup_transform('odom', 'base_link',
                                               rclpy.time.Time(),
                                               timeout=Duration(seconds=2.0))
            ta_x = tf_after.transform.translation.x
            ta_y = tf_after.transform.translation.y
            dist_tf = math.hypot(ta_x - tb_x, ta_y - tb_y)
        except Exception:
            ta_x = ta_y = None
            dist_tf = float('nan')
    else:
        ta_x = ta_y = None
        dist_tf = float('nan')

    cmd_vx = last_twist[0].linear.x if last_twist[0] else float('nan')

    print()
    print("=========== VERDICT ===========")
    print(f"  /odom movement          : {dist_odom:.3f} m     "
          f"(BEFORE {bx:+.2f},{by:+.2f}  ->  AFTER {ax:+.2f},{ay:+.2f})")
    if ta_x is not None:
        print(f"  TF odom->base_link move : {dist_tf:.3f} m     "
              f"(BEFORE {tb_x:+.2f},{tb_y:+.2f}  ->  AFTER {ta_x:+.2f},{ta_y:+.2f})")
    else:
        print("  TF odom->base_link move : N/A (TF not available)")
    print(f"  odom.twist.linear.x now : {cmd_vx:+.3f} m/s  "
          f"(should settle to 0 after the stop)")
    print()

    # 0.3 m/s for 4 s ~= 1.2 m if no wall contact.
    if dist_odom > 0.5:
        print("  RESULT: YES, the robot moved. If RViz didn't show it, the")
        print("          problem is almost certainly the RViz Target Frame")
        print("          tracking base_link. Open the Views panel and set")
        print("          Target Frame = <Fixed Frame>. (Already fixed in")
        print("          config/view_robot.rviz — rebuild + relaunch.)")
        exit_code = 0
    elif dist_odom > 0.02:
        print("  RESULT: the robot crept. Likely hitting a wall. Try moving")
        print("          the spawn somewhere clearer or drive with a turn:")
        print("          ros2 topic pub -r 10 /cmd_vel geometry_msgs/msg/Twist \\")
        print("              \"{linear: {x: 0.3}, angular: {z: 0.4}}\"")
        exit_code = 1
    else:
        print("  RESULT: NO motion. Diagnostics:")
        print(f"          * /cmd_vel had {sub_count} subscriber(s) — must be >= 1")
        print("          * Check bridge is alive:  ros2 node info /ros_gz_bridge")
        print("          * Check /cmd_vel topic type is geometry_msgs/msg/Twist")
        print("          * Make sure Gazebo is unpaused (press play or run")
        print("            with gz_args containing '-r').")
        exit_code = 2

    n.destroy_node()
    rclpy.shutdown()
    sys.exit(exit_code)


if __name__ == '__main__':
    main()
