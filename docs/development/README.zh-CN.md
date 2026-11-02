# 开发流程

<p align="center"><a href="README.md">English</a> | 中文</p>

## 执行位置

仓库只读检查可在宿主机或 CI runner 运行。Bazel 构建与测试、Recipe 预览、SDK 执行检查、
应用打包及构建依赖准备必须在配套开发容器内完成，CI 同样遵守。
宿主机可以调用 Docker 执行这些操作，但不能回退到宿主机工具链。
设备只运行部署后的应用，不承担构建、打包或开发预览。

| 操作 | 执行位置 |
| --- | --- |
| 仓库结构、双语链接、Schema 清单、发布元数据及模拟工具策略检查 | 宿主机或 CI runner：`python3 tools/run_checks.py --scope repository` |
| 宿主机工具清点、Docker 可用性和已有容器选择 | 宿主机 |
| SDK 安装／导入检查、Bazel build/test/run、Recipe 预览及模拟应用测试 | 配套开发容器，包括 CI |
| 依赖包和应用部署包生成 | 配套开发容器 |
| SSH 和传输已准备的制品 | 已获授权且能访问选定设备的宿主机／容器 |
| 安装与显式在线运行应用 | 设备 vbot shell，遵循部署指南和操作前提 |

这里的“只读”指仓库检查，不能因为应用离线运行或使用模拟传输就归为只读检查。
检查过程中使用临时测试文件，不等于执行应用打包。
不依赖 SDK 的检查分组由 [checks.json](../../catalog/checks.json)统一维护；仅列出不会执行：

```bash
python3 tools/run_checks.py --scope repository --list
python3 tools/run_checks.py --scope recipes --list
python3 tools/run_checks.py --scope packaging --list
```

先按[容器指南](../../docker/README.zh-CN.md)检查并复用合适容器，确认镜像、工作区挂载及目标架构。
容器内的上下文检查同时要求 Linux 容器标记和 `VBOT_DEV_CONTAINER=1`；单个环境变量或
`--profile container` 都不充分。该检查用于防误操作，不是镜像认证或安全沙箱，
不证明 SDK 兼容，也不授予设备访问权限。

```bash
python3 tools/container_context.py
python3 tools/in_container.py -- bazel build //recipes/subscribe-state:main
python3 tools/in_container.py -- bazel run //recipes/subscribe-state:main
python3 tools/run_checks.py --scope recipes
python3 tools/run_checks.py --scope packaging
```

上述命令在开发容器内的仓库根目录执行，Recipe 预览不建立设备会话。
上下文不满足或容器不可用时，说明具体阻塞并停止，不在宿主机设置变量绕过检查。
该入口不会拦截任意手工命令，直接执行的命令同样必须遵守执行位置规则。

## 应用开发流程

当前设备流程面向 foot_quadruped；机型专属信息见 [设备类型指南](../robots/README.zh-CN.md)。

1. 准备或复用[开发容器](../../docker/README.zh-CN.md)，按 [Python SDK 指南](../../packages/aorta/python/README.zh-CN.md)安装与开发环境匹配的 SDK。首个示例见[快速开始](../getting-started/README.zh-CN.md)，设备部署见 [Python 部署流程](python-deployment.zh-CN.md)。
2. 通过 [能力索引](../../catalog/README.zh-CN.md)选择接口，从 [Recipes](../../recipes/README.zh-CN.md)选择程序，在容器内用 Bazel 构建、测试及离线预览。
3. 按 [共用连接指南](../robots/quadruped-common/connection.zh-CN.md)完成 SSH 登录，再配置 [设备环境](../getting-started/device-environment.zh-CN.md)。
4. 按 [Python 部署流程](python-deployment.zh-CN.md)打包并传输所选示例和 ARM64 wheel，以 vbot 身份在设备新应用目录创建 venv。先运行只读示例，再在满足安全条件后显式运行控制示例。
5. 长驻程序先交互调试，再按 [用户程序自启动](../guides/user-autostart.zh-CN.md)配置启动、日志与停用流程。

Python 源码通常无需交叉编译，但原生运行库必须匹配目标架构与 ABI。不要把工作站 venv 直接复制到设备。当前 Recipes 在线运行于设备本地，不提供工作站直连 Aorta 的路由配置；工作站构建成功不代表已建立设备连接。

完整应用可从[只读健康监测](../../blueprints/health-monitor/README.zh-CN.md)开始，生成独立工作区，
用合成数据测试业务规则，再独立打包与部署。开发入口见 [Agent 快速开始](../agents/README.zh-CN.md)，
问题定位见[分层诊断](diagnostics.zh-CN.md)。

实时查看 topic 可使用 [Foxglove 指南](../guides/foxglove.zh-CN.md)。
bridge 在设备上运行，查看端从电脑连接。

## C++ 路径

无需访问注册表的构建方式见 [离线构建指南](offline-build.zh-CN.md)。

C++ 应用按 [C++ SDK 指南](../../packages/aorta/cpp/README.zh-CN.md)准备编译器与对应架构发布制品，
无需 Python venv。选择 Recipe 的 `:main_cpp` 目标：原生 SDK／默认构建用于容器内预览及测试，
ARM64 SDK 与 `bazel build --config=arm64` 用于生成设备程序，再通过 SSH 部署这些 ARM64
可执行文件及 Aorta 动态库。相机 `:main_cpp_decode` 另需 FFmpeg；不要混用工作站与设备架构的依赖。
进入设备 shell 后再设置会话环境并显式执行；安全条件和完成语义沿用同一份 Recipe。
