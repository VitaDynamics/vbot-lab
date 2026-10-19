# Versions and compatibility

<p align="center">English | <a href="compatibility.zh-CN.md">中文</a></p>

## Robot application version

The application version targeted by this repository's device guides, interfaces and
Recipes is **V1.6.0-12**, for `foot_quadruped` EDU. This is an application-version target,
not a minimum-version range or a guarantee for earlier/later releases.
It does not rename the SDK, Schema, development image, system image or peripheral firmware.
Those components retain their own version numbers and pairing requirements below.

The [release configuration](../catalog/release.md) records the component combination
in [release.json](../catalog/release.json). Unfilled fields remain explicit; a locally
consistent configuration does not by itself announce a release or establish device compatibility.

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

The interface reference for application `V1.6.0-12` includes the public topic set, native system state,
static TF, command topics, and the RCP action, alongside
[perception outputs](interfaces/perception.md) and [audio/voice input](interfaces/audio.md).
Check exact route discovery, message types and the configuration limits below on the selected device.

| Component | Current availability | Compatibility checks |
| --- | --- | --- |
| Repository source | Source tag `V1.6.0.12` | Clone the repository, then select this tag as shown in the [quickstart](getting-started/README.md); source references and SDK Release assets have independent versions |
| Development image | dev-v0.0.1 pinned by digest in Compose and release configuration; runs on linux/amd64 and includes ARM64 GCC/G++ cross-compilers | Use the ARM64 SDK and `bazel build --config=arm64` for device C++ binaries; default builds/previews/tests are native; stage ARM64 Python wheels directly |
| Bazel | 7.6.1 scaffold baseline | Validate with the SDK and image |
| [Aorta Python SDK](../packages/aorta/python/README.md) | Distributed as vbot-lab release assets (first release `edu-sdk-*`); the release's `EDU_SDK_MANIFEST.json` records the version pairing | Pin the public version and artifacts |
| Python / ABI | Python 3.10 or newer; SDK wheels are available for macOS arm64, Linux x86_64, and Linux aarch64. Download all four required wheels, including `flatbuffers`, from `edu-sdk-2026.10.14`. The `linux_*` wheels are Ubuntu/glibc builds | Check architecture and native dependencies separately for workstation and device; installation can run offline after the matching wheels are downloaded; optional capture/decode dependencies are prepared separately |
| Workstation native runtime | Distributed as vbot-lab release assets (first release `edu-sdk-*`) as Ubuntu 22.04 archives for x86_64 and aarch64; the release's `EDU_SDK_MANIFEST.json` records the version pairing | Match architecture, system, and SDK; the tested bundle needs glibc 2.34 or newer |
| Off-robot router | Not released. Install Eclipse zenoh `zenohd` 1.10.x from the [official releases](https://github.com/eclipse-zenoh/zenoh/releases), the zenoh minor the SDK is built on; 1.10.1 is the tested version | Match the router minor with the SDK; the robot image provides its own router |
| Device Aorta / ROS 2 tools | Configuration and selected available bridge routes documented for application `V1.6.0-12` | Check public files, shell variables, types, discovery, and actual samples separately |
| [Interface Definitions — public Aorta Schema](../schemas/README.md) | Distributed as vbot-lab release assets (first release `edu-sdk-*`); the release's `EDU_SDK_MANIFEST.json` records the version pairing | Match the SDK version, dependencies, and generated bindings |
| [Recipes](../recipes/README.md) | Python and C++ examples organized by capability, with Bazel targets and offline tests | Validate Python dependencies, Bazel targets, documented interfaces, and expected results |
| [VBOT Blueprints](../blueprints/README.md) | Runnable read-only health monitor in Python and C++, with independent project generation and packaging | Follow the selected language's SDK pairing, configuration, deployment and stopping instructions; synthetic tests do not establish live data availability |
| [Agent HTTP MCP](interfaces/agent/http-mcp.md) | Contract documented for application `V1.6.0-12` | Check runtime availability and Agent-to-tool calls; no server executable is included here |
| [Device Skills / AGENTS.md API](interfaces/agent/content-api.md) | Authoring and HTTP content contract documented for application `V1.6.0-12` | Check route availability and user-content paths; back up before writing, compare readback, and use the content in a new Turn |
| [Coding Agent Skills](../skills/README.md) | `vbot-dev-setup`, `vbot-app-dev` and `vbot-diagnose` cover setup, application development and scoped diagnosis; shared Codex / Claude Code discovery links | Confirm discovery and invocation in the harness you use |
| [Capability catalog](../catalog/README.md) | Local JSON query and validation | Versioned format, references, release gating; not live device discovery |
| Robot application | `V1.6.0-12` | Confirm the installed application version and required interfaces; component versions are separate |

Application `V1.6.0-12` pairs device Aorta `2026.10.16`, ROS 2 bridge `2026.10.12` and
`vbot-agent-harness` `v3.0.5`. Application dependencies are SDK `2026.10.12` / ABI 13,
EDU Schema `2026.10.13-v4` and Release `edu-sdk-2026.10.14`.
Device component and client SDK version numbers need not be identical; use this recorded
pairing rather than changing SDK dependencies to match a CLI version string.

## Device configuration and schema-pack rows

The EDU schema pack numbers its public routes with stable row identifiers; the shipped
`manifest/edu_public_allowlist.json` lists them under `map_rows`. A robot software image
decides which of those rows its access control admits, so match the image against the rows
your application uses.

For application `V1.6.0-12`, the public surface includes the enabled bridge routes for
`/audio/play_pcm` (row 57, pub/sub input) and `/speech_control` (row 58, service).
The paired pack contains 58 numbered public rows; `schemas/ros2/routes.json` has 72
mapping entries because aliases and derived ROS outputs can produce multiple entries.
Older communication configurations can have different subsets; their exclusions are not
the current release's interface list. Match the installed application and route discovery
to the [interface reference](interfaces/aorta-ros2.md) before use.

Software with the EDU router publishes `/opt/vita/aorta/edu/edu_session_peer.json5`; check
with `test -r /opt/vita/aorta/edu/edu_session_peer.json5`. With it, EDU programs may also use
any other topic, service or action name among themselves, in client or peer mode, and
`/opt/vita/aorta/edu/foxglove_bridge.yaml` configures the Foxglove bridge. Without it, the
session connects in client mode only and names outside the admitted rows are dropped.

Schema availability alone does not establish a running provider or publisher. Check the
exact route and type on the selected device. A missing provider, no current input or a
communication mismatch can all appear as a timeout; do not infer the cause from a timeout alone.

### Version queries on the robot

These commands report the system image or individual components, not the supported
application version `V1.6.0-12`. Record them separately from the robot's application-version information.

| Command | Result |
| --- | --- |
| `cat /etc/version` | Prints the installed system-image identifier; do not treat it as the robot application version |
| `aorta --version` | Prints the CLI version; if it reports `0.0.0+unstamped`, it cannot identify the component release |
| `zenohd --version` | Prints the router version; if it reports `0.0.0+unstamped`, it cannot identify the component release |

## C++ example pairing

The [C++ SDK guide](../packages/aorta/cpp/README.md) pins SDK 2026.10.12 / ABI 13 with
EDU Schema 2026.10.13-v4, Ubuntu 22.04 x86_64/aarch64 artifacts and C++17.
The image includes ARM64 GCC/G++ 11 cross-compilers. Use the ARM64 SDK with
`bazel build --config=arm64` for device binaries; default Bazel builds and local tests
use the native SDK/compiler. Cross-built binaries run on the robot, not in the AMD64 container.
Camera RGB decoding is an optional FFmpeg target requiring target-architecture
development/runtime libraries; basic examples need no FFmpeg.
Build success, SDK pairing and live device interface availability are separate checks.
