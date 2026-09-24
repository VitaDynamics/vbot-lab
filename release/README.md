# Versions and compatibility

<p align="center">English | <a href="README.zh-CN.md">中文</a></p>

The SDK is published as [GitHub releases](https://github.com/VitaDynamics/vbot-lab/releases)
named `edu-sdk-<date>`; each carries `EDU_SDK_MANIFEST.json` with the version pairing and
`SHA256SUMS`. Releases are marked pre-release until they are verified on a robot. The
[compatibility matrix](compatibility.md) records the current availability of each component,
supported robot types, and which robot software serves which interfaces.

Before choosing or upgrading a version:

- Check your robot type, product model, hardware revision, and firmware version.
- Use compatible versions of the development image, Python SDK, Schema, and examples.
- Use the image tag or digest documented for that version.
- Review API changes and back up your device Skills, AGENTS.md, and application data.
- Verify read-only access first, then test your application under the documented safety conditions.

The current EDU scope is `foot_quadruped`; the other robot-type guides are not yet released.
Device Skill / AGENTS.md compatibility and Coding Agent Skill compatibility are tracked separately.
