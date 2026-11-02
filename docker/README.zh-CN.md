# EDU 开发容器

<p align="center"><a href="README.md">English</a> | 中文</p>

Compose 将 `dev-v0.0.1` 镜像固定到 [release.json](../catalog/release.json) 中的不可变 digest：
`sha256:8d5081784d9e7d34463f62ae5bef2b58cf4a0a37383435379c4bfc37ec01fdcd`。
镜像支持匿名拉取，无需登录镜像仓库。已发布平台为 **linux/amd64**，Compose 显式选择该平台。
ARM64 宿主机需具备兼容的 Linux/amd64 运行环境，不自动修改宿主机仿真设置。

进入容器后，按 [SDK 指南](../packages/aorta/README.zh-CN.md)为所选语言和架构准备配套 SDK 与 Schema 制品。
不要假定镜像自带的软件包与所选 SDK 发布版本一致。

## 使用

在 host 的仓库根目录先检查 Docker 客户端／服务端、Compose v2 和当前 context。
以下为只读检查，执行时设置合理超时：

```bash
docker version
docker compose version
docker context show
docker info --format '{{.OSType}}/{{.Architecture}}'
docker compose -f docker/compose.yaml config --quiet
```

当前用户应可访问 Docker 服务端，且服务端支持 Linux 容器。
检查失败时先处理缺少安装、daemon 不可用或访问权限问题，不自动修改 socket 权限或切换 context。
host 无需安装 Bazel 和 SDK。仅检查环境时到此为止；拉取与启动容器属于环境搭建步骤。

### 优先复用已有容器

先列出全部容器，包括已停止的以及其他 Compose 项目创建的容器：

```bash
docker ps -a --format 'table {{.ID}}\t{{.Names}}\t{{.Image}}\t{{.Status}}'
```

将下面的占位值替换为选定的容器 ID，核对镜像、状态和工作区挂载；
不要只按容器名判断，也不要输出无关环境变量：

```bash
VBOT_DEV_CONTAINER_ID=REPLACE_WITH_CONTAINER_ID
docker inspect --format '{{.Config.Image}} {{.Image}} {{.State.Status}}' "$VBOT_DEV_CONTAINER_ID"
docker inspect --format '{{json .Mounts}}' "$VBOT_DEV_CONTAINER_ID"
```

确认它来自提供的开发镜像，且挂载了当前需要的工作区。多候选时先选择一个。
以下使用默认挂载路径 /workspace；已有容器路径不同时改为已核对的实际路径。

- 已运行：直接进入，不拉取、不重启、不重建。
- 已停止：仅执行 `docker start "$VBOT_DEV_CONTAINER_ID"`，再进入。
- 镜像／挂载不匹配、暂停、重启循环或启动失败：说明问题，不自动删除或替换容器。
- 仅检查环境时不启动容器。

```bash
docker exec -it -e VBOT_DEV_CONTAINER=1 -w /workspace "$VBOT_DEV_CONTAINER_ID" /bin/bash
```

Agent 非交互命令不使用 -it，例如：

```bash
docker exec -e VBOT_DEV_CONTAINER=1 -w /workspace "$VBOT_DEV_CONTAINER_ID" /bin/bash -lc 'python3 tools/check_environment.py --profile container'
```

### 仅在没有合适容器时创建

从仓库根目录执行。保留容器以供后续复用；正常使用不需要每次拉取或重新创建：

```bash
docker compose -f docker/compose.yaml pull
docker compose -f docker/compose.yaml up -d --no-recreate dev
docker compose -f docker/compose.yaml exec dev /bin/bash
```

后续在该容器的 `/workspace` 中继续。ARM64 应用开发、SDK 准备、Bazel 构建、离线预览及打包
均在这里执行；host 负责 Docker，也可通过 SSH 传输生成的制品。
已经位于提供的容器内时跳过 host 检查，使用 container 清点模式：

```bash
cd /workspace
python3 tools/check_environment.py --profile container
python3 tools/container_context.py
uname -m
```

仓库只读检查可在宿主机或 CI runner 运行；Bazel 构建／测试、Recipe 预览、SDK 执行检查、
依赖准备和打包必须在本容器内完成，CI 同样遵守，参阅[执行位置](../docs/development/README.zh-CN.md)。
Compose 自动声明 `VBOT_DEV_CONTAINER=1`；复用已有容器时，上面的 exec 命令在镜像／挂载检查后
声明该变量，不重建或修改容器配置。上下文检查还要求 Linux 运行时标记；
单个变量不证明镜像、架构或工作区正确。

镜像运行平台为 `linux/amd64`，已包含 ARM64 GCC／G++ 交叉编译器。
容器运行架构不决定编译器的输出架构。在开发容器内分别检查原生与交叉编译目标：

```bash
uname -m
g++ -dumpmachine
aarch64-linux-gnu-gcc -dumpmachine
aarch64-linux-gnu-g++ -dumpmachine
```

交叉编译器应输出 `aarch64-linux-gnu`，它们在 AMD64 上运行并生成 ARM64 代码。
应复用当前容器，不因 `uname -m` 为 x86_64 就要求另建 ARM64 容器。
[C++ Recipe 指南](../packages/aorta/cpp/README.zh-CN.md)使用 `bazel build --config=arm64`
配合 ARM64 SDK 生成设备程序；默认 Bazel 构建仍为容器内预览／测试所用的原生构建。
不要在此 AMD64 容器内执行 ARM64 程序。
部署前需匹配所选编译器、ARM64 SDK／运行库与产物架构，不改在 host 或机器人上编译来绕过问题。
Python 源码可移植，但 wheel 与原生依赖仍需匹配目标设备。机器人只运行部署的应用，
这些示例不要求设备安装 Docker 或 Bazel。

首个 Python 应用可在 AMD64 容器内暂存 ARM64 wheel，无需在该容器安装或执行它们，
见[快速开始](../docs/getting-started/README.zh-CN.md)。

默认只挂载本仓到 `/workspace`，并为 Bazel 使用独立的命名缓存卷。
本地可通过 `VBOT_LAB_DEV_IMAGE` 覆盖完整镜像引用，版本选择见[兼容矩阵](../docs/compatibility.zh-CN.md)。

## 安全与权限

此镜像仅用于本地隔离开发。
本配置启动交互 Shell，不开放 SSH 端口。
若自行启用 SSH，应先完成认证、连接身份与网络隔离检查，不得暴露到不可信网络。

开发容器账户与设备的 `vbot` 账户属于不同环境。本配置不修改设备账号、ACL、服务或资源限额。
挂载目录中新建文件的所有权可能与主机用户不同，使用主机工具编辑前请检查文件所有权。
