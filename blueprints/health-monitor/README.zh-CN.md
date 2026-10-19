# 只读健康监测

<p align="center"><a href="README.md">English</a> | 中文</p>

这是组合[运动状态](../../docs/interfaces/locomotion.zh-CN.md)、[电池数据](../../docs/interfaces/sensors.zh-CN.md)
与[系统状态](../../docs/interfaces/system-peripherals.zh-CN.md)的完整 Python／C++ 应用。
它报告数据新鲜度和可配置的低电量提示，不判断物理安全或硬件健康。
不发送运动、service 或 RCP 指令，也不采集音视频。
配套 foot_quadruped 应用 V1.6.0-12 与 SDK Release edu-sdk-2026.10.14。

## 开发——容器

下面是 Python 命令。C++ SDK 构建、测试、ARM64 打包和设备运行见 [C++ 实现](cpp/README.zh-CN.md)。
两种语言共用 config.json，监测相同数据流。

```bash
bazel build //blueprints/health-monitor:main &&
bazel test //blueprints/health-monitor:model_test &&
bazel run //blueprints/health-monitor:main &&
bazel run //blueprints/health-monitor:main -- --simulate
```

预览、模拟及模型测试不需要 SDK。合成数据测试覆盖无输入、断流过期、重复／乱序消息、
异常值、低电量和恢复。这是应用状态测试，不是物理仿真或传感器精度测量。

model.py 接收解码字段和传入的本地单调时钟时间，runtime.py 通过有界队列订阅三路固定只读接口，
main.py 汇总并输出 JSON Lines。缺少输入为 waiting_data，不代表能力不支持。
队列溢出或 SDK 报告丢包时停止，不静默忽略数据丢失。
新鲜度使用回调中记录并随消息入队的单调时间，之后出队／解码不会刷新旧样本。
源时间戳只用于单路消息排序；时间戳重置后需重新启动这个有界程序。
新鲜度不等于采集到接收的延迟；源时间戳为零时，该流不做时间戳排序。
Python 解码前，wire.py 根据三路配套 SDK 的 BFBS Schema 检查边界、表、字符串、向量及内联结构体。
坏包增加 invalid，不刷新上次有效样本；合法的零值／默认字段仍被允许。
检查限制为单包 1 MiB、64 层嵌套及 65,536 个对象。这是结构校验，不验证数据来源身份，
也不证明硬件健康。预览和模拟仍无需 SDK 或额外的原生校验库。

config.json 支持 stale_after_seconds，范围 (0, 120]，以及 low_battery_percent，范围 [0, 100]。
`--config` 选择文件，`--duration` 将在线运行限制在 (0, 120] 秒，默认 10 秒。
退出及清理说明见[独立工作区指南](../../templates/python-app/README.zh-CN.md)。

Python 失败时在 stderr 输出脱敏 JSON，包含 stage、error_code 与 next_step。
配置错误会在 SDK／设备访问前停止；按错误码选择对应检查，不将所有失败都归因于连接问题。
说明见[应用错误](../../docs/troubleshooting/README.zh-CN.md#application-errors)。

## 创建自己的 Python 应用

在开发容器的 VBOT Lab 根目录执行：

```bash
python3 tools/create_app.py --name my-monitor --output /tmp/my-monitor
```

新工作区包含源码、配置、测试、Bazel 文件、APP.json 运行文件清单、固定依赖及许可证。
不覆盖已有目录；可选新路径，或自行复用已有应用。创建过程不安装 SDK 或部署。
生成的项目无需依赖参考仓库即可构建不依赖 SDK 的逻辑，部署后的程序同样独立。
打包仍使用参考仓库工具和已校验的发布制品。
实际开发时选择容器／宿主机挂载可见的输出路径。

按[工作区指南](../../templates/python-app/README.zh-CN.md)打包并安装应用。
此处部署包为 application.tar.gz，不是 Recipe 专用的 python-recipe.tar.gz；完整保留包内文件。
[快速开始](../../docs/getting-started/README.zh-CN.md)说明免密 SSH 与新应用目录的创建方式，不覆盖已有应用。
本应用只用 SDK 基础依赖，设备不需要仓库或 Bazel。
Ctrl+C 或时长到期即可停止；没有配置守护、自恢复或开机自启动。

## 创建自己的 C++ 应用

在开发容器的 VBOT Lab 根目录执行，另选新的输出目录：

```bash
python3 tools/create_app.py --language cpp --name my-cpp-monitor --output /tmp/my-cpp-monitor
```

新工作区包含 C++ 源码／模型／解码测试、CLI 测试、共用辅助代码、本地 SDK 接入规则、
ARM64 工具链、配置、许可证及中英双语 README／AGENTS。
不再依赖本仓库的源码或 Bazel 标签。SDK 制品保持外置：原生测试／预览使用原生 SDK，
交叉构建使用 ARM64 SDK。
按 [C++ 工作区指南](../../templates/cpp-app/README.zh-CN.md)打包可执行文件／运行库，
并以 vbot 运行，不使用 Python 的 package_app.py。
生成器的范围与文件说明见[应用模板](../../templates/README.zh-CN.md)。

遇到问题时按[分层诊断指南](../../docs/development/diagnostics.zh-CN.md)检查。
