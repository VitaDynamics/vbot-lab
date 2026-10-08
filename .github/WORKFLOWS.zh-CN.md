# CI 与仓库协作说明

<p align="center"><a href="WORKFLOWS.md">English</a> | 中文</p>

当前工作流在 GitHub 托管运行器执行无网络、无设备操作的仓库内容与离线 Agent 工作区检查。
检出代码由 GitHub Actions 完成；检查脚本本身不请求网络。

检查双语文档、Codex／Claude Code 的相对 Skill 链接、能力索引决策、本地环境工具行为，
以及不依赖 SDK 的 Recipe 预览和安全前提，不启动模型会话或建立 Aorta 会话。

当前工作流尚不包含依赖构建和 SDK 测试。

## 提交 PR 前

在仓库根目录运行相同的离线检查：

```bash
python3 tests/check_repository.py
python3 tests/check_schemas.py
python3 tests/test_agent_workspace.py
python3 tests/test_recipes.py
python3 tests/test_family_recipes.py
python3 tests/test_offline_build.py
```

按[贡献说明](../CONTRIBUTING.zh-CN.md)，在 PR 中附上检查结果及相关构建或设备验证情况。
新建 Issue 时使用问题报告或文档改进模板；一般使用问题优先到
[社区与支持](../docs/community/README.zh-CN.md)交流。

## 评审与合并

1. 在工作分支修改，并向 `main` 提交 PR。
2. 由 [CODEOWNERS](CODEOWNERS) 列出的另一位维护者批准。
   新的待评审提交会使此前批准失效；最后一次推送的变更须由推送者之外的人批准。
3. 解决评审讨论，确保 GitHub Actions 的 `repository-layout` 检查在当前 `main` 基础上通过。
   目标分支有新提交时，更新工作分支。
4. 使用 **Squash and merge**。禁止直接推送、强推或删除 `main`，管理员也未配置绕过权限。

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
