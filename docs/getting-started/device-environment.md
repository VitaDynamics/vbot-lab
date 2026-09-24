# Device shell environment

<p align="center">English | <a href="device-environment.zh-CN.md">中文</a></p>

Configure the `vbot` account's Bash environment before using Aorta or ROS 2 tools on the
robot. This guide targets the current `foot_quadruped` EDU software with the public
`/opt/vita` tool paths. Check the [version scope](../../release/compatibility.md) first;
shared robot-dog connection instructions do not imply identical software support.

Aorta is the native communication layer. The system starts `aorta_ros2_bridge` to preserve
a subset of the previously published ROS 2 interfaces. You only load the client environment;
you do not need to start the bridge yourself. See [available interfaces](../interfaces/aorta-ros2.md).

## 1. Select the right terminal

Follow the [wired connection guide](../robots/quadruped-common/connection.md), then run the
following in the robot's SSH terminal, not your workstation or development container:

```bash
whoami
test -x /opt/vita/aorta/bin/aorta
test -r /opt/vita/aorta/edu/edu_session.json5
test -r /opt/vita/ros/humble/setup.bash
test -r /opt/vita/aorta/ros/local_setup.bash
```

Expect `vbot` and a successful exit status from each `test` (no output on success).
If a path is missing or unreadable, stop and check the installed software version and
delivery with support. Do not work around this by changing device permissions.
Use the public paths below; no other environment bootstrap script is required.

## 2. Load and persist the environment

First run this block in the current Bash shell. Stop if either `source` command reports an
error. Load the ROS base before the bridge message-type overlay, then set the DDS options:

```bash
# BEGIN VBOT EDU environment
export PATH="/opt/vita/aorta/bin:$PATH"
export ZENOH_SESSION_CONFIG_URI=/opt/vita/aorta/edu/edu_session.json5

source /opt/vita/ros/humble/setup.bash
source /opt/vita/aorta/ros/local_setup.bash
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
export ROS_DOMAIN_ID=178
export ROS_LOCALHOST_ONLY=1
# END VBOT EDU environment
```

To keep this setup, back up the `vbot` account's existing `~/.bashrc` to an unused filename,
then add this block once using a text editor (create the file if needed). If a VBOT block
already exists, update it in place. Preserve unrelated settings and check for later lines
that override these variables. Do not add this block to the workstation's `.bashrc`.

Check the edited file's syntax before loading it:

```bash
bash -n ~/.bashrc && source ~/.bashrc
```

Run `source` only if the syntax check succeeds. Loading `.bashrc` also executes its other
commands, so review existing content first. Repeated sourcing prepends another copy of the
Aorta directory to `PATH`; do not keep appending or sourcing the block in a loop.
Open a fresh SSH session and repeat the checks below to verify persistence. If an interactive
login does not read `.bashrc`, inspect the user's existing login startup file and ensure it
sources `.bashrc`; do not replace that file wholesale.

| Setting | Purpose |
| --- | --- |
| `PATH` | Finds the device's Aorta command-line tools |
| `ZENOH_SESSION_CONFIG_URI` | Selects the delivered EDU Aorta session configuration; do not edit the delivered file (the [SDK quickstart](../../packages/aorta/python/README.md) covers the off-robot copy) |
| ROS base + bridge overlay | Loads ROS 2 Humble tools and the bridge's ROS message/service types |
| `RMW_IMPLEMENTATION` | Uses the bridge's Fast DDS middleware |
| `ROS_DOMAIN_ID` | Selects domain `178` |
| `ROS_LOCALHOST_ONLY` | Limits ROS discovery to the device itself |

ROS 2 commands must run on the device: this bridge's DDS transport is local-only.
Setting the same domain on a computer does not expose it remotely, and changing
`ROS_LOCALHOST_ONLY` alone does not create a supported remote connection.
This Aorta session file also configures a device-side client, not a workstation client.

## 3. Check the loaded shell without contacting interfaces

```bash
command -v aorta
command -v ros2
printf 'ZENOH_SESSION_CONFIG_URI=%s\n' "$ZENOH_SESSION_CONFIG_URI"
printf 'RMW_IMPLEMENTATION=%s\n' "$RMW_IMPLEMENTATION"
printf 'ROS_DOMAIN_ID=%s\n' "$ROS_DOMAIN_ID"
printf 'ROS_LOCALHOST_ONLY=%s\n' "$ROS_LOCALHOST_ONLY"
```

Both commands should resolve; the variables should match the setup block.
For a machine-readable check, run [check_device_environment.py](../../tools/check_device_environment.py)
with Python 3.10+ **in that same device shell**. If the checkout is on the device:

```bash
python3 tools/check_device_environment.py
```

Run from the checkout root, or use the file's absolute path. Alternatively, transfer only
that standalone file to a user-owned directory as a separate, requested action; it needs
no SDK or other checkout files. Do not run the workstation checker with a device profile.

The JSON report checks the effective account, public file access, executable lookup, and
selected environment variables. Exit `0` means these shell checks passed; `1` means something
needs attention; `2` means invalid arguments. It never sources scripts, reads the session
configuration contents, edits files, runs discovered tools, opens network connections, or
checks live interfaces. Passing does not prove the ROS overlay's types can load, the SDK is
installed, or any robot function works.

## 4. Discover interfaces and receive one sample

These are separate, read-only device operations. Run them only when device checks are in
scope. Keep the robot stationary; do not publish control messages or invoke services to
test environment setup. Run each command separately and inspect its result:

```bash
timeout 15s aorta topic list
timeout 15s aorta service list
timeout 15s aorta schema get /imu_raw
timeout 15s aorta topic echo /imu_raw --count 1
```

Aorta lists may include directory entries marked `absent`. A listed route or retrievable
Schema is not evidence that samples are arriving. Expect a decoded IMU sample from the last
command; record a timeout as inconclusive/no sample in the observation window, not success.

```bash
timeout 15s ros2 topic list --no-daemon -t
timeout 15s ros2 service list --no-daemon -t
timeout 15s ros2 interface show sensor_msgs/msg/Imu
timeout 15s ros2 topic echo /imu_raw sensor_msgs/msg/Imu --no-daemon --once --qos-reliability best_effort
timeout 15s ros2 topic echo /servo/status --no-daemon --once --qos-reliability best_effort
```

`--no-daemon` avoids reusing a CLI daemon started with a different environment. IMU checks a
standard ROS type; `/servo/status` additionally exercises a bridge-specific type from the
overlay. The Humble [echo options](https://github.com/ros2/ros2cli/blob/humble/ros2topic/ros2topic/verb/echo.py)
support one-sample and best-effort subscriptions. `timeout` bounds each check even if no
publisher is active; exit `124` means the time limit expired, not a passed check. Do not
automatically retry forever or stop/restart system services.

Report environment checks, discovery, Schema/type loading, and actual sample reception
separately. Do not require an exact topic count: auxiliary and derived ROS topics, inactive
producers, and version-specific interface sets can change the list. Start with one stream;
concurrent high-bandwidth subscriptions require separate performance validation.

## Non-interactive commands and user-program startup

An SSH command, Coding Agent tool shell, or autostart process may not read interactive
`.bashrc` (many files return early for non-interactive shells). A child process inherits its
parent's exported environment; editing `.bashrc` does not update already-running processes.
For a non-interactive Bash script, place the same environment block before the command that
needs Aorta/ROS 2 and stop if sourcing fails. Do not assume `bash -lc` or `source ~/.bashrc`
loads this block in every startup configuration.

The same rule applies to a user program started by `/userdata/vbot/init.sh`: load the block
in a Bash launcher before starting that program. If the existing entry uses `/bin/sh`, keep
it intact and invoke a Bash launcher rather than inserting Bash `source` syntax into it.
Editing a startup script is a separate requested change, not part of the checker. This
environment setup changes neither account permissions nor process resource limits.

The system calls this entry as vbot during boot. For the complete launcher, executable
permissions, background startup, logs, and disable procedure, follow
[user-program autostart](../guides/user-autostart.md).

## Troubleshooting

| Symptom | Next check |
| --- | --- |
| `aorta` not found | Public binary exists and `/opt/vita/aorta/bin` is on this shell's `PATH` |
| `ros2` not found | Both setup files are readable and sourced successfully in order |
| Only `/parameter_events` and `/rosout` | Device-local terminal, domain `178`, RMW, full environment, and `--no-daemon`; then check version support |
| Unknown ROS package/type | Bridge overlay loading and delivered message types; a discovered topic does not prove local typesupport is present |
| Aorta Schema query times out | Session path, readable delivered configuration, route spelling and current interface scope |
| A topic is listed but echo times out | Producer activity, type loading, QoS, and the documented interface requirements; no sample is not proof of a sensor failure |
| New SSH session loses the environment | Effective user's `.bashrc`, login startup chain, and later variable overrides |
| CLI works but an application/startup script fails | Its own parent environment, Bash loading, dependencies, and architecture/ABI |

For interface access issues, use the [available interface reference](../interfaces/aorta-ros2.md)
and provide the software version, command, exit status, and a short redacted error report.
Do not include session configuration contents or access tokens.
