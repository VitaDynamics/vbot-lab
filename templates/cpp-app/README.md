# C++ application workspace

<p align="center">English | <a href="README.zh-CN.md">中文</a></p>

A standalone C++17 / Bazel workspace starting from the read-only health monitor.
It subscribes only to /locomotion/status, /bms_state and /system/sm_status.
It does not publish controls, call services/actions or capture audio/video.
The supported target is foot_quadruped application V1.6.0-12, C++ SDK 2026.10.12 / ABI 13,
and Schema pack 2026.10.13-v4 from SDK Release edu-sdk-2026.10.14.

## Project contents

health_monitor/model.h owns SDK-independent business state; decoder.h validates and decodes
FlatBuffers; main.cc owns subscriptions, the bounded queue and JSON Lines output.
support/ contains copied shared helpers, sdk/ the local artifact rule, and toolchains/
the supplied ARM64 cross-build configuration. No source or Bazel label points back into
the VBOT Lab checkout. APP.json records the language, SDK pairing, build target and runtime
configuration inventory; it is project metadata, not a device API or a Python deployment manifest.

All build, test, preview, simulation and packaging commands run in the existing VBOT development
container. The image runs on AMD64 and provides ARM64 GCC/G++ 11. Only deployed binaries run
on the robot. No robot repository, Bazel, Python runtime or internet download is required.

## Build and test — development container

From this application's root, SDK-free state tests are available independently:

```bash
bazel test //:model_test
```

Prepare verified native and ARM64 SDK artifacts and the common Schema according to the
[C++ SDK guide](https://github.com/VitaDynamics/vbot-lab/blob/main/packages/aorta/cpp/README.md).
Replace SDK_ARTIFACTS below with their actual parent directory; it does not have to be in
the reference checkout. First use of Bazel may need network for public build-rule dependencies;
no SDK or compiler is downloaded by the application's repository rule.

```bash
SDK_ARTIFACTS=/workspace/sdk/edu-sdk-2026.10.14 &&
export AORTA_CPP_SDK_DIR="$SDK_ARTIFACTS/cpp-sdk-x86_64" &&
export AORTA_EDU_SCHEMA_DIR="$SDK_ARTIFACTS/edu-schema" &&
bazel build //:main &&
bazel test //:model_test //:sdk_test //:cli_test &&
bazel run //:main -- --config config.json &&
bazel run //:main -- --config config.json --simulate
```

Native CLI tests use Python in the development container to run the C++ executable, not
Python SDK wheels. Tests and previews never create a Node. Default output has execute=false;
simulation reports synthetic receiving/stale states.

## Configure the application

Edit config.json before packaging, or pass --config FILE when running. It accepts exactly
stale_after_seconds in (0, 120] and low_battery_percent in [0, 100], as finite JSON numbers.
The configuration file is limited to 4096 bytes. --duration is in (0, 120] seconds, default 10.
--simulate and --execute cannot be combined. With no --config, config.json is read from
the working directory. The application name does not rename its health_monitor source package.

Data freshness uses local monotonic time recorded in the callback and preserved through the queue,
not dequeue/decoding time; delayed processing cannot refresh an old sample. Source timestamps order messages only within
their own stream. Zero disables ordering; a timestamp reset requires restarting the monitor.
JSON Lines report waiting_data, receiving or stale, counters, decoded values and a low_battery
advisory. Missing input is not proof of an unsupported interface or a hardware fault.
Exit 0 means all three streams were fresh at the end; 1 means an input/configuration/runtime
problem, 2 invalid arguments, and 130 interruption. Subscribers close before the Node.

## Cross-build and package — development container

Keep SDK_ARTIFACTS and AORTA_EDU_SCHEMA_DIR from the previous block. Select the ARM64 SDK
before cross-building. Do not run or test ARM64 binaries in the AMD64 container.

```bash
export AORTA_CPP_SDK_DIR="$SDK_ARTIFACTS/cpp-sdk-aarch64" &&
bazel build --config=arm64 //:main &&
PACKAGE_DIR=$(mktemp -d /tmp/vbot-cpp-app-XXXXXX) &&
test -n "$PACKAGE_DIR" &&
mkdir -p "$PACKAGE_DIR/bin" "$PACKAGE_DIR/lib" "$PACKAGE_DIR/licenses/aorta" &&
cp -L bazel-bin/main "$PACKAGE_DIR/bin/health-monitor" &&
cp -L "$AORTA_CPP_SDK_DIR/lib/libaorta_core.so.13" "$PACKAGE_DIR/lib/" &&
cp config.json APP.json "$PACKAGE_DIR/" &&
cp LICENSE NOTICE "$PACKAGE_DIR/licenses/" &&
cp "$AORTA_CPP_SDK_DIR/LICENSE" "$AORTA_CPP_SDK_DIR/NOTICE" \
  "$AORTA_CPP_SDK_DIR/FLATBUFFERS-LICENSE" \
  "$AORTA_CPP_SDK_DIR/THIRD_PARTY_COMPONENTS.md" \
  "$AORTA_CPP_SDK_DIR/THIRD_PARTY_NOTICES.md" "$PACKAGE_DIR/licenses/aorta/" &&
file "$PACKAGE_DIR/bin/health-monitor" "$PACKAGE_DIR/lib/libaorta_core.so.13" &&
aarch64-linux-gnu-readelf -d "$PACKAGE_DIR/bin/health-monitor" &&
(cd "$PACKAGE_DIR" && find bin lib licenses config.json APP.json -type f -exec sha256sum {} + > SHA256SUMS) &&
printf 'Package directory: %s\n' "$PACKAGE_DIR"
```

Both ELF files must report AArch64. Inspect recursive dependencies as described in the SDK
guide and use compatible robot system libraries; never copy host glibc over robot libraries.
The package contains only the executable, Aorta shared runtime, configuration, metadata and
licenses. Additional libraries/assets require updating the build and explicit package inventory;
the commands do not automatically discover arbitrary application dependencies.
The Python-only package_app.py tool does not package C++ projects.
Keep the complete package and its printed path. Repackage after changing configuration;
checksums are not signatures. Returning to native tests requires restoring the native SDK path.

## Transfer — machine with SSH access

Reuse working public-key SSH. Replace ROBOT with the selected wired/Wi-Fi address or SSH alias.
If unreachable, stop and connect the device or correct its address.
PACKAGE_DIR must name the complete package on this machine.

```bash
ROBOT=vbot@192.168.126.2 &&
ssh -o BatchMode=yes "$ROBOT" \
  'test "$(id -un)" = vbot && test "$(uname -m)" = aarch64 && id -un && uname -m' &&
APP_DIR=$(ssh -o BatchMode=yes "$ROBOT" \
  'mkdir -p /userdata/vbot/apps && mktemp -d /userdata/vbot/apps/cpp-app-XXXXXX') &&
test -n "$APP_DIR" &&
printf 'Device application directory: %s\n' "$APP_DIR" &&
scp -r "$PACKAGE_DIR/." "$ROBOT:$APP_DIR/" &&
ssh "$ROBOT"
```

Record APP_DIR. The next commands run after logging into the device as vbot.

## Run — device vbot shell

Replace APP_DIR with the printed directory. A failed checksum or unresolved shared library
must stop the chain; correct the deployment package rather than device permissions.

```bash
APP_DIR=/userdata/vbot/apps/cpp-app-REPLACE_FROM_OUTPUT &&
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

A new login requires entering the same directory and setting the three runtime variables again;
no reinstall is needed. Stop with Ctrl+C or let the duration expire. No service, autostart, ACL
or resource setting is changed.

Use [VBOT Lab](https://github.com/VitaDynamics/vbot-lab) for connection, environment and
interface documentation. Use the [C++ diagnostic path](https://github.com/VitaDynamics/vbot-lab/blob/main/docs/development/diagnostics.md#cpp)
without installing Python wheels. Bring a reviewed, reproducible report to
[Vbot 超能社区](https://forum.vbot.cn/); never share credentials or session configuration.
