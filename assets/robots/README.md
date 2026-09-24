# Robot models

<p align="center">English | <a href="README.zh-CN.md">中文</a></p>

Robot-description resources live under `assets/robots/<robot_type>/`, separately
from documentation screenshots and communication Schema. Each type's `model.json`
identifies its model and whether local files are available.

| Robot type | Model entry | Local resources |
| --- | --- | --- |
| `foot_quadruped` | [VbotBaboEDU](foot_quadruped/README.md) | URDF and meshes bundled |

Use [Vbot Viewer](../../docs/guides/vbot-viewer.md) to browse the online model.
Online availability does not mean its files are included in this checkout or that
every robot type has released EDU software support. No model resources are provided
here for `wheel_quadruped` or `foot_humanoid` yet.

Within a type directory, `urdf/` holds robot descriptions, `meshes/` holds geometry,
and `textures/` is added only when required. The concrete model is recorded in
`model.json`, not in an extra model-name directory. Local paths in that metadata
are relative to the type directory; `null` is not an importable model path.

When models are provided, use their accompanying scope and licensing information.
An online model and a repository snapshot can change independently. Model poses,
limits and physical properties are descriptions, not robot commands or hardware measurements.
