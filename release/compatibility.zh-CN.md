# 兼容矩阵

<p align="center"><a href="compatibility.md">English</a> | 中文</p>

## 设备类型与 EDU 发布范围

| 设备类型 | EDU 发布范围 | 传感器参考 | 开发入口 |
| --- | --- | --- | --- |
| [foot_quadruped](../docs/robots/foot_quadruped/README.zh-CN.md) | 当前发布对象 | [机器狗共用规格](../docs/hardware/quadruped-common/sensors.zh-CN.md) | 已提供连接、shell 配置、Aorta／ROS 2 与 Agent 接口指南；组件可用性见下表 |
| [wheel_quadruped](../docs/robots/wheel_quadruped/README.zh-CN.md) | 后续发布；指南未发布 | [同一份机器狗共用规格](../docs/hardware/quadruped-common/sensors.zh-CN.md) | 尚未开放 EDU |
| [foot_humanoid](../docs/robots/foot_humanoid/README.zh-CN.md) | 后续发布；指南未发布 | 待补充；不适用机器狗参数 | 尚未开放 EDU |

此处尚未登记具体产品型号与硬件修订版本。
选择版本时需核对设备类型、型号／硬件版本、固件、开发镜像、SDK、Schema 集合及示例／接口覆盖范围。
构建标识存在或硬件参数相同，都不能单独作为软件兼容性证明。

## 组件接入状态

`foot_quadruped` EDU 使用 [vbot shell 配置](../docs/getting-started/device-environment.zh-CN.md)与
[Aorta／ROS 2 可用接口映射](../docs/interfaces/aorta-ros2.zh-CN.md)。
设备 CLI 可用性与工作站 SDK 安装是不同的前置条件。

接口参考还包含较新固件扩展的开放 topic 集、原生系统状态、静态 TF、控制 topic 与 RCP action，
以及[感知输出](../docs/interfaces/perception.zh-CN.md)和[音频／语音输入](../docs/interfaces/audio.zh-CN.md)。
这些接口的最低固件版本尚未公布；请在已安装固件上检查确切路由与消息类型。

| 项目 | 当前可用状态 | 兼容性检查 |
| --- | --- | --- |
| 仓库 | Unreleased | 目前尚无正式版本 |
| 开发镜像 | dev-v0.0.1 标签已配置 | 拉取镜像、固定 digest 并检查所需工具 |
| Bazel | 7.6.1 骨架基线 | 与 SDK 和镜像联调 |
| [Aorta Python SDK](../packages/aorta/python/README.zh-CN.md) | 通过 vbot-lab Release 附件分发（首版 `edu-sdk-*`），版本配对见 Release 内 `EDU_SDK_MANIFEST.json` | 固定公开版本与制品 |
| Python / ABI | 需要 Python 3.10 或更高版本；SDK wheel 提供 macOS arm64、Linux x86_64 与 Linux aarch64 版本。从 GitHub Releases 下载 SDK；`edu-sdk-2026.9.24` 还附带 `vbot_edu_msgs` 所需的 `flatbuffers` wheel，也可从 PyPI 获取。`linux_*` wheel 是 Ubuntu/glibc 构建 | 分别检查工作站与设备的架构、原生依赖；离线安装须另行准备完整 wheelhouse |
| 工作站原生运行库 | 通过 vbot-lab Release 附件分发（首版 `edu-sdk-*`），提供 x86_64 与 aarch64 的 Ubuntu 22.04 压缩包；版本配对见 Release 内 `EDU_SDK_MANIFEST.json` | 匹配架构、系统与 SDK；已验证的包需要 glibc 2.34 或更高版本 |
| 离机路由器 | 不随 Release 分发。请从[官方 Release 页面](https://github.com/eclipse-zenoh/zenoh/releases)安装 Eclipse zenoh `zenohd` 1.10.x（SDK 所基于的 zenoh minor），已验证版本为 1.10.1 | 路由器 minor 与 SDK 保持一致；机器人镜像自带路由器 |
| 设备 Aorta／ROS 2 工具 | 已整理上述快照的配置和部分可用 bridge 路由 | 分别检查公开文件、shell 变量、类型、发现与实际收数 |
| [Interface Definitions — 开放 Aorta Schema](../schemas/README.zh-CN.md) | 通过 vbot-lab Release 附件分发（首版 `edu-sdk-*`），版本配对见 Release 内 `EDU_SDK_MANIFEST.json` | 匹配 SDK 版本、依赖及生成的绑定 |
| [Recipes](../recipes/README.zh-CN.md) | 按能力组织的 Python 与 C++ 示例，包含 Bazel 目标与离线测试 | 验证 Python 依赖、Bazel 目标、文档列明的接口及预期结果 |
| [VBOT Blueprints](../blueprints/README.zh-CN.md) | 规划中，无可运行应用 | 按应用验证依赖、部署、预期结果和停止方法 |
| [Agent HTTP MCP](../docs/interfaces/agent/http-mcp.zh-CN.md) | 契约已整理；最低固件／运行时版本尚未公布 | 检查固件兼容性与 Agent 到工具调用；本仓不包含服务可执行代码 |
| [设备端 Skills／AGENTS.md API](../docs/interfaces/agent/content-api.zh-CN.md) | 编写规范与 HTTP 内容契约已整理；最低固件／运行时版本尚未公布 | 检查路由可用性及用户内容路径；写入前备份、写入后比较读回，并在新 Turn 使用内容 |
| [Coding Agent Skills](../skills/README.zh-CN.md) | 按范围检查环境，或完成 SDK 准备、部署与只读状态订阅；共享 Codex／Claude Code 发现链接 | 在使用的 harness 中确认发现与调用 |
| [能力索引](../catalog/README.zh-CN.md) | 本地 JSON 查询与校验 | 格式版本、引用及发布范围检查，不是在线设备发现 |
| 设备 / 固件 | 在选定设备上确认 | 按接口指南核对型号及已安装固件 |

构建和运行应用时，使用相互匹配的固件、SDK、Schema 及原生运行库版本。

## 机器人镜像与 schema pack 行

EDU schema pack 用稳定的行号标识公开路由；随包分发的 `manifest/edu_public_allowlist.json`
在 `map_rows` 中列出这些行。机器人镜像决定其访问控制允许哪些行，因此请按应用使用的行
核对镜像。

| 机器人镜像 | 允许的 schema pack 行 | 说明 |
| --- | --- | --- |
| `v5.0.21-2026091102edu`（早期试点设备） | 1–49、51–52 | 服务行 17（`/get_jpeg_images`）与 32（`/rcp/function_input`）存在但被禁用；话题行 50、53–56 不在该镜像的 ACL 中 |
| 带 EDU 路由器的 PVT-EDU 软件（2026-09-24 起构建） | 1–55 | 缺少行 56（`uwb/audio_done`） |

带 EDU 路由器的软件会发布 `/opt/vita/aorta/edu/edu_session_peer.json5`，可用
`test -r /opt/vita/aorta/edu/edu_session_peer.json5` 检查。有该文件时，EDU 程序之间还可以
使用其他任意话题、服务和动作名，client 与 peer 模式均可，并可用
`/opt/vita/aorta/edu/foxglove_bridge.yaml` 配置 Foxglove bridge。没有该文件时，会话只支持
client 模式，允许行以外的名称会被丢弃。

`edu-sdk-2026.9.24` 的 pack 有 56 行，因此行 50（`system/sm_status`）、53
（`perception/detections2d`）、54（`perception/poses`）、55（`audio/uwb_adpcm_segment`）、
56（`uwb/audio_done`）需要更新的机器人镜像；行 17、32 在该镜像上同样不可用。
ACL 拒绝是静默丢弃：不可用的行表现为没有提供方或超时，而不是错误信息。

### 设备端版本查询

| 命令 | 结果 |
| --- | --- |
| `cat /etc/version` | 打印已安装的软件镜像，例如 `v5.0.21-2026091102edu` |
| `aorta --version` | Release 中的 CLI 会打印其版本；机器人上的 CLI 打印 `0.0.0+unstamped`，请改用 `cat /etc/version` |
| `zenohd --version` | 机器人上的路由器打印 `0.0.0+unstamped`，不是可用版本；请改用 `cat /etc/version` |

## C++ 示例配套

[C++ SDK 指南](../packages/aorta/cpp/README.zh-CN.md)固定使用 SDK 2026.9.23／ABI 12 与 EDU Schema 2026.9.24-v4，
支持 Ubuntu 22.04 x86_64／aarch64 制品和 C++17。示例使用 Bazel 本地原生编译，不提供交叉编译工具链。
相机 RGB 解码为可选 FFmpeg 目标，需要目标架构的开发库和运行库；基础示例不依赖 FFmpeg。
构建、SDK 版本匹配与目标设备实际接口可用性是不同检查项。
