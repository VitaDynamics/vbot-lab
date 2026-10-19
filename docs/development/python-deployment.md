# Deploy a Python recipe to the robot

<p align="center">English | <a href="python-deployment.zh-CN.md">中文</a></p>

The robot does not come with a VBOT Lab checkout or an application venv. Build on the
development container, transfer a small source package and ARM64 wheels,
then create a venv on the robot. Device-side Git, Bazel, a compiler and internet access
are not required for this Python deployment **after the complete wheelhouse has been
prepared inside a connected development container**. This is not an end-to-end offline setup.
Do not copy a workstation venv or Bazel launcher/runfiles to the robot.

Run each Bash block as one command chain: `&&` prevents later commands in that block
from running after a failure, without exiting your interactive shell. Fix the error
before continuing to another block.

## 1. Prepare in the development container

Run SDK preparation, the Bazel commands and packaging below **inside the matching development
container**, not in the host shell or directly on a CI runner. See [execution locations](README.md).
Step 2 only transfers the prepared package and may use the host; step 3 runs on the robot.

Start at the mounted VBOT Lab repository root inside the development container. The example below deploys the read-only
`subscribe-state` recipe. For another recipe, set RECIPE to its directory name and
PREVIEW_ARGS to that Recipe's offline-preview arguments;
the package includes only its main.py and shared Python modules, not every recipe or
the complete repository. Build through [offline Bazel](offline-build.md) when using
the packaged dependency bundle.

The fetch helper stages the matching Linux aarch64 SDK, aorta-msgs, vbot-edu-msgs and
FlatBuffers wheels plus release/license metadata from
[GitHub Releases](https://github.com/VitaDynamics/vbot-lab/releases/tag/edu-sdk-2026.10.14).
It checks their pinned hashes and reuses already-verified files. For a disconnected container,
bring those same assets into the asset directory first; skip downloading, not verification.
Downloading assets requires network access but no PyPI download for this base profile.
Staging files does not install the ARM64 SDK into the container's Python environment.
If an asset is missing or invalid, stop; do not download dependencies on the robot.

```bash
RECIPE=subscribe-state &&
PREVIEW_ARGS=() &&
python3 tools/fetch_sdk.py --output artifacts/edu-sdk-2026.10.14 &&
bazel build "//recipes/$RECIPE:main" &&
bazel run "//recipes/$RECIPE:main" -- "${PREVIEW_ARGS[@]}" &&
PACKAGE_DIR="artifacts/python-$RECIPE" &&
python3 tools/package_python.py --recipe "$RECIPE" \
  --assets-dir artifacts/edu-sdk-2026.10.14 --output "$PACKAGE_DIR" &&
python3 tools/package_python.py --verify "$PACKAGE_DIR"
```

The empty Bash array is correct for `subscribe-state`. For the motion Recipe, replace
the first two assignments in the block with `RECIPE=locomotion` and
`PREVIEW_ARGS=(--mode stand)`; `--mode` is required even for its offline preview.
The quoted array passes each argument separately through Bazel's `--` separator.
Choose other arguments from the selected [Recipe](../../recipes/README.md).
Do not put `--execute` in PREVIEW_ARGS: this stage only previews and packages,
and does not connect to the robot or perform the selected action.

The container-side packager replaces manual tar/wheel copying. It verifies the selected
Recipe, all four base wheels, their release hashes, metadata/dependency closure and bundled
licenses. It emits `PACKAGE_MANIFEST.json`, `requirements.txt`, `SHA256SUMS` and the deployable
source archive containing `recipes/common.py`, `recipes/observe.py` and the selected entry.
No SSH, SDK installation or implicit build occurs during packaging. Existing output is never
overwritten; choose a fresh output directory or verify and reuse the existing one.
The default download profile stages only the four ARM64/base wheels and release/license
metadata. Use `fetch_sdk.py --profile all` only when the full SDK asset set is needed.


The tar contains the `recipes/` package layout needed by `python -m` and applicable
LICENSE/NOTICE files. It contains neither a venv nor SDK/native binaries.

The tool's `base` profile covers SDK-only operations such as state, message metadata and ASR.
Audio/video payload saving additionally needs `numpy==2.2.6`; camera decoding also needs
`av==16.1.0`. These are not included in this package or SDK Release. An application using
those options needs its own dependency package matched to ARM64 and the device's Python ABI
(Python 3.10 for this pairing), with separate integrity and license checks.
Do not append files to this verified base package or rewrite its checksums to bypass verification.
The read-only state example needs neither optional dependency.

## 2. Transfer from the machine with SSH access

Complete [public-key login](../robots/quadruped-common/connection.md) first. Replace
ROBOT with the confirmed device address or your ordinary vbot SSH alias. If SSH is
unreachable, connect the device or correct its address before proceeding.

Run in the step 1 container shell if it has SSH access; otherwise transfer the prepared
PACKAGE_DIR to the authorized host and set that variable there before continuing. The identity check must report
vbot, aarch64 and a supported Python version. Each deployment gets a fresh directory;
do not overwrite another application. Stop immediately on any failed command.

```bash
ROBOT=vbot@192.168.126.2 &&
ssh -o BatchMode=yes "$ROBOT" \
  'test "$(id -un)" = vbot && test "$(uname -m)" = aarch64 &&
   python3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" &&
   id -un && uname -m && python3 --version' &&
APP_DIR=$(ssh -o BatchMode=yes "$ROBOT" \
  'mkdir -p /userdata/vbot/apps && mktemp -d /userdata/vbot/apps/python-recipe-XXXXXX') &&
test -n "$APP_DIR" &&
printf 'Device application directory: %s\n' "$APP_DIR" &&
scp -r "$PACKAGE_DIR/." "$ROBOT:$APP_DIR/" &&
ssh "$ROBOT"
```

The first SSH command checks the account, architecture and Python 3.10+ before any
directory creation or transfer. On failure, resolve the mismatch instead of bypassing it.
Record the printed APP_DIR. The next commands run in the **device shell** opened by
the final ssh command. Workstation shell variables do not carry over to that shell.
If only the host has SSH access, bring the staged PACKAGE_DIR to that host first.

## 3. Create the runtime on the device

Replace `python-recipe-ABC123` below with the actual directory printed in step 2.
This is the **application deployment directory**, not a preinstalled repository.
Verify checksums before extraction/installation and stop if any check fails.

```bash
cd /userdata/vbot/apps/python-recipe-ABC123 &&
sha256sum -c SHA256SUMS &&
tar -xzf python-recipe.tar.gz &&
unset PYTHONPATH &&
unset AORTA_CORE_FFI_LIB &&
export PYTHONNOUSERSITE=1 &&
python3 -m venv .venv &&
.venv/bin/python -m pip install --no-index --find-links wheelhouse -r requirements.txt &&
.venv/bin/python -m pip check &&
.venv/bin/python -c 'import aorta; from locomotion.LocomotionStatus import LocomotionStatus; core = aorta.load_library(); print("SDK imports and native runtime OK; ABI", core.aorta_abi_version())'
```

If Python/venv support or native runtime dependencies are missing, resolve them using
the supported device environment before continuing; do not install into system Python
or reuse an unrelated application's environment. This installation is for the base profile;
it does not enable the optional capture/decode features described above.

## 4. Run from that application directory

The directory now contains `recipes/`, `wheelhouse/` and `.venv/`. It does not need
.git, MODULE.bazel, SDK source or the rest of the repository. In this same device shell:

```bash
. .venv/bin/activate &&
unset PYTHONPATH &&
unset AORTA_CORE_FFI_LIB &&
export PYTHONNOUSERSITE=1 &&
export PATH="/opt/vita/aorta/bin:$PATH" &&
export ZENOH_SESSION_CONFIG_URI=/opt/vita/aorta/edu/edu_session.json5 &&
python -m recipes.subscribe-state.main --execute --count 3 --timeout 10
```

Complete the offline preview in the development container before deployment. The device
command requests three state samples.
A timeout is not success. See the selected [recipe](../../recipes/README.md) for its
arguments, safety/consent requirements and completion checks. For another Recipe, replace
both the module name and the device-run arguments with its documented command, not just
the preview arguments. In particular, `--count` belongs to stream-reading examples;
motion also requires its safety confirmation before live execution.

After reconnecting, cd to the recorded application directory and repeat the shell
setup/activation block before running. Do not assume .bashrc has loaded this venv.
Use a dedicated native-SDK shell; ROS PYTHONPATH can shadow wheel packages.
For an updated application, build and deploy into a new directory and verify it before
switching any [autostart entry](../guides/user-autostart.md). This walkthrough does not
change startup scripts or start background processes.
