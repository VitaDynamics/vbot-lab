# System and peripherals

<p align="center">English | <a href="README.zh-CN.md">中文</a></p>

[Family index](../README.md) · [Interface contract](../../docs/interfaces/system-peripherals.md) · [Python](main.py) · [C++](main.cc)

## Select a stream

`--stream`: system → /system/sm_status; display → /display_node/status.

System output preserves category, lifecycle status, severity, active-state path, timestamp and heartbeat. A system observation does not complete an unrelated application request. Display data remains opaque text, not an assumed JSON object or image. These subscriptions never change lights or display contents. For existing read-only firmware and light queries, see [device-info](../device-info/README.md) and [service-call](../service-call/README.md).

## Build and offline preview

Python and C++ accept the same arguments. Defaults print a plan without creating a Node. C++ builds and previews require matching SDK/Schema artifacts.

```bash
bazel build //recipes/system-peripherals:main //recipes/system-peripherals:main_cpp
bazel run //recipes/system-peripherals:main -- --stream system
bazel run //recipes/system-peripherals:main_cpp -- --stream system
```

## Read on the robot

For Python, complete [Python deployment](../../docs/development/python-deployment.md) for this recipe. Run as vbot from the resulting application directory (APP_DIR), using its newly created venv and configured device environment. For C++, follow [binary deployment](../../packages/aorta/cpp/README.md), naming the deployed executable bin/system-peripherals; its application directory is separate from the Python deployment.

```bash
python -m recipes.system-peripherals.main --stream system --count 3 --timeout 20 --execute
```

C++: switch to the deployed binary's application directory and configure its runtime libraries as in the C++ guide, then run:

```bash
./bin/system-peripherals --stream system --count 3 --timeout 20 --execute
```

Select one stream at a time. Replace --stream using the list above; do not automatically restart services or switch modes to obtain samples.

## Output and exit

A zero or missing timestamp is unknown, not evidence of freshness. Reading three messages alone does not guarantee advancing source time; check timestamps, state and validity before using the data.

Output is JSON Lines, retaining the source topic and capture time when the source supplies it. Non-finite numbers become null. A received sample does not establish validity or permission to control the robot; check state, validity and timestamps against the contract. Timeout means no sufficient samples, not zero values or absence. --count is 1–1000; --timeout is (0,120] seconds for the whole capture. Queue/sample overflow fails explicitly. Exit codes: 0 preview or requested reads completed, 1 runtime failure/timeout, 2 invalid arguments, 130 interruption. Exit closes subscriptions and Node; there are no automatic retries or command publications.
