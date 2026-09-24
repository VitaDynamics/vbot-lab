# Capabilities & Interfaces

<p align="center">English | <a href="README.zh-CN.md">中文</a></p>

A local index of workflows and interfaces, not a device-discovery service.
Use [capabilities.json](capabilities.json) to locate the relevant workflow, interface,
SDK requirement, Recipe, and verification boundary without reading every document.

## Query the catalog

From the checkout root, using Python 3.10+:

```bash
python3 tools/vbot_catalog.py
python3 tools/vbot_catalog.py --robot-type foot_quadruped --capability robot.state.subscribe
python3 tools/vbot_catalog.py --robot-type foot_quadruped --capability device.environment.check
python3 tools/vbot_catalog.py --robot-type foot_quadruped --capability device.application.autostart
python3 tools/vbot_catalog.py --robot-type foot_quadruped --capability robot.sensors
python3 tools/vbot_catalog.py --robot-type foot_quadruped --capability robot.cameras
python3 tools/vbot_catalog.py --robot-type foot_quadruped --capability robot.perception
python3 tools/vbot_catalog.py --robot-type foot_quadruped --capability robot.audio
python3 tools/vbot_catalog.py --robot-type foot_quadruped --capability robot.locomotion
python3 tools/vbot_catalog.py --robot-type foot_quadruped --capability robot.system-peripherals
python3 tools/vbot_catalog.py --robot-type foot_quadruped --capability robot.rcp
python3 tools/vbot_catalog.py --robot-type foot_quadruped --capability robot.slam.mapping-localization
python3 tools/vbot_catalog.py --robot-type wheel_quadruped --capability device.agent.content
```

The query is offline. Exit 0 means the query succeeded, not that a capability can run.
Inspect each result's `decision`: `local_only`, `requires_robot_selection`, `blocked_release`,
`not_applicable`, `blocked_integration`, or `requires_device_verification`.
Unknown identifiers or invalid data return exit 2. A blocked decision is still a valid query result.

Robot interfaces are grouped by family. Query perception once for detections and human
keypoints, or audio once for frames, recognized text, and events. The query is a documentation
lookup, not a request to subscribe to every route in that family. Choose the needed outputs
in its guide; command inputs still require deliberate operation.

## Format version 1

This is a VBOT Lab convention, explicitly consumed by its Skills and tools, not a universal
Coding Agent manifest. JSON keeps validation available in the Python standard library.
All paths are relative to the checkout root. Machine-readable identifiers and paths have one
source; English Markdown references have paired `.zh-CN.md` documents for Chinese readers.

| Field | Meaning |
| --- | --- |
| `availability` | `implemented` local entry, `documented` device contract, or `planned` integration; not live readiness |
| `robot_types` | Scope of this capability; an empty list is only allowed for local inventory, never “all robots” |
| `execution_location` | Developer host/container, device service, developer-owned tool service, or `device_shell` (run after device login) |
| `interface_kind` | Communication category, including `pub_sub`, `service`, and `action`; `null` means not selected, not inferred |
| `reference` | Authoritative behavior/interface document |
| `skill`, `tool`, `recipe` | Corresponding checkout resources, or `null` when absent; a Recipe reference can be an outline |
| `requires_sdk` | Whether the workflow depends on the Aorta Python SDK |
| `effect` | Local read-only, device read-only, or operation-dependent; not an authorization grant |
| `minimum_firmware` | Known minimum version, or `null` when unknown; unknown does not mean any version |
| `verification` | Entry check status: `local_tests` for tested local tools, `documentation_only` for documented interfaces/workflows, or `not_verified` for unchecked entries |

`documentation_only` entries guide you to interface instructions rather than an executable
helper. For device entries, `requires_device_verification` means to check the selected
device's interface availability and operating prerequisites before following the workflow.

SDK metadata records integration and version separately. Robot profiles distinguish the current
release target from planned releases; empty `models` means exact models are not recorded.
The robot profile's `application_version` is the supported application target: `V1.6.0`
for `foot_quadruped`, and `null` for unreleased types. Queries return it under `robot`.
It is not the SDK or system-image version and does not mean "this version or newer".
`minimum_firmware` remains a separate optional lower bound; `null` does not remove the
declared application target or establish compatibility with other versions.
Hardware applicability is not software support. Both robot-dog profiles reference the same
sensor/connection sources; the bipedal profile does not inherit them.

The loader checks format versions, identifiers, enum values, reference existence, robot membership,
and executable-entry availability. It never executes a command from catalog data.
See [offline tests](../tests/README.md) for validation and [compatibility](../docs/compatibility.md)
for the human-readable matrix.

## Follow the source

- [Device environment](../docs/getting-started/device-environment.md): vbot shell configuration and offline inventory, independent of SDK integration.
- [User-program autostart](../docs/guides/user-autostart.md): boot entry, explicit environment, logs, and disabling startup; configuration and application launches change device state.
- [Aorta / ROS 2](../docs/interfaces/aorta-ros2.md): public topics, subscription/publish directions, types, service mappings, and the RCP action; not SDK recipe readiness.
- [Interface families](../docs/interfaces/README.md): sensors, cameras, perception, audio, locomotion, system/peripherals, RCP, and SLAM definitions and usage.
- [Mapping and localization](../docs/guides/mapping-localization.md): native Aorta SLAM workflow and state-based completion checks; mode changes require explicit intent.
- [Aorta Python SDK](../packages/aorta/python/README.md): release wheel installation documented.
- [Schema](../schemas/README.md): checked-in field/type definitions.
- [Interface reference](../docs/interfaces/README.md): exact documented contracts, including device Agent APIs.
- [Recipes](../recipes/README.md): planned single-task implementations.
- [Skills](../skills/README.md): Coding Agent workflows, not device runtime content.

Do not copy topic names, fields, units, or HTTP route lists into this index by hand.
They remain in the referenced Schema/contract sources; generate structural indexes from those
sources when integrated. The application target is `V1.6.0`; check the installed application
and runtime availability on the selected device.

Cameras, audio, locomotion and RCP remain grouped by interface family; the `recipe` field links to the
corresponding SDK example rather than splitting checks by Topic. The family CLI guide remains usable
without the SDK (`requires_sdk=false`); live execution of its linked Python Recipe requires the wheels.
`implemented` means an executable entry exists, not that a device is connected. The application
target does not replace route checks on the selected device.

`sdk.cpp` records the C++ version, ABI, Schema pairing and setup guide.
Recipe entries expose `implementations.python` and `implementations.cpp`, each with source
and Bazel target. The existing `tool` retains the Python entry for compatibility; choose
C++ through implementations rather than guessing its entry point. Languages share one
interface-family entry and the same operation boundaries.
