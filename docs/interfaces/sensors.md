# Sensors and hardware telemetry

<p align="center">English | <a href="sensors.zh-CN.md">中文</a></p>

For Python/C++ read-only examples, see the [sensors Recipe](../../recipes/sensors/README.md), including Bazel builds, offline previews, and explicit device reads.

Use these outputs for sensor ingestion, a device dashboard, and hardware fault reporting.
They are pub/sub subscriptions, not sensor configuration or actuator commands.
Complete [device shell setup](../getting-started/device-environment.md) first. Scope is
`foot_quadruped` EDU; use the [interface table](aorta-ros2.md) for exact Aorta/ROS types and
mappings and inspect the Schema delivered with the installed firmware.

## Routes and data meaning

| Aorta topic | Meaning and key fields | Typical use |
| --- | --- | --- |
| `/bms_state` | Battery `voltage_mv`, signed `current_ma`, `soc_percent`, alarms, charger connection, and temperature/cell-voltage arrays | Battery dashboard; convert mV/mA to V/A explicitly and use valid element counts, not padded array tails |
| `/imu_raw` | Body IMU orientation, angular velocity, linear acceleration, covariance, `timestamp`, and `frame_id` | Body inertial data; keep the source frame and verify the delivered firmware's angular-velocity/acceleration units before conversion |
| `/lidar_imu` | IMU data associated with the LiDAR, with its own timestamp and frame | Sensor fusion; do not substitute it for the body IMU without a frame transform |
| `/lidar_points` | Point-cloud `fields`, `point_stride`, `data`, timestamp, frame, and pose | Spatial processing; decode field offsets/types and stride instead of casting bytes to a fixed XYZ layout |
| `/lidar_packets` | Timestamped opaque protocol bytes in `data` | Driver-level processing with a decoder for the delivered LiDAR model, not an alternative PointCloud layout |
| `/lidar_diagnostic_status` | A `status` array of named diagnostic entries, each with level, message, and key/value detail | Display OK/WARN/ERROR/STALE; a diagnostic is not a point-cloud sample |
| `/uwb/ranging` | `distance` / `distance_filtered` in meters; `angle`, `pitch`, and `angle_filtered` in degrees; RSSI and `pos_confidence` (0–100) | Relative tag ranging, not a person's map coordinates |
| `/uwb/state` | Connection/ranging `state`, mode, remote battery percentage, and charging state | Distinguish paired, actively ranging, and idle before using ranging data |
| `/uwb/head_touch` | Touch event with `total_count` and `since_boot_count`, including the current event | Event-triggered interaction; per-boot count restarts after reboot |
| `/lowlevel/servo_status` | Per-servo `statuses` identified by ID/name; validity flags, angles, thermal and electrical values | Joint dashboard; angles in degrees and speed in degrees/s; check each validity flag before using its fields |
| `/gnss/fix` | Raw fix status, latitude/longitude in degrees, altitude in meters, covariance, acquisition time, and validity flags | Geographic location; no-fix or unknown covariance must not be treated as a valid zero position |
| `/gnss/fusion` | Fused geographic result with `valid`, `source`, acquisition time, and location | Coarse global location; inspect source and freshness instead of assuming a fresh satellite fix |

## Read and interpret

After logging in, discover once, inspect the routes needed for the task, then sample a
small output. For example, a battery dashboard:

```bash
timeout 15s aorta topic list
timeout 15s aorta schema get /bms_state --describe
timeout 15s aorta topic echo /bms_state --count 1
```

For an inertial-data application, use this instead of sampling every sensor:

```bash
timeout 15s aorta schema get /imu_raw --describe
timeout 15s aorta topic echo /imu_raw --count 1
```

1. Decode with the selected route's Schema. Keep its units, coordinate frame, validity
   flags, and acquisition timestamp with the values. Publish time is not acquisition time.
2. Give each stream a bounded buffer and a freshness deadline appropriate for the application.
   Invalid or stale data should appear as unavailable, not as a zero measurement.
3. Correlate sensor streams by timestamps and known transforms, not message arrival order.
   Check that the clocks are comparable before subtracting timestamps.
4. For touch events, subscribe before the interaction and deduplicate received events;
   account for reboot when using counters. Silence between touches is normal.
5. Close subscriptions when leaving the screen or stopping the application. Collect raw
   point clouds or packets only when needed; they can be substantially larger than status data.

## ROS conversion and recovery

The ROS mappings can have different field layouts. Fused GNSS is split between the fix
output and fusion-extra output; battery fixed arrays and some optional UWB data also need
care. Inspect ROS types independently and follow [conversion notes](aorta-ros2.md).

A missing sample is not proof of a failed sensor. First check the shell, route, Schema,
producer activity, and input conditions: UWB needs a connected tag/ranging session, and a
GNSS stream can legitimately report no fix. Inspect LiDAR diagnostics alongside a missing
cloud. Do not reset hardware or change device services as an automatic response.

Exit `124` from the bounded commands means the wait expired. Report unavailable data and
release resources rather than running an unbounded retry loop.
