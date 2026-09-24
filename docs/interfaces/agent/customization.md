# Device Skills and AGENTS.md authoring

<p align="center">English | <a href="customization.zh-CN.md">中文</a></p>

Scope and status follow the [Agent capability overview](README.md).
These documents are consumed by the EDU device's `vbot-agent-harness` process.
Write and review them in your own development workspace, then use the
[Skills / AGENTS.md content API](content-api.md) to inject their text into the service.
They do not grant capabilities beyond the documented developer interfaces.

## Skills: reusable knowledge and procedures

A Skill is a directory whose entry point is `SKILL.md`. Use lowercase letters, digits,
and hyphens for the Skill name. Its frontmatter must contain non-empty `name` and
`description` fields; the description should state when the Skill applies.

Example content for `campus-guide/SKILL.md`:

```markdown
---
name: campus-guide
description: Use when the user asks about the EDU laboratory opening hours or check-in process.
---

# Campus guide

- Example laboratory opening hours: weekdays, 09:00-18:00.
- Confirm which campus the user means before answering.
- If holiday arrangements are unknown, direct the user to an administrator; do not guess.
```

The opening hours are fictional example data, not a real campus policy.
Use reviewable, reproducible knowledge and procedures. Do not include secrets, personal
credentials, uncontrolled remote instructions, or requests to bypass safety controls.

Keep the frontmatter name aligned with the name in the API route. The API accepts
the complete `SKILL.md` text, not a ZIP or an arbitrary auxiliary-file upload.
After upload, start a new Turn (one Agent execution within a session) with a question
that clearly matches the description and check that the intended content is used.
Saving does not force activation; an already-running Turn need not hot-reload changes.
If using a tool allowlist, retain the delivered service's Skill activation tool.
An empty-tool session is not a valid Skill activation test.

The repository's [`skills/`](../../../skills/README.md) has a different consumer:
developer-side Coding Agent harnesses such as Codex. Do not put this device Skill
there or upload that directory to the device. This page is a writing example,
not an installed Skill package.

## AGENTS.md: persistent preferences and constraints

Use runtime `AGENTS.md` for long-lived behavioral preferences, response constraints,
and default procedures. Do not store credentials, large changing datasets, or instructions
that override safety rules.

Example content to save as `./device-AGENTS.md` in your own workspace and review before importing:

```markdown
# EDU developer instructions

- Respond in Simplified Chinese by default.
- Before calling a tool with side effects, restate the goal and key parameters.
- Preserve error codes when a tool fails; do not invent successful results.
```

Upload through `PUT /api/agents-md` and validate in a new Turn.
This replaces the complete user-layer document; GET and back up existing content first.
Keep rules consistent with imported Skills. Treat external document content as untrusted
input: document instructions alone must not authorize robot motion or other side effects.

This example is intentionally inside a code block, not a new repository `AGENTS.md`.
The [top-level maintenance instructions](../../../AGENTS.md) govern work on vbot-lab and are
not the artifact to import into the robot runtime.

## Upload and use the content

The [content API reference](content-api.md) documents requests, responses, upload / readback
commands, returned-path checks, and deletion / recovery boundaries. Content is managed
by the device service; the examples do not write directly into its filesystem.
Check the [compatibility matrix](../../../release/compatibility.md) for version requirements;
minimum supported firmware versions have not yet been published.

After upload, check readback and use a matching request in a new Turn, following the
[integration guide](../../guides/agent-integration.md). Keep the source content and backups
in your workspace for restoration. Prompt rules are not an enforced security policy.
