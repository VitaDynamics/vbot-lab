# Developer Guide

<p align="center">English | <a href="README.zh-CN.md">中文</a></p>

Environment setup, device connection, and application development for VBOT EDU robots.
Follow the chapters below. For Codex or Claude Code setup, see [Build with your Agent](agents/README.md).

1. [Platform overview](overview/README.md): supported scope and architecture.
2. [Robot-type guides](robots/README.md): choose a device type and check its EDU release scope.
3. [Hardware reference](hardware/README.md): specifications with explicit applicability, shared where appropriate.
4. [Quickstart](getting-started/README.md): shared environment setup and the first-run workflow.
5. [Development workflow](development/README.md): Bazel, device connectivity, and deployment.
6. [Interface reference](interfaces/README.md): Aorta / Python interfaces and [Agent capabilities](interfaces/agent/README.md).
7. [Guides](guides/README.md): interface workflows, autostart, and [Agent integration](guides/agent-integration.md).
8. [Troubleshooting](troubleshooting/README.md): environment, connectivity, and version issues.
9. [Community & Support](community/README.md): ask questions, share applications, and provide reproducible feedback.

The current EDU release scope is `foot_quadruped` only. Start with its
[type-specific guide](robots/foot_quadruped/README.md); the other type directories are future-release placeholders.
Common chapters stay in their existing paths, type-specific differences live under
`robots/<robot_type>/`, and reusable hardware specifications stay under `hardware/`.
See the [documentation structure rules](robots/README.md) before adding a new type or hardware variant.

The documentation includes hardware specifications, Agent interfaces, and development-environment setup.
Features without a runnable implementation are marked as planned or pending integration.

## Continue building

- [Vbot Viewer](guides/vbot-viewer.md): inspect and edit URDF models in the browser; separate from live robot data.
- [Robot models](../assets/robots/README.md): resource locations and availability by robot type; `foot_quadruped` bundles URDF and meshes.

- [Device resources](resources/README.md): body/head trajectories, expression IDs and light modes, independent of RCP orchestration.

- [Capabilities & Interfaces](../catalog/README.md): query task availability, device scope, and source references.

- [Aorta Python SDK](../packages/README.md): Aorta Python SDK access and compatibility.
- [Recipes](../recipes/README.md): single-task Python/C++ reference programs with Bazel targets.
- [VBOT Blueprints](../blueprints/README.md): complete reference applications, currently planned.
- [Skills](../skills/README.md): local environment-check workflow and setup instructions for Codex and Claude Code.
- [Interface Definitions](../schemas/README.md): checked-in public Aorta Schema and versioned generated bindings.
