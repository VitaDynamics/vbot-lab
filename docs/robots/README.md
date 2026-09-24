# Robot-type guides

<p align="center">English | <a href="README.zh-CN.md">中文</a></p>

Choose a guide by robot type. The current EDU release scope is limited to the four-legged
robot dog; four-wheeled robot-dog and bipedal EDU guides
are reserved for later releases.
Type-specific directory names match the canonical `robot_type` identifiers used by the build system.
`quadruped-common/` holds content shared by the two robot-dog types; it is not a build identifier.
These identifiers select documentation; their presence is not proof of EDU support.

| Robot type | Build identifier / guide | EDU scope | Documentation status |
| --- | --- | --- | --- |
| Four-legged robot dog | [foot_quadruped](foot_quadruped/README.md) | Current release target | [Shared connection guide](quadruped-common/connection.md), shell setup, hardware reference, and interface workflows available; Python/C++ Recipes available |
| Four-wheeled robot dog | [wheel_quadruped](wheel_quadruped/README.md) | Future release | [Shared connection guide](quadruped-common/connection.md) and hardware reference available; no released complete EDU guide |
| Bipedal robot | [foot_humanoid](foot_humanoid/README.md) | Future release | Placeholder; hardware reference and EDU guide pending |

Exact product models, firmware, SDK, and interface support belong in the
[compatibility matrix](../../release/compatibility.md).

## Documentation structure

- Shared chapters: [quickstart](../getting-started/README.md),
  [development workflow](../development/README.md), [interfaces](../interfaces/README.md),
  and [guides](../guides/README.md). Keep common procedures here rather than copying them per robot type.
- Robot-dog shared content: keep the [wired connection and SSH login guide](quadruped-common/connection.md)
  in `docs/robots/quadruped-common/`, with links from both robot-dog guides. This does not
  apply to bipedal robots or change either type's EDU release status.
- Type-specific content: use `docs/robots/<robot_type>/` for connection differences,
  device prerequisites, available interfaces, examples, deployment differences, and troubleshooting.
  Add chapters as the corresponding EDU release is integrated and validated.
- Hardware: keep specifications in [docs/hardware/](../hardware/README.md).
  The two robot-dog types link to a single [shared sensor specification](../hardware/quadruped-common/sensors.md).
  Bipedal hardware must have its own reviewed specification; it does not inherit robot-dog parameters.
- Compatibility: distinguish robot type, exact product model / hardware revision,
  and firmware / SDK version. A robot type or a shared sensor set alone is not a compatibility guarantee.

When adding a robot type or changing release status, update this index, the type-specific
guide, the hardware applicability index, and the compatibility matrix in both languages.
If hardware variants diverge, add separately named specifications with explicit applicability
instead of silently replacing a shared parameter set or duplicating it in multiple guides.
