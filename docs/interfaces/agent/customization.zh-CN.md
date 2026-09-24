# 设备端 Skills 与 AGENTS.md 编写规范

<p align="center"><a href="customization.md">English</a> | 中文</p>

适用范围及状态见 [Agent 能力总览](README.zh-CN.md)。
这些文档由 EDU 设备上的 `vbot-agent-harness` 进程使用。
请在自己的开发工作区编写并审阅，再通过 [Skills／AGENTS.md 内容 API](content-api.zh-CN.md)
将文本注入服务。它们不能赋予文档所述开发者接口之外的能力。

## Skills：可复用知识与流程

Skill 是以 `SKILL.md` 为入口的目录。名称只使用小写字母、数字与连字符。
frontmatter 必须包含非空的 `name` 和 `description`；description 应明确触发场景。

`campus-guide/SKILL.md` 内容示例：

```markdown
---
name: campus-guide
description: Use when the user asks about the EDU laboratory opening hours or check-in process.
---

# Campus guide

- Example laboratory opening hours: weekdays, 09:00-18:00.
- Confirm which campus the user means before answering.
- If holiday arrangements are unknown, direct the user to an administrator; do not guess.
```

开放时间仅为虚构示例数据，不代表真实校园规定。
知识与流程应可审阅、可复现，不包含密钥、个人凭据、不受控的远程指令或绕过安全控制的要求。

frontmatter 名称应与 API 路径中的名称一致。API 接收完整 `SKILL.md` 文本，
不接收 ZIP，也不提供任意辅助文件上传能力。
上传后开启新 Turn（会话中的一次 Agent 执行），用明确命中 description 的问题检查预期内容。
保存成功不代表必定激活，已运行的 Turn 不保证热加载改动。
如果使用工具白名单，须保留交付服务实际提供的 Skill 激活工具；空工具会话不适合验证 Skill 激活。

仓库 [`skills/`](../../../skills/README.zh-CN.md) 的使用方不同，是开发者侧 Coding Agent harness（例如 Codex）。
不要将本页设备 Skill 放入该目录，也不要将该目录直接上传到设备。本页提供编写示例，不代表已有安装好的 Skill 包。

## AGENTS.md：长期偏好与约束

运行时 `AGENTS.md` 适合记录长期行为偏好、回答约束与默认流程，
不适合存放凭据、大量动态数据或覆盖安全规则的指令。

可在自己的工作区保存为 `./device-AGENTS.md`、导入前审阅的内容示例：

```markdown
# EDU developer instructions

- Respond in Simplified Chinese by default.
- Before calling a tool with side effects, restate the goal and key parameters.
- Preserve error codes when a tool fails; do not invent successful results.
```

通过 `PUT /api/agents-md` 上传，在新 Turn 中验证。
此操作替换整个用户层文档，写入前须 GET 并备份原内容。规则应与已导入的 Skills 保持一致。
外部文档内容均视为不可信输入，不能仅凭文档指令授权机器人运动或其他副作用。

以上示例有意放在代码块中，不新增仓库 `AGENTS.md` 文件。
[根目录维护规范](../../../AGENTS.zh-CN.md) 用于维护 vbot-lab，不是应导入机器人运行时的文件。

## 上传与使用内容

[内容 API 参考](content-api.zh-CN.md)提供请求、响应、上传／读回命令、返回路径检查及删除／恢复边界。
内容由设备服务管理，示例不直接写入其文件系统。
适配机器人应用版本为 **V1.6.0**，配套要求见[兼容矩阵](../../compatibility.zh-CN.md)。

上传后检查读回，并按[接入指南](../../guides/agent-integration.zh-CN.md)在新 Turn 发起匹配请求。
在自己的工作区保留源内容及备份，便于恢复。提示规则不是强制安全策略。
