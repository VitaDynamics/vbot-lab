# Security

<p align="center">English | <a href="SECURITY.zh-CN.md">中文</a></p>

Do not submit credentials, private keys, or information that could be used to attack devices
in public issues, PRs, logs, or examples.
Do not post vulnerability details in public issues. A dedicated security-reporting
contact has not yet been published.

The development container is a workstation environment, not a robot permission-isolation mechanism.
Device development uses the `vbot` account; SDKs, examples, and Skills must not grant
system-administration privileges.

See the [container guide](docker/README.md) for the existing image's isolated-development
boundary and SSH precautions.
Repository checks do not replace security testing of your application and deployment.
