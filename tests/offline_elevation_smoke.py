#!/usr/bin/python3
"""Run after roslaunch elevation_mapping_demos offline_mapping.launch."""
import time
import numpy as np
import rospy
from grid_map_msgs.msg import GridMap
from sensor_msgs.msg import PointCloud2
from sensor_msgs import point_cloud2
from std_msgs.msg import Header

rospy.init_node('offline_elevation_smoke', anonymous=True)
received = []
filtered = []
rospy.Subscriber('/elevation_mapping/elevation_map', GridMap, received.append)
rospy.Subscriber('/cloud_registered/filtered', PointCloud2, filtered.append)
pub = rospy.Publisher('/cloud_registered', PointCloud2, queue_size=1)
# Flat floor and raised platform, both inside the production height limits.
points = [(float(x), float(y), -0.8 if x > 0.3 else -1.0)
          for x in np.arange(-0.9, 0.91, 0.04)
          for y in np.arange(-0.9, 0.91, 0.04)]
points += [(float('nan'), 0, -1), (float('inf'), 0, -1)]
deadline = time.monotonic() + 40
while time.monotonic() < deadline and not rospy.is_shutdown():
    pub.publish(point_cloud2.create_cloud_xyz32(
        Header(stamp=rospy.Time.now(), frame_id='odom_corrected'), points))
    rospy.sleep(0.2)
    for msg in received[-3:]:
        data = np.asarray(msg.data[msg.layers.index('elevation')].data)
        valid = data[np.isfinite(data)]
        if valid.size > 500 and np.any(np.abs(valid + 1.0) < 0.02) and np.any(np.abs(valid + 0.8) < 0.02):
            assert msg.info.header.frame_id == 'odom_corrected'
            assert abs(msg.info.resolution - 0.05) < 1e-6
            assert data.size == 3600, data.size
            assert filtered and filtered[-1].width == len(points) - 2
            assert not any(np.allclose(p, [0, 0, 0]) for p in point_cloud2.read_points(filtered[-1], field_names=('x', 'y', 'z')))
            print('PASS: 60x60 elevation map, %.2fm resolution, %d finite cells, floor -1.0m and step -0.8m; invalid points removed' % (msg.info.resolution, valid.size))
            raise SystemExit(0)
raise SystemExit('FAIL: no valid floor/step elevation map within 40 seconds')
