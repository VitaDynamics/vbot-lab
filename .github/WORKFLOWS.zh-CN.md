# CI 与仓库协作说明

<p align="center"><a href="WORKFLOWS.md">English</a> | 中文</p>

PR 及 `main`、`pre_release/**` 推送时，工作流将仓库检查与应用执行分开。
`repository-checks` 在 GitHub 托管运行器执行只读内容检查及模拟工具检查；
`recipe-checks` 在 `docker/compose.yaml` 选定的开发容器内执行不依赖 SDK 的预览和模拟应用流程。
`sdk-integration` 使用同一套固定镜像配置，执行真实 SDK 集成、全新 venv 安装、所有 Python／C++
Recipe 构建、SDK 序列化测试及部署包完整性检查；使用前核对 `catalog/release.json` 固定的制品。
每个全新 SDK venv 均清除 `AORTA_CORE_FFI_LIB`，显式加载 wheel 自带的原生库并核对来源和发布 ABI；
仅导入成功不足以证明原生库可用。
还会为 ARM64 交叉构建基础 C++ Recipes 并检查目标 ELF／依赖，不在 AMD64 runner／容器内执行 ARM64 程序。
同时核对 `fastbuild`、`opt`、`dbg` 的实际 ARM64 编译命令。
代码、镜像、SDK 获取及首次 Bazel 依赖解析需要网络；随后 pip 仅使用已校验的本地 wheel 安装。
这是不连接设备的集成任务，不是从零开始的完全断网构建。检查不联系机器人，不创建 Aorta Node，
也不启动模型会话。

保留现有必需的 `repository-layout` 汇总检查，汇总上述三个任务；任一失败、跳过或取消都不能通过。
[checks.json](../catalog/checks.json)是本地与 CI 共用的检查清单；参阅[执行位置](../docs/development/README.zh-CN.md)。

相同的本地命令见[无机器人 SDK 集成检查](../tools/README.zh-CN.md#sdk-integration)。
模拟制品的打包测试在该容器任务内运行；纯仓库检查仍可在宿主机执行。
该任务也构建 Python／C++ 健康监测 Blueprint，运行原生模型／解码／CLI 测试，
交叉构建 ARM64 的 C++ 程序／测试但不执行，并检查独立 Python／C++ 工作区生成、Python 打包与分层诊断流程。
生成的 C++ 工作区另行独立构建／测试，执行原生 SDK 预览及 ARM64 产物检查。
生成的 Python 工作区也会构建／测试，使用真实固定 SDK wheel 打包、校验，
在全新 venv 安装并执行离线预览／模拟；ARM64 部署包仅校验，不执行 ARM64 代码。

## 提交代码或 PR 前

在宿主机或 CI runner 的仓库根目录执行：

```bash
python3 tools/run_checks.py --scope repository
```

在已检查的开发容器内，从同一仓库根目录执行：

```bash
python3 tools/run_checks.py --scope recipes
```

宿主机可以通过选定的容器执行第二条命令。即使不依赖 SDK 或网络，Recipe 测试、Bazel 和打包
也不能直接在 runner／宿主机执行。容器不可用时如实说明未运行，不回退到宿主机。

按[贡献说明](../CONTRIBUTING.zh-CN.md)，为修改保留检查结果及相关构建或设备验证情况。
新建 Issue 时使用问题报告或文档改进模板；一般使用问题优先到
[社区与支持](../docs/community/README.zh-CN.md)交流。

[发布配置检查](../catalog/release.zh-CN.md)比较本地组件配套关系并测试不一致时的处理，
不下载附件，也不发布 Release。

## 迭代分支更新

使用选定版本族的 `pre_release/V<major>.<minor>.<patch>.X` 分支。
维护者完成适用检查后，可以直接提交和推送，不要求 PR；需要评审时也可使用工作分支 PR。
保留禁止强推和删除的保护。CI 在迭代分支推送后运行，不要求每个新提交先创建 PR
或先获得推送前的 CI 结果。

## 正式发布的评审与合并

1. 只有明确要求正式发布时，才向 `main` 提交 PR。
2. 由 [CODEOWNERS](CODEOWNERS) 列出的另一位维护者批准。
   新的待评审提交会使此前批准失效；最后一次推送的变更须由推送者之外的人批准。
3. 解决评审讨论，确保 GitHub Actions 的 `repository-layout` 检查在当前目标分支基础上通过。
   目标分支有新提交时，更新工作分支。
4. 使用 **Squash and merge**。为 `main` 配置保护，禁止直接推送、强推或删除，
   不配置管理员绕过权限。

## 版本迭代与正式发布

| 引用 | 用途 |
| --- | --- |
| `main` | 最新正式版本，不合入尚未正式发布的版本更新 |
| `pre_release/V1.6.0.X` | `V1.6.0` 版本族的长期迭代分支，末尾 `X` 保留为字母 |
| `V1.6.0.12` | 机器人应用 `V1.6.0-12` 配套的源码 tag；以发布配置中明确记录的源码 tag 为准 |
| `edu-sdk-*` | SDK 附件 Release tag，与源码 tag 和机器人应用版本分别管理 |

`V1.6.0` 的分支不作为所有后续版本的共用分支。
例如，新版本族 `V1.6.1` 使用自己的 `pre_release/V1.6.1.X` 分支。

1. 新版本族从明确的基线创建分支；切换管理方式时保留已有迭代内容。
   后续修改可直接向该版本族的分支提交，不要求 PR。
2. 更新[发布配置](../catalog/release.zh-CN.md)、组件配套与双语文档，
   完成离线检查及适用的 SDK／构建／设备检查后，在检查通过的迭代提交上创建新源码 tag。
3. 迭代 tag 不代表已批准正式发布。后续修改继续在选定的迭代分支上进行，
   日常迭代期间不提前创建提升 PR。
4. 只有明确要求正式发布时，才选定准确的已检查快照，填齐发布配置，提交提升至 `main` 的 PR。
   不混入其他修改，不移动已有迭代 tag；需要补充修改时使用新 tag。
5. 得到正式发布确认并完成维护者评审后，才通过 PR 流程更新 VBOT Lab 的 `main`，
   并按需发布已确认的源码版本和 SDK 附件。本工作流不会自动发布版本，
   不对 `main` 执行 reset 或强推。

匹配 `V*` 和 `edu-sdk-*` 的 tag 允许新增，但不能改写或删除。
需要修正时使用新 tag，不要让已有版本指向另一份内容。
创建源码 tag 不会自动创建 GitHub Release：本工作流没有 tag 触发器或 Release 发布步骤。
SDK 下载资产与源码 tag 分别管理。

## 自动化安全

工作流使用只读令牌、GitHub 托管运行器及固定完整 commit SHA 的 checkout action，
并关闭 Git 凭据持久化。仓库默认令牌同样为只读，不允许 Actions 批准 PR，
且要求 action 固定完整 commit SHA。修改 CI 时应保留这些边界，
不得向不可信 PR 代码提供密钥，也不得操作机器人。

Dependabot 告警覆盖 GitHub 能识别的依赖，不等于对 Bazel 依赖、下载的 SDK 包及原生库
进行了完整安全审查。更新 [SDK 配套版本](../docs/compatibility.zh-CN.md)时需单独检查这些内容。
漏洞请按[安全说明](../SECURITY.zh-CN.md)私下反馈。
