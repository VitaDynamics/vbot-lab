# 开发流程

<p align="center"><a href="README.md">English</a> | 中文</p>

当前设备流程面向 foot_quadruped；机型专属信息见 [设备类型指南](../robots/README.zh-CN.md)。

1. 准备 [开发容器](../../docker/README.zh-CN.md)，按 [Python SDK](../../packages/aorta/python/README.zh-CN.md)指南安装配套发布版 wheel。
2. 通过 [能力索引](../../catalog/README.zh-CN.md)选择接口，从 [Recipes](../../recipes/README.zh-CN.md)选择程序，在容器内用 Bazel 构建、测试及离线预览。
3. 按 [共用连接指南](../robots/quadruped-common/connection.zh-CN.md)完成 SSH 登录，再配置 [设备环境](../getting-started/device-environment.zh-CN.md)。
4. 按 [Python 部署流程](python-deployment.zh-CN.md)打包并传输所选示例和 ARM64 wheel，以 vbot 身份在设备新应用目录创建 venv。先运行只读示例，再在满足安全条件后显式运行控制示例。
5. 长驻程序先交互调试，再按 [用户程序自启动](../guides/user-autostart.zh-CN.md)配置启动、日志与停用流程。

Python 源码通常无需交叉编译，但原生运行库必须匹配目标架构与 ABI。不要把工作站 venv 直接复制到设备。当前 Recipes 在线运行于设备本地，不提供工作站直连 Aorta 的路由配置；工作站构建成功不代表已建立设备连接。

完整应用归入 [VBOT Blueprints](../../blueprints/README.zh-CN.md)，目前仍处于规划阶段。开发入口及上下文选择见 [Agent 快速开始](../agents/README.zh-CN.md)。

实时查看 topic 可使用 [Foxglove 指南](../guides/foxglove.zh-CN.md)。
bridge 在设备上运行，查看端从电脑连接。

## C++ 路径

无需访问注册表的构建方式见 [离线构建指南](offline-build.zh-CN.md)。

C++ 应用按 [C++ SDK 指南](../../packages/aorta/cpp/README.zh-CN.md)准备编译器与对应架构发布制品，
无需 Python venv。选择 Recipe 的 `:main_cpp` 目标，先在构建机预览，再通过 SSH 部署 ARM64
可执行文件及 Aorta 动态库。相机 `:main_cpp_decode` 另需 FFmpeg；不要混用工作站与设备架构的依赖。
进入设备 shell 后再设置会话环境并显式执行；安全条件和完成语义沿用同一份 Recipe。
