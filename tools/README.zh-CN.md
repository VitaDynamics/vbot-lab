# 开发工具

<p align="center"><a href="README.md">English</a> | 中文</p>

环境清点、能力查询及容器内 SDK／打包工具。

Bazel 依赖交付见 [离线构建](../docs/development/offline-build.zh-CN.md)。
`prepare_bazel_offline.py` 在联网的开发容器内显式准备依赖包；`bazel_offline.py`
校验依赖包后执行禁止仓库下载的 Bazel 构建。与环境清点工具不同，这两个工具
会执行构建工具并写入构建产物。
工具使用 Python 3.10+。清点与部署包检查不需要安装 SDK；显式 SDK 集成命令还会执行 Bazel、编译器与 SDK 测试。

## 环境清点

```bash
python3 tools/check_environment.py --profile host
python3 tools/check_environment.py --profile container --robot-type foot_quadruped
```

工作站模式检查 PATH 上的 Bash、Git 和 Docker；Bazel 仅在容器模式要求，容器模式检查 Bash、Git 和 Bazel，不要求 Docker。
实际 Docker 可用性检查及进入容器的步骤见[容器指南](../docker/README.zh-CN.md)。
Python 版本按本地工具基线 3.10 检查，不检查 SDK 原生依赖或设备 Python ABI。
其他工具仅查找、不执行；预期 Bazel 版本读取自 `.bazelversion`，
不是对已安装二进制版本的观测。

输出为 JSON。退出码 0 表示清点完成，未发现必需工具缺失或设备类型发布阻塞；
1 表示这些本地要求需要处理；2 表示输入或仓库／索引数据错误。
参数解析错误写入 stderr。
`sdk_status` 与本地清点成功、仓库接入状态分开报告：索引 SDK 接入为 `pending` 时返回
`blocked_integration`，为 `integrated` 时返回 `not_verified`；清点不导入 SDK，也不检查 ABI。
通过 `python3 tools/vbot_catalog.py --summary` 获取由索引生成的 SDK 元数据及各自统计的 Recipe／Blueprint 数量，
不要把清点退出码当作应用就绪状态。

工具不调用 Docker、不安装包、不拉取镜像、不通过 SSH 连接，也不调用机器人 API，
并明确列出未测试部分。不传设备类型时保持未选择；未知类型报错，
规划类型不因共用硬件就继承软件支持。

## 能力查询

```bash
python3 tools/vbot_catalog.py --robot-type foot_quadruped --capability device.agent.content
```

详见[索引格式与查询决策](../catalog/README.zh-CN.md)。
退出码 0 表示查询成功，包括返回被阻塞能力的情况；2 表示查询或索引错误。
工具不执行索引条目。

两个工具均根据自身文件的实际位置定位参考仓库，可在其他应用目录通过绝对路径调用。
仅在明确选择另一份完整 VBOT Lab 仓库时使用 `--root`。

## 设备 shell 清点

独立脚本已具备时，在配置好的设备 `vbot` shell 中运行：

```bash
python3 tools/check_device_environment.py
```

此工具检查有效账户、公开 setup 文件可读性、指定环境变量和 `aorta`／`ros2`／`timeout` 命令查找，
并拒绝抢先匹配到其他位置的 Aorta 程序。不输出当前环境值或会话文件内容，不运行工具、编辑文件或联系接口。
退出码 0 表示 shell 检查通过；1 表示需要处理；2 表示参数无效。
它不能证明设备身份、ROS 类型加载、实际收数或持久化有效。
与上方依赖仓库的工具不同，它不需要索引或 SDK，也不接受 `--root`。
手动检查、传输范围、`.bashrc` 配置及单独执行的有时限在线检查见[设备配置](../docs/getting-started/device-environment.zh-CN.md)。

## 下载固定版本的 SDK 制品

在开发容器的仓库根目录执行：

```bash
python3 tools/fetch_sdk.py --output artifacts/edu-sdk-2026.10.14
```

默认 `python` 配套下载七个文件：四个 Linux ARM64／基础 wheel、`EDU_SDK_MANIFEST.json`、
`SHA256SUMS` 和 FlatBuffers 许可证。版本与哈希来自 [release.json](../catalog/release.json)，
不查询可变的“最新版”。本地原生 SDK 测试使用 `--platform linux_x86_64`；
需要含 C++／Schema 压缩包的全部 SDK 制品时使用 `--profile all`。
复用已校验文件，发现无效文件会报错而不覆盖。下载需要网络，不进行 SDK 安装、构建或 SSH；
断网使用时可另行带入相同制品。

## 打包 Python Recipe

先在容器内构建并预览所选 Recipe，再单独打包：

```bash
python3 tools/package_python.py --recipe subscribe-state \
  --assets-dir artifacts/edu-sdk-2026.10.14 --output artifacts/first-state &&
python3 tools/package_python.py --verify artifacts/first-state
```

打包仅可在容器内运行，默认目标为 `linux_aarch64`，输出目录必须是新目录；
不构建、安装、联网或操作设备。`--platform linux_x86_64` 生成的是**本地预览**包，不可部署到机器人。
Recipe 必须已纳入能力索引；工具检查四个基础 wheel 的固定哈希、平台标签、发行元数据、依赖闭包与随包许可证。

输出仅包含所选源码入口／公共模块、LICENSE/NOTICE、四个 wheel、SDK manifest、FlatBuffers 许可证、
固定版本的 `requirements.txt`、`PACKAGE_MANIFEST.json` 与 `SHA256SUMS`。
manifest 记录源码哈希、目标及依赖／许可证清单；不复制 venv、会话配置、密钥或完整仓库。
NumPy／PyAV 数据保存／解码选项不在基础配套内，使用前参阅 [Python 部署](../docs/development/python-deployment.zh-CN.md)。

`--verify` 仅读取现有包，可在宿主机或 CI 执行，拒绝被修改、缺失、多余的文件及 SDK 配套不一致。
它按 `PACKAGE_MANIFEST.json` 记录的平台核对包内 wheel，不按宿主机架构判断。
不要将 `--verify` 与 `--recipe`、`--assets-dir`、`--output` 或显式 `--platform` 混用；
这些组合返回参数错误 2。`PACKAGE_MANIFEST.json` 和 `SHA256SUMS` 必须是包内普通文件，
不能是软链接或特殊文件。
哈希检查完整性，不是发布者签名，也不证明设备兼容。传输／安装／运行属于[快速开始](../docs/getting-started/README.zh-CN.md)
中的独立显式步骤，打包不会自动部署。

<a id="sdk-integration"></a>

## 无机器人 SDK 集成检查

在开发容器内执行，每轮使用新的工作目录：

```bash
python3 tools/sdk_ci.py --download \
  --assets-dir artifacts/sdk-ci-assets --work-dir artifacts/sdk-ci-work
```

`--download` 获取或复用完整的固定版本 Release；仅在全部制品已具备时省略。
哈希检查后，在全新原生 venv 安装并检查导入／依赖，构建全部 Python 与 C++ Recipe 目标，
以模拟传输运行真实生成类型及 C++ SDK 测试。还会生成部署包，在第二个全新 venv 中安装并离线预览，
检查 ARM64 部署包，以及运行模拟制品的打包测试。两个 venv 均清除 `AORTA_CORE_FFI_LIB`，
显式调用 `aorta.load_library()`，确认加载的是该 venv 中 wheel 自带的库，
并与发布配置核对 ABI，不创建 Node。Linux x86_64 上还会使用 ARM64 SDK
交叉构建全部十一个基础 C++ Recipes 与 C++ SDK 测试程序；`cpp_artifacts.py` 仅读取 ELF 头、
加载器、GLIBC 要求及递归的 `DT_NEEDED`，对照目标 SDK／编译器库检查；还会检查
`fastbuild`、`opt`、`dbg` 的实际 ARM64 编译命令。文档中的部署命令链使用模拟命令检查
校验／构建／传输失败、输出目录为空、动态库缺失及设备写入前账户／架构／Python 版本不匹配等情况，
不执行这些 ARM64 文件。
不覆盖已有工作目录。

Release 下载和首次 Bazel 依赖解析需要网络，wheel 安装离线完成。这是不连接设备的 CI，
不是从零开始的完全断网构建。不创建 Aorta Node，不通过 SSH 连接，也不证明机器人运行效果。
原生测试与 ARM64 制品检查分开报告，均不能代替机器人上的 ARM64 实际运行。
打包依赖构建见[离线 Bazel](../docs/development/offline-build.zh-CN.md)。

首次使用时，Bazelisk 可能下载 .bazelversion 固定的 Bazel 版本。
SDK CI 为此准备步骤保留 180 秒；需要时使用 --bazel-prepare-timeout SECONDS，范围 30–600 秒。
仅检查编译器版本的步骤仍限制为 20 秒。准备失败时在 stderr 输出 JSON，包含
stage=bazel_prepare、独立 error_code 及 dns、tls、proxy、http、integrity 或 network 等脱敏原因。
不输出原始下载内容或 URL；bazel_prepare_timeout 不代表 SDK 不兼容。

上述三个命令完成返回 0，输入／上下文／操作失败返回 1，命令行参数错误返回 2。
`sdk_ci.py` 还需要 Bazel 7.6.1、原生 C++17 编译器、镜像内的 ARM64 GCC／G++ 11／binutils 和支持 Zstandard 的 `tar`。
失败时保留部分输出供检查；修正原因后使用新的输出／工作目录。

## 独立应用与诊断

SDK 集成检查会构建两种语言的健康监测 Blueprint，执行 Python／C++ 模型与真实类型序列化测试，
并交叉构建／检查 C++ ARM64 程序；C++ 预览及语义对照测试不创建 Node。
应用工作区／打包及诊断回归位于仅容器可运行的打包分组。

在开发容器内，用 `create_app.py --name my-monitor --output /tmp/my-monitor`
从[健康监测 Blueprint](../blueprints/health-monitor/README.zh-CN.md)创建 Python 工作区。
C++ 使用 `create_app.py --language cpp --name my-cpp-monitor --output /tmp/my-cpp-monitor`，
文件组成及语言边界见[应用模板](../templates/README.zh-CN.md)。
C++ 项目包含已迁移路径的源码／辅助代码、本地 SDK 规则与 ARM64 工具链，
按项目 README 进行原生测试、交叉构建及二进制／库部署。
SDK 集成也会独立构建／测试此工作区，不访问设备。
生成的 Python 工作区也会构建／测试，使用真实 SDK wheel 打包、校验，
在全新 venv 安装并检查原生运行库／ABI，执行离线预览／模拟；ARM64 包仅单独校验不执行。
`package_app.py --project /tmp/my-monitor --assets-dir artifacts/edu-sdk-2026.10.14 --output /tmp/my-monitor-package`
按 Python 项目的 APP.json 显式清单打包运行文件及四个固定 SDK wheel，不构建或部署。
`package_app.py --verify /tmp/my-monitor-package` 仅校验，可在宿主机／CI 执行。
输出必须为新目录，新增依赖需要单独准备适合应用的流程。
APP.json 由打包工具生成，部署控制文件以及 wheelhouse/、licenses/ 为保留路径，
source_files 不能与其重叠。具体路径见生成的 [Python 工作区指南](../templates/python-app/README.zh-CN.md)。
打包和校验均会在解压前拒绝冲突。

`diagnose.py --level inventory` 是本地只读清点。SDK 执行在容器内，设备检查与单流采样
需在设备 vbot shell 显式启用。命令、状态语义及分享边界见[分层诊断](../docs/development/diagnostics.zh-CN.md)。
其中 sdk／sample 层级依赖 Python SDK；C++ 使用指南中独立的 SDK 输入、设备动态库及单路 CLI 检查，
不需要 Python venv 或安装 wheel。

应用开发可使用 [vbot-app-dev](../skills/vbot-app-dev/SKILL.zh-CN.md)，
限定范围的故障检查使用 [vbot-diagnose](../skills/vbot-diagnose/SKILL.zh-CN.md)。

## 验证与后续工具

遵循[执行位置](../docs/development/README.zh-CN.md)：纯仓库检查可在宿主机或 CI runner 执行；
Bazel、Recipe 预览、模拟应用测试、依赖准备和打包必须在配套开发容器内进行，CI 同样遵守。

```bash
python3 tools/run_checks.py --scope repository
```

在已检查的开发容器内，从仓库根目录执行：

```bash
python3 tools/container_context.py &&
python3 tools/in_container.py -- bazel build //recipes/subscribe-state:main &&
python3 tools/run_checks.py --scope recipes &&
python3 tools/run_checks.py --scope packaging
```

`container_context.py` 只读检查，符合已声明的容器上下文时返回 0，否则返回 1，参数错误返回 2。
同时要求运行时标记和 `VBOT_DEV_CONTAINER=1`；它不验证镜像身份或工作区挂载，需先按容器指南检查。
`in_container.py` 检查上下文后才执行显式命令，保留参数和当前工作目录，并传递退出状态；
不自动进入／创建容器，也不连接机器人。

`run_checks.py --scope ... --list` 只列出[检查分组](../catalog/checks.json)。不传 `--list` 时，
全部检查通过才返回 0；检查失败、分组元数据错误或上下文缺失返回 1，命令行参数错误返回 2。
`CI=true` 或 `--profile container` 都不能豁免容器要求。

`check_release.py` 比较[发布配置](../catalog/release.zh-CN.md)与仓库中的组件版本，
并可选地核对已下载的 manifest 和附件校验值。工具离线、只读，不发布或批准版本。

Schema 生成、用户程序部署和设备日志收集工具仍处于规划阶段。
任务流程见 [Skills](../skills/README.zh-CN.md)，证据边界见[测试说明](../tests/README.zh-CN.md)。
