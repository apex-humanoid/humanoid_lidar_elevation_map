# Component licenses and upstream notices

This repository collects independently licensed source components. The root
[LICENSE](LICENSE) covers original repository documentation and tests/integration
material outside vendored components. It does not relicense third-party source,
images, documentation, or examples. Existing copyright notices and file-level
license terms remain in place. Local modifications within a component follow
that component's applicable terms.

## ROS packages and SDK

Paths in the mapping rows below are relative to
[`ws_map/src/elevation_mapping_humanoid/`](ws_map/src/elevation_mapping_humanoid/).
Multiple license entries describe different included portions, not a choice to
redistribute the entire package under any one of them.

| Component / ROS package | Directory | License texts and scope |
| --- | --- | --- |
| Livox SDK 2 | `Livox-SDK2/` (repository root) | [MIT and bundled notices](Livox-SDK2/LICENSE.txt); nested libraries retain their notices below. |
| `livox_ros_driver2` | `ws_livox/src/livox_ros_driver2/` (repository root) | [MIT and upstream third-party notices](ws_livox/src/livox_ros_driver2/LICENSE.txt). |
| `fast_lio` | `fast_lio_mid360/` | [GNU GPL v2 text](ws_map/src/elevation_mapping_humanoid/fast_lio_mid360/LICENSE), with BSD-3-Clause source notices and a separately licensed MIT header described below. |
| `elevation_mapping` | `elevation_mapping/elevation_mapping/` | [BSD-3-Clause](ws_map/src/elevation_mapping_humanoid/elevation_mapping/elevation_mapping/LICENSE). |
| `elevation_mapping_demos` | `elevation_mapping/elevation_mapping_demos/` | [BSD-3-Clause](ws_map/src/elevation_mapping_humanoid/elevation_mapping/elevation_mapping_demos/LICENSE). |
| `kindr_msgs` | `kindr_ros/kindr_msgs/` | [BSD-3-Clause](ws_map/src/elevation_mapping_humanoid/kindr_ros/kindr_msgs/LICENSE). |
| `kindr_ros` | `kindr_ros/kindr_ros/` | [BSD-3-Clause](ws_map/src/elevation_mapping_humanoid/kindr_ros/kindr_ros/LICENSE). |
| `kindr_rviz_plugins` | `kindr_ros/kindr_rviz_plugins/` | [BSD-3-Clause](ws_map/src/elevation_mapping_humanoid/kindr_ros/kindr_rviz_plugins/LICENSE). |
| `multi_dof_joint_trajectory_rviz_plugins` | `kindr_ros/multi_dof_joint_trajectory_rviz_plugins/` | [BSD-3-Clause](ws_map/src/elevation_mapping_humanoid/kindr_ros/multi_dof_joint_trajectory_rviz_plugins/LICENSE). |
| `message_logger` | `message_logger/` | [BSD-3-Clause](ws_map/src/elevation_mapping_humanoid/message_logger/LICENSE). |
| `pose_publisher` | `pose_publisher/` | [BSD-3-Clause and BSD-2-Clause notices](ws_map/src/elevation_mapping_humanoid/pose_publisher/LICENSE), from Zhi Yan and Robotnik Automation respectively. |

Every ROS package has a license text at its package root and matching license
entries in `package.xml`. The six license files added beneath `elevation_mapping/`
and `kindr_ros/` are verbatim copies of their existing parent-component licenses;
the original parent files are retained. CMake installs each package's license
text with the package. The Livox driver keeps its upstream `LICENSE.txt` name.

## Upstream comparison

The license review checked these two references on 2026-10-02:

- [ArthurAllshire/elevation_mapping_humanoid at 214bc3f](https://github.com/ArthurAllshire/elevation_mapping_humanoid/tree/214bc3f687cbdf6183013647b9248314afff3f5b).
- [smoggy-P/elevation_mapping_humanoid at 31f82e3](https://github.com/smoggy-P/elevation_mapping_humanoid/tree/31f82e3f97b9790d440a60480cb7fb0cff38022f).

Neither reference has a repository-root license. Both retain license files in
`elevation_mapping`, `fast_lio_mid360`, `kindr_ros`, `message_logger`, and
`pose_publisher`. Those five license files are byte-for-byte identical to the
corresponding original files retained here. These are references checked for
licensing, not a claim that every local source file matches either commit.

Both references declare `BSD` in `fast_lio_mid360/package.xml` while shipping the
GNU GPL v2 text in `fast_lio_mid360/LICENSE`. This repository preserves that GPL
text and changes the manifest to include `GPL-2.0`, together with the BSD and MIT
notices for bundled portions. It does not treat the entire FAST-LIO package as
BSD-licensed or replace its original file-level copyright notices.

The Livox ROS driver is vendored from official tag `1.2.4`, commit
[`b6ff7d1c8b210a96b74e919823771e1e32249758`](https://github.com/Livox-SDK/livox_ros_driver2/tree/b6ff7d1c8b210a96b74e919823771e1e32249758).
Its `package.xml` is copied from `package_ROS1.xml`. Local packaging changes
discover SDK headers from the install prefix and install the driver configuration
directory and license text. Keep the bundled driver and SDK versions together.

## Bundled dependencies and file-level notices

- Livox SDK 2 includes [FastCRC](Livox-SDK2/3rdparty/FastCRC/LICENSE.md),
  [RapidJSON](Livox-SDK2/3rdparty/rapidjson/license.txt),
  [spdlog](Livox-SDK2/3rdparty/spdlog/LICENSE), and
  [fmt](Livox-SDK2/3rdparty/spdlog/spdlog/fmt/bundled/LICENSE.rst).
  Their included license texts and copyright notices are retained. RapidJSON's
  notice also describes BSD-licensed `msinttypes`; its JSON-checker distribution
  notice is preserved, although the `bin/jsonchecker` sources are not included.
- The Livox driver also includes [RapidJSON](ws_livox/src/livox_ros_driver2/3rdparty/rapidjson/license.txt).
  Its top-level license preserves the upstream ROS BSD and ROS 2 Apache-2.0
  notices; those do not change the driver's own MIT declaration.
- FAST-LIO includes BSD-3-Clause notices in
  [laserMapping.cpp](ws_map/src/elevation_mapping_humanoid/fast_lio_mid360/src/laserMapping.cpp)
  and the [IKFoM/MTK headers](ws_map/src/elevation_mapping_humanoid/fast_lio_mid360/include/IKFoM_toolkit/).
  These notices are retained alongside the component GPL license. The bundled
  [ikd-Tree](ws_map/src/elevation_mapping_humanoid/fast_lio_mid360/include/ikd-Tree/)
  also retains its source and research attribution under the component's license arrangement.
- The bundled `fast_lio_mid360/include/matplotlibcpp.h` originates from
  [matplotlib-cpp](https://github.com/lava/matplotlib-cpp). Its MIT notice is
  supplied in [matplotlibcpp.LICENSE](ws_map/src/elevation_mapping_humanoid/fast_lio_mid360/include/matplotlibcpp.LICENSE),
  copied from the [upstream license at ef0383f](https://github.com/lava/matplotlib-cpp/blob/ef0383f1315d32e0156335e10b82e90b334f6d9f/LICENSE).
  This reference identifies the license text, not the header's exact source revision.

External dependencies installed through ROS, apt, or a separate checkout,
including `kindr`, retain their own licenses; their source is not included here.

## Attribution and local changes

The mapping integration follows Elevation Mapping Humanoid and builds on
[ANYbotics elevation_mapping](https://github.com/ANYbotics/elevation_mapping),
[FAST-LIO MID-360](https://github.com/SylarAnh/fast_lio_mid360),
[kindr_ros](https://github.com/ANYbotics/kindr_ros),
[message_logger](https://github.com/ANYbotics/message_logger), and
[pose_publisher](https://github.com/RobotnikAutomation/pose_publisher).
The sensor acquisition components are
[Livox SDK 2](https://github.com/Livox-SDK/Livox-SDK2) and
[Livox ROS Driver 2](https://github.com/Livox-SDK/livox_ros_driver2).
Upstream README files retain their research citations and acknowledgments.

Local changes recorded on 2026-09-30 include an explicit SDK `<cstdint>` include,
corrected build dependencies and installation rules, invalid-point filtering,
TF frame and retry fixes, gravity alignment corrections, pose frame handling,
map configuration fixes, and synthetic mapping tests. On 2026-10-02,
license packaging was added, BSD manifest names were made explicit, the FAST-LIO
manifest was aligned with its supplied license texts, and public setup
documentation was narrowed to the mapping pipeline. Existing upstream license
texts and copyright holders were preserved.

The subsequent 2026-10-02 entry-point cleanup renamed the full MID-360 launch,
removed unused RealSense launch configuration and inactive experimental
comments, changed fixed-transform publication to a single latched publication,
and adjusted diagnostic logging. Original calibration values and YAML parameter
values were retained; upstream examples remain available with their workflow
status documented in the top-level README.
