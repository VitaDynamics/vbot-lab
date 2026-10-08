# View Aorta topics in Foxglove

<p align="center">English | <a href="foxglove.zh-CN.md">中文</a></p>

Run `aorta-foxglove-bridge` on the robot as `vbot`, then connect Foxglove on your
computer over WebSocket. This is a native Aorta topic viewer, separate from the
ROS 2 compatibility bridge; it does not require a workspace checkout, SDK installation,
Docker, or Bazel on the robot.

To inspect robot geometry, joints or URDF files without a live robot connection,
use [Vbot Viewer](vbot-viewer.md) instead. It is a model tool, not a live topic viewer.

Choose the connection mode before starting the bridge:

| Connection mode | Bridge listens on the robot | Foxglove connects on the computer |
| --- | --- | --- |
| Wired, direct | `192.168.126.2:8765` | `ws://192.168.126.2:8765` |
| Wi-Fi, through an SSH tunnel | `127.0.0.1:8765` | `ws://127.0.0.1:8765` after starting the tunnel |

The robot's Wi-Fi IP is the **SSH entry address**. It is not necessarily an interface
address in the device shell running the bridge; do not substitute it for `--host`.
The tunnel carries the WebSocket connection through SSH without exposing a separate
WebSocket port on the Wi-Fi network.

## 1. Connect and prepare the device shell

Establish SSH access as `vbot`. For a wired connection, follow
[device connection and SSH login](../robots/quadruped-common/connection.md).
For Wi-Fi, the robot must already be connected and its assigned IP reachable from your
computer. Reuse working public-key access, or complete the linked public-key setup first.
In a **computer terminal**, replace the placeholder with the robot's actual Wi-Fi IP:

```bash
ROBOT_SSH_TARGET='vbot@<robot-wifi-ip>'
ssh "$ROBOT_SSH_TARGET"
```

If you already use an SSH alias for this robot's `vbot` account, set `ROBOT_SSH_TARGET`
to that alias instead, both here and in the tunnel terminal below. Use the same SSH
destination for the shell and tunnel. If login fails, resolve connectivity, authentication
or host-key errors before continuing; do not disable host-key checking.

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
The topic-list commands also supply that same path explicitly through `--zenoh-config`.
ROS setup files, RMW_IMPLEMENTATION, ROS_DOMAIN_ID and ROS_LOCALHOST_ONLY are not needed
for this native bridge. For persistent shell setup, see [device environment](../getting-started/device-environment.md).
Non-interactive launchers must export the environment themselves rather than assume
that an interactive `.bashrc` was loaded.

## 2. Start the bridge

Choose one of the following launch methods; do not start multiple bridges on the same
port. The bridge subscribes even with no viewer connected. Keep this device terminal open
while viewing.

### Wi-Fi: listen on loopback

In the device shell prepared above, start with a small, read-only selection:

```bash
aorta-foxglove-bridge \
  --group default \
  --zenoh-config /opt/vita/aorta/edu/edu_session.json5 \
  --host 127.0.0.1 \
  --port 8765 \
  --server-name edu-vbot \
  --include bms_state \
  --include imu_raw \
  --blacklist-full 'aorta/*/ctx/**' \
  --blacklist-full 'aorta/*/sys/telemetry/**' \
  --ctx-snapshot-interval-ms 0
```

This selects battery and IMU topics, excludes context/telemetry channels and disables
context snapshots; it does not subscribe to audio or camera topics. Keep the bridge
running and create the SSH tunnel in section 3. No system service or network-rule changes
are needed for this workflow.

### Wired: with the published configuration

This configuration and the full topic list below include audio, ASR, and camera streams.
Obtain permission from people whose audio/video will be accessed before starting either.

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

### Wired: with a topic list

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
  Use `192.168.126.2` for the documented wired connection and `127.0.0.1` for the SSH
  tunnel. The Wi-Fi SSH entry IP is not a replacement for either listening address.
- `--port 8765` is the WebSocket port. If occupied, choose an unused port and update
  the direct viewer URL or the tunnel's remote destination port as appropriate;
  do not stop an unrelated process.
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

### Wired, direct connection

On the computer, open a **Foxglove WebSocket** connection to `ws://192.168.126.2:8765`.
Without a tunnel, use the bridge's reachable device address, not the computer's `localhost`.

### Wi-Fi, through an SSH tunnel

Leave the bridge running in the first terminal. Open a **second terminal on the same
computer as Foxglove**, not inside the device SSH shell or a development container.
Replace the placeholder with the same Wi-Fi IP used for the first login, or reuse the
same SSH alias:

```bash
ROBOT_SSH_TARGET='vbot@<robot-wifi-ip>'
ssh -N -T -o ExitOnForwardFailure=yes \
  -L 127.0.0.1:8765:127.0.0.1:8765 "$ROBOT_SSH_TARGET"
```

The first `127.0.0.1:8765` is the computer's local listener. The second is the robot's
loopback address and bridge port, reached from the SSH server. `-N -T` opens no remote
shell and requests no terminal; it does not launch the bridge. A quiet terminal that
keeps running is expected. Keep both terminals open.

In Foxglove, choose **Foxglove WebSocket** and connect to `ws://127.0.0.1:8765`.
`ws://localhost:8765` also works when `localhost` resolves to IPv4 loopback; use the
explicit IPv4 URL if it resolves to `::1` instead. Do not connect to the Wi-Fi IP's
8765 port for this workflow.

If port 8765 is already used **on the computer**, choose another local port:

```bash
ssh -N -T -o ExitOnForwardFailure=yes \
  -L 127.0.0.1:18765:127.0.0.1:8765 "$ROBOT_SSH_TARGET"
```

Then connect Foxglove to `ws://127.0.0.1:18765`; the device bridge still uses 8765.
If the **device** port changes, update `--port` and the final port in `-L` together.
Bind the local forward to `127.0.0.1`, not `0.0.0.0`, to keep it local to your computer.
`ExitOnForwardFailure` detects failure to establish the forwarding listener; it does
not prove that the remote bridge is running or that topics are producing data.

### Check incoming messages

Select an available channel in Raw Messages to inspect its decoded fields, then choose
a suitable plotting or visualization panel. Channel discovery and actual message arrival
are separate: check changing values/timestamps. Image rendering also depends on the
message schema and supported encoding; the H.265 streams are compressed video, not raw RGB.
For the small Wi-Fi selection, use `aorta/default/pub/bms_state` and
`aorta/default/pub/imu_raw`. Expect decoded battery fields and updating IMU timestamps;
an open connection or a channel name alone is not sufficient. To view additional topics,
stop the bridge and adjust its includes using the topic list above, keeping
`--host 127.0.0.1` for the tunnel. Obtain permission before adding audio or camera streams.
The published configuration can also be used through the tunnel by changing its launch
command to `--host 127.0.0.1`; it selects all topics described in section 2.

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

Disconnect Foxglove, then press Ctrl+C in the tunnel terminal, if used, and in the
bridge's device terminal. Stopping the tunnel does not stop the bridge, and stopping
the bridge does not close the tunnel. This foreground procedure does not configure
autostart or modify system services.

| Symptom | Next check |
| --- | --- |
| Executable not found | Device tool availability and PATH in the same shell |
| Session/configuration error | Readable EDU session path and matching explicit configuration |
| Cannot bind address | For wired access, check the device interface address; for a tunnel, use `--host 127.0.0.1`, not the Wi-Fi entry IP |
| Address already in use | Determine whether the computer or device port is occupied, then adjust the matching port and URL; do not stop unrelated processes |
| Computer cannot connect | Device IP, cable/network route, chosen port and bridge process |
| SSH tunnel reports `connect failed: Connection refused` | The bridge is running in the same SSH destination and listening on the loopback address/port at the right of `-L` |
| SSH tunnel reports `administratively prohibited` | The selected SSH endpoint's forwarding policy; stop and contact support rather than changing device permissions or SSH service settings |
| Tunnel stays open but Foxglove cannot connect | Use the local forwarded port on the same computer, try `127.0.0.1` instead of `localhost`, and confirm the remote bridge is still running |
| Channel appears but has no samples | Producer activity and interface prerequisites; do not issue motion commands merely to generate data |
| Raw messages arrive but a panel is empty | Message schema, encoding and panel support |
| High load or delayed display | Remove unused includes and avoid simultaneous video variants; reconnect with a smaller topic set |

Do not copy session configuration contents or credentials into diagnostics.
