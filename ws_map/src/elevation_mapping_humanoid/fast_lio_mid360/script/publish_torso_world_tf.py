#!/usr/bin/env python3
import rospy
import tf2_ros
import geometry_msgs.msg
import tf.transformations as tf


class TorsoWorldPublisher:
    def __init__(self):
        rospy.init_node("torso_link_world_publisher")

        self.br = tf2_ros.TransformBroadcaster()
        self.buffer = tf2_ros.Buffer()
        self.listener = tf2_ros.TransformListener(self.buffer)

        self.rate = rospy.Rate(100)

    def run(self):
        while not rospy.is_shutdown():
            try:
                # 1. Lookup the current torso pose in the corrected odom frame
                trans = self.buffer.lookup_transform(
                    "odom_corrected",
                    "torso_link",
                    rospy.Time(0),
                    rospy.Duration(0.1)
                )
            except Exception as e:
                rospy.logwarn_throttle(1.0, f"TF missing: {e}")
                self.rate.sleep()
                continue

            # 2. Extract the current rotation
            current_rot = [
                trans.transform.rotation.x,
                trans.transform.rotation.y,
                trans.transform.rotation.z,
                trans.transform.rotation.w
            ]

            # 3. Convert Quaternion to Euler angles (Roll, Pitch, Yaw)
            # We use 'sxyz' static axes (standard for ROS)
            (roll, pitch, yaw) = tf.euler_from_quaternion(current_rot)

            # 4. Create new Quaternion using ONLY the Yaw
            # Setting Roll and Pitch to 0 aligns the Z axis with odom_corrected
            # Keeping Yaw ensures X axis is the projection of torso_link's X
            new_rot = tf.quaternion_from_euler(0, 0, yaw)

            # 5. Build the new transform message
            out = geometry_msgs.msg.TransformStamped()
            out.header.stamp = rospy.Time.now()
            out.header.frame_id = "odom_corrected"
            out.child_frame_id = "torso_link_world"

            # Use the original translation (same position as torso_link)
            out.transform.translation = trans.transform.translation

            # Use the new flattened rotation
            out.transform.rotation.x = new_rot[0]
            out.transform.rotation.y = new_rot[1]
            out.transform.rotation.z = new_rot[2]
            out.transform.rotation.w = new_rot[3]

            self.br.sendTransform(out)
            self.rate.sleep()


if __name__ == "__main__":
    TorsoWorldPublisher().run()
