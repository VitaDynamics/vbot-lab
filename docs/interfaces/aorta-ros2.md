# Aorta and ROS 2 compatibility

<p align="center">English | <a href="aorta-ros2.zh-CN.md">中文</a></p>

Aorta is the native communication layer for VBOT EDU robots. `aorta_ros2_bridge` preserves
a subset of previously published ROS 2 interfaces; it is not a second, fully equivalent
robot interface. Start with the [device shell setup](../getting-started/device-environment.md).

## Version scope

This reference covers `foot_quadruped` EDU software. Interface availability depends on the
installed firmware; discover the exact routes and inspect their delivered types before use.
Minimum firmware versions for all entries are not yet published. Other robot types are
not covered by this software scope.

This page lists the public topic set and supported mappings, along with services and the
RCP action. The topic tables contain 46 distinct Aorta routes: 43 subscription outputs
and 3 command inputs. After discovering an output, take a bounded sample to check its
producer; do not publish to command topics as an environment check.
Python SDK wheel installation and checked-in Schema sources are documented separately;
device CLI access does not require installing the Python SDK.

For the native Aorta SLAM workflow, including map saving, localization, and coordinate data,
see [Mapping and localization](../guides/mapping-localization.md).

## Use by interface family

Each family explains purpose, data meaning, reading flow, and recovery. Select a family for
the task, then inspect only the routes it needs; individual topics are not separate
capability-check entries.

| Family | Coverage |
| --- | --- |
| [Sensors and hardware telemetry](sensors.md) | Battery, IMU, LiDAR, UWB, GNSS, servo feedback |
| [Cameras and AprilTags](cameras.md) | Calibration, compressed video, tag detection |
| [Perception](perception.md) | Object detections and human keypoints |
| [Audio](audio.md) | Audio frames, ASR text, voice events, UWB input completion |
| [Locomotion](locomotion.md) | State, terminal reports, joystick/velocity inputs |
| [System and peripherals](system-peripherals.md) | System state, display, ear-light modulation |
| [RCP](rcp.md) | Task action and trace events |
| [SLAM](../guides/mapping-localization.md) | Odometry, maps, transforms, mapping/localization workflow |

## Read-only topics for discovery and inspection

Names below are user-facing Aorta CLI routes, not transport key expressions. `pub/sub`
describes the communication primitive; the direction is from the developer's perspective.
The tables are not full field contracts or guarantees of continuous data. Use CLI discovery
for the installed version's list. ROS middleware topics such as logs and parameters are not
robot capabilities and are not included in this list.

| Purpose | Aorta topic | ROS 2 topic | Primitive / developer direction | Aorta root type | ROS 2 message type |
| --- | --- | --- | --- | --- | --- |
| [Battery](sensors.md) | `/bms_state` | `/bms_state` | pub/sub — subscribe | `bms.BmsState` | `lowlevel_msg/msg/BmsState` |
| [Body IMU](sensors.md) | `/imu_raw` | `/imu_raw` | pub/sub — subscribe | `aorta.topic.sensor.Imu` | `sensor_msgs/msg/Imu` |
| [LiDAR IMU](sensors.md) | `/lidar_imu` | `/lidar_imu` | pub/sub — subscribe | `aorta.topic.sensor.Imu` | `sensor_msgs/msg/Imu` |
| [LiDAR point cloud](sensors.md) | `/lidar_points` | `/lidar_points` | pub/sub — subscribe | `foxglove.PointCloud` | `sensor_msgs/msg/PointCloud2` |
| [LiDAR diagnostics](sensors.md) | `/lidar_diagnostic_status` | `/lidar_diagnostic_status` | pub/sub — subscribe | `aorta.topic.sensor.DiagnosticArray` | `diagnostic_msgs/msg/DiagnosticArray` |
| [LiDAR packets](sensors.md) | `/lidar_packets` | `/lidar_packets` | pub/sub — subscribe | `aorta.topic.sensor.LidarPacket` | `aorta_msgs/msg/LidarPacket` |
| [UWB ranging](sensors.md) | `/uwb/ranging` | `/uwb/data` | pub/sub — subscribe | `aorta.uwb.UwbRangingData` | `uwb_location/msg/UWB` |
| [UWB state](sensors.md) | `/uwb/state` | `/uwb/state` | pub/sub — subscribe | `aorta.uwb.UwbState` | `uwb_msgs/msg/Status` |
| [Head-touch event](sensors.md) | `/uwb/head_touch` | `/uwb/head_touch` | pub/sub — subscribe | `aorta.uwb.HeadTouchEvent` | `aorta_msgs/msg/HeadTouchEvent` |
| [Servo state](sensors.md) | `/lowlevel/servo_status` | `/servo/status` | pub/sub — subscribe | `lowlevel.ServoStatuses` | `lowlevel_msg/msg/ServoStatuses` |
| [Raw GNSS fix](sensors.md) | `/gnss/fix` | `/gnss/fix` | pub/sub — subscribe | `aorta.topic.gnss.NavSatFix` | `sensor_msgs/msg/NavSatFix` |
| [Fused GNSS; split representation](sensors.md) | `/gnss/fusion` | `/gnss/fusion` + `/gnss/fusion_extra` | pub/sub — subscribe | `gnss.GnssFusion` | `sensor_msgs/msg/NavSatFix` + `aorta_msgs/msg/GnssFusionExtra` |
| [Odometry + derived dynamic TF](../guides/mapping-localization.md) | `/odometry` | `/odometry` + `/tf` | pub/sub — subscribe | `aorta.topic.navigation.Odometry` | `nav_msgs/msg/Odometry` + `tf2_msgs/msg/TFMessage` |
| [Static coordinate transforms](../guides/mapping-localization.md) | `/slam/static_transforms` | `/tf_static` | pub/sub — subscribe | `aorta.topic.slam.TransformArray` | `tf2_msgs/msg/TFMessage` |
| [SLAM state](../guides/mapping-localization.md) | `/slam/status` | `/slam/status` | pub/sub — subscribe | `aorta.topic.slam.SlamStatus` | `slam_msgs/msg/SlamStatus` |
| [Compressed grid map](../guides/mapping-localization.md) | `/slam/grid_map/compressed` | `/grid_map/compressed` | pub/sub — subscribe | `foxglove.CompressedImage` | `foxglove_msgs/msg/CompressedImage` |
| [Left camera calibration](cameras.md) | `/stereo_left/camera_info` | `/stereo_left/camera_info` | pub/sub — subscribe | `foxglove.CameraCalibration` | `sensor_msgs/msg/CameraInfo` |
| [Right camera calibration](cameras.md) | `/stereo_right/camera_info` | `/stereo_right/camera_info` | pub/sub — subscribe | `foxglove.CameraCalibration` | `sensor_msgs/msg/CameraInfo` |
| [Left H.265 video](cameras.md) | `/image_left_raw/h265` | `/image_left_raw/h265` | pub/sub — subscribe | `foxglove.CompressedVideo` | `foxglove_msgs/msg/CompressedVideo` |
| [Left H.265 half stream](cameras.md) | `/image_left_raw/h265_half` | `/image_left_raw/h265_half` | pub/sub — subscribe | `foxglove.CompressedVideo` | `foxglove_msgs/msg/CompressedVideo` |
| [Left H.265 quarter stream](cameras.md) | `/image_left_raw/h265_quarter` | `/image_left_raw/h265_quarter` | pub/sub — subscribe | `foxglove.CompressedVideo` | `foxglove_msgs/msg/CompressedVideo` |
| [Left undistorted H.265 video](cameras.md) | `/image_left_raw/h265_undistort` | `/image_left_raw/h265_undistort` | pub/sub — subscribe | `foxglove.CompressedVideo` | `foxglove_msgs/msg/CompressedVideo` |
| [Right H.265 video](cameras.md) | `/image_right_raw/h265` | `/image_right_raw/h265` | pub/sub — subscribe | `foxglove.CompressedVideo` | `foxglove_msgs/msg/CompressedVideo` |
| [Right H.265 half stream](cameras.md) | `/image_right_raw/h265_half` | `/image_right_raw/h265_half` | pub/sub — subscribe | `foxglove.CompressedVideo` | `foxglove_msgs/msg/CompressedVideo` |
| [Right H.265 quarter stream](cameras.md) | `/image_right_raw/h265_quarter` | `/image_right_raw/h265_quarter` | pub/sub — subscribe | `foxglove.CompressedVideo` | `foxglove_msgs/msg/CompressedVideo` |
| [Stereo AprilTag detection](cameras.md) | `/stereo_apriltag/detection` | `/function/stereo_tag_detection` | pub/sub — subscribe | `aorta.topic.sensor.StereoTagDetection` | `function_msgs/msg/StereoTagDetection` |
| [2D object detection, including people](perception.md) | `/perception/detections2d` | `/perception/detections2d` | pub/sub — subscribe | `perception.Detection2DArray` | `vision_msgs/msg/Detection2DArray` |
| [Human 2D keypoints](perception.md) | `/perception/poses` | `/perception/poses` | pub/sub — subscribe | `perception.PoseDetection` | `vision_msgs/msg/PoseDetection` |
| [Locomotion state](locomotion.md) | `/locomotion/status` | `/locomotion/status` | pub/sub — subscribe | `locomotion.LocomotionStatus` | `software_msgs/msg/LocomotionStatus` |
| [Body action state](locomotion.md) | `/locomotion/body_action_status` | `/locomotion/body_action_status` | pub/sub — subscribe | `locomotion.BodyActionStatus` | `function_msgs/msg/BodyActionStatus` |
| [Head state](locomotion.md) | `/locomotion/head_status` | `/locomotion/head_status` | pub/sub — subscribe | `locomotion.HeadStatus` | `aorta_msgs/msg/HeadStatus` |
| [Body task reports](locomotion.md) | `/locomotion/body/task_report` | `/locomotion/body/task_report` | pub/sub — subscribe | `aorta.topic.task.TaskReport` | `aorta_msgs/msg/TaskReport` |
| [Head task reports](locomotion.md) | `/locomotion/head/task_report` | `/locomotion/head/task_report` | pub/sub — subscribe | `aorta.topic.task.TaskReport` | `aorta_msgs/msg/TaskReport` |
| [Action reports](locomotion.md) | `/locomotion/action_report` | `/locomotion/action_report` | pub/sub — subscribe | `locomotion.ActionReport` | `aorta_msgs/msg/ActionReport` |
| [Locomotion events](locomotion.md) | `/locomotion/event` | `/locomotion/event` | pub/sub — subscribe | `locomotion.LocomotionEvent` | `software_msgs/msg/LocomotionEvent` |
| [RCP task trace events](rcp.md) | `/rcp/trace` | `/rcp/trace` | pub/sub — subscribe | `aorta.topic.rcp.TraceEvent` | `function_msgs/msg/TraceEvent` |
| [System state machine](system-peripherals.md) | `/system/sm_status` | `/sm/status` | pub/sub — subscribe | `sm.SmStatus` | `software_msgs/msg/SystemStateMachineStatus` |
| [Display state](system-peripherals.md) | `/display_node/status` | `/display_node/status` | pub/sub — subscribe | `aorta.topic.peripheral.DisplayStatus` | `aorta_msgs/msg/DisplayStatus` |
| [Voice interaction events](audio.md) | `/voice/event` | `/voice/event` | pub/sub — subscribe | `aorta.voice.VoiceEvent` | `aorta_msgs/msg/VoiceEvent` |
| [Final recognized text; provider distinguishes body / UWB input](audio.md) | `/speech/asr_result` | `/speech/asr_result` | pub/sub — subscribe | `aorta.topic.speech.AsrResult` | `aorta_msgs/msg/AsrResult` |
| [Robot-body microphone audio frames](audio.md) | `/raw_audio_dump` | `/raw_audio_dump` | pub/sub — subscribe | `foxglove.RawAudio` | `foxglove_msgs/msg/RawAudio` |
| [UWB signalling audio frames from the remote control](audio.md) | `/audio/uwb_adpcm_segment` | `/audio/uwb_adpcm_segment` | pub/sub — subscribe | `foxglove.RawAudio` | `foxglove_msgs/msg/RawAudio` |
| [UWB audio input-end event](audio.md) | `/uwb/audio_done` | `/uwb/audio_done` | pub/sub — subscribe | `aorta.uwb.AudioDoneEvent` | `aorta_msgs/msg/AudioDoneEvent` |

IMU, LiDAR, images, maps, and audio can have substantial bandwidth or privacy implications.
For initial checks use one IMU stream and a short deadline, not every topic concurrently.
Camera variants and other state/event streams should be selected by exact discovered name,
not by assuming a wildcard describes a single endpoint.

## Command topics

All three routes below are **pub/sub inputs**: the application publishes; the ROS bridge
forwards ROS → Aorta. They are not robot-state subscriptions. Before publishing, select one
control owner, inspect the delivered type and QoS, and define cleanup and stopping behavior.
For motion, confirm the operating mode, a supervised safe area, and a reachable stopping
control. Do not send placeholder or zero-valued test messages during discovery.

| Purpose | Aorta topic | ROS 2 topic | Primitive / developer direction | Aorta root type | ROS 2 message type |
| --- | --- | --- | --- | --- | --- |
| [Joystick control input](locomotion.md) | `/locomotion/joy` | `/joy` | pub/sub — publish | `locomotion.Joy` | `sensor_msgs/msg/Joy` |
| [Velocity control input](locomotion.md) | `/locomotion/velocity_command` | `/vel_cmd` | pub/sub — publish | `aorta.topic.navigation.Twist` | `geometry_msgs/msg/Twist` |
| [Ear-light brightness modulation](system-peripherals.md) | `/light/ear_modulation` | `/light/ear_modulation` | pub/sub — publish | `aorta.topic.peripheral.EarModulation` | `aorta_msgs/msg/EarModulation` |

- Joystick axes must be finite and within the normalized range [-1, 1]. Do not invent an
  axis/button mapping from the generic ROS type. The native Joy message has no ROS header;
  ROS timestamp and frame identity are not carried into it.
- Velocity commands can move the robot. Do not infer permitted axes, units, speed limits,
  or a safe stopping procedure from a Twist message alone; use the installed control contract.
- Ear modulation is a finite `value` in [0, 1] multiplying the current ear-light brightness.
  It does not select an RGB color or start an effect; use the light-control or gradient
  service for those operations. When an active ROS forwarding session ends, the bridge
  restores the neutral factor `1.0`, not darkness.
- The ROS command bridge enforces single-writer ownership, input validation, and a missing-input
  timeout. Rejected frames are dropped, not silently clamped. On an active session ending,
  motion routes send their terminal zero command and stop forwarding; this is not a substitute
  for the robot's normal stopping control. These are **bridge** behaviors, not promises that
  arbitrary direct Aorta publishers receive the same ownership or timeout protection.
- An `armed` diagnostic means the command route is ready to consider input, not that a
  command has executed. `NEVER_SEEN` can mean no command has arrived; `DEADMAN_STOP` can
  mean the previous input stream ended. Check current safety, ownership, and connection
  fields before interpreting the state.

## Services and control interfaces

Services are request/reply interfaces, not topics to subscribe to. Discover them with
`aorta service list` and `ros2 service list --no-daemon -t`. Do not call them as an automatic
environment check, even when their purpose is read-only.

| Aorta service | ROS 2 service | Purpose / developer operation |
| --- | --- | --- |
| `/firmware_version/motor` | `/firmware_version/motor` | service — query motor firmware |
| `/firmware_version/servo` | `/firmware_version/servo` | service — query servo firmware |
| `/firmware_version/lidar` | `/firmware_version/lidar` | service — query LiDAR firmware |
| `/firmware_version/uwb` | `/firmware_version/uwb` | service — query UWB firmware |
| `/display_node/get_supported_emotions` | `/display_node/get_supported_emotions` | service — query available expressions |
| `/display_node/play_emotion` | `/display_node/play_emotion` | service — play an expression |
| `/display_node/display_imgs` | `/display_node/display_imgs` | service — display images |
| `/light_node/status` | `/light_node/status` | service — query ear-light state, despite the name `status` |
| `/light_node/control` | `/light_node/control` | service — control the ear-light effect |
| `/light_node/gradient` | `/light_node/gradient` | service — set an ear-light gradient |
| `/locomotion/lowlevel_action` | `/sm/action/lowlevel` | service — body control; not a ROS action |
| `/locomotion/head_action` | `/head_action` | service — head control |
| `/locomotion/set_run_mode` | `/locomotion/set_run_mode` | service — change run mode |
| `/locomotion/runtime_control` | `/locomotion/runtime_control` | service — change locomotion runtime settings |
| `/slam/set_slam_mode` | `/slam/set_slam_mode` | service — mapping, saving, and localization modes |
| `/slam/get_path_to_target` | `/slam/get_path_to_target` | service — request a path; not a motion command |
| `/slam/query_map` | `/slam/query_map` | service — query map data |
| `/volume_control` | `/volume_control` | service — query/change audio volume according to request |
| `/speech/set_speak` | `/set_speak` | service — speech playback/control |

Firmware queries require the appropriate `target_device_type`: MOTOR=`0`, SERVO=`1`,
LIDAR=`2`, UWB=`3`. Inspect the delivered request type before calling; an empty/default request
is not valid for every device class. The table does not supply control payloads or relax
operation-specific preconditions.

## RCP task action

`/rcp/execute_task` is an **action**, not a topic or service. It accepts a DAG or preset,
reports progress, produces a terminal result, and supports cancellation.

| Aorta action | Goal / result / feedback data roots | ROS 2 action | ROS 2 action type |
| --- | --- | --- | --- |
| `/rcp/execute_task` | `aorta.action.rcp.ExecuteTaskGoal` / `aorta.action.rcp.ExecuteTaskResult` / `aorta.action.rcp.ExecuteTaskFeedbackData` | `/rcp/execute_task` | `aorta_msgs/action/ExecuteTask` |

See [RCP tasks and tracing](rcp.md) for goal input, progress, terminal results, cancellation,
concurrency limits, and trace consumption. Provider inspection does not submit a goal;
executing a DAG requires deliberate intent.

## Read-only system and transform checks

System state is available natively through `/system/sm_status` and through ROS `/sm/status`.
Static transforms are available through `/slam/static_transforms` and ROS `/tf_static`.
Dynamic `/tf` remains derived from odometry. Run one bounded check at a time in the device shell:

```bash
timeout 15s aorta topic echo /system/sm_status --count 1
timeout 15s ros2 topic echo /sm/status software_msgs/msg/SystemStateMachineStatus --no-daemon --once --qos-reliability best_effort
timeout 15s aorta topic echo /slam/static_transforms --count 1
timeout 15s ros2 topic echo /tf_static tf2_msgs/msg/TFMessage --no-daemon --once --qos-reliability reliable --qos-durability transient_local
```

The native static-transform source refreshes periodically; allow time for a new sample.
ROS static TF uses transient-local durability, so request that durability to receive the
retained snapshot. Do not republish those same child frames from a second static-TF source.

To inspect bridge route state without commanding the robot:

```bash
timeout 15s ros2 topic echo /aorta_bridge/diagnostics diagnostic_msgs/msg/DiagnosticArray --no-daemon --once --qos-reliability best_effort
```

Some outputs activate only when a subscriber is present. An inactive route waiting for a
reader is not an unimplemented interface. Event streams can remain quiet between events;
an old event's age is not itself a sensor fault. Inspect the route's reason and take an
appropriate bounded sample rather than assuming every listed topic publishes continuously.

## Data interpretation and subscriptions

- Equal route names do not mean equal serialization, fields, or semantics. Query Aorta
  Schema and ROS types separately before decoding; the bridge performs conversion.
- ROS `/tf` is derived from odometry.
- Some battery timestamps have no ROS counterpart; some ADC fields are zero-filled.
  Observe valid element counts in battery arrays, not unused fixed-array tail values.
- GNSS detail is split across the standard fix and fusion-extra outputs; some UWB fields
  are omitted or defaulted. Some service results combine detailed status into booleans.
  The documented ROS map-query interface does not apply the radius; its returned point cloud uses XYZI.
- Subscribe only to the streams the application needs. Use bounded queues and check
  timestamps so that stale data is not used after a processing or network delay.

If data does not arrive, check the device shell environment, selected route, message type,
and producer state. See [device shell setup](../getting-started/device-environment.md)
for the discovery and single-sample commands.
