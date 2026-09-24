# 四足机器狗 EDU

<p align="center"><a href="README.md">English</a> | 中文</p>

- 构建标识：`foot_quadruped`。
- EDU 范围：当前唯一纳入发布范围的设备类型。
- 已有指南：连接、shell 配置、硬件、SLAM 及 Agent 接口。已有 Python／C++ 示例程序，组件可用性见兼容矩阵。

## 开发入口

- [Vbot Viewer](../../guides/vbot-viewer.zh-CN.md)与[模型资源](../../../assets/robots/foot_quadruped/README.zh-CN.md)：可在线查看模型，也可在本地加载随仓库提供的 URDF 与网格。

- [两类机器狗共用的有线连接与 SSH 登录指南](../quadruped-common/connection.zh-CN.md)：连接转接头、设置电脑网卡，并使用 `vbot` 账户登录。
- [设备 shell 配置](../../getting-started/device-environment.zh-CN.md)与 [Aorta／ROS 2 兼容接口](../../interfaces/aorta-ros2.zh-CN.md)：SSH 登录后，在设备终端配置 `vbot` 环境并检查 CLI 访问，无需等待 SDK 接入。
- [两类机器狗共用的传感器规格](../../hardware/quadruped-common/sensors.zh-CN.md)。
- [Agent 能力](../../interfaces/agent/README.zh-CN.md)及[接入清单](../../guides/agent-integration.zh-CN.md)：S100 可信开发者场景的 HTTP MCP、Skills 与运行时 AGENTS.md，交付版本须另行确认。
- [兼容矩阵](../../../release/compatibility.zh-CN.md)：设备开发前确认具体型号、
  硬件版本、固件、SDK 和接口开放情况。
- [通用快速开始](../../getting-started/README.zh-CN.md)与
  [开发流程](../../development/README.zh-CN.md)：工作站环境及开发步骤。
- [接口参考](../../interfaces/README.zh-CN.md)与 [Recipes](../../../recipes/README.zh-CN.md)：
  使用文档列明且已验证适用于本类型的接口。

## 待补齐的机型专属章节

设备识别与前置条件、开放接口覆盖范围、示例前置条件、用户程序部署差异及排障方法，
在完成验证后逐步补充到本目录。
共用传感器规格不代表相同固件或运动控制接口可以用于 `wheel_quadruped`。

返回[设备类型指南索引](../README.zh-CN.md)。
