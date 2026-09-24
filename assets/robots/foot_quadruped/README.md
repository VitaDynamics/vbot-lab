# Four-legged EDU model resources

<p align="center">English | <a href="README.zh-CN.md">中文</a></p>

Model: **VbotBaboEDU**. Robot type: `foot_quadruped`.

This directory bundles the VbotBaboEDU URDF and the meshes it references.
[model.json](model.json) reports `availability: bundled`, the `urdf` entry file and the
mesh list. Its paths are relative to this directory. No textures are bundled.

## Resource layout

- `urdf/VbotBaboEDU.urdf`: default entry, with the body, four legs and head yaw/pitch chain.
- `urdf/VbotBaboEDU_*.urdf`: variants `mock_head`, `mock_head_silence` (silenced foot meshes),
  `backboard` and `backboard_bracket`.
- `meshes/`: STL geometry referenced by the URDF files.
- `model.json`: model identifier, robot type, entry file, mesh list and public Viewer URL.

## Load the URDF

Mesh paths use `package://VbotBaboEDU/meshes/...` URIs. Map the `package://VbotBaboEDU/`
prefix to this directory in your URDF loader, or place this directory in a ROS 2
package named `VbotBaboEDU`. Expected result: the loader resolves every mesh and shows
19 joints in `VbotBaboEDU.urdf`.

Model poses, joint limits, inertials and meshes are descriptions for visualization and
simulation, not robot commands or hardware measurements. These files are a snapshot; the
[online model](https://vbot-viewer.vitarobot.cc/?model=VbotBaboEDU) can change independently
(see the [Viewer guide](../../../docs/guides/vbot-viewer.md)). `model_license` is not declared yet.

For device development, use the [four-legged EDU guide](../../../docs/robots/foot_quadruped/README.md).
For model questions or suggestions, see [Community & Support](../../../docs/community/README.md).
