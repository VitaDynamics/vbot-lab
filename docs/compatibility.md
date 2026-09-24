# Versions and compatibility

<p align="center">English | <a href="compatibility.zh-CN.md">中文</a></p>

## Robot application version

The application version targeted by this repository's device guides, interfaces and
Recipes is **V1.6.0**, for `foot_quadruped` EDU. This is an application-version target,
not a minimum-version range or a guarantee for earlier/later releases.
It does not rename the SDK, Schema, development image, system image or peripheral firmware.
Those components retain their own version numbers and pairing requirements below.

## SDK downloads and version selection

Download the SDK from [GitHub Releases](https://github.com/VitaDynamics/vbot-lab/releases)
under `edu-sdk-<date>`. Each release includes `EDU_SDK_MANIFEST.json` for version pairing
and `SHA256SUMS` for artifact checksums. Check the release's pre-release status and use
the matching [Python](../packages/aorta/python/README.md) or
[C++](../packages/aorta/cpp/README.md) installation guide.

Before choosing or upgrading a version:

- Check your robot type, product model, hardware revision, application and firmware versions.
- Match the development image, SDK, Schema and examples using the matrix below; use the documented image tag or digest.
- Review API changes and back up your device Skills, AGENTS.md and application data.
- Verify read-only access first, then run your application under the documented safety conditions.

Device Skill / AGENTS.md compatibility and Coding Agent Skill compatibility are tracked separately.

## Robot types and EDU release scope

| Robot type | EDU release scope | Sensor reference | Development entry points |
| --- | --- | --- | --- |
| [foot_quadruped](robots/foot_quadruped/README.md) | Current release target | [Shared robot-dog specification](hardware/quadruped-common/sensors.md) | Connection, shell setup, Aorta / ROS 2, and Agent interface guides available; see component availability below |
| [wheel_quadruped](robots/wheel_quadruped/README.md) | Future release; guide not released | [Same shared robot-dog specification](hardware/quadruped-common/sensors.md) | Not released for EDU |
| [foot_humanoid](robots/foot_humanoid/README.md) | Future release; guide not released | Pending; robot-dog parameters do not apply | Not released for EDU |

Exact product models and hardware revisions are not yet recorded here.
When selecting a version, check the combination of robot type, model / hardware revision,
firmware, development image, SDK, Schema set, and example / interface coverage.
Neither the build identifier nor shared hardware parameters establish software compatibility.

## Component integration status

For `foot_quadruped` EDU, follow the [vbot shell configuration](getting-started/device-environment.md)
and [available Aorta / ROS 2 interface mappings](interfaces/aorta-ros2.md).
Device CLI availability and workstation SDK installation are separate requirements.

The interface reference for application `V1.6.0` includes the public topic set, native system state,
static TF, command topics, and the RCP action, alongside
[perception outputs](interfaces/perception.md) and [audio/voice input](interfaces/audio.md).
Check exact route discovery, message types and the configuration limits below on the selected device.

| Component | Current availability | Compatibility checks |
| --- | --- | --- |
| Repository source snapshot | Git tag `V1.6.0` | The source tag is separate from the SDK Release and its downloadable artifacts |
| Development image | dev-v0.0.1 tag configured | Pull the image, pin its digest, and check required tools |
| Bazel | 7.6.1 scaffold baseline | Validate with the SDK and image |
| [Aorta Python SDK](../packages/aorta/python/README.md) | Distributed as vbot-lab release assets (first release `edu-sdk-*`); the release's `EDU_SDK_MANIFEST.json` records the version pairing | Pin the public version and artifacts |
| Python / ABI | Python 3.10 or newer; SDK wheels are available for macOS arm64, Linux x86_64, and Linux aarch64. Download the SDK from GitHub Releases; `edu-sdk-2026.9.24` also attaches the `flatbuffers` wheel `vbot_edu_msgs` needs, which is available from PyPI as well. The `linux_*` wheels are Ubuntu/glibc builds | Check architecture and native dependencies separately for workstation and device; offline installation requires a separately prepared complete wheelhouse |
| Workstation native runtime | Distributed as vbot-lab release assets (first release `edu-sdk-*`) as Ubuntu 22.04 archives for x86_64 and aarch64; the release's `EDU_SDK_MANIFEST.json` records the version pairing | Match architecture, system, and SDK; the tested bundle needs glibc 2.34 or newer |
| Off-robot router | Not released. Install Eclipse zenoh `zenohd` 1.10.x from the [official releases](https://github.com/eclipse-zenoh/zenoh/releases), the zenoh minor the SDK is built on; 1.10.1 is the tested version | Match the router minor with the SDK; the robot image provides its own router |
| Device Aorta / ROS 2 tools | Configuration and selected available bridge routes documented for application `V1.6.0` | Check public files, shell variables, types, discovery, and actual samples separately |
| [Interface Definitions — public Aorta Schema](../schemas/README.md) | Distributed as vbot-lab release assets (first release `edu-sdk-*`); the release's `EDU_SDK_MANIFEST.json` records the version pairing | Match the SDK version, dependencies, and generated bindings |
| [Recipes](../recipes/README.md) | Python and C++ examples organized by capability, with Bazel targets and offline tests | Validate Python dependencies, Bazel targets, documented interfaces, and expected results |
| [VBOT Blueprints](../blueprints/README.md) | Planned; no runnable application | Validate dependencies, deployment, expected results, and stopping procedures per application |
| [Agent HTTP MCP](interfaces/agent/http-mcp.md) | Contract documented for application `V1.6.0` | Check runtime availability and Agent-to-tool calls; no server executable is included here |
| [Device Skills / AGENTS.md API](interfaces/agent/content-api.md) | Authoring and HTTP content contract documented for application `V1.6.0` | Check route availability and user-content paths; back up before writing, compare readback, and use the content in a new Turn |
| [Coding Agent Skills](../skills/README.md) | Scoped environment checks or full setup through SDK preparation, deployment and read-only state subscription; shared Codex / Claude Code discovery links | Confirm discovery and invocation in the harness you use |
| [Capability catalog](../catalog/README.md) | Local JSON query and validation | Versioned format, references, release gating; not live device discovery |
| Robot application | `V1.6.0` | Confirm the installed application version and required interfaces; component versions are separate |

Use matching firmware, SDK, Schema, and native-library versions when building and running applications.

## Device configuration and schema-pack rows

The EDU schema pack numbers its public routes with stable row identifiers; the shipped
`manifest/edu_public_allowlist.json` lists them under `map_rows`. A robot software image
decides which of those rows its access control admits, so match the image against the rows
your application uses.

The application target remains `V1.6.0`. The configurations below describe route access,
not additional supported application versions; a version label alone does not establish route availability.

| Device communication configuration | Admitted schema-pack rows | Notes |
| --- | --- | --- |
| Legacy client-only configuration | 1–49 and 51–52 | Service rows 17 (`/get_jpeg_images`) and 32 (`/rcp/function_input`) are present but disabled; topic rows 50 and 53–56 are absent from the image's ACL |
| EDU-router configuration | 1–55 | Row 56 (`uwb/audio_done`) is absent from this configuration |

Software with the EDU router publishes `/opt/vita/aorta/edu/edu_session_peer.json5`; check
with `test -r /opt/vita/aorta/edu/edu_session_peer.json5`. With it, EDU programs may also use
any other topic, service or action name among themselves, in client or peer mode, and
`/opt/vita/aorta/edu/foxglove_bridge.yaml` configures the Foxglove bridge. Without it, the
session connects in client mode only and names outside the admitted rows are dropped.

The `edu-sdk-2026.9.24` release ships a 56-row schema pack. Definitions for rows 50 (`system/sm_status`),
53 (`perception/detections2d`), 54 (`perception/poses`), 55 (`audio/uwb_adpcm_segment`), and
56 (`uwb/audio_done`) do not override the configuration limits above. Rows 17 and 32 cannot
be used with the legacy configuration either. Denials are silent drops: an unavailable row appears as a
missing provider or a timeout, not as an error message.

### Version queries on the robot

These commands report the system image or individual components, not the supported
application version `V1.6.0`. Record them separately from the robot's application-version information.

| Command | Result |
| --- | --- |
| `cat /etc/version` | Prints the installed system-image identifier; do not treat it as the robot application version |
| `aorta --version` | Prints the CLI version; if it reports `0.0.0+unstamped`, it cannot identify the component release |
| `zenohd --version` | Prints the router version; if it reports `0.0.0+unstamped`, it cannot identify the component release |

## C++ example pairing

The [C++ SDK guide](../packages/aorta/cpp/README.md) pins SDK 2026.9.23 / ABI 12 with
EDU Schema 2026.9.24-v4, Ubuntu 22.04 x86_64/aarch64 artifacts and C++17.
Examples use native Bazel compilation, not a supplied cross-compilation toolchain.
Camera RGB decoding is an optional FFmpeg target requiring target-architecture
development/runtime libraries; basic examples need no FFmpeg.
Build success, SDK pairing and live device interface availability are separate checks.
