# 测试

<p align="center"><a href="README.md">English</a> | 中文</p>

在仓库根目录使用 Python 3.10+ 与 Bash：

```bash
python3 tests/check_repository.py
python3 tests/check_schemas.py
python3 tests/test_agent_workspace.py
python3 tests/test_recipes.py
python3 tests/test_family_recipes.py
bazel build //:repository_files //recipes/...
bazel test //tests:repository_layout_test //tests:agent_workspace_test //tests:recipe_test
```

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

Viewer／社区导航与 Issue 入口链接在本地检查；尚未提供 URDF 和网格时，
模型元数据必须将预留的 `foot_quadruped` 资源明确标为不可用。
检查不会访问 Viewer，也不会向论坛发帖。

所有纳入版本控制的文本文件都会检查是否含有私有网络地址、工作站路径、设备主机名和私有
仓库名；会话配置、凭据字典和密钥文件不得纳入版本控制。`tests/check_schemas.py` 检查
`schemas/ros2/` 恰好包含 `routes.json` 中公开路由使用的定义、它们引用的类型以及说明取值的
常量定义，并检查 `MANIFEST.json` 与目录内容一致。

## Agent 工作区

离线套件检查：

- 索引格式、标识、引用、已知／未知设备类型及发布决策。
- 设备文档契约、待接入能力和本地工具的状态区分。
- 工作站／容器前置要求、缺失工具、Python 兼容性及 CLI 退出码。
- 清点过程不执行外部命令或网络调用。
- 设备 shell 账户、公开文件访问、环境不匹配、命令遮蔽、脱敏输出及独立 CLI 退出码；均不使用机器人测试。
- Codex／Claude Code 别名中的 Skill 内容一致性，以及 Claude 的共享指令导入。
- 源码工作区中目录软链接的相对路径元数据。
- 外部应用链接单个 Skill 的场景，包括参考仓库路径含空格的情况。

Bazel 会重新组织 runfiles，因此在其中跳过源码目录的软链接元数据测试，但仍检查别名内容。
直接运行 Python 套件和 GitHub Actions 会检查真实源码软链接。
CI 运行仓库、工作区和不依赖 SDK 的 Recipe Python 测试，不运行设备测试。

## 手工工作流检查

[全新会话场景](agent-scenarios/README.zh-CN.md)覆盖 Codex／Claude Code 实际 Skill 发现和任务选择，
不由确定性测试套件执行。
离线套件不启动 harness 会话、SDK 应用、容器或设备程序。

普通外部 PR 不得触发实机测试。

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

这些目标均为 manual，普通 CI 不下载 SDK 或操作设备；需显式运行，不能把未运行记为通过。
