# VBOT Blueprints

<p align="center"><a href="README.md">English</a> | 中文</p>

面向 VBOT EDU 机器人的参考应用，将设备接口组合成完整的应用流程。

**当前状态：规划中。本仓库尚无可运行的 Blueprint。**

## 从接口到应用

[Recipes](../recipes/README.zh-CN.md) 聚焦单个接口或开发步骤。
Blueprint 将这些基础能力组合为开发者可以理解、运行、验证，并按自身场景改造的应用。

每个发布的 Blueprint 将包含：

- 应用场景与架构说明。
- 源码、配置，以及 Bazel 构建、运行和测试入口。
- 支持的设备类型、固件、SDK 版本、依赖与运行位置。
- 部署步骤、预期结果及可复现的验证方法。
- 安全前置条件、停止方法和清理步骤。

可用状态将按应用分别说明。当前 EDU 发布范围仍为 `foot_quadruped`；
这一规划板块不增加其他设备类型的支持。

从 [Aorta Python SDK](../packages/README.zh-CN.md) 和[Developer Guide（开发者指南）](../docs/README.zh-CN.md)开始。
返回 [VBOT Lab](../README.zh-CN.md)。
