# 执行本体动作

<p align="center"><a href="README.md">English</a> | 中文</p>

[Recipes 索引](../README.zh-CN.md) · [Python](main.py) · [C++](main.cc)

接口: `/locomotion/set_run_mode`, `/locomotion/lowlevel_action`, `/locomotion/body/task_report`, `/locomotion/action_report`, `/locomotion/status` — service + pub/sub.

生成类型: `aorta.services.locomotion.SetRunModeRequest`, `aorta.services.locomotion.LowlevelActionRequest`, `aorta.topic.task.TaskReport`, `locomotion.ActionReport`, `locomotion.LocomotionStatus`.

执行前须获得授权，现场有人监护，周围空间安全，具备明确停止方式，且没有其他控制者或任务。示例先要求收到不同序号的两个心跳，并确认当前处于空闲的站立或趴下姿态。这只是保守的程序前置检查，不是安全联锁；这里的 `safe-stop` 不是紧急停机工具。

| 模式 | 请求 |
| --- | --- |
| `stand` | `/locomotion/set_run_mode`：`MANUAL=0`、`target_state=1`，显式设置 `traction_user_param.is_user_param=false` |
| `lie-down` | `/locomotion/lowlevel_action`：`SAFE_LAYDOWN_SEQUENCE=4`、`target_state=1` |
| `safe-stop` | `/locomotion/lowlevel_action`：`SAFE_STOP_SEQUENCE=3`、`target_state=1` |

站起和趴下使用设备 harness 的 `pose` 动作背后的核心运控操作，不执行配套的头部、灯光或声音行为。`FIXED_STAND` 与 `FIXED_LAYDOWN` 是不同操作，不应替代上述请求。

## Python：构建与离线预览

```bash
bazel build //recipes/locomotion:main
bazel run //recipes/locomotion:main -- --mode stand
```

默认只输出 JSON 请求计划，不安装 SDK、不连接设备、不发送请求。

## Python：在设备上运行

先完成 [Python 部署流程](../../docs/development/python-deployment.zh-CN.md)：传输本示例及配套 wheel，并在设备创建 venv。保持位于部署所得的应用目录（APP_DIR），激活该目录的 venv、配置设备环境后运行：

```bash
python -m recipes.locomotion.main --mode stand --confirm-motion --execute --timeout 20
```

程序在发送请求**前**建立报告订阅，提交前输出唯一 `req_id`。service 响应中的 status/error_code 为零只表示受理。

- `stand`：等待相同请求标识的 `/locomotion/body/task_report`，要求 `LocomotionTaskResult.stage=EXECUTE` 且状态成功。这表示模式已启动，不表示物理站起完成。随后观察连续三个心跳推进的状态样本，要求站立姿态、空闲运动状态且 `current_action=RL_TROT`。状态消息没有请求标识，因此输出明确标注为观察结果，不作为因果关联的完成报告；程序退出后控制器仍持续运行。
- `lie-down` / `safe-stop`：等待相同请求标识且属于 BODY 的 `/locomotion/action_report`，要求 `terminal_status=SUCCESS` 且 `error_code=0`。

实际姿态和稳定性仍需现场确认。超时、中断或响应丢失时，结果可能未知，设备也可能仍在动作。需检查状态并使用既定停止方式；退出程序不会取消运动。示例不盲目重试或下发兜底指令，也不发布速度或摇杆指令。

## C++

先按 [C++ SDK 指南](../../packages/aorta/cpp/README.zh-CN.md)准备配套 SDK／Schema 压缩包与编译环境，设置两个发布制品路径。在构建机上显式构建 C++ 目标，预览也需要链接 SDK，但不会创建 Node 或访问设备：

```bash
bazel build //recipes/locomotion:main_cpp
bazel run //recipes/locomotion:main_cpp -- --mode stand
```

按[二进制部署流程](../../packages/aorta/cpp/README.zh-CN.md#在机器人上运行)设置 RECIPE=locomotion 并完成部署。以 vbot 身份 SSH 登录后，进入部署所得应用目录，按流程配置 shell 和动态库路径，满足上面的任务前提后直接运行可执行文件：

```bash
./bin/locomotion --mode stand --confirm-motion --execute --timeout 20
```

设备无需 Bazel、编译器或仓库副本。C++ 使用与 Python 相同的路由、操作许可和完成条件；只读订阅不会发布指令。

## 完成、失败与退出

输出为逐行 JSON；退出码 0 表示完成本示例的操作（离线预览也返回 0），1 表示运行失败或超时，2 表示参数不合法，130 表示中断。检查 execute 参数和输出语义，不要把离线预览视为在线成功。所有等待都有上限；订阅队列溢出会报错，不把丢失样本当完整数据。退出时关闭订阅、客户端及 Node。

测试说明见 [Recipes](../README.zh-CN.md)；默认测试不连接或操作设备。
