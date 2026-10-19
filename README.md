# VBOT Lab

<p align="center">English | <a href="README.zh-CN.md">中文</a></p>

**An agent-native development workspace for VBOT EDU robots.**

[Documentation](docs/README.md) · [Vbot Viewer](docs/guides/vbot-viewer.md) · [Community](docs/community/README.md)

VBOT Lab brings together task-oriented Skills, a capability catalog, the Aorta Python SDK,
interface definitions, and reference programs for building robot applications.

Current robot application target: **V1.6.0-12**, for `foot_quadruped` EDU.
See the [compatibility matrix](docs/compatibility.md) for SDK and platform pairing.

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
| [Skills](skills/README.md) | Task workflows for Coding Agents | Environment setup, Python/C++ application development and layered diagnosis |
| [Capabilities & Interfaces](catalog/README.md) | Device scope, interface references, and prerequisites | Queryable catalog; check interface availability on the selected device |
| [Recipes](recipes/README.md) | Reusable single-task programs | Python and C++ examples grouped by capability, with Bazel targets and offline previews |
| [VBOT Blueprints](blueprints/README.md) | Complete reference applications | Python/C++ read-only health monitor and independent application templates |
| [Developer Guide](docs/README.md) | Environment, connection, hardware, APIs, and troubleshooting | Chapters available with version-specific scope |

The [Aorta Python SDK](packages/README.md) stays under `packages/aorta/python/`;
[public Schema](schemas/README.md) stays under `schemas/`. Schema sources are checked in; release wheels and runnable examples are documented in the
[Python SDK guide](packages/aorta/python/README.md).

## Run your first application

Start with [Quickstart: read robot state with Python](docs/getting-started/README.md).
It follows one path: prepare the development container, build and preview `subscribe-state`,
package its pinned ARM64 dependencies, log in over SSH, then deploy and receive three
decoded `/locomotion/status` samples. Each step identifies its terminal, expected result
and troubleshooting link. No motion or audio/video capture is required.

Already in a development container? Reuse it; no Docker installation inside it is needed.
Build, preview and package there; run the deployed application in the robot's `vbot` shell.
An inventory or preview alone is not a successful live run.

For other paths, see [C++](packages/aorta/cpp/README.md),
[wired / Wi-Fi connection](docs/robots/quadruped-common/connection.md),
[device shell setup](docs/getting-started/device-environment.md),
[editor integration](.devcontainer/README.md), or [troubleshooting](docs/troubleshooting/README.md).
Repository validation is a separate [contribution workflow](#contributing-and-validation).

## Scope and safety

The current EDU release target is `foot_quadruped`;
`wheel_quadruped` and `foot_humanoid` remain future releases.
Shared robot-dog hardware or connection procedures do not establish software compatibility.
Check the [robot guides](docs/robots/README.md) and [compatibility matrix](docs/compatibility.md).

The Python and C++ workflows use Bazel-based Recipes; the health-monitor Blueprint provides
both implementations, Python/C++ workspace generation and device deployment.
The documented Python and C++ examples include camera, locomotion, RCP and audio access.
Check the SDK pairing and device prerequisites before live execution.

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
On the host or CI runner, run `python3 tools/run_checks.py --scope repository`.
Recipe checks, Bazel and packaging run in the development container, including CI.
See [execution locations](docs/development/README.md) for the shared rule.
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
