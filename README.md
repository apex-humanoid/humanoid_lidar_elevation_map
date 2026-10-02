# Humanoid LiDAR Elevation Map

Livox MID-360 acquisition, FAST-LIO odometry, and local elevation mapping for humanoid robots. The pipeline publishes a `grid_map_msgs/GridMap` on `/elevation_mapping/elevation_map`.

**The supplied configurations are specifically prepared for the Unitree G1.** Other robots require reconfiguration of frames, topics, and mapping parameters, plus calibration of the LiDAR-to-body and LiDAR-to-IMU transforms. Recheck the mounting calibration if the sensor placement changes, including on another G1.

## Requirements

- Ubuntu 20.04, **ROS 1 Noetic**, catkin, and system Python 3. Use a shell without ROS 2 or Conda activated.
- A Livox MID-360 connected by Ethernet to the mapping computer; hardware is optional for the synthetic test.
- The bundled Livox SDK 2 and ROS Driver 2 **v1.2.4**, built in ROS 1 mode. Keep this driver/SDK pair together.

## Preparation

From your cloned checkout, install dependencies in an environment with ROS Noetic already installed. Replace `/path/to/repo` with the checkout path:

```bash
cd /path/to/repo
export REPO_ROOT="$PWD"
source /opt/ros/noetic/setup.bash
export PATH=/opt/ros/noetic/bin:/usr/bin:/bin:$PATH

sudo apt update
sudo apt install -y \
  build-essential cmake git libeigen3-dev libpcl-dev libopencv-dev \
  python3-dev python3-numpy python3-yaml python3-matplotlib python3-catkin-tools \
  ros-noetic-pcl-ros ros-noetic-eigen-conversions \
  ros-noetic-cv-bridge ros-noetic-image-transport \
  ros-noetic-tf ros-noetic-tf-conversions ros-noetic-tf2-ros ros-noetic-tf2-sensor-msgs \
  ros-noetic-grid-map-core ros-noetic-grid-map-ros ros-noetic-grid-map-msgs \
  ros-noetic-grid-map-rviz-plugin ros-noetic-grid-map-visualization \
  ros-noetic-grid-map-filters ros-noetic-rviz ros-noetic-rostest
```

For hardware operation, put the computer and MID-360 on the same subnet. In [MID360_config.json](ws_livox/src/livox_ros_driver2/config/MID360_config.json), set the `MID360.host_net_info` IP fields to the computer's address (`log_data_ip` if logging is enabled) and `lidar_configs[0].ip` to the LiDAR's address. Review the G1 calibration files listed below before launching.

## Build

Install the external `kindr` library and bundled Livox SDK:

```bash
export DEPENDENCY_ROOT="$(mktemp -d /tmp/humanoid-dependencies-XXXXXX)"
git clone https://github.com/ethz-asl/kindr.git "$DEPENDENCY_ROOT/kindr"
cmake -S "$DEPENDENCY_ROOT/kindr" -B "$DEPENDENCY_ROOT/kindr/build"
cmake --build "$DEPENDENCY_ROOT/kindr/build" --parallel 4
sudo cmake --install "$DEPENDENCY_ROOT/kindr/build"

cmake -S "$REPO_ROOT/Livox-SDK2" -B "$REPO_ROOT/Livox-SDK2/build" -DCMAKE_BUILD_TYPE=Release
cmake --build "$REPO_ROOT/Livox-SDK2/build" --parallel 4
sudo cmake --install "$REPO_ROOT/Livox-SDK2/build"
sudo ldconfig
```

Build the ROS driver, then the mapping workspace. The driver's build script recreates its workspace's `build`, `devel`, and `install` directories.

```bash
cd "$REPO_ROOT/ws_livox/src/livox_ros_driver2"
bash build.sh ROS1
source "$REPO_ROOT/ws_livox/devel/setup.bash"

cd "$REPO_ROOT/ws_map"
export kindr_DIR=/usr/local/share/kindr/cmake
export CMAKE_PREFIX_PATH="/usr/local:${CMAKE_PREFIX_PATH}"
catkin config --cmake-args -DCMAKE_BUILD_TYPE=Release -DPYTHON_EXECUTABLE=/usr/bin/python3
catkin build -j4
source devel/setup.bash
```

Adjust `kindr_DIR` if your installed `kindrConfig.cmake` is elsewhere.

## Run

Source both workspaces in **each terminal**, replacing the path with your checkout:

```bash
export REPO_ROOT=/path/to/repo
source /opt/ros/noetic/setup.bash
source "$REPO_ROOT/ws_livox/devel/setup.bash"
source "$REPO_ROOT/ws_map/devel/setup.bash"
```

| Function | Command | Usage |
| --- | --- | --- |
| LiDAR acquisition | `roslaunch livox_ros_driver2 msg_MID360.launch` | Publishes `/livox/lidar` and `/livox/imu`; keep the default `xfer_format=1` for FAST-LIO. |
| Odometry | `roslaunch fast_lio mapping_mid360.launch` | Run alongside the driver above in a second terminal. |
| Full elevation mapping | `roslaunch elevation_mapping_demos mid360_elevation_mapping.launch` | Starts the driver, FAST-LIO, TF helpers, filtering, and mapping together. Stop standalone driver/odometry launches first; keep the robot stationary during gravity initialization. |
| Synthetic mapping test | `roslaunch elevation_mapping_demos offline_mapping.launch` | Run without the hardware pipeline, then execute the test below in another terminal. |
| Visualization | `rviz` | While mapping runs, select fixed frame `odom_corrected` and add a **GridMap** display for `/elevation_mapping/elevation_map`. |

```bash
# With offline_mapping.launch running, in a second sourced terminal:
/usr/bin/python3 "$REPO_ROOT/tests/offline_elevation_smoke.py"
```

The synthetic test expects the supplied 3 × 3 m map, 0.05 m resolution, frames, and filtering settings; run it before changing these defaults or update its expectations.

Recorded checks cover Noetic builds and synthetic mapping; real LiDAR acquisition, FAST-LIO estimation, and mapping during motion still require validation. Other bundled upstream examples are outside this walkthrough.

## Core configuration files

The [full launch](ws_map/src/elevation_mapping_humanoid/elevation_mapping/elevation_mapping_demos/launch/mid360_elevation_mapping.launch) wires these files together and overrides the pose publisher's `map_frame`. Paths are relative to the repository root.

| File | What to configure |
| --- | --- |
| [MID360_config.json](ws_livox/src/livox_ros_driver2/config/MID360_config.json) | Computer/LiDAR IPs and driver settings. |
| [publish_tf.py](ws_map/src/elevation_mapping_humanoid/fast_lio_mid360/script/publish_tf.py) | G1 mounting TFs and frame names; translation in metres, rotation as roll/pitch/yaw in radians. |
| [publish_torso_world_tf.py](ws_map/src/elevation_mapping_humanoid/fast_lio_mid360/script/publish_torso_world_tf.py) | Yaw-aligned torso TF; update its hard-coded `torso_link`, `torso_link_world`, and `odom_corrected` names when changing robot frames. |
| [pose_publisher.launch](ws_map/src/elevation_mapping_humanoid/pose_publisher/launch/pose_publisher.launch) | Pose `base_frame` (`torso_link`), `map_frame` (overridden to `odom_corrected` by the full launch), output topic, and rate. |
| [mid360.yaml](ws_map/src/elevation_mapping_humanoid/fast_lio_mid360/config/mid360.yaml) | LiDAR/IMU topics, preprocessing, noise parameters, and `mapping/extrinsic_T`, `mapping/extrinsic_R` calibration. |
| [mapping_mid360.launch](ws_map/src/elevation_mapping_humanoid/fast_lio_mid360/launch/mapping_mid360.launch) | FAST-LIO downsampling (`filter_size_surf`, `filter_size_map`), point filtering, and iteration limits. |
| [simple_demo_robot.yaml](ws_map/src/elevation_mapping_humanoid/elevation_mapping/elevation_mapping_demos/config/robots/simple_demo_robot.yaml) | **Map size** (`length_in_x/y`: 3 m), **resolution** (`resolution`: 0.05 m), map/body frames, input topic, tracking offset, update rates, variance, and height limits. |
| [postprocessor_pipeline.yaml](ws_map/src/elevation_mapping_humanoid/elevation_mapping/elevation_mapping_demos/config/postprocessing/postprocessor_pipeline.yaml) | Hole filling and surface-normal calculation radii. |
| [pc_filter.py](ws_map/src/elevation_mapping_humanoid/elevation_mapping/elevation_mapping_demos/scripts/pc_filter.py) | Filtering frame `torso_link_world` and private parameter `~distance_threshold`: upper Z limit, default 0.15 m. |
| [gravity_correction_publisher.py](ws_map/src/elevation_mapping_humanoid/elevation_mapping/elevation_mapping_demos/scripts/gravity_correction_publisher.py) | Gravity initialization and frames `odom_torso`, `lidar_link`, and `odom_corrected`. |

## License

Licenses are assigned by component. The root [LICENSE](LICENSE) covers this repository's original documentation and test/integration material outside vendored components. Vendored components and changes within them retain their component licenses: Livox code uses MIT, FAST-LIO includes GPL v2 code, and the mapping/support packages use BSD licenses. Each ROS package includes its license text and declares its licenses in `package.xml`; existing file-level notices remain applicable. See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) for the package-by-package scope, nested dependencies, and upstream references.

## Acknowledgments

Built on [Livox SDK 2](https://github.com/Livox-SDK/Livox-SDK2), [Livox ROS Driver 2](https://github.com/Livox-SDK/livox_ros_driver2), [FAST-LIO MID-360](https://github.com/SylarAnh/fast_lio_mid360), [Elevation Mapping Humanoid](https://github.com/smoggy-P/elevation_mapping_humanoid), and [ANYbotics Elevation Mapping](https://github.com/ANYbotics/elevation_mapping).
