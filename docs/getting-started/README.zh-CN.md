# 快速开始

<p align="center"><a href="README.md">English</a> | 中文</p>

本章是工作站环境搭建的通用说明。连接设备前，请选择对应的
[设备类型指南](../robots/README.zh-CN.md)，并核对[兼容矩阵](../../release/compatibility.zh-CN.md)。
当前 EDU 发布范围仅为 `foot_quadruped`，容器可以启动不代表其他类型已获支持。

## 先了解机器人模型（可选）

连接设备前，可用 [Vbot Viewer](../guides/vbot-viewer.zh-CN.md) 在浏览器中查看 EDU 模型、
关节轴与连杆结构。此步骤可选，不需要 SSH、Docker 或 SDK，也不会控制机器人。

## 先做本地检查

Codex 或 Claude Code 用户可按 [Agent 快速开始](../agents/README.zh-CN.md)操作。
不使用 harness 时，在仓库根目录运行 `python3 tools/check_environment.py --profile host`。
在现有开发容器内改用 `--profile container`；检查器不安装软件、不访问 Docker，也不联系设备。

## 环境启动配置与仓库检查

```bash
git clone https://github.com/VitaDynamics/vbot-lab.git
cd vbot-lab
docker compose -f docker/compose.yaml pull
docker compose -f docker/compose.yaml run --rm dev
```

如果 GitHub 提示登录，请使用有权访问本仓库的账户。当前版本的镜像可用性尚未验证。
进入容器后可运行 README 中的仓库检查；详情见[容器说明](../../docker/README.zh-CN.md)。

## 连接机器人

四足与四轮机器狗共用[有线连接与 SSH 登录指南](../robots/quadruped-common/connection.zh-CN.md)。
指南包含 USB-C 转网口连接、电脑 IPv4 配置及 `vbot` 账户登录步骤。
网卡设置与 SSH 登录均在电脑上、开发容器外完成；其他设备类型请先核对其专属指南。
当前 EDU 发布范围仍仅为 `foot_quadruped`。

## 配置并检查设备 shell

SSH 登录后，按[设备环境配置](device-environment.zh-CN.md)加载 `vbot` Bash 环境、
保存到 `.bashrc`，并分别检查 Aorta／ROS 2 访问。这些设备 CLI 检查不依赖 Python SDK 安装。
Aorta 是原生入口；ROS 2 是设备本机[兼容子集](../interfaces/aorta-ros2.zh-CN.md)。

## 构建并运行 Python 示例

1. 按 [Python SDK 指南](../../packages/aorta/python/README.zh-CN.md)在工作站环境安装配套的发布版 wheel。
2. 用 Bazel 构建并预览 [Recipe](../../recipes/README.zh-CN.md)，预览不连接机器人。
3. 确认所选固件提供所需路由，然后以 vbot 身份 [SSH 登录设备](../robots/quadruped-common/connection.zh-CN.md)。
4. 按 [Python 部署流程](../development/python-deployment.zh-CN.md)传输所选示例与 ARM64 wheel，在设备创建 venv 并配置 shell。设备默认没有仓库，不要复制工作站原生库。
5. 显式传入 --execute 运行[只读状态订阅](../../recipes/subscribe-state/README.zh-CN.md)，确认实际样本后再加入控制操作。
6. service/action 操作遵循对应 Recipe 的前提、完成检查和停止方式；交互运行正常后再配置[自启动](../guides/user-autostart.zh-CN.md)。

C++ 开发可选择同一 Recipe 的 `:main_cpp` 目标，使用 [C++ SDK 安装与部署流程](../../packages/aorta/cpp/README.zh-CN.md)，
替代上面的 Python wheel／venv 步骤。SSH 登录、设备 shell 和操作前提不变。
