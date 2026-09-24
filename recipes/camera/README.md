# Read camera images

<p align="center">English | <a href="README.zh-CN.md">中文</a></p>

[Recipes index](../README.md) · [Python](main.py) · [C++](main.cc)

Interface: `/image_left_raw/h265`, `/image_right_raw/h265` — pub/sub.

Generated types: `foxglove.CompressedVideo`.

Selects one camera and prints format, frame ID, acquisition timestamp and payload size. The payload is an H.265 Annex B stream, not JPEG or RGB. The default path only reads metadata. With permission, save compressed bytes to a new file or use `--decode` to obtain RGB images in memory. Use one decoder per camera. Decoding needs a keyframe and VPS/SPS/PPS; joining mid-stream may produce no image until they arrive.

## Python: build and offline preview

```bash
bazel build //recipes/camera:main
bazel run //recipes/camera:main
```

By default, prints only a JSON request plan: no SDK installation, device connection, or request.

## Python: run on the robot

First complete [Python deployment](../../docs/development/python-deployment.md): transfer this recipe and matching wheels, then create the device venv. In the resulting application directory (APP_DIR), with its venv activated and device environment configured, run:

```bash
python -m recipes.camera.main --camera left --execute --count 60 --timeout 10
```

Optional image decoding: prepare architecture-matching wheels in `artifacts/wheelhouse`
using the [offline guide](../../docs/development/offline-build.md), then install in the
executing machine's venv. Binary saving also needs NumPy for bulk payload extraction:

```bash
python -m pip install --no-index --find-links artifacts/wheelhouse av==16.1.0 numpy==2.2.6
python -m recipes.camera.main --camera left --execute --count 120 --timeout 20 --decode --consent
python -m recipes.camera.main --camera left --execute --count 120 --timeout 20 --output left.h265 --consent
```

The decoder calls `frame.to_rgb()`; access pixels through `bytes(rgb.planes[0])` and respect `plane.line_size` row padding. Output reports decoded width, height, pixel format and row stride. No decoded image by the limit is an error, not success. A saved stream may start before a usable keyframe. There is no stereo synchronization or image-file export in this example. For person detection, prefer the built-in [perception outputs](../../docs/interfaces/perception.md); decoding and a new model are not prerequisites for that task.

## C++

First follow the [C++ SDK guide](../../packages/aorta/cpp/README.md) for matching SDK/Schema archives, compiler and two artifact paths. On the build machine, build the C++ target explicitly; even previews require SDK linkage, but never create a Node or access a device:

```bash
bazel build //recipes/camera:main_cpp
bazel run //recipes/camera:main_cpp
```

Follow [binary deployment](../../packages/aorta/cpp/README.md#run-on-the-robot) with RECIPE=camera. After vbot SSH login, switch to the deployed application directory and configure the shell and library path as shown there. With the task prerequisites above satisfied, run the executable directly:

```bash
./bin/camera --camera left --execute --count 60 --timeout 10
```

The robot does not need Bazel, a compiler, or a repository checkout. C++ uses the same routes, operation permissions and completion conditions as Python; read-only subscriptions never publish commands.

The basic `:main_cpp` target needs only Aorta and can save compressed bytes with
`--output left.h265 --consent`; H.265 is not RGB. For C++ decoding, meet the optional
[FFmpeg build prerequisites](../../packages/aorta/cpp/README.md), build and deploy `:main_cpp_decode` as `bin/camera-decode` together with its FFmpeg runtime libraries, then run on the configured device:

```bash
./bin/camera-decode --camera left --decode --consent --execute --count 120 --timeout 20
```

In [decoder.h](decoder.h), `rgb` owns contiguous RGB24 bytes with row stride width × 3.
Consume or transfer that buffer before leaving the frame scope. Use one decoder per
camera; delayed frames are drained at completion. No decoded image is an error.
This example neither saves image files nor synchronizes stereo frames.

## Completion, failures and exit

Output is JSON Lines. Exit 0 means the example finished (including an offline preview), 1 runtime failure/timeout, 2 invalid arguments, and 130 interruption. Check the execute flag and output semantics; a preview is not live success. Waits are bounded; receive-queue overflow is an error rather than silently claiming complete data. Subscribers, clients and Node are closed on exit.

Files are created exclusively, never overwritten. Limits are 8 MiB per sample and 16 MiB per capture. Failure/interruption may leave a partial file; inspect the error and retain or remove it according to privacy requirements.

For tests, see [Recipes](../README.md); default tests never connect to or operate a robot.
