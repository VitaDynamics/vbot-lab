# 常见问题

<p align="center"><a href="README.md">English</a> | 中文</p>

Aorta／ROS 2 命令缺失、topic 发现不完整或非交互 shell 失败时，先查看
[设备环境检查](../getting-started/device-environment.zh-CN.md)与[可用接口映射](../interfaces/aorta-ros2.zh-CN.md)。

接入时按以下类别记录可复现问题、检查命令与预期结果：

- 镜像拉取、容器启动、挂载和文件属主。
- Bazel 版本、依赖下载及缓存。
- Python 导入、原生库加载与架构 / ABI 不匹配。
- 设备网络、`vbot` 账户登录和 Aorta 连接。
- 接口未开放、Schema 不匹配、服务超时。
- 权限拒绝、程序退出及用户侧日志获取。

反馈问题时请附上相关软件版本、复现步骤及错误信息；分享日志前移除个人信息和访问令牌。

## 到社区获取帮助

按上述方法仍未解决时，欢迎到 [Vbot 超能社区](https://forum.vbot.cn/)提问。
按[社区与支持](../community/README.zh-CN.md)选择板块并整理简短、可复现的反馈，
注明已经尝试的方法，不上传完整配置或凭据。解决后请在原帖补充有效方法。
明确属于仓库代码／文档的缺陷仍可使用 GitHub Issues。
安全漏洞细节不公开发布，处理方式见[安全说明](../../SECURITY.zh-CN.md)。
