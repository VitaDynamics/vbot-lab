# VBOT Lab

<p align="center"><a href="README.md">English</a> | 中文</p>

**面向 VBOT EDU 机器人的 agent-native 开发工作区。**

[开发文档](docs/README.zh-CN.md) · [Vbot Viewer](docs/guides/vbot-viewer.zh-CN.md) · [社区与支持](docs/community/README.zh-CN.md)

VBOT Lab 汇集面向任务的 Skills、能力索引、Aorta Python SDK、接口定义和参考程序，
用于开发机器人应用。

当前适配的机器人应用版本：**V1.6.0-12**，适用于 `foot_quadruped` EDU。
SDK 与平台配套见[兼容矩阵](docs/compatibility.zh-CN.md)。

## 与 Agent 开始开发

在 Codex 或 Claude Code 中打开本仓库，然后提出任务：

> 检查这台工作站是否具备 VBOT 开发条件。报告已有工具、缺失依赖和发布限制。
> 不要安装软件，也不要连接机器人。

[vbot-dev-setup Skill](skills/vbot-dev-setup/SKILL.zh-CN.md) 提供本地只读清点。
Codex 通过 `.agents/skills/` 发现共享 Skills，Claude Code 使用 `.claude/skills/`；
两者都指向 `skills/`。[AGENTS.md](AGENTS.zh-CN.md) 提供任务路由，
[CLAUDE.md](CLAUDE.zh-CN.md) 导入同一份指令。

调用方式、在自己的应用仓库中使用 Skills、软链接要求和 harness 发现验证，
请参阅 [Agent 快速开始](docs/agents/README.zh-CN.md)。

## 查找所需内容

| 入口 | 用途 | 当前可用状态 |
| --- | --- | --- |
| [Skills](skills/README.zh-CN.md) | Coding Agent 任务流程 | 环境搭建、Python/C++ 应用开发与分层诊断 |
| [Capabilities & Interfaces](catalog/README.zh-CN.md) | 设备范围、接口参考与前置条件 | 能力索引可查询；在选定设备上确认接口可用性 |
| [Recipes](recipes/README.zh-CN.md) | 可复用的单项任务程序 | 按能力组织的 Python 与 C++ 示例，提供 Bazel 目标与离线预览 |
| [VBOT Blueprints](blueprints/README.zh-CN.md) | 完整参考应用 | Python／C++ 只读健康监测及独立应用模板 |
| [Developer Guide](docs/README.zh-CN.md) | 环境、连接、硬件、接口与排障 | 已提供分章节文档，适用范围按版本注明 |

[Aorta Python SDK](packages/README.zh-CN.md) 保持在 `packages/aorta/python/`，
[开放 Schema](schemas/README.zh-CN.md) 保持在 `schemas/`；Schema 已入库，发布版 wheel 安装与运行步骤见 [Python SDK 指南](packages/aorta/python/README.zh-CN.md)。
不提供替代 SDK API，也不猜测设备 topic。

## 运行首个应用

从[快速开始：使用 Python 读取机器人状态](docs/getting-started/README.zh-CN.md)进入。
沿一条主路径完成：准备开发容器、构建并预览 `subscribe-state`、打包固定版本的 ARM64 依赖、
SSH 登录、部署并收到三条解码后的 `/locomotion/status` 消息。
每步注明执行终端、预期结果与排障入口，无需运动或音视频采集。

已经在开发容器中时直接复用，无需在容器内安装 Docker。
构建、预览和打包在容器内完成，部署后的程序在机器人 `vbot` shell 运行；
仅清点或预览通过不代表在线运行成功。

其他路径见 [C++](packages/aorta/cpp/README.zh-CN.md)、
[有线／Wi-Fi 连接](docs/robots/quadruped-common/connection.zh-CN.md)、
[设备 shell 配置](docs/getting-started/device-environment.zh-CN.md)、
[编辑器集成](.devcontainer/README.zh-CN.md)或[排障](docs/troubleshooting/README.zh-CN.md)。
仓库检查属于独立的[贡献流程](#贡献与验证)。

## 范围与安全

当前 EDU 发布对象为 `foot_quadruped`；
`wheel_quadruped` 与 `foot_humanoid` 为后续版本。
共用硬件参数或连接流程不代表软件兼容，请核对[设备指南](docs/robots/README.zh-CN.md)
及[兼容矩阵](docs/compatibility.zh-CN.md)。

当前文档与示例使用 Python／C++ 和 Bazel，包含相机、运控、RCP 和语音访问。
健康监测 Blueprint 提供两种语言实现、Python／C++ 工作区生成及设备部署流程。
在线执行前应检查 SDK 配套关系及设备前提。

开发者侧 Skills 与[设备 Agent API](docs/interfaces/agent/README.zh-CN.md)中的
HTTP MCP、Skill／AGENTS.md 注入能力分开。
本地检查不联系设备，也不改变服务、权限、资源或运动状态。
设备写入与运动操作需具备任务授权，并满足文档列明的前置条件。

## 社区与支持

开发中遇到问题，或有希望支持的新能力？欢迎到 [Vbot 超能社区](https://forum.vbot.cn/)
提问、交流开发经验和分享成果。[社区与支持](docs/community/README.zh-CN.md)
提供对应板块及简短反馈模板。附上复现步骤与必要的脱敏信息，便于大家一起定位，
也能帮助后来者找到答案。

## 贡献与验证

参阅[贡献说明](CONTRIBUTING.zh-CN.md)、[测试](tests/README.zh-CN.md)
及 [Agent 工作流检查](tests/agent-scenarios/README.zh-CN.md)。
仓库检查在本地执行，不联系设备。
宿主机或 CI runner 运行 `python3 tools/run_checks.py --scope repository`；
Recipe 检查、Bazel 和打包在开发容器内完成，CI 同样遵守。
统一规则见[执行位置](docs/development/README.zh-CN.md)。
漏洞报告方式见[安全说明](SECURITY.zh-CN.md)。

## 许可证

Copyright (c) 2026 VitaDynamics

除另有说明外，本仓库的代码、文档、接口定义与示例均采用
[Apache License, Version 2.0](LICENSE)（`Apache-2.0`），署名信息见 [NOTICE](NOTICE)。

协议允许商业使用、修改和再分发。再分发时须附带许可证、保留适用的署名声明，
并标明修改过的文件。协议不要求衍生作品开源；除第 6 条规定的例外外，不授予商标使用权。

第三方组件保留各自的许可证。另行分发的 SDK 包、固件与容器镜像适用其随附的许可条款，
本仓库许可证不会重新授权这些内容。正式条款以英文 LICENSE 文件为准，
此摘要不增加或替代协议条款。
