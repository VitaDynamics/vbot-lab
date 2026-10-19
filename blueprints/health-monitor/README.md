# Read-only health monitor

<p align="center">English | <a href="README.zh-CN.md">中文</a></p>

A complete Python / C++ application combining [locomotion state](../../docs/interfaces/locomotion.md),
[battery telemetry](../../docs/interfaces/sensors.md) and [system state](../../docs/interfaces/system-peripherals.md).
It reports data freshness and a configurable low-battery advisory, not physical safety or hardware health.
It never sends motion, service or RCP commands, and does not capture audio/video.
Use foot_quadruped application V1.6.0-12 and SDK Release edu-sdk-2026.10.14.

## Develop — container

The commands below use Python. For C++ SDK builds, tests, ARM64 packaging and device execution,
follow the [C++ implementation](cpp/README.md). Both languages share config.json and monitor the same streams.

```bash
bazel build //blueprints/health-monitor:main &&
bazel test //blueprints/health-monitor:model_test &&
bazel run //blueprints/health-monitor:main &&
bazel run //blueprints/health-monitor:main -- --simulate
```

No SDK is needed for previews, simulation or model tests. Synthetic tests cover no input,
stale streams, duplicate/out-of-order messages, malformed values, low battery and recovery.
These are application-state tests, not physical simulation or sensor accuracy measurements.

model.py takes decoded values and an injected monotonic receive time; runtime.py subscribes
to the three fixed read-only routes with a bounded queue; main.py merges streams and emits JSON Lines.
Missing input is waiting_data, not a claim of unsupported capability. A queue overflow stops
the application instead of silently accepting lost data; SDK-reported drops also stop it.
Freshness uses the monotonic time recorded in the receive callback, carried through the queue;
later dequeue/decoding does not refresh an old sample. Source timestamps only order messages
within one stream; a timestamp reset requires restarting this bounded monitor. Freshness
does not measure capture-to-reception latency. Zero source timestamps disable ordering for that stream.
Before Python decoding, wire.py checks bounds, tables, strings, vectors and inline structs against
the three pinned SDK BFBS schemas. Malformed samples increment invalid without refreshing the
last valid sample; legal zero/default fields remain allowed. Checks are bounded to 1 MiB per
sample, 64 nested levels and 65,536 objects. This is structural validation, not source authentication
or proof of hardware health. Previews and simulation still need no SDK or native verifier library.

config.json supports stale_after_seconds in (0, 120] and low_battery_percent in [0, 100].
`--config` selects a file, `--duration` bounds live execution to (0, 120] seconds (default 10).
Exit and cleanup behavior are documented in the [standalone workspace guide](../../templates/python-app/README.md).

Python failures write a sanitized JSON error to stderr with stage, error_code and next_step.
Configuration errors stop before SDK/device access; use the code to choose the relevant
check rather than treating every failure as a connection issue. See
[application errors](../../docs/troubleshooting/README.md#application-errors).

## Create your own Python application

In the development container, at the VBOT Lab root:

```bash
python3 tools/create_app.py --name my-monitor --output /tmp/my-monitor
```

The new workspace includes source, configuration, tests, Bazel files, an explicit APP.json
runtime inventory, pinned requirements, and licenses. Existing directories are never overwritten.
Use a new path or reuse an existing application yourself; creation does not install SDKs or deploy.
The generated project does not need the reference checkout to build its SDK-free logic or run
its deployed program. Packaging uses the reference checkout's tool and verified release assets.
For container builds in a generated directory, use an output path visible in the container/workstation mount.

Follow the [workspace guide](../../templates/python-app/README.md) to package and install the
application. Deployment uses application.tar.gz, not the Recipe-specific python-recipe.tar.gz.
Keep the complete package together. [Quickstart](../../docs/getting-started/README.md) explains
public-key SSH and creating a fresh application directory; do not overwrite an existing application.
The monitor uses only the SDK's base dependencies. The device does not need a repository or Bazel.
Stop with Ctrl+C or allow the duration to expire; no daemon, auto-restart or autostart is configured.

## Create your own C++ application

In the development container, at the VBOT Lab root, select another new output directory:

```bash
python3 tools/create_app.py --language cpp --name my-cpp-monitor --output /tmp/my-cpp-monitor
```

The generated workspace includes the C++ source/model/decoder tests, CLI tests, shared helpers,
local SDK repository rule, ARM64 toolchain, configuration, licenses and paired README/AGENTS
documents. It needs no source/Bazel labels from this checkout. SDK artifacts remain separate;
use the native SDK for native tests/previews and ARM64 SDK for cross-builds.
Follow the [C++ workspace guide](../../templates/cpp-app/README.md) for packaging only the
binary/runtime libraries and running as vbot. The Python package_app.py tool is not used.
See [application templates](../../templates/README.md) for the generator's scope and files.

For problems, use the [layered diagnostic guide](../../docs/development/diagnostics.md).
