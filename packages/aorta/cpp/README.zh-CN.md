# Aorta C++ SDK

<p align="center"><a href="README.md">English</a> | 中文</p>

使用 [edu-sdk-2026.9.24 版本](https://github.com/VitaDynamics/vbot-lab/releases/tag/edu-sdk-2026.9.24)：
C++ SDK `2026.9.23`、ABI `12`，配套 EDU Schema pack `2026.9.24-v4`。
示例使用 C++17、Bazel 7.6.1 与发布包中的生成头文件，不依赖 Python wheel，也无需本地生成 Schema。

## 准备发布制品

C++ 制品面向 **Ubuntu 22.04 Linux x86_64 或 aarch64**。SDK 必须匹配编译目标与运行架构，
并满足 glibc/libstdc++ 兼容性。以下使用原生编译：选择 aarch64 压缩包不会自动配置交叉编译。
ARM64 程序应在准备好的 ARM64 构建机或 ARM64 开发容器上构建，
不能将 x86_64 可执行文件部署到 ARM64 机器人。另见[兼容矩阵](../../../release/compatibility.zh-CN.md)。

将对应 SDK 压缩包、EDU Schema 压缩包及 `SHA256SUMS` 下载至
`artifacts/edu-sdk-2026.9.24/`。Linux x86_64 上从仓库根目录执行：

```bash
cd artifacts/edu-sdk-2026.9.24
sha256sum --ignore-missing -c SHA256SUMS
mkdir cpp-sdk-x86_64 edu-schema
tar --zstd -xf aorta-cpp-sdk-2026.9.23-abi12-ubuntu22.04-x86_64.tar.zst -C cpp-sdk-x86_64
tar --zstd -xf aorta-edu-schema-pack-2026.9.24-v4.tar.zst -C edu-schema
cd ../..
export AORTA_CPP_SDK_DIR="$PWD/artifacts/edu-sdk-2026.9.24/cpp-sdk-x86_64"
export AORTA_EDU_SCHEMA_DIR="$PWD/artifacts/edu-sdk-2026.9.24/edu-schema"
```

确认所选两个压缩包的校验均通过；校验命令会跳过未下载制品。使用新的解压目录；
如果目录已存在，应检查并复用已验证内容，而不是直接覆盖解压。
ARM64 环境中将压缩包和目录名的 `x86_64` 替换为 `aarch64`。
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
  //recipes/rcp-task:main_cpp
bazel run //recipes/camera:main_cpp
bazel run //recipes/locomotion:main_cpp -- --mode stand
bazel run //recipes/rcp-task:main_cpp
bazel test //tests:recipe_cpp_test //tests:recipe_cpp_sdk_test
```

C++ 目标标记为 `manual`，需要显式指定。普通 `//recipes/...` 构建与 `//tests/...`
测试仍可在没有 SDK 压缩包时使用，不会隐式下载 C++ 依赖。
与 Python 预览不同，**C++ 预览仍需先构建并链接发布版 SDK**，但不会创建 Node 或连接机器人。
测试覆盖参数与安全前提，以及真实生成类型的序列化，不建立设备会话。

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
pkg-config --modversion libavcodec libavutil libswscale
bazel build //recipes/camera:main_cpp_decode
bazel run //recipes/camera:main_cpp_decode -- --decode --consent
```

上面的命令仅为构建机预览；按下文部署可执行文件与 FFmpeg 运行库后，
使用相机示例中的直接运行二进制命令。
解码器等待可解码的关键帧数据，结束时排空延迟帧，输出 RGB 尺寸与行跨度。
`decoder.h` 中提供应用持有的 RGB 字节，示例不保存图片文件。
单张 RGB 图像上限为 32 MiB。

## 在机器人上运行

在准备好的 **ARM64 构建机或 ARM64 开发容器**中构建，再将可执行文件和依赖动态库
部署到设备。设备只运行已部署的程序，无需 Bazel、编译器、SDK 头文件或仓库副本。
x86_64 构建产物用于主机预览，不能部署到 ARM64；仅选择 ARM64 SDK 制品不会配置交叉编译器。

### 1. 在构建机上构建与打包

先按上文准备配套制品。在 ARM64 构建机的仓库根目录执行，以下以只读状态订阅示例为例。
部署其他示例时，将 RECIPE 改为对应的示例目录名。
逐步执行，任何一步失败都应停止。

```bash
# Build machine: repository root, matching ARM64 SDK/Schema already configured.
RECIPE=subscribe-state
bazel build "//recipes/$RECIPE:main_cpp"
PACKAGE_DIR=$(mktemp -d /tmp/vbot-cpp-app-XXXXXX)
mkdir -p "$PACKAGE_DIR/bin" "$PACKAGE_DIR/lib" "$PACKAGE_DIR/licenses/aorta"
cp -L "bazel-bin/recipes/$RECIPE/main_cpp" "$PACKAGE_DIR/bin/$RECIPE"
cp -L "$AORTA_CPP_SDK_DIR/lib/libaorta_core.so.12" "$PACKAGE_DIR/lib/"
cp LICENSE NOTICE "$PACKAGE_DIR/licenses/"
cp "$AORTA_CPP_SDK_DIR/LICENSE" "$AORTA_CPP_SDK_DIR/NOTICE" \
   "$AORTA_CPP_SDK_DIR/FLATBUFFERS-LICENSE" \
   "$AORTA_CPP_SDK_DIR/THIRD_PARTY_COMPONENTS.md" \
   "$AORTA_CPP_SDK_DIR/THIRD_PARTY_NOTICES.md" "$PACKAGE_DIR/licenses/aorta/"
file "$PACKAGE_DIR/bin/$RECIPE" "$PACKAGE_DIR/lib/libaorta_core.so.12"
LD_LIBRARY_PATH="$PACKAGE_DIR/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}" \
  ldd "$PACKAGE_DIR/bin/$RECIPE"
(cd "$PACKAGE_DIR" && find bin lib licenses -type f -exec sha256sum {} + > SHA256SUMS)
```

确认两个文件均为 AArch64，且没有动态库显示 `not found`。
C++ 封装库静态链接，但 Aorta core 是动态库，因此只复制可执行文件不够。
保留软件包的许可证与第三方声明。设备需提供兼容的 glibc/libstdc++；
不要复制构建机的 glibc，也不要覆盖设备系统库。

相机解码需构建 `//recipes/camera:main_cpp_decode`，将
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
ROBOT=vbot@192.168.126.2
ssh -o BatchMode=yes "$ROBOT" 'id -un; uname -m'
APP_DIR=$(ssh -o BatchMode=yes "$ROBOT" \
  'mkdir -p /userdata/vbot/apps && mktemp -d /userdata/vbot/apps/cpp-recipe-XXXXXX')
printf 'Device application directory: %s\n' "$APP_DIR"
scp -r "$PACKAGE_DIR/bin" "$PACKAGE_DIR/lib" "$PACKAGE_DIR/licenses" \
  "$PACKAGE_DIR/SHA256SUMS" "$ROBOT:$APP_DIR/"
ssh "$ROBOT"
```

记录输出的 APP_DIR。构建机的 shell 变量不会自动传入 SSH 会话；
下一段命令需填入刚才输出的实际路径。目录创建或传输失败时不要继续。

### 3. 在设备 shell 中直接运行

SSH 登录后先[配置设备 shell](../../../docs/getting-started/device-environment.zh-CN.md)。
进入上传所得应用目录，运行前检查文件校验和与动态库。
若校验失败、出现 `not found` 或 GLIBC/GLIBCXX 版本缺失，应停止；
修正 ARM64 软件包或构建兼容性后重新传输，不要替换设备系统库。

```bash
# Device shell: replace this value with the APP_DIR printed during transfer.
APP_DIR=/userdata/vbot/apps/cpp-recipe-XXXXXX
cd "$APP_DIR"
sha256sum -c SHA256SUMS
export PATH="/opt/vita/aorta/bin:$PATH"
export ZENOH_SESSION_CONFIG_URI=/opt/vita/aorta/edu/edu_session.json5
export LD_LIBRARY_PATH="$PWD/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
ldd ./bin/subscribe-state
./bin/subscribe-state
./bin/subscribe-state --execute --count 3 --timeout 10
```

第一次调用仅输出离线预览；第二次接收三条状态消息后退出。
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
