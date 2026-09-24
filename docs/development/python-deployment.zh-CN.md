# 将 Python 示例部署到设备

<p align="center"><a href="python-deployment.md">English</a> | 中文</p>

设备默认没有 VBOT Lab 仓库或应用 venv。先在开发机／开发容器构建，再传输精简源码包与
ARM64 wheel，最后在设备上创建 venv。此 Python 部署流程不要求设备安装 Git、Bazel、
编译器或连接互联网，**前提是已在联网开发机准备好完整 wheelhouse**，
并非从准备到部署全程离线。不要将开发机 venv 或 Bazel 启动器／runfiles 直接复制到设备。

## 1. 在开发机或开发容器准备

从本地 VBOT Lab 仓库根目录开始。下面部署只读的 `subscribe-state` 示例；其他示例
将 RECIPE 改为对应目录名。打包内容仅包含所选 main.py 与公共 Python 模块，不包含全部示例或
完整仓库。使用配套依赖包时，按[离线 Bazel 指南](offline-build.zh-CN.md)替换构建入口。

按 [SDK 指南](../../packages/aorta/python/README.zh-CN.md)，从
[GitHub Releases](https://github.com/VitaDynamics/vbot-lab/releases/tag/edu-sdk-2026.9.24)
将匹配的 Linux aarch64 SDK、aorta-msgs 和 vbot-edu-msgs wheel 下载到 `artifacts/wheelhouse/`。
Release 同时附带 `flatbuffers` 25.12.19 通用 wheel；下面开头的命令改为在开发机联网从 PyPI
下载同一 wheel，不会把 ARM64 SDK 安装进开发机的 Python 环境。
打包前依据 Release 的 `SHA256SUMS` 核对全部文件（FlatBuffers 文件也可依据可信发行来源的
校验值核对）。
下面四个文件都必须具备；下载或校验失败就停止，设备端不下载缺失依赖。

```bash
mkdir -p artifacts/wheelhouse
python3 -m pip download --only-binary=:all: --no-deps \
  --dest artifacts/wheelhouse "flatbuffers==25.12.19"
RECIPE=subscribe-state
bazel build "//recipes/$RECIPE:main"
bazel run "//recipes/$RECIPE:main" -- --help
mkdir -p artifacts
PACKAGE_DIR=$(mktemp -d "$PWD/artifacts/python-recipe-XXXXXX")
mkdir "$PACKAGE_DIR/wheelhouse"
tar -czf "$PACKAGE_DIR/python-recipe.tar.gz" \
  LICENSE NOTICE recipes/__init__.py recipes/common.py recipes/observe.py \
  "recipes/$RECIPE/main.py"
cp artifacts/wheelhouse/aorta_sdk-2026.9.23-py3-none-linux_aarch64.whl \
  artifacts/wheelhouse/aorta_msgs-2026.9.23-py3-none-any.whl \
  artifacts/wheelhouse/vbot_edu_msgs-2026.9.24-py3-none-any.whl \
  artifacts/wheelhouse/flatbuffers-25.12.19-py2.py3-none-any.whl \
  "$PACKAGE_DIR/wheelhouse/"
(cd "$PACKAGE_DIR" && sha256sum python-recipe.tar.gz wheelhouse/*.whl > SHA256SUMS)
```

压缩包保留 `python -m` 所需的 `recipes/` 包结构，以及适用的 LICENSE/NOTICE；
不包含 venv 或 SDK／原生二进制。

音视频二进制保存还需加入兼容设备的 `numpy==2.2.6` wheel，相机解码另需 `av==16.1.0`。
除 ARM64 架构外，还需匹配设备 Python ABI（当前配套设备使用 Python 3.10）。
将可选 wheel 加入暂存 wheelhouse 后，**重新生成 SHA256SUMS**。只读状态示例不需要这些可选依赖。

## 2. 从具备 SSH 连接的机器传输

先完成[公钥登录](../robots/quadruped-common/connection.zh-CN.md)。将 ROBOT 改为确认可用的
设备地址或普通 vbot SSH 别名。SSH 不可达时，先连接设备或修正地址，不继续部署。

在步骤 1 的同一个开发机／容器 shell 中执行。身份检查应显示 vbot、aarch64 和受支持的
Python 版本。每次部署使用新目录，不覆盖其他应用。任何命令失败都应立即停止。

```bash
ROBOT=vbot@192.168.126.2
ssh -o BatchMode=yes "$ROBOT" 'id -un; uname -m; python3 --version'
APP_DIR=$(ssh -o BatchMode=yes "$ROBOT" \
  'mkdir -p /userdata/vbot/apps && mktemp -d /userdata/vbot/apps/python-recipe-XXXXXX')
printf 'Device application directory: %s\n' "$APP_DIR"
scp "$PACKAGE_DIR/python-recipe.tar.gz" "$PACKAGE_DIR/SHA256SUMS" "$ROBOT:$APP_DIR/"
scp -r "$PACKAGE_DIR/wheelhouse" "$ROBOT:$APP_DIR/"
ssh "$ROBOT"
```

记下输出的 APP_DIR。后续命令在最后一条 ssh 打开的**设备 shell**执行；
开发机 shell 变量不会自动带入设备。如果只有宿主机可以 SSH，先把暂存的 PACKAGE_DIR 交给宿主机。

## 3. 在设备创建运行环境

将下面的 `python-recipe-ABC123` 替换为步骤 2 实际输出的目录名。
这是**应用部署目录**，不是预装仓库。先核验校验值，通过后才解压和安装；任一校验失败都应停止。

```bash
cd /userdata/vbot/apps/python-recipe-ABC123
sha256sum -c SHA256SUMS
tar -xzf python-recipe.tar.gz
unset PYTHONPATH
export PYTHONNOUSERSITE=1
python3 -m venv .venv
.venv/bin/python -m pip install --no-index --find-links wheelhouse \
  aorta-sdk==2026.9.23 aorta-msgs==2026.9.23 \
  vbot-edu-msgs==2026.9.24 flatbuffers==25.12.19
.venv/bin/python -m pip check
.venv/bin/python -c 'import aorta; from locomotion.LocomotionStatus import LocomotionStatus; print("SDK imports OK")'
```

缺少 Python、venv 或原生运行依赖时，应先按受支持的设备环境解决，不要装进系统 Python，
也不要复用其他应用的环境。可选采集／解码依赖也从已准备的 wheelhouse 使用 --no-index 安装。

## 4. 从应用部署目录运行

此时目录内已有 `recipes/`、`wheelhouse/` 与 `.venv/`，
不需要 .git、MODULE.bazel、SDK 源码或仓库其他内容。在同一个设备 shell 中执行：

```bash
. .venv/bin/activate
unset PYTHONPATH
export PYTHONNOUSERSITE=1
export PATH="/opt/vita/aorta/bin:$PATH"
export ZENOH_SESSION_CONFIG_URI=/opt/vita/aorta/edu/edu_session.json5
python -m recipes.subscribe-state.main
python -m recipes.subscribe-state.main --execute --count 3 --timeout 10
```

第一条示例命令仅预览，不连接设备；第二条读取三条状态消息。超时不代表成功。
其他参数、安全／采集授权要求和完成条件见对应 [Recipe](../../recipes/README.zh-CN.md)；
模块名只替换为实际部署的示例。

重新登录后，先 cd 到记下的应用目录，再执行上述环境配置／激活步骤，不要假设 .bashrc
已激活此 venv。原生 SDK 使用独立 shell，避免 ROS 的 PYTHONPATH 覆盖 wheel 包。
更新应用时重新构建并部署到新目录，验证后再决定是否切换[自启动入口](../guides/user-autostart.zh-CN.md)；
本流程不会修改自启动脚本或启动后台进程。
