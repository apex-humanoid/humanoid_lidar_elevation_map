#!/usr/bin/env python3

import rospy
import tf2_ros
import geometry_msgs.msg
import tf.transformations

class StaticTransformPublisher:
    def __init__(self):
        rospy.init_node('static_transform_publisher')

        self.broadcaster = tf2_ros.StaticTransformBroadcaster()

        # Reference mounting transforms: translation in metres, RPY in radians.
        # Preserve these values unless recalibrating the sensor mounting.
        import math

        self.transforms = [
            {
                'parent_frame': 'torso_link',
                'child_frame': 'camera_depth_optical_frame',
                'translation': (0.0576235, 0.01753, 0.41987),
                'rpy': (-2.416, 0.0, -1.571)
            },
            {
                'parent_frame': 'torso_link',
                'child_frame': 'lidar_link',
                'translation': (0.0002835, 0.00003, 0.41618),
                'rpy': (3.1416, math.radians(0.), 0)
            },
            {
                'parent_frame': 'odom',
                'child_frame': 'odom_torso',
                'translation': (0.0, 0.0, 0.0),
                'rpy': (-3.1415, 0.0, 0)
            }
        ]

    def publish_transforms(self):
        static_transforms = []
        for transform in self.transforms:
            t = geometry_msgs.msg.TransformStamped()
            t.header.stamp = rospy.Time.now()
            t.header.frame_id = transform['parent_frame']
            t.child_frame_id = transform['child_frame']

            t.transform.translation.x = transform['translation'][0]
            t.transform.translation.y = transform['translation'][1]
            t.transform.translation.z = transform['translation'][2]

            # Convert RPY to Quaternion
            quaternion = tf.transformations.quaternion_from_euler(
                transform['rpy'][0],
                transform['rpy'][1],
                transform['rpy'][2]
            )

            t.transform.rotation.x = quaternion[0]
            t.transform.rotation.y = quaternion[1]
            t.transform.rotation.z = quaternion[2]
            t.transform.rotation.w = quaternion[3]

            static_transforms.append(t)

        self.broadcaster.sendTransform(static_transforms)
        rospy.loginfo("Published static transforms")

if __name__ == '__main__':
    try:
        static_transform_publisher = StaticTransformPublisher()
        # /tf_static is latched: publish once and keep the broadcaster alive.
        static_transform_publisher.publish_transforms()
        rospy.spin()
    except rospy.ROSInterruptException:
        pass
