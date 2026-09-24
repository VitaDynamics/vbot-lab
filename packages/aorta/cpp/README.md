# Aorta C++ SDK

<p align="center">English | <a href="README.zh-CN.md">中文</a></p>

Use the [edu-sdk-2026.9.24 pre-release](https://github.com/VitaDynamics/vbot-lab/releases/tag/edu-sdk-2026.9.24):
C++ SDK `2026.9.23`, ABI `12`, with EDU Schema pack `2026.9.24-v4`.
The examples use C++17, Bazel 7.6.1 and the release's generated headers.
They do not require Python wheels or local Schema generation.

## Prepare release artifacts

Supported C++ artifacts target **Ubuntu 22.04 Linux x86_64 or aarch64**.
Use the artifact matching the compiler target and runtime architecture, with compatible
glibc/libstdc++. These instructions use native compilation: choosing an aarch64 archive
does not configure cross-compilation. Build ARM64 programs on a prepared ARM64 builder; never deploy an x86_64 binary to an ARM64 robot.
Check [compatibility](../../../release/compatibility.md).

Download the matching SDK archive, the EDU Schema archive and `SHA256SUMS` into
`artifacts/edu-sdk-2026.9.24/`. From the checkout root on Linux x86_64:

```bash
cd artifacts/edu-sdk-2026.9.24
sha256sum --ignore-missing -c SHA256SUMS
mkdir cpp-sdk-x86_64 edu-schema
tar --zstd -xf aorta-cpp-sdk-2026.9.23-abi12-ubuntu22.04-x86_64.tar.zst -C cpp-sdk-x86_64
tar --zstd -xf aorta-edu-schema-pack-2026.9.24-v4.tar.zst -C edu-schema
cd ../..
export AORTA_CPP_SDK_DIR="$PWD/artifacts/edu-sdk-2026.9.24/cpp-sdk-x86_64"
export AORTA_EDU_SCHEMA_DIR="$PWD/artifacts/edu-sdk-2026.9.24/edu-schema"
```

Both selected archive checksums must pass; the checksum command skips absent assets.
Use fresh extraction directories; if they already exist, inspect/reuse the verified
contents rather than blindly extracting over them. For ARM64 substitute `aarch64`
for `x86_64` in the archive and directory names. Ensure `g++`, `zstd` and Bazel
are available. Do not copy generated headers or binary libraries into Git.

The local Bazel repository reads these two absolute paths; it does not download
SDKs or configure a compiler. You can also supply the paths using Bazel
`--repo_env=AORTA_CPP_SDK_DIR=...` and `--repo_env=AORTA_EDU_SCHEMA_DIR=...`.
Keep the bundled FlatBuffers headers: C++ generated code checks its exact
FlatBuffers version (`25.9.23` for this pairing); the Python package version is
not a replacement for these C++ headers.

## Build and preview

For a self-contained build environment, use the [offline build entry](../../../docs/development/offline-build.md)
with the packaged Bazel dependencies; SDK archives alone do not contain Bazel's build rules.

Each Recipe preserves Python `:main` and adds C++ `:main_cpp`:

```bash
bazel build \
  //recipes/device-info:main_cpp \
  //recipes/subscribe-state:main_cpp \
  //recipes/service-call:main_cpp \
  //recipes/camera:main_cpp \
  //recipes/audio:main_cpp \
  //recipes/locomotion:main_cpp \
  //recipes/rcp-task:main_cpp
bazel run //recipes/camera:main_cpp
bazel run //recipes/locomotion:main_cpp -- --mode stand
bazel run //recipes/rcp-task:main_cpp
bazel test //tests:recipe_cpp_test //tests:recipe_cpp_sdk_test
```

C++ targets are tagged `manual`: name them explicitly. Ordinary `//recipes/...`
builds and `//tests/...` tests remain usable without SDK archives; they do not
silently fetch C++ dependencies. Unlike Python previews, **C++ previews still require
building/linking the release SDK**, but do not create a Node or contact a robot.
Tests cover CLI guards and real generated-type serialization without device sessions.

The shared helpers handle arguments, bounded queues and files; they do not replace
Aorta APIs. The actual examples use `Node::Create`, `CreateSubscriber`,
`CreateClientTyped`, and `CreateActionClient`. Check each `StatusOr` before
accessing its value. Typed service clients inject the header and matching schema
metadata from `*_msg.h`. Message callbacks receive borrowed views: copy with
`MessageView::ToVector()` before deferring work. Validate FlatBuffers before
using accessors and keep the owning buffer/response alive.

RCP uses `ExecuteTaskAction` and generated `*Msg`/variant types in
`execute_task_msg.h`, not the Python `*T` object API. These generated C++
DAG helper types are in `aorta::action::rcp`; wire enums remain in
`aorta::services::rcp`. See [goal construction](../../../recipes/rcp-task/goal.h).

## Optional camera decoding

If FFmpeg is supplied as a separate directory rather than installed system-wide,
set `VBOT_FFMPEG_DIR` to its absolute path before building. The supported bundle
layout is FFmpeg 4.4 headers in `include/` and shared libraries `libavcodec.so.58`,
`libavutil.so.56`, `libswscale.so.5` in `lib/`, with their symlink targets present.
Bazel imports those files explicitly. Include that `lib/` directory in the
device's `LD_LIBRARY_PATH` when deploying. See the [offline guide](../../../docs/development/offline-build.md).
Leave the variable unset to use installed system development libraries.

The basic camera target reads H.265 metadata and optionally records compressed bytes.
To decode RGB in C++, use the separate `:main_cpp_decode` target. Its build
environment needs the development headers/libraries for `libavcodec`,
`libavutil` and `libswscale` (Ubuntu packages `libavcodec-dev`,
`libavutil-dev`, `libswscale-dev`). They are system dependencies, not installed
by Bazel. Provide them in the development image; the runtime also needs matching
FFmpeg shared libraries and a software HEVC decoder.

```bash
pkg-config --modversion libavcodec libavutil libswscale
bazel build //recipes/camera:main_cpp_decode
bazel run //recipes/camera:main_cpp_decode -- --decode --consent
```

The command above is a build-machine preview. Deploy the executable and FFmpeg
runtime as described below, then use the camera recipe's direct binary command. The decoder waits for decodable keyframe
data, drains delayed frames on completion and reports RGB dimensions/row stride.
Application-owned RGB bytes are available in `decoder.h`; the example does not
save image files. Each decoded RGB image is limited to 32 MiB.

## Run on the robot

Build on a prepared **ARM64 build machine or ARM64 development container**, then
transfer the executable and its shared libraries. The robot only runs the deployed
program: it does not need Bazel, a compiler, SDK headers, or a repository checkout.
An x86_64 build is for host-side previews, not ARM64 deployment; selecting ARM64
SDK artifacts alone does not configure a cross-compiler.

### 1. Build and package on the build machine

Prepare the matching artifacts as above. From the checkout root on the ARM64
builder, package the read-only state subscription example below. Change RECIPE
to another recipe directory name to package that example instead.
Run each step in order and stop on any error.

```bash
# Build machine: repository root, matching ARM64 SDK/Schema already configured.
RECIPE=subscribe-state
bazel build "//recipes/$RECIPE:main_cpp"
PACKAGE_DIR=$(mktemp -d /tmp/vbot-cpp-app-XXXXXX)
mkdir -p "$PACKAGE_DIR/bin" "$PACKAGE_DIR/lib" "$PACKAGE_DIR/licenses/aorta"
cp -L "bazel-bin/recipes/$RECIPE/main_cpp" "$PACKAGE_DIR/bin/$RECIPE"
cp -L "$AORTA_CPP_SDK_DIR/lib/libaorta_core.so.12" "$PACKAGE_DIR/lib/"
cp LICENSE NOTICE "$PACKAGE_DIR/licenses/"
cp "$AORTA_CPP_SDK_DIR/LICENSE" "$AORTA_CPP_SDK_DIR/NOTICE" \
   "$AORTA_CPP_SDK_DIR/FLATBUFFERS-LICENSE" \
   "$AORTA_CPP_SDK_DIR/THIRD_PARTY_COMPONENTS.md" \
   "$AORTA_CPP_SDK_DIR/THIRD_PARTY_NOTICES.md" "$PACKAGE_DIR/licenses/aorta/"
file "$PACKAGE_DIR/bin/$RECIPE" "$PACKAGE_DIR/lib/libaorta_core.so.12"
LD_LIBRARY_PATH="$PACKAGE_DIR/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}" \
  ldd "$PACKAGE_DIR/bin/$RECIPE"
(cd "$PACKAGE_DIR" && find bin lib licenses -type f -exec sha256sum {} + > SHA256SUMS)
```

Check that both files report AArch64 and that no library is reported as
`not found`. The C++ wrapper is statically linked; Aorta core is shared, so
the executable alone is insufficient. Keep the licenses and notices with the
package. The robot must provide compatible glibc/libstdc++; do not copy the
builder's glibc or overwrite device system libraries.

For camera decoding, build `//recipes/camera:main_cpp_decode`, copy
`bazel-bin/recipes/camera/main_cpp_decode` as `bin/camera-decode`, and include
matching ARM64 FFmpeg runtime libraries in `lib/`. For the supported bundle
these include `libavcodec.so.58`, `libavutil.so.56`, and `libswscale.so.5`;
copy the actual contents under those names (for example with `cp -L`).
Inspect their transitive dependencies too: the three libraries are not a
guarantee of a complete runtime for every FFmpeg build. Include applicable
FFmpeg/third-party license notices and regenerate SHA256SUMS after adding files.

### 2. Transfer through SSH

First establish [public-key SSH access](../../../docs/robots/quadruped-common/connection.md).
Replace ROBOT with your confirmed device address or configured SSH alias; if
unreachable, connect the device or obtain its address before continuing.
The identity check must return `vbot` and `aarch64`. Create a new application
directory for this deployment instead of overwriting an existing application.

```bash
# Build/transfer machine: keep PACKAGE_DIR from the previous step.
ROBOT=vbot@192.168.126.2
ssh -o BatchMode=yes "$ROBOT" 'id -un; uname -m'
APP_DIR=$(ssh -o BatchMode=yes "$ROBOT" \
  'mkdir -p /userdata/vbot/apps && mktemp -d /userdata/vbot/apps/cpp-recipe-XXXXXX')
printf 'Device application directory: %s\n' "$APP_DIR"
scp -r "$PACKAGE_DIR/bin" "$PACKAGE_DIR/lib" "$PACKAGE_DIR/licenses" \
  "$PACKAGE_DIR/SHA256SUMS" "$ROBOT:$APP_DIR/"
ssh "$ROBOT"
```

Record the printed APP_DIR. Local shell variables do not carry over into the SSH
session; use that actual path in the next block. Stop if directory creation or
transfer fails.

### 3. Run directly in the device shell

After SSH login, [configure the device shell](../../../docs/getting-started/device-environment.md).
In the uploaded application directory, verify checksums and dynamic libraries
before running. Do not continue if a checksum fails, a library is `not found`,
or a GLIBC/GLIBCXX version is missing; fix the ARM64 package/build compatibility
and transfer again, without replacing system libraries.

```bash
# Device shell: replace this value with the APP_DIR printed during transfer.
APP_DIR=/userdata/vbot/apps/cpp-recipe-XXXXXX
cd "$APP_DIR"
sha256sum -c SHA256SUMS
export PATH="/opt/vita/aorta/bin:$PATH"
export ZENOH_SESSION_CONFIG_URI=/opt/vita/aorta/edu/edu_session.json5
export LD_LIBRARY_PATH="$PWD/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
ldd ./bin/subscribe-state
./bin/subscribe-state
./bin/subscribe-state --execute --count 3 --timeout 10
```

The first invocation prints an offline preview; the second receives three state
messages and exits. For other recipes, substitute their deployed `./bin/<recipe>`
name and documented arguments. For the decoder use `./bin/camera-decode` with
the [camera recipe's arguments](../../../recipes/camera/README.md).
Run from the application directory and set LD_LIBRARY_PATH in each new shell.
Live examples require the device `vbot` account and the documented session URI;
check route availability and each recipe's consent/safety prerequisites before
adding `--execute`. A successful build or preview is not proof of a live interface.

## Operation boundaries

All programs default to a JSON preview. Live reads require `--execute`; voice
access requires `--consent`, motion requires `--confirm-motion`, and image
capture/decoding requires `--consent`. Logs are JSON Lines; errors go to stderr.
Exit codes: 0 completed/preview, 1 runtime error/timeout, 2 invalid arguments,
130 interruption. A SIGINT/SIGTERM requests graceful exit; a blocking RPC may
return only when its configured timeout expires. SIGKILL cannot run cleanup.

RAII closes subscriptions/clients before the Node. Motion admission is not
completion: match the BODY terminal report's request ID. A timeout does not
cancel a robot action. RCP demonstrates only a two-node Sleep DAG, with bounded
result waits and best-effort cancellation on interruption or failure after
admission. A failed cancellation still requires a terminal-result check.
An admission timeout without a handle leaves the outcome unknown: inspect the
logged goal/task IDs, never resubmit automatically. No goal secret is logged.
For field semantics and task-specific commands, see [Recipes](../../../recipes/README.md).
