# 传感器与硬件遥测

<p align="center"><a href="sensors.md">English</a> | 中文</p>

Python/C++ 只读示例见 [sensors Recipe](../../recipes/sensors/README.zh-CN.md)，包含 Bazel 构建、离线预览及显式设备读取。

这些输出用于传感器接入、设备看板和硬件故障提示，均为 pub/sub 订阅，
不是传感器配置或执行器指令。先完成[设备 shell 配置](../getting-started/device-environment.zh-CN.md)。
范围为 `foot_quadruped` EDU／DEV；准确的 Aorta／ROS 类型及映射见[接口表](aorta-ros2.zh-CN.md)，
字段以已安装固件交付的 Schema 为准。

## 路由与数据含义

| Aorta topic | 含义与关键字段 | 典型用途 |
| --- | --- | --- |
| `/bms_state` | 电池 `voltage_mv`、带符号的 `current_ma`、`soc_percent`、告警、充电器连接及温度／单体电压数组 | 电池看板；显式把 mV/mA 转为 V/A，按有效元素数量读取，忽略填充尾部 |
| `/imu_raw` | 机身 IMU 朝向、角速度、线加速度、协方差、`timestamp` 和 `frame_id` | 保留来源坐标系；换算前确认所用固件发布的角速度／加速度单位 |
| `/lidar_imu` | 雷达侧 IMU，具有自身时间戳和坐标系 | 传感器融合；没有坐标变换时不能直接替代机身 IMU |
| `/lidar_points` | 点云 `fields`、`point_stride`、`data`、时间戳、坐标系与位姿 | 空间处理；按字段偏移、类型和步长解码，不能强制转换成固定 XYZ 布局 |
| `/lidar_packets` | 带时间戳的原始协议字节 `data` | 使用匹配交付雷达型号的解码器做驱动级处理，不是另一种 PointCloud 布局 |
| `/lidar_diagnostic_status` | `status` 数组，包含具名诊断项、级别、消息和键值详情 | 显示 OK/WARN/ERROR/STALE；诊断不是点云样本 |
| `/uwb/ranging` | `distance`／`distance_filtered` 单位米；`angle`、`pitch`、`angle_filtered` 单位度；RSSI 与 `pos_confidence`（0～100） | 相对标签测距，不是人在地图中的坐标 |
| `/uwb/state` | 连接／测距 `state`、模式、遥控器电量百分比及充电状态 | 使用测距前区分已配对、测距中与空闲 |
| `/uwb/head_touch` | 触摸事件，`total_count` 和 `since_boot_count` 均包含当前事件 | 事件触发交互；本次启动计数在重启后重新开始 |
| `/lowlevel/servo_status` | 按 ID／名称识别的逐舵机 `statuses`，含有效位、角度、温度和电气数据 | 关节看板；角度为度，角速度为度/秒，先检查每组有效位再读取字段 |
| `/gnss/fix` | 原始定位状态、经纬度（度）、高度（米）、协方差、采集时间及有效位 | 地理位置；无定位或未知协方差不能当作有效的零位置 |
| `/gnss/fusion` | 融合地理位置，含 `valid`、`source`、采集时间和位置 | 粗粒度全局定位；检查来源与新鲜度，不假定一定是新的卫星定位 |

## 电池字段与缺失值

原生 Aorta 电池数据以 [BmsState Schema](../../schemas/aorta/schemas/topic/bms/bms_state.fbs) 为准。
充电器连接、输入来源与充电进度需要分开判断：

| 字段 | 含义 |
| --- | --- |
| `charge_state` | UNKNOWN=0、IDLE=1、CHARGING=2、FULL=3；表示充电进度，不表示输入来源 |
| `charge_source` | NONE=0、PD=1、DOCK=2、UNKNOWN=255；UNKNOWN 不能当作未接充电器 |
| `pd_role` | UNKNOWN=0、SINK=1、SOURCE=2；只有同一条消息中 `charge_source=PD` 且 `pd_role=SINK` 才确认 PD 受电 |
| `alarm`、`alarm_full` | `alarm` 是兼容旧接口的低 16 位。优先使用可选的 32 位 `alarm_full`，包括有效的零；缺失时才回退到旧值 |
| `p_positive_voltage_mv`、`recharge_thresh_percent` | 电池回报的可选扩展电压（mV）与回充阈值（百分比） |
| `record_counts_start`、`record_counts_end` | 电池回报的可选记录计数；存在时保留零值 |
| `smart_charge_soc_limit`、`smart_charge_enabled` | 电池回报的可选智能充电 SOC 上限（80–100%）与开关；`false` 是有效的关闭状态 |

旧发布端、不支持的电池固件或查询失败可能不提供可选字段。Python 返回 `None`，C++ 返回可选值；
输出 JSON 时保留为 `null`，不能替换成 `0` 或 `false`。配置请求成功不等于电池已读回该设置。
当前 ROS `lowlevel_msg/msg/BmsState` 不包含这些原生扩展字段，不要根据充电连接标志推算。
[电池 Recipe](../../recipes/sensors/README.zh-CN.md) 的两种语言实现均保留上述区别。

## 读取与使用

登录后统一发现接口，再检查任务所需路由并采样小消息。以电池看板为例：

```bash
timeout 15s aorta topic list
timeout 15s aorta schema get /bms_state --describe
timeout 15s aorta topic echo /bms_state --count 1
```

惯性数据应用改用以下命令，无需逐个采集全部传感器：

```bash
timeout 15s aorta schema get /imu_raw --describe
timeout 15s aorta topic echo /imu_raw --count 1
```

1. 使用所选路由的 Schema 解码，把单位、坐标系、有效位和采集时间戳与数值一起保留。
   发布时间不等于采集时间。
2. 为各数据流配置有界缓冲与适合应用的新鲜度期限。无效或过期数据标为不可用，不能补零当测量。
3. 通过时间戳与已知变换关联传感器，不按消息到达顺序配对；相减前确认时钟可比较。
4. 触摸应用先订阅再交互，并对收到的事件去重；使用计数时考虑重启。两次触摸之间无消息属于正常情况。
5. 页面退出或程序停止时关闭订阅；仅在需要时采集原始点云或数据包，它们通常明显大于状态消息。

## ROS 转换与排障

ROS 映射的字段布局可能不同。融合 GNSS 拆分为定位输出与 fusion-extra 输出；
电池固定数组和部分 UWB 可选数据也需注意。单独检查 ROS 类型并遵循[转换说明](aorta-ros2.zh-CN.md)。

没有样本不代表传感器故障。先检查 shell、路由、Schema、发布者活动与输入条件：
UWB 需要标签连接／测距会话，GNSS 合法情况下也可能报告无定位。
点云缺失时结合雷达诊断检查，不自动重置硬件或调整设备服务。

限时命令退出码 `124` 表示等待超时。报告数据不可用并释放资源，不进入无限重试循环。
