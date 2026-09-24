# 四足 EDU 模型资源

<p align="center"><a href="README.md">English</a> | 中文</p>

模型：**VbotBaboEDU**。设备类型：`foot_quadruped`。

本目录附带 VbotBaboEDU 的 URDF 及其引用的网格。[model.json](model.json) 的 `availability`
为 `bundled`，并给出 `urdf` 入口文件与网格列表；其中路径均相对于本目录。未附带纹理。

## 资源布局

- `urdf/VbotBaboEDU.urdf`：默认入口，包含机身、四条腿与头部偏航／俯仰链。
- `urdf/VbotBaboEDU_*.urdf`：变体 `mock_head`、`mock_head_silence`（静音足端网格）、
  `backboard` 与 `backboard_bracket`。
- `meshes/`：URDF 文件引用的 STL 网格。
- `model.json`：模型标识、设备类型、入口文件、网格列表与公开 Viewer 地址。

## 加载 URDF

网格路径使用 `package://VbotBaboEDU/meshes/...` URI。在 URDF 加载器中将
`package://VbotBaboEDU/` 前缀映射到本目录，或将本目录放入名为 `VbotBaboEDU` 的 ROS 2 包。
预期结果：加载器能解析全部网格，`VbotBaboEDU.urdf` 显示 19 个关节。

模型姿态、关节限位、惯性参数与网格用于可视化和仿真，属于描述数据，不是机器人控制指令或硬件实测值。
这些文件是快照，[在线模型](https://vbot-viewer.vitarobot.cc/?model=VbotBaboEDU)可能独立更新
（参见 [Viewer 指南](../../../docs/guides/vbot-viewer.zh-CN.md)）。`model_license` 尚未声明。

设备开发见[四足 EDU 指南](../../../docs/robots/foot_quadruped/README.zh-CN.md)。
模型问题与建议可按[社区与支持](../../../docs/community/README.zh-CN.md)反馈。
