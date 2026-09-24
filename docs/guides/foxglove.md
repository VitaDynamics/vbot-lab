# View Aorta topics in Foxglove

<p align="center">English | <a href="foxglove.zh-CN.md">中文</a></p>

Run `aorta-foxglove-bridge` on the robot as `vbot`, then connect Foxglove on your
computer over WebSocket. This is a native Aorta topic viewer, separate from the
ROS 2 compatibility bridge; it does not require a workspace checkout, SDK installation,
Docker, or Bazel on the robot.

To inspect robot geometry, joints or URDF files without a live robot connection,
use [Vbot Viewer](vbot-viewer.md) instead. It is a model tool, not a live topic viewer.

## 1. Connect and prepare the device shell

First follow [device connection and SSH login](../robots/quadruped-common/connection.md).
Run the following in that **device SSH shell**, not on the host or in the development container:

```bash
whoami
export PATH="/opt/vita/aorta/bin:$PATH"
export ZENOH_SESSION_CONFIG_URI=/opt/vita/aorta/edu/edu_session.json5
command -v aorta-foxglove-bridge
test -r "$ZENOH_SESSION_CONFIG_URI"
```

Expect `vbot`, a resolved bridge executable, and a successful readability check.
If any check fails, stop and check the installed device tools; do not change permissions.
PATH locates the executable; ZENOH_SESSION_CONFIG_URI selects the delivered EDU session.
The launch command also supplies that same path explicitly through `--zenoh-config`.
ROS setup files, RMW_IMPLEMENTATION, ROS_DOMAIN_ID and ROS_LOCALHOST_ONLY are not needed
for this native bridge. For persistent shell setup, see [device environment](../getting-started/device-environment.md).
Non-interactive launchers must export the environment themselves rather than assume
that an interactive `.bashrc` was loaded.

## 2. Start the bridge

Both commands below include audio, ASR, and camera streams. Obtain permission from people
whose audio/video will be accessed before starting. The bridge subscribes even with no
viewer connected. Keep the terminal open while viewing.

### With the published configuration

Robot software with the EDU router publishes `/opt/vita/aorta/edu/foxglove_bridge.yaml`.
It selects every robot topic EDU programs can read, plus every topic your own EDU programs
publish:

```bash
aorta-foxglove-bridge \
  --config /opt/vita/aorta/edu/foxglove_bridge.yaml \
  --host 192.168.126.2 \
  --port 8765 \
  --server-name edu-vbot
```

A topic appears in Foxglove after its first message. If the file is missing, the robot
software has no EDU router; use the topic list below.

### With a topic list

Name only the topics you need to reduce device and network load, especially for video
variants and LiDAR. Remove the audio, ASR, and camera entries when they are not needed.

```bash
aorta-foxglove-bridge \
  --group default \
  --zenoh-config /opt/vita/aorta/edu/edu_session.json5 \
  --host 192.168.126.2 \
  --port 8765 \
  --server-name edu-vbot \
  --include audio/uwb_adpcm_segment \
  --include bms_state \
  --include display_node/status \
  --include gnss/fix \
  --include gnss/fusion \
  --include image_left_raw/h265 \
  --include image_left_raw/h265_half \
  --include image_left_raw/h265_quarter \
  --include image_left_raw/h265_undistort \
  --include image_right_raw/h265 \
  --include image_right_raw/h265_half \
  --include image_right_raw/h265_quarter \
  --include imu_raw \
  --include lidar_diagnostic_status \
  --include lidar_imu \
  --include lidar_packets \
  --include lidar_points \
  --include light/ear_modulation \
  --include locomotion/action_report \
  --include locomotion/body/task_report \
  --include locomotion/body_action_status \
  --include locomotion/event \
  --include locomotion/head/task_report \
  --include locomotion/head_status \
  --include locomotion/joy \
  --include locomotion/status \
  --include locomotion/velocity_command \
  --include lowlevel/servo_status \
  --include odometry \
  --include perception/detections2d \
  --include perception/poses \
  --include raw_audio_dump \
  --include rcp/trace \
  --include slam/grid_map/compressed \
  --include slam/static_transforms \
  --include slam/status \
  --include speech/asr_result \
  --include stereo_apriltag/detection \
  --include stereo_left/camera_info \
  --include stereo_right/camera_info \
  --include system/sm_status \
  --include uwb/audio_done \
  --include uwb/head_touch \
  --include uwb/ranging \
  --include uwb/state \
  --include voice/event
```

- `--group default` selects the Aorta group.
- `--host` is the robot's local listening address, not the computer's address.
  Use `192.168.126.2` for the documented wired connection; for another connection,
  replace it with an address actually assigned to the robot and reachable from the computer.
- `--port 8765` is the WebSocket port. If occupied, choose an unused port and update
  the viewer URL; do not stop an unrelated process.
- `--server-name edu-vbot` is a display name; replace it with a recognizable name.
- Repeated `--include` values are topic suffixes without a leading slash, for example
  `imu_raw` for Aorta `/imu_raw`. They select published-topic streams, not ROS topic
  mappings, service calls or RCP task submission.
- Includes narrow published topics, but are not a network-security boundary and do not
  filter the bridge's context/telemetry channels. Do not expose the listener to untrusted
  networks or forward it to the internet.

Command topics such as `locomotion/joy`, `locomotion/velocity_command` and
`light/ear_modulation` are observed as messages here; including them does not send
commands. Use the [interface reference](../interfaces/README.md) for types and meanings.
A configured topic may be idle; inclusion does not start a producer or guarantee data.

## 3. Connect from Foxglove

On the computer, open a **Foxglove WebSocket** connection to `ws://192.168.126.2:8765`.
Use the listening address and port from the previous step. Do not use the computer's
`localhost` for a bridge running on the robot.

Select an available channel in Raw Messages to inspect its decoded fields, then choose
a suitable plotting or visualization panel. Channel discovery and actual message arrival
are separate: check changing values/timestamps. Image rendering also depends on the
message schema and supported encoding; the H.265 streams are compressed video, not raw RGB.

### Topic naming in Foxglove

The bridge uses the **full Aorta transport key** as the Foxglove channel's topic
name, not the short Aorta API name or a ROS 2 mapped name:

```text
Aorta topic:       /<topic>
CLI filter:        --include <topic>
Foxglove topic:    aorta/<group>/pub/<topic>
```

For the `--group default` command above:

| Aorta topic | `--include` value | Foxglove topic |
| --- | --- | --- |
| `/imu_raw` | `imu_raw` | `aorta/default/pub/imu_raw` |
| `/locomotion/status` | `locomotion/status` | `aorta/default/pub/locomotion/status` |
| `/image_left_raw/h265` | `image_left_raw/h265` | `aorta/default/pub/image_left_raw/h265` |
| `/perception/detections2d` | `perception/detections2d` | `aorta/default/pub/perception/detections2d` |
| `/audio/uwb_adpcm_segment` | `audio/uwb_adpcm_segment` | `aorta/default/pub/audio/uwb_adpcm_segment` |
| `/slam/static_transforms` | `slam/static_transforms` | `aorta/default/pub/slam/static_transforms` |

Select the full name in Foxglove's topic picker and saved layouts. There is **no
leading slash** before `aorta/`. The `pub` segment identifies the published-topic
namespace, not a permission to send commands. A different group changes the group
segment; `--server-name` changes only the server display name, not these topic names.
In particular, `/slam/static_transforms` does not become ROS 2 `/tf_static` here.

Other channels, when available, keep their own namespaces:
`aorta/<group>/ctx/<path>` for context and
`aorta/<group>/sys/telemetry/<path>` for telemetry. Do not add `pub/` to these names
or confuse them with the `--include` values for published topics.

The message Schema name (for example `foxglove.RawAudio`) describes the payload
type; it is not the topic name. A missing Schema does not rename the channel.

## 4. Stop and troubleshoot

Press Ctrl+C in the bridge's device terminal to stop it. This foreground procedure does
not configure autostart or modify system services.

| Symptom | Next check |
| --- | --- |
| Executable not found | Device tool availability and PATH in the same shell |
| Session/configuration error | Readable EDU session path and matching explicit configuration |
| Cannot bind address | The address belongs to the robot's current network interface |
| Address already in use | Choose an unused port and update the viewer URL |
| Computer cannot connect | Device IP, cable/network route, chosen port and bridge process |
| Channel appears but has no samples | Producer activity and interface prerequisites; do not issue motion commands merely to generate data |
| Raw messages arrive but a panel is empty | Message schema, encoding and panel support |
| High load or delayed display | Remove unused includes and avoid simultaneous video variants; reconnect with a smaller topic set |

Do not copy session configuration contents or credentials into diagnostics.
