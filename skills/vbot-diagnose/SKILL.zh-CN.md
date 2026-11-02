---
name: vbot-diagnose
description: 通过显式只读分层检查及脱敏摘要，排查已有 VBOT 应用的环境、SDK 导入／链接或遥测无数据问题。用于故障诊断，不自动修复、部署、运动或采集。
---

# 排查 VBOT 应用

<p align="center"><a href="SKILL.md">English</a> | 中文</p>

先解析 Skill 物理目录，定位对应 VBOT Lab 仓库，即使它通过其他项目中的软链接发现。
确认对应 tools/diagnose.py 存在，不执行用户应用目录中的同名文件；仓库不完整时请求其位置。

## 缩小故障范围

根据已有证据确定实际命令／错误、执行位置、Python/C++、已知版本配套及所选路由／设备。
仅询问下一步确实需要的信息。从[症状索引](../../docs/troubleshooting/README.zh-CN.md)
和[分层诊断](../../docs/development/diagnostics.zh-CN.md)定位，不扫描所有接口。
只读检查相关源码与配置，不展示凭据或会话文件。

## 显式选择一个诊断层级

- 本地工具：tools/diagnose.py --level inventory 不连接设备、不安装、不检查 Docker，
  不导入 SDK，也不能证明应用环境已就绪。
- Python SDK：在开发容器中用应用选定的 venv 执行 --level sdk。
  区分包版本、原生库来源、ABI 与设备通信。
- C++ SDK／链接：按诊断指南 C++ 章节核对原生／ARM64 制品与编译目标。
  缺少 Python wheel 不等于 C++ 故障，不安装 wheel 修复 C++，不在宿主机对 ARM64 二进制执行 ldd。
- 设备 shell：仅在请求设备检查时使用所选连接及文档中的 vbot shell。
  传输 diagnose.py 是独立写入步骤，未覆盖时先取得对应范围。
  --level device --allow-device-check 只检查 shell 前提，不确认接口支持或机器人应用版本。
- 单路采样：仅在请求采样时选择 state/battery/system 之一，显式执行
  --level sample --allow-device-check 并限定 --timeout；Python 需要应用 venv。
  C++ 诊断路径改用文档中的有时限设备 Aorta CLI 采样。

某一层不授权下一层。遵循[执行位置](../../docs/development/README.zh-CN.md)，
SDK／构建复用所选开发容器。SSH 不可达就停止，请用户连接设备或提供实际地址，
不扫描或更换设备。认证、主机密钥错误与不可达分开处理，不绕过身份核验或内嵌密码。

## 解释与交接

区分 confirmed_missing、mismatch、not_verified 与 waiting_data_timeout。
超时不等于固件不支持、ACL 拒绝、生产者停止或硬件故障。
sample_received 仅说明收到字节，不保证解码或新鲜度；本地订阅也不证明远端生产者存在。
保留采样与清理失败，说明到达的实际阶段。

给出观察结果、仍未知的部分及最小的后续检查。
不自动重启服务、修改权限／配额／模式、重装依赖、发布控制或采集音视频。
纯诊断请求不授权修复。分享前检查最小 JSON 摘要，去掉原始异常、主机、会话和凭据信息。
可协助准备经用户审阅的[社区反馈](../../docs/community/README.zh-CN.md)，不自动发布。
