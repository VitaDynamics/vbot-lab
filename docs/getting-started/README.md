# Quickstart

<p align="center">English | <a href="README.zh-CN.md">中文</a></p>

This shared chapter covers workstation setup. Before connecting to a device, select its
[robot-type guide](../robots/README.md) and check the [compatibility matrix](../compatibility.md).
The current EDU release scope is `foot_quadruped` only; a working container does not
establish support for other robot types.

## Explore the robot model (optional)

Use [Vbot Viewer](../guides/vbot-viewer.md) to inspect the EDU model, joint axes and
link structure in your browser before connecting a robot. This optional step does
not require SSH, Docker or SDK installation and does not command a robot.

## Check locally first

For Codex or Claude Code, use [Agent quickstart](../agents/README.md).
Without a harness, run `python3 tools/check_environment.py --profile host` from the checkout root.
Inside an existing development container, select `--profile container` instead.
The checker does not install software, access Docker, or contact a device.

## Environment startup configuration and repository checks

```bash
git clone https://github.com/VitaDynamics/vbot-lab.git
cd vbot-lab
docker compose -f docker/compose.yaml pull
docker compose -f docker/compose.yaml run --rm dev
```

If GitHub asks you to authenticate, use an account with access to this repository.
Image availability has not yet been verified for this version.
Inside the container, run the repository checks listed in the top-level README.
See the [container guide](../../docker/README.md) for details.

## Connect to the robot

Four-legged and four-wheeled robot dogs share the
[wired connection and SSH login guide](../robots/quadruped-common/connection.md).
The guide covers the USB-C Ethernet adapter, computer IPv4 settings, and the `vbot` login.
Perform the network setup and SSH login on your computer, outside the development container.
For other robot types, check their own guide before applying network settings.
The current EDU release scope remains `foot_quadruped` only.

## Configure and check the device shell

After SSH login, follow [device environment setup](device-environment.md) to load the
`vbot` Bash environment, save it in `.bashrc`, and check Aorta / ROS 2 access separately.
These device CLI checks do not require Python SDK installation. Aorta is native;
ROS 2 is a device-local [compatibility subset](../interfaces/aorta-ros2.md).

## Build and run a Python example

1. Install the matching release wheels in the workstation environment using the [Python SDK guide](../../packages/aorta/python/README.md).
2. Build and preview a [Recipe](../../recipes/README.md) with Bazel; previews do not contact the robot.
3. Confirm the selected firmware exposes the required route, then [SSH into the device](../robots/quadruped-common/connection.md) as vbot.
4. Follow [Python deployment](../development/python-deployment.md) to transfer the selected recipe and ARM64 wheels, create a device venv, and configure the device shell. The robot does not come with a checkout; do not copy workstation native libraries.
5. Run the [read-only state subscription](../../recipes/subscribe-state/README.md) with explicit --execute. Inspect actual samples before adding commands.
6. Use the selected Recipe's preconditions, completion checks and stopping procedure for service/action operations. Configure [autostart](../guides/user-autostart.md) only after interactive operation works.

For C++, select the same Recipe's `:main_cpp` target and use the [C++ SDK build/deployment workflow](../../packages/aorta/cpp/README.md)
instead of Python wheel/venv steps. SSH login, device shell setup and operation prerequisites remain the same.
