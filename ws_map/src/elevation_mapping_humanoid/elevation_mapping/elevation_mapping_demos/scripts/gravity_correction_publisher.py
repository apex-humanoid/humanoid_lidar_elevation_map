#!/usr/bin/env python3

import rospy
import tf
import tf2_ros
import numpy as np
from sensor_msgs.msg import Imu
from geometry_msgs.msg import TransformStamped
from tf.transformations import (
    quaternion_matrix,
    quaternion_from_matrix,
    quaternion_from_euler,
    quaternion_about_axis
)

class GravityCorrectionPublisher:
    def __init__(self):
        rospy.init_node('gravity_correction_publisher')

        # TF listener and broadcaster
        self.tf_listener = tf.TransformListener()
        self.tf_broadcaster = tf2_ros.StaticTransformBroadcaster()

        # Subscribe to IMU data
        self.imu_sub = rospy.Subscriber('/livox/imu', Imu, self.imu_callback)
        self.gravity_queue = []

        self.measured_gravity = None

        # Frame names
        self.lidar_frame = 'lidar_link'
        self.odom_frame = 'odom_torso'
        self.lidar_to_odom_trans = None
        self.lidar_to_odom_rot = None

        self.corrected_frame = 'odom_corrected'
        self.published = False

        self.n_average_linvel = 10

        # Publishing rate
        self.rate = rospy.Rate(100)  # 100 Hz

        # Wait for transforms to become available
        rospy.loginfo("Waiting for transforms to become available...")
        try:
            self.tf_listener.waitForTransform(
                self.odom_frame,
                self.lidar_frame,
                rospy.Time(),
                rospy.Duration(5.0)
            )
            rospy.loginfo("Transforms are now available!")
        except (tf.Exception, tf.ConnectivityException, tf.LookupException):
            rospy.logwarn("Transform not available after waiting! Will keep trying during execution...")

    def imu_callback(self, msg):
        """Process incoming IMU messages."""
        if self.measured_gravity is not None:
            self.imu_sub.unregister()
            rospy.logdebug("Gravity samples collected; unsubscribed from IMU data")
            return

        latest_accel_recv = np.array([
            msg.linear_acceleration.x,
            msg.linear_acceleration.y,
            msg.linear_acceleration.z
        ])
        rospy.logdebug(f"Received IMU data. Acceleration: {latest_accel_recv}")

        self.gravity_queue.append(latest_accel_recv)
        if len(self.gravity_queue) > self.n_average_linvel:

            average_linvel = np.mean(self.gravity_queue, axis=0)

            # Preserve the reference setup's acceleration sign convention.
            # This sign inversion is not a physical IMU-to-LiDAR rotation.
            R = np.array([
                [-1, 0, 0],
                [0, -1, 0],
                [0, 0, -1]
            ])

            self.measured_gravity = np.dot(R, average_linvel)

    def compute_gravity_vector(self):
        """Compute rotation to align with gravity vector."""
        if self.measured_gravity is None:
            rospy.logwarn_throttle(1.0, "No IMU data received yet!")
            return None

        # Normalize acceleration vector
        accel_norm = np.linalg.norm(self.measured_gravity)
        if accel_norm < 1e-6:
            rospy.logwarn_throttle(1.0, "Acceleration magnitude too small!")
            return None

        accel_normalized = self.measured_gravity / accel_norm
        rospy.logdebug(f"Normalized acceleration vector: {accel_normalized}")

        return accel_normalized

    def get_odom_to_lidar_transform(self):

        try:
            # Get transform from odom_torso to lidar_link
            # Use a slightly older timestamp to avoid extrapolation
            timestamp = rospy.Time.now() - rospy.Duration(0.1)  # 100ms in the past

            try:
                self.tf_listener.waitForTransform(
                    self.odom_frame,
                    self.lidar_frame,
                    timestamp,
                    rospy.Duration(0.1)
                )
            except tf.Exception as e:
                rospy.logwarn_throttle(1.0, f"Wait for transform failed: {str(e)}")
                return None, None

            (trans, rot) = self.tf_listener.lookupTransform(
                self.odom_frame,
                self.lidar_frame,
                timestamp
            )
            rospy.logdebug(f"Current transform - Translation: {trans}, Rotation: {rot}")
            return trans, rot

        except (tf.LookupException, tf.ConnectivityException, tf.ExtrapolationException) as e:
            rospy.logwarn_throttle(1.0, f"Failed to lookup transform: {str(e)}")
            return None, None
    def publish_corrected_frame(self):
        """Publish the gravity-corrected frame."""
        if self.published:
            return
        if self.measured_gravity is None:
            rospy.logwarn_throttle(1.0, "Waiting for IMU data...")
            return

        if self.lidar_to_odom_trans is None or self.lidar_to_odom_rot is None:
            trans, rot = self.get_odom_to_lidar_transform()
            if trans is None or rot is None:
                rospy.logwarn_throttle(1.0, "Failed to get transform")
                return
            self.lidar_to_odom_trans = trans
            self.lidar_to_odom_rot = rot

        # Compute gravity correction in lidar frame
        gravity_vector = self.compute_gravity_vector()
        if gravity_vector is None:
            return
        rospy.logdebug(f"OG gravity vector: {gravity_vector}")

        # first, get the rotation matrix from the rotation quaternion
        rot_mat = quaternion_matrix(self.lidar_to_odom_rot)
        rospy.logdebug(f"Rotation matrix: {rot_mat}")

        local_gravity_vector = np.dot(rot_mat, np.concatenate((gravity_vector, np.array([1.0]))))[0:3]
        rospy.logdebug(f"Local gravity vector: {local_gravity_vector}")

        local_gravity_vector = local_gravity_vector / np.linalg.norm(local_gravity_vector)
        rospy.logdebug(f"Normalized local gravity vector: {local_gravity_vector}")

        # Desired gravity direction in the corrected frame (pointing down)
        gravity_target = np.array([0.0, 0.0, -1.0])

        # Compute rotation axis (cross product)
        rotation_axis = np.cross(local_gravity_vector, gravity_target)
        rotation_axis_norm = np.linalg.norm(rotation_axis)

        # TF stores the corrected child orientation in the odometry parent.
        # This is the inverse of the rotation mapping measured gravity to -Z.
        cos_angle = np.clip(np.dot(local_gravity_vector, gravity_target), -1.0, 1.0)
        if rotation_axis_norm < 1e-6:
            gravity_correction_quat = (quaternion_from_euler(0, 0, 0)
                if cos_angle > 0 else quaternion_about_axis(np.pi, [1, 0, 0]))
        else:
            gravity_correction_quat = quaternion_about_axis(
                -np.arccos(cos_angle), rotation_axis / rotation_axis_norm)

        corrected_rot_mat = quaternion_matrix(gravity_correction_quat)
        rospy.logdebug(f"Corrected rotation matrix: {corrected_rot_mat}")

        final_trans = corrected_rot_mat[:3, 3]
        final_rot = quaternion_from_matrix(corrected_rot_mat)

        # Create and publish transform message
        t = TransformStamped()
        t.header.stamp = rospy.Time.now()
        t.header.frame_id = self.odom_frame
        t.child_frame_id = self.corrected_frame

        t.transform.translation.x = final_trans[0]
        t.transform.translation.y = final_trans[1]
        t.transform.translation.z = final_trans[2]

        t.transform.rotation.x = final_rot[0]
        t.transform.rotation.y = final_rot[1]
        t.transform.rotation.z = final_rot[2]
        t.transform.rotation.w = final_rot[3]

        self.tf_broadcaster.sendTransform(t)
        rospy.loginfo("Published gravity-corrected static transform")
        self.published = True

    def run(self):
        """Main run loop."""
        rospy.loginfo("Starting gravity correction publisher...")
        while not rospy.is_shutdown():
            self.publish_corrected_frame()
            self.rate.sleep()
        rospy.spin()

if __name__ == '__main__':
    try:
        node = GravityCorrectionPublisher()
        node.run()
    except rospy.ROSInterruptException:
        pass
