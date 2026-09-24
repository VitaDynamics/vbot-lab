# Sensors

<p align="center">English | <a href="README.zh-CN.md">中文</a></p>

[Family index](../README.md) · [Interface contract](../../docs/interfaces/sensors.md) · [Python](main.py) · [C++](main.cc)

## Select a stream

`--stream`: battery → /bms_state; imu → /imu_raw; lidar-imu → /lidar_imu; points → /lidar_points.

Battery output converts mV/mA to V/A while retaining signed current, SOC, alarm and charger connection. IMU output preserves acquisition time, frame, quaternion and covariance; angular velocity and acceleration are emitted as raw values without inferred unit conversion. Confirm the selected firmware/stream units before numerical integration. orientation_unit_length only checks a finite quaternion norm within 0.01 of one; it is not a validity guarantee. Do not use invalid orientation or silently normalize it. Covariance -1 denotes an unavailable estimate; zero covariance does not prove perfect certainty. Point clouds expose byte length, stride and field layout, not a guessed XYZ structure. This example does not copy or save raw point bytes.

## Build and offline preview

Python and C++ accept the same arguments. Defaults print a plan without creating a Node. C++ builds and previews require matching SDK/Schema artifacts.

```bash
bazel build //recipes/sensors:main //recipes/sensors:main_cpp
bazel run //recipes/sensors:main -- --stream battery
bazel run //recipes/sensors:main_cpp -- --stream battery
```

## Read on the robot

For Python, complete [Python deployment](../../docs/development/python-deployment.md) for this recipe. Run as vbot from the resulting application directory (APP_DIR), using its newly created venv and configured device environment. For C++, follow [binary deployment](../../packages/aorta/cpp/README.md), naming the deployed executable bin/sensors; its application directory is separate from the Python deployment.

```bash
python -m recipes.sensors.main --stream battery --count 3 --timeout 20 --execute
```

C++: switch to the deployed binary's application directory and configure its runtime libraries as in the C++ guide, then run:

```bash
./bin/sensors --stream battery --count 3 --timeout 20 --execute
```

Select one stream at a time. Replace --stream using the list above; do not automatically restart services or switch modes to obtain samples.

## Output and exit

A zero or missing timestamp is unknown, not evidence of freshness. Reading three messages alone does not guarantee advancing source time; check timestamps, state and validity before using the data.

Output is JSON Lines, retaining the source topic and capture time when the source supplies it. Non-finite numbers become null. A received sample does not establish validity or permission to control the robot; check state, validity and timestamps against the contract. Timeout means no sufficient samples, not zero values or absence. --count is 1–1000; --timeout is (0,120] seconds for the whole capture. Queue/sample overflow fails explicitly. Exit codes: 0 preview or requested reads completed, 1 runtime failure/timeout, 2 invalid arguments, 130 interruption. Exit closes subscriptions and Node; there are no automatic retries or command publications.
