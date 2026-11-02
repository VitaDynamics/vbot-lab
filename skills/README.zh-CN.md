# Skills

<p align="center"><a href="README.md">English</a> | 中文</p>

面向 Codex、Claude Code 等开发者侧 Coding Agent 的任务流程。
本目录是唯一维护源；`.agents/skills/` 与 `.claude/skills/` 都通过相对软链接指向这里。

## 当前工作流

[vbot-dev-setup](vbot-dev-setup/SKILL.zh-CN.md) 引导 Python 或 C++ 开发起步：
准备 SDK、Bazel 构建、SSH 设备配置、部署，最后完成有时限的只读状态订阅。
复用 SDK 与部署指南，设备不需要仓库副本或 Bazel。
纯仓库检查可在宿主机或 CI runner 执行，构建、预览和打包始终在配套开发容器内完成，
参阅[执行位置](../docs/development/README.zh-CN.md)。
仅要求清点或咨询时保持该范围，不扩展为完整搭建。
清点程序使用 Python 3.10+ 标准库，不安装软件、不启动容器、不联系设备，也不修改配置。

Skill 与离线工具已实现；确认 Skill 出现在所用 harness 中后，可要求检查本地环境，
或完整搭建直到收到首批状态消息。
更多开发场景见[工作流检查](../tests/agent-scenarios/README.zh-CN.md)。
配置和外部项目使用方式见 [Agent 快速开始](../docs/agents/README.zh-CN.md)。

[vbot-app-dev](vbot-app-dev/SKILL.zh-CN.md) 用于开发或扩展独立的 Python/C++ 应用、选择接口，
并准备本地部署包。
不会因为打包成功就执行部署。

[vbot-diagnose](vbot-diagnose/SKILL.zh-CN.md) 用于排查已有应用的环境、SDK／链接或无数据问题。
它显式选择诊断层级，区分超时与接口不支持，不自动修复或连接设备。

各工作流复用索引、SDK 和相关指南，不重复维护接口约定；无需 Skill 也可直接调用工具。
在其他项目中只链接需要的工作流，并保留已有配置，参阅
[Agent 快速开始](../docs/agents/README.zh-CN.md)。

这些 Skills 不是设备端 `vbot-agent-harness` 内容。
设备 Skill／AGENTS.md 的编写和注入使用[设备内容 API](../docs/interfaces/agent/content-api.zh-CN.md)。
