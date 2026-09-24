# 版本与兼容性

<p align="center"><a href="README.md">English</a> | 中文</p>

SDK 以名为 `edu-sdk-<日期>` 的 [GitHub Release](https://github.com/VitaDynamics/vbot-lab/releases)
发布，每个 Release 都附带记录版本配对的 `EDU_SDK_MANIFEST.json` 与 `SHA256SUMS`。在机器人上
验证通过前，Release 标记为预发布。[兼容矩阵](compatibility.zh-CN.md)记录各组件的可用状态、
支持的设备类型，以及哪些机器人软件提供哪些接口。

选择或升级版本前：

- 核对设备类型、产品型号、硬件版本及固件版本。
- 使用相互兼容的开发镜像、Python SDK、Schema 和示例版本。
- 使用对应版本文档列明的镜像标签或 digest。
- 查阅 API 变更，备份设备 Skill、AGENTS.md 及应用数据。
- 先验证只读访问，再按文档中的安全条件测试应用。

当前 EDU 范围为 `foot_quadruped`，其他设备类型的指南尚未发布。
设备 Skill／AGENTS.md 与 Coding Agent Skill 的兼容性分别记录。
