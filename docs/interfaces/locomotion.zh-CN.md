# 运动状态、报告与控制输入

<p align="center"><a href="locomotion.md">English</a> | 中文</p>

调用方式选择与字段对应见[直接服务与 RCP](../guides/control-paths.zh-CN.md)。

本功能域用于观察姿态／动作状态、跟踪请求的完成情况，或接入明确要求的控制输入。

Python 和 C++ SDK 实现见 [locomotion Recipe](../../recipes/locomotion/README.zh-CN.md)，包含源码、Bazel 目标、离线预览与显式设备运行。接口语义以下文为准。
在选定的 `foot_quadruped` EDU 设备上完成[设备 shell 配置](../getting-started/device-environment.zh-CN.md)。
准确类型与 ROS 映射见[接口表](aorta-ros2.zh-CN.md)，不能混淆输出 topic 与控制输入。

## 路由与数据含义

| Aorta topic | 方向 | 定义与用途 |
| --- | --- | --- |
| `/locomotion/status` | 订阅 | `posture`、`motion`、`current_action`、`heartbeat_seq`、`stamp_ns`；观察当前姿态和新鲜度 |
| `/locomotion/body_action_status` | 订阅 | 机身执行 `status`、`mode`、`mode_str`、`modify_source`；是模式快照，不是任务完成结果 |
| `/locomotion/head_status` | 订阅 | 头部 `state`、`current_action`、`pending_action`、`fault_reason`；显示头部活动与故障 |
| `/locomotion/body/task_report` | 订阅 | 按 `req_id` 关联的机身任务终态；检查 `status`、`reason` 及可选类型化结果 |
| `/locomotion/head/task_report` | 订阅 | 同样关联方式的头部任务终态，不能与无关的机身请求匹配 |
| `/locomotion/action_report` | 订阅 | 机身／头部动作结果：`action_family`、`action_name`、`terminal_status`、`req_id`、`error_code`、`reason` |
| `/locomotion/event` | 订阅 | 包含 `req_id`、`event_name`、动作、成功标志、原因和参数的运行事件，是上下文而不是周期位姿 |
| `/locomotion/joy` | 发布 | 摇杆轴／按键输入，由 ROS 摇杆输入桥接，可触发运动 |
| `/locomotion/velocity_command` | 发布 | 速度指令，由 ROS 速度输入桥接，可触发运动 |

表中均为 pub/sub。机身／头部／运行模式／运行时控制 service 是独立的请求／响应接口，
见 [service 表](aorta-ros2.zh-CN.md)。

## 最小只读流程

```bash
timeout 15s aorta schema get /locomotion/status --describe
timeout 15s aorta schema get /locomotion/body/task_report --describe
timeout 15s aorta topic echo /locomotion/status --count 1
```

1. 先订阅状态，确认心跳／时间字段保持新鲜。区分未知、过渡、恢复和紧急状态，不能都视为空闲可执行。
2. 用户要求操作时，先建立对应报告订阅，再发送请求，并保留 service 契约使用的请求 ID。
3. Service 启动回复只表示是否接纳，不表示完成。按确切请求匹配终态，
   再检查成功／失败／取消与结构化结果；单纯变为空闲不能证明请求动作成功。
4. 任务报告先检查 `result_type` 再读取 `result`。运动结果含 `stage` 时区分准备与执行。
   使用稳定的状态／原因字段决策；`diagnostic` 是说明文字，不是机器可读错误码。
5. 请求 ID 为空的动作报告不能安全地结束某个指定请求。
   每个请求设定超时，没有匹配终态时报告结果未知，不盲目重发可能仍在执行的操作。

## 控制输入行为

### 站起与趴下

核心站起操作使用 `/locomotion/set_run_mode`，选择 `MANUAL=0` 并显式设置
`traction_user_param.is_user_param=false`。趴下使用 `/locomotion/lowlevel_action`，
设置 `target_state=1` 与 `SAFE_LAYDOWN_SEQUENCE=4`。这与设备 harness 的 `pose`
动作背后的运控操作一致；直接调用 service 不包含预设的头部、灯光或声音行为。
不要仅因为名称与目标姿态相似，就替换为 `FIXED_STAND` 或 `FIXED_LAYDOWN`。

MANUAL 模式的执行任务报告成功表示控制器已启动，不表示物理站起完成。
还需观察后续姿态并在现场确认稳定性。[示例](../../recipes/locomotion/README.zh-CN.md)
说明了各操作的完成检查与超时处理。

### 摇杆与速度

发布前阅读[控制 topic 保护说明](aorta-ros2.zh-CN.md)，确认唯一控制方、机器人模式、
有人监护的安全区域与停止方式。构造指令前检查交付的轴／按键契约、允许的速度分量、限制与 QoS。
通用 Joy 或 Twist 消息不是完整的控制器规格。

ROS bridge 提供占用管理、校验与超时处理；直接使用 Aorta 的发布者不能假定继承这些保护。
退出时按控制流程停止，检查后续机器人状态，再释放发布者。仅关闭终端不能保证物理停止。

## 控制启停服务

`/locomotion/control_enable` 用于在电源切换期间暂停／恢复控制循环和电机通信。
[Schema](../../schemas/aorta/schemas/service/locomotion/control_enable.fbs) 定义请求
`aorta.services.locomotion.ControlEnableRequest` 和响应
`aorta.services.locomotion.ControlEnableResponse`，两者均包含 `aorta_header`。
请求的 `enable=true` 恢复控制，`enable=false` 暂停控制。ROS 2 在同名服务使用
`std_srvs/srv/SetBool`，请求 `data` 对应 Aorta 的 `enable`。
Aorta 返回 `status` 和 `message`；ROS 返回 `success` 和 `message`，
其中 `ServiceStatus.SUCCESS=0` 表示成功。

[Bridge 路由](../../schemas/ros2/routes.json) 设置 25000 ms 服务超时、
最多一个在途请求、单写者、每秒 5 个请求、突发上限 10、请求大小上限 4096 字节。
QoS 为 reliable、volatile、keep-last、深度 4。未配置 deadman 超时或
zero-on-deadman 指令。只检查类型，不调用服务：

```bash
timeout 15s ros2 interface show std_srvs/srv/SetBool
```

## 跟随与导航模式服务

`/function/following` 控制跟随／导航模式。
[Schema](../../schemas/aorta/schemas/service/vln/control_following.fbs) 定义请求
`aorta.services.vln.ControlFollowingRequest` 和响应
`aorta.services.vln.ControlFollowingResponse`，两者均包含 `aorta_header`。
ROS 2 在同名服务使用 [function_msgs/srv/ControlFollowing](../../schemas/ros2/function_msgs/srv/ControlFollowing.srv)。
成功回复表示请求已获确认，不表示到达目标。

| 请求字段 | 含义 |
| --- | --- |
| `target_state` | 0=OFF、1=ON；bridge 只允许这两个值 |
| `mode` | Bridge 允许域为 0–9，具名常量见下文 |
| `req_id` | 请求跟踪 ID |
| `pre_check` | 为 true 时只执行准备／检查阶段 |
| `x`, `y`, `yaw` | 目标位置与到达时的偏航角（弧度）；仅用于 NAV_TO_POINT |
| `goal_frame` | 设置为 `global` 时使用全局／世界坐标；默认 `local` |
| `stop_distance` | 到达阈值覆盖值；0.0 使用配置默认值 |
| `max_xvel` | NAV_TO_POINT 最大前向速度覆盖值；<=0 使用默认值（ROS 注释指定 0.5 m/s） |
| `prompt` | 语义导航指令；Aorta 注释包括 SYNC/ASYNC_SEMANTIC_NAV 和 CIVIC_NAV，ROS 注释列出模式 6/7 |
| `source` | 仅 Aorta 支持的 ControlSource：UNKNOWN=0、RCP=1、FSM=2、BASE_ACTION=3、ODOM_QR=4 |
| `waypoints` | 仅 Aorta 支持的 CIVIC_NAV 路径提示：base_link 下的 `x1,y1,...,x40,y40` |

ROS 服务声明 `STOP=0`、`FOLLOWING=1`、`ROAMING=2`、`NAV_TO_POINT=3`、
`COME_TO_ME=4`、`WALK=5`、`SYNC_SEMANTIC_NAV=6`、`ASYNC_SEMANTIC_NAV=7` 和
`ACCOMPANY=8`。虽然其模式注释只列出 0–8，路由允许 0–9；共享的
[FollowMode Schema](../../schemas/aorta/schemas/shared/follow_common/follow_common.fbs)
定义 `CIVIC_NAV=9`，ROS 服务中没有对应具名常量。

Aorta 返回 `status`、`message`、`error_code` 和 `warning`。ROS 返回 `success`、
`message` 和 `error_code`；成功映射为 `ServiceStatus.SUCCESS=0`，保留错误码数值域。
仅 Aorta 提供的 `warning` 描述并发控制方冲突，但请求仍获遵从。
ROS 请求没有 `source` 或 `waypoints`。

[Bridge 路由](../../schemas/ros2/routes.json) 设置 5000 ms 超时、最多一个在途请求、
单写者、每秒 5 个请求、突发上限 10、请求大小上限 65536 字节。
QoS 为 reliable、volatile、keep-last、深度 4。`x`、`y`、`yaw`、`stop_distance` 和
`max_xvel` 必须均为有限值。未配置 deadman 超时或 zero-on-deadman 指令。
只检查类型，不提交指令：

```bash
timeout 15s ros2 interface show function_msgs/srv/ControlFollowing
```

## 解释与排障

机身状态的模式编号和机身控制 service 的模式编号属于不同枚举域，不能从一方抄到另一方。
没有任务时事件流安静属于正常情况。状态停止更新、请求不匹配或出现故障时需排查，
不自动切换模式或重启运动服务。Bridge 的 `armed` 表示准备好评估指令，不表示运动成功。
限时读取退出码 `124` 表示没有获得样本，不能因此允许控制动作。
