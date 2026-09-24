# Sensor specification index

<p align="center">English | <a href="sensors.zh-CN.md">中文</a></p>

Select specifications by robot type. This index retains the original sensor-document
path; parameter tables are maintained in the linked hardware specification only.

| Robot type | Build identifier | Sensor specification | EDU release scope |
| --- | --- | --- | --- |
| Four-legged robot dog | `foot_quadruped` | [Shared robot-dog specification](quadruped-common/sensors.md) | Current release target |
| Four-wheeled robot dog | `wheel_quadruped` | [Same shared robot-dog specification](quadruped-common/sensors.md) | Future release; guide not released |
| Bipedal robot | `foot_humanoid` | Not yet documented; do not use the robot-dog parameters | Future release; guide not released |

The shared specification covers the stereo camera, LiDAR, infrared camera, UWB radar,
and IMU for the documented robot-dog hardware configuration.
Shared sensors do not imply shared firmware, public interfaces, SDK compatibility, or EDU availability.

See the [robot-type guides](../robots/README.md) and
[compatibility matrix](../../release/compatibility.md) before following a device workflow.
