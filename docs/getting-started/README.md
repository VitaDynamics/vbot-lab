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

## Select the matching source

For robot application `V1.6.0-10`, use source snapshot tag `V1.6.0.10`.
The SDK assets have their separate `edu-sdk-2026.10.14` release.
On the host, clone the repository and check out the matching source version:

```bash
git clone https://github.com/VitaDynamics/vbot-lab.git
cd vbot-lab
git checkout V1.6.0.10
```

If a checkout already exists, reuse it and check out the same tag rather than cloning
again. If that tag is missing locally, first run `git fetch origin tag V1.6.0.10`.

Checking out a tag enters detached HEAD mode; this is expected when reading, building
or running a versioned snapshot. To modify code in this checkout, create a working
branch first (use another name if this one already exists):

```bash
git switch -c my-edu-app
```

When choosing another source tag, use its documented robot application and SDK pairing
from the [compatibility matrix](../compatibility.md).

## Check locally first

For Codex or Claude Code, use [Agent quickstart](../agents/README.md).
Without a harness, run `python3 tools/check_environment.py --profile host` from the checkout root.
Inside an existing development container, select `--profile container` instead.
The checker does not install software, access Docker, or contact a device.

## Enter the development container

Follow the [container guide](../../docker/README.md) to check Docker and identify a
container using the provided image with this checkout mounted. Reuse a suitable
running container; start the same container if it is stopped. Pull and create a
container only when no suitable one exists. The development image supports anonymous
pulls without registry login.

Run SDK preparation, Bazel builds and packaging inside that container, not in the
host shell. With the default workspace mount:

```bash
cd /workspace
python3 tools/check_environment.py --profile container
python3 --version
bazel --version
uname -m
```

Use Python 3.10+ and Bazel 7.6.1. Follow the SDK guide for the versions required by
the selected source version rather than assuming the image already contains them.
An x86_64 container can prepare Python source and ARM64 wheels, but native C++
deployment needs an ARM64 container and compiler; see the [C++ guide](../../packages/aorta/cpp/README.md).

## Connect to the robot

Four-legged and four-wheeled robot dogs share the
[wired / Wi-Fi connection and SSH login guide](../robots/quadruped-common/connection.md).
For Wi-Fi, connect the robot through the mobile app, find its IP in the router's device
list, then SSH as `vbot` using that IP. The wired option covers the USB-C Ethernet
adapter and manual computer IPv4 settings.
Perform the network setup and SSH login on your computer, outside the development container.
For other robot types, check their own guide before applying network settings.
The current EDU release scope remains `foot_quadruped` only.

## Configure and check the device shell

After SSH login, follow [device environment setup](device-environment.md) to load the
`vbot` Bash environment, save it in `.bashrc`, and check Aorta / ROS 2 access separately.
These device CLI checks do not require Python SDK installation. Aorta is native;
ROS 2 is a device-local [compatibility subset](../interfaces/aorta-ros2.md).

## Build and run a Python example

1. Inside the development container, install the four matching release wheels in a dedicated venv using the [Python SDK guide](../../packages/aorta/python/README.md).
2. Build and preview a [Recipe](../../recipes/README.md) with Bazel in that container; previews do not contact the robot.
3. Confirm the selected firmware exposes the required route, then [SSH into the device](../robots/quadruped-common/connection.md) as vbot.
4. Follow [Python deployment](../development/python-deployment.md) to transfer the selected recipe and ARM64 wheels, create a device venv, and configure the device shell. The robot does not come with a checkout; do not copy workstation native libraries.
5. Run the [read-only state subscription](../../recipes/subscribe-state/README.md) with explicit --execute. Inspect actual samples before adding commands.
6. Use the selected Recipe's preconditions, completion checks and stopping procedure for service/action operations. Configure [autostart](../guides/user-autostart.md) only after interactive operation works.

For C++, select the same Recipe's `:main_cpp` target and use the [C++ SDK build/deployment workflow](../../packages/aorta/cpp/README.md)
instead of Python wheel/venv steps. SSH login, device shell setup and operation prerequisites remain the same.
