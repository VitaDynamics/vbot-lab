# Device resources

<p align="center">English | <a href="README.zh-CN.md">中文</a></p>

For invocation choices and field mappings, see [direct services versus RCP](../guides/control-paths.md).

Resource identifiers are separate from orchestration. Body/head trajectories, screen expressions and light modes are different capabilities. RCP can combine them, but the resources themselves are not DAGs.

These lists describe the current foot-quadruped EDU resource set. Installed resources can vary with device software; do not infer support for other robot types from a shared identifier.

- [Body trajectories](body-trajectories.md)
- [Head trajectories](head-trajectories.md): CSV names and their body/preset pairing
- [Expression IDs](expressions.md)
- [Light modes](lights.md)

Composition and execution: [RCP presets](../guides/rcp-presets.md) · [DAG guide](../guides/rcp-dag.md) · [NodeCommand](../interfaces/rcp-commands.md).
