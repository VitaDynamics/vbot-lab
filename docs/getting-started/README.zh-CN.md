# 快速开始

<p align="center"><a href="README.md">English</a> | 中文</p>

本章是工作站环境搭建的通用说明。连接设备前，请选择对应的
[设备类型指南](../robots/README.zh-CN.md)，并核对[兼容矩阵](../compatibility.zh-CN.md)。
当前 EDU 发布范围仅为 `foot_quadruped`，容器可以启动不代表其他类型已获支持。

## 先了解机器人模型（可选）

连接设备前，可用 [Vbot Viewer](../guides/vbot-viewer.zh-CN.md) 在浏览器中查看 EDU 模型、
关节轴与连杆结构。此步骤可选，不需要 SSH、Docker 或 SDK，也不会控制机器人。

## 选择配套源码

机器人应用版本 `V1.6.0-10` 使用源码快照 tag `V1.6.0.10`。
SDK 制品使用独立的 `edu-sdk-2026.10.14` Release。
在宿主机克隆仓库，再切换到配套的源码版本：

```bash
git clone https://github.com/VitaDynamics/vbot-lab.git
cd vbot-lab
git checkout V1.6.0.10
```

已有仓库时直接复用并切换到同一个 tag，不重复克隆。
本地缺少该 tag 时，先运行 `git fetch origin tag V1.6.0.10`。

切换到 tag 后会进入 detached HEAD 状态，这是阅读、构建或运行版本快照时的正常状态。
如果需要在该仓库中修改代码，先创建工作分支；分支名已存在时换一个名称：

```bash
git switch -c my-edu-app
```

选择其他源码 tag 时，按[兼容矩阵](../compatibility.zh-CN.md)使用其配套的机器人应用和 SDK 版本。

## 先做本地检查

Codex 或 Claude Code 用户可按 [Agent 快速开始](../agents/README.zh-CN.md)操作。
不使用 harness 时，在仓库根目录运行 `python3 tools/check_environment.py --profile host`。
在现有开发容器内改用 `--profile container`；检查器不安装软件、不访问 Docker，也不联系设备。

## 进入开发容器

按[容器指南](../../docker/README.zh-CN.md)检查 Docker，并寻找使用提供的镜像、
挂载当前仓库的容器。匹配的容器正在运行时直接进入；已停止时启动同一个容器。
只有没有合适容器时才拉取镜像并创建容器。开发镜像支持匿名拉取，无需注册表登录。

SDK 准备、Bazel 构建与打包均在该容器内执行，不在宿主机 shell 执行。
使用默认工作区挂载时：

```bash
cd /workspace
python3 tools/check_environment.py --profile container
python3 --version
bazel --version
uname -m
```

需要 Python 3.10+ 与 Bazel 7.6.1。按 SDK 指南准备所选源码版本要求的 SDK，
不要假设镜像已经包含配套 SDK。
x86_64 容器可准备 Python 源码及 ARM64 wheel，但原生 C++ 部署需 ARM64 容器与编译器；
参见 [C++ 指南](../../packages/aorta/cpp/README.zh-CN.md)。

## 连接机器人

四足与四轮机器狗共用[有线／Wi-Fi 连接与 SSH 登录指南](../robots/quadruped-common/connection.zh-CN.md)。
无线方式先通过手机 App 配网，再从路由器设备列表查询 IP，并以 `vbot` 账户 SSH 登录该 IP。
有线方式包含 USB-C 转网口连接及电脑手动 IPv4 配置。
网卡设置与 SSH 登录均在电脑上、开发容器外完成；其他设备类型请先核对其专属指南。
当前 EDU 发布范围仍仅为 `foot_quadruped`。

## 配置并检查设备 shell

SSH 登录后，按[设备环境配置](device-environment.zh-CN.md)加载 `vbot` Bash 环境、
保存到 `.bashrc`，并分别检查 Aorta／ROS 2 访问。这些设备 CLI 检查不依赖 Python SDK 安装。
Aorta 是原生入口；ROS 2 是设备本机[兼容子集](../interfaces/aorta-ros2.zh-CN.md)。

## 构建并运行 Python 示例

1. 在开发容器内，按 [Python SDK 指南](../../packages/aorta/python/README.zh-CN.md)将四个配套的发布版 wheel 安装到专用 venv。
2. 在该容器内用 Bazel 构建并预览 [Recipe](../../recipes/README.zh-CN.md)，预览不连接机器人。
3. 确认所选固件提供所需路由，然后以 vbot 身份 [SSH 登录设备](../robots/quadruped-common/connection.zh-CN.md)。
4. 按 [Python 部署流程](../development/python-deployment.zh-CN.md)传输所选示例与 ARM64 wheel，在设备创建 venv 并配置 shell。设备默认没有仓库，不要复制工作站原生库。
5. 显式传入 --execute 运行[只读状态订阅](../../recipes/subscribe-state/README.zh-CN.md)，确认实际样本后再加入控制操作。
6. service/action 操作遵循对应 Recipe 的前提、完成检查和停止方式；交互运行正常后再配置[自启动](../guides/user-autostart.zh-CN.md)。

C++ 开发可选择同一 Recipe 的 `:main_cpp` 目标，使用 [C++ SDK 安装与部署流程](../../packages/aorta/cpp/README.zh-CN.md)，
替代上面的 Python wheel／venv 步骤。SSH 登录、设备 shell 和操作前提不变。
