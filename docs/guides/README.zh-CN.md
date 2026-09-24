# 功能指南

<p align="center"><a href="README.md">English</a> | 中文</p>

调用方式选择与字段对应见[直接服务与 RCP](control-paths.zh-CN.md)。

- [Agent 接入](agent-integration.zh-CN.md)：HTTP MCP 连接、设备端 Skill／AGENTS.md API 注入及排障。
- [RCP DAG 编写](rcp-dag.zh-CN.md)：完整 Goal 示例、预设调用与自定义图；配套[预设目录](rcp-presets.zh-CN.md)、[节点字段参考](../interfaces/rcp-commands.zh-CN.md)与独立的[设备资源](../resources/README.zh-CN.md)。
- [Foxglove 实时查看](foxglove.zh-CN.md)：设备 shell 前置、Aorta bridge 启动、topic 选择与 WebSocket 连接。
- [Vbot Viewer](vbot-viewer.zh-CN.md)：查看机器人模型、编辑／校验 URDF、保存本地变体并导出；查看时无需连接机器人。
- [建图与定位](mapping-localization.zh-CN.md)：Aorta 接口检查、里程计、建图与保存、定位及完成条件。
- [用户程序自启动](user-autostart.zh-CN.md)：重启后以 vbot 身份启动程序、配置开机入口、查看日志及停用。

额外的部署工具及 SDK 应用指南仍在规划中。
具体接口以[接口参考](../interfaces/README.zh-CN.md)为准。

部署用户程序时，按已安装固件确认可用的自启动方式、可写路径和资源限制。
使用控制接口时，遵循相应的操作前置条件和停止方法。
