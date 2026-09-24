# 系统状态、显示与耳灯

<p align="center"><a href="system-peripherals.md">English</a> | 中文</p>

调用方式选择与字段对应见[直接服务与 RCP](../guides/control-paths.zh-CN.md)。

Python/C++ 只读示例见 [system-peripherals Recipe](../../recipes/system-peripherals/README.zh-CN.md)，包含 Bazel 构建、离线预览及显式设备读取。

本功能域用于系统状态看板、显示观察与明确要求的灯光交互。
在 `foot_quadruped` EDU 上完成[设备 shell 配置](../getting-started/device-environment.zh-CN.md)。
准确类型与 ROS 映射见[接口表](aorta-ros2.zh-CN.md)。系统／显示输出只读，耳灯调制是控制输入。

## 路由与数据含义

| Aorta topic | 方向 | 定义与用途 |
| --- | --- | --- |
| `/system/sm_status` | 订阅 | 系统类别、流程状态、活跃状态／路径、级别、心跳与描述数据；区分状态、OTA 和告警消息 |
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
