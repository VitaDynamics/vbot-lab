# VBOT Lab agent instructions

<p align="center">English | <a href="AGENTS.zh-CN.md">中文</a></p>

Help users build applications for VBOT EDU robots. Start with the task and load only its
relevant references; this repository is not a device runtime.

## Route the task

| User task | Start here |
| --- | --- |
| Check or set up the developer environment | [vbot-dev-setup](skills/vbot-dev-setup/SKILL.md), then [environment guide](docs/getting-started/README.md) |
| Configure the vbot device shell or check Aorta / ROS 2 access | [device environment](docs/getting-started/device-environment.md), [vbot-dev-setup](skills/vbot-dev-setup/SKILL.md), and [interface scope](docs/interfaces/aorta-ros2.md) |
| Find supported capabilities or select an interface | [catalog](catalog/README.md), then the referenced interface document |
| Read hardware telemetry or camera data | [sensors](docs/interfaces/sensors.md) or [cameras](docs/interfaces/cameras.md); select only the required streams |
| Detect a person, greet on appearance, or use human keypoints | [perception interfaces](docs/interfaces/perception.md); start with built-in detections, not AprilTags or a new video/model pipeline |
| Receive audio, recognized text, or voice events | [audio](docs/interfaces/audio.md); one family for frames, ASR, voice events, and UWB input completion |
| Observe or control motion | [locomotion](docs/interfaces/locomotion.md); distinguish state/report subscriptions from control inputs |
| Observe system/display state or use ear lights | [system and peripherals](docs/interfaces/system-peripherals.md) |
| Compose, execute or trace an RCP task | [DAG authoring](docs/guides/rcp-dag.md), [RCP presets](docs/guides/rcp-presets.md), then [RCP](docs/interfaces/rcp.md); distinguish preset goals from nodes and preserve resource/lifecycle constraints |
| Select body/head trajectories, screen expressions or light modes | [Device resources](docs/resources/README.md); for RCP node fields use [NodeCommand reference](docs/interfaces/rcp-commands.md) |
| Check odometry, build/save a map, or localize | [Mapping and localization](docs/guides/mapping-localization.md); distinguish read-only checks from mode changes |
| Develop a Python application | [Aorta Python SDK](packages/aorta/python/README.md), [Recipes](recipes/README.md), and the selected capability |
| Develop a C++ application | [Aorta C++ SDK](packages/aorta/cpp/README.md), [Recipes](recipes/README.md), and the selected capability; explicitly build :main_cpp |
| Start a user program after device reboot | [User-program autostart](docs/guides/user-autostart.md); preserve existing startup commands and distinguish boot launch from crash recovery |
| Understand a device or connect to it | [robot guides](docs/robots/README.md); confirm the user's robot type first |
| Inspect a robot model, joints or URDF | [Vbot Viewer](docs/guides/vbot-viewer.md), then [robot models](assets/robots/README.md); read model.json availability before assuming local model files exist |
| Get help or prepare a feedback report | [Community & Support](docs/community/README.md); draft a minimal, sanitized report for user review, not automatic posting |
| Author or inject device Skills / AGENTS.md | [device content API](docs/interfaces/agent/content-api.md), not developer-side Skills |
| Modify VBOT Lab itself | [Contributing](CONTRIBUTING.md) and relevant tests |

For another application workspace, follow [Agent quickstart](docs/agents/README.md).
Resolve a linked Skill to its physical checkout before using its relative resources.

## Facts and scope

- The current EDU release target is `foot_quadruped`. Other robot types are planned, even when hardware or connection guides are shared.
- Use the capability catalog as an index, not proof of live availability. Unknown firmware / SDK versions, routes, and ROS2 mappings stay unknown; do not invent them.
- Use the published wheel pairing in the Python SDK guide and the checked-in public Schema. Preserve Aorta package names and APIs. Recipes have offline previews and explicit device execution; building a target does not verify live compatibility.
- Device Aorta CLI access is separate from SDK integration. ROS 2 uses a device-local bridge subset; use documented mappings and limitations, not identical-name assumptions.
- Field and type facts belong to Schema; behavior and safety belong to the linked interface documentation. Skills reference these sources instead of duplicating them.
- Keep developer-side Coding Agent Skills in `skills/`; `.agents/skills/` and `.claude/skills/` expose that same source. They are not uploaded to `vbot-agent-harness`.
- Application code uses Python or C++ with Bazel. Development containers run on the workstation; device programs use the `vbot` account.

## Execution and evidence

- Environment inventory helpers are offline and read-only. They do not install tools, pull images, access Docker, connect over SSH, or contact robot APIs. Device configuration and live read-only sampling are separate, requested steps in the device guide.
- Prefer public-key SSH for device operations. Follow the [connection guide](docs/robots/quadruped-common/connection.md): reuse working key-based access, or guide the user through setup first, then verify non-interactive login from the environment that will run subsequent commands. Do not silently fall back to an embedded password. Installing a public key is a setup change, not part of a read-only check; never copy a private key to the robot or overwrite existing keys.
- Use the user's selected device address or SSH alias. If SSH is unreachable or refused, stop and ask the user to connect the device or provide its actual IP. Report authentication and host-key failures separately; do not scan for another device or bypass host-key verification.
- Match the user's requested scope. Before device writes, deployment, content injection, or motion, establish authorization, the intended device/version, and the documented preconditions. For motion, confirm a safe workspace and stopping procedure.
- Missing dependencies or unavailable interfaces are blockers to report, not reasons to improvise an API or change device permissions, quotas, or services.
- Viewer model edits/poses are not physical robot commands. Distinguish local variants from shared keyframe changes; do not infer a control API from UI controls or turn an exported model into a device deployment.
- For unresolved usage questions, offer the relevant community category and a reviewed report draft. Do not publish posts or upload logs without an explicit request; keep vulnerability details out of public channels.
- Separate local checks, build/test results, harness-session verification, and device verification. A successful build is not a successful device operation.
- Default tests never contact or control real devices. See [test scope](tests/README.md) and [Agent workflow checks](tests/agent-scenarios/README.md).

## Documentation and changes

Keep documentation English-default with paired `.zh-CN.md` pages and same-language links.
Write chapters around tasks, prerequisites, steps, and expected results. Keep project positioning
on the homepage; do not repeat audience statements in each chapter.
Prioritize correct, complete usage workflows. Keep device test reports and sampled performance
or accuracy results out of usage guides.
Retain interface contracts, operating limits, completion checks, and troubleshooting steps.
Use `VBOT EDU robots` / `VBOT EDU 机器人` with this capitalization.
Read [Contributing](CONTRIBUTING.md) before changing layout or shared robot documentation.
Validate with `python3 tests/check_repository.py`, `python3 tests/test_agent_workspace.py`,
and the applicable Bazel targets. Do not commit or publish unless requested.
