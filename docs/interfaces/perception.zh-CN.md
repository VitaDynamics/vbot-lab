# 目标检测与人体关键点

<p align="center"><a href="perception.md">English</a> | 中文</p>

Python/C++ 只读示例见 [perception Recipe](../../recipes/perception/README.zh-CN.md)，包含 Bazel 构建、离线预览及显式设备读取。

使用内置感知输出开发见人问候、画面人数统计、图像区域触发及关键点交互。
消费这些结果无需自行解码相机视频或部署另一套检测模型。
AprilTag 检测识别的是标签，不能代替人体检测。

## 前置条件与接口

当前适配 `foot_quadruped` EDU 的机器人应用版本 **V1.6.0**，
路由可用性须结合[兼容矩阵](../compatibility.zh-CN.md)确认。
使用 vbot 账户登录并完成[设备 shell 配置](../getting-started/device-environment.zh-CN.md)。
相机输入与感知服务需要正常运行。可识别类别与关键点取决于所安装的模型；当前默认模型检测人体。

两条接口均为 **pub/sub，只读订阅**，不是 service，也不是控制输入。

| 输出 | Aorta topic | Aorta 根类型 | ROS 2 topic | ROS 2 消息类型 |
| --- | --- | --- | --- | --- |
| 二维检测结果 | `/perception/detections2d` | `perception.Detection2DArray` | `/perception/detections2d` | `vision_msgs/msg/Detection2DArray` |
| 人体关键点 | `/perception/poses` | `perception.PoseDetection` | `/perception/poses` | `vision_msgs/msg/PoseDetection` |

使用设备 overlay 交付的 ROS 消息类型，包括其中的人体关键点类型；
工作站上独立安装的其他版本不能替代这一 overlay。

## 发现与检查

在设备 shell 中把两条路由作为一个 perception 功能域统一检查。
以下命令只检查元数据，不采集图像，也不是两个独立能力检查项：

```bash
timeout 15s aorta topic list
timeout 15s aorta schema get /perception/detections2d --describe
timeout 15s aorta schema get /perception/poses --describe
timeout 15s ros2 topic list --no-daemon -t
timeout 15s ros2 interface show vision_msgs/msg/Detection2DArray
timeout 15s ros2 interface show vision_msgs/msg/PoseDetection
```

然后按应用需要选择数据流，限时获取一条样本：

```bash
timeout 15s aorta topic echo /perception/detections2d --count 1
```

需要人体关键点时，改用：

```bash
timeout 15s aorta topic echo /perception/poses --count 1
```

也可以独立检查 ROS 订阅：

```bash
timeout 15s ros2 topic echo /perception/detections2d vision_msgs/msg/Detection2DArray --no-daemon --once --qos-reliability best_effort
```

路由可发现、Schema 可读取，表示能找到接口及其解码信息，不代表已有实时帧。
收到消息表示当时数据传递成功。退出码 `124` 表示时限内未收到样本，不能据此判断画面中无人。

## 理解二维检测结果

- 检测与姿态模型模式都会按处理帧发布数组。`detections` 为空表示该帧未检出目标，与没有消息不同。
- 每个目标包含字符串 `class_id`（人体为 `person`）、检测置信度 `score`，
  以及像素坐标检测框 `bbox`，字段为 `center_x`、`center_y`、`width`、`height`。
- 数组的 `frame_width`、`frame_height` 是源图像尺寸；`timestamp_ns` 为纳秒采集时间戳，
  `frame_id` 标识源坐标系。这些是图像坐标，不是机器人或地图坐标系中的米制位置。
- ROS 中类别与置信度位于 `detections[].results[].hypothesis.class_id` 和
  `detections[].results[].hypothesis.score`；检测框使用 `bbox.center.position.x`、
  `bbox.center.position.y`、`bbox.size_x`、`bbox.size_y`。采集时间与坐标系标识位于 `header`。
  bridge 不会把 Aorta 的图像宽高字段传入此 ROS 类型，需要这些尺寸时使用 Aorta。
  不要假设单独选择的视频流尺寸与检测器输入相同。
- 这些结果不提供稳定的人员身份或三维人体位置；画面检测框数量不等于独立访客人数。
  其他目标类别需按安装的模型确认，不能仅凭消息类型推断。

## 理解人体关键点

- 仅在 `model_type=pose` 时发布，每个检出人一条消息。无人时不发布姿态消息，
  不会发送空帧消息。使用检测数组流区分新鲜的空检测结果与数据缺失。
- `class_id` 是数值（人体为 `0`），不同于检测数组的字符串类别。
  `score` 是人体检测置信度。`bbox_min`、`bbox_max` 是像素坐标角点，
  `keypoints` 包含 17 个 COCO 关键点。框角点的额外坐标 `z` 为零，不是测得的深度。
- 关键点 `confidence` 是 **logit**，不是 0～1 概率。如需按概率设置阈值，
  先做数值稳定的 sigmoid 转换，不要直接把检测分数阈值套用到 logit 上。
  忽略无效或低置信度关键点。
- COCO 顺序：鼻；左／右眼；左／右耳；左／右肩；左／右肘；左／右腕；
  左／右髋；左／右膝；左／右踝。
- Aorta 通过 `timestamp_ns` 携带采集时间、`frame_id` 携带源坐标系；ROS 使用 `header`。
  桥接后关键点置信度仍为 logit。这些是人体图像姿态，**不是机器人里程计或定位结果**。
  手势标签与动作识别需要应用自行实现，不是此 topic 的附加输出。

## 开发“见到人就说你好”

1. 订阅检测数组 topic，确认持续收到新鲜帧；筛选人体类别与合适的检测置信度。
   使用有界队列，避免积压旧帧。
2. 维护未知、无人、有人三种状态。连续若干新鲜帧确认有人，以减少单帧误触发。
   首次确认有人可以问候一次；后续问候需要先确认无人，再重新确认有人。
3. 只有连续收到无符合条件人体的新鲜帧，才重新允许触发。数据缺失或过期时进入未知状态，
   不能当作人已离开，也不能重新允许问候；数据中断期间保留已经问候的标记。
4. 触发后通过 `/speech/set_speak` 或 ROS `/set_speak` 调用文档中的[语音服务](aorta-ros2.zh-CN.md)。
   构造载荷前检查交付的请求类型。播放语音是明确的应用动作，不是只读环境检查。
   增加冷却时间并避免重叠请求；服务失败时不要在每个相机帧上重复重试。
5. 交互期间保持订阅循环，退出时关闭订阅并释放资源。只修改设备 AGENTS.md 不会实现这一循环。

此流程可以按一次“有人出现”的周期问候，不识别具体个人。
只有交互还需要手势或身体姿态时，才使用关键点流。

## 收不到数据时

检查路由发现、已加载消息类型、时间戳、相机输入与感知运行状态。
关键点流还需检查安装的模型模式，以及画面中是否有人。
不要自动切换模型或重启设备服务。仅 ROS 收不到数据时，对比 Aorta 样本，
并按[设备环境排障](../getting-started/device-environment.zh-CN.md)检查。
