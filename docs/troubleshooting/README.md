# Troubleshooting

<p align="center">English | <a href="README.zh-CN.md">中文</a></p>

Start with the first failing step, not a service restart. Repository inspection may run on
the host; build, SDK, preview and packaging checks run in the development container.
Device commands run only in the selected robot's vbot shell, after authorized SSH login.
See [execution locations](../development/README.md) and [Quickstart](../getting-started/README.md).
Use [layered diagnostics](../development/diagnostics.md) for explicit Python checks or the
[C++ SDK/library/sample path](../development/diagnostics.md#cpp); a missing Python wheel is not a C++ failure.

| Symptom | Likely causes | Start here |
| --- | --- | --- |
| Container context rejected | Host shell, undeclared container session, wrong workspace | [Container context](#container) |
| SDK import or shared library fails | Wrong interpreter, ROS PYTHONPATH, wrong architecture, mismatched wheels | [SDK import](#sdk-import) |
| Bazel build fails or dependencies cannot download | Wrong Bazel/toolchain, unavailable dependency bundle | [Build](#build) |
| Package missing files or checksum failure | Incomplete download, altered output, wrong target | [Package](#package) |
| SSH timeout, authentication or host-key error | Network/address, key access or host identity | [SSH](#ssh) |
| Topic is listed but no decoded sample arrives | Shell/session/type/producer/input not yet confirmed | [No data](#no-data) |
| Deployed application fails to start | Wrong directory/interpreter, missing dependency or ABI mismatch | [Runtime](#runtime) |

<a id="container"></a>
## Container context

On the host, inspect and reuse the container following the [container guide](../../docker/README.md).
Inside the selected container, at its checkout root:

```bash
python3 tools/container_context.py
python3 tools/check_environment.py --profile container
```

`context_status=eligible` requires runtime evidence and the declared development context;
it does not prove image, mount, toolchain or SDK compatibility. Compose/editor sessions set
the declaration automatically; use the documented exec command for an existing container.
If already inside a confirmed development container, inspect and reuse it; do not require
nested Docker. A host flag alone is not a fix. Do not recreate containers, reset caches or
change Docker permissions automatically.

<a id="sdk-import"></a>
## SDK import

In the development container or the deployed application's vbot shell, use that application's
venv interpreter. For a robot installation, first enter its recorded APP_DIR:

```bash
unset PYTHONPATH
unset AORTA_CORE_FFI_LIB
export PYTHONNOUSERSITE=1
.venv/bin/python --version
.venv/bin/python -m pip check
.venv/bin/python -c 'import platform; import importlib.metadata as m; print(platform.machine()); print({name:m.version(name) for name in ("aorta-sdk","aorta-msgs","vbot-edu-msgs","flatbuffers")})'
.venv/bin/python -c 'import aorta; from locomotion.LocomotionStatus import LocomotionStatus; core = aorta.load_library(); print("SDK imports and native runtime OK; ABI", core.aorta_abi_version())'
```

Expected: Python 3.10+, the selected architecture, the versions recorded in the package's
requirements, and successful imports/native loading with the ABI printed. `ModuleNotFoundError` suggests the wrong interpreter
or missing wheel; `wrong ELF class`, `Exec format error`, `GLIBC_*` or `GLIBCXX_*` errors
require architecture/runtime investigation, not repeated pip installation. An SDK version
printed by package metadata does not prove its native library can load. The explicit
`load_library()` check runs the ABI guard without creating a Node; ordinary imports leave
the native runtime unloaded. Follow the
[Python SDK](../../packages/aorta/python/README.md) or [C++ SDK](../../packages/aorta/cpp/README.md).
Do not copy a workstation venv or replace robot system libraries.

<a id="build"></a>
## Bazel build

Inside the development container:

```bash
bazel --version
g++ -dumpmachine
python3 tools/in_container.py -- bazel build //recipes/subscribe-state:main
```

Use Bazel 7.6.1 and the intended compiler architecture. An x86_64 C++ binary is not an
ARM64 deployment artifact. If dependency downloads fail, obtain a matching verified bundle
and use the [offline build entry](../development/offline-build.md). SDK archives alone are
not a Bazel dependency bundle. Do not change registries, delete caches or compile on the
robot as an automatic workaround.

On a fresh image, bazel --version may first download the pinned tool through Bazelisk.
SDK CI gives this preparation 180 seconds, configurable with --bazel-prepare-timeout (30–600).
For stage=bazel_prepare, check the reported reason and download access before investigating
SDK compatibility; see [SDK integration](../../tools/README.md#sdk-integration-without-a-robot).

<a id="package"></a>
## Package generation or verification

The package command checks input hashes, wheel metadata, base dependency closure and
license presence before creating output. Missing or inconsistent inputs are explicit errors:
use the matching Release assets rather than files from unrelated SDK versions.
Existing output is never overwritten. To inspect a complete generated package, on the host
or in the container:

```bash
python3 tools/package_python.py --verify artifacts/first-state
```

Expected: `status=complete`, `device_contacted=false`, `deployed=false`. An altered or incomplete
package must not be transferred. Inspect the failure and regenerate into a new directory;
do not edit hashes merely to make verification pass. `base` packages do not include NumPy/PyAV
for optional payload saving/decoding. Details are in [Python deployment](../development/python-deployment.md).

<a id="ssh"></a>
## SSH

On the machine that will transfer the package, use the confirmed device IP or vbot alias:

```bash
ROBOT=vbot@192.168.126.2
ssh -o BatchMode=yes "$ROBOT" 'id -un; uname -m; python3 --version'
```

Expected: `vbot`, `aarch64`, Python 3.10+. For timeout/no route/refused, check physical or
Wi-Fi connection and the address. For `Permission denied`, check the selected public key and
SSH-agent access in this same environment. For an unknown/changed host key, verify the robot
identity and fingerprint before proceeding. Follow [connection setup](../robots/quadruped-common/connection.md).
Do not scan for another robot, embed passwords, disable host-key checking or overwrite keys.

<a id="no-data"></a>
## Topic listed but no data

After SSH login, load the public device environment and inspect only the route needed by
the application. For the first read-only example, in the vbot device shell:

```bash
export PATH="/opt/vita/aorta/bin:$PATH"
export ZENOH_SESSION_CONFIG_URI=/opt/vita/aorta/edu/edu_session.json5
test -r "$ZENOH_SESSION_CONFIG_URI"
timeout 12s aorta --group default topic echo /locomotion/status --count 1
```

If CLI receives a decoded sample but the application does not, check its interpreter,
Schema pairing and effective process environment. If neither receives data, check the
[device environment](../getting-started/device-environment.md), exact [route/type](../interfaces/aorta-ros2.md),
installed software and whether the producer/input is expected to be active. A directory
entry is not a sample; a timeout alone does not prove ACL rejection, unsupported capability,
a stopped producer or absence of people/audio. Keep unconfirmed causes unconfirmed.
Do not change permissions, robot modes or services to force a sample. Audio/video capture
still requires its own consent. For ROS-only failures, compare native Aorta reception first.

<a id="runtime"></a>
## Deployed application does not start

Confirm the recorded application directory, explicit venv/binary path, package checksum,
architecture and session environment. The robot has no preinstalled repository checkout;
a workstation Bazel launcher is not a deployment artifact. For C++, run the documented
`ldd` check on the deployed executable and required libraries. Return to the build/package
step if dependencies or GLIBC compatibility are wrong. Configure [autostart](../guides/user-autostart.md)
only after interactive execution works; non-interactive shells need explicit environment loading.

<a id="application-errors"></a>

## Python health-monitor errors

The reference application and generated Python workspaces report JSON errors on stderr:

```json
{"status":"error","stage":"config","error_code":"config_not_found","next_step":"Select an existing configuration file with --config."}
```

| Stage / error code | Next check |
| --- | --- |
| config / config_not_found, config_not_readable, config_read_failed | Select a readable configuration file; check file access/storage, not the device connection |
| config / invalid_config | Use UTF-8 JSON with exactly stale_after_seconds in (0, 120] and low_battery_percent in [0, 100] |
| environment / development_container_required | Run preview/simulation in the selected development container |
| environment / device_user_required, session_config_not_set, session_config_not_readable | Check the vbot shell and documented device Aorta environment |
| sdk / sdk_not_installed, sdk_version_mismatch, sdk_load_failed | Use the application venv and pinned requirements; check message bindings/BFBS files |
| subscription / subscription_setup_failed | Check the Aorta environment and selected routes with bounded read-only diagnostics |
| subscription / telemetry_queue_overflow, sdk_samples_dropped | The application stopped to avoid hiding data loss; inspect processing load/subscription settings |
| runtime / unexpected_error | Check the last completed stage and application changes; review logs before sharing |

These failures exit 1 without printing raw exceptions or configuration contents. A normal final
snapshot with missing/stale streams also exits 1 but is not a configuration exception; inspect its
stream statuses. CLI usage errors still exit 2, and interruption exits 130. No error automatically
restarts a service, changes permissions, installs dependencies or contacts another device.

## Ask the community

If unresolved, use [Vbot 超能社区](https://forum.vbot.cn/) and the
[Community & Support](../community/README.md) report template. Include the failing step,
source/SDK pairing, expected result, observed exit/error and checks already performed.
Identify unverified device/application versions as unknown rather than substituting a system
image or CLI version. Review and sanitize the report before sharing: no session files,
credentials, private keys, full environment dumps, device identities or unapproved recordings.
Do not automatically post logs. Share the solution in the same topic when resolved.
Use GitHub Issues for a specific repository bug; report vulnerabilities privately through
[Security](../../SECURITY.md).
