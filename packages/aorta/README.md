# Aorta

<p align="center">English | <a href="README.zh-CN.md">中文</a></p>

Aorta provides the communication SDK in VBOT Lab's [client libraries](../README.md).
Choose the [Aorta Python SDK](python/README.md) or [Aorta C++ SDK](cpp/README.md); installable
artifacts are distributed as vbot-lab release assets (first release `edu-sdk-*`).

Use the SDK together with matching [Interface Definitions](../../schemas/README.md).
The repository tracks the synchronized FlatBuffers and ROS 2 definitions; generated C++
headers remain in the matching schema-pack release asset.
SDK package names, import paths, and API contracts remain those of Aorta.

## Install

Download the assets from the [vbot-lab releases](https://github.com/VitaDynamics/vbot-lab/releases)
and verify them against the release's `SHA256SUMS`. `EDU_SDK_MANIFEST.json` in the
same release records the version pairing and each asset's SHA-256 digest.

### Python

Python 3.10 or newer is required. Download the `aorta_sdk` wheel for the machine —
`linux_aarch64`, `linux_x86_64`, or `macosx_11_0_arm64` — plus `aorta_msgs` and
`vbot_edu_msgs` from GitHub Releases. SDK downloads require network access.

`vbot_edu_msgs` also requires `flatbuffers`; the `edu-sdk-2026.9.24` release attaches the
`flatbuffers` 25.12.19 wheel. Follow the [Aorta Python SDK guide](python/README.md) to
install the SDK wheels in a dedicated venv, with `flatbuffers==25.12.19` from PyPI or from
the release.
That guide also covers preparing dependencies for a robot without Internet access,
connection modes, and a runnable example.

### C++

For Bazel examples, pinned versions, runtime deployment and optional camera decoding,
follow the [C++ guide](cpp/README.md). The commands below describe the archive layout.

Extract `aorta-cpp-sdk-<ver>-abi12-ubuntu22.04-<arch>.tar.zst` and
`aorta-edu-schema-pack-<ver>-v4.tar.zst` into separate directories:

```bash
mkdir -p sdk pack
tar --zstd -xf aorta-cpp-sdk-<ver>-abi12-ubuntu22.04-<arch>.tar.zst -C sdk
tar --zstd -xf aorta-edu-schema-pack-<ver>-v4.tar.zst -C pack
```

`<arch>` is `x86_64` or `aarch64`. The SDK archive is an Ubuntu 22.04 build that provides
the CMake package under `share/cmake` and the runtime libraries under `lib`; the schema pack
provides the generated message headers and `*_msg.h` wrappers under `include`.

A minimal project needs the CMake package, the generated headers, and the `Aorta::cpp`
target:

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

`12` requests the Core ABI generation that the archive name and version file carry. From
Aorta 2026.9.23 a versionless `find_package(Aorta CONFIG REQUIRED)` also works; earlier
archives require the `12`.

`publisher.cc`:

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

`subscriber.cc`:

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

Configure, build, and check the runtime libraries:

```bash
cmake -S . -B build \
  -DCMAKE_PREFIX_PATH="$PWD/sdk/share/cmake" \
  -DEDU_SCHEMA_INCLUDE="$PWD/pack/include" \
  -DCMAKE_BUILD_TYPE=Release
cmake --build build -j2
LD_LIBRARY_PATH="$PWD/sdk/lib" ldd build/edu_bms_subscriber
```

`ldd` must resolve `libaorta_core.so.12` and `libaorta_cpp.so` from the extracted
`sdk/lib` directory. Run every binary with `LD_LIBRARY_PATH="<sdk>/lib"` so the loader
finds both libraries.

With the local router and client configuration from the
[Aorta Python SDK](python/README.md#5-work-without-a-robot), run a local round trip:

```bash
export ZENOH_SESSION_CONFIG_URI=/tmp/aorta_quickstart_client.json5
LD_LIBRARY_PATH="$PWD/sdk/lib" ./build/edu_bms_subscriber &
LD_LIBRARY_PATH="$PWD/sdk/lib" ./build/edu_bms_publisher
```

Expected output:

```text
PUBLISHED sensor_timestamp_ns=987654321 voltage_mv=49500
RECEIVED sensor_timestamp_ns=987654321 voltage_mv=49500
```

On the robot, use the delivered session configuration. The S100 image ships GCC 11.4 but no
CMake, so build aarch64 binaries on a workstation and copy the executable together with
`libaorta_core.so.12` and `libaorta_cpp.so` to a user directory on the robot:

```bash
export ZENOH_SESSION_CONFIG_URI=/opt/vita/aorta/edu/edu_session.json5
LD_LIBRARY_PATH=<robot-user-directory> ./edu_bms_subscriber /bms_state
```

Expected output: `RECEIVED sensor_timestamp_ns=0 voltage_mv=45840`; the values depend on
robot state.

Extract the `aarch64` archive into `sdk-arm` (the same extraction step with the `aarch64`
file), then cross-compile with an aarch64 GCC 11 toolchain:

```bash
cmake -S . -B build-arm \
  -DCMAKE_SYSTEM_NAME=Linux -DCMAKE_SYSTEM_PROCESSOR=aarch64 \
  -DCMAKE_CXX_COMPILER=aarch64-linux-gnu-g++ \
  -DCMAKE_PREFIX_PATH="$PWD/sdk-arm/share/cmake" \
  -DEDU_SCHEMA_INCLUDE="$PWD/pack/include" \
  -DCMAKE_BUILD_TYPE=Release
cmake --build build-arm -j2
```

The S100 runs glibc 2.35; the bundle references at most GLIBC 2.34 and GLIBCXX 3.4.22, so
the cross-built binaries load on the device. Use the `aarch64` archive and an
`aarch64-linux-gnu-g++` 11 toolchain to match this tested combination.
