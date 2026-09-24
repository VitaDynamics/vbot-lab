# Hardware reference

<p align="center">English | <a href="README.zh-CN.md">中文</a></p>

Hardware specifications describe the robot's physical components and their parameters.
They are separate from runtime configuration, calibration data, and software interface contracts.

- [Sensor specification index](sensors.md): applicability and release scope by robot type.
- [Shared robot-dog sensor specification](quadruped-common/sensors.md): one parameter set for
  `foot_quadruped` and `wheel_quadruped`, covering stereo camera, LiDAR, infrared camera, UWB radar, and IMU.
- [Shared robot-dog back mounting and arm adapter plate](quadruped-common/back-mounting.md):
  back-hole dimensions, adapter drawings / STEP and illustrated fasteners for
  `foot_quadruped` and `wheel_quadruped`.

These shared specifications do not apply to `foot_humanoid`; its hardware documentation is pending.
Keep reusable specifications here and link them from the [robot-type guides](../robots/README.md).
Record applicable robot types, product models, and hardware revisions for each specification.
Add a separately scoped specification when hardware differs rather than duplicating or silently replacing shared data.

For software access, see the [interface reference](../interfaces/README.md).
Hardware specifications alone do not establish that a corresponding SDK interface is available.
