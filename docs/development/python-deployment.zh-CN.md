# 将 Python 示例部署到设备

<p align="center"><a href="python-deployment.md">English</a> | 中文</p>

设备默认没有 VBOT Lab 仓库或应用 venv。先在开发容器构建，再传输精简源码包与
ARM64 wheel，最后在设备上创建 venv。此 Python 部署流程不要求设备安装 Git、Bazel、
编译器或连接互联网，**前提是已在联网开发容器内准备好完整 wheelhouse**，
并非从准备到部署全程离线。不要将开发机 venv 或 Bazel 启动器／runfiles 直接复制到设备。

每个 Bash 命令块应作为一条命令链执行：`&&` 会在失败后跳过本段后续命令，
不会因此退出交互式 shell。处理错误后，再执行下一个命令块。

## 1. 在开发容器中准备

下方 SDK 准备、Bazel 命令和打包均在**配套开发容器内**执行，不在宿主机 shell 或 CI runner 直接执行，
参阅[执行位置](README.zh-CN.md)。第二步只传输准备好的部署包，可在宿主机进行；第三步在机器人上执行。

从开发容器内挂载的 VBOT Lab 仓库根目录开始。下面部署只读的 `subscribe-state` 示例；其他示例
将 RECIPE 改为对应目录名，并将 PREVIEW_ARGS 设为该 Recipe 的离线预览参数。
打包内容仅包含所选 main.py 与公共 Python 模块，不包含全部示例或
完整仓库。使用配套依赖包时，按[离线 Bazel 指南](offline-build.zh-CN.md)替换构建入口。

下载工具从 [GitHub Releases](https://github.com/VitaDynamics/vbot-lab/releases/tag/edu-sdk-2026.10.14)
暂存配套的 Linux aarch64 SDK、aorta-msgs、vbot-edu-msgs、FlatBuffers wheel 及发布／许可证元数据，
核对固定哈希，并复用已校验文件。容器不联网时，先将这些相同制品带入制品目录；
可跳过下载，不跳过校验。下载附件需要网络，基础配套无需从 PyPI 下载。
暂存文件不会将 ARM64 SDK 安装进容器的 Python 环境。
制品缺失或无效时停止，不在机器人端下载依赖。

```bash
RECIPE=subscribe-state &&
PREVIEW_ARGS=() &&
python3 tools/fetch_sdk.py --output artifacts/edu-sdk-2026.10.14 &&
bazel build "//recipes/$RECIPE:main" &&
bazel run "//recipes/$RECIPE:main" -- "${PREVIEW_ARGS[@]}" &&
PACKAGE_DIR="artifacts/python-$RECIPE" &&
python3 tools/package_python.py --recipe "$RECIPE" \
  --assets-dir artifacts/edu-sdk-2026.10.14 --output "$PACKAGE_DIR" &&
python3 tools/package_python.py --verify "$PACKAGE_DIR"
```

`subscribe-state` 使用空 Bash 数组即可。选择运动示例时，将命令块开头的两行赋值替换为
`RECIPE=locomotion` 和 `PREVIEW_ARGS=(--mode stand)`；其离线预览也必须指定 `--mode`。
带引号的数组会通过 Bazel 的 `--` 分隔符逐项传递参数。
其他参数见所选 [Recipe](../../recipes/README.zh-CN.md)。
PREVIEW_ARGS 中不要加入 `--execute`：此阶段只预览和打包，不连接设备，也不执行所选动作。

容器内打包工具替代手动 tar／复制 wheel：检查所选 Recipe、四个基础 wheel、发布哈希、
元数据／依赖闭包及随包许可证，生成 `PACKAGE_MANIFEST.json`、`requirements.txt`、`SHA256SUMS`
和源码压缩包；源码包含 `recipes/common.py`、`recipes/observe.py` 及所选入口。
打包不进行 SSH、SDK 安装或隐式构建，不覆盖已有输出；选择新目录，或校验并复用已有包。
默认下载仅暂存四个 ARM64／基础 wheel 及发布／许可证元数据；仅在需要全部 SDK 制品时使用
`fetch_sdk.py --profile all`。


压缩包保留 `python -m` 所需的 `recipes/` 包结构，以及适用的 LICENSE/NOTICE；
不包含 venv 或 SDK／原生二进制。

工具的 `base` 配套覆盖状态、消息元数据、ASR 等仅依赖 SDK 的操作。
音视频数据保存另需 `numpy==2.2.6`，相机解码还需 `av==16.1.0`；本部署包及 SDK Release 均不附带它们。
使用这些选项的应用需单独准备匹配 ARM64 与设备 Python ABI（当前配套为 Python 3.10）的依赖包，
独立检查完整性与许可证。不要向已校验的基础包追加文件，或重写校验和绕过检查。
只读状态示例无需这两项可选依赖。

## 2. 从具备 SSH 连接的机器传输

先完成[公钥登录](../robots/quadruped-common/connection.zh-CN.md)。将 ROBOT 改为确认可用的
设备地址或普通 vbot SSH 别名。SSH 不可达时，先连接设备或修正地址，不继续部署。

步骤 1 的容器可使用 SSH 时在同一 shell 中执行；否则先把准备好的 PACKAGE_DIR 交给已授权的宿主机，
并将该变量设置为宿主机上的实际路径。身份检查应显示 vbot、aarch64 和受支持的
Python 版本。每次部署使用新目录，不覆盖其他应用。任何命令失败都应立即停止。

```bash
ROBOT=vbot@192.168.126.2 &&
ssh -o BatchMode=yes "$ROBOT" \
  'test "$(id -un)" = vbot && test "$(uname -m)" = aarch64 &&
   python3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" &&
   id -un && uname -m && python3 --version' &&
APP_DIR=$(ssh -o BatchMode=yes "$ROBOT" \
  'mkdir -p /userdata/vbot/apps && mktemp -d /userdata/vbot/apps/python-recipe-XXXXXX') &&
test -n "$APP_DIR" &&
printf 'Device application directory: %s\n' "$APP_DIR" &&
scp -r "$PACKAGE_DIR/." "$ROBOT:$APP_DIR/" &&
ssh "$ROBOT"
```

第一条 SSH 命令会检查账户、架构与 Python 3.10+，通过后才创建目录或传输。失败时先解决不匹配，不绕过检查。
记下输出的 APP_DIR。后续命令在最后一条 ssh 打开的**设备 shell**执行；
开发机 shell 变量不会自动带入设备。如果只有宿主机可以 SSH，先把暂存的 PACKAGE_DIR 交给宿主机。

## 3. 在设备创建运行环境

将下面的 `python-recipe-ABC123` 替换为步骤 2 实际输出的目录名。
这是**应用部署目录**，不是预装仓库。先核验校验值，通过后才解压和安装；任一校验失败都应停止。

```bash
cd /userdata/vbot/apps/python-recipe-ABC123 &&
sha256sum -c SHA256SUMS &&
tar -xzf python-recipe.tar.gz &&
unset PYTHONPATH &&
unset AORTA_CORE_FFI_LIB &&
export PYTHONNOUSERSITE=1 &&
python3 -m venv .venv &&
.venv/bin/python -m pip install --no-index --find-links wheelhouse -r requirements.txt &&
.venv/bin/python -m pip check &&
.venv/bin/python -c 'import aorta; from locomotion.LocomotionStatus import LocomotionStatus; core = aorta.load_library(); print("SDK imports and native runtime OK; ABI", core.aorta_abi_version())'
```

缺少 Python、venv 或原生运行依赖时，应先按受支持的设备环境解决，不要装进系统 Python，
也不要复用其他应用的环境。此安装步骤仅针对基础配套，不启用上文的可选采集／解码功能。

## 4. 从应用部署目录运行

此时目录内已有 `recipes/`、`wheelhouse/` 与 `.venv/`，
不需要 .git、MODULE.bazel、SDK 源码或仓库其他内容。在同一个设备 shell 中执行：

```bash
. .venv/bin/activate &&
unset PYTHONPATH &&
unset AORTA_CORE_FFI_LIB &&
export PYTHONNOUSERSITE=1 &&
export PATH="/opt/vita/aorta/bin:$PATH" &&
export ZENOH_SESSION_CONFIG_URI=/opt/vita/aorta/edu/edu_session.json5 &&
python -m recipes.subscribe-state.main --execute --count 3 --timeout 10
```

部署前先在开发容器内完成离线预览；设备上的命令读取三条状态消息。超时不代表成功。
其他参数、安全／采集授权要求和完成条件见对应 [Recipe](../../recipes/README.zh-CN.md)；
选择其他 Recipe 时，应同时替换模块名和设备运行参数，使用其文档中的运行命令，
不要直接沿用预览参数。尤其是 `--count` 适用于流式读取示例；运动的实机执行还需明确确认安全条件。

重新登录后，先 cd 到记下的应用目录，再执行上述环境配置／激活步骤，不要假设 .bashrc
已激活此 venv。原生 SDK 使用独立 shell，避免 ROS 的 PYTHONPATH 覆盖 wheel 包。
更新应用时重新构建并部署到新目录，验证后再决定是否切换[自启动入口](../guides/user-autostart.zh-CN.md)；
本流程不会修改自启动脚本或启动后台进程。
