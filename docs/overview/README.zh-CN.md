# 平台概览

<p align="center"><a href="README.md">English</a> | 中文</p>

VBOT Lab 汇集 VBOT EDU 机器人的开发工具与接口参考。
设备指南按四足机器狗、四轮机器狗与双足机器人组织。
当前 EDU 发布范围仅为四足机器狗（`foot_quadruped`），已有 Aorta Python SDK 发布版 wheel、开放 Schema 源码与可执行 Recipes。
当前提供本地环境检查 Skill 与可查询的能力索引。
其他设备类型在[设备类型指南索引](../robots/README.zh-CN.md)中保留后续版本入口。
目录入口存在不代表所有设备型号均已获得支持。
支持的具体设备型号和固件版本以[兼容矩阵](../../release/compatibility.zh-CN.md)为准。

## 从任务到验证

- [与 Agent 开始开发](../agents/README.zh-CN.md)：Codex／Claude Code 入口与外部项目使用方式。
- [Skills](../../skills/README.zh-CN.md)：任务流程，从本地环境检查开始。
- [Capabilities & Interfaces](../../catalog/README.zh-CN.md)：发布范围与权威接口参考。
- [Developer Guide（开发者指南）](../README.zh-CN.md)：环境搭建、设备连接与接口文档。
- [Aorta Python SDK](../../packages/README.zh-CN.md)：基于 Aorta Python SDK 访问设备，已有发布版 wheel 安装说明。
- [Recipes](../../recipes/README.zh-CN.md)：单项任务参考程序，已有 Python／C++ 源码与 Bazel 目标。
- [VBOT Blueprints](../../blueprints/README.zh-CN.md)：完整参考应用，目前处于规划阶段。

Skills 负责任务路由，能力索引指向事实，Recipes 与工具提供实现，测试提供证据。
Aorta 保持原有包名与 API；Recipes 与 Blueprints 共用 Python 优先、基于 Bazel 的开发路径。

## 硬件与接口范围

传感器参数与安装位置请在[传感器规格索引](../hardware/sensors.zh-CN.md)中按类型选择。
现有参数由 `foot_quadruped` 与 `wheel_quadruped` 共用，不适用于 `foot_humanoid`；
这一硬件范围不扩大 EDU 软件支持范围。

- Schema 描述通信契约；SDK 提供调用能力；Recipes 实现单项任务；Blueprints 将接口组合成应用。
- 开发主线采用 Aorta；只记录确实存在并经过验证的 ROS2 映射。
- [设备 Agent 接口](../interfaces/agent/README.zh-CN.md)包含开发者自有 HTTP MCP 工具与 Skill／AGENTS.md 内容注入，其契约与 Aorta SDK、开发者侧 Coding Agent Skill 分开。
- Recipes 使用 Python／C++，覆盖文档明确列出的公开接口，包括语音输入。
- Docker 用于开发工作站，设备程序使用 `vbot` 账户。
- Schema 存在不代表接口已在设备开放。
