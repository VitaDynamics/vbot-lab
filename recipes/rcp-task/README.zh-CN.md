# 提交 RCP DAG

<p align="center"><a href="README.md">English</a> | 中文</p>

[Recipes 索引](../README.zh-CN.md) · [Python](main.py) · [C++](main.cc)

自定义图与现成行为见 [DAG 编写指南](../../docs/guides/rcp-dag.zh-CN.md)
及[RCP 预设目录](../../docs/guides/rcp-presets.zh-CN.md)。

接口: `/rcp/execute_task` — action.

生成类型: `aorta.action.rcp.ExecuteTaskGoal`, `aorta.services.rcp.DagSpec`, `aorta.services.rcp.DagNode`.

提交两个顺序执行的 Sleep 节点（second 依赖 first），不包含运动命令，但仍会占用任务执行器，运行前确认没有冲突任务。`make_goal()` 使用生成的对象类型演示 DagSpec union、NodeCommand.SleepCommand 类型标记、NORMAL 生命周期和依赖关系，不发送无类型 JSON。每个 Sleep 为 1–10000 ms。

## Python：构建与离线预览

```bash
bazel build //recipes/rcp-task:main
bazel run //recipes/rcp-task:main
```

默认只输出 JSON 请求计划，不安装 SDK、不连接设备、不发送请求。

## Python：在设备上运行

先完成 [Python 部署流程](../../docs/development/python-deployment.zh-CN.md)：传输本示例及配套 wheel，并在设备创建 venv。保持位于部署所得的应用目录（APP_DIR），激活该目录的 venv、配置设备环境后运行：

```bash
python -m recipes.rcp-task.main --execute --duration-ms 500 --timeout 10
```

要求提供方支持取消。输出包含 `task_id`、`goal_id`、节点进度和终态，不输出 goal secret。应检查终态 SUCCEEDED 且 error_category=0，不能只看提交受理。用较长的非运动 DAG 演示取消：

```bash
python -m recipes.rcp-task.main --execute --duration-ms 5000 --cancel-after 1 --timeout 15
```

取消请求的确认不代表终态。任务可能先自然完成，应以返回状态为准。超时或中断时，如果已取得 handle，程序会尝试取消并限时等待终态。受理阶段超时可能拿不到 handle，此时应使用已输出的标识检查任务，不要重复提交 DAG。提供方拒绝或并发任务拒绝属于错误，不会自动重试。

## C++

先按 [C++ SDK 指南](../../packages/aorta/cpp/README.zh-CN.md)准备配套 SDK／Schema 压缩包与编译环境，设置两个发布制品路径。在构建机上显式构建 C++ 目标，预览也需要链接 SDK，但不会创建 Node 或访问设备：

```bash
bazel build //recipes/rcp-task:main_cpp
bazel run //recipes/rcp-task:main_cpp
```

按[二进制部署流程](../../packages/aorta/cpp/README.zh-CN.md#在机器人上运行)设置 RECIPE=rcp-task 并完成部署。以 vbot 身份 SSH 登录后，进入部署所得应用目录，按流程配置 shell 和动态库路径，满足上面的任务前提后直接运行可执行文件：

```bash
./bin/rcp-task --execute --duration-ms 500 --timeout 10
```

设备无需 Bazel、编译器或仓库副本。C++ 使用与 Python 相同的路由、操作许可和完成条件；只读订阅不会发布指令。

[goal.h](goal.h) 使用生成的 C++ `*Msg` 和 variant 构建相同的两个 Sleep 节点。输出反馈进度和终态；取消示例：

```bash
./bin/rcp-task --execute --duration-ms 5000 --cancel-after 1 --timeout 15
```

## 完成、失败与退出

输出为逐行 JSON；退出码 0 表示完成本示例的操作（离线预览也返回 0），1 表示运行失败或超时，2 表示参数不合法，130 表示中断。检查 execute 参数和输出语义，不要把离线预览视为在线成功。所有等待都有上限；订阅队列溢出会报错，不把丢失样本当完整数据。退出时关闭订阅、客户端及 Node。

测试说明见 [Recipes](../README.zh-CN.md)；默认测试不连接或操作设备。
