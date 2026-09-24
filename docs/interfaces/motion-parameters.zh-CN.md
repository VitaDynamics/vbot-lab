# 运动参数与通用组合

<p align="center"><a href="motion-parameters.md">English</a> | 中文</p>

按目标操作选择接口并配置参数，不需要为每个动作复制预设或编写专用教程。
本页配合 [NodeCommand 字段](rcp-commands.zh-CN.md)、[资源名目录](../resources/README.zh-CN.md)
和[直接服务与 RCP](../guides/control-paths.zh-CN.md)使用，介绍请求构造，不提供新的可运行运动示例。

## 先选操作，再选参数

| 目标 | 接口 | 用户配置的参数 |
| --- | --- | --- |
| 有界原地转向 | BaseActionCommand.ROTATE 或 NavigateCommand.ROTATE_IN_PLACE | angle_rad，有限有符号弧度，方向遵循所选服务约定 |
| 有界平移 | BaseActionCommand.MOVE_FORWARD／MOVE_BACKWARD／MOVE_LEFT／MOVE_RIGHT | distance_m，正数米值，由 method 选择方向 |
| 已有跳跃、舞蹈等身体表现 | BodyCommand，需覆盖参数时用 DslTaskCommand | 从身体资源表选择匹配策略与 action_path，再配置适用的 action_params |
| 头部姿态或轨迹 | HeadCommand | 弧度 target_angles [pitch, yaw]，或头部 CSV action_path，二选一 |
| 表情、语音与灯光 | EmotionCommand、SpeakCommand、LightCommand | 表情 ID、语音文本、灯效／颜色，详见各类型字段表 |

有跳跃轨迹不意味着可配置跳跃高度、速度或循环次数。
不要虚构 height／speed／loop 字段，也不通过更换策略编号选择动作强度。
数学上一整圈是 2π 弧度，但能编码该数值不代表服务接受该范围，或现场具有足够安全空间。
资源／模式可用性及初始姿态要求仍取决于设备。

## action_params 放在哪里

| 入口 | 填写方式 |
| --- | --- |
| RCP 类型化 BodyCommand | 没有 action_params 字段 |
| RCP DslTaskCommand | task 为 body.RL_ACTION_POLICY1、body.RL_ACTION_POLICY2、body.RL_ACTION_POLICY3 或 body.RL_ACTION_POLICY4；args_json 编码 args 对象 |
| 身体任务 args 对象 | action_path：设备资源字符串；pre_check：布尔值；action_params：对象；completion_timeout_ms：可选身体完成等待预算 |
| 直接 /locomotion/lowlevel_action | action_params_json 只编码 action_params 对象；mode、action_path 为请求的独立字段 |

RCP 中先构造
`{"action_path": selected_resource, "action_params": selected_parameters}`，
再将整个对象 JSON 序列化一次写入 args_json。参数表在 args 内保持对象，不另编码成字符串。
这里是应用变量，不是可直接填写的资源名。Python 生成字段为 argsJson／actionPath；
按 DAG 指南使用生成的 payload 对象与 union 标记。

当前 RCP 身体任务仅为 RL_ACTION_POLICY1–4 转发 action_params；
不能假定 STREAM、RL_TROT 或姿态方法使用这些覆盖参数。
pre_check 是准备／检查阶段，不是通用的只读 dry-run。
completion_timeout_ms > 0 覆盖身体完成等待预算，省略／非正值使用任务默认；
它不替代 DAG 节点的 execution_timeout_ms。

action_params 每个值只能是布尔、数字或字符串等标量。
底层标量合并器不转发数组、嵌套对象或 null。
使用真实布尔、有限数字及准确字符串，不把数字编码成字符串。
未知键不是能力发现机制：能被转发不表示所选动作会使用。

请求值覆盖动作已有配置。省略表示继承，不是“沿用上一个预设的值”，也不代表通用安全默认值。
本流程不需要在路径中嵌入参数语法，action_path 保持资源名即可。

## 过渡参数

这些参数适用于身体动作选用的踏步过渡路径，覆盖参数不能让控制器凭空支持新的姿态转换。
下表区分请求省略与实现回退值，不是推荐的运动参数组合。

| 参数 | 类型 | 默认／省略行为 | 含义及约束 |
| --- | --- | --- | --- |
| `transition_stepping_enabled` | bool | false 回退值，设备动作配置可覆盖 | 启用踏步过渡策略，不是坐下请求，也不是任意姿态转换器。 |
| `transition_validation_mode` | string | 设备配置；请求省略即不覆盖 | required 或 skip；required 请求过渡后检查，skip 跳过。不能为了绕过拒绝而改为 skip。 |
| `transition_validation_require_ramp` | bool | 后检查定义默认为 true | 启用后检查时，是否要求坡度估计／检查。 |
| `transition_validation_require_payload` | bool | 后检查定义默认为 true | 启用后检查时，是否要求负载估计／检查。 |
| `transition_validation_ramp_angle_deg` | number | 设备过渡配置 | 坡度阈值，度。填写有限且符合使用条件的阈值；没有统一的用户安全上限。 |
| `transition_validation_payload_min_kg` | number | 设备过渡配置 | 估计负载下限，kg；估计值可带符号，不是机器人额定载重。 |
| `transition_validation_payload_max_kg` | number | 设备过渡配置 | 估计负载上限，kg；同时填写时必须 >= min，不通过放宽阈值强行执行。 |
| `transition_validation_estimator_timeout_s` | number | 设备过渡配置 | 估计器等待预算，秒；使用有限正数，区别于节点 execution_timeout_ms。 |

显式填写检查覆盖参数而不填 mode，可能启用后检查；显式 skip 会禁用。
请求未填的数值阈值由设备过渡配置解析，不能从另一个动作照搬，
也不能为了让拒绝的请求执行而削弱检查。

## 动作避障检查参数

这些参数定义分方向的避障检查盒，不是自动路径规划，也不是从轨迹计算出的扫掠体积。
尺寸需要覆盖实际动作的空间需求。

| 键 | 类型 | 约束／省略行为 |
| --- | --- | --- |
| `obstacle_avoidance_enabled` | bool | 省略表示未显式请求此动作级检查，false 表示跳过 |
| `obstacle_avoidance_<direction>_enabled` | bool | 总开关为 true 时，front、rear、left、right、top 每组必填 |
| `obstacle_avoidance_<direction>_length_m` | number | base_link 下的盒 X 向尺寸，米 |
| `obstacle_avoidance_<direction>_width_m` | number | base_link 下的盒 Y 向尺寸，米 |
| `obstacle_avoidance_<direction>_height_m` | number | 盒 Z 向尺寸，米，起点为配置的动作检查 Z 原点 |

开启时填写五组完整字段，加总开关共 21 个标量键，至少启用一个方向。
启用方向的尺寸必须有限且为正；关闭方向也要提供尺寸字段，可为 0。
不能使用嵌套的 directions 对象。配置的 Z 起点不一定是地面，
不存在适合所有动作的同一套尺寸。
RCP 的动作避障功能开关可能使请求 true 最终不生效，不能仅凭请求字段就认定实际进行了避障检查。

## 通用编排模式

1. 选择操作并确认支持的初始状态；只有姿态转换约定要求时才执行独立准备任务。
   “坐下”等名字不是状态检查。
2. 构建 DagSpec，将不可缺少的输出列入必需资源，必须说话时包括 AUDIO_OUT。
   保持 skip_batch_pre_check 为 false，并保留必要前置条件。
3. 表情／灯光使用 DAEMON；有限运动与语音使用 NORMAL，按需求设置共同依赖。
   需要边运动边说话时，不让语音依赖运动完成。
4. 清理 BARRIER 同时依赖有限运动与语音。它释放图内全部已持有 daemon，
   不是选择性停止；继续读取 Goal 终态。
5. 触发、去抖、冷却、离开检测留在应用层。失败／超时后先处理活动 Goal 与实际设备状态，
   再允许下一轮触发。

这是一种组合方式，不保证各输出帧级同步。语音可能比动作长；
若要求整段语音落在运动区间内，需要根据所选操作与输出事件明确时序，
不能只依赖并行节点。图完成或控制器启动报告也不等于某个具体物理姿态已经达成。

用户在运动／资源约定内选择支持的参数。若某资源的起始姿态、策略兼容性或必需参数没有说明，
需先补齐这些约定，不能靠试错猜参数。
现成预设只是便捷入口，不是自定义图的唯一表达方式。
