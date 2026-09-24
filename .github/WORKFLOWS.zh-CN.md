# CI 与仓库协作说明

<p align="center"><a href="WORKFLOWS.md">English</a> | 中文</p>

当前工作流在 GitHub 托管运行器执行无网络、无设备操作的仓库内容与离线 Agent 工作区检查。
检出代码由 GitHub Actions 完成；检查脚本本身不请求网络。

检查双语文档、Codex／Claude Code 的相对 Skill 链接、能力索引决策、本地环境工具行为，
以及不依赖 SDK 的 Recipe 预览和安全前提，不启动模型会话或建立 Aorta 会话。

当前工作流尚不包含依赖构建和 SDK 测试。
