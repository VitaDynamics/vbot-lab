# EDU 开发容器

<p align="center"><a href="README.md">English</a> | 中文</p>

当前配置引用镜像标签 `dev-v0.0.1`，支持匿名拉取，无需登录镜像仓库。
配置使用标签而非不可变 digest；需要固定环境时，将 `VBOT_LAB_DEV_IMAGE` 设置为带 digest 的镜像引用。

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
docker exec -it -w /workspace "$VBOT_DEV_CONTAINER_ID" /bin/bash
```

Agent 非交互命令不使用 -it，例如：

```bash
docker exec -w /workspace "$VBOT_DEV_CONTAINER_ID" /bin/bash -lc 'python3 tools/check_environment.py --profile container'
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
uname -m
```

原生代码除 `uname -m` 外还需检查实际编译目标与产物架构，Docker 不会自动将 x86_64 程序交叉编译为 ARM64。
[C++ 指南](../packages/aorta/cpp/README.zh-CN.md)当前使用原生编译，该路径需在兼容的 ARM64 容器环境中
使用提供的镜像。缺少该环境时停止并取得匹配的容器环境，不改在 host 或机器人上编译。
Python 源码可移植，但 wheel 与原生依赖仍需匹配目标设备。机器人只运行部署的应用，
这些示例不要求设备安装 Docker 或 Bazel。

默认只挂载本仓到 `/workspace`，并为 Bazel 使用独立的命名缓存卷。
本地可通过 `VBOT_LAB_DEV_IMAGE` 覆盖完整镜像引用，版本选择见[兼容矩阵](../docs/compatibility.zh-CN.md)。

## 安全与权限

此镜像仅用于本地隔离开发。
本配置启动交互 Shell，不开放 SSH 端口。
若自行启用 SSH，应先完成认证、连接身份与网络隔离检查，不得暴露到不可信网络。

开发容器账户与设备的 `vbot` 账户属于不同环境。本配置不修改设备账号、ACL、服务或资源限额。
挂载目录中新建文件的所有权可能与主机用户不同，使用主机工具编辑前请检查文件所有权。
