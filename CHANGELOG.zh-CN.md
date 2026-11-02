# 更新记录

<p align="center"><a href="CHANGELOG.md">English</a> | 中文</p>

## Rel/V1.6.0 — 2026-11-02

V1.6.0 最终正式版汇总 VBOT Lab 自建仓以来提供的能力。
当前支持 `foot_quadruped` EDU，适配机器人应用 **V1.6.0-15**。
开发请从 **`release/V1.6.0`** 分支开始，操作见[快速开始](docs/getting-started/README.zh-CN.md)。
`Rel/V1.6.0` 标记正式源码快照；组件配套见 [release.json](catalog/release.json)及其关联的 SDK 指南。

### 从环境搭建到设备部署

- 提供默认英文、配套简体中文的文档，共用机器狗连接指南，并按设备类型明确适用范围；四轮和双足 EDU 软件不属于本次发布范围。
- 补全开发容器搭建、复用运行中或已停止的容器、编辑器接入与 ARM64 交叉编译流程；应用在开发容器内构建和打包，不在机器人端编译。
- 覆盖有线连接、通过 Vbot App 配置 Wi-Fi、在已绑定设备的 App 中进入设置 → 关于查看当前 Wi-Fi IP、SSH 登录及公钥配置，再完成设备端 Aorta 与已开放 ROS 2 bridge 接口所需的 shell 环境配置。
- 跑通首个 Python 应用的完整路径：构建与预览、源码和 wheel 打包、SSH 传输、设备 venv 创建及机器人状态读取。C++ 按 ARM64 可执行文件与依赖库部署，设备无需仓库副本或 Bazel。
- 补充受限网络下的 Bazel 依赖包准备与离线构建方法，分清构建、打包和设备运行步骤。
- 补充 `/userdata/vbot/init.sh` 用户程序自启动流程，包括显式运行环境、日志、重启后的检查、更新与停用，见[用户自启动](docs/guides/user-autostart.zh-CN.md)。

### Agent-native 工作区与应用工具

- 将工作区组织为 Skills、机器可读能力索引、SDK 指南、Schema、单项 Recipes、完整 Blueprints 与独立应用模板。
- 通过 `AGENTS.md` 为 Codex 与 Claude Code 提供共享指令，`.agents/skills/`、`.claude/skills/` 指向同一份 Skill 来源；同时说明在本仓库与用户自己的应用工作区内使用的方法。
- 提供 `vbot-dev-setup`、`vbot-app-dev`、`vbot-diagnose`，分别覆盖环境搭建、Python／C++ 应用开发与分层诊断，沿用用户的语言、已有项目及明确的设备操作范围。
- 增加能力查询、环境清点、Python／C++ 项目生成、应用打包和结构化诊断工具；区分本地清点、SDK 就绪、设备环境与实际收数，不以某一步成功代替后续步骤。

### 机器人开放接口与数据

- 提供开放 Aorta Schema 及受支持 bridge 路由使用的 ROS 2 定义，按传感器、相机、Perception、Audio、运动、系统与外设、RCP、SLAM 八类说明准确路由名、类型、方向及通信方式。
- 覆盖电池、IMU、雷达、UWB、GNSS 和舵机遥测，以及相机标定、H.265 视频、AprilTag 和 JPEG 获取；明确 JPEG 请求尺寸用于选择最接近的已启用通道，以响应的实际尺寸为准。
- 说明内置目标／人体检测与人体关键点输出，为人体出现触发交互提供开发入口；区分目标检测、AprilTag 结果、人体关键点与机器人自身位姿。
- 梳理本体麦克风音频、UWB 音频、ASR 结果和输入结束事件，以及 ASR 来源的区分方式；将扬声器 PCM 输入、语音策略查询／控制与音频采集分别说明。
- 说明运动状态、控制 topic、动作报告、站起／安全趴下流程、控制使能及跟随／导航服务；区分请求受理、任务终态与实际设备状态。
- 覆盖系统／显示状态、耳灯亮度与灯光服务、应用版本查询和低功耗控制，区分只读观察与改变设备状态的操作。
- 提供完整的[建图与定位流程](docs/guides/mapping-localization.zh-CN.md)：模式切换、采集、地图保存与重载、重定位，以及地图、里程计、位姿、变换的使用和坐标系语义。
- 说明[设备 Agent 接口](docs/interfaces/agent/README.zh-CN.md)：HTTP MCP 工具接入、动态新增／编辑外部 MCP 连接、启停与发现刷新，以及设备 Skill／AGENTS.md 内容 API 的上传、读回、备份、删除与恢复；设备运行时内容与 Coding Agent Skills 分开。

### RCP 编排与可复用设备资源

- 解释 `DagPresetRef` 和自定义 `DagSpec`、图／节点字段、`NodeCommand` 类型、参数范围、依赖、并行、超时、前置条件、资源占用与清理。
- 提供预设引用清单，以及独立的身体／头部轨迹、表情 ID、灯光模式目录；说明资源名和 ID 如何关联直接接口与 RCP 节点，使用时无需访问设备安装目录。
- 补充可配置运动参数、受支持的准备与姿态转换，让应用基于通用契约编排受支持行为，不局限于复制单一握手场景配置。
- 说明何时直接调用能力、何时使用 RCP，以及任务提交、反馈、终态、取消与追踪关联，见 [DAG 编写](docs/guides/rcp-dag.zh-CN.md)和[控制路径](docs/guides/control-paths.zh-CN.md)。

### Python／C++ 示例与完整应用

- 按八类接口提供统一使用 Bazel 构建的 Python／C++ Recipes，包括相机读取与采集、感知和音频输入、运动、系统／版本读取、RCP DAG 提交与取消、SLAM 只读数据。
- 提供结合机器人状态、电池与系统消息的只读健康监测 Blueprint，包含 Python／C++ 实现、模拟、独立工作区生成、打包与部署说明。
- 补全 SDK 序列化测试、离线预览、有界采样、显式运动／采集选项、资源清理与可操作的错误提示；默认预览和测试不联系机器人。
- SDK 与生成绑定通过独立 Release 附件分发，配套清单、校验值和许可证。下载完整配套后可校验并本地安装；首次环境搭建仍需按 SDK 指南完成下载。

### 可视化、机器人模型与硬件资料

- 补充 [Foxglove](docs/guides/foxglove.zh-CN.md) bridge 启动、设备环境、topic 选择及导出命名规则，覆盖有线直连与 Wi-Fi SSH 隧道接入。
- 引入 [Vbot Viewer](docs/guides/vbot-viewer.zh-CN.md) 浏览器模型查看、URDF 编辑和导出流程，明确其与实时消息可视化、真实机器人控制的区别。
- 在 `assets/robots/foot_quadruped/` 提供 VbotBaboEDU URDF 变体及关联网格资源，包含头部关节舵机限位修正，并说明模型可用状态及本地／在线资源的区别。
- 补充四足与轮式四足共用的传感器规格、背部安装尺寸、安装图纸和转接板 CAD；共用硬件资料不代表另一设备类型的软件已开放。

### 社区、安全与协作

- 引导使用问题、开发经验与能力建议优先进入 [Vbot 超能社区](https://forum.vbot.cn/)，提供先搜索、再反馈的流程及脱敏模板；具体代码／文档缺陷通过仓库 Issue／PR 协作。
- 提供技术支持与私密漏洞反馈邮箱 `vbot-edu@vbot.cn`，说明首次登录修改密码、公钥 SSH、连接配置的安全存放，以及不在公开反馈中披露设备标识或凭据。
- 仓库代码、文档、接口和公司自有模型／硬件资料采用 Apache-2.0，补充 `Copyright (c) 2026 VitaDynamics`、署名及第三方许可说明。
- 完善贡献指南、维护者／CODEOWNERS、Issue／PR 模板及 CI，覆盖双语文档、索引／Schema 一致性、Python／C++ 构建、应用打包与不连接机器人的 SDK 集成检查。

## V1.6.0

适配机器人应用 `V1.6.0` 的源码快照。SDK 制品仍通过独立的 `edu-sdk-2026.9.24`
GitHub Release 下载；本次源码 tag 不创建额外的 Release。

- 将版本说明统一放入 `docs/compatibility.zh-CN.md`，在能力索引中记录适配应用版本。
- 补充四足与轮式四足共用的背部安装图纸和转接板 CAD。
- 公布私密安全反馈邮箱，由仓库管理员担任维护者及代码评审负责人。

- 在 `assets/robots/foot_quadruped/` 附带 VbotBaboEDU 的 URDF、其变体与引用的 STL 网格；`model.json` 列出入口文件与网格。
- SDK 指南改用 `edu-sdk-2026.9.24`：Aorta 2026.9.23（C++ `find_package` 可不带版本号）与 EDU schema pack 2026.9.24，其 `vbot_edu_msgs` wheel 钉该 Aorta 版本并附带 `LICENSE`/`NOTICE`。Release 在 PyPI 的 FlatBuffers wheel 旁附上其许可证文本。`edu-sdk-2026.9.24` 经真机验证后转为正式版本，不再是预发布。
- 说明 EDU 路由器：client 与 peer 会话文件、EDU 程序之间共享的任意名称、发布的 Foxglove bridge 配置，以及离机开发使用 `zenohd` 1.10.x。
- 移除面向维护者的发布手册以及发布、schema 同步 workflow；release 不再附带 ROS 2 bridge bundle。
- `schemas/ros2/` 只保留公开 bridge 路由使用的 ROS 2 定义（原 375 个中的 152 个），以 `routes.json` 取代路由清单、`MANIFEST.json` 取代 `SYNC_MANIFEST.json`，第三方许可证见 `THIRD_PARTY_NOTICES.txt`；由 `tests/check_schemas.py` 校验。
- 工作站上的 EDU 会话文件副本放在 `~/.config/vbot/robots/<robot-alias>/`；`.gitignore` 与仓库检查拒绝会话文件、凭据字典和密钥。
- 首次登录时修改 `vbot` 初始密码。
- 引入 Agent-native 的 VBOT Lab 工作流：共享 AGENTS 指令、Claude Code 导入入口，以及共用一份来源的 Codex／Claude Code Skill 发现软链接。
- 添加 vbot-dev-setup Skill，支持按范围检查环境，或完成 SDK 准备、构建、部署与只读状态订阅；提供带格式版本的能力索引和离线测试。
- 在 `packages/aorta/` 提供 Aorta Python 与 C++ SDK 接入指南，在 `schemas/` 提供 EDU Schema 定义，在 `recipes/` 提供带 Bazel 构建目标的 Python／C++ 示例。
- 补充 Python 源码与 wheel 部署、C++ 可执行文件与动态库部署流程；设备均无需仓库副本或 Bazel。
- 完整应用 Blueprints 仍处于规划阶段，尚不是可运行应用。
- 补充 `foot_quadruped` 与 `wheel_quadruped` 共用的中英双语有线连接与 SSH 登录指南，包含英文标注接线图、电脑网卡配置和连接排查；EDU 发布范围保持不变。
- 明确设备连接要求及网络安全注意事项。
- 补充设备 HTTP MCP 与 Skill／AGENTS.md 注入 API，提供上传、读回及接入检查，区分设备内容与 Coding Agent Skill。
- 按标准设备类型组织 EDU 指南；当前发布范围限定为 `foot_quadruped`，其他类型为后续版本预留。
- 两类机器狗共用一份传感器规格，原传感器路径保留为适用范围索引。
- 明确仓库面向各类 VBOT EDU 机器人的开发者，单独界定设备支持情况与硬件规格适用范围。
- 在硬件参考中加入中英双语的 EDU 传感器规格。
- 初始化文档、Schema、Python SDK、示例、Skill 和工具目录。
- 添加现有 EDU 开发镜像的 Compose 与编辑器集成配置。
- 添加仓库结构与本地文档链接检查。
- 文档默认使用英文，配套简体中文版和语言切换入口。
- 检查双语配对、同语言导航及两版代码示例的一致性。
