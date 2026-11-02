---
name: vbot-app-dev
description: 使用能力索引与独立项目模板开发或扩展 Python/C++ VBOT 应用。用于应用开发，不用于设备端 Skill 注入或单纯环境清点。
---

# 开发 VBOT 应用

<p align="center"><a href="SKILL.md">English</a> | 中文</p>

## 定位参考仓库

先解析本文件的物理路径。即使从其他项目通过软链接发现，skills/vbot-app-dev 所在位置
也属于 VBOT Lab。确认对应 tools/create_app.py 与 catalog/capabilities.json 存在；
若缺失则请求完整仓库位置。应用修改放在用户项目中，不修改参考仓库。
保留已有 AGENTS.md、CLAUDE.md、Skills 与源码，不覆盖已有目录重新生成。

## 选择开发路径

沿用用户语言与现有项目；未指定时说明先采用 Python，不将现有 C++ 应用改为 Python，
也不默认执行两种语言流程。明确目标行为、所需数据流、输出影响、完成条件与停止方式。
从[能力索引](../../catalog/README.zh-CN.md)定位，只读取选中接口与 SDK 指南。
支持的能力和参数来自这些参考，不猜测 API 名称。

新项目使用[模板](../../templates/README.zh-CN.md)及 tools/create_app.py，
指定 --language python 或 cpp 和新的应用目录。它复制的是
[健康监测应用](../../blueprints/health-monitor/README.zh-CN.md)，不会自动生成任意机器人行为；
需要按任务修改业务规则。已有项目保留布局，仅选用相关接口与辅助逻辑。

## 先完成本地开发，再部署

遵循[执行位置](../../docs/development/README.zh-CN.md)，复用已选开发容器。
环境未就绪时使用 [vbot-dev-setup](../vbot-dev-setup/SKILL.zh-CN.md) 的环境流程。
不退回宿主机／设备构建，也不因容器运行在 AMD64 就再创建容器。
C++ 设备构建使用镜像提供的 ARM64 工具链与对应 SDK，原生预览／测试使用原生 SDK。

分离 SDK 传输与业务状态，保留有界等待／队列、回调接收时间、无效数据处理、停止和清理。

按项目 README 构建、测试、预览，再根据需要打包；Python 使用 wheel，C++ 部署二进制与库。
打包不等于部署。没有覆盖相应操作的请求时，不 SSH、安装、配置自启动、采集传感器或下发控制。
经授权的实机操作使用所选设备／账户与文档前提；新增或修改的实机示例在发布前需要设备验证。

## 交付

说明修改文件、实际构建／测试结果、需要时生成的本地包及尚待执行的部署／设备步骤。
不把离线测试成功描述为实机成功。排查已有故障时使用
[vbot-diagnose](../vbot-diagnose/SKILL.zh-CN.md) 与
[排障入口](../../docs/troubleshooting/README.zh-CN.md)，不扩展用户任务。
