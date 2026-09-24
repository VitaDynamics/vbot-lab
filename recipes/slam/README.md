# SLAM observations

<p align="center">English | <a href="README.zh-CN.md">中文</a></p>

[Family index](../README.md) · [Interface contract](../../docs/guides/mapping-localization.md) · [Python](main.py) · [C++](main.cc)

## Select a stream

`--stream`: status → /slam/status; odometry → /odometry; transforms → /slam/static_transforms.

Read status before interpreting odometry. Position and orientation must both exist before the example emits a pose; otherwise it emits null. The primary pose is distinct from body_in_map and head_in_body. Units are meters and x/y/z/w quaternions. Origin changes require a frame conversion; the name map alone does not define a persistent map origin. Static transforms arrive periodically. None of these commands starts mapping, saves or replaces a map, resets odometry, or moves the robot. Use the linked mapping guide for deliberate mode changes.

## Build and offline preview

Python and C++ accept the same arguments. Defaults print a plan without creating a Node. C++ builds and previews require matching SDK/Schema artifacts.

```bash
bazel build //recipes/slam:main //recipes/slam:main_cpp
bazel run //recipes/slam:main -- --stream status
bazel run //recipes/slam:main_cpp -- --stream status
```

## Read on the robot

For Python, complete [Python deployment](../../docs/development/python-deployment.md) for this recipe. Run as vbot from the resulting application directory (APP_DIR), using its newly created venv and configured device environment. For C++, follow [binary deployment](../../packages/aorta/cpp/README.md), naming the deployed executable bin/slam; its application directory is separate from the Python deployment.

```bash
python -m recipes.slam.main --stream status --count 3 --timeout 20 --execute
```

C++: switch to the deployed binary's application directory and configure its runtime libraries as in the C++ guide, then run:

```bash
./bin/slam --stream status --count 3 --timeout 20 --execute
```

Select one stream at a time. Replace --stream using the list above; do not automatically restart services or switch modes to obtain samples.

## Output and exit

A zero or missing timestamp is unknown, not evidence of freshness. Reading three messages alone does not guarantee advancing source time; check timestamps, state and validity before using the data.

Output is JSON Lines, retaining the source topic and capture time when the source supplies it. Non-finite numbers become null. A received sample does not establish validity or permission to control the robot; check state, validity and timestamps against the contract. Timeout means no sufficient samples, not zero values or absence. --count is 1–1000; --timeout is (0,120] seconds for the whole capture. Queue/sample overflow fails explicitly. Exit codes: 0 preview or requested reads completed, 1 runtime failure/timeout, 2 invalid arguments, 130 interruption. Exit closes subscriptions and Node; there are no automatic retries or command publications.
