# Capabilities & Interfaces

<p align="center"><a href="README.md">English</a> | 中文</p>

工作流与接口的本地索引，不是设备发现服务。
通过 [capabilities.json](capabilities.json)定位工作流、接口、SDK 要求、Recipe 和验证边界，
无需读取所有文档。

## 查询能力索引

在仓库根目录使用 Python 3.10+：

```bash
python3 tools/vbot_catalog.py
python3 tools/vbot_catalog.py --robot-type foot_quadruped --capability robot.state.subscribe
python3 tools/vbot_catalog.py --robot-type foot_quadruped --capability device.environment.check
python3 tools/vbot_catalog.py --robot-type foot_quadruped --capability device.application.autostart
python3 tools/vbot_catalog.py --robot-type foot_quadruped --capability robot.sensors
python3 tools/vbot_catalog.py --robot-type foot_quadruped --capability robot.cameras
python3 tools/vbot_catalog.py --robot-type foot_quadruped --capability robot.perception
python3 tools/vbot_catalog.py --robot-type foot_quadruped --capability robot.audio
python3 tools/vbot_catalog.py --robot-type foot_quadruped --capability robot.locomotion
python3 tools/vbot_catalog.py --robot-type foot_quadruped --capability robot.system-peripherals
python3 tools/vbot_catalog.py --robot-type foot_quadruped --capability robot.rcp
python3 tools/vbot_catalog.py --robot-type foot_quadruped --capability robot.slam.mapping-localization
python3 tools/vbot_catalog.py --robot-type wheel_quadruped --capability device.agent.content
```

查询离线执行。退出码 0 只表示查询成功，不代表能力可以运行。
需检查每个结果的 `decision`：`local_only`、`requires_robot_selection`、`blocked_release`、
`not_applicable`、`blocked_integration` 或 `requires_device_verification`。
未知标识或数据错误返回退出码 2；表示阻塞的 decision 仍然是有效的查询结果。

机器人接口按功能域组织。检测与人体关键点统一查询 perception；音频帧、识别文本与事件统一查询 audio。
查询只定位文档，不表示要订阅该功能域的每条路由。按指南选择所需输出，控制输入仍需明确操作意图。

## 格式版本 1

这是由本仓库 Skills 与工具明确读取的 VBOT Lab 约定，不是通用 Coding Agent manifest。
JSON 可由 Python 标准库直接校验。所有路径相对于仓库根目录。
机器可读标识与路径只维护一份；索引引用的英文 Markdown 配有 `.zh-CN.md` 译文供中文阅读。

| 字段 | 含义 |
| --- | --- |
| `availability` | `implemented` 本地入口、`documented` 设备契约、`planned` 待接入；不表示在线就绪 |
| `robot_types` | 能力范围；空列表仅适用于本地清点，不能解释成“全部机器人” |
| `execution_location` | 开发者工作站／容器、设备服务、开发者自有工具服务，或 `device_shell`（设备登录后运行） |
| `interface_kind` | 通信类别，包括 `pub_sub`、`service` 和 `action`；`null` 表示尚未选择，不推测 |
| `reference` | 行为／接口的权威文档 |
| `skill`、`tool`、`recipe` | 对应仓库资源，不存在时为 `null`；Recipe 引用可能只有提纲 |
| `requires_sdk` | 是否依赖 Aorta Python SDK |
| `effect` | 本地只读、设备只读或取决于具体操作；不授予操作权限 |
| `minimum_firmware` | 已知最低版本，未知为 `null`；未知不代表任意版本 |
| `verification` | 条目检查状态：`local_tests` 为已有本地测试的工具，`documentation_only` 为已有文档的接口／流程，`not_verified` 为尚未检查的条目 |

`documentation_only` 条目提供接口操作说明，不提供可执行工具。
设备条目的 `requires_device_verification` 表示按流程操作前，先检查选定设备的接口可用性和操作前置条件。

SDK 元数据分别记录接入状态和版本。设备配置区分当前发布对象与规划类型；
`models` 为空表示尚未登记具体型号。硬件适用性不代表软件支持。
设备配置的 `application_version` 记录应用适配版本：`foot_quadruped` 为 `V1.6.0`，
尚未发布的类型为 `null`；查询结果在 `robot` 中返回该字段。
它不是 SDK 或系统镜像版本，也不表示“此版本及以上均支持”。
`minimum_firmware` 是独立的可选最低版本约束；`null` 不取消已声明的应用适配版本，
也不代表兼容其他版本。
两类机器狗引用同一份传感器／连接资料，双足配置不继承这些资料。

加载器检查格式版本、标识、枚举值、引用存在性、设备归属和可执行入口可用状态，
不执行索引数据中的命令。验证范围见[离线测试](../tests/README.zh-CN.md)，
便于人阅读的矩阵见[兼容说明](../docs/compatibility.zh-CN.md)。

## 跟随事实来源

- [设备环境](../docs/getting-started/device-environment.zh-CN.md)：vbot shell 配置与离线清点，不依赖 SDK 接入。
- [用户程序自启动](../docs/guides/user-autostart.zh-CN.md)：开机入口、显式环境、日志及停用；配置和启动应用会改变设备状态。
- [Aorta／ROS 2](../docs/interfaces/aorta-ros2.zh-CN.md)：开放 topic、订阅／发布方向、类型、service 映射及 RCP action，不表示 SDK Recipe 就绪。
- [接口功能域](../docs/interfaces/README.zh-CN.md)：传感器、相机、perception、audio、运动、系统／外设、RCP、SLAM 的定义与用法。
- [建图与定位](../docs/guides/mapping-localization.zh-CN.md)：原生 Aorta SLAM 流程与基于状态的完成检查；模式切换须有明确操作意图。
- [Aorta Python SDK](../packages/aorta/python/README.zh-CN.md)：已有发布版 wheel 安装说明。
- [Schema](../schemas/README.zh-CN.md)：已入库的字段与类型定义。
- [接口参考](../docs/interfaces/README.zh-CN.md)：确切的已整理契约，包括设备 Agent API。
- [Recipes](../recipes/README.zh-CN.md)：规划中的单项任务实现。
- [Skills](../skills/README.zh-CN.md)：Coding Agent 工作流，不是设备运行时内容。

不手动向索引复制 topic、字段、单位或 HTTP 路由列表；这些内容保留在所引用的 Schema／契约来源中，
接入后再从这些来源生成结构索引。应用适配版本为 `V1.6.0`，选定设备后检查已安装应用及运行时可用性。

相机、音频、运控与 RCP 保持按接口族归类，`recipe` 字段指向对应 SDK 示例，不拆分成每个 Topic 的独立检查。
接口族的 CLI 文档仍可独立于 SDK 使用（`requires_sdk=false`）；在线运行所链接的 Python Recipe 则需要配套 wheel。
`implemented` 表示已有程序入口，不表示已连接设备；应用适配版本不能代替目标路由检查。

`sdk.cpp` 记录 C++ SDK 版本、ABI、Schema 配套与安装指南。
Recipe 条目的 `implementations.python` 和 `implementations.cpp` 分别记录源码与 Bazel 目标；
`tool` 保留已有 Python 入口以兼容现有调用者。选择 C++ 时使用 implementations 字段，不根据名字猜测入口。
两种语言共用接口族和操作边界，不重复拆分能力条目。
