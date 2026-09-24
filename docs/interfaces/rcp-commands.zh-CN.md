# RCP NodeCommand 字段参考

<p align="center"><a href="rcp-commands.md">English</a> | 中文</p>

先阅读 [Goal 与 DAG 教程](../guides/rcp-dag.zh-CN.md)。本页解释 command 对象的所有字段。
command_type 选择类型，command 放对应对象；例如 SleepCommand 对应 `{"duration_ms":500}`。
以下默认值来自 [Schema](../../schemas/aorta/schemas/service/rcp/function_input.fbs)，不一定等于所有底层服务默认。
枚举有定义不代表所有机器人配置都支持；特别是视觉导航、运控模式需具备对应服务与运行条件。

## 类型、默认值与范围

bool 只填 true／false；int 为有符号 32 位（−2,147,483,648…2,147,483,647），
uint 为无符号 32 位（0…4,294,967,295），float 为 32 位浮点数，应用应填写有限数。
字符串／数组无显式值时为省略。物理范围不等于存储范围；下表优先给业务范围，未定义统一限值的字段明确说明。
使用命名枚举，不跨接口复制数值；特别是 BodyMethod 与底层运控枚举的数值不同。

- [BodyCommand](#bodycommand)
- [HeadCommand](#headcommand)
- [LightCommand](#lightcommand)
- [EmotionCommand](#emotioncommand)
- [SpeakCommand](#speakcommand)
- [VlnCommand](#vlncommand)
- [VlnSessionCommand](#vlnsessioncommand)
- [LocomotionCommand](#locomotioncommand)
- [BaseActionCommand](#baseactioncommand)
- [NavigateCommand](#navigatecommand)
- [SleepCommand](#sleepcommand)
- [BarrierCommand](#barriercommand)
- [DslTaskCommand](#dsltaskcommand)

## BodyCommand

控制身体模式或播放匹配轨迹，占用 LEGS。现成表现动作应保留完整预设；此类型没有暴露预设的额外 action_params。

| 字段 | 类型 | Schema 默认值 | 含义／填写范围 |
| --- | --- | --- | --- |
| `method` | `BodyMethod` | PASSIVE | 显式选择下面的 BodyMethod 名称；默认 PASSIVE 不是无害空操作。FIXED_LAYDOWN 不是协调趴下。RL_WHEEL 是 schema 值，不代表四足支持。 |
| `action_path` | `string` | 省略 | 从[身体资源](../resources/body-trajectories.zh-CN.md)复制设备轨迹文件名并配对 method。STREAM 必须非空，RL_ACTION_POLICY1–4 传递此字段，其余当前 RCP 身体方法不使用它。不是 DAG 路径或本地上传。 |
| `pre_check` | `bool` | false | 布尔预检查选择；不是授权，也不是通用的只读 dry-run。保留预设检查流程。 |

method 枚举：`PASSIVE`, `FIXED_STAND`, `FIXED_LAYDOWN`, `SAFE_STOP_SEQUENCE`, `SAFE_LAYDOWN_SEQUENCE`, `RL`, `RL_TROT`, `MPC`, `STREAM`, `PILOT`, `RL_ACTION_POLICY1`, `RL_ACTION_POLICY2`, `RL_ACTION_POLICY3`, `RL_ACTION_POLICY4`, `RL_WHEEL`.

## HeadCommand

CSV 标识见[头部轨迹资源](../resources/head-trajectories.zh-CN.md)。

控制头部角度或头部轨迹，占用 HEAD。target_angles 与 action_path 二选一，角度优先；两者都空时回正。

| 字段 | 类型 | Schema 默认值 | 含义／填写范围 |
| --- | --- | --- | --- |
| `method` | `HeadMethod` | ANGLE_CONTROL | ANGLE_CONTROL 或 STREAM；当前实际分派由角度／路径字段决定，method 应与所填内容一致。 |
| `pre_check` | `bool` | false | 布尔值。轨迹预检查会将头部回正，可能运动；没有轨迹时预检查提前返回。 |
| `duration_ms` | `int` | 0 | 目标角度动作时长，毫秒；当前 RCP 将小于 5000 的值提升为 5000，不是轨迹播放超时。 |
| `loop_enabled` | `bool` | false | true 时循环头部轨迹；需提供显式取消与有限阶段，不依赖自然结束。 |
| `playback_rate` | `float` | 1.0 | schema 中为 float；当前 RCP 头部任务不使用该字段，保持 1.0，不依赖它调速。 |
| `target_angles` | `[float]` | 省略 | 填写两个有限弧度值 [pitch, yaw]。物理范围依赖机器人配置，schema 没有给出通用安全范围，不猜测限位。 |
| `action_path` | `string` | 省略 | 设备头部轨迹文件名，例如挥手预设中的 WAVE.csv，不是 WAVE_50hz.npz。保留完整配套行为。 |

method 枚举：`ANGLE_CONTROL`, `STREAM`.

## LightCommand

设置灯光层，占用 LIGHT。[灯光资源](../resources/lights.zh-CN.md)列出模式。使用 DAEMON + 有限阶段 + BARRIER，或支持有限持有的 DSL 任务。

| 字段 | 类型 | Schema 默认值 | 含义／填写范围 |
| --- | --- | --- | --- |
| `method` | `LightMethod` | FIXED_COLOR | 下面六种 LightMethod 之一。类型化 FIXED_COLOR／CIRCLE_AND_FLASH 对应 DSL light.FIXEDCOLOR／light.CIRCLEANDFLASH。 |
| `red` | `uint` | 0 | 红色分量 0–255；uint32 编码不代表更大值有效。 |
| `green` | `uint` | 0 | 绿色分量 0–255。 |
| `blue` | `uint` | 0 | 蓝色分量 0–255。 |
| `brightness` | `uint` | 255 | 亮度 0–255。 |
| `speed` | `float` | 1.0 | 有限数值的效果参数，不是毫秒或秒。没有模式约定时保持 1.0，此处未定义统一效果速度范围。 |
| `duration_ms` | `int` | 0 | 当前 RCP 灯光任务不使用此值结束节点。保持 0，用生命周期或 DSL play_for_ms。 |
| `layer` | `DisplayLayer` | UNSPECIFIED | UNSPECIFIED 保留任务默认 INTERACTION，普通用户输出显式用 INTERACTION。其他 schema 值为 AMBIENT、MISSION、ANIMATION、WARNING、SAFETY，不覆盖安全提示。 |
| `sync` | `bool` | false | 当前任务不使用此值限定持有时间，保持 false。 |

method 枚举：`FIXED_COLOR`, `GRADIENT`, `BREATHING`, `FLASHING`, `CIRCLE_AND_FLASH`, `PULSE`.

## EmotionCommand

显示屏幕表情，占用 SCREEN。从[表情资源](../resources/expressions.zh-CN.md)选 ID，不是身体动画。

| 字段 | 类型 | Schema 默认值 | 含义／填写范围 |
| --- | --- | --- | --- |
| `method` | `EmotionMethod` | UNSPECIFIED | 下方命名别名，不是资源 ID 数值。UNSPECIFIED 通过 BLINK_ONCE 分派；HAPPY 对应 19，SAY_HI 对应 48。 |
| `emotion_id` | `uint` | 0 | 使用资源目录实际列出的 ID，不能任填 uint32。非零值优先于 method 别名；ID 0 配 BLINK_ONCE（或 UNSPECIFIED），不能搭配其他别名并指望零值覆盖。 |
| `duration_ms` | `int` | 0 | 传给显示端的 int32 播放／循环时间参数，-1 保持显示端默认。不是 RCP 持有时长；method 名称带 10S 不代表节点 10 秒完成。 |
| `layer` | `DisplayLayer` | UNSPECIFIED | UNSPECIFIED 保留任务默认 INTERACTION，普通用户输出显式用 INTERACTION。其他 schema 值为 AMBIENT、MISSION、ANIMATION、WARNING、SAFETY，不覆盖安全提示。 |
| `sync` | `bool` | false | 当前任务不使用此字段结束持有，保持 false，使用生命周期或 DSL play_for_ms。 |

method 枚举：`UNSPECIFIED`, `BLINK_ONCE`, `WINK_10S`, `LISTEN_10S`, `SAD_10S`, `HAPPY_10S`, `HAPPY_30S`, `CONFOUND_3S`, `TIMID_15S`, `COURAGE_15S`, `COURAGE_30S`, `FEAR_10S`, `ANGRY_10S`, `DIZZY_30S`, `SURPRISE_20S`, `ANGRY`, `BLINK_MANY`, `COURAGE`, `DIZZY`, `FEAR_COURAGE`, `HAPPY`, `LISTEN`, `SHY`, `SLEEPING`, `SLEEPY`, `SWEATY`, `TALK`, `WAKEUP`, `WINK`, `WRONGED`, `STREAM`, `DOG_BARKING`, `SAY_HI`, `HAPPY_BIRTHDAY`, `HIGH_FIVE`, `LUNGE_FORWARD`, `NEW_YEAR`, `RHYTHMIC_SWING`, `FEAR_ALT`, `COURAGE_ALT`, `HAPPY_ALT`, `DEFAULT_EMOTION`, `LONG_TALK`.

## SpeakCommand

播放设备音效或合成语音，占用 AUDIO_OUT。不会自动套用 harness 的人格或问候前缀。

| 字段 | 类型 | Schema 默认值 | 含义／填写范围 |
| --- | --- | --- | --- |
| `method` | `SpeakMethod` | MACHINE_LANGUAGE | MACHINE_LANGUAGE 选择设备音效，HUMAN_VOICE 选择语音文本。 |
| `text` | `string` | 省略 | HUMAN_VOICE 且 human_language_text 为空时使用的非空文本；MACHINE_LANGUAGE 忽略。 |
| `machine_language_name` | `string` | 省略 | MACHINE_LANGUAGE 的已有音效名，例如 confirm；不是任意文本、表情 ID 或本地音频路径。 |
| `human_language_text` | `string` | 省略 | 非空 HUMAN_VOICE 文本，存在时优先于 text；建议两个字段只填一个。 |

method 枚举：`MACHINE_LANGUAGE`, `HUMAN_VOICE`.

## VlnCommand

底层视觉导航操作。依赖运动与导航服务可用，schema 中存在不代表完整导航流程可用；此命令不负责完整模式进入与恢复。

| 字段 | 类型 | Schema 默认值 | 含义／填写范围 |
| --- | --- | --- | --- |
| `method` | `VlnMethod` | FOLLOW | 下方 VlnMethod 名称。仅 NAV_TO_POINT 转发坐标相关字段，其余方法忽略。 |
| `x` | `float` | 0.0 | NAV_TO_POINT 的有限 x 坐标，米，由 frame 解释。 |
| `y` | `float` | 0.0 | NAV_TO_POINT 的有限 y 坐标，米，由 frame 解释。 |
| `frame` | `string` | 省略 | NAV_TO_POINT 坐标系字符串，省略保留任务默认 local；使用服务明确约定的坐标系，不假定 ROS map／odom 别名。 |
| `stop_distance` | `float` | 0.0 | 导航停止容差，有限非负米数；0 是编码默认，不代表保证零误差到达。 |

method 枚举：`FOLLOW`, `ROAM`, `NAV_TO_POINT`, `COME_TO_ME`, `WALK`, `STOP`, `WALK_WITH_MPC`.

## VlnSessionCommand

管理视觉导航会话：进入所需运控模式、运行导航、退出／取消时恢复之前模式。依赖对应设备服务，不只是 VlnCommand 的别名。

| 字段 | 类型 | Schema 默认值 | 含义／填写范围 |
| --- | --- | --- | --- |
| `method` | `VlnSessionMethod` | FOLLOW | 下方 VlnSessionMethod 名称；NAV_TO_POINT 使用坐标，语义方法使用 prompt，其他方法忽略这些字段。 |
| `x` | `float` | 0.0 | NAV_TO_POINT 的有限 x 坐标，米，由 frame 解释。 |
| `y` | `float` | 0.0 | NAV_TO_POINT 的有限 y 坐标，米，由 frame 解释。 |
| `frame` | `string` | 省略 | NAV_TO_POINT 坐标系字符串，省略保留任务默认 local；使用服务明确约定的坐标系，不假定 ROS map／odom 别名。 |
| `stop_distance` | `float` | 0.0 | 导航停止容差，有限非负米数；0 是编码默认，不代表保证零误差到达。 |
| `prompt` | `string` | 省略 | SYNC_SEMANTIC_NAV／ASYNC_SEMANTIC_NAV 的非空文本，其他方法不传递。 |

method 枚举：`FOLLOW`, `ROAM`, `NAV_TO_POINT`, `COME_TO_ME`, `WALK`, `SYNC_SEMANTIC_NAV`, `ASYNC_SEMANTIC_NAV`.

## LocomotionCommand

选择高层运控模式或姿态操作，占用 LEGS。优先使用已提供的站起／趴下预设，保留协调行为。

| 字段 | 类型 | Schema 默认值 | 含义／填写范围 |
| --- | --- | --- | --- |
| `method` | `LocomotionMethod` | SET_MODE | SET_MODE、STAND_UP、LIE_DOWN、STOP。站起预设可使用此枚举未表达的 DSL 操作，不应假定等价。 |
| `mode` | `uint` | 0 | 仅 SET_MODE 使用。线上为 uint32，当前任务读取 uint8（0–255），只有服务定义的模式 ID 有效，不是 BodyMethod，不能从枚举数字猜模式。 |

method 枚举：`SET_MODE`, `STAND_UP`, `LIE_DOWN`, `STOP`.

## BaseActionCommand

有界基础移动、导航或头部操作。运动通常需要 LEGS，MOVE_HEAD 使用 HEAD。选择一个方法，仅填写相关字段。

| 字段 | 类型 | Schema 默认值 | 含义／填写范围 |
| --- | --- | --- | --- |
| `method` | `BaseActionMethod` | ROTATE | ROTATE 使用 angle_rad；MOVE_FORWARD/BACKWARD/LEFT/RIGHT 使用 distance_m；NAVIGATE_TO 使用 x/y/stop_distance；MOVE_HEAD 将 angle_rad 当 pitch、x 当 yaw。 |
| `angle_rad` | `float` | 0.0 | 旋转时为有限有符号弧度，MOVE_HEAD 时表示 pitch；schema 未定义统一物理范围。 |
| `distance_m` | `float` | 0.0 | 方向移动填写正的有限米数，用 method 选方向，不使用负距离；范围受现场安全空间限制。 |
| `x` | `float` | 0.0 | NAVIGATE_TO 的 x 坐标，米、遵循服务坐标约定；MOVE_HEAD 则为 yaw 弧度。此类型没有 frame 字段。 |
| `y` | `float` | 0.0 | NAVIGATE_TO 的 y 坐标，米；MOVE_HEAD 不使用。 |
| `stop_distance` | `float` | 0.0 | 导航停止容差，有限非负米数；0 是编码默认，不代表保证零误差到达。 |

method 枚举：`ROTATE`, `MOVE_FORWARD`, `MOVE_BACKWARD`, `MOVE_LEFT`, `MOVE_RIGHT`, `NAVIGATE_TO`, `MOVE_HEAD`.

## NavigateCommand

原地旋转，占用 LEGS，不是通用地图导航命令。

| 字段 | 类型 | Schema 默认值 | 含义／填写范围 |
| --- | --- | --- | --- |
| `method` | `NavigateMethod` | ROTATE_IN_PLACE | 仅 ROTATE_IN_PLACE。 |
| `angle_rad` | `float` | 0.0 | 有限有符号弧度，正负方向遵循导航服务约定；不能由 float 存储范围推导安全幅度。 |

method 枚举：`ROTATE_IN_PLACE`.

## SleepCommand

有限等待，不占执行器资源，使用 NORMAL；适合顺序控制或分支汇合。

| 字段 | 类型 | Schema 默认值 | 含义／填写范围 |
| --- | --- | --- | --- |
| `duration_ms` | `int` | 0 | 非负 int32 毫秒，0…2,147,483,647。使用明确的有限等待；正数节点超时需容纳等待完成。 |

## BarrierCommand

空对象 {}。使用 BARRIER 生命周期，依赖本阶段结束的有限工作节点。取消图内所有已持有的 daemon，不是选择性释放资源或普通汇合。

## DslTaskCommand

通用运动参数与组合规则见[运动参数参考](motion-parameters.zh-CN.md)。

用于调用类型化命令未覆盖参数的已注册 DSL 任务，不是 shell、任意代码执行或嵌套预设加载器。

| 字段 | 类型 | Schema 默认值 | 含义／填写范围 |
| --- | --- | --- | --- |
| `task` | `string` | 省略 | 准确的已支持标准键，例如 emotion.HAPPY 或 light.FIXEDCOLOR，不能从任意字符串推断任务存在。 |
| `args_json` | `string` | 省略 | 编码 JSON 对象的字符串。空表示 {}，数组／标量被拒绝。表情／灯光有限持有可编码 play_for_ms > 0，例如 {"layer":"INTERACTION","play_for_ms":1500}，配 NORMAL。其他类型化字段名不自动代表 DSL 支持该参数。 |

## 持有时长与资源关联

类型化 LightCommand／EmotionCommand 没有 play_for_ms。
灯光 duration_ms 当前不控制结束，表情 duration_ms 是显示端播放参数，sync 也不补足这一缺口。
因此普通类型化表情／灯光节点使用 DAEMON，由有限工作和 BARRIER 界定阶段；
需要一个自行完成的 NORMAL 节点时，使用已支持的 DslTaskCommand 并明确 play_for_ms > 0。

身体资源名填 action_path，表情资源 ID 填 emotion_id，灯光按 method 与颜色填写；
它们不能相互替代。参见[设备资源](../resources/README.zh-CN.md)与[组合示意](../guides/rcp-dag.zh-CN.md)。
