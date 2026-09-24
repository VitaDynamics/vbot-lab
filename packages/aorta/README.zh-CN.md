# Aorta

<p align="center"><a href="README.md">English</a> | 中文</p>

Aorta 提供 VBOT Lab [客户端开发库](../README.zh-CN.md)中的通信 SDK。
可选择 [Aorta Python SDK](python/README.zh-CN.md) 或 [Aorta C++ SDK](cpp/README.zh-CN.md)，可安装制品通过 vbot-lab Release
附件分发（首版 `edu-sdk-*`）。

使用时需配套匹配版本的 [Interface Definitions（接口定义）](../../schemas/README.zh-CN.md)。
仓库会跟踪同步生成的 FlatBuffers 与 ROS 2 定义；生成的 C++ 头文件仍由匹配的
schema-pack release 资产提供。
SDK 的包名、导入路径及 API 契约仍沿用 Aorta。

## 安装

从 [vbot-lab Releases](https://github.com/VitaDynamics/vbot-lab/releases) 下载附件，
并用同一 Release 中的 `SHA256SUMS` 校验。同一 Release 内的 `EDU_SDK_MANIFEST.json`
记录了版本配对及每个附件的 SHA-256 摘要。

### Python

需要 Python 3.10 或更高版本。从 GitHub Releases 下载对应机器的 `aorta_sdk` wheel——
`linux_aarch64`、`linux_x86_64` 或 `macosx_11_0_arm64`——以及 `aorta_msgs`、
`vbot_edu_msgs`。SDK 下载需要联网。

`vbot_edu_msgs` 还依赖 `flatbuffers`；`edu-sdk-2026.9.24` Release 附带 `flatbuffers`
25.12.19 wheel。按 [Aorta Python SDK 指南](python/README.zh-CN.md)在专用 venv 中安装
SDK wheel，`flatbuffers==25.12.19` 可从 PyPI 或 Release 获取。
该指南还介绍了无互联网设备的依赖准备、连接方式与可运行示例。

### C++

Bazel 示例、配套版本、运行库部署及可选相机解码见 [C++ 指南](cpp/README.zh-CN.md)。

将 `aorta-cpp-sdk-<ver>-abi12-ubuntu22.04-<arch>.tar.zst` 与
`aorta-edu-schema-pack-<ver>-v4.tar.zst` 分别解压到各自目录；配置时将
`CMAKE_PREFIX_PATH` 指向 SDK 的 `share/cmake` 目录，并把 schema pack 的 `include/`
目录加入头文件搜索路径：

```bash
mkdir -p sdk pack
tar --zstd -xf aorta-cpp-sdk-<ver>-abi12-ubuntu22.04-<arch>.tar.zst -C sdk
tar --zstd -xf aorta-edu-schema-pack-<ver>-v4.tar.zst -C pack
```

`<arch>` 为 `x86_64` 或 `aarch64`。SDK 包是 Ubuntu 22.04 构建：CMake 包位于
`share/cmake`，运行时库位于 `lib`；schema pack 在 `include` 下提供生成的消息头文件与
`*_msg.h` 包装头。

最小工程需要 CMake 包、生成的头文件与 `Aorta::cpp` 目标：

```cmake
cmake_minimum_required(VERSION 3.16)
project(edu_bms_roundtrip LANGUAGES CXX)

find_package(Aorta 12 CONFIG REQUIRED)

add_executable(edu_bms_publisher publisher.cc)
target_compile_features(edu_bms_publisher PRIVATE cxx_std_17)
target_include_directories(edu_bms_publisher PRIVATE "${EDU_SCHEMA_INCLUDE}")
target_link_libraries(edu_bms_publisher PRIVATE Aorta::cpp)

add_executable(edu_bms_subscriber subscriber.cc)
target_compile_features(edu_bms_subscriber PRIVATE cxx_std_17)
target_include_directories(edu_bms_subscriber PRIVATE "${EDU_SCHEMA_INCLUDE}")
target_link_libraries(edu_bms_subscriber PRIVATE Aorta::cpp)
```

`12` 请求压缩包名与版本文件所标注的 Core ABI 代际。从 Aorta 2026.9.23 起，不带版本号的
`find_package(Aorta CONFIG REQUIRED)` 同样可用；更早的压缩包必须保留 `12`。

`publisher.cc`：

```cpp
#include <iostream>
#include "aorta/aorta.h"
#include "bms_state_msg.h"

int main() {
  return aorta::RunOrFatal([] {
    auto node = aorta::Must(aorta::Node::Create("edu_sdk"), "Create node");
    auto publisher = aorta::Must(
        node->CreatePublisher<bms::BmsState>("/edu_verify/bms_state"),
        "Create publisher");
    if (!aorta::Must(publisher->WaitForMatching(5000), "Wait for subscriber")) {
      std::cerr << "subscriber did not match\n";
      return 1;
    }
    aorta::CheckOk(
        publisher->PublishTyped<bms::BmsState>([](bms::BmsStateMsg& message) {
          message.sensor_timestamp_ns = 987654321;
          message.voltage_mv = 49500;
        }),
        "Publish BmsState");
    std::cout << "PUBLISHED sensor_timestamp_ns=987654321 voltage_mv=49500\n";
    return 0;
  });
}
```

`subscriber.cc`：

```cpp
#include <atomic>
#include <chrono>
#include <iostream>
#include <string>

#include "aorta/aorta.h"
#include "bms_state_msg.h"

int main(int argc, char** argv) {
  return aorta::RunOrFatal([&] {
    const std::string topic = argc > 1 ? argv[1] : "/edu_verify/bms_state";
    auto node = aorta::Must(aorta::Node::Create("edu_sdk"), "Create node");
    auto executor = aorta::Must(aorta::Executor::Create(), "Create executor");
    aorta::CheckOk(executor->AddNode(node), "Add node");
    std::atomic<bool> received{false};
    auto subscriber = aorta::Must(
        node->CreateSubscriberTypedView<bms::BmsState>(
            topic,
            [&received, topic] (const bms::BmsState& message,
                               const aorta::MessageContextView&) {
              std::cout << "RECEIVED sensor_timestamp_ns="
                        << message.sensor_timestamp_ns()
                        << " voltage_mv=" << message.voltage_mv() << "\n";
              received = topic == "/bms_state" ||
                         (message.sensor_timestamp_ns() == 987654321 &&
                          message.voltage_mv() == 49500);
            }),
        "Create subscriber");
    const auto deadline = std::chrono::steady_clock::now() + std::chrono::seconds(10);
    while (!received && std::chrono::steady_clock::now() < deadline) {
      auto status = executor->SpinOnce(std::chrono::milliseconds(100));
      if (!status.ok() && status.code() != AORTA_ERR_TIMEOUT) {
        aorta::CheckOk(status, "SpinOnce");
      }
    }
    return received ? 0 : 1;
  });
}
```

配置、构建并检查运行时库：

```bash
cmake -S . -B build \
  -DCMAKE_PREFIX_PATH="$PWD/sdk/share/cmake" \
  -DEDU_SCHEMA_INCLUDE="$PWD/pack/include" \
  -DCMAKE_BUILD_TYPE=Release
cmake --build build -j2
LD_LIBRARY_PATH="$PWD/sdk/lib" ldd build/edu_bms_subscriber
```

`ldd` 必须从解压出的 `sdk/lib` 解析到 `libaorta_core.so.12` 与 `libaorta_cpp.so`。
每次运行二进制时都要设置 `LD_LIBRARY_PATH="<sdk>/lib"`，以便加载器找到这两个库。

配合 [Aorta Python SDK](python/README.zh-CN.md#5-无机器人开发)中的本地路由器与客户端
配置，执行一次本地往返：

```bash
export ZENOH_SESSION_CONFIG_URI=/tmp/aorta_quickstart_client.json5
LD_LIBRARY_PATH="$PWD/sdk/lib" ./build/edu_bms_subscriber &
LD_LIBRARY_PATH="$PWD/sdk/lib" ./build/edu_bms_publisher
```

预期输出：

```text
PUBLISHED sensor_timestamp_ns=987654321 voltage_mv=49500
RECEIVED sensor_timestamp_ns=987654321 voltage_mv=49500
```

在机器人上使用随设备交付的会话配置。S100 镜像自带 GCC 11.4 但没有 CMake，因此请在工作站
构建 aarch64 二进制，并把可执行文件连同 `libaorta_core.so.12`、`libaorta_cpp.so` 复制到
机器人上的用户目录：

```bash
export ZENOH_SESSION_CONFIG_URI=/opt/vita/aorta/edu/edu_session.json5
LD_LIBRARY_PATH=<robot-user-directory> ./edu_bms_subscriber /bms_state
```

预期输出：`RECEIVED sensor_timestamp_ns=0 voltage_mv=45840`；数值取决于机器人状态。

将 `aarch64` 压缩包解压到 `sdk-arm`（与安装步骤相同，只是改用 `aarch64` 文件），
然后使用 aarch64 GCC 11 工具链交叉编译：

```bash
cmake -S . -B build-arm \
  -DCMAKE_SYSTEM_NAME=Linux -DCMAKE_SYSTEM_PROCESSOR=aarch64 \
  -DCMAKE_CXX_COMPILER=aarch64-linux-gnu-g++ \
  -DCMAKE_PREFIX_PATH="$PWD/sdk-arm/share/cmake" \
  -DEDU_SCHEMA_INCLUDE="$PWD/pack/include" \
  -DCMAKE_BUILD_TYPE=Release
cmake --build build-arm -j2
```

S100 运行 glibc 2.35；该包最多引用 GLIBC 2.34 与 GLIBCXX 3.4.22，因此交叉编译产物可在
设备上加载。请使用 `aarch64` 包与 `aarch64-linux-gnu-g++` 11 工具链，与此处验证过的
组合保持一致。
