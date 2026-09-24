# Platform overview

<p align="center">English | <a href="README.zh-CN.md">中文</a></p>

VBOT Lab organizes development tools and interface references for VBOT EDU robots.
Robot guides are grouped into four-legged robot dogs, four-wheeled robot dogs, and bipedal robots.
The current EDU release scope is the four-legged robot dog (`foot_quadruped`) only,
with public Schema sources, released Python SDK wheels and executable Recipes.
A local environment-check Skill and a queryable capability catalog are available.
The other robot types have future-release placeholders in the [robot-type guide index](../robots/README.md).
Directory entries do not imply that every device model is already supported.
Supported device models and firmware versions are defined in the
[compatibility matrix](../../release/compatibility.md).

## From task to verification

- [Build with your Agent](../agents/README.md): Codex / Claude Code entry points and external-project use.
- [Skills](../../skills/README.md): task workflows; start with the local environment check.
- [Capabilities & Interfaces](../../catalog/README.md): release scope and authoritative interface references.
- [Developer Guide](../README.md): environment setup, robot connection, and interface documentation.
- [Aorta Python SDK](../../packages/README.md): device access through the Aorta Python SDK; release wheel installation documented.
- [Recipes](../../recipes/README.md): single-task reference programs; Python/C++ source and Bazel targets available.
- [VBOT Blueprints](../../blueprints/README.md): complete reference applications, currently planned.

Skills route the task; the catalog points to facts; Recipes and tools provide implementations;
tests supply evidence. Aorta retains its package/API identity. Recipes and Blueprints share
the Python-first, Bazel-based development path.

## Hardware and interface scope

For sensor parameters and mounting locations, select a type in the
[sensor specification index](../hardware/sensors.md).
The documented sensors are shared by `foot_quadruped` and `wheel_quadruped`,
not by `foot_humanoid`; this hardware scope does not extend EDU software support.

- Schema defines communication contracts; the SDK provides calls; Recipes implement individual tasks; Blueprints combine them into applications.
- Aorta is the primary development path; document only ROS2 mappings that exist and have been verified.
- [Device Agent interfaces](../interfaces/agent/README.md) cover developer-owned HTTP MCP tools and Skill / AGENTS.md content injection; their contract is separate from the Aorta SDK and developer-side Coding Agent Skills.
- The Recipes use Python/C++ and cover the explicitly documented public interfaces, including audio.
- Docker runs on the development workstation; device programs use the `vbot` account.
- The existence of a Schema does not mean its interface is available on the device.
