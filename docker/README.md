# EDU development container

<p align="center">English | <a href="README.zh-CN.md">中文</a></p>

Compose pins the `dev-v0.0.1` image to the immutable digest recorded in
[release.json](../catalog/release.json):
`sha256:8d5081784d9e7d34463f62ae5bef2b58cf4a0a37383435379c4bfc37ec01fdcd`.
The image supports anonymous pulls without registry login. Its published platform is
**linux/amd64**; Compose selects that platform explicitly. On ARM64 hosts, a compatible
Linux/amd64 runtime is required. Do not change host emulation settings automatically.

After entering the container, follow the [SDK guides](../packages/aorta/README.md)
to prepare the matching SDK and Schema artifacts for your language and architecture.
Do not assume the image's bundled packages match the selected SDK release.

## Usage

On the host, from the repository root, first check the Docker client/server, Compose v2 and selected context.
Run these read-only checks with a bounded command timeout:

```bash
docker version
docker compose version
docker context show
docker info --format '{{.OSType}}/{{.Architecture}}'
docker compose -f docker/compose.yaml config --quiet
```

The server must be reachable with the current user's permissions and support Linux
containers. If a check fails, resolve the missing installation, daemon or access issue
before continuing; do not change socket permissions or switch contexts automatically.
Host Bazel and SDK installation are unnecessary. A check-only request stops here;
pulling and starting the container belong to environment setup.

### Reuse an existing container first

List all containers, including stopped containers and those from other Compose projects:

```bash
docker ps -a --format 'table {{.ID}}\t{{.Names}}\t{{.Image}}\t{{.Status}}'
```

Replace the placeholder below with the selected container ID and inspect its image,
state and workspace mounts. Do not identify a container only by name or dump unrelated
environment variables:

```bash
VBOT_DEV_CONTAINER_ID=REPLACE_WITH_CONTAINER_ID
docker inspect --format '{{.Config.Image}} {{.Image}} {{.State.Status}}' "$VBOT_DEV_CONTAINER_ID"
docker inspect --format '{{json .Mounts}}' "$VBOT_DEV_CONTAINER_ID"
```

Confirm that it uses the provided development image and mounts the intended workspace.
Choose one if several candidates match. Commands below use the default /workspace mount;
substitute the verified workspace path when reusing a different layout.

- Running: enter directly; do not pull, restart or recreate.
- Stopped: run only `docker start "$VBOT_DEV_CONTAINER_ID"`, then enter.
- Image/mount mismatch, paused state, restart loop or startup failure: explain the issue;
  do not automatically delete or replace the container.
- Check-only requests do not start containers.

```bash
docker exec -it -e VBOT_DEV_CONTAINER=1 -w /workspace "$VBOT_DEV_CONTAINER_ID" /bin/bash
```

For non-interactive Agent commands omit -it, for example:

```bash
docker exec -e VBOT_DEV_CONTAINER=1 -w /workspace "$VBOT_DEV_CONTAINER_ID" /bin/bash -lc 'python3 tools/check_environment.py --profile container'
```

### Create only when no suitable container exists

Run from the repository root. Keep the container for reuse; normal use does not
require pulling or creating it again:

```bash
docker compose -f docker/compose.yaml pull
docker compose -f docker/compose.yaml up -d --no-recreate dev
docker compose -f docker/compose.yaml exec dev /bin/bash
```

Continue in `/workspace` inside this container. ARM64 application development, SDK
preparation, Bazel builds, offline previews and packaging take place here; the host
manages Docker and may transfer the resulting artifacts over SSH. If already in the
provided container, skip the host checks and use the container inventory profile:

```bash
cd /workspace
python3 tools/check_environment.py --profile container
python3 tools/container_context.py
uname -m
```

Read-only repository checks may run on the host or CI runner. Bazel builds/tests, Recipe
previews, SDK execution checks, dependency preparation and packaging must run in this
container, including CI; see [execution locations](../docs/development/README.md).
Compose declares `VBOT_DEV_CONTAINER=1` automatically. For an existing container, the exec
commands above declare it only after image/mount inspection, without recreating or modifying
the container configuration. The context guard also requires a Linux runtime marker; the
flag alone does not verify an image, architecture or workspace.

The image runs on `linux/amd64` and includes the ARM64 GCC/G++ cross-compilers.
The container's runtime architecture does not determine the compiler's output architecture.
Inside the development container, inspect both native and cross-compiler targets:

```bash
uname -m
g++ -dumpmachine
aarch64-linux-gnu-gcc -dumpmachine
aarch64-linux-gnu-g++ -dumpmachine
```

The cross-compilers should report `aarch64-linux-gnu`; they run on AMD64 and produce
ARM64 code. Reuse this container rather than requiring another ARM64 container solely
because `uname -m` reports x86_64. The [C++ Recipe guide](../packages/aorta/cpp/README.md)
uses `bazel build --config=arm64` with the ARM64 SDK for device binaries; default Bazel
builds remain native for container previews/tests. Do not execute ARM64 binaries in this AMD64 container.
Match the selected compiler, ARM64 SDK/libraries and output architecture before deployment;
do not build on the host or robot as a workaround. Python source is portable, but wheels
and native dependencies must still match the target. The robot runs deployed applications;
it does not need Docker or Bazel for these examples.

For the first Python application, the AMD64 container can stage ARM64 wheels without
installing or executing them. Follow [Quickstart](../docs/getting-started/README.md).

By default, only this repository is mounted at `/workspace`, with a separate named cache volume for Bazel.
Use `VBOT_LAB_DEV_IMAGE` to override the complete image reference locally.
Use the image version listed in the [compatibility matrix](../docs/compatibility.md).

## Security and permissions

Use this image for isolated local development.
This configuration starts an interactive shell and exposes no SSH ports.
If you enable SSH yourself, first complete authentication, connection-identity, and network-isolation checks;
do not expose it to untrusted networks.

The development-container account and the device's `vbot` account belong to different environments.
This configuration does not change device accounts, ACLs, services, or resource quotas.
New files in the mounted host directory may have different ownership from the host user;
check ownership before editing those files with host tools.
