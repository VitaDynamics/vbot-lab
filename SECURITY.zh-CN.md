# 安全说明

<p align="center"><a href="SECURITY.md">English</a> | 中文</p>

请勿在公开 Issue、PR、日志或示例中提交凭据、私钥或可用于攻击设备的信息。

## 报告安全漏洞

请通过 [vbot-edu@vbot.cn](mailto:vbot-edu@vbot.cn) 私下提交安全问题。
不要在公开 Issue、PR 或社区论坛发布漏洞细节和利用步骤。

请说明受影响的组件及版本、潜在影响，以及能安全执行的最小复现步骤。
仅提供必要的脱敏日志片段，不附带密码、令牌、私钥、设备会话文件或个人信息。
不要为了收集证据重复危险的机器人操作。公开披露前，请通过同一邮箱与维护者协调。

一般配置或开发问题请使用[社区与支持](docs/community/README.zh-CN.md)。
本项目由仓库管理员共同维护，评审负责人见 [CODEOWNERS](.github/CODEOWNERS)。

## 开发边界

开发容器是工作站环境，不是机器人权限隔离方案。设备开发使用 `vbot` 账户，
不能通过 SDK、示例或 Skill 开放系统管理权限。

现有镜像的隔离开发边界及 SSH 注意事项见[容器说明](docker/README.zh-CN.md)。
仓库检查不能替代应用及部署环境的安全测试。
