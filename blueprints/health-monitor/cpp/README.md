# C++ read-only health monitor

<p align="center">English | <a href="README.zh-CN.md">中文</a></p>

C++17 / Aorta C++ SDK implementation of the [health-monitor Blueprint](../README.md).
It combines `/locomotion/status`, `/bms_state` and `/system/sm_status`; it never publishes
control messages, calls services/actions, or records audio/video. Use foot_quadruped
application V1.6.0-12, SDK 2026.10.12 / ABI 13 and Schema pack 2026.10.13-v4 from
Release edu-sdk-2026.10.14. No Python runtime or wheel is needed on the robot.

## Build and preview — development container

Prepare the native x86_64 SDK and Schema directories using the [C++ SDK guide](../../../packages/aorta/cpp/README.md).
Set AORTA_CPP_SDK_DIR / AORTA_EDU_SCHEMA_DIR to those verified, extracted paths.
From the checkout root, inside the existing development container:

```bash
bazel build //blueprints/health-monitor:main_cpp &&
bazel test //blueprints/health-monitor:model_cpp_test \
  //blueprints/health-monitor:sdk_cpp_test //tests:health_monitor_cpp_test &&
bazel run //blueprints/health-monitor:main_cpp -- \
  --config blueprints/health-monitor/config.json &&
bazel run //blueprints/health-monitor:main_cpp -- \
  --config blueprints/health-monitor/config.json --simulate
```

C++ previews require the linked SDK but do not create a Node. The model-only test needs
no SDK; serialization and CLI tests use the real generated headers, with no device access.
The default CLI prints execute=false. Simulation emits synthetic receiving/stale states;
it is not robot data or a physical simulation.

## Configuration and behavior

Both languages use the same config.json and freshness/advisory rules. The C++ configuration
reader supports a flat object containing exactly stale_after_seconds in (0, 120] and
low_battery_percent in [0, 100], using these literal keys and finite JSON numbers (maximum
4096 bytes). It rejects extra/duplicate keys and trailing data without adding a JSON dependency.
From a deployed application's working directory, omitted --config reads config.json;
repository commands above select the file explicitly.

--duration is in (0, 120] seconds, default 10. --simulate and --execute are mutually exclusive.
JSON Lines contain source, all_streams_receiving, low_battery and each stream's status,
age_seconds, sample/error counters and decoded data. The final record adds final=true.
waiting_data is not an unsupported-interface verdict. Freshness uses the local monotonic
time recorded in the receive callback, not dequeue time, cross-stream clock comparison or capture latency.
Delayed processing cannot refresh a queued sample. Source timestamps
order only their own stream; zero disables ordering, and a producer timestamp reset
requires restarting the monitor. Low battery is advisory, not a control action or a safety verdict.

model.h contains SDK-independent state logic. decoder.h verifies FlatBuffers before access.
main.cc copies borrowed callback bytes into one 64-message queue (1 MiB per sample limit),
then merges and reports on the consumer thread. Queue overflow or SDK-reported drops stop
the application. RAII releases subscribers before the Node, including partial setup failure
and Ctrl+C. Exit 0 means all streams were fresh at the end; 1 means missing/stale input or
runtime/configuration failure; 2 means invalid CLI arguments; interruption exits 130.

## Build and package ARM64 — development container

Reuse the verified ARM64 SDK and common Schema prepared in the C++ SDK guide. Replace
these paths if your extracted directories differ. The AMD64 container cross-compiles;
do not run the ARM64 program or ARM64 tests there.

```bash
export AORTA_CPP_SDK_DIR="$PWD/artifacts/edu-sdk-2026.10.14/cpp-sdk-aarch64" &&
export AORTA_EDU_SCHEMA_DIR="$PWD/artifacts/edu-sdk-2026.10.14/edu-schema" &&
bazel build --config=arm64 //blueprints/health-monitor:main_cpp &&
PACKAGE_DIR=$(mktemp -d /tmp/vbot-health-cpp-XXXXXX) &&
test -n "$PACKAGE_DIR" &&
mkdir -p "$PACKAGE_DIR/bin" "$PACKAGE_DIR/lib" "$PACKAGE_DIR/licenses/aorta" &&
cp -L bazel-bin/blueprints/health-monitor/main_cpp "$PACKAGE_DIR/bin/health-monitor" &&
cp -L "$AORTA_CPP_SDK_DIR/lib/libaorta_core.so.13" "$PACKAGE_DIR/lib/" &&
cp blueprints/health-monitor/config.json "$PACKAGE_DIR/config.json" &&
cp LICENSE NOTICE "$PACKAGE_DIR/licenses/" &&
cp "$AORTA_CPP_SDK_DIR/LICENSE" "$AORTA_CPP_SDK_DIR/NOTICE" \
  "$AORTA_CPP_SDK_DIR/FLATBUFFERS-LICENSE" \
  "$AORTA_CPP_SDK_DIR/THIRD_PARTY_COMPONENTS.md" \
  "$AORTA_CPP_SDK_DIR/THIRD_PARTY_NOTICES.md" "$PACKAGE_DIR/licenses/aorta/" &&
file "$PACKAGE_DIR/bin/health-monitor" "$PACKAGE_DIR/lib/libaorta_core.so.13" &&
aarch64-linux-gnu-readelf -d "$PACKAGE_DIR/bin/health-monitor" &&
(cd "$PACKAGE_DIR" && find bin lib licenses config.json -type f -exec sha256sum {} + > SHA256SUMS)
```

Both ELF files must report AArch64. Keep PACKAGE_DIR for transfer. The package includes
the executable, shared runtime, shared configuration and license notices. Inspect recursive
dependencies as described in the C++ SDK guide. Use the robot's compatible system libraries;
do not copy host glibc or replace robot libraries. Editing packaged config.json invalidates
its checksum: update configuration before packaging or explicitly repackage your own application.

## Transfer — machine with SSH access

Reuse verified [public-key SSH](../../../docs/robots/quadruped-common/connection.md).
Replace ROBOT with the selected vbot address/alias (wired or Wi-Fi); if unreachable, stop
and connect the device or correct its address. This step requires only transfer access,
not a compiler. PACKAGE_DIR must refer to the complete package on this machine.

```bash
ROBOT=vbot@192.168.126.2 &&
ssh -o BatchMode=yes "$ROBOT" \
  'test "$(id -un)" = vbot && test "$(uname -m)" = aarch64 && id -un && uname -m' &&
APP_DIR=$(ssh -o BatchMode=yes "$ROBOT" \
  'mkdir -p /userdata/vbot/apps && mktemp -d /userdata/vbot/apps/health-monitor-cpp-XXXXXX') &&
test -n "$APP_DIR" &&
printf 'Device application directory: %s\n' "$APP_DIR" &&
scp -r "$PACKAGE_DIR/." "$ROBOT:$APP_DIR/" &&
ssh "$ROBOT"
```

Record APP_DIR; the next block runs after login, not in the development container.
The device needs no repository, Bazel, SDK headers, Python or internet dependency download.

## Run — device vbot shell

Replace APP_DIR with the printed directory. A checksum or dynamic-library failure must stop
the command chain; fix the package, not permissions or system libraries.

```bash
APP_DIR=/userdata/vbot/apps/health-monitor-cpp-REPLACE_FROM_OUTPUT &&
cd "$APP_DIR" &&
sha256sum -c SHA256SUMS &&
export PATH="/opt/vita/aorta/bin:$PATH" &&
export ZENOH_SESSION_CONFIG_URI=/opt/vita/aorta/edu/edu_session.json5 &&
export LD_LIBRARY_PATH="$PWD/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}" &&
LDD_OUTPUT=$(ldd ./bin/health-monitor) &&
printf '%s\n' "$LDD_OUTPUT" &&
[[ "$LDD_OUTPUT" != *"not found"* ]] &&
./bin/health-monitor --config config.json --execute --duration 10
```

For a fresh login, re-enter the same directory and set the three runtime environment variables
before rerunning the binary. Allow the duration to expire or press Ctrl+C; nothing is added to
background services or autostart.
Use [layered diagnostics](../../../docs/development/diagnostics.md) to distinguish environment,
SDK and missing-data problems. To continue in your own project, use the
[C++ application generator](../../../templates/README.md) and follow the generated workspace's
README. It copies source/build helpers and the ARM64 toolchain without referencing this checkout;
SDK artifacts remain separate. Both paths deploy a binary, not a source checkout.
