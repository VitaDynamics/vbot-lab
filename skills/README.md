# Skills

<p align="center">English | <a href="README.zh-CN.md">中文</a></p>

Task workflows for developer-side Coding Agents, including Codex and Claude Code.
This directory is the single source; both `.agents/skills/` and `.claude/skills/`
are relative symlinks to it.

## Available workflows

[vbot-dev-setup](vbot-dev-setup/SKILL.md) guides Python or C++ setup through SDK preparation,
Bazel build, SSH device setup, deployment and a bounded read-only state subscription.
It reuses the SDK and deployment guides; the robot needs no repository checkout or Bazel.
Repository-only checks may run on the host or CI runner. Builds, previews and packaging stay
in the matching development container; see [execution locations](../docs/development/README.md).
For inventory-only or advice requests, it stays within that narrower scope.
The inventory checker uses Python 3.10+ and the standard library. It never installs software,
starts a container, contacts a device, or changes configuration.

The Skill and offline helper are implemented. Confirm the Skill appears in your harness,
then request either a local environment check or full setup through the first state sample.
Additional development scenarios are listed
in [workflow checks](../tests/agent-scenarios/README.md).
See [Agent quickstart](../docs/agents/README.md) for setup and external-project use.

Use [vbot-app-dev](vbot-app-dev/SKILL.md) to build or extend an independent Python/C++
application, choose interfaces and prepare a local deployment package. The Skill does not
deploy merely because packaging succeeded.

Use [vbot-diagnose](vbot-diagnose/SKILL.md) for an existing application's environment,
SDK/linkage or missing-data failure. It selects explicit diagnostic levels and distinguishes
timeouts from unsupported interfaces; it does not automatically repair or contact a device.

Each workflow references the catalog, SDK and relevant guides rather than duplicating contracts.
Tools remain directly usable without a Skill. See [Agent quickstart](../docs/agents/README.md)
for linking only the selected workflows into another project without overwriting its configuration.

These Skills are not device-side `vbot-agent-harness` content.
For device Skill / AGENTS.md authoring and injection, use the
[device content API](../docs/interfaces/agent/content-api.md).
