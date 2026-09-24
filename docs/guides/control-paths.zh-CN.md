# 选择 RCP 编排还是直接调用服务

<p align="center"><a href="control-paths.md">English</a> | 中文</p>

同一套设备资源可以通过不同接口使用。RCP 提供编排与任务生命周期管理，
直接服务调用则请求某个执行模块完成一次操作；两者不会改变轨迹资源或表情 ID 的含义。

## 什么场景推荐哪一种？

| 场景 | 推荐入口 | 原因 |
| --- | --- | --- |
| 执行现成挥手、舞蹈、站起／趴下表现 | RCP DagPresetRef | 保留预设参数、姿态过渡及身体／头部／外设的配套节点 |
| 按阶段组合表情、灯光、语音与运动 | RCP DagSpec | 管理依赖、图级资源准入、反馈、取消和后台任务清理 |
| 应用独占显示控制，只需播放一次表情 | 直接 play_emotion 服务 | 无需构建图；应用负责时长、恢复与冲突处理 |
| 已掌握完整控制约定，只做一次身体操作 | 直接 lowlevel_action 服务 | 应用自行管理请求关联、姿态检查、参数、报告与恢复 |
| 应用已有控制器／调度器 | 可选直接服务 | 避免叠加调度器，但需要自行提供控制权与恢复逻辑 |
| 只知道轨迹名，不清楚策略与过渡参数 | 已提供的 RCP 预设 | 文件名不是完整运动请求 |

RCP 不会让任意运动图自动变安全。直接调用仍受设备端检查约束，
但**不会自动继承** RCP 的图级准入、资源占用、预检查编排和取消管理。
服务响应成功、Goal 被受理，都不等于物理动作完成。

## 身体：资源名相同，模式枚举不同

| 含义 | 直接 /locomotion/lowlevel_action | RCP BodyCommand |
| --- | --- | --- |
| 启动操作 | target_state = 1 | 身体任务构造启动请求 |
| 选择挥手身体策略 | mode = LowlevelActionMode.RL_ACTION_POLICY1（100） | method = BodyMethod.RL_ACTION_POLICY1（10） |
| 选择挥手身体资源 | action_path = WAVE_50hz.npz | action_path = WAVE_50hz.npz |
| 额外运控参数 | action_params_json：JSON 对象字符串 | 类型化 BodyCommand 未暴露；完整预设保留 action_params |
| 关联进度／完成 | 应用 req_id 与匹配的身体报告 | Action Goal 标识、反馈与终态，RCP 管理子请求 |
| 预检查 | pre_check 选择执行模块的准备／检查阶段 | 节点 pre_check 及图的自动批量预检查，不等于一次直接检查 |

上面的 100 和 10 属于**不同枚举域**。RCP 按名称转换，不能把 BodyMethod 数字直接发给底层服务。
policy2–4 同理：直接服务为 101–103，RCP 为 11–13。使用各自 schema 生成的命名常量。

此表只是字段映射，不是完整挥手执行示例。两种方式都在设备端加载资源，
action_path 都不会上传本地文件，也不是选择 DAG。
完整挥手使用 `DagPresetRef.relative_path = "actions/WAVE.json"`。
配套 `WAVE.csv` 使用头部接口／HeadCommand，不交给身体服务。
资源见[身体轨迹](../resources/body-trajectories.zh-CN.md)与[头部轨迹](../resources/head-trajectories.zh-CN.md)。

直接请求还可携带 aorta_header 元数据。必须明确 target_state：
默认值 0 是 OFF，不是启动。停止请求不是取消 RCP Goal，不要用它打断其他控制方。
保留原行为参数，不能为了让请求受理而削弱检查。

直接调用身体操作时，先订阅报告，再使用独立 req_id 发请求；
读取 status／error_code／error_detail，并匹配该请求的执行阶段报告。
控制器启动成功后仍可能需要观察后续姿态。遵循[运动流程](../interfaces/locomotion.zh-CN.md)，
超时意味着结果未知，不是自动重试的依据。
核心站起使用 set_run_mode，不能根据“站起”字面意思猜一个 lowlevel 模式。

## 表情：直接服务的 mode 就是资源 ID

| 含义 | 直接 /display_node/play_emotion | RCP EmotionCommand |
| --- | --- | --- |
| 显示 048_say_hi | target_state = 1，mode = 48 | emotion_id = 48；method 可为 BLINK_ONCE，非零 ID 优先 |
| 通过别名选择 | 没有 EmotionMethod 字段 | method = SAY_HI，解析为资源 ID 48 |
| 眨眼资源 000_blink_once | target_state = 1，mode = 0 | emotion_id = 0，配 BLINK_ONCE 或 UNSPECIFIED |
| 播放时间参数 | duration_ms 传给显示端 | duration_ms 转发到显示端，不是 RCP 持有时长 |
| 显示层管理 | 没有 layer 字段 | layer 选择 RCP 外设层，普通输出为 INTERACTION |
| 结束输出 | 显示端时长规则或显式 target_state = 0 | 图完成、屏障或取消时释放持有任务／层 |

直接服务的 mode 是**资源 ID**，不是 EmotionMethod 枚举数值：
SAY_HI 的枚举值是 32，但对应资源 48，不能填 32 来表达 SAY_HI。
从[表情清单](../resources/expressions.zh-CN.md)选 ID，或查询设备支持的表情。
直接 mode 的编码范围是 uint8（0–255），只有已安装的 ID 有效。

直接请求字段为 target_state（0 OFF／1 ON）、req_id（请求标识）、
pre_check（播放时为 false）、mode（资源 ID）、duration_ms（int32 播放时间参数），
以及可选 aorta_header。pre_check 成功不证明表情存在或已显示。
读取响应 status、message、error_code；成功表示启动播放，不是播放完成。

duration_ms = -1 表示播放序列后恢复默认显示。
不能将其等同于 RCP 任务完成：RCP 表情任务仍可持续持有层，直到释放。
类型化 EmotionCommand 没有 play_for_ms；
使用 DAEMON／BARRIER 划分有限阶段，或按 [NodeCommand 参考](../interfaces/rcp-commands.zh-CN.md)
使用已支持的 DSL 有限持有参数。
直接 OFF 会停止播放并恢复显示轮播，**不是**只释放某个 RCP 层。

## 同一行为不要混用控制方

RCP 图正在占用身体或显示资源时，不要直接调用服务覆盖它。
直接显示写入不在 RCP 层管理的记录中，后续层更新可能覆盖它；
直接停止也不会取消 RCP 节点。直接身体控制同样可能改变图预期的状态，却不结束其 Goal。

每个行为选择一条控制路径。切换前先完成或取消现有任务，
读取终态并检查实际设备状态，再发起新操作。图取消本身不保证机器人已经处于安全姿态。

路由与通信名称见[接口表](../interfaces/aorta-ros2.zh-CN.md)：
原生身体服务映射到 ROS 2 /sm/action/lowlevel，play_emotion 保持同名。
RCP /rcp/execute_task 是 **action**，这里两个直接接口是 **service**。

Schema：[LowlevelAction](../../schemas/aorta/schemas/service/locomotion/lowlevel_action.fbs)、
[PlayEmotion](../../schemas/aorta/schemas/service/peripheral/play_emotion.fbs)、
[RCP commands](../../schemas/aorta/schemas/service/rcp/function_input.fbs)。
