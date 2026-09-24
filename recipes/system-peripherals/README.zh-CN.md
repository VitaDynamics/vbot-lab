# 系统与外设

<p align="center"><a href="README.md">English</a> | 中文</p>

[分类索引](../README.zh-CN.md) · [接口语义](../../docs/interfaces/system-peripherals.zh-CN.md) · [Python](main.py) · [C++](main.cc)

## 选择数据流

`--stream`: system → /system/sm_status; display → /display_node/status.

系统输出保留类别、流程状态、严重性、活动状态路径、时间戳与心跳。系统状态不能作为无关应用请求的完成依据。显示 data 按原始文本保留，不假设为 JSON 对象或图像。订阅不改变灯光或显示内容。已有固件查询与灯光查询示例见 [device-info](../device-info/README.zh-CN.md) 和 [service-call](../service-call/README.zh-CN.md)。

## 构建与离线预览

Python 与 C++ 使用相同参数，默认仅输出计划，不创建 Node。C++ 需要配套 SDK/Schema 才能构建和运行预览。

```bash
bazel build //recipes/system-peripherals:main //recipes/system-peripherals:main_cpp
bazel run //recipes/system-peripherals:main -- --stream system
bazel run //recipes/system-peripherals:main_cpp -- --stream system
```

## 在设备上读取

Python 先按 [Python 部署流程](../../docs/development/python-deployment.zh-CN.md)部署本示例，再以 vbot 身份从所得应用目录（APP_DIR）使用新建的 venv 运行，并配置设备环境。C++ 按[二进制部署流程](../../packages/aorta/cpp/README.zh-CN.md)准备，部署可执行文件名为 bin/system-peripherals；其应用目录与 Python 部署目录分开。

```bash
python -m recipes.system-peripherals.main --stream system --count 3 --timeout 20 --execute
```

C++：切换到已部署 C++ 二进制的应用目录，按 C++ 指南配置运行库后执行：

```bash
./bin/system-peripherals --stream system --count 3 --timeout 20 --execute
```

每次只选择一个数据流。按上方列表替换 --stream；不要为获取样本而自动重启服务或改变模式。

## 输出与退出

时间戳为零或缺失时视为未知，不能据此声称数据新鲜；连续读取三条消息也不保证来源时间持续推进。使用数据前检查时间戳、状态和有效性。

输出为 JSON Lines，保留来源 topic 与采集时间（源消息提供时）。非有限浮点数输出为 null。收到样本不等于数据有效或当前可用于控制；按接口契约检查状态、有效性及时间。超时不代表零值或无人。--count 为 1–1000，--timeout 为 (0,120] 秒且覆盖整个采样过程。队列或样本超限会报错。退出码 0 表示预览或指定数量读取完成，1 表示运行错误/超时，2 表示无效参数，130 表示中断；退出会关闭订阅和 Node。不自动重试，不发布控制消息。
