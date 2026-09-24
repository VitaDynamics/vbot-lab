# 更新记录

<p align="center"><a href="CHANGELOG.md">English</a> | 中文</p>

## Unreleased

- SDK 指南改用 `edu-sdk-2026.9.24`：Aorta 2026.9.23（C++ `find_package` 可不带版本号）与 EDU schema pack 2026.9.24，其 `vbot_edu_msgs` wheel 钉该 Aorta 版本并附带 `LICENSE`/`NOTICE`。Release 在 PyPI 的 FlatBuffers wheel 旁附上其许可证文本。
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
