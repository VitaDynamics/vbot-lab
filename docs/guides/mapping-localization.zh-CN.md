# 建图与定位

<p align="center"><a href="mapping-localization.md">English</a> | 中文</p>

Python/C++ 只读示例见 [slam Recipe](../../recipes/slam/README.zh-CN.md)，包含 Bazel 构建、离线预览及显式设备读取。

使用设备上的 Aorta CLI 检查里程计、建立并保存室内地图，再在地图中定位。
本指南适用于当前 `foot_quadruped` EDU 接口集。
操作前确认设备的[软件范围](../compatibility.zh-CN.md)
和在线接口。本 CLI 流程不依赖Aorta Python SDK 安装。

## 1. 连接与准备

1. 先完成 [SSH 公钥免密登录](../robots/quadruped-common/connection.zh-CN.md)，再加载
   [vbot shell 环境](../getting-started/device-environment.zh-CN.md)。以下命令均在设备 shell
   中运行，不在开发容器中运行。
2. 初始检查时保持机器人静止，确认 LiDAR、IMU 正常且无遮挡。相机和 GNSS 数据流不是
   本室内流程的前置条件。
3. 切换模式前，确认没有其他应用正在建图、定位或导航；模式切换会影响共用的 SLAM 会话。
   使用新的地图名，避免覆盖仍需保留的地图；名称仅使用字母、数字、下划线和连字符，例如
   `edu_lab_1f`。后续命令始终使用同一个选定名称。
4. 建图需要在安全区域内有人看护地移动机器人。使用正常控制器，保持停止控制随时可用；
   位姿数据过期或跟踪丢失时停止移动。本指南不授权自主运动。

## 2. 检查所需接口

以下原生接口已包含在 EDU 接口集中。发现路由不代表发布进程正在运行，也不代表数据可用。

| 数据／操作 | Aorta CLI 路由 | 类型与消息类型 | 用途 |
| --- | --- | --- | --- |
| SLAM 状态 | `/slam/status` | pub/sub；`aorta.topic.slam.SlamStatus` | 模式、里程计／定位／地图状态、选中地图、关键帧数量 |
| 里程计与动态位姿 | `/odometry` | pub/sub；`aorta.topic.navigation.Odometry` | 位姿、速度、协方差、时间戳及机身／头部复合位姿 |
| 地图预览 | `/slam/grid_map/compressed` | pub/sub；`foxglove.CompressedImage` | 用于建图界面的压缩栅格图像 |
| 静态坐标变换 | `/slam/static_transforms` | pub/sub；`aorta.topic.slam.TransformArray` | 坐标系关系和传感器外参 |
| 切换模式／保存地图／重定位 | `/slam/set_slam_mode` | service；`aorta.services.slam.SetSlamModeRequest`／`aorta.services.slam.SetSlamModeResponse` | 控制 SLAM 流程 |

传感器检查可使用公开的 `/imu_raw`、`/lidar_imu` 和 `/lidar_points`。
已支持的 ROS 映射见 [Aorta／ROS 2 接口](../interfaces/aorta-ros2.zh-CN.md)。
本流程全程使用 Aorta，不替换成 ROS 路由名称或请求语法。

逐条运行以下只读检查：

```bash
timeout 15s aorta topic list
timeout 15s aorta service list
timeout 15s aorta service info /slam/set_slam_mode
timeout 15s aorta topic echo /slam/status --count 3
timeout 15s aorta topic echo /lidar_imu --count 1
timeout 5s aorta topic hz /lidar_points
```

确认所需路由可发现、状态时间戳持续推进、输入数据流有数据到达。
频率检查会在指定时间后结束；退出码 124 只表示到达时限，不表示接收检查通过。
里程计和地图预览可能需要进入相应模式后才输出数据。发现、解码或传感器接收失败时，
先解决问题再切换模式；不要把修改权限或重启服务作为这些检查的一部分。

## 3. 区分请求响应与完成状态

以下服务请求使用 JSON。检查响应中的 `status`、`accepted` 和 `message`：
`accepted=true` 只表示请求已进入处理队列，不表示建图或定位完成。
CLI 正常退出也不代表服务接受了请求。
`operation_mode` 可能在切换完成前就显示目标模式，应等待后续新鲜的状态与里程计样本，
不能只看第一次返回。

| 状态字段 | 本流程使用的值 |
| --- | --- |
| `operation_mode` | `ODOMETRY=1`、`MAPPING=2`、`LOCALIZATION=3` |
| `odom_status` | `TRACKING=2`；`DEGRADED=3`、`LOST=4`、`RESETTING=5` 需要处理 |
| `map_status` | `MAPPING=1`、`SAVING=3`、`READY=4`、`SAVE_FAILED=5` |
| `loc_status` | `TRACKING=3`、`LOST=4`、`RELOC=5`、`RELOC_FAILED=6` |
| `current_map_name` | 保存／定位检查时必须匹配请求的地图名 |
| `sensor_timestamp_ns`、`odom_status_seq`、`num_keyframes`、`context` | 数据新鲜度、里程计状态变化、建图覆盖情况和诊断信息 |

以上数值含义适用于本文记录的接口集。使用其他版本时核对交付契约，不能把未知值解释成成功。

## 4. 进入里程计模式

此操作会改变 SLAM 状态，并可能放弃尚未保存的建图会话。满足前述条件后再执行：

```bash
timeout 15s aorta service call /slam/set_slam_mode '{"mode":1,"map_name":""}' --timeout 5
```

请求被接受后，检查多个样本：

```bash
timeout 15s aorta topic echo /slam/status --count 3
timeout 15s aorta topic echo /odometry --count 3
```

确认 `operation_mode=1`、`odom_status=2`，且里程计时间戳持续推进后再继续。
静止时位姿不变是正常现象，时间戳过期则不是。

## 5. 建图

使用空地图名开始建图：

```bash
timeout 15s aorta service call /slam/set_slam_mode '{"mode":2,"map_name":""}' --timeout 5
```

等待 `operation_mode=2`、`map_status=1`、`odom_status=2`，且里程计持续更新后再移动。
在另一个设备终端中观察有人看护的建图过程：

```bash
timeout 60s aorta topic echo /slam/status
```

观察窗口结束不会停止建图。需要更长时间时，有意识地继续观察。
覆盖门口、墙角、走廊等稳定结构，观察 `num_keyframes` 增长；关键帧数量本身不能证明地图质量足够。
按需查看一条地图预览，不持续输出大量图像字节：

```bash
timeout 15s aorta topic echo /slam/grid_map/compressed --count 1
```

若里程计重置且模式回到里程计，应将本轮建图视为中止。停止移动，等待跟踪稳定后，
再显式开始新一轮建图。

## 6. 保存并验证地图

在已建图区域内的安全位置停止移动。建图仍处于活动状态时，通过模式 2 传入选定地图名：

```bash
timeout 15s aorta service call /slam/set_slam_mode '{"mode":2,"map_name":"edu_lab_1f"}' --timeout 5
```

系统保存地图后会自动转入定位验证，不要立即再发送定位或保存请求。观察后续状态：

```bash
timeout 60s aorta topic echo /slam/status
```

- `map_status=3` 时显示“正在保存”，阻止重复请求。
- 通过 `map_status=4` 和 `current_map_name="edu_lab_1f"` 确认地图就绪；定位就绪还必须满足
  `operation_mode=3`、`loc_status=3`、`odom_status=2`，并且里程计持续更新。
- `map_status=5` 表示保存失败。超时或响应缺失表示结果未知，应先读取新鲜状态再决定是否重试。
  CLI 命令结束不会取消已经接受的操作。

## 7. 加载已有地图或请求重定位

后续会话中，选择已保存在本设备的地图：

```bash
timeout 15s aorta service call /slam/set_slam_mode '{"mode":3,"request_reloc":true,"map_name":"edu_lab_1f"}' --timeout 5
```

等待满足前述定位就绪条件。已经处于定位模式且已选中地图时，可用空地图名复用当前地图：

```bash
timeout 15s aorta service call /slam/set_slam_mode '{"mode":3,"request_reloc":true,"map_name":""}' --timeout 5
```

不要在里程计模式下通过空地图名选择地图。定位失败时，检查地图选择、传感器输入以及机器人
是否位于已建图区域。小范围调整位置也须有人看护且能够安全停止；不能仅因模式切换请求被接受
就启动导航。

## 8. 在应用中使用数据

- 同一时间只保留一个待完成的模式／保存请求。记录本地接收时间及传感器时间戳推进情况，
  为应用明确设置新鲜度与完成时限。数据缺失、过期、失败或状态未知时不开放导航。
  记录请求、响应和后续状态变化；`context` 是诊断文本，不是稳定枚举。
- 里程计含 `frame_id`／`child_frame_id`，主位姿不一定是机身位姿。
  使用成对的 `body_position_in_map` 与 `body_orientation_in_map` 获取输出的机身位姿，
  使用 `head_position_in_body` 与 `head_orientation_in_body` 获取头部相对机身的位姿；
  每组位置／朝向都必须同时存在。平移单位为米，四元数使用 x/y/z/w 分量，不能混用不同样本的字段。
  跨建图、定位或进程初始化阶段比较机身位姿前，先确认已安装版本的坐标系和原点语义。
- 里程计坐标相对于初始化参考系。原点变化后，应先转换到共同参考系，再与已保存的位置组合使用。
  `frame_id` 为 `map` 本身不是持久地图标识；不要把切换到里程计模式当作原点重置命令。
- 静态变换包含父 `frame_id`、`child_frame_id`、平移和旋转。
  订阅 `/slam/static_transforms` 并等待周期发布，新订阅者不一定立即收到快照。
  ROS bridge 通过 `/tf_static` 提供这些变换，使用 reliable、transient-local QoS 接收保留的静态快照。
  动态 `/tf` 单独从里程计派生。只读订阅命令见[接口参考](../interfaces/aorta-ros2.zh-CN.md)。
- 栅格预览的数据字节为 PNG 图像，`format` 字符串还包含
  `png;resolution=...;x_min=...;y_min=...`；显示时保留分辨率与原点元数据。
  收到缩略图不能证明地图保存或定位完成。
- 应用按需维护地图显示名、房间、区域和目标点。地图名作为标识保存，不作为设备文件路径。
  本流程选择已知地图，不引入地图列表或上传 API。

## 停止与恢复

关闭终端命令不会停止机器人或 SLAM。先用正常控制器停止移动。
需要主动放弃建图或退出定位时，确认没有进行中的保存／切换操作，并确认可以放弃未保存内容，
再使用第 4 步的里程计模式命令，检查后续新鲜状态；该命令不是急停命令。
其他应用占用会话时，不自动切换模式。
