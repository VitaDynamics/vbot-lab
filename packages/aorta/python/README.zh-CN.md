# Aorta Python SDK

<p align="center"><a href="README.md">English</a> | 中文</p>

Aorta Python SDK 通过 [vbot-lab Release](https://github.com/VitaDynamics/vbot-lab/releases)
附件分发。目前 SDK 安装包需要从 GitHub Releases 下载，克隆仓库不会自动安装 SDK。
下载需要联网，安装时也需要访问 PyPI 获取 Release 中缺失的依赖。本页说明如何安装 SDK、让 EDU 客户端连接机器人并
接收实时状态。支持的机器人镜像见[兼容矩阵](../../../docs/compatibility.zh-CN.md)，
版本配对见 Release 内的 `EDU_SDK_MANIFEST.json`。

从 [edu-sdk-2026.9.24](https://github.com/VitaDynamics/vbot-lab/releases/tag/edu-sdk-2026.9.24)
安装 Python wheel。版本配套以发布清单为准，而不是要求各包版本号相同：

| 发行包 | 版本 | 用途 |
| --- | --- | --- |
| `aorta-sdk` | `2026.9.23` | `import aorta`；Python API 与平台相关的原生运行库 |
| `aorta-msgs` | `2026.9.23` | 基础消息的生成代码与 Schema 元数据 |
| `vbot-edu-msgs` | `2026.9.24` | EDU 消息的生成代码与 Schema 元数据 |

Aorta 与 EDU wheel 在 `.dist-info/licenses/` 下附带各自的 `LICENSE` 和 `NOTICE`。
PyPI 的 FlatBuffers wheel 不含许可证文件，因此 release 附上其上游许可证文本
`flatbuffers-<ver>.LICENSE`。

使用 Python 3.10 或更新版本。SDK wheel 提供 Linux x86_64、Linux aarch64 和 macOS arm64
版本。检查实际运行机器的架构与原生库兼容性；工作站安装成功不代表设备固件兼容。
另见[兼容矩阵](../../../docs/compatibility.zh-CN.md)。

## 1. 选择 Release wheel

从 `edu-sdk-2026.9.24` 下载所选平台的以下三个 wheel，
以及 `SHA256SUMS` 与 `EDU_SDK_MANIFEST.json`：

| Wheel | 用途 |
| --- | --- |
| `aorta_sdk-<ver>-py3-none-<platform>.whl` | 对应平台的 SDK 包与原生运行库 |
| `aorta_msgs-<ver>-py3-none-any.whl` | Aorta 消息类型 |
| `vbot_edu_msgs-<ver>-py3-none-any.whl` | EDU 消息类型与生成的 schema 辅助模块 |

按机器选择 `aorta_sdk` wheel——`linux_aarch64`（S100）、`linux_x86_64` 或
`macosx_11_0_arm64`。需要 Python 3.10 或更高版本。`linux_*` 标签范围较宽：这两个 wheel
是 Ubuntu/glibc 构建。

`vbot_edu_msgs` 还依赖 `flatbuffers`。Release 同时附带 `flatbuffers` 25.12.19 wheel，
四个 wheel 可以离线安装；下方命令改为从 PyPI 获取 `flatbuffers==25.12.19`。
`EDU_SDK_MANIFEST.json` 的 `pairing.wheels` 记录所有 wheel 的版本。

## 2. 联网安装

不要把二进制加入 Git。将三个配套 wheel、`SHA256SUMS` 与 `EDU_SDK_MANIFEST.json`
放到 `artifacts/edu-sdk-2026.9.24/`。在实际运行 Python 的环境中，确保 Python 3.10+、
venv 支持和 PyPI 网络访问可用。从 `artifacts/` 的上一级目录运行以下 Linux 示例：

```bash
uname -m
python3 --version
cd artifacts/edu-sdk-2026.9.24
sha256sum --ignore-missing -c SHA256SUMS
cd ../..
python3 -m venv .venv
. .venv/bin/activate
unset PYTHONPATH
export PYTHONNOUSERSITE=1
SDK_PLATFORM=linux_x86_64
python -m pip install \
  "artifacts/edu-sdk-2026.9.24/aorta_sdk-2026.9.23-py3-none-${SDK_PLATFORM}.whl" \
  artifacts/edu-sdk-2026.9.24/aorta_msgs-2026.9.23-py3-none-any.whl \
  artifacts/edu-sdk-2026.9.24/vbot_edu_msgs-2026.9.24-py3-none-any.whl \
  "flatbuffers==25.12.19"
python -m pip check
python -c 'import aorta; from foxglove.CompressedVideo import CompressedVideo; from aorta.action.rcp.ExecuteTaskGoal import ExecuteTaskGoalT; print("SDK imports OK")'
```

ARM64 机器人上应将变量**改为** `SDK_PLATFORM=linux_aarch64`。macOS arm64 使用
`macosx_11_0_arm64` 和可用的 SHA-256 校验工具。确认三个 SDK wheel 的校验均通过；
上面的命令会跳过未下载的文件，不会自动安装它们。缺少 Python、venv 或原生依赖时，
先解决运行环境问题。不要把工作站的 venv 或 x86_64 原生库直接复制到机器人。

该命令从本地 Release 下载文件安装三个 SDK 包，并从 PyPI 获取 FlatBuffers。
除非已经在本地准备齐全部依赖，否则不要加 `--no-index`。下载失败或依赖缺失时，
应先解决问题再继续；已有缓存不能证明 Release 提供了完整离线安装包。

设备无法访问互联网时，按 [Python 部署指南](../../../docs/development/python-deployment.zh-CN.md)
先在联网开发机下载 ARM64 SDK wheel 和缺失依赖，再传输完整 wheelhouse。
只有准备齐全后的设备安装阶段可以离线执行，首次下载／准备仍需要网络。

生成模块保留 Schema 命名空间，例如 `foxglove.CompressedVideo`、
`locomotion.LocomotionStatus` 和 `aorta.services.*`。
发行包名 `vbot-edu-msgs` **不是** Python import 命名空间。
wheel 已包含生成代码与元数据，无需在本地运行 `flatc`。

## 3. 连接

EDU 程序使用 `/opt/vita/aorta/edu/` 下发布的会话文件连接机器人的 EDU 路由器：

| 文件 | 用途 |
| --- | --- |
| `edu_session.json5` | client 模式。适用于 CLI、Foxglove bridge 和大多数程序 |
| `edu_session_peer.json5` | peer 模式。peer 之间还会直接交换数据；该文件会读取 `edu_dictionary.txt` |
| `edu_dictionary.txt` | peer 模式使用的凭据字典 |

话题、服务和动作名带前导斜杠（`/imu_raw`、`/my_app/status`），不需要加前缀。机器人
命名空间由会话配置在链路上附加，不要在 API 调用中添加。属于机器人公开接口的名称按
[接口参考](../../../docs/interfaces/README.zh-CN.md)到达机器人；其他任意名称只在连接到
同一台机器人的 EDU 程序之间共享，client 与 peer 模式都适用。EDU 程序处于同一个信任域：
其他 EDU 程序可以用任意名称发布，包括机器人话题的名称。

使用机器人接口的程序请以 `edu_sdk` 或 `edu_bridge` 作为节点名：机器人只以这两个名称
列出 EDU 节点。示例使用 `edu_sdk`。EDU 程序之间可以使用其他节点名。

### 机上（S100）

加载[设备 shell 环境](../../../docs/getting-started/device-environment.zh-CN.md)后，
以 `vbot` 运行客户端，并使用随设备交付的会话配置：

```bash
export ZENOH_SESSION_CONFIG_URI=/opt/vita/aorta/edu/edu_session.json5
```

使用 peer 模式时改用 `edu_session_peer.json5`。

### 离机经 X5 Wi-Fi

X5 把其 Wi-Fi 地址的 TCP 7447 端口转发到 EDU 路由器。把会话配置从机器人复制到工作站上
任何项目目录之外的私有目录，保留其中的 `namespace` 与凭据，只修改 `connect` 端点。
把 `<robot-alias>` 换成你为这台机器人取的名字：

```bash
dir="$HOME/.config/vbot/robots/<robot-alias>"
install -d -m 700 "$dir"
scp vbot@<robot-address>:/opt/vita/aorta/edu/edu_session.json5 "$dir/edu_session.json5"
chmod 600 "$dir/edu_session.json5"
perl -pi -e 's#tcp/127\.0\.0\.1:744[78]#tcp/<X5_WIFI_IP>:7447#g' "$dir/edu_session.json5"
nc -vz -w 3 <X5_WIFI_IP> 7447
export ZENOH_SESSION_CONFIG_URI="$dir/edu_session.json5"
```

使用 peer 模式时，还要复制字典，并把 `dictionary_file` 指向本地副本：

```bash
scp vbot@<robot-address>:/opt/vita/aorta/edu/edu_session_peer.json5 "$dir/edu_session_peer.json5"
scp vbot@<robot-address>:/opt/vita/aorta/edu/edu_dictionary.txt "$dir/edu_dictionary.txt"
chmod 600 "$dir/edu_session_peer.json5" "$dir/edu_dictionary.txt"
perl -pi -e 's#tcp/127\.0\.0\.1:7448#tcp/<X5_WIFI_IP>:7447#g' "$dir/edu_session_peer.json5"
perl -pi -e "s#/opt/vita/aorta/edu/edu_dictionary\.txt#$dir/edu_dictionary.txt#g" "$dir/edu_session_peer.json5"
export ZENOH_SESSION_CONFIG_URI="$dir/edu_session_peer.json5"
```

会话文件和字典包含 EDU 凭据。`chmod 600` 只能阻止本机其他用户读取，不能阻止 Git 提交
仓库目录中的文件。请把副本放在 `~/.config/vbot/robots/` 下，不要放进项目目录，也不要
贴到 issue 或聊天中。本仓库的 `.gitignore` 也会忽略这些文件名。只修改工作站副本；设备上
交付的文件保持不变。

没有 EDU 路由器的机器人软件不提供 `edu_session_peer.json5`；其 `edu_session.json5`
连接 7447 端口，只支持 client 模式，机器人公开接口以外的名称会被丢弃。哪些软件带
EDU 路由器见[兼容矩阵](../../../docs/compatibility.zh-CN.md)。

## 4. 接收实时状态

将以下脚本保存为 `subscribe_state.py`，并使用第 3 步的环境运行。它订阅 `/imu_raw`
与 `/bms_state`，每条流打印一行，各收到 20 条样本后退出：

```python
import threading
import time

import aorta
import aorta.topic.sensor.Imu as Imu
import bms.BmsState as BmsState

counts = {"imu": 0, "bms": 0}
first = {}
times = {}
done = threading.Event()


def update(name, field):
    now = time.monotonic()
    counts[name] += 1
    first.setdefault(name, field)
    times.setdefault(name, [now, now])[1] = now
    if all(count >= 20 for count in counts.values()):
        done.set()


def on_imu(message, _context):
    update("imu", (message.Seq(), message.FrameId()))


def on_bms(message, _context):
    update("bms", (message.VoltageMv(), message.SocPercent()))


with aorta.Node("edu_sdk") as node:
    node.create_subscriber_typed(
        lambda payload: Imu.Imu.GetRootAs(payload, 0), "/imu_raw", on_imu
    )
    node.create_subscriber_typed(
        lambda payload: BmsState.BmsState.GetRootAs(payload, 0),
        "/bms_state",
        on_bms,
    )
    if not done.wait(30):
        raise SystemExit(f"timeout counts={counts}")

for name in ("imu", "bms"):
    elapsed = times[name][1] - times[name][0]
    rate = (counts[name] - 1) / elapsed if elapsed else 0.0
    print(f"{name}: count={counts[name]} rate_hz={rate:.2f} first={first[name]!r}")
```

首批样本会立即到达；`/bms_state` 约 1 Hz 而 `/imu_raw` 约 104 Hz，因此脚本大约运行
20 秒。预期输出：

```text
imu: count=2069 rate_hz=104.01 first=(0, b'imu_link')
bms: count=20 rate_hz=1.00 first=(45750, 100.0)
```

计数与首个字段随机器人而异；两条流的速率应保持在约 104 Hz 与 1 Hz。出现
`SystemExit: timeout counts=...` 表示其中一条流始终没有数据：检查会话配置、端点，
以及所选机器人镜像是否提供该话题（见[兼容矩阵](../../../docs/compatibility.zh-CN.md)）。

## 5. 无机器人开发

SDK wheel 不包含路由器，Release 也不分发路由器。离机开发需从
[官方 Release 页面](https://github.com/eclipse-zenoh/zenoh/releases)自行安装官方
Eclipse zenoh `zenohd` **1.10.x**（与 SDK 所基于的 zenoh 相同的 minor），例如
`zenoh-1.10.1-<arch>-<os>-standalone.zip`。

启动本地路由器，然后使用 Aorta quickstart 的客户端配置让 SDK 节点连接：

```bash
zenohd --listen tcp/127.0.0.1:7447 --no-multicast-scouting
```

```bash
cat > /tmp/aorta_quickstart_client.json5 <<'EOF'
{
  mode: "client",
  connect: {
    endpoints: ["tcp/127.0.0.1:7447"]
  },
  scouting: {
    multicast: { enabled: false },
    gossip: { enabled: false }
  },
  transport: {
    shared_memory: { enabled: false }
  }
}
EOF
export ZENOH_SESSION_CONFIG_URI=/tmp/aorta_quickstart_client.json5
```

用一次本地发布/订阅往返验证安装：

```python
import threading

import aorta
import bms.BmsState as BmsState
import bms_state_schema_meta as schema

received = []
ready = threading.Event()


def decode(payload):
    return BmsState.BmsState.GetRootAs(payload, 0)


def on_message(message, _context):
    received.append((message.SensorTimestampNs(), message.VoltageMv()))
    ready.set()


with aorta.Node("edu_sdk") as node:
    node.create_subscriber_typed(decode, "/edu_verify/bms_state", on_message)
    publisher = node.create_publisher_typed(schema, "/edu_verify/bms_state")
    assert publisher.wait_for_matching(5000), "subscriber did not match"

    def fill(builder, header):
        BmsState.BmsStateStart(builder)
        BmsState.BmsStateAddAortaHeader(builder, header)
        BmsState.BmsStateAddSensorTimestampNs(builder, 987654321)
        BmsState.BmsStateAddVoltageMv(builder, 49500)
        return BmsState.BmsStateEnd(builder)

    publisher.publish_typed(fill)
    assert ready.wait(5), "message not received"
    assert received[-1] == (987654321, 49500), received
print("PUBSUB BMS OK", received[-1])
```

预期输出：

```text
PUBSUB BMS OK (987654321, 49500)
```

## 先构建，再在正确的环境中运行

无需访问注册表时，使用配套 Bazel 依赖包和
[离线构建入口](../../../docs/development/offline-build.zh-CN.md)。
图像解码和音视频二进制保存还需要 `numpy==2.2.6`，以批量提取消息中的数据；
请将匹配架构的 wheel 一并放入 wheelhouse。

在开发机／开发容器的仓库根目录使用 Bazel 7.6.1 构建 Python 入口。构建不会安装 wheel，也不会打包跨平台
运行库。显式选择已安装配套 wheel 的解释器：

```bash
bazel build //recipes/...
PATH="$PWD/.venv/bin:$PATH" bazel run //recipes/subscribe-state:main -- --help
PATH="$PWD/.venv/bin:$PATH" bazel run //recipes/subscribe-state:main
```

未传 `--execute` 时，所有示例只输出离线请求计划，不建立 Aorta 会话，预览也无需安装 SDK。
在线执行按 [Python 部署流程](../../../docs/development/python-deployment.zh-CN.md)：
在开发机构建，传输所选示例与 ARM64 wheelhouse，再在设备新建的应用目录中创建 venv 并安装依赖。
设备不预装仓库或应用 venv。完成该指南后，以 `vbot` 身份保持位于其记录的 APP_DIR 再运行：

```bash
. .venv/bin/activate
unset PYTHONPATH
export PYTHONNOUSERSITE=1
export PATH="/opt/vita/aorta/bin:$PATH"
export ZENOH_SESSION_CONFIG_URI=/opt/vita/aorta/edu/edu_session.json5
python -m recipes.subscribe-state.main --execute --count 3 --timeout 10
```

直接 Python 入口不要求设备安装 Bazel，执行的源码与 Bazel 目标相同。
精简部署包不含 Bazel 构建文件；仅在设备安装 Bazel 并不能使这些目标可用。示例会拒绝在设备 `vbot` shell 之外或使用
其他会话配置时在线运行，不会猜测工作站路由地址。原生 Aorta 示例无需加载 ROS 2 环境。

请在专用 shell 中运行原生 SDK 程序。ROS 环境可能把生成的 Python 包加入
`PYTHONPATH`，使其优先于 venv 中的包（包括其他版本的 `aorta-msgs`）；仅激活
venv 不会清除这些路径。以上命令只隔离当前 shell，不要把 unset 命令加入全局
shell 启动文件。需要 ROS 工具时，另开一个 SSH shell。

## 从 Schema 到 SDK

字段、枚举、联合类型与头部见 [Schema](../../../schemas/README.zh-CN.md)；
路由行为与前提见[接口说明](../../../docs/interfaces/README.zh-CN.md)。
收到的字节使用生成的访问器解析。类型化 service 调用传入配套的 `*_schema_meta` 模块，
由 SDK 提供 Aorta header。RCP 使用生成的对象类型配合 `FlatbuffersActionCodec`；
union 的类型标记必须与载荷一致。完整实现见 [Recipes](../../../recipes/README.zh-CN.md)。

`Node` 管理订阅者、客户端与 action 客户端。使用上下文管理器、有界队列与超时，
退出时释放资源。service 受理不代表运动完成，需通过请求标识匹配终态报告；
取消请求受理也不代表 action 已终态取消。超时可能意味着结果未知，应检查状态，
不要自动重复写操作。

离线测试不会建立设备会话：

```bash
bazel test //tests:recipe_test
bazel test --test_env=PATH="$PWD/.venv/bin:$PATH" //tests:recipe_sdk_test
```

第二个显式测试需要发布版 wheel，检查生成类型的序列化，不连接机器人。
相机、语音、运控和 RCP 的命令及额外前提见 [Recipes](../../../recipes/README.zh-CN.md)。

单项任务参考程序与完整应用见 [Recipes](../../../recipes/README.zh-CN.md) 与
[Blueprints](../../../blueprints/README.zh-CN.md)。
