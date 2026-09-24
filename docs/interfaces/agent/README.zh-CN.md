# Agent 接口能力

<p align="center"><a href="README.md">English</a> | 中文</p>

本章节介绍设备端 `vbot-agent-harness` 的 HTTP MCP 工具、运行时 Skills、
开发者提供的 `AGENTS.md` 指令，以及注入用户内容的 HTTP API。
适用场景为单设备、单个可信开发者，使用 S100 上的 `vbot` 账户。
本仓库当前发布范围仅为 [foot_quadruped](../../robots/foot_quadruped/README.zh-CN.md)，
不能据此推断 `wheel_quadruped` 或 `foot_humanoid` 已开放这些能力。

## 能力划分

| 能力 | 开发者负责 | Agent 行为 | 详细说明 |
| --- | --- | --- | --- |
| HTTP MCP | 在 S100 上运行开发者自己的 HTTP MCP 服务 | EDU 运行时作为 MCP 客户端，通过固定内网入口发现并调用工具 | [HTTP MCP 契约](http-mcp.zh-CN.md) |
| 设备端 Skills | 编写 `SKILL.md`，通过 Skills API 上传 | 发现可复用知识／流程，并在匹配的请求中激活 | [编写规范](customization.zh-CN.md)、[内容 API](content-api.zh-CN.md) |
| 设备端 AGENTS.md | 编写长期偏好，通过 AGENTS.md API 替换用户层内容 | 在后续 Turn 构建提示时合并指令 | [编写规范](customization.zh-CN.md)、[内容 API](content-api.zh-CN.md) |

这些能力与 Aorta Python SDK 分开：MCP 让 Agent 调用开发者工具，Aorta 接口提供机器人能力。
本契约不定义 Aorta 路由或 ROS2 映射。工具使用设备文档列明的接口。
Skills 与 `AGENTS.md` 提供指令，不授予额外的操作系统权限。

## 区分内容的使用方

| 内容 | 使用方 | 位置／交付方式 |
| --- | --- | --- |
| Coding Agent Skill | 开发者侧编程 harness，例如 Codex 或 Claude Code | [`skills/`](../../../skills/README.zh-CN.md)；本地环境检查 Skill |
| 设备端 Skill | EDU `vbot-agent-harness` | 开发者编写 `SKILL.md`，通过 `/api/skills/{name}` 注入 |
| 设备端 AGENTS.md | EDU `vbot-agent-harness` | 开发者编写指令，通过 `/api/agents-md` 注入 |
| 仓库 AGENTS.md | 使用或贡献 vbot-lab 的 Coding Agent | [共享任务路由与指令](../../../AGENTS.zh-CN.md)；不是设备定制内容 |

## 版本兼容性

API 可用性取决于设备的固件及运行时版本。
接入前请查看[兼容矩阵](../../../release/compatibility.zh-CN.md)，当前尚未公布最低支持版本。
通过[接入指南](../../guides/agent-integration.zh-CN.md)检查 API 响应、内容路径及新 Turn 中的行为。
在自己的工作区保留源内容及备份，升级固件前阅读对应版本说明。

本仓库提供接口文档，目前不包含可执行 MCP 服务或可安装的设备 Skill 包。

## 开放边界

- 约定 MCP 入口为 `http://192.168.127.2:18080/mcp`，内容 API 使用
  `http://192.168.127.10:8787`。两者是机器人内部网络上的不同接口契约。
  不得将 `18080` 或 `8787` 端口暴露或转发到校园公网、互联网。
- 使用 `vbot` 账户及文档列明的访问方式，操作不得超出账户已分配的权限。
- MCP 仅承诺已列出的工具子集，不承诺 stdio transport、Resources 或 Prompts。
- 每台设备只有一个约定 MCP 入口。多个工具提供者应在开发者的 S100 服务内聚合，不按多租户托管平台使用。
- MCP 会话请求头只是传输层状态，不是内容 API 的凭证。
- 用户层 Skills 与 `AGENTS.md` 使用[内容 API](content-api.zh-CN.md)注入。
- 本章节聚焦 MCP 与用户内容定制，不是完整的应用会话协议，也不暴露服务管理操作。
