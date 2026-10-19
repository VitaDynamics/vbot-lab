# 测试

<p align="center"><a href="README.md">English</a> | 中文</p>

使用 Python 3.10+ 与 Bash，在宿主机或 CI runner 的仓库根目录运行纯仓库检查：

```bash
python3 tools/run_checks.py --scope repository
```

在配套开发容器内，从仓库根目录执行：

```bash
python3 tools/container_context.py
python3 tools/run_checks.py --scope recipes
python3 tools/run_checks.py --scope packaging
bazel build //:repository_files //recipes/...
bazel test //tests:repository_layout_test //tests:agent_workspace_test //tests:recipe_test //tests:release_configuration_test
```

遵循[执行位置](../docs/development/README.zh-CN.md)：所有 Bazel 命令、SDK 测试、Recipe 预览和应用测试
都在容器内执行，CI 同样遵守。`--list` 仅列出分组，属于只读操作。
共用分组位于 [checks.json](../catalog/checks.json)；不符合开发上下文时，执行器会在运行 Recipe 检查前停止。

## 独立应用

Skill 测试检查共享发现及保留外部项目指令／其他 Skills；全新 harness 行为仍需手动检查。

test_applications.py 在仅容器可运行的打包分组中执行，覆盖独立工作区生成、不覆盖已有文件、
显式源码清单、模拟 wheel 的双架构可复现打包、预览／模拟隔离、订阅清理与溢出，以及诊断授权／超时语义。
同时运行健康监测模型的空输入、过期、排序、异常值及恢复测试。
Bazel 入口为 `//blueprints/health-monitor:model_test` 和 `//tests:applications_test`。
测试不连接设备，SDK 集成 CI 会执行打包分组。
生成的 Python CLI 使用独立子进程检查预览、模拟、参数／配置错误、缺失／过期数据及中断的
0/1/2/130 退出码。数据流／中断用例使用模拟传输和时钟，所有子进程均阻止导入 SDK。
回归覆盖延迟消费时保留回调时间、出队前后发现 SDK 丢包，以及空等待期间的丢包。
C++ 序列化测试也覆盖积压消息按回调时间过期，以及无效数据不刷新有效样本。
名称边界测试在生成前拒绝结尾连字符，Python 打包清单使用相同规则。
诊断测试仅使用模拟 SDK，区分导入、Node 创建、订阅、样本到达及清理失败。
真实 Git 检查验证两种生成项目的共用忽略规则，涵盖环境文件变体、会话、凭据字典、密钥，
并保留可见的 .env.example 例外。真实 SDK 套件检查完整／默认消息，以及损坏的根偏移、
vtable、字段、嵌套 header、字符串和表向量。坏包不能让 Python 监测成功或刷新已有有效数据；
C++ 测试同样拒绝全零输入。

并行的 [C++ 健康监测](../blueprints/health-monitor/cpp/README.zh-CN.md)提供显式目标
`model_cpp_test`、`sdk_cpp_test` 和 `//tests:health_monitor_cpp_test`，覆盖不依赖 SDK 的状态转换、
真实 FlatBuffer 解码、CLI／配置失败，以及 Python／C++ 状态摘要一致性，不创建 Node。
SDK 集成运行这些原生测试，再交叉构建 ARM64 程序和 C++ 测试，但不执行 ARM64 产物。
生成器支持 Python 与 C++，分别提供独立构建文件。C++ 生成测试核对 include 路径迁移、
工具链／元数据完整性，以及 Python 打包工具对 C++ 的明确拒绝。
SDK 集成另行构建／测试生成的 C++ 工作区、运行原生预览／模拟，
并交叉构建／检查其 ARM64 程序与测试，不连接设备。
另行构建／测试生成的 Python 工作区，使用真实 SDK wheel 打包、校验，
在全新 venv 安装并检查 wheel 原生 ABI，执行离线预览／模拟；独立应用 ARM64 包仅校验不执行。
安装后的独立 Python 包还会通过包内 wire.py 和已安装 SDK 元数据，解码合法默认消息并拒绝全零坏包，
不创建 Node。
打包测试覆盖打包及校验时拒绝部署保留路径，即使归档与清单校验和被重新生成也会拒绝。
两种架构的包均用 tar 解压，再检查原包文件不变、原 SHA256SUMS 仍有效；应用自己的嵌套元数据仍被允许。
真实 SDK 集成也会在解压生成的 Python 包前后检查 SHA256SUMS。

## 仓库与文档

结构测试检查双语配对、支持 frontmatter 的语言导航、同语言链接、
两版代码示例一致性、Agent-first 导航、Recipe 任务入口和退役路径。
还保留设备类型边界、共用传感器数值及接线图／连接参数、SSH 文档命令、
设备 Agent API 路由、MCP JSON／握手顺序和 Bash 语法检查。
设备环境示例检查语法，并通过模拟 `source` 验证加载顺序和导出值，不加载设备文件。
Aorta／ROS 2 标识在中英文之间保持一致。
使用指南还检查是否混入测试报告专用章节及精度采样统计。

文档中的 SSH／HTTP 命令仅检查文本或语法，不对设备执行。
文档遍历排除重复的 Skill 发现别名，只检查一次 `skills/` 中的原始文档。

Viewer／社区导航与 Issue 入口链接在本地检查；模型检查核对随仓库提供的
`foot_quadruped` URDF 入口、网格清单与网格引用。
检查不会访问 Viewer，也不会向论坛发帖。
共用背部安装参考检查附件完整性、两类机器狗的导航，以及双语尺寸／紧固件数据一致性，
不依赖 PDF 或 CAD 运行库。

所有纳入版本控制的文本文件都会检查是否含有敏感网络地址、工作站路径、设备主机名和
不可分发的标识；会话配置、凭据字典和密钥文件不得纳入版本控制。`tests/check_schemas.py` 检查
`schemas/ros2/` 恰好包含 `routes.json` 中公开路由使用的定义、它们引用的类型以及说明取值的
常量定义，并检查 `MANIFEST.json` 与目录内容一致。

## Agent 工作区

离线套件检查：

- 索引格式、标识、引用、已知／未知设备类型及发布决策。
- Python／C++ Blueprint 的源码／目标入口、所属 Bazel 包，以及分开的 Recipe／Blueprint 摘要。
- 设备文档契约、待接入能力和本地工具的状态区分。
- 工作站／容器前置要求、缺失工具、Python 兼容性及 CLI 退出码。
- 清点过程不执行外部命令或网络调用。
- 设备 shell 账户、公开文件访问、环境不匹配、命令遮蔽、脱敏输出及独立 CLI 退出码；均不使用机器人测试。
- Codex／Claude Code 别名中的 Skill 内容一致性，以及 Claude 的共享指令导入。
- 源码工作区中目录软链接的相对路径元数据。
- 外部应用链接单个 Skill 的场景，包括参考仓库路径含空格的情况。

Bazel 会重新组织 runfiles，因此在其中跳过源码目录的软链接元数据测试，但仍检查别名内容。
直接运行 Python 套件和 GitHub Actions 会检查真实源码软链接。
CI 在 runner 执行仓库／工作区检查，在开发容器内执行不依赖 SDK 的 Recipe 测试及独立的固定 SDK 集成任务，
不运行设备测试，参阅 [CI](../.github/WORKFLOWS.zh-CN.md)。

`test_execution_policy.py` 检查分组边界、在启动子进程或创建输出前拒绝错误容器上下文、
由元数据生成的 SDK／Recipe 摘要及 CI 汇总门禁。策略测试中的命令执行均为模拟，
不会运行 Recipe、Bazel 或 Docker。

## 手工工作流检查

[全新会话场景](agent-scenarios/README.zh-CN.md)覆盖 Codex／Claude Code 实际 Skill 发现和任务选择，
不由确定性测试套件执行。
纯仓库套件不启动 harness 会话、SDK 应用、容器或设备程序。

普通外部 PR 不得触发实机测试。

## 发布配置

`test_release.py` 将[发布配置](../catalog/release.zh-CN.md)与设备配置、能力元数据、
Recipe 版本约束、C++ ABI 导入、生成的 Schema 元数据、SDK 指南、Compose 和 Bazel 比较。
还覆盖未填写字段、迭代分支／tag 配套、错误输入、发布 manifest 比较及本地模拟附件的
校验失败处理。不下载附件、拉取镜像、检查在线设备或执行发布；普通 CI 允许一致的草案配置。
显式使用 `--require-complete` 才会拒绝尚未填写的发布字段。

## Recipes 与发布版 SDK

`test_recipes.py` 不依赖 SDK，检查离线预览、参数上限、设备环境前提、语音／运动显式确认、队列溢出、超时、关联规则及资源释放。
`test_recipe_sdk.py` 是显式启用的测试，需要配套 wheel，检查真实生成类型、service header、RCP union 与依赖序列化，
并用模拟传输检查运动报告关联、RCP 执行／取消／超时清理及音视频消息解析。测试禁止创建真实 Node，不连接设备。

按 [SDK 指南](../packages/aorta/python/README.zh-CN.md)安装后运行：

```bash
bazel test --test_env=PATH="$PWD/.venv/bin:$PATH" //tests:recipe_sdk_test
```

该目标标记为 manual，默认 `bazel test //...` 不需要下载 wheel。构建与离线测试不能代替设备实际运行结果。

## C++ 显式测试

依赖包完整性、仓库版本匹配、路径检查及缺包报错可独立测试，不下载依赖或启动 Bazel：

```bash
python3 tests/test_offline_build.py
```

使用配套依赖包执行 Bazel 目标的方法见 [离线构建指南](../docs/development/offline-build.zh-CN.md)。
这些单元检查本身不能证明依赖包已包含干净构建所需的全部内容。

按 [C++ SDK 指南](../packages/aorta/cpp/README.zh-CN.md)设置制品目录后执行：

```bash
bazel test //tests:recipe_cpp_test //tests:recipe_cpp_sdk_test
```

第一个目标执行十一个 C++ 程序的预览、帮助与非法参数检查，包括四个新增只读分类的所有数据流选项；第二个检查真实生成类型的
DAG union／依赖、service header、FlatBuffer 验证、超时、中断及文件不覆盖行为，不创建 Node。
可选相机解码测试另需 FFmpeg 开发库及 libx265 编码器，只生成本地合成帧：

```bash
bazel test //tests:recipe_cpp_decoder_test
```

依赖 SDK 的目标均为 manual，在开发容器内运行。独立的 CI SDK 任务显式选择三个基础 SDK 目标，
可选解码仍需单独检查；各任务均不操作设备，不能把未运行记为通过。

## 干净环境 SDK 集成与 Python 部署包

在开发容器内执行：

```bash
python3 tools/sdk_ci.py --download \
  --assets-dir artifacts/sdk-ci-assets --work-dir artifacts/sdk-ci-work
```

核对固定 Release 哈希，检查全新原生 SDK 安装／导入、所有 Recipe 构建、`recipe_sdk_test`、
`recipe_cpp_test`、`recipe_cpp_sdk_test`，并在第二个全新环境中从生成包安装／离线预览。
也会检查 ARM64 部署包，但不在 x86_64 执行 ARM64 二进制。每次使用新的工作目录。
每个全新 SDK venv 均清除 `AORTA_CORE_FFI_LIB`，显式加载 wheel 自带的原生库并核对来源和发布 ABI；
仅检查导入无法覆盖延迟加载。
Linux x86_64 上还会为 ARM64 构建十一个基础 C++ Recipes 及 SDK 测试程序，检查 ELF 架构、加载器、
GLIBC 要求与目标运行库依赖；ARM64 测试程序仅构建不执行，原生 SDK 测试仍会运行。
同时构建两种语言的健康监测 Blueprint；原生运行模型、序列化和 C++ CLI 测试，
并为 ARM64 交叉构建 C++ 程序、模型测试和序列化测试。
SDK 检查还会核对 ARM64 `fastbuild`、`opt`、`dbg` 的实际编译命令。
下载及首次 Bazel 依赖解析需联网；pip 使用本地 wheel，不创建真实 Node 或设备连接。
具体边界见[工具说明](../tools/README.zh-CN.md#sdk-integration)。

`test_python_packaging.py` 使用模拟 wheel 检查可复现打包、完整性、元数据、架构／依赖／许可证错误、
篡改、保留已有输出及容器检查。还检查校验／打包参数互斥、默认／显式目标选择，
在读取前拒绝缺失、软链接或非普通的清单文件，并拒绝未列出的特殊文件；只读校验覆盖两种包架构。
通过 `--scope packaging` 或 manual 的 `//tests:python_packaging_test`
运行，仅在容器内执行；这些单元测试不执行 SDK，还通过模拟原生库探针覆盖加载失败、ABI 错误、
外部／缺失库、软链接越界及两种安装模式下覆盖变量的清除。真实固定 SDK 由上述全新安装流程覆盖。

`test_deployment_commands.py` 对中英双语的快速开始、Python 部署、Python SDK 安装、C++、两类应用模板、
C++ Blueprint、离线依赖包准备与工具命令链
逐个注入模拟命令失败，
确认后续命令不再执行；另覆盖目录为空、动态库缺失、venv 激活失败及交互式 shell／变量保留。
切换 Python 部署示例时，使用真实离线 CLI 核对空参数、必填参数和多参数传递，并拦截 SDK／设备访问。
SSH 前置检查在本地使用模拟的账户／架构／版本信息执行，确认不匹配时不会创建目录或传输；
C++ 不要求 Python 运行环境。测试不进行实际构建、安装或设备连接。通过 `--scope packaging` 或 manual 的
`//tests:deployment_commands_test` 在开发容器内运行；SDK CI 包含这两组打包相关测试。

`test_execution_policy.py` 中的模拟检查覆盖错误／截断 ELF、错误加载器、过新的 GLIBC 要求及目标库缺失，
不调用 binutils；离线入口测试检查 ARM64 目标选择，并拒绝交叉 `run`／`test`。
原生测试仅显式继承已通过检查的容器声明，仍拒绝宿主机执行并忽略外部 Bazel 配置。
