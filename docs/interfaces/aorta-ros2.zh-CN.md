# Aorta 与 ROS 2 兼容接口

<p align="center"><a href="aorta-ros2.md">English</a> | 中文</p>

Aorta 是 VBOT EDU 机器人的原生通信层。`aorta_ros2_bridge` 保留部分此前已公开的
ROS 2 接口，并非另一套完全等价的机器人接口。请先完成[设备 shell 配置](../getting-started/device-environment.zh-CN.md)。

## 版本范围

本参考适用于 `foot_quadruped` EDU 软件。接口是否可用取决于已安装固件，
使用前请发现确切路由并检查交付的消息类型。
各条目的最低固件版本尚未全部公布；此软件范围不覆盖其他机器人类型。

本页列出开放 topic 集及受支持的映射，并整理 service 与 RCP action。
topic 表共包含 46 个不同的 Aorta 路由：43 个订阅输出、3 个控制输入。
发现输出路由后，限时获取样本检查发布者；不要通过向控制 topic 发布消息来检查环境。
Python SDK wheel 安装与已入库的 Schema 源码有独立说明，
设备 CLI 使用不要求安装 Python SDK。

原生 Aorta SLAM 流程，包括地图保存、定位与坐标数据，见[建图与定位](../guides/mapping-localization.zh-CN.md)。

## 按功能域使用

每个功能域统一说明用途、数据含义、读取流程与异常处理。按任务选择一个入口，
再只检查需要的具体路由，不将每条 topic 拆成独立能力检查项。

| 功能域 | 包含内容 |
| --- | --- |
| [传感器与硬件遥测](sensors.zh-CN.md) | 电池、IMU、雷达、UWB、GNSS、舵机反馈 |
| [相机与 AprilTag](cameras.zh-CN.md) | 标定、压缩视频、标签检测 |
| [Perception](perception.zh-CN.md) | 目标检测与人体关键点 |
| [Audio](audio.zh-CN.md) | 音频帧、ASR 文本、语音事件、UWB 输入结束 |
| [运动](locomotion.zh-CN.md) | 状态、终态报告、摇杆／速度输入 |
| [系统与外设](system-peripherals.zh-CN.md) | 系统状态、显示、耳灯调制 |
| [RCP](rcp.zh-CN.md) | 任务 action 与追踪事件 |
| [SLAM](../guides/mapping-localization.zh-CN.md) | 里程计、地图、坐标变换、建图／定位流程 |

## 用于发现与检查的只读 topic

下列名称是面向用户的 Aorta CLI 路由，不是传输层 key 表达式。
`pub/sub` 表示通信原语，操作方向以开发者视角描述。
表格不是完整字段契约，也不保证持续输出。已安装版本的列表请通过 CLI 发现。
日志、参数等 ROS 中间件接口不是机器人功能，不列入此清单。

| 用途 | Aorta topic | ROS 2 topic | 原语／开发者方向 | Aorta 根类型 | ROS 2 消息类型 |
| --- | --- | --- | --- | --- | --- |
| [电池](sensors.zh-CN.md) | `/bms_state` | `/bms_state` | pub/sub — 订阅 | `bms.BmsState` | `lowlevel_msg/msg/BmsState` |
| [机身 IMU](sensors.zh-CN.md) | `/imu_raw` | `/imu_raw` | pub/sub — 订阅 | `aorta.topic.sensor.Imu` | `sensor_msgs/msg/Imu` |
| [雷达 IMU](sensors.zh-CN.md) | `/lidar_imu` | `/lidar_imu` | pub/sub — 订阅 | `aorta.topic.sensor.Imu` | `sensor_msgs/msg/Imu` |
| [雷达点云](sensors.zh-CN.md) | `/lidar_points` | `/lidar_points` | pub/sub — 订阅 | `foxglove.PointCloud` | `sensor_msgs/msg/PointCloud2` |
| [雷达诊断](sensors.zh-CN.md) | `/lidar_diagnostic_status` | `/lidar_diagnostic_status` | pub/sub — 订阅 | `aorta.topic.sensor.DiagnosticArray` | `diagnostic_msgs/msg/DiagnosticArray` |
| [雷达数据包](sensors.zh-CN.md) | `/lidar_packets` | `/lidar_packets` | pub/sub — 订阅 | `aorta.topic.sensor.LidarPacket` | `aorta_msgs/msg/LidarPacket` |
| [UWB 测距](sensors.zh-CN.md) | `/uwb/ranging` | `/uwb/data` | pub/sub — 订阅 | `aorta.uwb.UwbRangingData` | `uwb_location/msg/UWB` |
| [UWB 状态](sensors.zh-CN.md) | `/uwb/state` | `/uwb/state` | pub/sub — 订阅 | `aorta.uwb.UwbState` | `uwb_msgs/msg/Status` |
| [头部触摸事件](sensors.zh-CN.md) | `/uwb/head_touch` | `/uwb/head_touch` | pub/sub — 订阅 | `aorta.uwb.HeadTouchEvent` | `aorta_msgs/msg/HeadTouchEvent` |
| [舵机状态](sensors.zh-CN.md) | `/lowlevel/servo_status` | `/servo/status` | pub/sub — 订阅 | `lowlevel.ServoStatuses` | `lowlevel_msg/msg/ServoStatuses` |
| [原始 GNSS 定位](sensors.zh-CN.md) | `/gnss/fix` | `/gnss/fix` | pub/sub — 订阅 | `aorta.topic.gnss.NavSatFix` | `sensor_msgs/msg/NavSatFix` |
| [融合 GNSS；拆分表示](sensors.zh-CN.md) | `/gnss/fusion` | `/gnss/fusion` + `/gnss/fusion_extra` | pub/sub — 订阅 | `gnss.GnssFusion` | `sensor_msgs/msg/NavSatFix` + `aorta_msgs/msg/GnssFusionExtra` |
| [里程计与派生动态 TF](../guides/mapping-localization.zh-CN.md) | `/odometry` | `/odometry` + `/tf` | pub/sub — 订阅 | `aorta.topic.navigation.Odometry` | `nav_msgs/msg/Odometry` + `tf2_msgs/msg/TFMessage` |
| [静态坐标变换](../guides/mapping-localization.zh-CN.md) | `/slam/static_transforms` | `/tf_static` | pub/sub — 订阅 | `aorta.topic.slam.TransformArray` | `tf2_msgs/msg/TFMessage` |
| [SLAM 状态](../guides/mapping-localization.zh-CN.md) | `/slam/status` | `/slam/status` | pub/sub — 订阅 | `aorta.topic.slam.SlamStatus` | `slam_msgs/msg/SlamStatus` |
| [压缩栅格地图](../guides/mapping-localization.zh-CN.md) | `/slam/grid_map/compressed` | `/grid_map/compressed` | pub/sub — 订阅 | `foxglove.CompressedImage` | `foxglove_msgs/msg/CompressedImage` |
| [左相机标定](cameras.zh-CN.md) | `/stereo_left/camera_info` | `/stereo_left/camera_info` | pub/sub — 订阅 | `foxglove.CameraCalibration` | `sensor_msgs/msg/CameraInfo` |
| [右相机标定](cameras.zh-CN.md) | `/stereo_right/camera_info` | `/stereo_right/camera_info` | pub/sub — 订阅 | `foxglove.CameraCalibration` | `sensor_msgs/msg/CameraInfo` |
| [左相机 H.265 视频](cameras.zh-CN.md) | `/image_left_raw/h265` | `/image_left_raw/h265` | pub/sub — 订阅 | `foxglove.CompressedVideo` | `foxglove_msgs/msg/CompressedVideo` |
| [左相机 H.265 half 视频流](cameras.zh-CN.md) | `/image_left_raw/h265_half` | `/image_left_raw/h265_half` | pub/sub — 订阅 | `foxglove.CompressedVideo` | `foxglove_msgs/msg/CompressedVideo` |
| [左相机 H.265 quarter 视频流](cameras.zh-CN.md) | `/image_left_raw/h265_quarter` | `/image_left_raw/h265_quarter` | pub/sub — 订阅 | `foxglove.CompressedVideo` | `foxglove_msgs/msg/CompressedVideo` |
| [左相机去畸变 H.265 视频](cameras.zh-CN.md) | `/image_left_raw/h265_undistort` | `/image_left_raw/h265_undistort` | pub/sub — 订阅 | `foxglove.CompressedVideo` | `foxglove_msgs/msg/CompressedVideo` |
| [右相机 H.265 视频](cameras.zh-CN.md) | `/image_right_raw/h265` | `/image_right_raw/h265` | pub/sub — 订阅 | `foxglove.CompressedVideo` | `foxglove_msgs/msg/CompressedVideo` |
| [右相机 H.265 half 视频流](cameras.zh-CN.md) | `/image_right_raw/h265_half` | `/image_right_raw/h265_half` | pub/sub — 订阅 | `foxglove.CompressedVideo` | `foxglove_msgs/msg/CompressedVideo` |
| [右相机 H.265 quarter 视频流](cameras.zh-CN.md) | `/image_right_raw/h265_quarter` | `/image_right_raw/h265_quarter` | pub/sub — 订阅 | `foxglove.CompressedVideo` | `foxglove_msgs/msg/CompressedVideo` |
| [双目 AprilTag 检测](cameras.zh-CN.md) | `/stereo_apriltag/detection` | `/function/stereo_tag_detection` | pub/sub — 订阅 | `aorta.topic.sensor.StereoTagDetection` | `function_msgs/msg/StereoTagDetection` |
| [二维目标检测（含人体）](perception.zh-CN.md) | `/perception/detections2d` | `/perception/detections2d` | pub/sub — 订阅 | `perception.Detection2DArray` | `vision_msgs/msg/Detection2DArray` |
| [人体二维关键点](perception.zh-CN.md) | `/perception/poses` | `/perception/poses` | pub/sub — 订阅 | `perception.PoseDetection` | `vision_msgs/msg/PoseDetection` |
| [运动状态](locomotion.zh-CN.md) | `/locomotion/status` | `/locomotion/status` | pub/sub — 订阅 | `locomotion.LocomotionStatus` | `software_msgs/msg/LocomotionStatus` |
| [机身动作状态](locomotion.zh-CN.md) | `/locomotion/body_action_status` | `/locomotion/body_action_status` | pub/sub — 订阅 | `locomotion.BodyActionStatus` | `function_msgs/msg/BodyActionStatus` |
| [头部状态](locomotion.zh-CN.md) | `/locomotion/head_status` | `/locomotion/head_status` | pub/sub — 订阅 | `locomotion.HeadStatus` | `aorta_msgs/msg/HeadStatus` |
| [机身任务报告](locomotion.zh-CN.md) | `/locomotion/body/task_report` | `/locomotion/body/task_report` | pub/sub — 订阅 | `aorta.topic.task.TaskReport` | `aorta_msgs/msg/TaskReport` |
| [头部任务报告](locomotion.zh-CN.md) | `/locomotion/head/task_report` | `/locomotion/head/task_report` | pub/sub — 订阅 | `aorta.topic.task.TaskReport` | `aorta_msgs/msg/TaskReport` |
| [动作报告](locomotion.zh-CN.md) | `/locomotion/action_report` | `/locomotion/action_report` | pub/sub — 订阅 | `locomotion.ActionReport` | `aorta_msgs/msg/ActionReport` |
| [运动事件](locomotion.zh-CN.md) | `/locomotion/event` | `/locomotion/event` | pub/sub — 订阅 | `locomotion.LocomotionEvent` | `software_msgs/msg/LocomotionEvent` |
| [RCP 任务追踪事件](rcp.zh-CN.md) | `/rcp/trace` | `/rcp/trace` | pub/sub — 订阅 | `aorta.topic.rcp.TraceEvent` | `function_msgs/msg/TraceEvent` |
| [系统状态机](system-peripherals.zh-CN.md) | `/system/sm_status` | `/sm/status` | pub/sub — 订阅 | `sm.SmStatus` | `software_msgs/msg/SystemStateMachineStatus` |
| [显示状态](system-peripherals.zh-CN.md) | `/display_node/status` | `/display_node/status` | pub/sub — 订阅 | `aorta.topic.peripheral.DisplayStatus` | `aorta_msgs/msg/DisplayStatus` |
| [语音交互事件](audio.zh-CN.md) | `/voice/event` | `/voice/event` | pub/sub — 订阅 | `aorta.voice.VoiceEvent` | `aorta_msgs/msg/VoiceEvent` |
| [最终识别文本；provider 区分本体／UWB 输入](audio.zh-CN.md) | `/speech/asr_result` | `/speech/asr_result` | pub/sub — 订阅 | `aorta.topic.speech.AsrResult` | `aorta_msgs/msg/AsrResult` |
| [本体麦克风音频帧](audio.zh-CN.md) | `/raw_audio_dump` | `/raw_audio_dump` | pub/sub — 订阅 | `foxglove.RawAudio` | `foxglove_msgs/msg/RawAudio` |
| [遥控器经 UWB 信令传入的音频帧](audio.zh-CN.md) | `/audio/uwb_adpcm_segment` | `/audio/uwb_adpcm_segment` | pub/sub — 订阅 | `foxglove.RawAudio` | `foxglove_msgs/msg/RawAudio` |
| [UWB 音频输入结束事件](audio.zh-CN.md) | `/uwb/audio_done` | `/uwb/audio_done` | pub/sub — 订阅 | `aorta.uwb.AudioDoneEvent` | `aorta_msgs/msg/AudioDoneEvent` |

IMU、雷达、图像、地图与音频可能涉及较高带宽或隐私要求。
初始检查使用单条 IMU 流和短时限，不同时订阅全部 topic。
相机变体及其他状态／事件流应按发现的确切名称选择，不能把通配符当成一个端点名称。

## 控制 topic

下列三条路由均为 **pub/sub 输入**：应用发布，ROS bridge 按 ROS → Aorta 转发，
不是机器人状态订阅。发布前明确唯一控制方、检查交付类型与 QoS，并约定清理和停止方式。
运动操作还需确认运行模式、有人监护的安全区域以及可随时使用的停止控制。
发现接口时不要发送占位消息或全零测试消息。

| 用途 | Aorta topic | ROS 2 topic | 原语／开发者方向 | Aorta 根类型 | ROS 2 消息类型 |
| --- | --- | --- | --- | --- | --- |
| [摇杆控制输入](locomotion.zh-CN.md) | `/locomotion/joy` | `/joy` | pub/sub — 发布 | `locomotion.Joy` | `sensor_msgs/msg/Joy` |
| [速度控制输入](locomotion.zh-CN.md) | `/locomotion/velocity_command` | `/vel_cmd` | pub/sub — 发布 | `aorta.topic.navigation.Twist` | `geometry_msgs/msg/Twist` |
| [耳灯亮度调制](system-peripherals.zh-CN.md) | `/light/ear_modulation` | `/light/ear_modulation` | pub/sub — 发布 | `aorta.topic.peripheral.EarModulation` | `aorta_msgs/msg/EarModulation` |

- 摇杆轴值必须有限，且处于归一化范围 [-1, 1]。不能从通用 ROS 类型猜测轴／按键映射。
  原生 Joy 消息没有 ROS header，ROS 时间戳与坐标系标识不会传入该消息。
- 速度指令可能驱动机器人运动。不能只凭 Twist 消息推断允许的轴、单位、速度限制或安全停止方式，
  应遵循已安装版本的控制契约。
- 耳灯调制使用有限的 `value`，范围为 [0, 1]，乘到当前耳灯亮度上。
  它不选择 RGB 颜色，也不启动灯效；这些操作使用灯效控制或渐变 service。
  活跃的 ROS 转发会话结束时，bridge 恢复中性因子 `1.0`，不是关灯。
- ROS 控制 bridge 实施单写入方占用、输入检查和输入中断超时保护。
  被拒帧直接丢弃，不自动截断数值。活跃会话结束时，运动路由发送终止零指令后停止转发；
  这不能替代机器人的正常停止控制。这些是 **bridge** 行为，不能据此认定任意直接使用
  Aorta 的发布者也有同样的占用管理与超时保护。
- 诊断中的 `armed` 表示控制路由已准备好评估输入，不表示指令执行成功。
  `NEVER_SEEN` 可以表示还没有收到指令；`DEADMAN_STOP` 可以表示上一段输入流已结束。
  解释状态前同时检查当前安全条件、控制占用和连接字段。

## 服务与控制接口

Service 是请求／响应接口，不是用于订阅的 topic。
通过 `aorta service list` 和 `ros2 service list --no-daemon -t` 发现。
不要把调用服务作为自动环境检查，即使其用途是只读查询。

| Aorta service | ROS 2 service | 用途／开发者操作 |
| --- | --- | --- |
| `/firmware_version/motor` | `/firmware_version/motor` | service — 查询电机固件 |
| `/firmware_version/servo` | `/firmware_version/servo` | service — 查询舵机固件 |
| `/firmware_version/lidar` | `/firmware_version/lidar` | service — 查询雷达固件 |
| `/firmware_version/uwb` | `/firmware_version/uwb` | service — 查询 UWB 固件 |
| `/display_node/get_supported_emotions` | `/display_node/get_supported_emotions` | service — 查询可用表情 |
| `/display_node/play_emotion` | `/display_node/play_emotion` | service — 播放表情 |
| `/display_node/display_imgs` | `/display_node/display_imgs` | service — 显示图片 |
| `/light_node/status` | `/light_node/status` | service — 查询耳灯状态，尽管名称为 `status` |
| `/light_node/control` | `/light_node/control` | service — 控制耳灯灯效 |
| `/light_node/gradient` | `/light_node/gradient` | service — 设置耳灯渐变 |
| `/locomotion/lowlevel_action` | `/sm/action/lowlevel` | service — 机身控制，并非 ROS action |
| `/locomotion/head_action` | `/head_action` | service — 头部控制 |
| `/locomotion/set_run_mode` | `/locomotion/set_run_mode` | service — 切换运行模式 |
| `/locomotion/runtime_control` | `/locomotion/runtime_control` | service — 调整运动运行时设置 |
| `/slam/set_slam_mode` | `/slam/set_slam_mode` | service — 建图、保存与定位模式 |
| `/slam/get_path_to_target` | `/slam/get_path_to_target` | service — 请求路径，不是运动命令 |
| `/slam/query_map` | `/slam/query_map` | service — 查询地图数据 |
| `/volume_control` | `/volume_control` | service — 按请求查询／调整音量 |
| `/speech/set_speak` | `/set_speak` | service — 语音播放／控制 |

固件查询需要正确的 `target_device_type`：MOTOR=`0`、SERVO=`1`、LIDAR=`2`、UWB=`3`。
调用前检查交付的请求类型，不能对所有设备类型都使用空请求／默认请求。
此表不提供控制载荷，也不改变具体操作所需的前置条件。

## RCP 任务 action

`/rcp/execute_task` 是 **action**，不是 topic 或 service。
它接受 DAG 或预设，提供进度反馈、终态结果，并支持取消。

| Aorta action | Goal／result／feedback 数据根类型 | ROS 2 action | ROS 2 action 类型 |
| --- | --- | --- | --- |
| `/rcp/execute_task` | `aorta.action.rcp.ExecuteTaskGoal` / `aorta.action.rcp.ExecuteTaskResult` / `aorta.action.rcp.ExecuteTaskFeedbackData` | `/rcp/execute_task` | `aorta_msgs/action/ExecuteTask` |

任务输入、进度、终态、取消、并发限制与追踪事件的使用见 [RCP 任务与追踪](rcp.zh-CN.md)。
检查 provider 不提交目标；执行 DAG 需明确操作意图。

## 系统状态与坐标变换的只读检查

系统状态可通过原生 `/system/sm_status` 和 ROS `/sm/status` 读取。
静态变换可通过 `/slam/static_transforms` 和 ROS `/tf_static` 读取；
动态 `/tf` 仍由里程计派生。在设备 shell 中逐条限时检查：

```bash
timeout 15s aorta topic echo /system/sm_status --count 1
timeout 15s ros2 topic echo /sm/status software_msgs/msg/SystemStateMachineStatus --no-daemon --once --qos-reliability best_effort
timeout 15s aorta topic echo /slam/static_transforms --count 1
timeout 15s ros2 topic echo /tf_static tf2_msgs/msg/TFMessage --no-daemon --once --qos-reliability reliable --qos-durability transient_local
```

原生静态变换源会周期刷新，新订阅需留出等待样本的时间。
ROS 静态 TF 使用 transient-local 持久性；订阅时请求该持久性，以接收保留快照。
不要从另一个静态 TF 发布源重复发布相同子坐标系。

仅查看 bridge 路由状态、不发送机器人指令：

```bash
timeout 15s ros2 topic echo /aorta_bridge/diagnostics diagnostic_msgs/msg/DiagnosticArray --no-daemon --once --qos-reliability best_effort
```

部分输出仅在有订阅者时激活。因等待订阅者而处于 inactive 的路由不等于接口未实现。
事件流在两次事件之间可以没有消息，上一条事件时间较旧本身不代表传感器故障。
应检查路由给出的原因并按需限时采样，不要假设所有列出的 topic 都持续发布。

## 数据解释与订阅

- 路由同名不代表序列化、字段或语义等价。解码前分别查询 Aorta Schema 与 ROS 类型；bridge 会进行转换。
- ROS `/tf` 从里程计派生。
- 部分电池时间戳没有对应 ROS 字段，部分 ADC 字段补零。电池数组应遵循有效元素数量，不使用固定数组的无效尾部。
- GNSS 细节拆分到标准定位与 fusion-extra 输出；部分 UWB 字段被省略或使用默认值。
  部分服务把细分状态合并为布尔值。本文记录的 ROS 地图查询接口不应用 radius，返回点云采用 XYZI。
- 只订阅应用需要的数据流，使用有界队列并检查时间戳，避免在处理或网络延迟后使用过期数据。

收不到数据时，检查设备 shell 环境、所选路由、消息类型及发布者状态。
发现与单条采样命令见[设备 shell 配置](../getting-started/device-environment.zh-CN.md)。
