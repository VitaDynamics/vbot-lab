# VBOT Lab Agent 指令

<p align="center"><a href="AGENTS.md">English</a> | 中文</p>

帮助用户开发 VBOT EDU 机器人应用。根据任务按需读取相关资料；本仓库不是设备运行时。

## 任务路由

| 用户任务 | 从这里开始 |
| --- | --- |
| 检查或搭建开发环境 | [vbot-dev-setup](skills/vbot-dev-setup/SKILL.zh-CN.md)，再查阅[环境指南](docs/getting-started/README.zh-CN.md) |
| 配置 vbot 设备 shell 或检查 Aorta／ROS 2 访问 | [设备环境](docs/getting-started/device-environment.zh-CN.md)、[vbot-dev-setup](skills/vbot-dev-setup/SKILL.zh-CN.md)与[接口范围](docs/interfaces/aorta-ros2.zh-CN.md) |
| 查找开放能力、选择接口 | [能力索引](catalog/README.zh-CN.md)，再读取对应接口文档 |
| 选择应用／SDK 版本或核对兼容性 | [版本与兼容性](docs/compatibility.zh-CN.md)，再查阅所链接的 SDK 指南 |
| 读取硬件遥测或相机数据 | [传感器](docs/interfaces/sensors.zh-CN.md)或[相机](docs/interfaces/cameras.zh-CN.md)，只选择所需数据流 |
| 检测人体、见人问候或使用人体关键点 | [感知接口](docs/interfaces/perception.zh-CN.md)|
| 接收音频、识别文本或语音事件 | [audio](docs/interfaces/audio.zh-CN.md)，统一音频帧、ASR、语音事件与 UWB 输入结束 |
| 观察或控制运动 | [运动](docs/interfaces/locomotion.zh-CN.md)，区分状态／报告订阅与控制输入 |
| 观察系统／显示状态或使用耳灯 | [系统与外设](docs/interfaces/system-peripherals.zh-CN.md) |
| 编排、执行或追踪 RCP 任务 | [DAG 编写](docs/guides/rcp-dag.zh-CN.md)、[RCP 预设目录](docs/guides/rcp-presets.zh-CN.md)，再看 [RCP](docs/interfaces/rcp.zh-CN.md)；区分预设 Goal 与节点，保留资源和生命周期约束 |
| 选择身体／头部轨迹、屏幕表情或灯光模式 | [设备资源](docs/resources/README.zh-CN.md)；RCP 节点字段见 [NodeCommand 参考](docs/interfaces/rcp-commands.zh-CN.md) |
| 检查里程计、建图／保存地图或定位 | [建图与定位](docs/guides/mapping-localization.zh-CN.md)，区分只读检查与模式切换 |
| 开发 Python 应用 | [Aorta Python SDK](packages/aorta/python/README.zh-CN.md)、[Recipes](recipes/README.zh-CN.md)与所选能力 |
| 开发 C++ 应用 | [Aorta C++ SDK](packages/aorta/cpp/README.zh-CN.md)、[Recipes](recipes/README.zh-CN.md) 及所选能力；显式构建 :main_cpp |
| 设备重启后自动启动用户程序 | [用户程序自启动](docs/guides/user-autostart.zh-CN.md)，保留已有启动命令，区分开机启动与崩溃恢复 |
| 了解设备或连接设备 | [设备指南](docs/robots/README.zh-CN.md)，先确认用户的设备类型 |
| 查看机器人模型、关节或 URDF | [Vbot Viewer](docs/guides/vbot-viewer.zh-CN.md)，再查阅[机器人模型](assets/robots/README.zh-CN.md)；先读取 model.json 可用状态，不假定本地模型文件存在 |
| 查找背部安装尺寸或机械臂转接板 CAD | [机器狗共用背部安装参考](docs/hardware/quadruped-common/back-mounting.zh-CN.md)，适用于 foot_quadruped 与 wheel_quadruped，不适用于 foot_humanoid；不把机械适配等同于负载或机械臂控制支持 |
| 获取帮助或整理问题反馈 | [社区与支持](docs/community/README.zh-CN.md)，整理最少且脱敏的反馈供用户审阅，不自动发帖 |
| 编写或注入设备 Skill／AGENTS.md | [设备内容 API](docs/interfaces/agent/content-api.zh-CN.md)，不是开发者侧 Skills |
| 修改 VBOT Lab 仓库 | [贡献说明](CONTRIBUTING.zh-CN.md)与相关测试 |

在其他应用工作区使用时，遵循 [Agent 快速开始](docs/agents/README.zh-CN.md)。
使用链接 Skill 的相对资源前，先解析其实际所在的仓库路径。

## 事实与范围

- 当前 EDU 发布对象为 `foot_quadruped`。其他设备类型处于规划阶段，共用硬件或连接指南不改变这一范围。
- 当前适配的机器人应用版本为 `V1.6.0`，由设备配置的 `application_version` 记录。它与 SDK、Schema、系统镜像及外设固件版本分别管理，不推断更早或后续应用版本兼容。
- 能力目录是索引，不是在线可用性证明。未知固件／SDK 版本、路由与 ROS2 映射应保持未知，不得猜测。
- 使用 Python SDK 指南指定的发布版 wheel 配套与已入库的开放 Schema，保留 Aorta 包名与 API。Recipes 提供离线预览及显式设备执行，构建成功不代表在线兼容。
- 设备 Aorta CLI 访问与 SDK 接入独立。ROS 2 使用设备本机 bridge 子集，遵循已整理的映射与限制，不凭同名推测。
- 字段和类型以 Schema 为准，行为与安全条件以所链接的接口文档为准；Skills 引用这些来源，不重复维护。
- 开发者侧 Coding Agent Skills 位于 `skills/`；`.agents/skills/` 与 `.claude/skills/` 暴露同一份来源，不上传给 `vbot-agent-harness`。
- 应用代码使用 Python 或 C++，统一采用 Bazel。开发容器运行在工作站，设备程序使用 `vbot` 账户。

## 执行与证据

- 环境清点工具离线、只读；不安装工具、不拉取镜像、不访问 Docker、不通过 SSH 连接，也不联系机器人 API。设备配置和在线只读采样是设备指南中按用户请求单独执行的步骤。
- 设备操作优先使用 SSH 公钥免密登录。按[连接指南](docs/robots/quadruped-common/connection.zh-CN.md)复用已有可用配置；尚未配置时先引导用户完成，再从后续实际执行命令的环境验证非交互登录。不自动回退到内嵌密码。安装公钥属于配置修改，不属于只读检查；不向设备复制私钥，也不覆盖已有密钥。
- 使用用户选定的设备地址或 SSH 别名。SSH 不可达或连接被拒绝时停止，提示先连接设备或提供实际 IP。认证与主机密钥错误分别说明，不扫描其他设备，也不绕过主机密钥核验。
- 操作范围应符合用户请求。设备写入、部署、内容注入或运动前，明确任务授权、目标设备／版本及文档要求的前置条件。运动还需确认安全场地与停止方法。
- 依赖缺失或接口不可用时报告阻塞，不自行编造 API，也不调整设备权限、配额或服务。
- Viewer 模型编辑／姿态不是机器人控制指令；区分本地变体与共享关键帧修改，不从网页控件猜测控制 API，也不将导出模型自动部署到设备。
- 使用问题仍未解决时，可推荐对应社区板块并整理反馈草稿；未经明确请求不发布帖子或上传日志，漏洞细节不进入公开渠道。
- 区分本地检查、构建／测试、harness 会话验证与实机验证；构建成功不代表设备操作成功。
- 默认测试不联系或控制真实设备。参阅[测试范围](tests/README.zh-CN.md)和 [Agent 工作流检查](tests/agent-scenarios/README.zh-CN.md)。

## 文档与修改

文档默认英文，配套 `.zh-CN.md` 页面及同语言链接。
章节直接说明任务、前置条件、操作步骤与预期结果。项目定位保留在首页，不在各章重复受众描述。
优先保证功能使用流程正确、完整。使用指南不放设备测试报告、性能或精度实测；
保留接口契约、使用限制、完成条件与排障步骤。
主体统一使用 `VBOT EDU robots`／`VBOT EDU 机器人`，保持大小写。
调整结构或共用设备文档前，阅读[贡献说明](CONTRIBUTING.zh-CN.md)。
运行 `python3 tests/check_repository.py`、`python3 tests/test_agent_workspace.py`
及适用的 Bazel 目标进行验证。未收到请求时不提交或发布。
