# Development workflow

<p align="center">English | <a href="README.zh-CN.md">中文</a></p>

## Execution locations

Read-only repository checks may run on the host or a CI runner. Bazel builds and tests,
Recipe previews, SDK execution checks, application packaging and build-dependency preparation
must run inside the matching development container, including in CI. The host may invoke
Docker to run those operations, but must not fall back to its own toolchain. Robots run
deployed applications, not builds, packaging or development previews.

| Operation | Where to run |
| --- | --- |
| Repository layout, bilingual links, Schema inventory, release metadata and mocked tool-policy checks | Host or CI runner: `python3 tools/run_checks.py --scope repository` |
| Host tool inventory, Docker readiness and existing-container selection | Host |
| SDK installation/import checks, Bazel build/test/run, Recipe previews and simulated application tests | Matching development container, including CI |
| Dependency bundles and application packages | Matching development container |
| SSH and transfer of already-prepared artifacts | The authorized host/container with access to the selected robot |
| Installation and explicit live application execution | Robot's vbot shell, under the deployment guide and operation prerequisites |

"Read-only" here means repository inspection, not running an application merely because it
is offline or uses mocked transport. Temporary test fixtures do not turn a repository check
into an application-packaging task. The SDK-free check groups are maintained in
[checks.json](../../catalog/checks.json); listing them never runs them:

```bash
python3 tools/run_checks.py --scope repository --list
python3 tools/run_checks.py --scope recipes --list
python3 tools/run_checks.py --scope packaging --list
```

First inspect and reuse a suitable container following the [container guide](../../docker/README.md).
Confirm its image, workspace mount and target architecture. Inside it, the context check
requires both a Linux container marker and `VBOT_DEV_CONTAINER=1`; neither a flag nor
`--profile container` alone is enough. This is a mistake-prevention guard, not image attestation
or a security sandbox. It does not verify SDK compatibility or grant device access.

```bash
python3 tools/container_context.py
python3 tools/in_container.py -- bazel build //recipes/subscribe-state:main
python3 tools/in_container.py -- bazel run //recipes/subscribe-state:main
python3 tools/run_checks.py --scope recipes
python3 tools/run_checks.py --scope packaging
```

The commands above run in the development container at the checkout root. The Recipe preview
does not open a device session. If the context or container is unavailable, stop with the
specific blocker; do not set a host-side flag to bypass the guard. Arbitrary hand-written
commands are not intercepted by this helper and must follow the same execution rule.

## Application workflow

Current device workflows target foot_quadruped; for type-specific details see [robot-type guides](../robots/README.md).

1. Prepare or reuse the [development container](../../docker/README.md), then follow the [Python SDK guide](../../packages/aorta/python/README.md) to install the SDK matching your development environment. See [Quickstart](../getting-started/README.md) for the first example and [Python deployment](python-deployment.md) for device deployment.
2. Use the [capability catalog](../../catalog/README.md) to select an interface and a program from [Recipes](../../recipes/README.md); build, test and preview it with Bazel in the container.
3. Follow the [shared connection guide](../robots/quadruped-common/connection.md) to log in over SSH, then configure the [device environment](../getting-started/device-environment.md).
4. Follow [Python deployment](python-deployment.md) to package and transfer a selected recipe plus ARM64 wheels, then create the venv in a new device application directory as vbot. Run read-only examples before explicitly running control examples with their safety prerequisites.
5. Debug long-running programs interactively before configuring [user-program autostart](../guides/user-autostart.md) with startup, logs and disable procedures.

Python source normally needs no cross-compilation, but native libraries must match the target architecture and ABI. Do not copy a workstation venv to the robot. Current Recipes run live on the device; they do not configure workstation-to-Aorta routing. A workstation build does not establish device connectivity.

Start a complete application from the [read-only health monitor](../../blueprints/health-monitor/README.md).
Generate an independent workspace, test its business rules with synthetic data, and package it
separately from deployment. For task routing see [Agent quickstart](../agents/README.md).
For failure investigation, use [layered diagnostics](diagnostics.md).

For live topic visualization, follow [Foxglove viewing](../guides/foxglove.md).
The bridge runs on the device; the viewer connects from your computer.

## C++ path

For builds without registry access, use the [offline build guide](offline-build.md).

For C++ applications, follow the [C++ SDK guide](../../packages/aorta/cpp/README.md) for a compiler
and architecture-matching release artifacts; no Python venv is needed. Select the Recipe's
`:main_cpp` target; native SDK/default builds serve container previews/tests, while ARM64 SDK
plus `bazel build --config=arm64` produces device executables. Deploy those ARM64 executables and the Aorta shared
runtime over SSH. Camera `:main_cpp_decode` additionally needs FFmpeg. Never mix workstation
and device native dependencies. Configure the session in the device shell before explicit
execution; the same Recipe defines safety conditions and completion semantics.
