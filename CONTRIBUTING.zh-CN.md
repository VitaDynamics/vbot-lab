# 贡献说明

<p align="center"><a href="CONTRIBUTING.md">English</a> | 中文</p>

提交改动前，请说明解决的开发者问题、涉及的功能、验证方法及兼容性影响。

当前自动检查的范围见 [CI 与仓库协作说明](.github/WORKFLOWS.zh-CN.md)。

使用问题、应用讨论与新能力建议，优先按[社区与支持](docs/community/README.zh-CN.md)到论坛交流。
明确的仓库代码或文档修改使用 Issue／PR；已有相关论坛讨论时，附上链接即可。

- Python／C++ Recipes 与参考应用统一使用 Bazel；SDK API、Schema、代码、文档和 Skill 应保持一致。
- Aorta SDK 接入放在 `packages/aorta/python/` 与 `packages/aorta/cpp/`，单项任务参考程序放在 `recipes/`，完整参考应用放在 `blueprints/`。如实说明可用状态，不将提纲或规划中的 Blueprint 展示为可运行程序。
- Skills 仅在 `skills/` 维护一份，通过 `.agents/skills/` 与 `.claude/skills/` 软链接暴露。`CLAUDE.md` 仅薄层导入共享 `AGENTS.md`，不维护分叉的 harness 指令。发现入口使用英文 `SKILL.md`，`.zh-CN.md` 为配对译文。
- `AGENTS.md` 保持简短并面向任务。能力范围与引用记录在 `catalog/`，结构事实保留在 Schema，行为通过接口文档解释。索引修改用离线工具测试校验，未知版本与路由不能变成隐含支持。
- 每份文档均维护英文和简体中文。默认文件名对应英文，中文使用 `.zh-CN.md` 后缀；在同一 PR 中同步更新，并保留语言切换和同语言文档链接。
- 使用指南应提供完整、正确的功能流程：前置条件、命令、响应、完成条件及恢复方法。测试报告与使用说明分开。
- 遵循[设备类型文档结构](docs/robots/README.zh-CN.md)：复用通用章节与硬件规格，隔离机型差异，同步发布范围和兼容矩阵，不把尚未发布的类型写成已支持。
- 保留 `foot_quadruped` 与 `wheel_quadruped` 现有的共用有线连接和传感器规格，不重复维护，也不应用到 `foot_humanoid`。其他类型单独发布并记录之前，当前 EDU 范围仍为 `foot_quadruped`。
- Schema 修改应包含构建所需依赖，并保持生成的 Python 绑定一致。
- 提供复现步骤及相关测试结果；分享问题报告时遵循[安全说明](SECURITY.zh-CN.md)。
- 运行 `python3 tests/check_repository.py`、`python3 tests/test_agent_workspace.py` 及相关 Bazel 检查；区分离线测试与实际 harness 会话、设备运行行为。
- 设备测试必须区分只读检查和控制操作；不得在普通 CI 中自动操控机器人。
- 新增或修改的在线示例发布前，必须使用文档规定的账户、SDK 配套版本、环境配置与部署步骤，在支持的机器人上验证每种公开语言实现和文档中的执行分支。仅编译、预览或离线测试不能满足发布条件。验证证据保留在评审记录中，不放入公开使用指南；未验证或仍有问题的分支不得作为可运行示例发布。

## 贡献内容的许可

除明确另行说明外，主动提交并拟纳入本项目的贡献按 [Apache-2.0](LICENSE) 第 5 条授权。
仅提交你有权贡献的内容，并保留适用的第三方许可证和署名声明，包括 [NOTICE](NOTICE) 中的声明。
