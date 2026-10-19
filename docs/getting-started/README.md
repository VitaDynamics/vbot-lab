# Quickstart: receive your first robot state

<p align="center">English | <a href="README.zh-CN.md">中文</a></p>

The default path is **Python + foot_quadruped EDU + a read-only state subscription**.
It targets robot application `V1.6.0-12`, source tag `V1.6.0.12` and SDK Release
`edu-sdk-2026.10.14`.
The goal is three decoded `/locomotion/status` samples followed by
normal program exit. No motion, audio/video capture or autostart is involved.

| Step | Execution location | Successful result | If it fails |
| --- | --- | --- | --- |
| Select source and reuse a development container | Host, then container | Matching checkout, Python 3.10+, Bazel 7.6.1 | [Container setup](../../docker/README.md) |
| Build, preview and package | Development container | Offline preview and a verified ARM64 package | [Build/import/package issues](../troubleshooting/README.md) |
| Confirm SSH and transfer | Host with access to the selected robot | `vbot`, `aarch64`, fresh application directory | [SSH troubleshooting](../troubleshooting/README.md#ssh) |
| Install and receive state | Robot's vbot shell | Three JSON Lines, exit code 0 | [Subscription timeout](../troubleshooting/README.md#no-data) |

## 1. Select the matching source — host

Check the [robot-type guide](../robots/README.md) and [compatibility matrix](../compatibility.md).
Four-wheeled and bipedal EDU software are not part of this release. Clone normally, then
select the documented source tag:

```bash
git clone https://github.com/VitaDynamics/vbot-lab.git &&
cd vbot-lab &&
git checkout V1.6.0.12
```

For an existing checkout, run `git fetch origin tag V1.6.0.12` if the tag is absent.
Preserve local changes before switching. A tag checkout uses detached HEAD mode,
which is normal for a version snapshot. See the [release configuration](../../catalog/release.md)
for the source and component pairing.
If you want to edit this checkout, create a working branch first:

```bash
git switch -c my-edu-app
```

Repository-only checks can run on the host or CI runner. Bazel builds/tests, Recipe previews,
SDK checks and packaging run inside the development container, including CI; see
[execution locations](../development/README.md). Repository contribution checks are not a
prerequisite for this first application.

Run each Bash block as one command chain. `&&` skips its remaining commands after a
failure without changing the shell's error-handling settings. Fix the error before
continuing to the next block.

## 2. Build and package — development container

Follow the [container guide](../../docker/README.md) to reuse a suitable running container,
or start an existing stopped one. Create one only if none is suitable. If already in a
confirmed development container, use it directly; Docker is not required inside it.
Confirm the checkout mount and tool versions. With the default mount:

```bash
cd /workspace &&
python3 tools/check_environment.py --profile container &&
python3 tools/container_context.py &&
python3 --version &&
bazel --version &&
uname -m
```

Use Python 3.10+ and Bazel 7.6.1. The published image runs on `linux/amd64`, includes
ARM64 GCC/G++ cross-compilers, and can stage ARM64 Python source/wheels.
The first Python path below does not need cross-compilation. For C++ Recipe build scope,
see the [C++ SDK guide](../../packages/aorta/cpp/README.md).
The matching image digest is recorded in the compatibility matrix and Compose configuration.

From the container checkout root, download the pinned Release assets, build and preview the
read-only Recipe, then package it. Existing matching downloads are reused. The package
output must be new; if it already exists, inspect/reuse it or choose another output path.

```bash
python3 tools/fetch_sdk.py --output artifacts/edu-sdk-2026.10.14 &&
python3 tools/in_container.py -- bazel build //recipes/subscribe-state:main &&
python3 tools/in_container.py -- bazel run //recipes/subscribe-state:main &&
python3 tools/package_python.py --recipe subscribe-state \
  --assets-dir artifacts/edu-sdk-2026.10.14 --output artifacts/first-state &&
python3 tools/package_python.py --verify artifacts/first-state
```

Expected: the preview prints `execute=false`; packaging and verification report `status=complete`
and `device_contacted=false`. Preview is not a robot sample. The package includes only the
selected source, four ARM64/base wheels, requirements, licenses and checksums. No workstation
venv or host-built native library is copied to the robot. A workstation SDK installation is not needed
for this SDK-free preview; the runtime SDK is installed on the robot below.

If dependencies cannot be downloaded, use the [offline build guide](../development/offline-build.md)
with a previously prepared bundle. Do not change dependency registries or fetch missing packages
on the robot to work around a failed build/package.

## 3. Log in and transfer — host

First complete [public-key SSH login](../robots/quadruped-common/connection.md), or reuse your
working configuration. Wired access normally uses `192.168.126.2`; for Wi-Fi, connect through
the mobile app, find the robot IP in the router, and replace ROBOT below. An existing vbot SSH
alias also works. Do not continue after connection, authentication or host-key errors.

Run at the host checkout root, where `artifacts/first-state` is visible through the workspace
mount. If the container is elsewhere, transfer the already-generated package to this host first.

```bash
PACKAGE_DIR=artifacts/first-state &&
ROBOT=vbot@192.168.126.2 &&
ssh -o BatchMode=yes "$ROBOT" \
  'test "$(id -un)" = vbot && test "$(uname -m)" = aarch64 &&
   python3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" &&
   id -un && uname -m && python3 --version' &&
APP_DIR=$(ssh -o BatchMode=yes "$ROBOT" \
  'mkdir -p /userdata/vbot/apps && mktemp -d /userdata/vbot/apps/first-state-XXXXXX') &&
test -n "$APP_DIR" &&
printf 'Device application directory: %s\n' "$APP_DIR" &&
scp -r "$PACKAGE_DIR/." "$ROBOT:$APP_DIR/" &&
ssh "$ROBOT"
```

The first SSH command requires `vbot`, `aarch64` and Python 3.10+ before creating a directory
or transferring files. If it fails, check the selected account, architecture and Python version;
do not bypass the check. Record the printed APP_DIR.
The next block runs **after SSH login**, not in the host/container. Local variables do not
carry into that shell. The robot needs neither a checkout, Git nor Bazel.

## 4. Install and receive state — robot

Replace the directory below with the APP_DIR printed above. Keep the robot's existing
services and permissions unchanged. Use a dedicated native-SDK shell, without ROS package
paths shadowing the installed wheels:

```bash
cd /userdata/vbot/apps/first-state-REPLACE_FROM_OUTPUT &&
sha256sum -c SHA256SUMS &&
tar -xzf python-recipe.tar.gz &&
unset PYTHONPATH &&
unset AORTA_CORE_FFI_LIB &&
export PYTHONNOUSERSITE=1 &&
python3 -m venv .venv &&
.venv/bin/python -m pip install --no-index --find-links wheelhouse -r requirements.txt &&
.venv/bin/python -m pip check &&
.venv/bin/python -c 'import aorta; from locomotion.LocomotionStatus import LocomotionStatus; core = aorta.load_library(); print("SDK imports and native runtime OK; ABI", core.aorta_abi_version())' &&
export PATH="/opt/vita/aorta/bin:$PATH" &&
export ZENOH_SESSION_CONFIG_URI=/opt/vita/aorta/edu/edu_session.json5 &&
.venv/bin/python -m recipes.subscribe-state.main --execute --count 3 --timeout 10
```

Stop at any failed checksum, installation, import or environment check. Expected: all
checksums pass, `pip check` reports no broken requirements, imports and native-library ABI
checks succeed, then three
JSON Lines contain `heartbeat_seq`, `posture`, `motion`, `current_action` and `stamp_ns`.
Values depend on the robot; the process exits with code 0 after the third sample.
This is read-only telemetry, not motion completion. A timeout, topic listing or preview
is not success; use the [symptom-based troubleshooting](../troubleshooting/README.md).

To run again after reconnecting, enter the recorded application directory, clear PYTHONPATH and AORTA_CORE_FFI_LIB,
set the same Aorta variables and use `.venv/bin/python` with the final command. Persistent
shell setup is optional here; see [device environment](device-environment.md).

## Next steps

- Use [Python deployment](../development/python-deployment.md) for another Recipe, package contents and optional dependencies.
- Use the [Python SDK](../../packages/aorta/python/README.md) for application development and the [Recipe index](../../recipes/README.md) for other capabilities.
- For C++, use the [C++ SDK guide](../../packages/aorta/cpp/README.md). Select the ARM64 SDK and `bazel build --config=arm64` for device binaries; use the native SDK and default build for container previews/tests.
- Configure [autostart](../guides/user-autostart.md) only after interactive operation works.
- [Vbot Viewer](../guides/vbot-viewer.md) is optional for model exploration and never commands the robot. ROS 2 is an optional [device-local compatibility subset](../interfaces/aorta-ros2.md), not required for this Aorta example.
