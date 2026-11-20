# 读取相机图像

<p align="center"><a href="README.md">English</a> | 中文</p>

[Recipes 索引](../README.zh-CN.md) · [Python](main.py) · [C++](main.cc) · [S100 硬件解码](main_s100.cc)

接口: `/image_left_raw/h265`, `/image_right_raw/h265` — pub/sub.

生成类型: `foxglove.CompressedVideo`.

选择单路相机，输出编码、frame ID、采集时间戳和载荷长度。载荷是 H.265 Annex B 视频流，不是 JPEG 或 RGB。默认仅读取元数据；获得许可后，可保存压缩字节到新文件，或用 `--decode` 获取内存中的 RGB 图像。每路相机独立使用解码器；解码依赖关键帧与 VPS/SPS/PPS，中途订阅可能暂时没有可解码图像。

S100 硬件解码优先使用[地瓜原生 SDK](../../docs/interfaces/cameras.zh-CN.md#s100-硬件解码)，
并按其中说明检查 `vbot` 账户的 `/dev/vpu` 权限。下文独立的
[S100 C++ 目标](#c-s100-硬件解码)使用该后端；原有 PyAV／FFmpeg 目标保留，
其 `--decode` 参数不会选择 VPU。

## Python：构建与离线预览

```bash
bazel build //recipes/camera:main
bazel run //recipes/camera:main
```

默认只输出 JSON 请求计划，不安装 SDK、不连接设备、不发送请求。

## Python：在设备上运行

先完成 [Python 部署流程](../../docs/development/python-deployment.zh-CN.md)：传输本示例及配套 wheel，并在设备创建 venv。保持位于部署所得的应用目录（APP_DIR），激活该目录的 venv、配置设备环境后运行：

```bash
python -m recipes.camera.main --camera left --execute --count 60 --timeout 10
```

可选图像解码：按 [离线指南](../../docs/development/offline-build.zh-CN.md)，将匹配架构的
wheel 放入 `artifacts/wheelhouse`，再安装到执行机器的 venv。二进制保存同样需要 NumPy
批量提取载荷：

```bash
python -m pip install --no-index --find-links artifacts/wheelhouse av==16.1.0 numpy==2.2.6
python -m recipes.camera.main --camera left --execute --count 120 --timeout 20 --decode --consent
python -m recipes.camera.main --camera left --execute --count 120 --timeout 20 --output left.h265 --consent
```

解码器调用 `frame.to_rgb()`；通过 `bytes(rgb.planes[0])` 访问像素，并按 `plane.line_size` 处理行填充。输出解码后的宽、高、像素格式和行跨度。在上限内没有解码出图像会报错，不算成功。保存的流开头可能早于可用关键帧。本示例不实现双目同步，也不导出图片文件。人体检测优先使用内置[感知输出](../../docs/interfaces/perception.zh-CN.md)，无需先解码并部署新模型。

## C++

先按 [C++ SDK 指南](../../packages/aorta/cpp/README.zh-CN.md)准备配套 SDK／Schema 压缩包与编译环境，设置两个发布制品路径。在构建机上显式构建 C++ 目标，预览也需要链接 SDK，但不会创建 Node 或访问设备：

```bash
bazel build //recipes/camera:main_cpp
bazel run //recipes/camera:main_cpp
```

按[二进制部署流程](../../packages/aorta/cpp/README.zh-CN.md#在机器人上运行)设置 RECIPE=camera 并完成部署。以 vbot 身份 SSH 登录后，进入部署所得应用目录，按流程配置 shell 和动态库路径，满足上面的任务前提后直接运行可执行文件：

```bash
./bin/camera --camera left --execute --count 60 --timeout 10
```

设备无需 Bazel、编译器或仓库副本。C++ 使用与 Python 相同的路由、操作许可和完成条件；只读订阅不会发布指令。

基础 `:main_cpp` 只依赖 Aorta SDK，可通过 `--output left.h265 --consent` 保存压缩字节，
不会把 H.265 当作 RGB。C++ 解码使用 [FFmpeg 构建前提](../../packages/aorta/cpp/README.zh-CN.md)中的可选目标，
在构建机生成 `:main_cpp_decode`，将其以 `bin/camera-decode` 名称连同 FFmpeg 运行库部署后，在已配置的设备上执行：

```bash
./bin/camera-decode --camera left --decode --consent --execute --count 120 --timeout 20
```

[decoder.h](decoder.h) 中的 `rgb` 是连续 RGB24 字节，行跨度为宽度乘 3；
使用或移交该缓冲区后再离开当前帧作用域。每路相机独立解码，结束时排空延迟帧，
未解码出图像时报错；本例不保存图片或进行双目同步。

## C++ S100 硬件解码

该目标订阅相同的左／右 H.265 topic，通过 S100 MediaCodec 接口解码，
不依赖 FFmpeg，也不会回退到软件解码。程序仅输出 NV12 图像尺寸、Y／UV 行跨度、
时间戳与帧计数，不保存或外传像素。通过 `--camera left` 或 `--camera right`
选择一路相机，每路独立使用解码器。

### 在开发容器内构建

按 [C++ SDK 指南](../../packages/aorta/cpp/README.zh-CN.md#构建-arm64-程序)
准备 **ARM64** Aorta SDK 与 EDU Schema。
另按[地瓜官方 SDK 文档](https://developer.d-robotics.cc/rdk_s_doc/Advanced_development/multimedia_development/S100/codec)
获取配套 S100 多媒体 SDK，将 `VBOT_S100_MULTIMEDIA_DIR` 设为容器内可见的绝对路径，
目录结构如下，并保留所有软链接指向的实际文件：

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

使用完整、配套的 SDK 头文件与 ARM64 库。该可选目标只读取本地提供的 SDK，
Bazel 不会下载它，其他 Recipe 目标无需此依赖。
设置好 `AORTA_CPP_SDK_DIR` 与 `AORTA_EDU_SCHEMA_DIR` 后执行：

```bash
export VBOT_S100_MULTIMEDIA_DIR=/absolute/path/to/s100-multimedia-sdk &&
bazel build --config=arm64 //recipes/camera:main_cpp_s100_decode &&
file bazel-bin/recipes/camera/main_cpp_s100_decode &&
aarch64-linux-gnu-readelf -d bazel-bin/recipes/camera/main_cpp_s100_decode
```

输出必须为 AArch64。在 AMD64 容器中对此仅支持 ARM64 的目标执行构建，
不要 `bazel run`。将可执行文件、配套 Aorta 运行库与声明文件打包：

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

将此 `PACKAGE_DIR` 用于 [SSH 传输步骤](../../packages/aorta/cpp/README.zh-CN.md#2-通过-ssh-传输)。
S100 设备在 `/usr/hobot/lib` 提供多媒体运行库，不要用构建机上的副本替换设备系统库。
若缺少配套运行库，应先解决 SDK 与设备的兼容问题再运行。

### 在设备 vbot shell 中运行

检查 [VPU 权限](../../docs/interfaces/cameras.zh-CN.md#s100-硬件解码)，
并[配置设备 shell](../../docs/getting-started/device-environment.zh-CN.md)。
使用传输时输出的实际 `APP_DIR`：

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

`--count` 指**解码输出帧数**，不是收到的数据包数；`--timeout` 限制整个接收／解码循环。
成功结束时输出 `complete: true`、达到请求数量的 `decoded_frames` 及
`decoder_released: true`。缺少参数集／关键帧、接收溢出、编解码器失败或超时都会报错，
不会将空结果视为成功。实时解码必须同时指定 `--execute` 与 `--consent`，
默认只输出计划。Ctrl-C 会请求清理并退出。

### 在哪里处理图像

源码按以下流程展开：

1. [main_s100.cc](main_s100.cc)校验 Aorta `CompressedVideo` 消息，将 Annex-B 访问单元传给解码器。
2. [h265_start.h](h265_start.h)等待 VPS／SPS／PPS 与随机访问帧，支持中途加入码流。
3. [s100_decoder.h](s100_decoder.h)完成 MediaCodec 的初始化、配置、启动，借入输入缓冲区，复制压缩字节并只提交一次。
4. 确认可用输出后借出 NV12 图像。在 `consume` 回调中通过 `frame.vir_ptr[0]` 处理 Y、`frame.vir_ptr[1]` 处理交错 UV，分别使用 `frame.stride` 与 `frame.vstride`。尺寸以返回值为准，不写死相机尺寸。
5. 回调结束后通过 `hb_mm_mc_queue_output_buffer` 归还输出，回调抛异常时也会归还；正常退出、超时、异常及已处理的中断均停止并释放解码器。

图像指针是**借用数据**，不属于应用。应同步处理，或在回调返回前复制所需的各行，
不要将这些指针保留给其他线程。NV12 不是 RGB／BGR，颜色转换需要另行处理。
该实时流示例在取得指定帧数后停止，不保存视频、不修改相机配置，也不进行双目同步。

## 完成、失败与退出

输出为逐行 JSON；退出码 0 表示完成本示例的操作（离线预览也返回 0），1 表示运行失败或超时，2 表示参数不合法，130 表示中断。检查 execute 参数和输出语义，不要把离线预览视为在线成功。所有等待都有上限；订阅队列溢出会报错，不把丢失样本当完整数据。退出时关闭订阅、客户端及 Node。

文件只会新建，不覆盖已有路径；每个样本最多 8 MiB，总捕获最多 16 MiB。失败或中断可能保留部分文件，需按错误输出判断，并按隐私要求手动保留或删除。

测试说明见 [Recipes](../README.zh-CN.md)；默认测试不连接或操作设备。
