#!/usr/bin/python3
import importlib.util
from pathlib import Path
import unittest
import numpy as np
from sensor_msgs import point_cloud2
from std_msgs.msg import Header
from tf.transformations import quaternion_matrix

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / 'ws_map/src/elevation_mapping_humanoid/elevation_mapping/elevation_mapping_demos/scripts'
def load(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

class HelpersTest(unittest.TestCase):
    def test_invalid_points_do_not_become_origin(self):
        cls = load('pc_filter').PointCloudFilter
        node = cls.__new__(cls)
        msg = point_cloud2.create_cloud_xyz32(Header(), [(1, 2, -1), (np.nan, 0, 0), (np.inf, 0, 0)])
        np.testing.assert_allclose(node.pointcloud2_to_numpy(msg), [[1, 2, -1]])
        empty = point_cloud2.create_cloud_xyz32(Header(), [(np.nan, 0, 0)])
        self.assertEqual(node.pointcloud2_to_numpy(empty).shape, (0, 3))

    def test_gravity_alignment_and_single_publication(self):
        module = load('gravity_correction_publisher')
        module.rospy.Time.now = lambda: module.rospy.Time(1)
        for vector in ([0, 0, -1], [0, 0, 1], [0.3, 0.4, -0.8]):
            node = module.GravityCorrectionPublisher.__new__(module.GravityCorrectionPublisher)
            node.published = False
            node.measured_gravity = np.asarray(vector, dtype=float)
            node.lidar_to_odom_trans = [0, 0, 0]
            node.lidar_to_odom_rot = [0, 0, 0, 1]
            node.odom_frame = 'odom_torso'
            node.corrected_frame = 'odom_corrected'
            sent = []
            node.tf_broadcaster = type('Capture', (), {'sendTransform': lambda _, msg: sent.append(msg)})()
            node.publish_corrected_frame()
            self.assertEqual(len(sent), 1)
            q = sent[0].transform.rotation
            rotation = quaternion_matrix([q.x, q.y, q.z, q.w])[:3, :3]
            gravity = node.measured_gravity / np.linalg.norm(node.measured_gravity)
            np.testing.assert_allclose(rotation.T @ gravity, [0, 0, -1], atol=1e-6)
            node.publish_corrected_frame()
            self.assertEqual(len(sent), 1)

if __name__ == '__main__':
    unittest.main()
