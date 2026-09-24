# VBOT Lab

<p align="center">English | <a href="README.zh-CN.md">中文</a></p>

**An agent-native development workspace for VBOT EDU robots.**

[Documentation](docs/README.md) · [Vbot Viewer](docs/guides/vbot-viewer.md) · [Community](docs/community/README.md)

VBOT Lab brings together task-oriented Skills, a capability catalog, the Aorta Python SDK,
interface definitions, and reference programs for building robot applications.

## Build with your Agent

Open this checkout in Codex or Claude Code, then ask:

> Check this workstation for VBOT development. Report available tools, missing dependencies,
> and release limitations. Do not install software or connect to a robot.

The [vbot-dev-setup Skill](skills/vbot-dev-setup/SKILL.md) performs a local, read-only inventory.
Codex discovers the shared Skills through `.agents/skills/`; Claude Code uses
`.claude/skills/`. Both point to `skills/`. [AGENTS.md](AGENTS.md) provides task routing;
[CLAUDE.md](CLAUDE.md) imports the same instructions.

See [Agent quickstart](docs/agents/README.md) for invocation, using Skills from your own
application repository, symlink requirements, and checking discovery in your harness.

## Find what you need

| Entry | Purpose | Current availability |
| --- | --- | --- |
| [Skills](skills/README.md) | Task workflows for Coding Agents | Local environment-check Skill and shared discovery links available |
| [Capabilities & Interfaces](catalog/README.md) | Device scope, interface references, and prerequisites | Queryable catalog; check interface availability on the selected device |
| [Recipes](recipes/README.md) | Reusable single-task programs | Seven tasks with Python and C++ examples with Bazel targets and offline previews |
| [VBOT Blueprints](blueprints/README.md) | Complete reference applications | Planned |
| [Developer Guide](docs/README.md) | Environment, connection, hardware, APIs, and troubleshooting | Chapters available with version-specific scope |

The [Aorta Python SDK](packages/README.md) stays under `packages/aorta/python/`;
[public Schema](schemas/README.md) stays under `schemas/`. Schema sources are checked in; release wheels and runnable examples are documented in the
[Python SDK guide](packages/aorta/python/README.md).

## Start locally

From the checkout root, with Python 3.10 or later:

```bash
python3 tools/check_environment.py --profile host
python3 tools/vbot_catalog.py --robot-type foot_quadruped
python3 tests/check_repository.py
python3 tests/test_agent_workspace.py
python3 tests/test_recipes.py
bazel build //:repository_files //recipes/...
bazel test //tests:repository_layout_test //tests:agent_workspace_test //tests:recipe_test
```

The first command inventories this machine, not a connected robot. Use `--profile container`
inside the development container. Tool discovery does not verify versions, Docker daemon
access, image availability, or SDK readiness. See [Developer tools](tools/README.md).

For environment setup, use the [container guide](docker/README.md) and
[editor integration](.devcontainer/README.md). To connect a robot dog, follow the
[shared wired connection guide](docs/robots/quadruped-common/connection.md), including its
connection photo. Connection and device operations are separate, explicitly requested steps.

After login, follow [device shell setup and checks](docs/getting-started/device-environment.md)
for Aorta and the [ROS 2 compatibility subset](docs/interfaces/aorta-ros2.md).
The device CLI workflow is independent of Python SDK installation.

## Scope and safety

The current EDU release target is `foot_quadruped`;
`wheel_quadruped` and `foot_humanoid` remain future releases.
Shared robot-dog hardware or connection procedures do not establish software compatibility.
Check the [robot guides](docs/robots/README.md) and [compatibility matrix](release/compatibility.md).

The documented Python and C++ workflows use Bazel-based Recipes; Blueprints remain planned.
The documented Python and C++ examples include camera, locomotion, RCP and audio access.
Check the pre-release SDK pairing and device prerequisites before live execution.

Developer-side Skills are separate from the [device Agent APIs](docs/interfaces/agent/README.md)
for HTTP MCP and Skill / AGENTS.md injection. Local checks do not contact devices or change
services, permissions, resources, or motion state. Device writes and motion require task
authorization and the documented preconditions.

## Community & Support

Stuck on an integration, exploring a new capability, or ready to share what you built?
Join [Vbot 超能社区](https://forum.vbot.cn/) to ask questions, exchange development
experience and suggest improvements. See [Community & Support](docs/community/README.md)
for topic categories and a short report template. Include reproduction steps and
sanitized details so others can help and benefit from the answer.

## Contributing and validation

See [Contributing](CONTRIBUTING.md), [tests](tests/README.md), and
[Agent workflow checks](tests/agent-scenarios/README.md).
Repository checks run locally without contacting a device.
See [Security](SECURITY.md) for reporting vulnerabilities.

## License

Unless otherwise noted, the code, documentation, interface definitions, and examples in
this repository are licensed under the [Apache License, Version 2.0](LICENSE)
(`Apache-2.0`). Attribution is provided in [NOTICE](NOTICE).

Commercial use, modification, and redistribution are permitted under the license.
Redistribution must include the license, preserve applicable attribution notices, and
identify modified files. The license does not require derivative works to be open source
and does not grant trademark rights beyond the exceptions in Section 6.

Third-party components retain their own licenses. Separately distributed SDK packages,
firmware, and container images are governed by their accompanying license terms; this
repository's license does not relicense them. The English LICENSE file is authoritative;
this summary does not add to or replace its terms.
