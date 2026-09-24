# Guides

<p align="center">English | <a href="README.zh-CN.md">中文</a></p>

For invocation choices and field mappings, see [direct services versus RCP](control-paths.md).

- [Agent integration](agent-integration.md): HTTP MCP connection, device Skill / AGENTS.md API injection, and troubleshooting.
- [RCP DAG authoring](rcp-dag.md): complete Goal examples, preset calls and custom graphs; [preset catalog](rcp-presets.md), [command fields](../interfaces/rcp-commands.md), and independent [device resources](../resources/README.md).
- [Foxglove live viewing](foxglove.md): device shell prerequisites, Aorta bridge startup, topic selection and WebSocket connection.
- [Vbot Viewer](vbot-viewer.md): robot-model inspection, URDF editing/checks, local variants and export; no robot connection required for viewing.
- [Mapping and localization](mapping-localization.md): Aorta interface checks, odometry, map creation/saving, localization, and completion criteria.
- [User-program autostart](user-autostart.md): launch programs as vbot after reboot, configure the boot entry, check logs, and disable startup.

Additional deployment tooling and SDK application guides remain planned.
Use the [interface reference](../interfaces/README.md) for concrete interfaces.

When deploying a user program, check the autostart mechanism, writable paths, and resource
limits available in the installed firmware. Follow each control interface's operating
preconditions and stopping procedure.
