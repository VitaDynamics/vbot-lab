# Four-legged EDU model resources

<p align="center">English | <a href="README.zh-CN.md">中文</a></p>

Model: **VbotBaboEDU**. Robot type: `foot_quadruped`.

This directory currently reserves the model location only. **No URDF, meshes or
textures are bundled.** [model.json](model.json) reports `availability: not_bundled`
and `urdf: null`; there is no model to load from this checkout yet.

Open the [online model](https://vbot-viewer.vitarobot.cc/?model=VbotBaboEDU) and follow
the [Viewer guide](../../../docs/guides/vbot-viewer.md) to inspect its structure.
The website's model is separate from this local resource directory.

## Resource layout

- `urdf/`: reserved for URDF descriptions, including their entry file.
- `meshes/`: reserved for the geometry referenced by those descriptions.
- `textures/`: optional; created only when model files require it.
- `model.json`: concrete model identifier, robot type, public Viewer URL and local availability.

URDF and mesh placeholders do not contain a sample or fallback robot. There is no
runnable model target; `BUILD.bazel` exposes only repository metadata/documentation
for the repository checks. Model-specific hardware revisions, coordinate conventions,
asset versions and license terms are not declared until a model package is provided.

For device development, use the [four-legged EDU guide](../../../docs/robots/foot_quadruped/README.md).
For model questions or suggestions, see [Community & Support](../../../docs/community/README.md).
