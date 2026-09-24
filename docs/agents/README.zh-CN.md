# 与 Agent 开始开发

<p align="center"><a href="README.md">English</a> | 中文</p>

在 Codex 或 Claude Code 中配置 Skills，从本仓库或自己的项目中运行开发任务。
首个流程是本地环境清点，不是自动部署机器人。

## 在 VBOT Lab 内工作

使用保留软链接的 Git 工作副本。开发容器及 Linux／WSL 工作区适合这一文件系统要求；
复制仓库或解压归档后需要验证链接。内容仅为 `../skills` 的普通文本文件不是可用软链接。

| Coding Agent | 项目指令 | Skill 发现入口 | 显式调用 |
| --- | --- | --- | --- |
| Codex | `AGENTS.md` | `.agents/skills/` → `../skills` | `$vbot-dev-setup` |
| Claude Code | `CLAUDE.md` 导入 `AGENTS.md` | `.claude/skills/` → `../skills` | `/vbot-dev-setup` |

仅将 `skills/<name>/SKILL.md` 作为发现来源维护；`.zh-CN.md` 是供人阅读的译文，
不是另一份已安装 Skill。不要在不同 harness 目录分别维护不同指令。

在 Agent 中打开仓库，请它检查开发环境，不安装软件、不连接机器人。
确认 harness 的 Skill 选择器中出现 `vbot-dev-setup`。
如果没有，检查软链接、项目信任与配置，并在仓库内重启会话。
具体行为见官方 [Codex Skill 指南](https://learn.chatgpt.com/docs/build-skills)、
[Claude Code Skill 指南](https://code.claude.com/docs/zh-CN/skills)
及 [Claude 项目指令指南](https://code.claude.com/docs/zh-CN/memory)。
其他 Agent 请按其 Skill 发现机制配置，并在调用前确认 Skill 已出现。

仓库检查验证链接目标及内容一致性，不证明某个 harness 版本已经加载 Skill。
请在全新会话执行[工作流检查](../../tests/agent-scenarios/README.zh-CN.md)，单独记录 harness 与版本。

## 在自己的应用仓库中工作

在 Agent 所在文件系统保留完整、固定版本的 VBOT Lab 工作副本。
将其中单独的 `vbot-dev-setup` 目录链接到应用仓库的 `.agents/skills/` 和／或 `.claude/skills/`，
不要替换这两个目录。保留其他 Skills，遇到同名条目时停止，不覆盖。

被链接的 Skill 解析实际位置后，使用同一版本的能力索引、工具与文档。
不要只复制 `SKILL.md`，否则这些资源会丢失。应用输出放在自己的工作区，
不应仅为开发应用而修改参考仓库。
这一方式要求能访问完整仓库，不是独立插件；可移植的插件分发仍处于规划阶段。
不要用 VBOT Lab 的仓库指令覆盖应用中已有的 `AGENTS.md` 或 `CLAUDE.md`。

## 配置设备环境

先按[连接指南](../robots/quadruped-common/connection.zh-CN.md)配置 SSH 公钥免密登录，
已有配置则验证并复用。开始后续设备任务前，从实际执行命令的环境确认非交互登录成功。
设备不可达时，先连接设备或提供实际 IP。

可请同一 Skill 在不连接设备的前提下说明 [vbot shell 配置](../getting-started/device-environment.zh-CN.md)，
或明确请求对指定设备配置／检查。它区分工作站、容器与设备 shell，将 `.bashrc` 修改与只读清点分开。
在线检查只使用有时限的发现和单条数据订阅，不发送控制命令。
[Aorta／ROS 2 参考](../interfaces/aorta-ros2.zh-CN.md)列出可用接口及其映射。

## 按任务开展开发

1. 通过 [Skills](../../skills/README.zh-CN.md)选择相关流程。
2. 查询[能力索引](../../catalog/README.zh-CN.md)，获得设备范围与参考资料。
3. 阅读所选接口、SDK 与 [Recipe](../../recipes/README.zh-CN.md)，不必加载所有文档。
4. 仅执行确实可用的构建／测试入口，报告实际结果和剩余阻塞。

SDK 开发流程覆盖 Python 和 C++；设备 Recipes 已有可执行代码，Blueprints 仍处于规划阶段。
设备端 Skills 与 AGENTS.md 属于独立的[内容 API](../interfaces/agent/content-api.zh-CN.md)，
不是这些 Coding Agent 发现目录。本地检查不赋予机器人控制权限。
