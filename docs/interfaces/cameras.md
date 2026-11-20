# Cameras, calibration, and AprilTags

<p align="center">English | <a href="cameras.zh-CN.md">中文</a></p>

Use this family for image capture/decoding, calibrated image processing, and tag-based interaction.

For Python/C++ implementations, see the [camera Recipe](../../recipes/camera/README.md): source, Bazel targets, deployment and explicit device execution. The interface semantics below remain authoritative.
The topic table below lists read-only pub/sub outputs for `foot_quadruped` EDU / DEV.
Log in, complete [device shell setup](../getting-started/device-environment.md), and use
the [interface table](aorta-ros2.md) for exact Aorta/ROS message types and mappings.

## Routes and data meaning

| Aorta topics | Meaning | Use |
| --- | --- | --- |
| `/stereo_left/camera_info`, `/stereo_right/camera_info` | Image dimensions, `distortion_model`, `d`, `k`, `r`, `p`, binning and ROI | Select calibration for the camera and image geometry being processed |
| `/image_left_raw/h265`, `/image_right_raw/h265` | Left/right compressed video | Decode only the side needed by the application |
| `/image_left_raw/h265_half`, `/image_right_raw/h265_half` | Half-stream variants | Select by measured decoded dimensions, not an assumed resolution |
| `/image_left_raw/h265_quarter`, `/image_right_raw/h265_quarter` | Quarter-stream variants | Lower-resolution image processing where suitable |
| `/image_left_raw/h265_undistort` | Left undistorted video | Use a matching rectified camera model, not raw-image distortion twice |
| `/stereo_apriltag/detection` | Left/right validity, tag IDs, decision margins, corners, camera parameters and frame IDs | Read tag detections directly; this is not human detection |

## Interpret the messages

- Video carries `timestamp`, `frame_id`, `format`, and compressed `data`, not an RGB array
  or an MP4 file. H.265 data uses Annex B NAL units; a decoder needs VPS/SPS/PPS parameters
  and a suitable keyframe. Keep one decoder state per stream; a single delta frame may not
  decode independently. Frame dimensions come from the decoded stream, not this message's fields.
- Calibration `k` and `r` are row-major 3×3 matrices, `p` is 3×4, and `d` depends on the
  distortion model. The camera optical frame points right/down/forward (+x/+y/+z).
  Check dimensions, binning, and ROI before using calibration on a resized or cropped stream.
- Tag data uses `left_valid` and `right_valid` independently. Read a side's tag ID/corners
  only when that side is valid. Decision margin is not a person-detection confidence.
  A tag message does not by itself supply a metric robot pose; pose estimation additionally
  requires the tag's physical size and matching calibration/coordinate transforms.

## Hardware decoding on S100

For H.265 hardware decoding on the robot, use the **D-Robotics S100 native multimedia
SDK**, specifically its MediaCodec APIs (`hb_mm_mc_*`). Follow the official
[S100 codec guide](https://developer.d-robotics.cc/rdk_s_doc/en/Advanced_development/multimedia_development/S100/codec)
for decoder configuration, input/output buffers and resource release.
The Aorta SDK receives compressed video; decoding is a separate application step.

The device image grants the `vbot` account read/write access to `/dev/vpu` through
the `vpu` group. After SSH login, check the actual session without accessing the
codec or changing permissions:

```sh
id -nG
stat -c 'device=%n mode=%a group=%G' /dev/vpu
if [ -c /dev/vpu ] && [ -r /dev/vpu ] && [ -w /dev/vpu ]; then
  printf '%s\n' '/dev/vpu is readable and writable'
else
  printf '%s\n' '/dev/vpu is missing or not readable/writable' >&2
  exit 1
fi
```

Expect `vpu` in the session's groups, that group on the device node, and a successful
permission check. This checks access only; decoder initialization, buffer allocation
and frame output must still succeed in your application. If access fails, retain the
output and contact support rather than changing device permissions.

Use native SDK headers and libraries matching the delivered device software. Build
ARM64 applications in the development container and deploy the executable and its
required libraries through the [C++ deployment flow](../../packages/aorta/cpp/README.md#run-on-the-robot).
Feed one subscribed H.265 stream to each decoder and respect the SDK's buffer ownership,
output format and stride. Stop and release your own decoder on exit without interrupting
the robot's camera services. The [S100 C++ hardware-decoding example](../../recipes/camera/README.md#c-s100-hardware-decoding)
shows the complete build/deployment flow and borrowed NV12 buffer handling.
The separate PyAV/FFmpeg paths do not select this native backend.

## JPEG snapshot dimensions

For the `/get_jpeg_images` service, request-item `width` and `height` are
**selection hints, not a guarantee of the returned resolution**. The camera selects
the closest enabled VSE (image-scaling output) channel by minimizing
`abs(requested_width - channel_width) + abs(requested_height - channel_height)`.
It does not arbitrarily resize the JPEG to the requested dimensions.

Use each response item's actual `width` and `height`, and check that they match
the decoded JPEG. For example, a 640×360 request can return a decodable 480×270
image when that is the selected enabled output. This dimension difference alone
is expected selection behavior, **not evidence of an Aorta/ROS 2 Bridge failure**.
Available output sizes depend on the camera configuration; this example is not
a fixed request-to-response mapping.

Check the item `status` and decode `data` before processing it. Allocate buffers,
interpret pixel coordinates and select calibration using the actual returned geometry.
If the application needs an exact input size, explicitly resize the decoded image
in the application and adjust pixel coordinates and camera intrinsics accordingly.
Failed decoding, unsuccessful status or a mismatch between response dimensions and
the decoded image should be investigated separately from request/response size differences.
See the [JPEG request and response schema](../../schemas/aorta/schemas/service/stereo/get_jpeg_images.fbs).

## Minimal reading and application flow

Metadata and calibration can be inspected without dumping a video payload:

```bash
timeout 15s aorta topic list
timeout 15s aorta schema get /image_left_raw/h265 --describe
timeout 15s aorta schema get /stereo_left/camera_info --describe
timeout 15s aorta topic echo /stereo_left/camera_info --count 1
```

For a tag interaction, inspect and read its processed output instead:

```bash
timeout 15s aorta schema get /stereo_apriltag/detection --describe
timeout 15s aorta topic echo /stereo_apriltag/detection --count 1
```

1. Choose one image stream, open a bounded subscription, and initialize a compatible H.265
   decoder for the architecture where it runs. Metadata discovery alone does not check decoding.
2. Wait for codec initialization data and a decodable frame. Associate frame timestamps,
   dimensions, and frame IDs with the matching calibration; pair stereo frames by capture
   time, not receipt order. Do not mix the two cameras' byte streams.
3. Process current frames with a bounded queue. After loss or reconnect, resynchronize the
   decoder at an appropriate keyframe instead of presenting corrupted/stale frames.
4. Close the decoder and subscription on exit. Obtain permission before recording people
   or retaining images. For [person detection](perception.md), prefer the built-in processed
   results unless the application specifically needs images or a different model.

## If output is missing or unusable

Check route/type discovery, camera activity, matching frame/calibration dimensions, and
codec parameters. No tag with valid flags may simply mean no supported tag is visible.
If a video route exists but frames cannot decode, inspect decoder support and stream
initialization before changing device configuration. Exit `124` is a bounded wait ending,
not proof of a camera failure or a decoded frame.
