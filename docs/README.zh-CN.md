# Developer Guide

<p align="center"><a href="README.md">English</a> | 中文</p>

VBOT EDU 机器人的环境搭建、设备连接与应用开发说明，按下面章节阅读。
Codex 或 Claude Code 配置见[与 Agent 开始开发](agents/README.zh-CN.md)。

搭建或升级环境前，先查阅[版本与兼容性](compatibility.zh-CN.md)，确认适配应用版本、
SDK 下载入口及组件配套要求。

1. [平台概览](overview/README.zh-CN.md)：支持范围与架构。
2. [设备类型指南](robots/README.zh-CN.md)：选择设备类型，确认 EDU 发布范围。
3. [硬件参考](hardware/README.zh-CN.md)：明确适用范围，按实际情况共用规格。
4. [快速开始](getting-started/README.zh-CN.md)：通用环境搭建与首次运行流程。
5. [开发流程](development/README.zh-CN.md)：Bazel、连接设备及部署。
6. [接口参考](interfaces/README.zh-CN.md)：Aorta／Python 接口及 [Agent 能力](interfaces/agent/README.zh-CN.md)。
7. [功能指南](guides/README.zh-CN.md)：接口流程、自启动及 [Agent 接入](guides/agent-integration.zh-CN.md)。
8. [常见问题](troubleshooting/README.zh-CN.md)：定位环境、连接及版本问题。
9. [社区与支持](community/README.zh-CN.md)：提问、分享应用，以及提供可复现的反馈。

当前 EDU 发布范围仅为 `foot_quadruped`，请从[四足机器狗指南](robots/foot_quadruped/README.zh-CN.md)进入；
其他类型目录为后续版本预留。
通用章节保持现有路径，机型差异放在 `robots/<robot_type>/`，可复用硬件规格放在 `hardware/`。
新增设备类型或硬件版本前，参阅[文档结构约定](robots/README.zh-CN.md)。

当前文档包含硬件规格、Agent 接口与开发环境配置；尚无可运行实现的功能标记为规划中或待接入。

## 继续构建

- [Vbot Viewer](guides/vbot-viewer.zh-CN.md)：在浏览器中查看与编辑 URDF 模型，与设备实时数据查看分开。
- [机器人模型](../assets/robots/README.zh-CN.md)：按设备类型组织的资源位置及状态，`foot_quadruped` 已附带 URDF 与网格。

- [设备资源](resources/README.zh-CN.md)：身体／头部轨迹、表情 ID 与灯光模式，独立于 RCP 编排。

- [Capabilities & Interfaces](../catalog/README.zh-CN.md)：查询任务可用状态、设备范围与事实来源。

- [Aorta Python SDK](../packages/README.zh-CN.md)：Aorta Python SDK 入口与兼容要求。
- [Recipes](../recipes/README.zh-CN.md)：单项任务 Python／C++ 参考程序与 Bazel 目标。
- [VBOT Blueprints](../blueprints/README.zh-CN.md)：完整参考应用，目前处于规划阶段。
- [Skills](../skills/README.zh-CN.md)：供 Codex 与 Claude Code 使用的本地环境检查流程及配置说明。
- [Interface Definitions（接口定义）](../schemas/README.zh-CN.md)：已入库的开放 Aorta Schema 与版本化生成绑定。
