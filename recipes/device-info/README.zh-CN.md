# 设备信息

<p align="center"><a href="README.md">English</a> | 中文</p>

[Recipes 索引](../README.zh-CN.md) · [Python](main.py) · [C++](main.cc)

接口: `/firmware_version/{motor,servo,lidar,uwb}` — service.

生成类型: `aorta.services.system.GetFirmwareVersionResponse`.

查询所选部件的固件版本；空 ID 数组表示查询该类全部设备。输出 service 状态及软硬件版本，不代表整机固件兼容性判断。非零状态为失败，不自动重试。

## Python：构建与离线预览

```bash
bazel build //recipes/device-info:main
bazel run //recipes/device-info:main
```

默认只输出 JSON 请求计划，不安装 SDK、不连接设备、不发送请求。

## Python：在设备上运行

先完成 [Python 部署流程](../../docs/development/python-deployment.zh-CN.md)：传输本示例及配套 wheel，并在设备创建 venv。保持位于部署所得的应用目录（APP_DIR），激活该目录的 venv、配置设备环境后运行：

```bash
python -m recipes.device-info.main --device uwb --execute
```



## C++

先按 [C++ SDK 指南](../../packages/aorta/cpp/README.zh-CN.md)准备配套 SDK／Schema 压缩包与编译环境，设置两个发布制品路径。在构建机上显式构建 C++ 目标，预览也需要链接 SDK，但不会创建 Node 或访问设备：

```bash
bazel build //recipes/device-info:main_cpp
bazel run //recipes/device-info:main_cpp
```

按[二进制部署流程](../../packages/aorta/cpp/README.zh-CN.md#在机器人上运行)设置 RECIPE=device-info 并完成部署。以 vbot 身份 SSH 登录后，进入部署所得应用目录，按流程配置 shell 和动态库路径，满足上面的任务前提后直接运行可执行文件：

```bash
./bin/device-info --device uwb --execute
```

设备无需 Bazel、编译器或仓库副本。C++ 使用与 Python 相同的路由、操作许可和完成条件；只读订阅不会发布指令。

## 完成、失败与退出

输出为逐行 JSON；退出码 0 表示完成本示例的操作（离线预览也返回 0），1 表示运行失败或超时，2 表示参数不合法，130 表示中断。检查 execute 参数和输出语义，不要把离线预览视为在线成功。所有等待都有上限；订阅队列溢出会报错，不把丢失样本当完整数据。退出时关闭订阅、客户端及 Node。

测试说明见 [Recipes](../README.zh-CN.md)；默认测试不连接或操作设备。
