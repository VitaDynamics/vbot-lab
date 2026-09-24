# Security

<p align="center">English | <a href="SECURITY.zh-CN.md">中文</a></p>

Do not submit credentials, private keys, or information that could be used to attack devices
in public issues, PRs, logs, or examples.

## Report a vulnerability

Send security reports privately to [vbot-edu@vbot.cn](mailto:vbot-edu@vbot.cn).
Do not post vulnerability details or exploit steps in public issues, PRs or the community forum.

Include the affected component and version, potential impact, and minimal reproduction
steps that can be performed safely. Share only the necessary sanitized log excerpts;
do not include passwords, tokens, private keys, device session files or personal data.
Do not repeat an unsafe robot operation to collect evidence. Coordinate any public
disclosure with the maintainers through the same email address.

For ordinary setup or development questions, use [Community & Support](docs/community/README.md).
The repository administrators maintain this project; review ownership is listed in
[CODEOWNERS](.github/CODEOWNERS).

## Development boundaries

The development container is a workstation environment, not a robot permission-isolation mechanism.
Device development uses the `vbot` account; SDKs, examples, and Skills must not grant
system-administration privileges.

See the [container guide](docker/README.md) for the existing image's isolated-development
boundary and SSH precautions.
Repository checks do not replace security testing of your application and deployment.
