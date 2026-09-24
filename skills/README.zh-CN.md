# Skills

<p align="center"><a href="README.md">English</a> | 中文</p>

面向 Codex、Claude Code 等开发者侧 Coding Agent 的任务流程。
本目录是唯一维护源；`.agents/skills/` 与 `.claude/skills/` 都通过相对软链接指向这里。

## 当前工作流

[vbot-dev-setup](vbot-dev-setup/SKILL.zh-CN.md) 引导 Python 或 C++ 开发起步：
准备 SDK、Bazel 构建、SSH 设备配置、部署，最后完成有时限的只读状态订阅。
复用 SDK 与部署指南，设备不需要仓库副本或 Bazel。
仅要求清点或咨询时保持该范围，不扩展为完整搭建。
清点程序使用 Python 3.10+ 标准库，不安装软件、不启动容器、不联系设备，也不修改配置。

Skill 与离线工具已实现；确认 Skill 出现在所用 harness 中后，可要求检查本地环境，
或完整搭建直到收到首批状态消息。
更多开发场景见[工作流检查](../tests/agent-scenarios/README.zh-CN.md)。
配置和外部项目使用方式见 [Agent 快速开始](../docs/agents/README.zh-CN.md)。

## 规划中的工作流

Python 应用开发与更全面的设备诊断 Skill 仍处于规划阶段。
后续引用[能力索引](../catalog/README.zh-CN.md)、[客户端开发库](../packages/README.zh-CN.md)、
[Recipes](../recipes/README.zh-CN.md)及[开发者指南](../docs/README.zh-CN.md)，不重复维护接口定义。

这些 Skills 不是设备端 `vbot-agent-harness` 内容。
设备 Skill／AGENTS.md 的编写和注入使用[设备内容 API](../docs/interfaces/agent/content-api.zh-CN.md)。
