# Perception

<p align="center">English | <a href="README.zh-CN.md">中文</a></p>

[Family index](../README.md) · [Interface contract](../../docs/interfaces/perception.md) · [Python](main.py) · [C++](main.cc)

## Select a stream

`--stream`: detections → /perception/detections2d; poses → /perception/poses.

Detections contain string classes, scores, pixel boxes, image dimensions and capture timestamps. person_boxes counts current person-class boxes without confidence filtering; it is not a unique-person count. A received empty array is different from a missing sample. Poses contain one person's COCO keypoints; confidence is a logit, and the example also computes a stable sigmoid probability. Coordinates are image pixels, not robot pose or depth. Pose output requires a pose model and a visible person; silence never proves absence. No images are saved, and no speech or motion is triggered.

## Build and offline preview

Python and C++ accept the same arguments. Defaults print a plan without creating a Node. C++ builds and previews require matching SDK/Schema artifacts.

```bash
bazel build //recipes/perception:main //recipes/perception:main_cpp
bazel run //recipes/perception:main -- --stream detections
bazel run //recipes/perception:main_cpp -- --stream detections
```

## Read on the robot

For Python, complete [Python deployment](../../docs/development/python-deployment.md) for this recipe. Run as vbot from the resulting application directory (APP_DIR), using its newly created venv and configured device environment. For C++, follow [binary deployment](../../packages/aorta/cpp/README.md), naming the deployed executable bin/perception; its application directory is separate from the Python deployment.

```bash
python -m recipes.perception.main --stream detections --count 3 --timeout 20 --execute
```

C++: switch to the deployed binary's application directory and configure its runtime libraries as in the C++ guide, then run:

```bash
./bin/perception --stream detections --count 3 --timeout 20 --execute
```

Select one stream at a time. Replace --stream using the list above; do not automatically restart services or switch modes to obtain samples.

## Output and exit

A zero or missing timestamp is unknown, not evidence of freshness. Reading three messages alone does not guarantee advancing source time; check timestamps, state and validity before using the data.

Output is JSON Lines, retaining the source topic and capture time when the source supplies it. Non-finite numbers become null. A received sample does not establish validity or permission to control the robot; check state, validity and timestamps against the contract. Timeout means no sufficient samples, not zero values or absence. --count is 1–1000; --timeout is (0,120] seconds for the whole capture. Queue/sample overflow fails explicitly. Exit codes: 0 preview or requested reads completed, 1 runtime failure/timeout, 2 invalid arguments, 130 interruption. Exit closes subscriptions and Node; there are no automatic retries or command publications.
