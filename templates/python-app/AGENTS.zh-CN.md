# 应用指令

<p align="center"><a href="AGENTS.md">English</a> | 中文</p>

这是独立用户应用，修改前阅读 README.md 和 APP.json。
业务规则放在 health_monitor/model.py，设备订阅和解码放在 runtime.py。
构建、测试、模拟和打包均在 VBOT 开发容器内执行，优先复用配套的已有容器；
仅清点可在宿主机或 CI 执行。默认执行为预览。
设备执行需明确目标机器人、vbot shell、配套 SDK／应用版本及显式 --execute，不将设备访问加入测试。
当前应用只观察数据；新增控制或采集需要单独的用户意图及接口安全前提。
区分未收到数据与接口不支持，保留用户文件和 Agent 配置。
不因测试业务逻辑而部署、配置自启动、安装密钥或发布反馈。
修改运行文件时更新 APP.json；打包与部署分开。
