# 快速开始：收到第一条机器人状态

<p align="center"><a href="README.md">English</a> | 中文</p>

默认主路径是 **Python＋四足 EDU＋只读状态订阅**。
适配机器人应用 `V1.6.0-12`、源码 tag `V1.6.0.12` 和 SDK Release `edu-sdk-2026.10.14`。
目标是收到三条解码后的 `/locomotion/status` 状态并正常退出，不涉及运动、音视频采集或自启动。

| 步骤 | 执行位置 | 成功结果 | 失败后查看 |
| --- | --- | --- | --- |
| 选择源码并复用开发容器 | 宿主机，再进入容器 | 配套仓库、Python 3.10+、Bazel 7.6.1 | [容器配置](../../docker/README.zh-CN.md) |
| 构建、预览和打包 | 开发容器 | 离线预览和已校验的 ARM64 包 | [构建／导入／打包问题](../troubleshooting/README.zh-CN.md) |
| 确认 SSH 并传输 | 能访问目标机器人的宿主机 | `vbot`、`aarch64`、新应用目录 | [SSH 排障](../troubleshooting/README.zh-CN.md#ssh) |
| 安装并收到状态 | 设备 vbot shell | 三条 JSON Lines，退出码 0 | [订阅超时](../troubleshooting/README.zh-CN.md#no-data) |

## 1. 选择配套源码——宿主机

先核对[设备类型指南](../robots/README.zh-CN.md)和[兼容矩阵](../compatibility.zh-CN.md)。
当前软件不包含四轮或双足 EDU 发布。正常克隆，再选择文档指定的源码 tag：

```bash
git clone https://github.com/VitaDynamics/vbot-lab.git &&
cd vbot-lab &&
git checkout V1.6.0.12
```

已有仓库缺少该 tag 时，先执行 `git fetch origin tag V1.6.0.12`，切换前保留本地修改。
切换 tag 后的 detached HEAD 是使用版本快照时的正常状态。
源码与组件配套见[发布配置](../../catalog/release.zh-CN.md)。
如需修改该仓库，先创建工作分支：

```bash
git switch -c my-edu-app
```

纯仓库检查可在宿主机或 CI runner 运行。Bazel 构建／测试、Recipe 预览、SDK 检查和打包
都在开发容器内完成，CI 同样遵守，参阅[执行位置](../development/README.zh-CN.md)。
仓库贡献检查不是跑通首个应用的前置条件。

每个 Bash 命令块应作为一条命令链执行。`&&` 会在失败后跳过本段后续命令，
不改变当前 shell 的错误处理设置。先处理错误，再执行下一个命令块。

## 2. 构建并打包——开发容器

按[容器指南](../../docker/README.zh-CN.md)复用合适的运行中容器，或启动已有的停止状态容器。
仅在没有合适容器时创建。已经位于确认过的开发容器内时直接复用，容器内不要求 Docker。
确认仓库挂载和工具版本，默认挂载下执行：

```bash
cd /workspace &&
python3 tools/check_environment.py --profile container &&
python3 tools/container_context.py &&
python3 --version &&
bazel --version &&
uname -m
```

需要 Python 3.10+ 和 Bazel 7.6.1。已发布镜像运行于 `linux/amd64`，包含 ARM64 GCC／G++
交叉编译器，也可暂存 ARM64 Python 源码／wheel。下方首个 Python 流程无需交叉编译；
C++ Recipe 构建范围见 [C++ SDK 指南](../../packages/aorta/cpp/README.zh-CN.md)。
配套镜像 digest 记录在兼容矩阵和 Compose 配置中。

从容器内仓库根目录下载固定 Release 制品，构建并预览只读 Recipe，再打包。
已存在且校验一致的下载会复用。包的输出目录必须是新目录；已有时检查／复用它，或换一个输出路径。

```bash
python3 tools/fetch_sdk.py --output artifacts/edu-sdk-2026.10.14 &&
python3 tools/in_container.py -- bazel build //recipes/subscribe-state:main &&
python3 tools/in_container.py -- bazel run //recipes/subscribe-state:main &&
python3 tools/package_python.py --recipe subscribe-state \
  --assets-dir artifacts/edu-sdk-2026.10.14 --output artifacts/first-state &&
python3 tools/package_python.py --verify artifacts/first-state
```

预期：预览输出 `execute=false`；打包与校验输出 `status=complete`、`device_contacted=false`。
预览不是机器人数据。包内只有所选源码、四个 ARM64／基础 wheel、依赖清单、许可证及校验值，
不会复制开发机 venv 或开发机架构的原生库到设备。本次不依赖 SDK 的预览无需在工作站安装 SDK，
运行所需 SDK 在后面的设备步骤安装。

依赖无法下载时，使用已准备的依赖包并按[离线构建指南](../development/offline-build.zh-CN.md)操作。
不要为绕过构建／打包失败切换依赖注册表，或到机器人上临时下载缺失包。

## 3. 登录并传输——宿主机

先完成[公钥 SSH 登录](../robots/quadruped-common/connection.zh-CN.md)，或复用已有可用配置。
有线通常使用 `192.168.126.2`；Wi-Fi 先通过手机 App 配网，再从路由器查询 IP，并替换下方 ROBOT。
已有 vbot SSH 别名也可使用。连接、认证或主机指纹错误时不要继续。

在宿主机仓库根目录执行，工作区挂载应使 `artifacts/first-state` 可见。
如果容器在其他机器，先将已生成的包传到此宿主机。

```bash
PACKAGE_DIR=artifacts/first-state &&
ROBOT=vbot@192.168.126.2 &&
ssh -o BatchMode=yes "$ROBOT" \
  'test "$(id -un)" = vbot && test "$(uname -m)" = aarch64 &&
   python3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" &&
   id -un && uname -m && python3 --version' &&
APP_DIR=$(ssh -o BatchMode=yes "$ROBOT" \
  'mkdir -p /userdata/vbot/apps && mktemp -d /userdata/vbot/apps/first-state-XXXXXX') &&
test -n "$APP_DIR" &&
printf 'Device application directory: %s\n' "$APP_DIR" &&
scp -r "$PACKAGE_DIR/." "$ROBOT:$APP_DIR/" &&
ssh "$ROBOT"
```

第一条 SSH 命令会要求账户为 `vbot`、架构为 `aarch64`、Python 为 3.10+，通过后才创建目录或传输。
失败时检查所选账户、架构与 Python 版本，不要绕过检查。记下输出的 APP_DIR。
下一段在 **SSH 登录以后**的设备 shell 执行，不是在宿主机或容器。
本地变量不会带入该 shell，设备不需要仓库、Git 或 Bazel。

## 4. 安装并收到状态——设备

将下方目录替换为前一步输出的 APP_DIR。不改变设备现有服务或权限。
使用专用原生 SDK shell，避免 ROS 包路径遮蔽 wheel：

```bash
cd /userdata/vbot/apps/first-state-REPLACE_FROM_OUTPUT &&
sha256sum -c SHA256SUMS &&
tar -xzf python-recipe.tar.gz &&
unset PYTHONPATH &&
unset AORTA_CORE_FFI_LIB &&
export PYTHONNOUSERSITE=1 &&
python3 -m venv .venv &&
.venv/bin/python -m pip install --no-index --find-links wheelhouse -r requirements.txt &&
.venv/bin/python -m pip check &&
.venv/bin/python -c 'import aorta; from locomotion.LocomotionStatus import LocomotionStatus; core = aorta.load_library(); print("SDK imports and native runtime OK; ABI", core.aorta_abi_version())' &&
export PATH="/opt/vita/aorta/bin:$PATH" &&
export ZENOH_SESSION_CONFIG_URI=/opt/vita/aorta/edu/edu_session.json5 &&
.venv/bin/python -m recipes.subscribe-state.main --execute --count 3 --timeout 10
```

任何校验、安装、导入或环境检查失败都停止。预期：校验全部通过，`pip check` 无依赖冲突，
导入及原生库 ABI 检查成功，随后三条 JSON Lines 包含 `heartbeat_seq`、`posture`、`motion`、`current_action` 和 `stamp_ns`。
字段值取决于设备，第三条样本后进程以 0 退出。这是只读状态，不代表运动动作完成。
超时、topic 列表或预览不算成功，请按[症状排障](../troubleshooting/README.zh-CN.md)继续。

重新登录后，进入记下的应用目录、清除 PYTHONPATH 和 AORTA_CORE_FFI_LIB、设置相同 Aorta 变量，再使用 `.venv/bin/python`
执行最后一条命令。本流程不强制持久化 shell 配置；需要时参阅[设备环境](device-environment.zh-CN.md)。

## 后续开发

- 其他 Recipe、包内结构及可选依赖见 [Python 部署](../development/python-deployment.zh-CN.md)。
- 应用开发见 [Python SDK](../../packages/aorta/python/README.zh-CN.md)，其他能力见 [Recipes 索引](../../recipes/README.zh-CN.md)。
- C++ 使用 [C++ SDK 指南](../../packages/aorta/cpp/README.zh-CN.md)。设备程序选择 ARM64 SDK 与 `bazel build --config=arm64`；容器内预览／测试使用原生 SDK 和默认构建。
- 交互运行正常后再配置[自启动](../guides/user-autostart.zh-CN.md)。
- [Vbot Viewer](../guides/vbot-viewer.zh-CN.md)可选用于模型查看，不控制机器人。ROS 2 是可选的[设备本机兼容子集](../interfaces/aorta-ros2.zh-CN.md)，本 Aorta 示例不依赖它。
