# Aorta C++ SDK

<p align="center"><a href="README.md">English</a> | 中文</p>

所有 SDK 构建检查、Bazel 构建／测试、Recipe 预览和打包都在配套开发容器内执行，CI 同样遵守；
参阅[执行位置](../../../docs/development/README.zh-CN.md)。下文“构建机”均指该容器，不是裸宿主机或机器人，需核对目标架构。

每个 Bash 命令块应作为一条命令链执行。`&&` 会在失败后跳过本段后续命令，
并保留下一步所需的 shell 变量。处理错误后，再执行下一个命令块。

使用 [edu-sdk-2026.10.14 版本](https://github.com/VitaDynamics/vbot-lab/releases/tag/edu-sdk-2026.10.14)：
C++ SDK `2026.10.12`、ABI `13`，配套 EDU Schema pack `2026.10.13-v4`。
示例使用 C++17、Bazel 7.6.1 与发布包中的生成头文件，不依赖 Python wheel，也无需本地生成 Schema。

## 准备发布制品

C++ 制品面向 **Ubuntu 22.04 Linux x86_64 或 aarch64**。SDK 必须匹配编译目标与运行架构，
并满足 glibc/libstdc++ 兼容性。开发镜像运行于 AMD64，已包含 ARM64 GCC／G++ 11 交叉编译器。
默认 Bazel 使用原生构建，用于容器内预览／测试；`bazel build --config=arm64` 选择仓库中的 ARM64
目标与交叉工具链，生成设备程序。每种构建需选择配套 SDK，不得将 x86_64 可执行文件部署到 ARM64 机器人。
另见[兼容矩阵](../../../docs/compatibility.zh-CN.md)。

在[开发容器](../../../docker/README.zh-CN.md)内，选择压缩包前先检查原生构建目标：

```bash
uname -m
g++ -dumpmachine
aarch64-linux-gnu-g++ -dumpmachine
bazel --version
```

部署到机器人时，所选编译器必须以 ARM64 为目标，并配套对应 SDK／运行库；
容器本身不必运行于 ARM64。使用 Bazel 7.6.1。上面的原生 `g++` 目标与容器架构一致，
镜像提供的 `aarch64-linux-gnu-g++` 则以 ARM64 为目标，区分方法见[容器编译器检查](../../../docker/README.zh-CN.md)。
原生预览／测试使用默认编译器，设备构建使用 `--config=arm64`。
该配置选择 `//toolchains:linux_arm64` 及镜像中的 GCC 11 工具和目标头文件，不下载编译器或 SDK。
不在 AMD64 容器内执行 ARM64 程序／测试，无需另建容器或在机器人上编译。

将对应 SDK 压缩包、EDU Schema 压缩包及 `SHA256SUMS` 下载至
`artifacts/edu-sdk-2026.10.14/`。Linux x86_64 上从仓库根目录执行：

```bash
cd artifacts/edu-sdk-2026.10.14 &&
sha256sum --ignore-missing -c SHA256SUMS &&
mkdir cpp-sdk-x86_64 edu-schema &&
tar --zstd -xf aorta-cpp-sdk-2026.10.12-abi13-ubuntu22.04-x86_64.tar.zst -C cpp-sdk-x86_64 &&
tar --zstd -xf aorta-edu-schema-pack-2026.10.13-v4.tar.zst -C edu-schema &&
cd ../.. &&
export AORTA_CPP_SDK_DIR="$PWD/artifacts/edu-sdk-2026.10.14/cpp-sdk-x86_64" &&
export AORTA_EDU_SCHEMA_DIR="$PWD/artifacts/edu-sdk-2026.10.14/edu-schema"
```

确认所选两个压缩包的校验均通过；校验命令会跳过未下载制品。使用新的解压目录；
如果目录已存在，应检查并复用已验证内容，而不是直接覆盖解压。
此处 x86_64 SDK 用于原生预览；设备构建前按下文准备 ARM64 SDK。
确保有 `g++`、`zstd` 和 Bazel。不要把生成头文件或二进制库加入 Git。

本地 Bazel repository 读取上述两个绝对路径，不下载 SDK，也不配置编译器。
也可通过 Bazel 参数 `--repo_env=AORTA_CPP_SDK_DIR=...` 和
`--repo_env=AORTA_EDU_SCHEMA_DIR=...` 指定路径。
保留发布包自带的 FlatBuffers 头文件：C++ 生成代码要求精确版本，
本配套为 `25.9.23`；Python 包的版本不能代替 C++ 头文件版本。

## 构建与预览

完整构建环境可按 [离线构建入口](../../../docs/development/offline-build.zh-CN.md)
使用配套 Bazel 依赖包；SDK 压缩包本身不包含 Bazel 构建规则。

每个 Recipe 保留 Python `:main`，新增 C++ `:main_cpp`：

```bash
bazel build \
  //recipes/device-info:main_cpp \
  //recipes/subscribe-state:main_cpp \
  //recipes/service-call:main_cpp \
  //recipes/camera:main_cpp \
  //recipes/audio:main_cpp \
  //recipes/locomotion:main_cpp \
  //recipes/rcp-task:main_cpp &&
bazel run //recipes/camera:main_cpp &&
bazel run //recipes/locomotion:main_cpp -- --mode stand &&
bazel run //recipes/rcp-task:main_cpp &&
bazel test //tests:recipe_cpp_test //tests:recipe_cpp_sdk_test
```

C++ 目标标记为 `manual`，需要显式指定。普通 `//recipes/...` 构建与 `//tests/...`
测试仍可在没有 SDK 压缩包时使用，不会隐式下载 C++ 依赖。
与 Python 预览不同，**C++ 预览仍需先构建并链接发布版 SDK**，但不会创建 Node 或连接机器人。
测试覆盖参数与安全前提，以及真实生成类型的序列化，不建立设备会话。

需要组合多路数据的完整应用时，参阅 [C++ 只读健康监测](../../../blueprints/health-monitor/cpp/README.zh-CN.md)，
其中包含共用配置、离线状态测试、ARM64 打包和设备运行流程。

共享辅助代码处理参数、有界队列和文件，不替代 Aorta API。示例直接使用
`Node::Create`、`CreateSubscriber`、`CreateClientTyped` 和 `CreateActionClient`。
访问值之前检查 `StatusOr`。类型化 service 客户端自动填充 header，并使用 `*_msg.h`
中的配套 Schema 元数据。消息回调收到的是借用视图，延后处理前需通过
`MessageView::ToVector()` 复制数据。使用访问器前验证 FlatBuffer，并保持底层字节或响应对象存活。

RCP 使用 `execute_task_msg.h` 的 `ExecuteTaskAction` 和生成的 `*Msg`／variant 类型，
不是 Python 的 `*T` 对象 API。这里生成的 C++ DAG 辅助类型位于
`aorta::action::rcp`，线上的枚举类型仍位于 `aorta::services::rcp`。
见 [goal 构建实现](../../../recipes/rcp-task/goal.h)。

## 可选相机解码

FFmpeg 以独立目录提供、而非安装到系统时，在构建前将 `VBOT_FFMPEG_DIR`
设为该目录的绝对路径。支持的目录布局为 FFmpeg 4.4 头文件位于 `include/`，
`libavcodec.so.58`、`libavutil.so.56`、`libswscale.so.5` 位于 `lib/`，
并保留软链接指向的实际库文件。Bazel 会显式引入这些文件；部署时将该 `lib/`
加入设备进程的 `LD_LIBRARY_PATH`。参见 [离线指南](../../../docs/development/offline-build.zh-CN.md)。
不设置该变量时，使用已安装的系统开发库。

基础相机目标读取 H.265 元数据，并可保存压缩字节。C++ RGB 解码使用单独的
`:main_cpp_decode` 目标。构建环境需具备 `libavcodec`、`libavutil` 和
`libswscale` 的开发头文件与库（Ubuntu 包名为 `libavcodec-dev`、
`libavutil-dev`、`libswscale-dev`）。这些是系统依赖，Bazel 不负责安装；
应在开发镜像中提供，运行环境也需要匹配的 FFmpeg 动态库及软件 HEVC 解码器。

```bash
pkg-config --modversion libavcodec libavutil libswscale &&
bazel build //recipes/camera:main_cpp_decode &&
bazel run //recipes/camera:main_cpp_decode -- --decode --consent
```

上面的命令仅为构建机预览；按下文部署可执行文件与 FFmpeg 运行库后，
使用相机示例中的直接运行二进制命令。
解码器等待可解码的关键帧数据，结束时排空延迟帧，输出 RGB 尺寸与行跨度。
`decoder.h` 中提供应用持有的 RGB 字节，示例不保存图片文件。
单张 RGB 图像上限为 32 MiB。

## 构建 ARM64 程序

复用上文已准备的 Schema 目录。在同一开发容器内，将 ARM64 SDK 解压到独立的新目录，
并为设备构建选择它：

```bash
cd artifacts/edu-sdk-2026.10.14 &&
sha256sum --ignore-missing -c SHA256SUMS &&
mkdir cpp-sdk-aarch64 &&
tar --zstd -xf aorta-cpp-sdk-2026.10.12-abi13-ubuntu22.04-aarch64.tar.zst -C cpp-sdk-aarch64 &&
cd ../.. &&
export AORTA_CPP_SDK_DIR="$PWD/artifacts/edu-sdk-2026.10.14/cpp-sdk-aarch64" &&
export AORTA_EDU_SCHEMA_DIR="$PWD/artifacts/edu-sdk-2026.10.14/edu-schema" &&
bazel build --config=arm64 //recipes/subscribe-state:main_cpp &&
file bazel-bin/recipes/subscribe-state/main_cpp &&
aarch64-linux-gnu-readelf -d bazel-bin/recipes/subscribe-state/main_cpp
```

可执行文件应显示 AArch64；`NEEDED` 包含 ARM64 Aorta core 及目标系统库。
替换 Recipe 名称即可构建其他 `:main_cpp`，同一配置适用于全部十一个基础 C++ Recipes。
在 AMD64 容器中仅 `build` 这些目标程序，不 `run` 或 `test`；恢复原生预览／测试时，
将 SDK 路径切回 x86_64，并省略 `--config=arm64`。

默认 `fastbuild` 模式使用 `-O0`；添加 `-c opt` 使用 `-O2 -DNDEBUG`，添加 `-c dbg`
使用 `-O0 -g`，例如 `bazel build --config=arm64 -c opt //recipes/subscribe-state:main_cpp`。
这些模式不改变所选 SDK 或目标架构。

断网构建使用离线入口的 `--target-platform arm64`，而不是 `--config=arm64`，
见[离线构建](../../../docs/development/offline-build.zh-CN.md)。
可选相机解码还需通过 `VBOT_FFMPEG_DIR` 提供 ARM64 FFmpeg 头文件／库，不能链接 host FFmpeg 库。

## 在机器人上运行

在开发容器内生成 **ARM64 可执行文件**，再将它和依赖动态库
部署到设备。设备只运行已部署的程序，无需 Bazel、编译器、SDK 头文件或仓库副本。
x86_64 可执行文件用于主机预览，不能部署到 ARM64。AMD64 容器可以通过交叉编译器及配套 Bazel
配置生成 ARM64 程序；本仓库设备构建需同时选择 ARM64 SDK 和 `--config=arm64`。

### 1. 在构建机上构建与打包

按上文准备 ARM64 SDK 与共用 Schema。在开发容器的仓库根目录构建与打包，
以下以只读状态订阅示例为例。
部署其他示例时，将 RECIPE 改为对应的示例目录名。
逐步执行，任何一步失败都应停止。

```bash
# Build machine: repository root, matching ARM64 SDK/Schema already configured.
RECIPE=subscribe-state &&
bazel build --config=arm64 "//recipes/$RECIPE:main_cpp" &&
PACKAGE_DIR=$(mktemp -d /tmp/vbot-cpp-app-XXXXXX) &&
test -n "$PACKAGE_DIR" &&
mkdir -p "$PACKAGE_DIR/bin" "$PACKAGE_DIR/lib" "$PACKAGE_DIR/licenses/aorta" &&
cp -L "bazel-bin/recipes/$RECIPE/main_cpp" "$PACKAGE_DIR/bin/$RECIPE" &&
cp -L "$AORTA_CPP_SDK_DIR/lib/libaorta_core.so.13" "$PACKAGE_DIR/lib/" &&
cp LICENSE NOTICE "$PACKAGE_DIR/licenses/" &&
cp "$AORTA_CPP_SDK_DIR/LICENSE" "$AORTA_CPP_SDK_DIR/NOTICE" \
   "$AORTA_CPP_SDK_DIR/FLATBUFFERS-LICENSE" \
   "$AORTA_CPP_SDK_DIR/THIRD_PARTY_COMPONENTS.md" \
   "$AORTA_CPP_SDK_DIR/THIRD_PARTY_NOTICES.md" "$PACKAGE_DIR/licenses/aorta/" &&
file "$PACKAGE_DIR/bin/$RECIPE" "$PACKAGE_DIR/lib/libaorta_core.so.13" &&
aarch64-linux-gnu-readelf -d "$PACKAGE_DIR/bin/$RECIPE" &&
aarch64-linux-gnu-readelf -d "$PACKAGE_DIR/lib/libaorta_core.so.13" &&
(cd "$PACKAGE_DIR" && find bin lib licenses -type f -exec sha256sum {} + > SHA256SUMS)
```

检查两个文件均显示 AArch64，并查看各自的 `NEEDED` 项。
不要在此 AMD64 容器内使用 host `ldd` 或执行目标程序；实际动态库解析在下文登录设备后使用 `ldd` 检查。
C++ 封装库静态链接，但 Aorta core 是动态库，因此只复制可执行文件不够。
保留软件包的许可证与第三方声明。设备需提供兼容的 glibc/libstdc++；
不要复制构建机的 glibc，也不要覆盖设备系统库。

相机解码需提供 ARM64 FFmpeg 输入，以 `--config=arm64` 构建 `//recipes/camera:main_cpp_decode`，将
`bazel-bin/recipes/camera/main_cpp_decode` 复制为 `bin/camera-decode`，
并将匹配的 ARM64 FFmpeg 运行库放入 `lib/`。支持的制品包含
`libavcodec.so.58`、`libavutil.so.56` 和 `libswscale.so.5`；
以这些名称复制库的实际内容（例如使用 `cp -L`），不要只复制失效的软链接。
还需检查这些库的间接依赖；不同 FFmpeg 构建不能保证只需上述三个库。
同时保留 FFmpeg／第三方许可证声明，补充文件后重新生成 SHA256SUMS。

### 2. 通过 SSH 传输

先配置 [SSH 免密登录](../../../docs/robots/quadruped-common/connection.zh-CN.md)。
将 ROBOT 替换为已确认的设备地址或 SSH 别名；无法连接时，先连接设备或确认地址再继续。
身份检查应输出 `vbot` 和 `aarch64`。本次部署创建新的应用目录，不覆盖已有应用。

```bash
# Build/transfer machine: keep PACKAGE_DIR from the previous step.
ROBOT=vbot@192.168.126.2 &&
ssh -o BatchMode=yes "$ROBOT" \
  'test "$(id -un)" = vbot && test "$(uname -m)" = aarch64 && id -un && uname -m' &&
APP_DIR=$(ssh -o BatchMode=yes "$ROBOT" \
  'mkdir -p /userdata/vbot/apps && mktemp -d /userdata/vbot/apps/cpp-recipe-XXXXXX') &&
test -n "$APP_DIR" &&
printf 'Device application directory: %s\n' "$APP_DIR" &&
scp -r "$PACKAGE_DIR/bin" "$PACKAGE_DIR/lib" "$PACKAGE_DIR/licenses" \
  "$PACKAGE_DIR/SHA256SUMS" "$ROBOT:$APP_DIR/" &&
ssh "$ROBOT"
```

第一条 SSH 命令会要求账户为 `vbot`、架构为 `aarch64`，通过后才创建目录或传输；此 C++ 部署不要求 Python。
记录输出的 APP_DIR。构建机的 shell 变量不会自动传入 SSH 会话；
下一段命令需填入刚才输出的实际路径。目录创建或传输失败时不要继续。

### 3. 在设备 shell 中直接运行

SSH 登录后先[配置设备 shell](../../../docs/getting-started/device-environment.zh-CN.md)。
进入上传所得应用目录，运行前检查文件校验和与动态库。
若校验失败、出现 `not found` 或 GLIBC/GLIBCXX 版本缺失，应停止；
修正 ARM64 软件包或构建兼容性后重新传输，不要替换设备系统库。

```bash
# Device shell: replace this value with the APP_DIR printed during transfer.
APP_DIR=/userdata/vbot/apps/cpp-recipe-XXXXXX &&
cd "$APP_DIR" &&
sha256sum -c SHA256SUMS &&
export PATH="/opt/vita/aorta/bin:$PATH" &&
export ZENOH_SESSION_CONFIG_URI=/opt/vita/aorta/edu/edu_session.json5 &&
export LD_LIBRARY_PATH="$PWD/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}" &&
LDD_OUTPUT=$(ldd ./bin/subscribe-state) &&
printf '%s\n' "$LDD_OUTPUT" &&
[[ "$LDD_OUTPUT" != *"not found"* ]] &&
./bin/subscribe-state --execute --count 3 --timeout 10
```

部署前先在开发容器内完成离线预览；设备上的调用接收三条状态消息后退出。
其他示例使用其部署后的 `./bin/<recipe>` 名称与文档参数；解码程序使用
`./bin/camera-decode` 和[相机示例参数](../../../recipes/camera/README.zh-CN.md)。
每次新建 shell 都需进入应用目录并设置 LD_LIBRARY_PATH。
在线示例要求设备 `vbot` 账户与指定的 session URI；
添加 `--execute` 前确认路由可用，并满足对应示例的授权与安全前提。
构建或预览成功不代表在线接口可用。

## 操作边界

所有程序默认输出 JSON 预览。在线读取要求 `--execute`，语音访问要求 `--consent`，
运动要求 `--confirm-motion`，图像保存／解码要求 `--consent`。
日志为 JSON Lines，错误写 stderr。退出码：0 完成／预览、1 运行错误／超时、
2 参数错误、130 中断。SIGINT/SIGTERM 请求正常退出，阻塞 RPC 可能需等配置的超时返回；
SIGKILL 无法执行清理。

RAII 在 Node 之前释放订阅与客户端。运动受理不等于完成，需关联 BODY 终态报告中的请求 ID；
超时不会取消机器人动作。RCP 仅演示两个 Sleep 节点，限时等待结果，
受理后中断或失败会尝试取消。取消失败仍需检查终态；
受理超时且没有 handle 时，结果未知，应使用日志中的 goal/task ID 检查，不要自动重交，
也不输出 goal secret。各任务的字段语义和命令见 [Recipes](../../../recipes/README.zh-CN.md)。
