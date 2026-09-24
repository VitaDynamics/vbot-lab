# Development workflow

<p align="center">English | <a href="README.zh-CN.md">中文</a></p>

Current device workflows target foot_quadruped; for type-specific details see [robot-type guides](../robots/README.md).

1. Prepare the [development container](../../docker/README.md) and install the release wheel pairing through [Python SDK](../../packages/aorta/python/README.md).
2. Use the [capability catalog](../../catalog/README.md) to select an interface and a program from [Recipes](../../recipes/README.md); build, test and preview it with Bazel in the container.
3. Follow the [shared connection guide](../robots/quadruped-common/connection.md) to log in over SSH, then configure the [device environment](../getting-started/device-environment.md).
4. Follow [Python deployment](python-deployment.md) to package and transfer a selected recipe plus ARM64 wheels, then create the venv in a new device application directory as vbot. Run read-only examples before explicitly running control examples with their safety prerequisites.
5. Debug long-running programs interactively before configuring [user-program autostart](../guides/user-autostart.md) with startup, logs and disable procedures.

Python source normally needs no cross-compilation, but native libraries must match the target architecture and ABI. Do not copy a workstation venv to the robot. Current Recipes run live on the device; they do not configure workstation-to-Aorta routing. A workstation build does not establish device connectivity.

Complete applications belong in [VBOT Blueprints](../../blueprints/README.md) and remain planned. For task routing and context selection see [Agent quickstart](../agents/README.md).

For live topic visualization, follow [Foxglove viewing](../guides/foxglove.md).
The bridge runs on the device; the viewer connects from your computer.

## C++ path

For builds without registry access, use the [offline build guide](offline-build.md).

For C++ applications, follow the [C++ SDK guide](../../packages/aorta/cpp/README.md) for a compiler
and architecture-matching release artifacts; no Python venv is needed. Select the Recipe's
`:main_cpp` target, preview on the builder, then deploy ARM64 executables and the Aorta shared
runtime over SSH. Camera `:main_cpp_decode` additionally needs FFmpeg. Never mix workstation
and device native dependencies. Configure the session in the device shell before explicit
execution; the same Recipe defines safety conditions and completion semantics.
