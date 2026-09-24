# Recipes

<p align="center">English | <a href="README.zh-CN.md">中文</a></p>

Single-task reference programs: a Recipe provides code, a [Skill](../skills/README.md) guides the workflow, and a [Blueprint](../blueprints/README.md) combines an application.

## Capability families

| Family | Recipes and scope | Interface |
| --- | --- | --- |
| Sensors | [sensors](sensors/README.md): battery, body/LiDAR IMU, point-cloud layout | pub/sub |
| Cameras | [camera](camera/README.md): H.265 metadata, saving and decoding | pub/sub |
| Perception | [perception](perception/README.md): object/person boxes and human keypoints | pub/sub |
| Audio | [audio](audio/README.md): body/UWB audio, ASR and input-end events | pub/sub |
| Motion | [locomotion](locomotion/README.md): stand/lie-down; [subscribe-state](subscribe-state/README.md): posture and heartbeat | service + pub/sub |
| System and peripherals | [system-peripherals](system-peripherals/README.md): system/display status; [device-info](device-info/README.md): firmware; [service-call](service-call/README.md): light status | service + pub/sub |
| RCP | [rcp-task](rcp-task/README.md): Sleep DAG submission, result and cancellation | action |
| SLAM | [slam](slam/README.md): state, odometry, static transforms | pub/sub |

Categories describe the implemented scope above, not one example for every public route.
SLAM observation does not change modes; use the [mapping workflow](../docs/guides/mapping-localization.md)
for explicit mapping, saving and localization. Existing helper entry points remain available.

These entries include Python/C++ source and Bazel targets. They target the current foot_quadruped EDU scope with the edu-sdk-2026.9.24 pre-release; install through [client libraries](../packages/README.md) and [Python SDK](../packages/aorta/python/README.md). SDK imports and a successful build do not establish live interface readiness; check routes and types on the selected firmware first.

## Python workflow

Build and preview first; then SSH into the robot, configure its shell and matching ARM64 venv, and meet the selected Recipe's preconditions. Nothing executes by default: --execute explicitly opens a device session. These checkout-root commands remain offline:

```bash
bazel build //recipes/...
bazel run //recipes/subscribe-state:main
bazel run //recipes/locomotion:main -- --mode stand
bazel run //recipes/rcp-task:main
bazel test //tests:recipe_test
```

Live reads also require --execute. Motion additionally requires --confirm-motion; voice access and image saving/decoding require --consent. Bazel's default Python toolchain selects python3 from PATH; activate the wheel-enabled venv before running. Follow [Python deployment](../docs/development/python-deployment.md) to transfer the selected source and wheelhouse and create the device venv. Then run python -m recipes.<directory>.main from that application directory; no device checkout or Bazel installation is required. Exact commands are in each page.

Logs use JSON Lines; errors go to stderr. A preview describes a request, not acquired data or an executed action. Subscriptions have count, time and queue limits; writes are not retried automatically.

## Tests and extension

Default tests cover offline previews, arguments, guards, resource cleanup, deadlines and correlation rules without installing the SDK or contacting a device. An explicit release-SDK test checks actual generated types and serialization:

```bash
bazel test --test_env=PATH="$PWD/.venv/bin:$PATH" //tests:recipe_sdk_test
```

The SDK guide defines the version pairing. When extending programs, start with [Schema](../schemas/README.md) for fields/types and the [capability catalog](../catalog/README.md) for behavior contracts; neither service admission nor action-cancel admission is terminal completion.

## C++ workflow

Every task also has a [C++ SDK](../packages/aorta/cpp/README.md) implementation in
`main.cc`, with target `:main_cpp`. Install architecture-matching SDK and Schema
artifacts and set the two directories from the guide, then explicitly build and preview:

```bash
bazel build //recipes/camera:main_cpp //recipes/audio:main_cpp //recipes/locomotion:main_cpp //recipes/rcp-task:main_cpp
bazel run //recipes/locomotion:main_cpp -- --mode stand
bazel test //tests:recipe_cpp_test //tests:recipe_cpp_sdk_test
```

All basic C++ targets are manual, so ordinary `//recipes/...` wildcard builds
do not implicitly require SDK artifacts. The base camera target reads/saves H.265;
the extra `:main_cpp_decode` target decodes RGB after installing FFmpeg development
dependencies. C++ previews require compilation and dynamic linkage, but do not
connect to devices. Live device use requires SSH login, shell setup, ARM64 executables
and matching runtime libraries.
