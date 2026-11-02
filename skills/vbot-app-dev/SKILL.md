---
name: vbot-app-dev
description: Build or extend a Python/C++ VBOT application using the capability catalog and independent project templates. Use for application development, not device-side Skill injection or environment inventory alone.
---

# Develop a VBOT application

<p align="center">English | <a href="SKILL.zh-CN.md">中文</a></p>

## Resolve the reference checkout

Resolve this file's physical path. Its containing skills/vbot-app-dev directory belongs to
VBOT Lab, including when linked from another project. Confirm tools/create_app.py and
catalog/capabilities.json exist there; request the complete checkout if they do not.
Keep changes in the user's application, not the reference checkout. Preserve its AGENTS.md,
CLAUDE.md, Skills and existing source. Do not regenerate over an existing directory.

## Choose the application path

Use the user's language and existing project. If unspecified, state a Python starting choice;
do not convert an existing C++ application or run both languages by default. Establish the
desired behavior, required streams, output effects, completion conditions and stopping method.
Use the [catalog](../../catalog/README.md), then only the selected interface and SDK guide.
Supported capabilities and parameters come from those references, not plausible API names.

For a new project, use [templates](../../templates/README.md) and tools/create_app.py with
--language python or cpp and a new application directory. This copies the
[health monitor](../../blueprints/health-monitor/README.md); it does not generate arbitrary robot
behaviors. Adapt business rules to the task rather than assuming the starter already implements it.
For an existing project, preserve its layout and use only the relevant interfaces/helpers.

## Develop locally before deployment

Follow [execution locations](../../docs/development/README.md). Reuse the selected development
container; if none is ready, use the environment workflow in
[vbot-dev-setup](../vbot-dev-setup/SKILL.md). Never fall back to host/device builds or create a
second container merely because its runtime architecture is AMD64. C++ device builds use the
supplied ARM64 toolchain and matching SDK; native previews/tests use the native SDK.

Separate SDK transport from business state. Preserve bounded waits/queues, callback receive
time, malformed-data handling, explicit stopping and cleanup.

Build/test/preview the selected project using its README. Package only after local checks;
follow the generated guide for Python wheels or C++ binaries/libraries. Packaging is not deployment.
Do not SSH, install, configure autostart, record sensors or issue controls without a request
covering those actions. Use the selected device/account and documented prerequisites for authorized
live work; new/modified live examples need device checks before publication.

## Handoff

Report changed files, exact build/test results, the local package if requested, and
remaining deployment/device steps. Do not turn successful offline tests into a live-success claim.
For existing failures, use [vbot-diagnose](../vbot-diagnose/SKILL.md) and the
[troubleshooting index](../../docs/troubleshooting/README.md), without broadening the task.
