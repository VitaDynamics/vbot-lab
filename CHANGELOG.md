# Changelog

<p align="center">English | <a href="CHANGELOG.zh-CN.md">中文</a></p>

## Rel/V1.6.0 — 2026-11-02

The final V1.6.0 release brings together the capabilities added since VBOT Lab was created.
It supports robot applications **V1.6.0-15** and **V1.6.0-17** on `foot_quadruped` EDU.
Start development on **`release/V1.6.0`** using the [quickstart](docs/getting-started/README.md).
`Rel/V1.6.0` identifies the formal source snapshot. For component pairing, see
[release.json](catalog/release.json) and the linked SDK guides.

### Development from setup to deployment

- Provide English-default documentation with paired Simplified Chinese pages, shared robot-dog connection guides and robot-type-specific scope. Wheeled-quadruped and bipedal EDU software remain outside this release.
- Document development-container setup, reuse of running or stopped containers, editor integration and ARM64 cross-compilation. Build and package applications in the container rather than on the robot.
- Cover wired and Vbot App-assisted Wi-Fi access, finding the current Wi-Fi IP under Settings → About in the bound app, SSH login and public-key setup, followed by device shell configuration for Aorta and the supported ROS 2 bridge interfaces.
- Complete the first Python application path: build and preview, package source and wheels, transfer over SSH, create a device venv and receive live robot state. Document C++ deployment as ARM64 executables plus required libraries, without requiring a device checkout or Bazel.
- Document Bazel dependency-bundle preparation and offline builds for constrained networks, with separate build, packaging and device-runtime steps.
- Add user-program startup through `/userdata/vbot/init.sh`, including explicit runtime environments, logs, reboot checks, updates and disabling startup. See [autostart](docs/guides/user-autostart.md).

### Agent-native workspace and application tools

- Organize the workspace into Skills, a machine-readable capability catalog, SDK guides, Schema, single-task Recipes, complete Blueprints and independent application templates.
- Share `AGENTS.md` instructions across Codex and Claude Code, with `.agents/skills/` and `.claude/skills/` exposing one maintained Skill source. Document use from an application's own workspace as well as this checkout.
- Provide `vbot-dev-setup`, `vbot-app-dev` and `vbot-diagnose` for environment setup, Python/C++ application development and layered diagnostics. Preserve the selected language, existing user project and explicit device-operation boundaries.
- Add catalog queries, environment inventory, Python/C++ project generation, application packaging and structured diagnostics. Distinguish local inventory, SDK readiness, device environment and received samples instead of treating one check as proof of the next.

### Robot interfaces and data

- Check in public Aorta Schema and the ROS 2 definitions used by the supported bridge routes. Document exact route names, types, directions and communication primitives, grouped into sensors, cameras, perception, audio, motion, system/peripherals, RCP and SLAM.
- Cover battery, IMU, LiDAR, UWB, GNSS and servo telemetry; camera calibration, H.265 video, AprilTags and JPEG capture. Explain that JPEG request dimensions select the nearest enabled channel and the returned dimensions are authoritative.
- Expose built-in object/person detections and human keypoints, with guidance for presence-triggered interaction. Distinguish object detection from AprilTag results and human keypoints from the robot's own pose.
- Explain body-microphone audio, UWB audio, ASR results and input-completion events, including how to identify the ASR source. Document PCM speaker input and speech-policy query/control separately from captured audio.
- Document locomotion state, command topics, reports, stand/safe-lie-down flows, control-enable and following/navigation services. Keep request admission, task completion and observed device state distinct.
- Cover system/display state, ear-light brightness and light services, application-version queries and power-saving control. Keep read-only observations separate from operations that change device state.
- Provide the complete [mapping and localization workflow](docs/guides/mapping-localization.md): enter the appropriate mode, collect data, save and reload maps, request relocalization and consume maps, odometry, poses and transforms with their coordinate-frame semantics.
- Document [device Agent interfaces](docs/interfaces/agent/README.md): HTTP MCP tool access, dynamic external MCP connection registration/editing, enable/disable and discovery refresh, plus device Skill / AGENTS.md content APIs for upload, readback, backup, deletion and recovery. Keep device runtime content separate from Coding Agent Skills.

### RCP composition and reusable device resources

- Explain `DagPresetRef` and custom `DagSpec` goals, graph/node fields, `NodeCommand` types, parameter ranges, dependencies, parallel work, timeouts, preconditions, resource ownership and cleanup.
- Publish preset references and separate catalogs for body/head trajectories, expression IDs and light modes. Explain how trajectory resource names and expression IDs connect to direct services and RCP nodes, without requiring access to the device installation directory.
- Document configurable motion parameters and supported preparation/posture transitions, so applications can compose supported behaviors rather than copy one task-specific handshake configuration.
- Explain when to use direct capabilities versus RCP, with submission, feedback, terminal results, cancellation and trace correlation. See [DAG authoring](docs/guides/rcp-dag.md) and [control paths](docs/guides/control-paths.md).

### Python/C++ examples and complete applications

- Provide Bazel-built Python and C++ Recipes across all eight interface families, including camera reads/capture, perception and audio input, motion, system/version reads, RCP DAG submission/cancellation and read-only SLAM data.
- Add a read-only health-monitor Blueprint combining robot state, battery and system messages, with Python/C++ implementations, simulation, independent workspace creation, packaging and deployment instructions.
- Include SDK serialization tests, offline previews, bounded sampling, explicit motion/capture options, resource cleanup and actionable errors. Default previews and tests do not contact a robot.
- Distribute SDK and generated bindings as separately downloaded Release assets, with manifests, checksums and license material. Support verified local installation after downloading the required files; a fresh setup still needs the downloads described in the SDK guides.

### Visualization, robot models and hardware references

- Document [Foxglove](docs/guides/foxglove.md) bridge startup, device environment, explicit topic selection and exported topic naming, with wired access and Wi-Fi access through an SSH tunnel.
- Introduce [Vbot Viewer](docs/guides/vbot-viewer.md) for browser-based model inspection, URDF editing and export, separate from live message visualization or physical robot control.
- Bundle the VbotBaboEDU URDF variants and referenced meshes under `assets/robots/foot_quadruped/`, including head-joint servo-limit corrections. Describe model availability and local versus online resources.
- Publish shared quadruped/wheeled-quadruped sensor specifications, back-mounting dimensions, installation drawings and adapter CAD. Shared hardware references do not imply released software support for another robot type.

### Community, security and collaboration

- Direct usage questions, development experience and feature suggestions to [Vbot 超能社区](https://forum.vbot.cn/), with search-first guidance and a sanitized feedback template; use repository issues/PRs for concrete code and documentation changes.
- Publish technical-support and private vulnerability-reporting contact `vbot-edu@vbot.cn`. Explain first-login password changes, public-key SSH, safe storage of session configuration and avoiding device identifiers or credentials in public reports.
- License repository code, documentation, interfaces and company-owned model/hardware assets under Apache-2.0, with `Copyright (c) 2026 VitaDynamics`, attribution and third-party notices.
- Add contribution guides, maintainers/CODEOWNERS, issue/PR templates and CI covering bilingual documents, catalog/Schema consistency, Python/C++ builds, application packaging and SDK integration without robot access.

## V1.6.0

Source snapshot for robot application `V1.6.0`. SDK artifacts remain available through
the separate `edu-sdk-2026.9.24` GitHub Release; this source tag does not create another Release.

- Consolidate version guidance under `docs/compatibility.md` and record the supported application version in the capability catalog.
- Add shared back-mounting drawings and adapter CAD for four-legged and wheeled quadruped robots.
- Publish the private security-reporting email and designate repository administrators as maintainers and code owners.

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
