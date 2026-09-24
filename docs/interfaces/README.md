# Public interface reference

<p align="center">English | <a href="README.zh-CN.md">中文</a></p>

Use the [capability catalog](../../catalog/README.md) to select the relevant interface and check
release scope. The catalog indexes these contracts; it does not establish live device availability.

## Agent extension interfaces

The [Agent capability reference](agent/README.md) documents HTTP MCP, device Skills, and runtime AGENTS.md,
including the [content injection API](agent/content-api.md),
for the current four-legged EDU scope. See the [integration guide](../guides/agent-integration.md)
for connection steps, protocol checks, and troubleshooting.
Confirm interface availability against your device's firmware and runtime version.

## Aorta and robot interfaces

The [Aorta / ROS 2 reference](aorta-ros2.md) lists the public topic set with communication
primitives, directions, Aorta/ROS types, and mappings, plus services and the RCP task action. Start with
[device shell setup](../getting-started/device-environment.md) for CLI discovery and read-only samples.
Select an interface family below. Each chapter covers its purpose, key data definitions,
reading workflow, and recovery. A family is one entry in the capability catalog; its routes
retain their distinct types and operating conditions. Inspect only what the task needs.

| Family | Definition and usage guide |
| --- | --- |
| Sensors | [Hardware telemetry](sensors.md): battery, IMU, LiDAR, UWB, GNSS, and servo feedback |
| Cameras | [Cameras and AprilTags](cameras.md): calibration, video decoding, and tag results |
| Perception | [Object detection and human keypoints](perception.md): presence and gesture inputs |
| Audio | [Audio and speech input](audio.md): audio frames, ASR text, voice events, and input completion |
| Locomotion | [State, reports, and control](locomotion.md): correlate requests, distinguish outputs from commands |
| System and peripherals | [System, display, and lights](system-peripherals.md): state interpretation and brightness control |
| RCP | [Tasks and tracing](rcp.md): action lifecycle, cancellation, and correlated events |
| SLAM | [Mapping and localization](../guides/mapping-localization.md): maps, poses, transforms, and mode transitions |

Field definitions are in [Schema](../../schemas/README.md); executable Python examples are in
[Recipes](../../recipes/README.md), with installation in the [SDK guide](../../packages/aorta/python/README.md).
Detailed Aorta interface pages must record:

- Function, public availability, supported `robot_type` identifiers, exact models / hardware revisions, and minimum firmware version.
- Exact Aorta route, communication primitive, and developer-side direction.
- Schema, field semantics, units, coordinate frames, and timestamp conventions.
- Preconditions, timeouts, error handling, and resource cleanup.
- Python SDK calls, buildable examples, and validation results.
- Verified ROS2 mappings when they exist; otherwise, explicitly mark them as not applicable.

Schema and registration metadata are the source of structural facts;
behavior and safety conditions still require manual documentation.
