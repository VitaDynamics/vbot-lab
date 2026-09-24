# RCP 任务与追踪

<p align="center"><a href="rcp.md">English</a> | 中文</p>

本功能域包含任务 action 和只读追踪输出。先在 `foot_quadruped` EDU 上完成
[设备 shell 配置](../getting-started/device-environment.zh-CN.md)。任务执行可能改变设备状态；
查看追踪与检查 provider 不会提交任务。类型及映射总览见[接口表](aorta-ros2.zh-CN.md)。

编排从 [DAG 编写指南](../guides/rcp-dag.zh-CN.md)与[RCP 预设目录](../guides/rcp-presets.zh-CN.md)开始，
了解节点字段、预设参数、依赖及灯光／表情生命周期。
各命令的完整字段见 [NodeCommand 参考](rcp-commands.zh-CN.md)，标识清单见独立的[设备资源](../resources/README.zh-CN.md)。
[Python／C++ 示例](../../recipes/rcp-task/README.zh-CN.md)提供非运动任务的提交、反馈与取消流程。

## 任务定义与使用

`/rcp/execute_task` 是 **action**，不是 topic 或 service。
它接受 DAG 或预设，提供进度反馈、终态结果，并支持取消。

| Aorta action | Goal／result／feedback 数据根类型 | ROS 2 action | ROS 2 action 类型 |
| --- | --- | --- | --- |
| `/rcp/execute_task` | `aorta.action.rcp.ExecuteTaskGoal` / `aorta.action.rcp.ExecuteTaskResult` / `aorta.action.rcp.ExecuteTaskFeedbackData` | `/rcp/execute_task` | `aorta_msgs/action/ExecuteTask` |

仅检查 provider 与交付类型，不提交目标：

```bash
timeout 15s aorta action list
timeout 15s aorta action info /rcp/execute_task
timeout 15s ros2 action list -t
timeout 15s ros2 interface show aorta_msgs/action/ExecuteTask
```

Goal 包含 `source`、带类型标记的 `input` 及可选的 `user_interaction_context`。
原生 Aorta JSON 使用匹配的 `input_type` 与 `input`。
ROS 交付类型则提供 `INPUT_TYPE_DAG_SPEC` 与 `input_dag_spec`，或
`INPUT_TYPE_DAG_PRESET_REF` 与 `input_dag_preset_ref`。两种表示不能直接交换载荷。

执行用户请求的任务前，先检查 DAG 的每个节点与前置条件：DAG 可能触发运动、语音、灯效等设备变化。
明确提交后保留返回的目标标识。接受不等于完成，需观察反馈，再检查 action 终态与结果。
反馈包含 `current_node`、`completed_nodes`、`total_nodes`、`progress_pct`；
结果包含 `duration_ms` 和 `error_category`。

ROS bridge 同时只允许一个目标执行，另一个会以 `GOAL_BUSY` 拒绝。
原生 provider 通过 action info 公布自身并发与结果保留设置，不要把这些数值套用到 ROS bridge。
取消是请求：需等待取消终态，或处理取消被拒／目标已经完成的情况。
客户端超时或关闭终端不等于任务被取消。应在 provider 保留期内获取结果，
使用 `/rcp/trace` 辅助了解任务事件，不能用它代替终态结果。

## 追踪 topic 的定义与使用

`/rcp/trace` 是只读 pub/sub 输出，Aorta 类型为 `aorta.topic.rcp.TraceEvent`，
映射到同名 ROS topic，类型为 `function_msgs/msg/TraceEvent`。

- `request_id` 用于请求关联，`trace_id`、`parent_id`、`task_level`、
  `subtask_name` 用于组织嵌套任务。不要只按相近到达时间拼接两条任务。
- `event_type` 按交付枚举解释，`timestamp` 是 ISO 8601 事件时间字符串。
  需要时间比较时先解析时间戳，不按本地接收顺序判断因果。
- `payload_json` 为事件相关的 JSON 内容，不预设所有事件都有相同字段。
  先分派事件类型，再检查字段存在性；未知类型可保留展示，但不能默认当作成功。
- 先订阅，再执行明确要求的任务；仅更新对应请求的进度视图，
  并用 action 终态／结果结束该任务。任务不活动时没有追踪消息属于正常情况。

只读示例：

```bash
timeout 15s aorta schema get /rcp/trace --describe
timeout 15s aorta topic echo /rcp/trace --count 1
```

读取不会创建任务，退出码 `124` 不表示执行器故障。
如需停止任务，显式请求取消并检查终态，然后清理订阅与本地目标状态；
不能因停止追踪订阅而认为任务已停止。结果超过保留期或断线导致缺失时报告结果未知，
不要自动重新执行整张 DAG。
