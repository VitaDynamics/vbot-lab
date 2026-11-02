# Agent capabilities

<p align="center">English | <a href="README.zh-CN.md">中文</a></p>

This section documents device-side `vbot-agent-harness` integration: HTTP MCP tools and connection configuration,
runtime Skills, and developer-supplied `AGENTS.md` instructions, including the HTTP APIs
for injecting user content. It applies to a single robot with
a single trusted developer using the `vbot` account on S100.
In this repository, the release scope is [foot_quadruped](../../robots/foot_quadruped/README.md)
only. Do not infer availability on `wheel_quadruped` or `foot_humanoid`.

## Capability map

| Capability | Developer responsibility | Agent behavior | Reference |
| --- | --- | --- | --- |
| HTTP MCP | Run a trusted HTTP MCP service and register its reachable URL when using an additional endpoint | The EDU runtime acts as an MCP client, discovers tools, and calls them | [Tool contract](http-mcp.md), [connection API](mcp-config.md) |
| Device Skills | Write `SKILL.md` and upload it through the Skills API | Discovers reusable knowledge / procedures and activates them for matching requests | [Authoring](customization.md), [content API](content-api.md) |
| Device AGENTS.md | Write persistent preferences and replace user-layer content through the AGENTS.md API | Merges instructions during subsequent Turn prompt builds | [Authoring](customization.md), [content API](content-api.md) |

These are distinct from the Aorta Python SDK: MCP lets the Agent call developer tools,
while Aorta interfaces provide robot capabilities. This contract does not
define an Aorta route or ROS2 mapping. Tools use the interfaces documented for the device.
Skills and `AGENTS.md` supply instructions; they do not grant additional OS permissions.

## Keep the consumers separate

| Artifact | Consumer | Location / delivery |
| --- | --- | --- |
| Coding Agent Skill | Developer-side coding harness, such as Codex or Claude Code | [`skills/`](../../../skills/README.md); local environment-check Skill |
| Device Skill | EDU `vbot-agent-harness` | Developer-authored `SKILL.md`, injected through `/api/skills/{name}` |
| Device AGENTS.md | EDU `vbot-agent-harness` | Developer-authored instructions, injected through `/api/agents-md` |
| Repository AGENTS.md | Coding Agents developing with or contributing to vbot-lab | [Shared task routing and instructions](../../../AGENTS.md); not a device customization artifact |

## Version compatibility

These APIs target robot application **V1.6.0-15** on `foot_quadruped` EDU.
Check the [compatibility matrix](../../compatibility.md) and the installed runtime before integration.
Use the [integration guide](../../guides/agent-integration.md) to verify API responses,
content paths, and behavior in a new Turn. Keep your source content and backups in your
own workspace, and consult the release instructions before a firmware upgrade.

This repository provides the interface documentation. It does not currently include
an executable MCP server or installable device Skill packages.

## Boundaries

- The default S100 MCP endpoint is `http://192.168.127.2:18080/mcp`; the configuration and content APIs use
  `http://192.168.127.10:8787`. These are separate contracts on the robot's internal network.
  Do not expose or forward ports `18080` or `8787` to campus public networks or the Internet.
- Use the `vbot` account and the documented access methods; stay within the account's assigned permissions.
- Only the documented MCP tool subset is promised: no stdio transport, Resources,
  or Prompts.
- Additional HTTP MCP services can be registered, edited, enabled/disabled and refreshed
  through the [connection API](mcp-config.md). Use addresses reachable from the device
  runtime and check discovery before starting a new Turn. This is not a multi-tenant hosting contract.
- An MCP session header is transport state, not a content API credential.
- Use the [content API](content-api.md) for user-layer Skills and `AGENTS.md`.
- This section covers MCP and user-content customization, not the full application
  conversation protocol or general system-service management.
