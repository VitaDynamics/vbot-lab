# Editor development container

<p align="center">English | <a href="README.zh-CN.md">中文</a></p>

Opening the repository with this configuration reuses the dev service in `docker/compose.yaml`.
It starts the development environment without automatically installing the SDK or connecting to a device.

For image prerequisites, permissions and network boundaries, see the
[container guide](../docker/README.md). After opening the container, check its tools
and build the selected example before device deployment.
The configuration declares the development context in the container terminal. Repository-only
checks may run on the host, but Bazel, Recipe previews and packaging stay in this container;
see [execution locations](../docs/development/README.md).
