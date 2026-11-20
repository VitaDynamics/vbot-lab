# Read camera images

<p align="center">English | <a href="README.zh-CN.md">中文</a></p>

[Recipes index](../README.md) · [Python](main.py) · [C++](main.cc) · [S100 hardware decoder](main_s100.cc)

Interface: `/image_left_raw/h265`, `/image_right_raw/h265` — pub/sub.

Generated types: `foxglove.CompressedVideo`.

Selects one camera and prints format, frame ID, acquisition timestamp and payload size. The payload is an H.265 Annex B stream, not JPEG or RGB. The default path only reads metadata. With permission, save compressed bytes to a new file or use `--decode` to obtain RGB images in memory. Use one decoder per camera. Decoding needs a keyframe and VPS/SPS/PPS; joining mid-stream may produce no image until they arrive.

For S100 hardware decoding, prefer the [D-Robotics native SDK](../../docs/interfaces/cameras.md#hardware-decoding-on-s100)
and check the `vbot` account's `/dev/vpu` access there. The separate
[S100 C++ target](#c-s100-hardware-decoding) below uses that backend. The existing
PyAV/FFmpeg targets remain available; their `--decode` flag does not select the VPU.

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

## C++: S100 hardware decoding

This target subscribes to the same left/right H.265 topics and decodes through the
S100 MediaCodec APIs, without FFmpeg or a software fallback. It reports NV12 frame
dimensions, Y/UV strides, timestamp and frame count; it never saves or exports pixels.
Use `--camera left` or `--camera right`, with one decoder per stream.

### Build in the development container

Prepare the **ARM64** Aorta SDK and EDU Schema following the
[C++ SDK guide](../../packages/aorta/cpp/README.md#build-arm64-binaries).
Separately obtain the matching D-Robotics S100 multimedia SDK through the
[official SDK documentation](https://developer.d-robotics.cc/rdk_s_doc/en/Advanced_development/multimedia_development/S100/codec).
Set `VBOT_S100_MULTIMEDIA_DIR` to an absolute directory visible inside the container,
with this layout and all symlink targets present:

```text
s100-multimedia-sdk/
├── include/
│   ├── hb_media_codec.h
│   ├── hb_media_basic_types.h
│   └── hb_media_error.h
└── lib/
    ├── libmultimedia.so
    ├── libhbmem.so.1
    └── libalog.so.1
```

Use complete, matching SDK headers and ARM64 libraries. This optional target reads
the supplied SDK locally; Bazel does not download it. Other Recipe targets do not
need this SDK. With `AORTA_CPP_SDK_DIR` and `AORTA_EDU_SCHEMA_DIR` already set:

```bash
export VBOT_S100_MULTIMEDIA_DIR=/absolute/path/to/s100-multimedia-sdk &&
bazel build --config=arm64 //recipes/camera:main_cpp_s100_decode &&
file bazel-bin/recipes/camera/main_cpp_s100_decode &&
aarch64-linux-gnu-readelf -d bazel-bin/recipes/camera/main_cpp_s100_decode
```

The output must be AArch64. Build, do not `bazel run`, this ARM64-only target in an
AMD64 container. Package the executable with the matching Aorta runtime and notices:

```bash
PACKAGE_DIR=$(mktemp -d /tmp/vbot-camera-s100-XXXXXX) &&
mkdir -p "$PACKAGE_DIR/bin" "$PACKAGE_DIR/lib" "$PACKAGE_DIR/licenses/aorta" &&
cp -L bazel-bin/recipes/camera/main_cpp_s100_decode "$PACKAGE_DIR/bin/camera-s100" &&
cp -L "$AORTA_CPP_SDK_DIR/lib/libaorta_core.so.14" "$PACKAGE_DIR/lib/" &&
cp LICENSE NOTICE "$PACKAGE_DIR/licenses/" &&
cp "$AORTA_CPP_SDK_DIR/LICENSE" "$AORTA_CPP_SDK_DIR/NOTICE" \
   "$AORTA_CPP_SDK_DIR/FLATBUFFERS-LICENSE" \
   "$AORTA_CPP_SDK_DIR/THIRD_PARTY_COMPONENTS.md" \
   "$AORTA_CPP_SDK_DIR/THIRD_PARTY_NOTICES.md" "$PACKAGE_DIR/licenses/aorta/" &&
(cd "$PACKAGE_DIR" && find bin lib licenses -type f -exec sha256sum {} + > SHA256SUMS)
```

Use this `PACKAGE_DIR` in the [SSH transfer step](../../packages/aorta/cpp/README.md#2-transfer-through-ssh).
The S100 device supplies its multimedia runtime in `/usr/hobot/lib`; do not replace
device system libraries with copies from the build machine. If the matching runtime
is absent, resolve the SDK/device compatibility before running.

### Run in the vbot device shell

Check [VPU permissions](../../docs/interfaces/cameras.md#hardware-decoding-on-s100)
and [configure the device shell](../../docs/getting-started/device-environment.md).
Use the actual `APP_DIR` printed during transfer:

```bash
APP_DIR=/userdata/vbot/apps/cpp-recipe-XXXXXX &&
cd "$APP_DIR" &&
sha256sum -c SHA256SUMS &&
export ZENOH_SESSION_CONFIG_URI=/opt/vita/aorta/edu/edu_session.json5 &&
export LD_LIBRARY_PATH="$PWD/lib:/usr/hobot/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}" &&
LDD_OUTPUT=$(ldd ./bin/camera-s100) &&
printf '%s\n' "$LDD_OUTPUT" &&
[[ "$LDD_OUTPUT" != *"not found"* ]] &&
./bin/camera-s100 --camera left --execute --consent --count 5 --timeout 15
```

`--count` is the number of **decoded output frames**, not received packets;
`--timeout` bounds the whole receive/decode loop. A successful run ends with
`complete: true`, the requested `decoded_frames`, and `decoder_released: true`.
Missing headers/keyframes, receive overflow, codec failures or deadline expiry are
errors, not a successful empty result. Live decoding requires both `--execute` and
`--consent`; the default only prints a plan. Ctrl-C requests cleanup and exit.

### Where to process the image

The source follows this sequence:

1. [main_s100.cc](main_s100.cc) validates the Aorta `CompressedVideo` sample and passes its Annex-B access unit to the decoder.
2. [h265_start.h](h265_start.h) waits for VPS/SPS/PPS and a random-access picture before starting mid-stream.
3. [s100_decoder.h](s100_decoder.h) initializes/configures/starts MediaCodec, borrows an input buffer, copies the compressed bytes and queues it once.
4. It checks for completed output before borrowing an NV12 frame. Process Y at `frame.vir_ptr[0]` and interleaved UV at `frame.vir_ptr[1]` in the `consume` callback, using `frame.stride` and `frame.vstride` respectively. Use returned dimensions, not assumed camera sizes.
5. The output is returned with `hb_mm_mc_queue_output_buffer` after the callback, including when the callback throws. Stop/release run on normal exit, timeout, exceptions and handled interruption.

The frame pointers are **borrowed**, not application-owned. Process synchronously
or copy the required rows before the callback returns; never retain those pointers
for another thread. NV12 is not RGB/BGR; color conversion is a separate step.
This finite live-stream example stops after the requested frames rather than saving
video, changing camera settings or synchronizing stereo frames.

## Completion, failures and exit

Output is JSON Lines. Exit 0 means the example finished (including an offline preview), 1 runtime failure/timeout, 2 invalid arguments, and 130 interruption. Check the execute flag and output semantics; a preview is not live success. Waits are bounded; receive-queue overflow is an error rather than silently claiming complete data. Subscribers, clients and Node are closed on exit.

Files are created exclusively, never overwritten. Limits are 8 MiB per sample and 16 MiB per capture. Failure/interruption may leave a partial file; inspect the error and retain or remove it according to privacy requirements.

For tests, see [Recipes](../README.md); default tests never connect to or operate a robot.
