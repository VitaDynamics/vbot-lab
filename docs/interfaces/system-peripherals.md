# System state, display, and ear lights

<p align="center">English | <a href="system-peripherals.zh-CN.md">中文</a></p>

For invocation choices and field mappings, see [direct services versus RCP](../guides/control-paths.md).

For Python/C++ read-only examples, see the [system-peripherals Recipe](../../recipes/system-peripherals/README.md), including Bazel builds, offline previews, and explicit device reads.

Use this family for a system-state dashboard, display observation, and deliberate light
interaction. Complete [device shell setup](../getting-started/device-environment.md) on
`foot_quadruped` EDU. The [interface table](aorta-ros2.md) defines the exact types and ROS
mappings. System/display outputs are read-only; ear modulation is a command input.

## Routes and data meaning

| Aorta topic | Direction | Definition and use |
| --- | --- | --- |
| `/system/sm_status` | Subscribe | System category, flow status, active state/path, severity, heartbeat and descriptive data; distinguish state, OTA and alert messages |
| `/ota_version` | Subscribe | Committed application OTA version string in `version`; ROS uses String.data |
| `/display_node/status` | Subscribe | Display status carried in `data`; inspect the delivered representation, not an assumed image or stable JSON layout |
| `/light/ear_modulation` | Publish | Finite `value` in [0, 1] scales the current ear-light effect brightness; not a color/effect selector |

These are pub/sub interfaces. Display-expression/image services and light-control/gradient
services are separate operations in the [service table](aorta-ros2.md).

## Minimal read-only flow

```bash
timeout 15s aorta schema get /system/sm_status --describe
timeout 15s aorta schema get /display_node/status --describe
timeout 15s aorta schema get /light/ear_modulation --describe
timeout 15s aorta topic echo /system/sm_status --count 1
```

For a display observer, sample the display output instead:

```bash
timeout 15s aorta topic echo /display_node/status --count 1
```

1. For system state, inspect `category`, `status`, `state_id`, `state_name`,
   `active_state_path`, `severity`, and `is_active` together. Category-specific flow status
   is not the terminal result of an unrelated application task.
2. Check `heartbeat_seq` and message freshness before presenting a state as current.
   Keep machine decisions separate from free-form `message`/`data` strings. A state
   observation is not permission to change mode or issue a motion command.
3. ROS exposes the state path as paired ID/name arrays rather than Aorta's entry vector;
   preserve pairing and check lengths. The convenience power-saving flag is not an extra
   ROS field, so the two representations must not be decoded as identical structures.
4. Display status is an observation; receiving it does not prove a person saw a requested
   image. Do not claim pixel-level display contents from a status string alone.

## OTA application version

`/ota_version` is a read-only committed application OTA version string. Its
[Schema](../../schemas/aorta/schemas/topic/system_monitor/ota_version.fbs) defines
`aorta.topic.system_monitor.OtaVersion` with `aorta_header` and `version`.
ROS 2 exposes `std_msgs/msg/String` on the same topic, with Aorta `version`
represented by ROS `data`. The [bridge route](../../schemas/ros2/routes.json)
is Aorta → ROS, with reliable, volatile, keep-last QoS and depth 10.
No service timeout or command rate limit is declared for this output.
Use [system-peripherals](../../recipes/system-peripherals/README.md) with `--stream version`
for Python/C++ SDK reads. Compare the application identifier before any `~` build suffix;
retain the complete string for a support report. This value is not an SDK package version.

```bash
timeout 15s ros2 interface show std_msgs/msg/String
```

## Power-saving service

`/system/power_saving/enable` enters/exits power-saving mode. Its
[Schema](../../schemas/aorta/schemas/service/system/power_saving_enable.fbs) defines
`aorta.services.system.PowerSavingEnableRequest` and
`aorta.services.system.PowerSavingEnableResponse`, both with `aorta_header`.
Request `data=true` enters the mode; `data=false` exits it. Aorta returns
`status` and optional `message`; `ServiceStatus.SUCCESS=0` represents success.
ROS 2 uses `std_srvs/srv/SetBool` on the same name with request `data` and response
`success` and `message`.

The [bridge route](../../schemas/ros2/routes.json) sets a 5000 ms timeout, one in-flight
request, single-writer ownership, 5 requests/s, burst 10, and a 4096-byte request limit.
QoS is reliable, volatile, keep-last, depth 4. No deadman timeout or zero-on-deadman
command is configured. This is a command interface; inspect its type without calling it:

```bash
timeout 15s ros2 interface show std_srvs/srv/SetBool
```

## Ear-light interaction and cleanup

Select the requested effect with the documented light service when needed, then use
modulation only for brightness variation. Use one writer and follow the [command safeguards](aorta-ros2.md).
The ROS bridge rejects non-finite/out-of-range values and restores `1.0` when an active
modulation session ends; that is the neutral multiplier, not lights-off.

Changing the factor while no suitable effect is active may not create a visible effect.
For a direct Aorta publisher, do not assume bridge ownership or timeout restoration applies;
explicitly finish the application's modulation lifecycle. Stop and release publishers on exit.
No publish/service-call command is part of the read-only examples above.

## If observations do not match the application

Check freshness and message category before treating a system-state string as current.
For lights, distinguish an effect-selection request from brightness modulation and inspect
the light-status service contract rather than guessing from the input topic alone.
If a route is quiet or a bounded read exits `124`, check the producer/connection and keep
the UI state unknown; do not automatically trigger effects or restart services.
