# Mapping and localization

<p align="center">English | <a href="mapping-localization.zh-CN.md">中文</a></p>

For Python/C++ read-only examples, see the [slam Recipe](../../recipes/slam/README.md), including Bazel builds, offline previews, and explicit device reads.

Use the device's Aorta CLI to check odometry, build and save an indoor map, then localize
in it. This guide covers the current `foot_quadruped` EDU interface set. Confirm the installed
[software scope](../../release/compatibility.md) and live interfaces before proceeding.
This CLI workflow does not require Python SDK installation.

## 1. Connect and prepare

1. Complete [public-key SSH login](../robots/quadruped-common/connection.md), then load the
   [vbot shell environment](../getting-started/device-environment.md). Run all commands below
   in that device shell, not in the development container.
2. Keep the robot stationary for initial checks. Ensure the LiDAR and IMU are unobstructed
   and working. Camera and GNSS streams are not prerequisites for this indoor walkthrough.
3. Before changing modes, confirm no other application is mapping, localizing, or navigating.
   A mode change affects the shared SLAM session. Choose a new map name to avoid overwriting
   a map you need; use only letters, digits, underscores, and hyphens, for example
   `edu_lab_1f`. Use the same chosen name throughout the commands below.
4. Mapping requires supervised movement through a safe area. Use the normal controller,
   keep the stopping control available, and stop motion if pose updates become stale or
   tracking is lost. These instructions do not authorize autonomous movement.

## 2. Check the required interfaces

The following native interfaces are included in the EDU interface set. Discovery alone
does not prove that a producer is running or that the data is usable.

| Data / operation | Aorta CLI route | Primitive and message type | Use |
| --- | --- | --- | --- |
| SLAM state | `/slam/status` | pub/sub; `aorta.topic.slam.SlamStatus` | Mode, odometry/localization/map state, selected map, keyframe count |
| Odometry and dynamic poses | `/odometry` | pub/sub; `aorta.topic.navigation.Odometry` | Pose, velocity, covariance, timestamps, and composite body/head poses |
| Map preview | `/slam/grid_map/compressed` | pub/sub; `foxglove.CompressedImage` | Compressed grid image for a mapping UI |
| Static coordinate transforms | `/slam/static_transforms` | pub/sub; `aorta.topic.slam.TransformArray` | Frame relationships and sensor extrinsics |
| Change mode / save map / relocalize | `/slam/set_slam_mode` | service; `aorta.services.slam.SetSlamModeRequest` / `aorta.services.slam.SetSlamModeResponse` | Control the SLAM workflow |

For sensor checks, the public topics include `/imu_raw`, `/lidar_imu`, and `/lidar_points`.
See [Aorta / ROS 2 interfaces](../interfaces/aorta-ros2.md) for supported ROS mappings.
This walkthrough uses Aorta throughout; do not substitute ROS route names or request syntax.

Run the following read-only checks one at a time:

```bash
timeout 15s aorta topic list
timeout 15s aorta service list
timeout 15s aorta service info /slam/set_slam_mode
timeout 15s aorta topic echo /slam/status --count 3
timeout 15s aorta topic echo /lidar_imu --count 1
timeout 5s aorta topic hz /lidar_points
```

Check that the required routes are discoverable, status timestamps advance, and the input
streams arrive. The frequency command intentionally ends at its deadline; exit 124 only
means the deadline expired, not that reception passed. Odometry and map preview may require
the corresponding mode before they produce data. If discovery, decoding, or sensor reception
fails, resolve that issue before changing modes; do not change permissions or restart services
as part of these checks.

## 3. Understand replies and completion

Service requests below use JSON. Read the response's `status`, `accepted`, and `message`:
`accepted=true` acknowledges a queued request, not completed mapping or localization.
A successful CLI exit also does not imply that the service accepted the request.
The reported `operation_mode` may already name the requested mode before the transition
finishes. Wait for subsequent fresh status and odometry samples, not just the first reply.

| Status field | Values used by this workflow |
| --- | --- |
| `operation_mode` | `ODOMETRY=1`, `MAPPING=2`, `LOCALIZATION=3` |
| `odom_status` | `TRACKING=2`; `DEGRADED=3`, `LOST=4`, `RESETTING=5` need attention |
| `map_status` | `MAPPING=1`, `SAVING=3`, `READY=4`, `SAVE_FAILED=5` |
| `loc_status` | `TRACKING=3`, `LOST=4`, `RELOC=5`, `RELOC_FAILED=6` |
| `current_map_name` | Must match the requested map for saving/localization checks |
| `sensor_timestamp_ns`, `odom_status_seq`, `num_keyframes`, `context` | Freshness, odometry state transitions, mapping coverage, and diagnostic context |

These numeric meanings apply to this documented interface set. Check the delivered contract
when using a different version; unknown values must not be interpreted as success.

## 4. Enter odometry mode

This changes SLAM state and can abandon an unsaved mapping session. Only run it after the
preconditions above are met:

```bash
timeout 15s aorta service call /slam/set_slam_mode '{"mode":1,"map_name":""}' --timeout 5
```

After the service accepts the request, inspect several samples:

```bash
timeout 15s aorta topic echo /slam/status --count 3
timeout 15s aorta topic echo /odometry --count 3
```

Proceed when `operation_mode=1`, `odom_status=2`, and odometry timestamps keep advancing.
A single unchanged pose is normal while stationary; stale timestamps are not.

## 5. Build a map

Start with an empty map name:

```bash
timeout 15s aorta service call /slam/set_slam_mode '{"mode":2,"map_name":""}' --timeout 5
```

Wait for `operation_mode=2`, `map_status=1`, `odom_status=2`, and fresh odometry before moving.
In a separate device terminal, observe status during the supervised mapping session:

```bash
timeout 60s aorta topic echo /slam/status
```

The observation window does not limit or stop mapping. Deliberately continue monitoring if
more time is needed. Cover stable features such as doorways, corners, and corridors; watch
`num_keyframes` grow. A keyframe count alone does not establish sufficient map quality.
Inspect one map preview when needed, rather than continuously dumping image bytes:

```bash
timeout 15s aorta topic echo /slam/grid_map/compressed --count 1
```

If odometry resets and the mode returns to odometry, treat the current mapping attempt as
aborted. Stop moving, wait for stable tracking, and start a new mapping attempt explicitly.

## 6. Save and verify the map

Stop motion at a safe position within the mapped area. While mapping is active, use the
chosen map name with mode 2:

```bash
timeout 15s aorta service call /slam/set_slam_mode '{"mode":2,"map_name":"edu_lab_1f"}' --timeout 5
```

The system saves the map and automatically transitions to localization verification.
Do not immediately send another localization or save request. Observe subsequent status:

```bash
timeout 60s aorta topic echo /slam/status
```

- While `map_status=3`, show “Saving” and prevent duplicate requests.
- Confirm `map_status=4` and `current_map_name="edu_lab_1f"` for map readiness; then also
  require `operation_mode=3`, `loc_status=3`, `odom_status=2`, and fresh odometry for localization readiness.
- `map_status=5` is a save failure. A timeout or missing reply is an unknown outcome:
  inspect fresh status before deciding whether to retry. Ending the CLI command does not
  cancel an already accepted operation.

## 7. Load an existing map or request relocalization

For a later session, select a map already saved on this device:

```bash
timeout 15s aorta service call /slam/set_slam_mode '{"mode":3,"request_reloc":true,"map_name":"edu_lab_1f"}' --timeout 5
```

Wait for the same localization readiness conditions as above. When already in localization
mode with a selected map, an empty name reuses that map:

```bash
timeout 15s aorta service call /slam/set_slam_mode '{"mode":3,"request_reloc":true,"map_name":""}' --timeout 5
```

Do not use the empty-name form to select a map from odometry mode. If localization fails,
check the chosen map, sensor input, and whether the robot is inside the mapped area.
Any small repositioning must remain supervised with a safe stopping method; do not start
navigation merely because the mode-switch request was accepted.

## 8. Use the output in an application

- Keep a single pending mode/save request. Track local receipt time and advancing sensor
  timestamps; choose explicit freshness and completion deadlines for the application.
  A missing, stale, failed, or unknown state must not enable navigation. Record the request,
  reply, and subsequent state changes; `context` is diagnostic text, not a stable enum.
- Odometry carries `frame_id` / `child_frame_id`. Its primary pose is not automatically the
  body pose. Use the paired `body_position_in_map` and `body_orientation_in_map` fields for
  the reported body pose, and `head_position_in_body` with `head_orientation_in_body` for
  the head relative to the body; each position/orientation pair must be present. Translation
  is in meters and quaternions use x/y/z/w components. Do not mix fields from different
  samples. Verify the installed version's frame and origin semantics before comparing
  body poses across mapping, localization, or process initialization.
- Odometry coordinates are relative to their initialization reference. After an origin
  change, convert poses into a common reference frame before combining them with stored
  positions. A `frame_id` of `map` alone is not a persistent map identifier; do not treat
  switching to odometry mode as an origin-reset command.
- Static transforms contain parent `frame_id`, `child_frame_id`, translation, and rotation.
  Subscribe to `/slam/static_transforms` and wait for its periodic publication; a new
  subscriber need not receive an immediate snapshot. The ROS bridge exposes these transforms
  on `/tf_static`; use reliable, transient-local QoS for the retained static snapshot.
  Dynamic `/tf` is derived separately from odometry. Read-only subscription commands are in
  the [interface reference](../interfaces/aorta-ros2.md).
- Grid preview bytes are a PNG image. The `format` string also carries
  `png;resolution=...;x_min=...;y_min=...`; preserve the resolution and origin metadata when
  displaying it. A thumbnail is not proof that saving or localization has completed.
- Maintain map display names, rooms, areas, and named destinations in the application as
  needed. Store a map name as an identifier, not a device filesystem path. This workflow
  selects known maps; it does not introduce a map-list or map-upload API.

## Stop and recover

Stopping a terminal command does not stop the robot or SLAM. Stop robot movement using the
normal controller first. To deliberately abandon mapping or leave localization, confirm
that no save/transition is pending and that losing unsaved mapping work is acceptable, then
use the odometry-mode command in step 4 and verify fresh status. It is not an emergency-stop
command. Do not automatically switch modes when another application owns the session.
