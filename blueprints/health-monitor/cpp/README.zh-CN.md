# C++ 只读健康监测

<p align="center"><a href="README.md">English</a> | 中文</p>

这是[健康监测 Blueprint](../README.zh-CN.md)的 C++17／Aorta C++ SDK 实现，
组合 `/locomotion/status`、`/bms_state` 与 `/system/sm_status`，不发布控制消息、
不调用 service／action，也不采集音视频。配套 foot_quadruped 应用 V1.6.0-12，
以及 Release edu-sdk-2026.10.14 中的 SDK 2026.10.12／ABI 13、Schema pack 2026.10.13-v4。
机器人无需 Python 运行时或 wheel。

## 构建与预览——开发容器

先按 [C++ SDK 指南](../../../packages/aorta/cpp/README.zh-CN.md)准备原生 x86_64 SDK 与 Schema，
将 AORTA_CPP_SDK_DIR／AORTA_EDU_SCHEMA_DIR 指向已校验的解压路径。
在已有开发容器的仓库根目录执行：

```bash
bazel build //blueprints/health-monitor:main_cpp &&
bazel test //blueprints/health-monitor:model_cpp_test \
  //blueprints/health-monitor:sdk_cpp_test //tests:health_monitor_cpp_test &&
bazel run //blueprints/health-monitor:main_cpp -- \
  --config blueprints/health-monitor/config.json &&
bazel run //blueprints/health-monitor:main_cpp -- \
  --config blueprints/health-monitor/config.json --simulate
```

C++ 预览需链接 SDK，但不创建 Node。纯模型测试无需 SDK，序列化和 CLI 测试使用真实生成头文件，
不访问设备。默认 CLI 输出 execute=false；模拟输出合成的 receiving／stale 状态，
不属于机器人数据或物理仿真。

## 配置与行为

两种语言共用 config.json，以及相同的新鲜度／提示规则。C++ 配置读取器支持仅包含以下两个字段的
扁平对象：stale_after_seconds 范围 (0, 120]、low_battery_percent 范围 [0, 100]；
使用这两个原样字段名和有限 JSON 数值，文件不超过 4096 字节。
拒绝多余／重复字段和尾随内容，无需增加 JSON 库依赖。
在部署目录省略 --config 时读取 config.json；上方仓库命令显式指定配置。

--duration 范围 (0, 120] 秒，默认 10 秒；--simulate 与 --execute 互斥。
JSON Lines 包含 source、all_streams_receiving、low_battery，以及各流的 status、age_seconds、
样本／异常计数与解码字段。最后一条增加 final=true。
waiting_data 不判定接口不支持。新鲜度基于回调中记录的本地单调时间，不是出队时间；
延后处理不会刷新积压样本，不比较不同流时钟，也不代表采集延迟。
源时间戳仅用于本流排序，零值不排序；生产者时间戳重置后需重新启动监测。
低电量仅作提示，不触发控制，也不判断物理安全。

model.h 保存不依赖 SDK 的业务规则，decoder.h 在访问前校验 FlatBuffer。
main.cc 将回调中的借用字节复制到一个最多 64 条消息的队列，每条上限 1 MiB，
再在消费线程汇总输出。队列溢出或 SDK 报告丢包时停止。
RAII 保证先释放订阅再释放 Node，包括部分订阅失败与 Ctrl+C。
退出码 0 表示结束时三路数据均新鲜；1 表示缺少／过期输入或运行／配置失败；
2 表示 CLI 参数错误；中断为 130。

## ARM64 构建与打包——开发容器

复用 C++ SDK 指南中已校验的 ARM64 SDK 与共用 Schema；解压路径不同时替换下面变量。
AMD64 容器进行交叉编译，不在其中执行 ARM64 程序或测试。

```bash
export AORTA_CPP_SDK_DIR="$PWD/artifacts/edu-sdk-2026.10.14/cpp-sdk-aarch64" &&
export AORTA_EDU_SCHEMA_DIR="$PWD/artifacts/edu-sdk-2026.10.14/edu-schema" &&
bazel build --config=arm64 //blueprints/health-monitor:main_cpp &&
PACKAGE_DIR=$(mktemp -d /tmp/vbot-health-cpp-XXXXXX) &&
test -n "$PACKAGE_DIR" &&
mkdir -p "$PACKAGE_DIR/bin" "$PACKAGE_DIR/lib" "$PACKAGE_DIR/licenses/aorta" &&
cp -L bazel-bin/blueprints/health-monitor/main_cpp "$PACKAGE_DIR/bin/health-monitor" &&
cp -L "$AORTA_CPP_SDK_DIR/lib/libaorta_core.so.13" "$PACKAGE_DIR/lib/" &&
cp blueprints/health-monitor/config.json "$PACKAGE_DIR/config.json" &&
cp LICENSE NOTICE "$PACKAGE_DIR/licenses/" &&
cp "$AORTA_CPP_SDK_DIR/LICENSE" "$AORTA_CPP_SDK_DIR/NOTICE" \
  "$AORTA_CPP_SDK_DIR/FLATBUFFERS-LICENSE" \
  "$AORTA_CPP_SDK_DIR/THIRD_PARTY_COMPONENTS.md" \
  "$AORTA_CPP_SDK_DIR/THIRD_PARTY_NOTICES.md" "$PACKAGE_DIR/licenses/aorta/" &&
file "$PACKAGE_DIR/bin/health-monitor" "$PACKAGE_DIR/lib/libaorta_core.so.13" &&
aarch64-linux-gnu-readelf -d "$PACKAGE_DIR/bin/health-monitor" &&
(cd "$PACKAGE_DIR" && find bin lib licenses config.json -type f -exec sha256sum {} + > SHA256SUMS)
```

两个 ELF 文件均应显示 AArch64，保留 PACKAGE_DIR 供传输。
包内包括可执行文件、动态运行库、共用配置及许可证，按 C++ SDK 指南检查间接依赖。
使用设备兼容的系统库，不复制 host glibc 或覆盖设备库。
修改包内 config.json 会使校验失效；应在打包前改好配置，或显式重新打包自己的应用。

## 传输——具备 SSH 访问的机器

复用已验证的 [SSH 公钥登录](../../../docs/robots/quadruped-common/connection.zh-CN.md)。
ROBOT 替换为选定的 vbot 地址／别名，有线或 Wi-Fi 均可；连接失败时先连接设备或修正地址。
这一步只需要传输能力，不需要编译器，PACKAGE_DIR 必须指向本机可见的完整包。

```bash
ROBOT=vbot@192.168.126.2 &&
ssh -o BatchMode=yes "$ROBOT" \
  'test "$(id -un)" = vbot && test "$(uname -m)" = aarch64 && id -un && uname -m' &&
APP_DIR=$(ssh -o BatchMode=yes "$ROBOT" \
  'mkdir -p /userdata/vbot/apps && mktemp -d /userdata/vbot/apps/health-monitor-cpp-XXXXXX') &&
test -n "$APP_DIR" &&
printf 'Device application directory: %s\n' "$APP_DIR" &&
scp -r "$PACKAGE_DIR/." "$ROBOT:$APP_DIR/" &&
ssh "$ROBOT"
```

记下 APP_DIR，下一段在登录后的设备 shell 执行，不是在开发容器中执行。
设备不需要仓库、Bazel、SDK 头文件、Python 或联网下载依赖。

## 运行——设备 vbot shell

APP_DIR 替换为打印的实际目录。校验或动态库检查失败时停止，修正部署包，不修改权限或系统库。

```bash
APP_DIR=/userdata/vbot/apps/health-monitor-cpp-REPLACE_FROM_OUTPUT &&
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

重新登录后进入同一目录、设置三个运行环境变量，再运行程序。
时长到期或 Ctrl+C 即可停止，不会加入后台服务或自启动。
通过[分层诊断](../../../docs/development/diagnostics.zh-CN.md)区分环境、SDK 与收不到数据的问题。
要在自己的项目中继续开发，使用 [C++ 应用生成器](../../../templates/README.zh-CN.md)，
按生成工作区的 README 执行。生成器复制源码／构建辅助代码及 ARM64 工具链，
不再引用本仓库路径，SDK 制品保持外置。两条路径都部署二进制，不将源码仓库部署到设备。
