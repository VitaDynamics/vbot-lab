# Four-legged robot dog EDU

<p align="center">English | <a href="README.zh-CN.md">中文</a></p>

- Build identifier: `foot_quadruped`.
- EDU scope: the only robot type in the current release scope.
- Supported robot application version: `V1.6.0`.
- Available guides: connection, shell setup, hardware, SLAM, and Agent interfaces.
  Python/C++ Recipes are available; see the compatibility matrix for component availability.

## Development entry points

- [Vbot Viewer](../../guides/vbot-viewer.md) and [model resources](../../../assets/robots/foot_quadruped/README.md): inspect the online model; or load the bundled URDF and meshes locally.

- [Wired connection and SSH login shared by both robot-dog types](../quadruped-common/connection.md): connect the adapter, configure the computer's network interface, and log in with the `vbot` account.
- [Device shell setup](../../getting-started/device-environment.md) and [Aorta / ROS 2 compatibility](../../interfaces/aorta-ros2.md): after SSH login, configure the `vbot` environment in the device terminal and check CLI access without waiting for SDK integration.
- [Sensor specifications shared by the two robot-dog types](../../hardware/quadruped-common/sensors.md).
- [Back mounting and arm adapter plate shared by both robot-dog types](../../hardware/quadruped-common/back-mounting.md): mechanical dimensions, CAD files and fastener reference.
- [Agent capabilities](../../interfaces/agent/README.md) and [integration checklist](../../guides/agent-integration.md): HTTP MCP, Skills, and runtime AGENTS.md for a trusted developer on S100; confirm the delivered version separately.
- [Compatibility matrix](../../compatibility.md): confirm the exact model,
  hardware revision, firmware, SDK, and interface availability before device development.
- [Shared quickstart](../../getting-started/README.md) and
  [development workflow](../../development/README.md): workstation environment and development steps.
- [Interface reference](../../interfaces/README.md) and [Recipes](../../../recipes/README.md):
  use the interfaces documented and validated for this type.

## Type-specific chapters to complete

Device identification and prerequisites, public-interface coverage,
example prerequisites, user-program deployment differences, and troubleshooting
will be added under this directory as they are validated.
The shared sensor specification is not evidence that the same firmware or motion interfaces
can be used on `wheel_quadruped`.

Return to the [robot-type guide index](../README.md).
