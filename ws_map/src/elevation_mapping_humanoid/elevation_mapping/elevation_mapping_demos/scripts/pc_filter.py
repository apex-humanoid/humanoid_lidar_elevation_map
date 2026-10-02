#!/usr/bin/env python3

import rospy
import numpy as np
import tf2_ros
import tf2_py as tf2
import sensor_msgs.point_cloud2 as pc2
from sensor_msgs.msg import PointCloud2, PointField
from tf2_sensor_msgs.tf2_sensor_msgs import do_transform_cloud

class PointCloudFilter:
    def __init__(self):
        rospy.init_node('pointcloud_filter')

        self.distance_threshold = rospy.get_param('~distance_threshold', 0.15)  # Upper Z limit in torso_link_world (metres).

        self.subscriber = rospy.Subscriber('/cloud_registered', PointCloud2, self.pointcloud_callback)
        self.publisher = rospy.Publisher('/cloud_registered/filtered', PointCloud2, queue_size=10)

        self.tf_buffer = tf2_ros.Buffer()
        self.tf_listener = tf2_ros.TransformListener(self.tf_buffer)

    def pointcloud_callback(self, msg):
        # Transform into the yaw-aligned torso frame before filtering by height.
        try:
            trans = self.tf_buffer.lookup_transform("torso_link_world", msg.header.frame_id,
                                            msg.header.stamp,
                                            rospy.Duration(1.0))
        except (tf2.LookupException, tf2.ConnectivityException) as ex:
            rospy.logwarn_throttle(1.0, "Cannot transform cloud into torso_link_world: %s", ex)
            return
        except tf2.ExtrapolationException as ex:
            rospy.logwarn_throttle(1.0, "Cannot transform cloud into torso_link_world: %s", ex)
            return

        transformed_pc_msg = do_transform_cloud(msg, trans)

        transformed_points = self.pointcloud2_to_numpy(transformed_pc_msg)
        filtered_points = self.filter_points(transformed_points)
        filtered_msg = self.numpy_to_pointcloud2(filtered_points, transformed_pc_msg.header)

        self.publisher.publish(filtered_msg)

    def pointcloud2_to_numpy(self, msg):
        # Extract point cloud data from ROS message
        points = np.asarray(list(pc2.read_points(
            msg, field_names=("x", "y", "z"), skip_nans=True)), dtype=np.float32).reshape(-1, 3)
        return points[np.isfinite(points).all(axis=1)]

    def numpy_to_pointcloud2(self, points, header):
        # Convert numpy array to ROS PointCloud2 message
        msg = PointCloud2()
        msg.header = header

        msg.height = 1
        msg.width = points.shape[0]

        msg.fields = [
            PointField('x', 0, PointField.FLOAT32, 1),
            PointField('y', 4, PointField.FLOAT32, 1),
            PointField('z', 8, PointField.FLOAT32, 1),
        ]

        msg.is_bigendian = False
        msg.point_step = 12
        msg.row_step = msg.point_step * msg.width
        msg.is_dense = False
        msg.data = points.tobytes()

        return msg

    def filter_points(self, points):

        # The legacy distance_threshold parameter is an upper height limit.
        mask = points[:, 2] <= self.distance_threshold
        filtered_points = points[mask]

        return filtered_points

if __name__ == '__main__':
    try:
        PointCloudFilter()
        rospy.spin()
    except rospy.ROSInterruptException:
        pass
