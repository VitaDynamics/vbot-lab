# 机器人模型

<p align="center"><a href="README.md">English</a> | 中文</p>

机器人描述资源放在 `assets/robots/<robot_type>/`，与文档截图、通信 Schema 分开。
各类型目录的 `model.json` 标明具体模型以及本地文件是否可用。

| 设备类型 | 模型入口 | 本地资源 |
| --- | --- | --- |
| `foot_quadruped` | [VbotBaboEDU](foot_quadruped/README.zh-CN.md) | 仅预留目录，未附带 URDF 与网格 |

可先按 [Vbot Viewer 指南](../../docs/guides/vbot-viewer.zh-CN.md)在线浏览模型。
在线可用不代表模型文件已包含在当前仓库，也不代表各类型均已开放 EDU 软件支持。
目前这里尚未提供 `wheel_quadruped` 或 `foot_humanoid` 的模型资源。

类型目录内，`urdf/` 存放机器人描述，`meshes/` 存放网格，存在纹理依赖时再添加 `textures/`。
具体机型记录在 `model.json`，不再增加机型名称目录。元数据中的本地路径均相对于
设备类型目录；`null` 不能作为可导入的模型路径。

取得模型后，应按其随附说明确认适用范围和许可。在线模型与仓库快照可能独立更新。
模型的姿态、限位和物理属性属于描述数据，不是机器人控制指令或硬件实测值。
