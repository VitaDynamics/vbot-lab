# Perception

<p align="center"><a href="README.md">English</a> | 中文</p>

[分类索引](../README.zh-CN.md) · [接口语义](../../docs/interfaces/perception.zh-CN.md) · [Python](main.py) · [C++](main.cc)

## 选择数据流

`--stream`: detections → /perception/detections2d; poses → /perception/poses.

检测输出包含字符串类别、分数、像素框、图像尺寸与采集时间。person_boxes 仅统计当前 person 类检测框，未按置信度过滤，不是独立人数统计。收到空数组与没有收到消息不同。poses 输出单人的 COCO 关键点；confidence 是 logit，示例同时使用数值稳定的 sigmoid 计算概率。坐标为图像像素，不是机器人位姿或深度。关键点输出要求 pose 模型且画面中有人；没有消息不能证明无人。程序不保存图像，不触发语音或运动。

## 构建与离线预览

Python 与 C++ 使用相同参数，默认仅输出计划，不创建 Node。C++ 需要配套 SDK/Schema 才能构建和运行预览。

```bash
bazel build //recipes/perception:main //recipes/perception:main_cpp
bazel run //recipes/perception:main -- --stream detections
bazel run //recipes/perception:main_cpp -- --stream detections
```

## 在设备上读取

Python 先按 [Python 部署流程](../../docs/development/python-deployment.zh-CN.md)部署本示例，再以 vbot 身份从所得应用目录（APP_DIR）使用新建的 venv 运行，并配置设备环境。C++ 按[二进制部署流程](../../packages/aorta/cpp/README.zh-CN.md)准备，部署可执行文件名为 bin/perception；其应用目录与 Python 部署目录分开。

```bash
python -m recipes.perception.main --stream detections --count 3 --timeout 20 --execute
```

C++：切换到已部署 C++ 二进制的应用目录，按 C++ 指南配置运行库后执行：

```bash
./bin/perception --stream detections --count 3 --timeout 20 --execute
```

每次只选择一个数据流。按上方列表替换 --stream；不要为获取样本而自动重启服务或改变模式。

## 输出与退出

时间戳为零或缺失时视为未知，不能据此声称数据新鲜；连续读取三条消息也不保证来源时间持续推进。使用数据前检查时间戳、状态和有效性。

输出为 JSON Lines，保留来源 topic 与采集时间（源消息提供时）。非有限浮点数输出为 null。收到样本不等于数据有效或当前可用于控制；按接口契约检查状态、有效性及时间。超时不代表零值或无人。--count 为 1–1000，--timeout 为 (0,120] 秒且覆盖整个采样过程。队列或样本超限会报错。退出码 0 表示预览或指定数量读取完成，1 表示运行错误/超时，2 表示无效参数，130 表示中断；退出会关闭订阅和 Node。不自动重试，不发布控制消息。
