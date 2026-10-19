# VBOT Blueprints

<p align="center">English | <a href="README.zh-CN.md">中文</a></p>

Reference applications that bring device interfaces together into complete workflows for VBOT EDU robots.

Start with [Read-only health monitor](health-monitor/README.md): Python/C++ source, configuration,
synthetic business tests, a Python/C++ workspace generator and deployment steps for both languages.
It combines state, battery and system telemetry without sending control commands.

## From interfaces to applications

[Recipes](../recipes/README.md) focus on one interface or development step.
A Blueprint combines those building blocks into an application that developers can
understand, run, verify, and adapt to their own use case.

Each published Blueprint will include:

- A use-case description and architecture overview.
- Source code, configuration, and Bazel build, run, and test entry points.
- Supported robot types, firmware, SDK versions, dependencies, and execution location.
- Setup steps, expected results, and reproducible validation.
- Safety preconditions, stopping procedures, and cleanup.

Blueprint availability is documented per application. The current EDU release scope
remains `foot_quadruped`; this area does not add support for other robot types.

Start with [Aorta Python SDK](../packages/README.md) and the [Developer Guide](../docs/README.md).
Return to [VBOT Lab](../README.md).
