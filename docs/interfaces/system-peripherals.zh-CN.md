# 系统状态、显示与耳灯

<p align="center"><a href="system-peripherals.md">English</a> | 中文</p>

调用方式选择与字段对应见[直接服务与 RCP](../guides/control-paths.zh-CN.md)。

Python/C++ 只读示例见 [system-peripherals Recipe](../../recipes/system-peripherals/README.zh-CN.md)，包含 Bazel 构建、离线预览及显式设备读取。

本功能域用于系统状态看板、显示观察与明确要求的灯光交互。
在 `foot_quadruped` EDU／DEV 上完成[设备 shell 配置](../getting-started/device-environment.zh-CN.md)。
准确类型与 ROS 映射见[接口表](aorta-ros2.zh-CN.md)。系统／显示输出只读，耳灯调制是控制输入。

## 路由与数据含义

| Aorta topic | 方向 | 定义与用途 |
| --- | --- | --- |
| `/system/sm_status` | 订阅 | 系统类别、流程状态、活跃状态／路径、级别、心跳与描述数据；区分状态、OTA 和告警消息 |
| `/ota_version` | 订阅 | `version` 中的已提交应用 OTA 版本字符串；ROS 使用 String.data |
| `/display_node/status` | 订阅 | 通过 `data` 携带显示状态；按交付表示解析，不预设为图像或稳定 JSON 布局 |
| `/light/ear_modulation` | 发布 | [0, 1] 范围内的有限 `value` 缩放当前耳灯效果亮度，不是颜色／灯效选择器 |

这些是 pub/sub 接口。显示表情／图片 service 与灯效控制／渐变 service 是独立操作，
见 [service 表](aorta-ros2.zh-CN.md)。

## 最小只读流程

```bash
timeout 15s aorta schema get /system/sm_status --describe
timeout 15s aorta schema get /display_node/status --describe
timeout 15s aorta schema get /light/ear_modulation --describe
timeout 15s aorta topic echo /system/sm_status --count 1
```

显示观察应用改为采样显示输出：

```bash
timeout 15s aorta topic echo /display_node/status --count 1
```

1. 系统状态结合 `category`、`status`、`state_id`、`state_name`、`active_state_path`、
   `severity`、`is_active` 解释；某类别的流程状态不是无关应用任务的终态结果。
2. 用 `heartbeat_seq` 与消息新鲜度确认当前状态。机器决策与自由文本 `message`／`data` 分开，
   状态观察本身不授予切换模式或下发运动指令的权限。
3. ROS 用成对的 ID／名称数组表达状态路径，不同于 Aorta 的条目向量；保留配对并检查长度。
   便捷的低功耗标志没有对应的额外 ROS 字段，不能按相同结构解码两种表示。
4. 显示状态只是观察数据，收到它不能证明有人看到了指定图片，也不能由状态字符串推断完整像素内容。

## OTA 应用版本

`/ota_version` 是只读的已提交应用 OTA 版本字符串。
[Schema](../../schemas/aorta/schemas/topic/system_monitor/ota_version.fbs) 定义
`aorta.topic.system_monitor.OtaVersion`，字段为 `aorta_header` 和 `version`。
ROS 2 在同名 topic 使用 `std_msgs/msg/String`，Aorta 的 `version` 对应 ROS 的 `data`。
[Bridge 路由](../../schemas/ros2/routes.json) 方向为 Aorta → ROS，
QoS 为 reliable、volatile、keep-last、深度 10。
此输出未声明服务超时或指令速率限制。
Python／C++ SDK 读取使用 [system-peripherals](../../recipes/system-peripherals/README.zh-CN.md)
的 `--stream version`。比较 `~` 构建后缀之前的应用标识，反馈问题时保留完整字符串。
此值不是 SDK 包版本。

```bash
timeout 15s ros2 interface show std_msgs/msg/String
```

## 低功耗服务

`/system/power_saving/enable` 用于进入／退出低功耗模式。
[Schema](../../schemas/aorta/schemas/service/system/power_saving_enable.fbs) 定义
`aorta.services.system.PowerSavingEnableRequest` 和
`aorta.services.system.PowerSavingEnableResponse`，两者均包含 `aorta_header`。
请求 `data=true` 进入该模式，`data=false` 退出。Aorta 返回
`status` 和可选的 `message`；`ServiceStatus.SUCCESS=0` 表示成功。
ROS 2 在同名服务使用 `std_srvs/srv/SetBool`，请求为 `data`，响应为
`success` 和 `message`。

[Bridge 路由](../../schemas/ros2/routes.json) 设置 5000 ms 超时、最多一个在途请求、
单写者、每秒 5 个请求、突发上限 10、请求大小上限 4096 字节。
QoS 为 reliable、volatile、keep-last、深度 4。未配置 deadman 超时或 zero-on-deadman 指令。
这是控制接口；只检查类型，不调用服务：

```bash
timeout 15s ros2 interface show std_srvs/srv/SetBool
```

## 补光灯

`/light_node/fill_light` 是 **service**，不是耳灯 topic。原生 Aorta 使用
[FillLightRequest / FillLightResponse](../../schemas/aorta/schemas/service/peripheral/fill_light.fbs)，
ROS 2 在同名服务使用 `peripheral_msgs/srv/FillLight`。
`enable` 选择开关状态，`brightness` 为 0–100 的整数百分比；大于 100 无效，不能套用耳灯的 0–255 范围。
Aorta 返回 `status`、`message`，ROS 返回 `success`、`message`。检查响应后，另行确认现场灯光状态。
与其他应用协调控制权，并恢复自己改变的状态；发现接口时不自动开灯。

## 自动低功耗策略

`/system/power_saving/set_policy` 配置自动触发条件，**不会立即休眠或唤醒设备**。
原生 Aorta 使用
[PowerSavingSetPolicyRequest / PowerSavingSetPolicyResponse](../../schemas/aorta/schemas/service/system/power_saving_set_policy.fbs)，
ROS 2 在同名服务使用 `software_msgs/srv/SetPowerSaving`。

| 请求字段 | 含义 |
| --- | --- |
| `type` | `CHARGING_SLEEP=1`：充电时自动休眠；`POSE_SLEEP=2`：趴下时自动休眠。UNKNOWN=0 不是可选策略 |
| `enable` | 开启或关闭这一项自动触发策略 |

检查 Aorta `status`／`message` 或 ROS `success`／`message`。接纳请求本身不能独立证明设置已持久化，
更不能证明设备已进入休眠。修改前与其他应用协调，不用策略修改探测连通性。
明确要求立即休眠／唤醒时，使用独立的 `/system/power_saving/enable`。

这两项 service 的 bridge 均为一个在途请求、5000 ms 超时、每秒 5 次、突发 10 次、请求上限 4096 字节；
没有 deadman 自动撤销。只检查定义而不修改设置：

```bash
timeout 15s aorta schema get /light_node/fill_light --describe
timeout 15s aorta schema get /system/power_saving/set_policy --describe
```

## 显示服务

### 内置表情

`/display_node/play_emotion` 使用
[PlayEmotionRequest / PlayEmotionResponse](../../schemas/aorta/schemas/service/peripheral/play_emotion.fbs)。
通过 `mode` 选择[表情目录](../resources/expressions.zh-CN.md)中的编号。

| 请求字段 | 含义 |
| --- | --- |
| `target_state` | 1 开始播放；0 停止并恢复配置的默认表情 |
| `req_id`, `pre_check` | 请求关联与准备／检查选择；预检查成功不代表播放 |
| `duration_ms` | -1 播放一遍；0 循环；正值表示重复播放对应毫秒数，之后恢复默认表情 |
| `custom_images_name` | 内置表情保持为空；非空值选择之前已注册的序列，不是文件路径或上传入口 |

自定义序列应先通过[图片管理服务](#注册图片序列)注册，再使用准确名称。
非空 `custom_images_name` 优先于 `mode`；名称不存在时不会回退到内置表情。
不要将文件路径作为名称。
RCP 编排见[控制路径指南](../guides/control-paths.zh-CN.md)。

### 内联 JPEG 序列

`/display_node/display_imgs` 使用
[DisplayImgsRequest / DisplayImgsResponse](../../schemas/aorta/schemas/service/peripheral/display_imgs.fbs)。

| 请求字段 | 含义 |
| --- | --- |
| `images` | 非空 `ShowImg` 数组：`width=480`、`height=854`，`encoding` 为 `jpeg` 或 `jpg`，`data` 为完整 JPEG 字节；元数据和 JPEG 头均须为 480×854 像素 |
| `duration_ms` | 逐帧的无符号毫秒时长，数组长度须等于图片数量；零表示不主动等待，不是永久持屏 |
| `loop` | 默认 false：播放一遍并恢复默认表情；true：重复播放，直到显式替换或停止 |

原生输入限制为最多 4096 帧、单张 JPEG 不超过 8 MiB、总 JPEG 数据不超过 32 MiB。
可接受的 JPEG 编码仍受解码器限制。ROS bridge 的序列化请求上限为含消息开销的 8 MiB，
不能套用原生总量上限。

服务在首帧准备成功后才接管显示。`status=SUCCESS` 回复表示首帧已提交，
不是整个序列结束或人眼已看到画面。准备／首帧失败保留原画面，后续异步错误需检查状态。
播放器不会在图片请求切换时主动插入黑帧。

关闭客户端或收到启动回复不会结束循环。协调显示使用方后，结束时调用
`/display_node/play_emotion` 并设置 `target_state=0`。
不要发送空图片数组作为停止命令。`/display_node/status` 是描述文本，
不是像素级确认或与请求关联的序列完成事件。

兼容 ROS 类型 `peripheral_msgs/srv/PlayEmotion` 不包含 `custom_images_name`，
注册序列使用下文独立的完整字段 ROS 入口播放。
ROS 类型 `peripheral_msgs/srv/DisplayImgs` 不包含 `loop`，内联播放保留既有单次播放字段；
原生 Aorta 内联循环使用配套 SDK。

### 注册图片序列

下列接口均为 **service**，不是 topic。注册将不可变 JPEG 序列持久化，供后续播放，
本身不切换屏幕。三个管理服务共用
[custom_images_ctrl.fbs](../../schemas/aorta/schemas/service/peripheral/custom_images_ctrl.fbs)。

| Aorta／ROS 2 service | Aorta 请求／响应（命名空间 `aorta.services.peripheral`） | ROS 2 定义 |
| --- | --- | --- |
| `/display_node/add_images` | `AddImagesRequest`／`AddImagesResponse` | [`aorta_msgs/srv/AddImages`](../../schemas/ros2/aorta_msgs/srv/AddImages.srv) |
| `/display_node/get_images_status` | `GetImagesStatusRequest`／`GetImagesStatusResponse` | [`aorta_msgs/srv/GetImagesStatus`](../../schemas/ros2/aorta_msgs/srv/GetImagesStatus.srv) |
| `/display_node/del_images` | `DelImagesRequest`／`DelImagesResponse` | [`aorta_msgs/srv/DelImages`](../../schemas/ros2/aorta_msgs/srv/DelImages.srv) |

按以下生命周期使用：

1. **注册。** `custom_images_name` 为 1–64 字节 ASCII 字母、数字、`_`、`.` 或 `-`，
   首字符必须是字母或数字。按顺序填写 `images`，`fps` 为 1–60，默认 30。
   每帧 JPEG 的声明尺寸与编码尺寸均须为 480×854。整组为 1–4096 帧，
   单次请求至多携带 **4 MiB JPEG 数据**。ROS 图片类型使用
   [`aorta_msgs/msg/ShowImg`](../../schemas/ros2/aorta_msgs/msg/ShowImg.msg)，
   不是 `peripheral_msgs` 中的同名类型。
2. **完成上传。** 小序列一次提交时，`upload_id`、`frame_offset`、`total_frames`、
   `total_bytes` 保持默认值。分批时使用同一 `upload_id`、重复整组总量，
   并根据响应的 `next_frame_offset` 推进 `frame_offset`。
   只有 `complete=true` 才表示整组可用，批次已接收不等于序列可播放。
   同名同内容重复注册幂等成功，不同内容返回 `ALREADY_EXISTS`，不会覆盖已有资源。
3. **查询。** `custom_images_name` 指定名称，或留空列出全部。
   检查 [`CustomImageSequenceStatus`](../../schemas/ros2/aorta_msgs/msg/CustomImageSequenceStatus.msg)
   中的 `frame_count`、`fps`、`jpeg_bytes`、`in_use`，以及 JPEG／磁盘／缓存用量和上限，
   未完成上传字段 `uploading_seq_name`、`uploaded_frames`、`total_frames`、`reserved_bytes`。
   超时后先查询再决定续传或取消，不自动发起另一份上传。最多一个未完成上传，
   无活动 120 秒后过期回收。
4. **播放与停止。** 原生 Aorta 调用 `/display_node/play_emotion` 并填写已注册的
   `custom_images_name`。ROS 使用 **`/display_node/play_emotion_native`**，类型为
   [`aorta_msgs/srv/PlayEmotion`](../../schemas/ros2/aorta_msgs/srv/PlayEmotion.srv)。
   两者到达同一个 Aorta service，`_native` 是 ROS 入口，不是另一条 Aorta 路由。
   设置 `target_state=1`；`duration_ms=-1` 播放一次，`0` 循环，正数指定播放时长。
   启动响应表示首帧提交，不代表整组播放完成。通过同一入口设置 `target_state=0` 停止。
   两个 ROS 播放入口共享指令控制权，不能作为互相独立的并发控制方。
5. **删除。** 停止播放后，通过 `/display_node/del_images` 提交准确名称，
   删除已完成序列或取消其未完成上传。准备／播放期间可能返回 `BUSY`，
   应等待资源释放，不直接删除文件。删除后只能重新注册图片恢复。

生成的 ROS 定义保留 `aorta_header`／`has_aorta_header` 及原生 `status`／`message`。
检查 `status=0`（`ServiceStatus.SUCCESS`），不要使用兼容服务的 `success` 布尔值。
管理响应的 `error_code` 是**字符串**，完整字段播放响应中的 `error_code` 则为 **int32**。

[Bridge 契约](../../schemas/ros2/routes.json)为每条路由最多一个在途请求、每秒 5 次、
突发 10 次，不自动重试。注册超时 10 秒，序列化请求上限为 4 MiB + 256 KiB；
删除／查询／播放超时 5 秒，请求上限 4096 字节。超时不能证明注册／删除失败。
按响应中的实际容量上限处理，不能假设存储无限。

配置设备 shell 后，可只检查定义，不注册、播放或删除内容：

```bash
timeout 15s aorta schema get /display_node/add_images --describe
timeout 15s aorta schema get /display_node/get_images_status --describe
timeout 15s aorta schema get /display_node/del_images --describe
timeout 15s ros2 interface show aorta_msgs/srv/AddImages
timeout 15s ros2 interface show aorta_msgs/srv/GetImagesStatus
timeout 15s ros2 interface show aorta_msgs/srv/DelImages
timeout 15s ros2 interface show aorta_msgs/srv/PlayEmotion
```

链接中的 `.srv`／`.msg` 是 ROS 2 接口源定义，由 ROS 的 `rosidl` 工具链生成 IDL 与语言绑定。
定义文件不是可执行客户端，发现服务也不代表执行了对应操作。

## 耳灯交互与清理

需要时先用文档中的灯效 service 选择效果，再用调制改变亮度。
使用唯一发布方并遵循[控制保护说明](aorta-ros2.zh-CN.md)。
ROS bridge 拒绝非有限值／越界值，活跃调制会话结束时恢复 `1.0`；这是中性乘数，不是关灯。

没有合适的基础效果时，改变因子不一定产生可见灯效。
直接使用 Aorta 的发布者不能假定 bridge 的占用管理或超时恢复同样生效，需显式结束应用的调制周期。
退出时停止并释放发布者；上述只读示例不包含发布或 service 调用命令。

## 观察结果与应用预期不符时

把系统状态文字视为当前状态前，先检查新鲜度和消息类别。
灯光需区分灯效选择请求与亮度调制，检查灯光状态 service 的契约，不凭输入 topic 推断结果。
路由无消息或限时读取退出码为 `124` 时，检查发布者／连接并保持界面状态未知，
不自动触发灯效或重启服务。
