# Build with your Agent

<p align="center">English | <a href="README.zh-CN.md">中文</a></p>

Set up Skills in Codex or Claude Code and run development tasks from this checkout or your own project.
The initial workflow is a local environment inventory, not automatic robot deployment.

## Work inside VBOT Lab

Use a Git checkout that preserves symbolic links. The development container and Linux / WSL
workspaces are suitable filesystem choices; verify links after copying a checkout or extracting
an archive. Do not treat a text file containing `../skills` as a working link.

| Coding Agent | Project instructions | Skill discovery | Explicit invocation |
| --- | --- | --- | --- |
| Codex | `AGENTS.md` | `.agents/skills/` → `../skills` | `$vbot-dev-setup` |
| Claude Code | `CLAUDE.md` imports `AGENTS.md` | `.claude/skills/` → `../skills` | `/vbot-dev-setup` |

Only `skills/<name>/SKILL.md` is maintained as the discovery source. Its `.zh-CN.md` counterpart
is a human-readable translation, not another installed Skill. Do not copy different instruction
sets into each harness directory.

Select vbot-dev-setup for environment setup, vbot-app-dev for creating/extending Python/C++
applications, and vbot-diagnose for an existing application's failure. All three share the
same discovery directories: Codex uses `$<name>`, Claude Code uses `/<name>`.

Open the checkout in your agent and request a development-environment check without installing
anything or connecting to a robot. Check that `vbot-dev-setup` appears in the harness's Skill
selector. If not, verify the links, project trust and configuration, and restart in the checkout.
See the official [Codex Skill guide](https://learn.chatgpt.com/docs/build-skills),
[Claude Code Skill guide](https://code.claude.com/docs/en/skills), and
[Claude project-instruction guide](https://code.claude.com/docs/en/memory) for harness behavior.
For other agents, follow their Skill discovery mechanism and confirm the Skill appears before invoking it.

The repository checks validate link targets and shared content. They do not prove that a
particular harness version loaded the Skill. Use the [workflow checks](../../tests/agent-scenarios/README.md)
in a fresh session and record the harness/version separately.

## Work in your own application repository

Keep a complete, version-pinned VBOT Lab checkout accessible in the same filesystem as the
agent. Link only the individual workflow directories you need from that checkout into your application's
`.agents/skills/` and/or `.claude/skills/`, rather than replacing either directory. Preserve other
Skills and stop if an entry with the same name already exists.

For example, link vbot-app-dev for development and vbot-diagnose for troubleshooting; keep
vbot-dev-setup when setup is also needed. Do not replace .agents/skills or .claude/skills
with a whole-directory link in an existing application. Adding selected Skills does not
require changing its AGENTS.md or CLAUDE.md.

The linked Skill resolves its physical location to use the matching catalog, tools, and docs.
Do not copy just `SKILL.md`: those resources would be missing. Keep application output in your
own workspace; do not modify the reference checkout merely to build an application.
This arrangement needs access to the entire checkout and is not a self-contained plugin.
Portable plugin distribution remains planned. Do not overwrite your application's existing
`AGENTS.md` or `CLAUDE.md` with VBOT Lab's repository instructions.

## Configure the device environment

First follow the [connection guide](../robots/quadruped-common/connection.md) to set up
SSH public-key access, or verify and reuse an existing setup. Check non-interactive login
from the environment where subsequent commands will run before continuing with device tasks.
If the device cannot be reached, connect it or provide its actual IP first.

Ask the same Skill to explain the [vbot shell setup](../getting-started/device-environment.md)
without connecting, or explicitly request setup/checks on your selected device. It distinguishes
the workstation, container, and device shell, and keeps `.bashrc` edits separate from read-only
inventory. Live checks use bounded discovery and single-sample subscriptions, never control commands.
The [Aorta / ROS 2 reference](../interfaces/aorta-ros2.md) lists available interfaces and their mappings.

## Follow a development task

Repository-only checks may run on the host or CI runner. Bazel, Recipe previews, SDK checks
and packaging run in the matching development container, including CI. An Agent on the host
executes them through the selected container; an inventory profile or another terminal's
interactive session does not change its execution context. See [execution locations](../development/README.md).

1. Use [Skills](../../skills/README.md) to find the relevant workflow.
2. Query the [capability catalog](../../catalog/README.md) for the device scope and references.
3. Read the selected interface, SDK, and [Recipe](../../recipes/README.md), not every document.
4. Run only available build/test entries and report actual results and remaining blockers.

The documented SDK workflows cover Python and C++. Generate a standalone application with --language python or cpp
from the [health-monitor Blueprint](../../blueprints/health-monitor/README.md);
keep application files in its generated workspace, not this reference checkout.
Device-side Skills and AGENTS.md are a separate [content API](../interfaces/agent/content-api.md),
not these Coding Agent discovery folders. No local check grants permission to control a robot.
