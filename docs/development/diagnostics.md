# Layered diagnostics

<p align="center">English | <a href="diagnostics.zh-CN.md">中文</a></p>

Each level is explicit and independent. Inventory does not authorize a robot connection,
installation or the next level. diagnose.py prints a minimal JSON summary, not raw environment,
session contents, host addresses or exception traces. Review it before sharing in
[Vbot 超能社区](https://forum.vbot.cn/); no report is posted automatically.

## Choose the language first

diagnose.py's sdk and sample levels use the **Python SDK**, not the C++ SDK.
A missing Python wheel is not a C++ environment failure. C++ applications need no Python venv
or Python SDK on the robot: follow the [C++ path](#cpp) below. The inventory and device levels
only inspect tools/shell state and do not import either SDK.

| Level | Execution location | What it establishes |
| --- | --- | --- |
| inventory | Host or CI | Presence of Python/Bash/Git only; SDK/device remain not_verified |
| sdk | Development container, selected Python venv | Python package metadata, wheel-native runtime and ABI; no Node |
| device | Selected device vbot shell | Account, readable session file and environment; no interface contact |
| sample | Selected device vbot shell with Python SDK | One bounded raw state/battery/system sample; not decoded behavior |

## Python: local checks

From the checkout root, on the host or CI:

```bash
python3 tools/diagnose.py --level inventory
```

In the development container, using the venv where the matching Python SDK was installed:

```bash
.venv/bin/python tools/diagnose.py --level sdk
```

Expected: confirmed package checks and native_runtime_abi. confirmed_missing identifies a
missing tool/package; mismatch identifies a version difference. Inventory success does not
establish SDK installation. No dependency is automatically installed.

## Python: device checks

First log in to the selected device. The standalone diagnose.py needs no repository;
transferring it is a separate explicit step, like transferring an application.
Load PATH and ZENOH_SESSION_CONFIG_URI using [device setup](../getting-started/device-environment.md).
From the directory containing diagnose.py, in the device shell:

```bash
python3 diagnose.py --level device --allow-device-check
```

For Python SDK sampling, use the application's venv and replace the example path with APP_DIR.
Clear ROS/Python overrides:

```bash
unset PYTHONPATH &&
unset AORTA_CORE_FFI_LIB &&
export PYTHONNOUSERSITE=1 &&
/userdata/vbot/apps/my-app-REPLACE/.venv/bin/python diagnose.py \
  --level sample --allow-device-check --route state --timeout 5
```

Only state, battery and system are accepted. No audio/video capture, publishing, service/action
call, discovery scan or SSH is performed. Without --allow-device-check, device levels stop before
inspection. sample_received means bytes arrived; decoded:false does not claim semantic validation.
Use the application to decode. waiting_data_timeout leaves interface support and producer state
not_verified; it is not an ACL/firmware verdict. missing_or_unreadable does not distinguish an
absent file from an inaccessible one.

The sampling object records progress without claiming remote connectivity:

| Field | Meaning |
| --- | --- |
| attempted | SDK sampling was attempted after device prerequisites passed |
| session_opened | The local SDK Node context was successfully entered |
| subscription_created | The selected local subscription context was successfully entered |
| sample_received | A raw payload reached this diagnostic |

interfaces_contacted is retained for compatibility: true means subscription_created, not that
a producer was reached or the route is supported. False does not prove that no network activity
was attempted. SDK/session/subscription failures retain the reached flags and identify the failing
stage; no raw exception details are shared. A received sample does not hide a later cleanup failure.

Exit 0 means the selected level passed, 1 means blocked/attention required, and 2 means CLI misuse.
Sampling timeout is in (0, 30] seconds. The tool does not verify the application version, restart
services or change permissions.

<a id="cpp"></a>
## C++: build inputs, deployment libraries and samples

### SDK inputs — development container

Set verified AORTA_CPP_SDK_DIR and AORTA_EDU_SCHEMA_DIR using the
[C++ SDK guide](../../packages/aorta/cpp/README.md), then check:

```bash
test -n "$AORTA_CPP_SDK_DIR" &&
test -n "$AORTA_EDU_SCHEMA_DIR" &&
test -r "$AORTA_CPP_SDK_DIR/include/aorta/node.h" &&
test -r "$AORTA_CPP_SDK_DIR/lib/libaorta_cpp.a" &&
test -r "$AORTA_EDU_SCHEMA_DIR/include/locomotion_status_generated.h" &&
g++ -dumpmachine &&
aarch64-linux-gnu-g++ -dumpmachine &&
file "$AORTA_CPP_SDK_DIR/lib/libaorta_core.so.13"
```

Default g++ targets the container; aarch64-linux-gnu-g++ must report aarch64-linux-gnu.
The selected SDK ELF must match the chosen compiler target. Presence and file architecture
do not establish application linkage or runtime compatibility. From a generated C++ project,
run its native model/SDK/CLI tests with the native SDK, then cross-build with --config=arm64 and
the ARM64 SDK as described in its README. Do not run ARM64 tests in the AMD64 container,
use host ldd on ARM64 outputs, or install Python wheels to resolve C++ errors.

### Shared libraries — device vbot shell

For the [C++ health monitor](../../templates/cpp-app/README.md), after authorized SSH login,
replace APP_DIR with its printed deployment directory:

```bash
APP_DIR=/userdata/vbot/apps/cpp-app-REPLACE_FROM_OUTPUT &&
test "$(id -un)" = vbot &&
cd "$APP_DIR" &&
sha256sum -c SHA256SUMS &&
uname -m &&
export LD_LIBRARY_PATH="$PWD/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}" &&
LDD_OUTPUT=$(ldd ./bin/health-monitor) &&
printf '%s\n' "$LDD_OUTPUT" &&
[[ "$LDD_OUTPUT" != *"not found"* ]]
```

Expected: successful checksums, aarch64, and no unresolved dependencies. Resolve the packaged
Aorta runtime from the application's lib directory. A missing libaorta_core.so.13 means check
the complete package and LD_LIBRARY_PATH. Exec format error, GLIBC_* or GLIBCXX_* requires
matching the compiler/SDK/system runtime; repackage rather than replacing device system libraries.
For another C++ application, use its documented executable path and complete package inventory.

### Selected-route sample — device vbot shell

When read-only sampling is requested, use the device Aorta CLI; no Python SDK is needed:

```bash
export PATH="/opt/vita/aorta/bin:$PATH" &&
export ZENOH_SESSION_CONFIG_URI=/opt/vita/aorta/edu/edu_session.json5 &&
test -r "$ZENOH_SESSION_CONFIG_URI" &&
timeout 12s aorta --group default topic echo /locomotion/status --count 1
```

Only the selected state route is sampled. A decoded CLI sample checks that route/session,
not your C++ program's decoder. For the health monitor's three-stream behavior, enter its APP_DIR,
load the documented runtime environment and explicitly run ./bin/health-monitor --config config.json
--execute --duration 10. Keep callback receive time distinct from later dequeue time; SDK-reported
drops and application queue overflow are failures, not a reason to continue with incomplete input.

If CLI works but the binary does not, inspect shared libraries, Schema pairing and effective
process environment. If both time out, the cause remains unverified; do not change permissions,
robot modes or services to force data. See the [symptom index](../troubleshooting/README.md).
