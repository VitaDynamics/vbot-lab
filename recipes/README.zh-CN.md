# Recipes

<p align="center"><a href="README.md">English</a> | 中文</p>

单项任务参考程序：Recipe 提供实现，[Skill](../skills/README.zh-CN.md) 引导开发流程，[Blueprint](../blueprints/README.zh-CN.md) 组合完整应用。

## 能力分类

| 分类 | 示例与覆盖范围 | 接口类型 |
| --- | --- | --- |
| 传感器 | [sensors](sensors/README.zh-CN.md)：电池、本体／LiDAR IMU、点云布局 | pub/sub |
| 相机 | [camera](camera/README.zh-CN.md)：H.265 元数据、保存与解码 | pub/sub |
| Perception | [perception](perception/README.zh-CN.md)：目标／人体框、人体关键点 | pub/sub |
| Audio | [audio](audio/README.zh-CN.md)：本体／UWB 音频、ASR、输入结束事件 | pub/sub |
| 运动 | [locomotion](locomotion/README.zh-CN.md)：站起／趴下；[subscribe-state](subscribe-state/README.zh-CN.md)：姿态与心跳 | service + pub/sub |
| 系统与外设 | [system-peripherals](system-peripherals/README.zh-CN.md)：系统／显示状态；[device-info](device-info/README.zh-CN.md)：固件查询；[service-call](service-call/README.zh-CN.md)：灯光状态 | service + pub/sub |
| RCP | [rcp-task](rcp-task/README.zh-CN.md)：Sleep DAG 提交、结果与取消 | action |
| SLAM | [slam](slam/README.zh-CN.md)：状态、里程计、静态变换 | pub/sub |

各分类覆盖上表所列实现，并非每条公开路由都有独立示例。SLAM 读取不切换模式；
主动建图、保存与定位按[建图流程](../docs/guides/mapping-localization.zh-CN.md)执行。现有辅助示例入口继续保留。

这些入口已有 Python／C++ 源码与 Bazel 目标。适配四足 EDU 的机器人应用版本 **V1.6.0**，SDK 配套为 edu-sdk-2026.9.24；安装步骤见 [客户端开发库](../packages/README.zh-CN.md)及 [Python SDK](../packages/aorta/python/README.zh-CN.md)。SDK 可导入、代码可构建不代表设备接口已就绪；先检查目标固件的路由与类型。

## Python 运行流程

先构建与离线预览，再 SSH 登录设备、配置 shell 和配套 ARM64 venv，最后按各 Recipe 的前提运行。默认不执行；只有显式传入 --execute 才建立设备会话。以下命令从仓库根目录运行，不连接设备：

```bash
bazel build //recipes/...
bazel run //recipes/subscribe-state:main
bazel run //recipes/locomotion:main -- --mode stand
bazel run //recipes/rcp-task:main
bazel test //tests:recipe_test
```

在线读取也需要 --execute；运控额外要求 --confirm-motion，语音以及图像保存／解码需要 --consent。Bazel 默认 Python 工具链从 PATH 选择 python3，运行前激活已安装 wheel 的 venv；按 [Python 部署流程](../docs/development/python-deployment.zh-CN.md)传输所选源码与 wheelhouse，并创建设备 venv；随后从该应用目录执行 python -m recipes.<目录>.main，不要求设备具有仓库或安装 Bazel。完整命令见对应页面。

日志为 JSON Lines，错误写入 stderr。预览只描述请求，不代表已获取数据或执行动作。订阅有数量、时间和队列上限；不自动重试写操作。

## 验证和扩展

默认测试检查离线预览、参数、安全条件、资源释放、超时与关联规则，不安装 SDK、不访问设备。另有显式发布版 SDK 测试，检查真实生成类型与序列化：

```bash
bazel test --test_env=PATH="$PWD/.venv/bin:$PATH" //tests:recipe_sdk_test
```

SDK 安装说明包含版本配套。扩展程序时从 [Schema](../schemas/README.zh-CN.md)确定字段与类型，从 [能力索引](../catalog/README.zh-CN.md)查找行为契约；不要把 service 受理或 action 取消受理当作终态完成。

## C++ 运行流程

每项任务同时提供 [C++ SDK](../packages/aorta/cpp/README.zh-CN.md) 实现，源码为同目录的 `main.cc`，目标为 `:main_cpp`。
安装对应架构 SDK 与 Schema 制品，设置指南中的两个目录变量后，显式构建并预览：

```bash
bazel build //recipes/camera:main_cpp //recipes/audio:main_cpp //recipes/locomotion:main_cpp //recipes/rcp-task:main_cpp
bazel run //recipes/locomotion:main_cpp -- --mode stand
bazel test //tests:recipe_cpp_test //tests:recipe_cpp_sdk_test
```

基础 C++ 目标均标记为 manual，不随普通 `//recipes/...` 通配构建隐式引入 SDK 依赖。
基础相机目标读取／保存 H.265；额外的 `:main_cpp_decode` 在安装 FFmpeg 开发依赖后解码 RGB。
C++ 预览需要编译与动态链接，但不会连接设备。设备在线运行需完成 SSH 登录、shell 配置，并使用 ARM64 可执行文件及匹配运行库。
