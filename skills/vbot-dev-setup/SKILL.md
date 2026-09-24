---
name: vbot-dev-setup
description: Check host Docker readiness and guide ARM64 application development in the provided VBOT container, through SDK preparation, Bazel build, deployment and a first read-only state sample. Also supports scoped environment checks, not general robot diagnostics or motion control.
---

# VBOT development environment

<p align="center">English | <a href="SKILL.zh-CN.md">中文</a></p>

## Locate the workspace

Resolve this Skill's physical directory first: the containing `skills/vbot-dev-setup/`
belongs to the VBOT Lab checkout, even when discovered through a link in another project.
That checkout must also contain `tools/check_environment.py` and `catalog/capabilities.json`.
If only this Skill was copied, request the complete checkout path; do not run a similarly
named tool from the user's application directory or download dependencies automatically.

## Select the requested outcome

- Advice or inventory only: explain or perform only the requested checks; do not install,
  deploy, or contact a robot merely because this Skill was invoked.
- Device shell setup only: use the device section below and stop after the requested setup.
- Full development setup / first runnable example: follow the end-to-end workflow below.
  Tool inventory is its first checkpoint, not its completion condition.

Identify the language, current build environment, and intended robot/address from available
context. Preserve an existing language choice; if none is specified, offer Python as the
default and state that choice. Confirm missing device details before device operations;
local preparation can proceed independently. Do not run both language paths by default.

Distinguish workstation, development container, and device shell. For a device request,
confirm the intended robot/type and software version, then follow the device section below.
Do not run workstation inventory on a robot or load device paths into the workstation shell.

## Workstation inventory and interpretation

Identify whether the user is checking a workstation (`host`) or an existing development
container (`container`). If unclear, report the context or ask; Docker is not required inside
the container. Run this command from the resolved VBOT Lab root, or use its absolute path:

```bash
python3 tools/check_environment.py --profile host
```

Replace `host` with `container` for container checks. Add `--robot-type` only when the user's
type is known; never infer it from shared hardware. The command returns JSON, including
tool presence, release scope, SDK integration state, and checks it did not perform.

- Exit 0: the requested local inventory completed without missing required tools or a blocked robot type. This does not mean the SDK or device is ready.
- Exit 1: required tooling is missing, or the selected robot is a future release.
- Exit 2: invalid arguments, an unknown robot type, or invalid workspace/catalog data.
- Command presence does not verify its version, Docker daemon access, image availability, or a device connection. The checker executes no discovered tool.
- Report the SDK integration blocker independently of the exit code. Do not fabricate installation commands, import names, topics, or Bazel application targets.

For setup actions, read only the relevant [environment guide](../../docs/getting-started/README.md)
and [container guide](../../docker/README.md). Installing software or starting/pulling a container
is a separate action and must fit the user's request. For interface selection, use the
[catalog](../../catalog/README.md) and its linked source documents.

## Host to development container

For a host environment check or full setup, follow the Docker checks in the
[container guide](../../docker/README.md): check Docker CLI/client-server access,
Compose v2, the selected Docker context, and the Compose configuration. Use a bounded
command timeout. The inventory helper remains offline; its success does not replace
these checks. For advice-only requests, explain the commands without executing them.
If Docker is missing, its daemon is unavailable, or permissions fail, explain the specific
fix and stop before container setup. Do not automatically change socket permissions,
user groups, Docker context, or install software.

ARM64 application development, SDK preparation, Bazel builds, offline previews and
packaging all take place in the provided development container, not on the host or robot.
The host manages Docker, the mounted checkout and, when needed, SSH artifact transfer.
Host Bazel or a host SDK is not a prerequisite. For full setup, **look for an existing
development container before pulling an image or creating a container**:

- Prefer the user's selected container. Otherwise list all containers, including stopped
  ones, and inspect candidate image identity, workspace mounts and state as described in
  the container guide. Include containers created outside this checkout's Compose project.
- Reuse a suitable running container with docker exec; do not pull, recreate or restart it.
- For a suitable stopped container, start that same container, then exec into it.
- If several candidates match, ask which to use. A matching name alone is insufficient;
  if image or workspace mounts do not match, explain the mismatch without replacing it.
- Only when no suitable container exists, follow the guide's creation flow. Do not delete
  containers, reset caches or force recreation to perform setup; image upgrades are separate.

Record the selected container ID and mounted workspace path for subsequent commands. For a
check-only request, give these next steps without pulling or starting a container.
Do not perform separate anonymous-access probes as part of setup.

Continue from `/workspace` inside the container, using the container inventory profile.
An Agent running on the host must execute subsequent development commands through
the selected container; an interactive shell opened elsewhere does not move the Agent's
execution context. Confirm the mounted checkout, image and container identity first.
If already inside the provided container, skip host Docker checks; do not require Docker
inside it or mount the host Docker socket.

Check the container architecture and actual compiler target before producing ARM64 native
artifacts. Docker alone does not turn x86_64 builds into ARM64 builds. Follow the supported
SDK build path; if the provided container cannot produce compatible ARM64 binaries,
report that blocker and request a matching container environment. Do not fall back to host
or device compilation, invent a cross-toolchain, or change host emulation settings.

## Full setup: build, deploy, receive state

Read only the selected language's references. Reuse verified existing setup; do not reinstall
or create another deployment just because a previous stage has already completed.

1. **Prepare the build environment.** Run the appropriate inventory above. For full setup,
   additionally execute the relevant version checks and a real build; command presence alone
   is insufficient. Complete the host-to-container handoff above and run development steps
   in the provided container. If the image is unavailable, report the error; reuse an existing
   container from that image when available, not the host toolchain.
   Use the [offline build guide](../../docs/development/offline-build.md) for packaged Bazel
   dependencies. Resolve missing artifacts through documented public release sources or ask
   for the bundle; never substitute an undocumented dependency registry.
2. **Prepare SDK and build the read-only example.** Use
   [subscribe-state](../../recipes/subscribe-state/README.md), which reads `/locomotion/status`.
   - Python: follow the [SDK guide](../../packages/aorta/python/README.md) for release pairing
     and real import checks. Build `//recipes/subscribe-state:main` and run its offline preview
     inside the development container. Stage device-matching wheels using
     [Python deployment](../../docs/development/python-deployment.md).
   - C++: follow the [C++ SDK guide](../../packages/aorta/cpp/README.md), configure matching
     SDK/Schema paths, and build `//recipes/subscribe-state:main_cpp`. Device binaries must
     be ARM64 with compatible runtime libraries. An x86_64 preview is not a deployable ARM64
     binary; selecting ARM64 SDK archives does not configure cross-compilation. If no supported
     ARM64 builder is available, stop that path at this blocker rather than building on the robot.
3. **Connect and configure.** Follow the device section below: verify public-key SSH as
   `vbot`, then configure that device shell. Verify architecture and relevant runtime versions
   against the selected artifacts. Use a dedicated native Aorta SDK shell; ROS setup is not
   required for this example. For Python, follow the deployment guide's `PYTHONPATH` isolation
   rather than assuming activation of a venv removes ROS package paths.
4. **Deploy only the selected example.** Full setup includes transferring the documented
   application package to a fresh user application directory and setting up its runtime.
   Confirm the intended target before this write; if the request excludes device writes,
   stop with the staged package and remaining steps. Use the selected deployment guide:
   - Python: transfer source and ARM64 wheels, create a device-local venv, install offline,
     and check imports. Never transfer the workstation venv or assume a device checkout exists.
   - C++: transfer the executable and required shared libraries, check architecture, checksums
     and dynamic-library resolution, then run `./bin/subscribe-state` directly. No device Bazel
     or compiler is required. Do not replace system libraries.
5. **Receive actual state.** From the recorded application directory, with the documented
   runtime environment, run the recipe's bounded `--execute --count 3 --timeout 10` command
   for the selected language. Require decoded state samples and successful process completion;
   an offline preview, topic listing, or inventory exit code is not live success. On timeout
   or failure, inspect the relevant environment/import/library/route error and report the
   failing stage. Do not retry indefinitely or change services, permissions, bridge settings,
   or robot modes to force a sample.

Stop after the read-only example exits. Do not add motion, audio/video capture, background
processes, or autostart configuration to this setup. Hand off the recorded application path,
language/SDK pairing, exact rerun command and shell prerequisites, plus any remaining blocker.
If the device is unavailable, report local preparation as complete but live setup as unfinished.

## Device shell configuration and checks

Read the [device environment guide](../../docs/getting-started/device-environment.md) and
[Aorta / ROS 2 compatibility](../../docs/interfaces/aorta-ros2.md). Use the public `/opt/vita`
paths in that guide; Aorta is native, while ROS 2 is a device-local compatibility subset.
An unavailable ROS route is not a reason to invent a mapping or alter bridge settings.

- For advice-only requests, explain the setup without contacting or changing the device.
- Prefer public-key SSH before device setup or live checks. Follow the
  [connection guide](../../docs/robots/quadruped-common/connection.md): reuse existing access,
  or guide the user to configure it first, then verify with `BatchMode=yes` and public-key-only
  authentication in the environment that will run subsequent commands. Do not embed passwords
  or silently fall back to password automation. A read-only request does not authorize key
  installation; preserve existing keys and never transfer a private key to the device.
- Use the selected device address or SSH alias. If unreachable or refused, stop and ask the
  user to connect the device or provide its actual IP; distinguish authentication and host-key
  errors, and do not scan for another target or bypass host-key verification.
- For device setup, complete SSH login as `vbot` first, then configure the environment in
  that device shell. Do not run the device environment block in the workstation terminal.
- For requested device checks, establish the intended connection and use the `vbot` shell.
  Run `tools/check_device_environment.py` in that shell if the file is already available;
  otherwise use the documented manual checks. Transferring the standalone file is a
  separate action that must fit the request. The checker never connects on its own.
- For requested persistent setup, preserve and back up `.bashrc`, update one marked block,
  check syntax, and verify a fresh SSH session. Do not overwrite unrelated startup content.
- For non-interactive tool commands or user launchers, explicitly load the documented
  environment in the command's Bash process; do not rely on interactive `.bashrc` inheritance.
- Only when live checks are requested, use the bounded discovery/Schema/single-sample
  commands from the guide, one stream at a time. Never publish control messages, invoke
  services/actions, restart services, or change permissions as an environment test.

The device checker is independent of Python SDK installation; for application setup follow the
[Python SDK guide](../../packages/aorta/python/README.md) and its release pairing. Exit 0 confirms only its shell
inventory; ROS type loading, live samples, startup persistence, and firmware compatibility
remain separate checks. A timeout is not success, and a directory entry is not received data.

## Handoff

Summarize observed tools, missing requirements, release/SDK blockers, and the next applicable
step. Keep workstation inventory, device shell configuration, interface discovery, actual
samples, and persistence evidence separate. Report only checks performed and observed results.
Workstation inventory never implies permission to connect to or change a robot.
