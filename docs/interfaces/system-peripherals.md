# System state, display, and ear lights

<p align="center">English | <a href="system-peripherals.zh-CN.md">中文</a></p>

For invocation choices and field mappings, see [direct services versus RCP](../guides/control-paths.md).

For Python/C++ read-only examples, see the [system-peripherals Recipe](../../recipes/system-peripherals/README.md), including Bazel builds, offline previews, and explicit device reads.

Use this family for a system-state dashboard, display observation, and deliberate light
interaction. Complete [device shell setup](../getting-started/device-environment.md) on
`foot_quadruped` EDU / DEV. The [interface table](aorta-ros2.md) defines the exact types and ROS
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

## Fill light

`/light_node/fill_light` is a **service**, not an ear-light topic. Native Aorta uses
[FillLightRequest / FillLightResponse](../../schemas/aorta/schemas/service/peripheral/fill_light.fbs);
ROS 2 uses `peripheral_msgs/srv/FillLight` on the same name.
Set `enable` to the requested state and `brightness` to an integer percentage in
0–100. Values above 100 are invalid; do not substitute the ear-light 0–255 range.
Aorta responds with `status` and `message`; ROS responds with `success` and `message`.
Check the response and confirm the visible state separately. Coordinate ownership and
restore the state your application changed. Discovery does not turn the light on.

## Automatic power-saving policy

`/system/power_saving/set_policy` configures an automatic trigger. It does **not**
immediately put the robot to sleep or wake it. Native Aorta uses
[PowerSavingSetPolicyRequest / PowerSavingSetPolicyResponse](../../schemas/aorta/schemas/service/system/power_saving_set_policy.fbs);
ROS 2 uses `software_msgs/srv/SetPowerSaving` on the same name.

| Request field | Meaning |
| --- | --- |
| `type` | `CHARGING_SLEEP=1`: automatic sleep while charging; `POSE_SLEEP=2`: automatic sleep while lying down. UNKNOWN=0 is not a selectable policy |
| `enable` | Enable or disable that one automatic trigger |

Check Aorta `status` / `message`, or ROS `success` / `message`. A successful reply does not
independently prove durable storage or that the robot has entered sleep. Coordinate
with other applications before changing a policy; do not change it as a connectivity
probe. Use `/system/power_saving/enable` for an explicit sleep/wake operation instead.

For both services, the bridge permits one in-flight request, a 5000 ms timeout,
5 requests/s, burst 10 and at most 4096 request bytes; it does not add a deadman undo.
Inspect without changing either setting:

```bash
timeout 15s aorta schema get /light_node/fill_light --describe
timeout 15s aorta schema get /system/power_saving/set_policy --describe
```

## Display services

### Built-in expressions

`/display_node/play_emotion` uses
[PlayEmotionRequest / PlayEmotionResponse](../../schemas/aorta/schemas/service/peripheral/play_emotion.fbs).
Select an expression by `mode` from the [expression catalog](../resources/expressions.md).

| Request field | Meaning |
| --- | --- |
| `target_state` | 1 starts playback; 0 stops it and restores the configured default expression |
| `req_id`, `pre_check` | Request correlation and preparation/check selector; a successful precheck is not playback |
| `duration_ms` | -1 plays once; 0 loops; a positive value repeats for that many milliseconds, then restores the default |
| `custom_images_name` | Leave empty for built-in expressions. A nonempty value selects a previously registered sequence, not a file path or an upload |

For a custom sequence, register it through the [image-management services](#registered-image-sequences)
first and use its exact name. A nonempty `custom_images_name` takes precedence over `mode`;
a missing name does not fall back to a built-in expression. Do not substitute a file path.
For RCP composition, see the [control-path guide](../guides/control-paths.md).

### Inline JPEG sequences

`/display_node/display_imgs` uses
[DisplayImgsRequest / DisplayImgsResponse](../../schemas/aorta/schemas/service/peripheral/display_imgs.fbs).

| Request field | Meaning |
| --- | --- |
| `images` | Nonempty array of `ShowImg`: `width=480`, `height=854`, `encoding` set to `jpeg` or `jpg`, and `data` containing complete JPEG bytes. Metadata and JPEG headers must both describe 480×854 pixels |
| `duration_ms` | Unsigned per-frame milliseconds; array length must equal the image count. Zero means no deliberate wait, not an indefinite hold |
| `loop` | Default false: play once and restore the default expression. True: repeat until explicitly replaced or stopped |

Native input limits are 4096 frames, 8 MiB per JPEG and 32 MiB total JPEG data.
Decoder support still constrains acceptable JPEG encodings. The ROS bridge limits the
serialized request to 8 MiB including message overhead, not the native total.

The service prepares the first frame before taking over. A `status=SUCCESS` reply
means the first frame was submitted, not that the sequence finished or a person saw it.
Preparation/first-frame failures retain the previous display; later asynchronous failures
require checking status. The player does not deliberately insert a black frame between requests.

Closing the client or receiving a start reply does not stop a loop. Coordinate ownership,
then use `/display_node/play_emotion` with `target_state=0` when finished.
Do not send an empty image array as stop. `/display_node/status` is descriptive text,
not pixel-level confirmation or a request-correlated sequence-completion event.

The compatibility ROS `peripheral_msgs/srv/PlayEmotion` request has no `custom_images_name`;
use the separate full-field ROS entrance below for registered sequences.
ROS `peripheral_msgs/srv/DisplayImgs` has no `loop`; ROS inline playback retains its
existing play-once fields. Native Aorta inline looping uses the matching SDK.

### Registered image sequences

These are **services**, not topics. Registration stores an immutable JPEG sequence for
later playback; it does not change the screen. The three management services share
[custom_images_ctrl.fbs](../../schemas/aorta/schemas/service/peripheral/custom_images_ctrl.fbs).

| Aorta / ROS 2 service | Aorta request / response (namespace `aorta.services.peripheral`) | ROS 2 definition |
| --- | --- | --- |
| `/display_node/add_images` | `AddImagesRequest` / `AddImagesResponse` | [`aorta_msgs/srv/AddImages`](../../schemas/ros2/aorta_msgs/srv/AddImages.srv) |
| `/display_node/get_images_status` | `GetImagesStatusRequest` / `GetImagesStatusResponse` | [`aorta_msgs/srv/GetImagesStatus`](../../schemas/ros2/aorta_msgs/srv/GetImagesStatus.srv) |
| `/display_node/del_images` | `DelImagesRequest` / `DelImagesResponse` | [`aorta_msgs/srv/DelImages`](../../schemas/ros2/aorta_msgs/srv/DelImages.srv) |

Use this lifecycle:

1. **Register.** Set `custom_images_name` to 1–64 ASCII bytes: letters, digits, `_`, `.` or
   `-`, starting with a letter or digit. Supply ordered `images` and `fps` in 1–60
   (default 30). Each JPEG's declared and encoded dimensions must be 480×854.
   A sequence contains 1–4096 frames; one request carries at most **4 MiB of JPEG data**.
   ROS images use [`aorta_msgs/msg/ShowImg`](../../schemas/ros2/aorta_msgs/msg/ShowImg.msg),
   not the similarly named `peripheral_msgs` type.
2. **Finish an upload.** For a small one-request sequence, leave `upload_id`, `frame_offset`,
   `total_frames` and `total_bytes` at defaults. For batches, keep one `upload_id`, repeat
   the sequence totals; use `next_frame_offset` from the reply as the next `frame_offset`.
   Only `complete=true` means the whole sequence is ready. An acknowledged batch is not
   a playable sequence. Identical content under the same name is idempotent; different
   content returns `ALREADY_EXISTS` rather than overwriting the resource.
3. **Query.** Set `custom_images_name` to one name, or empty to list all. Inspect
   [`CustomImageSequenceStatus`](../../schemas/ros2/aorta_msgs/msg/CustomImageSequenceStatus.msg)
   entries (`frame_count`, `fps`, `jpeg_bytes`, `in_use`), JPEG/disk/cache usage and limits,
   and incomplete-upload fields `uploading_seq_name`, `uploaded_frames`, `total_frames`,
   `reserved_bytes`. Query after a timeout before deciding whether to resume or cancel;
   do not automatically submit a different upload. At most one incomplete upload is allowed;
   it expires after 120 seconds without activity.
4. **Play and stop.** Native Aorta calls `/display_node/play_emotion` with the registered
   `custom_images_name`. ROS uses **`/display_node/play_emotion_native`** with
   [`aorta_msgs/srv/PlayEmotion`](../../schemas/ros2/aorta_msgs/srv/PlayEmotion.srv).
   Both reach the same Aorta service; `_native` is a ROS entrance, not another Aorta route.
   Use `target_state=1`; `duration_ms=-1` plays once, `0` loops and a positive value sets
   the playback duration. A start reply acknowledges first-frame submission, not sequence
   completion. Stop with `target_state=0` through the same entrance. The two ROS playback
   entrances share command ownership; do not use them as independent concurrent controllers.
5. **Delete.** Call `/display_node/del_images` with the exact name after stopping playback.
   It deletes a completed sequence or cancels its unfinished upload. Preparation/playback
   can return `BUSY`; wait for release rather than deleting files directly. Deletion cannot
   be undone without registering the images again.

The generated ROS definitions preserve `aorta_header` / `has_aorta_header` and native
`status` / `message`. Check `status=0` (`ServiceStatus.SUCCESS`), not the compatibility
services' `success` boolean. Management replies carry a **string** `error_code`; the
full-field playback response uses an **int32** `error_code`.

The [bridge contracts](../../schemas/ros2/routes.json) allow one in-flight request per route,
5 requests/s with burst 10, and no automatic retry. Registration has a 10 s timeout and
a 4 MiB + 256 KiB serialized request limit; deletion/query/playback have 5 s timeouts and
4096-byte request limits. A timeout does not prove registration/deletion failed.
Use the returned capacity limits instead of assuming storage is unlimited.

After configuring the device shell, inspect the definitions without registering,
playing or deleting anything:

```bash
timeout 15s aorta schema get /display_node/add_images --describe
timeout 15s aorta schema get /display_node/get_images_status --describe
timeout 15s aorta schema get /display_node/del_images --describe
timeout 15s ros2 interface show aorta_msgs/srv/AddImages
timeout 15s ros2 interface show aorta_msgs/srv/GetImagesStatus
timeout 15s ros2 interface show aorta_msgs/srv/DelImages
timeout 15s ros2 interface show aorta_msgs/srv/PlayEmotion
```

The linked `.srv` / `.msg` files are ROS 2 interface source definitions; ROS's `rosidl`
toolchain generates IDL and language bindings from them. Generated definitions are not
an executable client, and discovering a service does not execute its operation.

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
