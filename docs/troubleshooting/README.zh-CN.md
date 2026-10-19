# 排障

<p align="center"><a href="README.md">English</a> | 中文</p>

从第一个失败的步骤开始，不先重启服务。仓库检查可在宿主机进行；构建、SDK、预览和打包检查
在开发容器内执行。设备命令只在获准 SSH 登录后的目标机器人 vbot shell 中执行。
参阅[执行位置](../development/README.zh-CN.md)和[快速开始](../getting-started/README.zh-CN.md)。
分层检查见[诊断指南](../development/diagnostics.zh-CN.md)，C++ 使用其中的
[SDK／运行库／采样路径](../development/diagnostics.zh-CN.md#cpp)，缺少 Python wheel 不代表 C++ 失败。

| 症状 | 可能原因 | 从这里开始 |
| --- | --- | --- |
| 容器上下文被拒绝 | 宿主机 shell、容器会话未声明、工作区错误 | [容器上下文](#container) |
| SDK 导入或动态库加载失败 | 解释器错误、ROS PYTHONPATH、架构错误、wheel 不配套 | [SDK 导入](#sdk-import) |
| Bazel 构建失败或无法下载依赖 | Bazel／工具链错误、缺少配套依赖包 | [构建](#build) |
| 打包缺文件或校验失败 | 下载不全、输出被改、目标不匹配 | [部署包](#package) |
| SSH 超时、认证或指纹错误 | 网络／地址、密钥访问或主机身份 | [SSH](#ssh) |
| 列出 topic 但没有解码样本 | shell／会话／类型／生产者／输入尚未确认 | [没有数据](#no-data) |
| 部署后程序无法启动 | 目录／解释器错误、依赖缺失或 ABI 不匹配 | [运行](#runtime) |

<a id="container"></a>
## 容器上下文

宿主机按[容器指南](../../docker/README.zh-CN.md)检查并复用容器。
在所选容器的仓库根目录执行：

```bash
python3 tools/container_context.py
python3 tools/check_environment.py --profile container
```

`context_status=eligible` 要求运行时证据及已声明的开发上下文，不证明镜像、挂载、工具链或 SDK 兼容。
Compose／编辑器会话自动声明，已有容器使用文档中的 exec 命令。
已经位于确认过的开发容器内时，检查并复用，不要求嵌套 Docker。
单独在宿主机设置变量不是修复，不自动重建容器、清空缓存或修改 Docker 权限。

<a id="sdk-import"></a>
## SDK 导入

在开发容器或已部署应用的设备 vbot shell 中，使用该应用的 venv 解释器。
设备安装先进入记下的 APP_DIR：

```bash
unset PYTHONPATH
unset AORTA_CORE_FFI_LIB
export PYTHONNOUSERSITE=1
.venv/bin/python --version
.venv/bin/python -m pip check
.venv/bin/python -c 'import platform; import importlib.metadata as m; print(platform.machine()); print({name:m.version(name) for name in ("aorta-sdk","aorta-msgs","vbot-edu-msgs","flatbuffers")})'
.venv/bin/python -c 'import aorta; from locomotion.LocomotionStatus import LocomotionStatus; core = aorta.load_library(); print("SDK imports and native runtime OK; ABI", core.aorta_abi_version())'
```

预期：Python 3.10+、所选架构、与包内 requirements 一致的版本，以及导入／原生库加载成功并输出 ABI。
`ModuleNotFoundError` 通常先检查解释器与 wheel；`wrong ELF class`、`Exec format error`、
`GLIBC_*` 或 `GLIBCXX_*` 需检查架构／运行库，不是反复 pip 安装。
包元数据显示版本不等于原生库能加载，仅导入也不会触发原生库的延迟加载。
显式 `load_library()` 会执行 ABI 检查，不创建 Node。按 [Python SDK](../../packages/aorta/python/README.zh-CN.md)
或 [C++ SDK](../../packages/aorta/cpp/README.zh-CN.md)继续，不复制开发机 venv 或替换机器人系统库。

<a id="build"></a>
## Bazel 构建

开发容器内执行：

```bash
bazel --version
g++ -dumpmachine
python3 tools/in_container.py -- bazel build //recipes/subscribe-state:main
```

使用 Bazel 7.6.1 和目标架构的编译器。x86_64 C++ 二进制不是 ARM64 部署制品。
依赖下载失败时取得匹配、已校验的依赖包，使用[离线构建入口](../development/offline-build.zh-CN.md)。
SDK 压缩包不等于 Bazel 依赖包，不自动切换注册表、删除缓存或改在机器人上编译。

全新镜像中，bazel --version 可能先通过 Bazelisk 下载固定版本工具。
SDK CI 为此准备保留 180 秒，可通过 --bazel-prepare-timeout 调整，范围 30–600 秒。
出现 stage=bazel_prepare 时，先按 reason 检查下载访问，不先归因于 SDK 不兼容；
参阅 [SDK 集成检查](../../tools/README.zh-CN.md#sdk-integration)。

<a id="package"></a>
## 打包或校验失败

打包命令在创建输出前检查输入哈希、wheel 元数据、基础依赖闭包及许可证是否存在。
缺失或不一致会明确报错，应使用同一配套 Release 的制品，不混入其他 SDK 版本。
已有输出不会被覆盖。在宿主机或容器中检查已生成的完整包：

```bash
python3 tools/package_python.py --verify artifacts/first-state
```

预期：`status=complete`、`device_contacted=false`、`deployed=false`。
被修改或不完整的包不应传输。检查原因并在新目录重新生成，不通过改写哈希“修复”校验。
`base` 配套不含可选保存／解码所需的 NumPy／PyAV，详情见 [Python 部署](../development/python-deployment.zh-CN.md)。

<a id="ssh"></a>
## SSH

在后续实际传输的机器上，使用已确认的 IP 或 vbot 别名：

```bash
ROBOT=vbot@192.168.126.2
ssh -o BatchMode=yes "$ROBOT" 'id -un; uname -m; python3 --version'
```

预期：`vbot`、`aarch64`、Python 3.10+。超时／无路由／拒绝连接时检查有线或 Wi-Fi 及地址；
`Permission denied` 检查所选公钥和同一环境的 SSH-agent 访问；未知／变化的主机密钥先确认设备身份与指纹。
按[连接配置](../robots/quadruped-common/connection.zh-CN.md)处理，不扫描其他机器人、不嵌入密码、
不关闭主机指纹检查或覆盖已有密钥。

<a id="no-data"></a>
## 列出了 topic 但没有数据

SSH 登录后加载公开设备环境，只检查应用需要的路由。首个只读示例在设备 vbot shell 中执行：

```bash
export PATH="/opt/vita/aorta/bin:$PATH"
export ZENOH_SESSION_CONFIG_URI=/opt/vita/aorta/edu/edu_session.json5
test -r "$ZENOH_SESSION_CONFIG_URI"
timeout 12s aorta --group default topic echo /locomotion/status --count 1
```

CLI 能解码样本而应用不能时，检查解释器、Schema 配套及进程实际环境。
两者都无数据时，检查[设备环境](../getting-started/device-environment.zh-CN.md)、确切[路由／类型](../interfaces/aorta-ros2.zh-CN.md)、
已安装软件和生产者／输入是否预期活跃。目录条目不是样本；仅超时不能判定 ACL 拒绝、能力不支持、
生产者停止或没有人／音频，未确认的原因保持未确认。
不为强行收数修改权限、设备模式或服务，音视频采集仍需单独授权。
仅 ROS 失败时先对比原生 Aorta 收数。

<a id="runtime"></a>
## 部署后程序无法启动

确认记下的应用目录、显式 venv／二进制路径、包校验、架构和会话环境。
设备没有预装仓库，开发机 Bazel 启动器不是部署制品。
C++ 按指南对已部署可执行文件和依赖库执行 `ldd` 检查。
依赖或 GLIBC 不匹配时返回构建／打包步骤。交互运行正常后再配置[自启动](../guides/user-autostart.zh-CN.md)，
非交互 shell 需要显式加载环境。

<a id="application-errors"></a>

## Python 健康监测错误

参考应用与生成的 Python 工作区在 stderr 输出 JSON 错误：

```json
{"status":"error","stage":"config","error_code":"config_not_found","next_step":"Select an existing configuration file with --config."}
```

| 阶段／错误码 | 下一步检查 |
| --- | --- |
| config / config_not_found、config_not_readable、config_read_failed | 选择可读配置文件，检查文件访问／存储，不先排查设备连接 |
| config / invalid_config | 使用 UTF-8 JSON，仅包含 stale_after_seconds，范围 (0, 120]，及 low_battery_percent，范围 [0, 100] |
| environment / development_container_required | 在选定开发容器内执行预览／模拟 |
| environment / device_user_required、session_config_not_set、session_config_not_readable | 检查 vbot shell 和文档中的设备 Aorta 环境 |
| sdk / sdk_not_installed、sdk_version_mismatch、sdk_load_failed | 使用应用 venv 和固定依赖，检查消息绑定与 BFBS 文件 |
| subscription / subscription_setup_failed | 使用有时限的只读诊断检查 Aorta 环境与所选路由 |
| subscription / telemetry_queue_overflow、sdk_samples_dropped | 程序为避免掩盖数据丢失而停止，检查处理负载／订阅设置 |
| runtime / unexpected_error | 检查最后完成的阶段与应用修改，分享日志前先审阅 |

这些错误以 1 退出，不输出原始异常或配置内容。正常结束时数据缺失／过期也以 1 退出，
但不属于配置异常，应查看最终快照中的流状态。命令行用法错误仍以 2 退出，中断以 130 退出。
任何错误都不会自动重启服务、修改权限、安装依赖或连接其他设备。

## 到社区反馈

未解决时使用 [Vbot 超能社区](https://forum.vbot.cn/)及[社区与支持](../community/README.zh-CN.md)反馈模板。
包含失败步骤、源码／SDK 配套、预期结果、实际退出码／错误和已做的检查。
未确认的设备／应用版本写未知，不以系统镜像或 CLI 版本替代。
分享前审阅并脱敏：不包含会话文件、凭据、私钥、完整环境输出、设备身份或未经允许的录制。
不自动发帖或上传日志，解决后在原话题补充结论。
具体仓库问题可用 GitHub Issues；漏洞按[安全说明](../../SECURITY.zh-CN.md)私下反馈。
