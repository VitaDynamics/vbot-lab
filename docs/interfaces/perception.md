# Object detection and human keypoints

<p align="center">English | <a href="perception.zh-CN.md">中文</a></p>

For Python/C++ read-only examples, see the [perception Recipe](../../recipes/perception/README.md), including Bazel builds, offline previews, and explicit device reads.

Use the built-in perception outputs for person-triggered greetings, visible-person counts,
image-region triggers, and keypoint-based interactions. Consuming these results does not
require decoding camera video or deploying another detection model. AprilTag detection
recognizes tags; it is not a person detector.

## Prerequisites and interfaces

The current scope is robot application **V1.6.0** on `foot_quadruped` EDU.
Check route availability against the [compatibility matrix](../compatibility.md).
Log in with the vbot account and complete
[device shell setup](../getting-started/device-environment.md). Camera input and the
perception service must be running. Available classes and keypoints depend on the installed
model; the current default model detects people.

Both interfaces are **pub/sub, read-only subscriptions**, not services or control inputs.

| Output | Aorta topic | Aorta root type | ROS 2 topic | ROS 2 message type |
| --- | --- | --- | --- | --- |
| 2D detections | `/perception/detections2d` | `perception.Detection2DArray` | `/perception/detections2d` | `vision_msgs/msg/Detection2DArray` |
| Human keypoints | `/perception/poses` | `perception.PoseDetection` | `/perception/poses` | `vision_msgs/msg/PoseDetection` |

Use the ROS message types delivered with the device overlay, including its human-keypoint
type. An unrelated workstation installation is not a substitute for that overlay.

## Discover and inspect

Inspect both routes as one perception family in the device shell. These commands inspect
metadata without collecting images; they are not two independent capability checks:

```bash
timeout 15s aorta topic list
timeout 15s aorta schema get /perception/detections2d --describe
timeout 15s aorta schema get /perception/poses --describe
timeout 15s ros2 topic list --no-daemon -t
timeout 15s ros2 interface show vision_msgs/msg/Detection2DArray
timeout 15s ros2 interface show vision_msgs/msg/PoseDetection
```

Then choose the stream needed by the application and take one bounded sample:

```bash
timeout 15s aorta topic echo /perception/detections2d --count 1
```

For human-keypoint work, sample this instead:

```bash
timeout 15s aorta topic echo /perception/poses --count 1
```

A ROS subscription can be checked independently:

```bash
timeout 15s ros2 topic echo /perception/detections2d vision_msgs/msg/Detection2DArray --no-daemon --once --qos-reliability best_effort
```

A listed route and a readable Schema confirm discovery and decoding information, not live
frames. A received message confirms data delivery at that time. Exit code `124` means no
sample arrived before the deadline; do not infer that no person is present.

## Interpret 2D detections

- Both detection and pose model modes publish one array per processed frame. An empty
  `detections` array means that frame produced no detections; it is different from no message.
- Each detection has a string `class_id` (`person` for a person), a detection `score`, and
  a pixel-space `bbox` with `center_x`, `center_y`, `width`, and `height`.
- The array's `frame_width` and `frame_height` describe the source image dimensions;
  `timestamp_ns` is the capture timestamp in nanoseconds and `frame_id` identifies the
  source frame. These are image coordinates, not metric positions in the robot or map frame.
- In ROS, the class and score are in `detections[].results[].hypothesis.class_id` and
  `detections[].results[].hypothesis.score`; the box uses `bbox.center.position.x`,
  `bbox.center.position.y`, `bbox.size_x`, and `bbox.size_y`. Capture time and frame identity
  are in `header`. The bridge does not carry the Aorta image-width/height fields into this
  ROS type; use Aorta when those dimensions are needed. Do not assume the dimensions of an
  independently selected video stream match the detector input.
- These results do not provide stable person identities or 3D body locations. Counting
  visible boxes is not counting unique visitors. Other model classes must be checked against
  the installed model rather than assumed from the message type.

## Interpret human keypoints

- Published only with `model_type=pose`, one message per detected person. No person means
  no pose message, not an empty-frame message. Use the detection-array stream to distinguish
  a fresh empty detection result from missing data.
- `class_id` is numeric (`0` for a person), unlike the detection array's string class.
  `score` is the person detection confidence. `bbox_min` and `bbox_max` are pixel-space
  corners; `keypoints` contains 17 COCO points. The extra coordinate `z` in the box points
  is zero, not a measured depth.
- Keypoint `confidence` is a **logit**, not a probability between 0 and 1. If a probability
  threshold is needed, apply a numerically stable sigmoid first; do not reuse a detection
  score threshold directly on logits. Ignore invalid or low-confidence keypoints.
- COCO order: nose; left/right eye; left/right ear; left/right shoulder; left/right elbow;
  left/right wrist; left/right hip; left/right knee; left/right ankle.
- Aorta carries capture time in `timestamp_ns` and source identity in `frame_id`; ROS uses
  `header`. Keypoint confidence remains a logit after bridging. These are human image-space
  poses, **not robot odometry or localization**. Gesture labels and action recognition are
  application logic, not additional outputs of this topic.

## Build a “see a person, say hello” application

1. Subscribe to the detection-array topic and confirm fresh frames arrive. Filter for
   the person class and a suitable detection confidence. Use a bounded queue so old frames
   do not accumulate.
2. Maintain presence state: unknown, absent, or present. Confirm presence across a short
   sequence of fresh frames to reduce one-frame triggers. An initial confirmed presence
   may greet once; subsequent greetings require a confirmed absence followed by presence.
3. Re-arm only after a sequence of fresh frames without a qualifying person. Missing or
   stale frames return the state to unknown; they must not count as a person leaving or
   re-arm a greeting. Retain the greeting latch across a data outage.
4. On a greeting trigger, call the documented [speech service](aorta-ros2.md) through
   `/speech/set_speak` or ROS `/set_speak`. Inspect the delivered request type before
   constructing the payload. Speech playback is an explicit application action, not a
   read-only setup check. Add a cooldown and prevent overlapping requests; handle service
   errors without retrying on every camera frame.
5. Keep the subscription loop running for the interaction, then close subscriptions and
   release resources on exit. Editing device AGENTS.md alone does not implement this loop.

This flow can greet once per presence episode; it does not identify individuals. Use the
keypoint stream only when the interaction also needs a gesture or body posture.

## If data is missing

Check route discovery, loaded message types, timestamps, camera input, and perception
activity. For keypoints, also check the installed model mode and whether a person is in
view. Do not automatically switch models or restart device services. For ROS-only issues,
compare an Aorta sample and follow the [device environment troubleshooting](../getting-started/device-environment.md).
