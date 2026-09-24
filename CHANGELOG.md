# Changelog

<p align="center">English | <a href="CHANGELOG.zh-CN.md">中文</a></p>

## Unreleased

- Bundle the VbotBaboEDU URDF, its variants and referenced STL meshes under `assets/robots/foot_quadruped/`; `model.json` lists the entry file and meshes.
- Move the SDK guides to `edu-sdk-2026.9.24`: Aorta 2026.9.23 (C++ `find_package` works without a version) and EDU schema pack 2026.9.24, whose `vbot_edu_msgs` wheel pins that Aorta release and carries `LICENSE`/`NOTICE`. Releases attach the FlatBuffers license text next to its PyPI wheel. After robot verification `edu-sdk-2026.9.24` is a regular release, no longer a pre-release.
- Document the EDU router: client and peer session files, free names shared among EDU programs, the published Foxglove bridge configuration, and `zenohd` 1.10.x for off-robot work.
- Remove the maintainer release runbook and the release and schema-sync workflows; releases no longer attach the ROS 2 bridge bundle.
- `schemas/ros2/` holds only the ROS 2 definitions the public bridge routes use (152 of the previous 375), with `routes.json` replacing the route manifest, `MANIFEST.json` replacing `SYNC_MANIFEST.json`, and third-party licenses in `THIRD_PARTY_NOTICES.txt`; `tests/check_schemas.py` checks the set.
- Keep workstation copies of EDU session files in `~/.config/vbot/robots/<robot-alias>/`; `.gitignore` and the repository checks reject session files, credential dictionaries and keys.
- Change the initial `vbot` password at first login.
- Introduce the Agent-native VBOT Lab workflow: shared AGENTS instructions, a Claude Code import entry, and Codex / Claude Code Skill discovery symlinks with one maintained source.
- Add the vbot-dev-setup Skill for scoped environment checks or SDK setup, build, deployment and read-only state subscription; include a versioned capability catalog and offline tests.
- Add Aorta Python and C++ SDK integration guides under `packages/aorta/`, EDU Schema definitions under `schemas/`, and Python/C++ examples with Bazel targets under `recipes/`.
- Document Python source/wheel deployment and C++ executable/shared-library deployment; neither requires a repository checkout or Bazel on the robot.
- Keep complete application Blueprints planned; they are not runnable applications yet.
- Add bilingual wired setup and SSH login instructions shared by `foot_quadruped` and `wheel_quadruped`, including an English-labeled connection photo, computer network settings, and connection troubleshooting; keep EDU release scope unchanged.
- Clarify device connection requirements and network-safety precautions.
- Document device HTTP MCP and Skill / AGENTS.md injection APIs, with upload, readback, and integration checks; distinguish device content from Coding Agent Skills.
- Organize EDU guides by canonical robot type; scope the current release to `foot_quadruped` and reserve other types for future releases.
- Keep one sensor specification shared by the two robot-dog types and retain the original sensor path as an applicability index.
- Clarify that the repository serves developers working with VBOT EDU robots across robot types, with device support and hardware specifications scoped separately.
- Add bilingual EDU sensor specifications under the hardware reference.
- Initialize documentation, Schema, Python SDK, example, Skill, and tool directories.
- Add Compose and editor integration for the existing EDU development image.
- Add repository structure and local documentation-link checks.
- Use English as the default documentation language and provide paired Simplified Chinese pages with language navigation.
- Check translation pairs, language-preserving links, and matching code examples.
