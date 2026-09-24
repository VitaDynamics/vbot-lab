# SLAM 数据读取

<p align="center"><a href="README.md">English</a> | 中文</p>

[分类索引](../README.zh-CN.md) · [接口语义](../../docs/guides/mapping-localization.zh-CN.md) · [Python](main.py) · [C++](main.cc)

## 选择数据流

`--stream`: status → /slam/status; odometry → /odometry; transforms → /slam/static_transforms.

解释里程计前先读状态。位置和姿态同时存在时才输出位姿，否则输出 null。主位姿与 body_in_map、head_in_body 分开输出。单位为米，四元数顺序为 x/y/z/w。原点变化后需先变换到同一参考系；map 名称本身不代表持久地图原点。静态变换周期发布。上述命令不开始建图、不保存或覆盖地图、不重置里程计，也不移动机器人。主动模式切换按所链接的建图指南进行。

## 构建与离线预览

Python 与 C++ 使用相同参数，默认仅输出计划，不创建 Node。C++ 需要配套 SDK/Schema 才能构建和运行预览。

```bash
bazel build //recipes/slam:main //recipes/slam:main_cpp
bazel run //recipes/slam:main -- --stream status
bazel run //recipes/slam:main_cpp -- --stream status
```

## 在设备上读取

Python 先按 [Python 部署流程](../../docs/development/python-deployment.zh-CN.md)部署本示例，再以 vbot 身份从所得应用目录（APP_DIR）使用新建的 venv 运行，并配置设备环境。C++ 按[二进制部署流程](../../packages/aorta/cpp/README.zh-CN.md)准备，部署可执行文件名为 bin/slam；其应用目录与 Python 部署目录分开。

```bash
python -m recipes.slam.main --stream status --count 3 --timeout 20 --execute
```

C++：切换到已部署 C++ 二进制的应用目录，按 C++ 指南配置运行库后执行：

```bash
./bin/slam --stream status --count 3 --timeout 20 --execute
```

每次只选择一个数据流。按上方列表替换 --stream；不要为获取样本而自动重启服务或改变模式。

## 输出与退出

时间戳为零或缺失时视为未知，不能据此声称数据新鲜；连续读取三条消息也不保证来源时间持续推进。使用数据前检查时间戳、状态和有效性。

输出为 JSON Lines，保留来源 topic 与采集时间（源消息提供时）。非有限浮点数输出为 null。收到样本不等于数据有效或当前可用于控制；按接口契约检查状态、有效性及时间。超时不代表零值或无人。--count 为 1–1000，--timeout 为 (0,120] 秒且覆盖整个采样过程。队列或样本超限会报错。退出码 0 表示预览或指定数量读取完成，1 表示运行错误/超时，2 表示无效参数，130 表示中断；退出会关闭订阅和 Node。不自动重试，不发布控制消息。
