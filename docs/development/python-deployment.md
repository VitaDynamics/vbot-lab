# Deploy a Python recipe to the robot

<p align="center">English | <a href="python-deployment.zh-CN.md">中文</a></p>

The robot does not come with a VBOT Lab checkout or an application venv. Build on the
workstation/development container, transfer a small source package and ARM64 wheels,
then create a venv on the robot. Device-side Git, Bazel, a compiler and internet access
are not required for this Python deployment **after the complete wheelhouse has been
prepared on a connected workstation**. This is not an end-to-end offline setup.
Do not copy a workstation venv or Bazel launcher/runfiles to the robot.

## 1. Prepare on the workstation or development container

Start at the local VBOT Lab repository root. The example below deploys the read-only
`subscribe-state` recipe. For another recipe, change RECIPE to its directory name;
the package includes only its main.py and shared Python modules, not every recipe or
the complete repository. Build through [offline Bazel](offline-build.md) when using
the packaged dependency bundle.

Download the matching Linux aarch64 SDK, aorta-msgs and vbot-edu-msgs wheels from
[GitHub Releases](https://github.com/VitaDynamics/vbot-lab/releases/tag/edu-sdk-2026.9.24)
into `artifacts/wheelhouse/`, following the [SDK guide](../../packages/aorta/python/README.md).
The release also attaches the `flatbuffers` 25.12.19 universal wheel; the first commands
below download the same wheel from PyPI on the workstation instead. They require network
access and do not install an ARM64 SDK into the workstation's Python environment.
Verify every file against the release `SHA256SUMS` (or the FlatBuffers file against its
trusted distribution checksum) before packaging. All four files below are required;
if a download or checksum check fails, stop. Do not fetch missing dependencies on the robot.

```bash
mkdir -p artifacts/wheelhouse
python3 -m pip download --only-binary=:all: --no-deps \
  --dest artifacts/wheelhouse "flatbuffers==25.12.19"
RECIPE=subscribe-state
bazel build "//recipes/$RECIPE:main"
bazel run "//recipes/$RECIPE:main" -- --help
mkdir -p artifacts
PACKAGE_DIR=$(mktemp -d "$PWD/artifacts/python-recipe-XXXXXX")
mkdir "$PACKAGE_DIR/wheelhouse"
tar -czf "$PACKAGE_DIR/python-recipe.tar.gz" \
  LICENSE NOTICE recipes/__init__.py recipes/common.py recipes/observe.py \
  "recipes/$RECIPE/main.py"
cp artifacts/wheelhouse/aorta_sdk-2026.9.23-py3-none-linux_aarch64.whl \
  artifacts/wheelhouse/aorta_msgs-2026.9.23-py3-none-any.whl \
  artifacts/wheelhouse/vbot_edu_msgs-2026.9.24-py3-none-any.whl \
  artifacts/wheelhouse/flatbuffers-25.12.19-py2.py3-none-any.whl \
  "$PACKAGE_DIR/wheelhouse/"
(cd "$PACKAGE_DIR" && sha256sum python-recipe.tar.gz wheelhouse/*.whl > SHA256SUMS)
```

The tar contains the `recipes/` package layout needed by `python -m` and applicable
LICENSE/NOTICE files. It contains neither a venv nor SDK/native binaries.

For audio/video binary saving, also include a device-compatible `numpy==2.2.6` wheel;
camera decoding additionally needs `av==16.1.0`. Match the device's Python ABI as well
as ARM64 (the current device pairing uses Python 3.10). Add these wheels to the staged
wheelhouse **before regenerating SHA256SUMS**. These optional dependencies are not
needed for the read-only state example.

## 2. Transfer from the machine with SSH access

Complete [public-key login](../robots/quadruped-common/connection.md) first. Replace
ROBOT with the confirmed device address or your ordinary vbot SSH alias. If SSH is
unreachable, connect the device or correct its address before proceeding.

Run in the same workstation/container shell as step 1. The identity check must report
vbot, aarch64 and a supported Python version. Each deployment gets a fresh directory;
do not overwrite another application. Stop immediately on any failed command.

```bash
ROBOT=vbot@192.168.126.2
ssh -o BatchMode=yes "$ROBOT" 'id -un; uname -m; python3 --version'
APP_DIR=$(ssh -o BatchMode=yes "$ROBOT" \
  'mkdir -p /userdata/vbot/apps && mktemp -d /userdata/vbot/apps/python-recipe-XXXXXX')
printf 'Device application directory: %s\n' "$APP_DIR"
scp "$PACKAGE_DIR/python-recipe.tar.gz" "$PACKAGE_DIR/SHA256SUMS" "$ROBOT:$APP_DIR/"
scp -r "$PACKAGE_DIR/wheelhouse" "$ROBOT:$APP_DIR/"
ssh "$ROBOT"
```

Record the printed APP_DIR. The next commands run in the **device shell** opened by
the final ssh command. Workstation shell variables do not carry over to that shell.
If only the host has SSH access, bring the staged PACKAGE_DIR to that host first.

## 3. Create the runtime on the device

Replace `python-recipe-ABC123` below with the actual directory printed in step 2.
This is the **application deployment directory**, not a preinstalled repository.
Verify checksums before extraction/installation and stop if any check fails.

```bash
cd /userdata/vbot/apps/python-recipe-ABC123
sha256sum -c SHA256SUMS
tar -xzf python-recipe.tar.gz
unset PYTHONPATH
export PYTHONNOUSERSITE=1
python3 -m venv .venv
.venv/bin/python -m pip install --no-index --find-links wheelhouse \
  aorta-sdk==2026.9.23 aorta-msgs==2026.9.23 \
  vbot-edu-msgs==2026.9.24 flatbuffers==25.12.19
.venv/bin/python -m pip check
.venv/bin/python -c 'import aorta; from locomotion.LocomotionStatus import LocomotionStatus; print("SDK imports OK")'
```

If Python/venv support or native runtime dependencies are missing, resolve them using
the supported device environment before continuing; do not install into system Python
or reuse an unrelated application's environment. Optional capture/decode dependencies
are installed from the prepared wheelhouse with the same --no-index option.

## 4. Run from that application directory

The directory now contains `recipes/`, `wheelhouse/` and `.venv/`. It does not need
.git, MODULE.bazel, SDK source or the rest of the repository. In this same device shell:

```bash
. .venv/bin/activate
unset PYTHONPATH
export PYTHONNOUSERSITE=1
export PATH="/opt/vita/aorta/bin:$PATH"
export ZENOH_SESSION_CONFIG_URI=/opt/vita/aorta/edu/edu_session.json5
python -m recipes.subscribe-state.main
python -m recipes.subscribe-state.main --execute --count 3 --timeout 10
```

The first command previews without connecting. The second requests three state samples.
A timeout is not success. See the selected [recipe](../../recipes/README.md) for its
arguments, safety/consent requirements and completion checks. Change the module name
only to the recipe actually deployed.

After reconnecting, cd to the recorded application directory and repeat the shell
setup/activation block before running. Do not assume .bashrc has loaded this venv.
Use a dedicated native-SDK shell; ROS PYTHONPATH can shadow wheel packages.
For an updated application, build and deploy into a new directory and verify it before
switching any [autostart entry](../guides/user-autostart.md). This walkthrough does not
change startup scripts or start background processes.
