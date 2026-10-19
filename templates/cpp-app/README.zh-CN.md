# C++ 应用工作区

<p align="center"><a href="README.md">English</a> | 中文</p>

这是以只读健康监测为起点的独立 C++17／Bazel 工作区。
只订阅 /locomotion/status、/bms_state 与 /system/sm_status，
不发布控制指令、不调用 service／action，也不采集音视频。
配套 foot_quadruped 应用 V1.6.0-12、C++ SDK 2026.10.12／ABI 13，
以及 SDK Release edu-sdk-2026.10.14 中的 Schema pack 2026.10.13-v4。

## 项目内容

health_monitor/model.h 管理不依赖 SDK 的业务状态，decoder.h 验证并解码 FlatBuffers，
main.cc 管理订阅、有界队列及 JSON Lines 输出。
support/ 包含复制的共用辅助代码，sdk/ 提供本地制品接入规则，
toolchains/ 包含配套 ARM64 交叉编译配置。源码和 Bazel 标签不再引用 VBOT Lab 仓库路径。
APP.json 记录语言、SDK 配套、构建目标和运行配置清单，是项目元数据，
不是设备 API，也不是 Python 部署清单。

构建、测试、预览、模拟及打包均在已有 VBOT 开发容器内完成。
镜像运行于 AMD64，并提供 ARM64 GCC／G++ 11；机器人只运行已部署的产物，
不需要仓库、Bazel、Python 运行时或联网下载依赖。

## 构建与测试——开发容器

在此应用根目录可独立运行不依赖 SDK 的状态测试：

```bash
bazel test //:model_test
```

按 [C++ SDK 指南](https://github.com/VitaDynamics/vbot-lab/blob/main/packages/aorta/cpp/README.zh-CN.md)
准备已校验的原生与 ARM64 SDK 制品及共用 Schema。
将 SDK_ARTIFACTS 替换为它们的实际父目录，不必放在参考仓库中。
首次 Bazel 构建可能需要联网获取公共构建规则；应用的接入规则不下载 SDK 或编译器。

```bash
SDK_ARTIFACTS=/workspace/sdk/edu-sdk-2026.10.14 &&
export AORTA_CPP_SDK_DIR="$SDK_ARTIFACTS/cpp-sdk-x86_64" &&
export AORTA_EDU_SCHEMA_DIR="$SDK_ARTIFACTS/edu-schema" &&
bazel build //:main &&
bazel test //:model_test //:sdk_test //:cli_test &&
bazel run //:main -- --config config.json &&
bazel run //:main -- --config config.json --simulate
```

原生 CLI 测试使用容器中的 Python 启动 C++ 程序，不需要 Python SDK wheel。
测试与预览不创建 Node。默认输出 execute=false；模拟输出合成数据的 receiving／stale 状态。

## 配置应用

打包前修改 config.json，或运行时通过 --config FILE 选择配置。
只支持 stale_after_seconds，范围 (0, 120]，与 low_battery_percent，范围 [0, 100]，
值须为有限 JSON 数字，配置文件最大 4096 字节。
--duration 范围 (0, 120] 秒，默认 10 秒。--simulate 与 --execute 不能同时使用。
省略 --config 时读取工作目录中的 config.json。
应用名称不会重命名 health_monitor 源码目录。

数据新鲜度使用回调中记录并随消息入队的本地单调时间，不是出队／解码时间；
延后处理不会刷新旧样本。源时间戳只用于单路排序，
为零时不排序，重置后需重新启动监测程序。
JSON Lines 输出 waiting_data、receiving 或 stale、计数器、解码值及 low_battery 提示。
无输入不代表接口不支持或硬件故障。
退出码 0 表示结束时三路数据均新鲜，1 表示输入／配置／运行问题，
2 表示参数错误，130 表示中断；退出时先释放订阅，再关闭 Node。

## 交叉构建与打包——开发容器

保留上一段的 SDK_ARTIFACTS 和 AORTA_EDU_SCHEMA_DIR。
先切换 ARM64 SDK 再交叉构建，不在 AMD64 容器内运行或测试 ARM64 二进制。

```bash
export AORTA_CPP_SDK_DIR="$SDK_ARTIFACTS/cpp-sdk-aarch64" &&
bazel build --config=arm64 //:main &&
PACKAGE_DIR=$(mktemp -d /tmp/vbot-cpp-app-XXXXXX) &&
test -n "$PACKAGE_DIR" &&
mkdir -p "$PACKAGE_DIR/bin" "$PACKAGE_DIR/lib" "$PACKAGE_DIR/licenses/aorta" &&
cp -L bazel-bin/main "$PACKAGE_DIR/bin/health-monitor" &&
cp -L "$AORTA_CPP_SDK_DIR/lib/libaorta_core.so.13" "$PACKAGE_DIR/lib/" &&
cp config.json APP.json "$PACKAGE_DIR/" &&
cp LICENSE NOTICE "$PACKAGE_DIR/licenses/" &&
cp "$AORTA_CPP_SDK_DIR/LICENSE" "$AORTA_CPP_SDK_DIR/NOTICE" \
  "$AORTA_CPP_SDK_DIR/FLATBUFFERS-LICENSE" \
  "$AORTA_CPP_SDK_DIR/THIRD_PARTY_COMPONENTS.md" \
  "$AORTA_CPP_SDK_DIR/THIRD_PARTY_NOTICES.md" "$PACKAGE_DIR/licenses/aorta/" &&
file "$PACKAGE_DIR/bin/health-monitor" "$PACKAGE_DIR/lib/libaorta_core.so.13" &&
aarch64-linux-gnu-readelf -d "$PACKAGE_DIR/bin/health-monitor" &&
(cd "$PACKAGE_DIR" && find bin lib licenses config.json APP.json -type f -exec sha256sum {} + > SHA256SUMS) &&
printf 'Package directory: %s\n' "$PACKAGE_DIR"
```

两份 ELF 均应显示 AArch64。按 SDK 指南检查递归依赖，使用设备兼容的系统库，
不能以宿主机 glibc 替换设备系统库。
包中仅有可执行文件、Aorta 动态运行库、配置、元数据及许可证。
新增运行库／资源时须同步构建和显式打包清单；命令不会自动发现任意应用依赖。
仅面向 Python 的 package_app.py 不用于 C++ 项目。
完整保留部署包及输出路径，修改配置后重新打包；校验和不等于数字签名。
恢复原生测试时，需将 SDK 路径切回原生版本。

## 传输——可 SSH 访问设备的机器

复用已可用的免密 SSH，将 ROBOT 替换为选定的有线／Wi-Fi 地址或 SSH 别名。
无法连接时先完成设备连接或更正地址，不继续部署。
PACKAGE_DIR 必须指向此机器上的完整包。

```bash
ROBOT=vbot@192.168.126.2 &&
ssh -o BatchMode=yes "$ROBOT" \
  'test "$(id -un)" = vbot && test "$(uname -m)" = aarch64 && id -un && uname -m' &&
APP_DIR=$(ssh -o BatchMode=yes "$ROBOT" \
  'mkdir -p /userdata/vbot/apps && mktemp -d /userdata/vbot/apps/cpp-app-XXXXXX') &&
test -n "$APP_DIR" &&
printf 'Device application directory: %s\n' "$APP_DIR" &&
scp -r "$PACKAGE_DIR/." "$ROBOT:$APP_DIR/" &&
ssh "$ROBOT"
```

记录 APP_DIR，下一段在登录设备后的 vbot shell 中执行。

## 运行——设备 vbot shell

将 APP_DIR 替换为输出目录。校验失败或动态库缺失时停止命令链，
修正部署包，不修改设备权限。

```bash
APP_DIR=/userdata/vbot/apps/cpp-app-REPLACE_FROM_OUTPUT &&
cd "$APP_DIR" &&
sha256sum -c SHA256SUMS &&
export PATH="/opt/vita/aorta/bin:$PATH" &&
export ZENOH_SESSION_CONFIG_URI=/opt/vita/aorta/edu/edu_session.json5 &&
export LD_LIBRARY_PATH="$PWD/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}" &&
LDD_OUTPUT=$(ldd ./bin/health-monitor) &&
printf '%s\n' "$LDD_OUTPUT" &&
[[ "$LDD_OUTPUT" != *"not found"* ]] &&
./bin/health-monitor --config config.json --execute --duration 10
```

重新登录后，进入同一目录并再次设置三个运行变量即可，无需重新安装。
Ctrl+C 或时长到期即可停止，不修改服务、自启动、ACL 或资源配置。

连接、环境及接口说明见 [VBOT Lab](https://github.com/VitaDynamics/vbot-lab)。
排障使用 [C++ 路径](https://github.com/VitaDynamics/vbot-lab/blob/main/docs/development/diagnostics.zh-CN.md#cpp)，不需要安装 Python wheel。
请在审阅报告后到 [Vbot 超能社区](https://forum.vbot.cn/)反馈可复现问题，
不分享凭据或会话配置。
