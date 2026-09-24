# Skills

<p align="center">English | <a href="README.zh-CN.md">中文</a></p>

Task workflows for developer-side Coding Agents, including Codex and Claude Code.
This directory is the single source; both `.agents/skills/` and `.claude/skills/`
are relative symlinks to it.

## Available workflow

[vbot-dev-setup](vbot-dev-setup/SKILL.md) guides Python or C++ setup through SDK preparation,
Bazel build, SSH device setup, deployment and a bounded read-only state subscription.
It reuses the SDK and deployment guides; the robot needs no repository checkout or Bazel.
For inventory-only or advice requests, it stays within that narrower scope.
The inventory checker uses Python 3.10+ and the standard library. It never installs software,
starts a container, contacts a device, or changes configuration.

The Skill and offline helper are implemented. Confirm the Skill appears in your harness,
then request either a local environment check or full setup through the first state sample.
Additional development scenarios are listed
in [workflow checks](../tests/agent-scenarios/README.md).
See [Agent quickstart](../docs/agents/README.md) for setup and external-project use.

## Planned workflows

Python application development and broader device diagnostics remain planned.
Their future Skills will reference [capabilities](../catalog/README.md),
[client libraries](../packages/README.md), [Recipes](../recipes/README.md), and
[Developer Guide](../docs/README.md), not duplicate interface definitions.

These Skills are not device-side `vbot-agent-harness` content.
For device Skill / AGENTS.md authoring and injection, use the
[device content API](../docs/interfaces/agent/content-api.md).
