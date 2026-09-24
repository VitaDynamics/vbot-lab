# Troubleshooting

<p align="center">English | <a href="README.zh-CN.md">中文</a></p>

For missing Aorta / ROS 2 commands, incomplete topic discovery, or non-interactive shell
failures, start with [device environment checks](../getting-started/device-environment.md)
and [available interface mappings](../interfaces/aorta-ros2.md).

During integration, record reproducible issues, diagnostic commands, and expected results for:

- Image pulls, container startup, mounts, and file ownership.
- Bazel versions, dependency downloads, and caches.
- Python imports, native library loading, and architecture / ABI mismatches.
- Device networking, `vbot` account login, and Aorta connections.
- Unavailable interfaces, Schema mismatches, and service timeouts.
- Permission denials, program exits, and user-accessible logs.

Include the relevant software versions, reproduction steps, and error messages in a report.
Remove personal information and access tokens before sharing logs.

## Ask the community

If the checks do not resolve the issue, ask in [Vbot 超能社区](https://forum.vbot.cn/).
Use [Community & Support](../community/README.md) to choose a category and prepare a
short, reproducible report. Include what you tried; do not upload full configuration
files or credentials. Follow up in the same topic when you find the solution.
For a specific repository code/documentation bug, GitHub Issues remains available.
Do not post vulnerability details publicly; see [Security](../../SECURITY.md).
