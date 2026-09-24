# CI and repository collaboration

<p align="center">English | <a href="WORKFLOWS.zh-CN.md">中文</a></p>

The current workflow runs repository-content and offline agent-workspace checks on GitHub-hosted runners.
GitHub Actions checks out the code; the check script itself makes no network requests
and performs no device operations.

It validates bilingual documentation, relative Codex / Claude Code Skill links, capability
catalog decisions, local environment-tool behavior, and SDK-free Recipe previews and safety guards.
It does not launch model sessions or open Aorta sessions.

Dependency builds and SDK tests are not yet included in this workflow.
