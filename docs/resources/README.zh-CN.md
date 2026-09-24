# 设备资源

<p align="center"><a href="README.md">English</a> | 中文</p>

调用方式选择与字段对应见[直接服务与 RCP](../guides/control-paths.zh-CN.md)。

资源标识与编排方式分开维护。身体／头部轨迹、屏幕表情和灯光模式是不同的能力；RCP 可以组合它们，但资源本身不是 DAG。

这些清单对应当前四足 EDU 资源集合；设备软件不同，安装资源可能不同，不能仅凭同名标识推断其他机器人类型支持。

- [身体轨迹](body-trajectories.zh-CN.md)
- [头部轨迹](head-trajectories.zh-CN.md)：CSV 资源名及身体／预设配套关系
- [表情 ID](expressions.zh-CN.md)
- [灯光模式](lights.zh-CN.md)

编排与调用：[RCP 预设](../guides/rcp-presets.zh-CN.md) · [DAG 入门](../guides/rcp-dag.zh-CN.md) · [NodeCommand](../interfaces/rcp-commands.zh-CN.md).
