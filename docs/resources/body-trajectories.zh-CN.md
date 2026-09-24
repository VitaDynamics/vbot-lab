# 身体轨迹资源

通用运动参数与组合规则见[运动参数参考](../interfaces/motion-parameters.zh-CN.md)。

<p align="center"><a href="body-trajectories.md">English</a> | 中文</p>

调用方式选择与字段对应见[直接服务与 RCP](../guides/control-paths.zh-CN.md)。

将下表资源名原样填入 `BodyCommand.action_path`（Python 对象字段为 `actionPath`），
并使用同一行的 `method`。这些是设备端身体轨迹，不是表情 ID、头部 CSV 或 DAG JSON。
下表列出[RCP 预设](../guides/rcp-presets.zh-CN.md)使用的 71 个不同身体轨迹；不代表设备上的所有轨迹文件均对外提供。
说明用于解释动作主题，不承诺具体幅度、时长或环境交互效果；L／R 保留资源的左右命名。
追球、嗅闻、倾听等名称表示表现动作，不会自动启动目标跟踪或感知流程。

**这些对应预设均包含额外的 `action_params`，而当前 BodyCommand 未覆盖全部参数。**
执行现成行为时，请通过最后一列的 `DagPresetRef.relative_path` 调用完整预设，
保留资源声明、姿态过渡与配套节点；此表不是仅凭 method 和文件名即可执行的独立示例。
站起与协调趴下使用[基础预设](../guides/rcp-presets.zh-CN.md)，不需要在这里寻找同名轨迹。
填写规则见 [DAG 编写指南](../guides/rcp-dag.zh-CN.md)。

自定义图使用 DslTaskCommand 携带支持的 action_params，无需逐个复制预设。
参数值按运动参考和资源约束选择；预设列只是可选的现成入口，不是定制的必需步骤。

配套 CSV 与准确的预设对应关系见[头部轨迹](head-trajectories.zh-CN.md)。
例如 WAVE_50hz.npz 填入 BodyCommand，而 WAVE.csv 填入 HeadCommand。

| 身体轨迹资源名（action_path） | 配套 BodyCommand.method | 动作说明 | 对应完整预设 |
| --- | --- | --- | --- |
| `BACK_OFF_50hz.npz` | `RL_ACTION_POLICY2` | 退避表现 | `actions/BACK_OFF.json` |
| `BOW_NEW_YEAR_50hz.npz` | `RL_ACTION_POLICY1` | 新年作揖 | `actions/BOW_NEW_YEAR.json` |
| `CAT_50hz.npz` | `RL_ACTION_POLICY1` | 猫咪模仿 | `actions/CAT.json` |
| `CHASE_BALL_50hz.npz` | `RL_ACTION_POLICY1` | 追球表现，不提供球体跟踪 | `actions/CHASE_BALL.json` |
| `CHEEKY_50hz.npz` | `RL_ACTION_POLICY1` | 俏皮表现 | `actions/CHEEKY.json` |
| `CHEER_L_50hz.npz` | `RL_ACTION_POLICY1` | 左侧欢呼 | `actions/CHEER_L.json` |
| `CHEER_R_50hz.npz` | `RL_ACTION_POLICY1` | 右侧欢呼 | `actions/CHEER_R.json` |
| `CONDUCT_50hz.npz` | `RL_ACTION_POLICY2` | 指挥表现 | `actions/CONDUCT.json` |
| `CRAWL_50hz.npz` | `RL_ACTION_POLICY1` | 爬行表现 | `actions/CRAWL.json` |
| `CURIOUS_50hz.npz` | `RL_ACTION_POLICY1` | 好奇表现 | `actions/CURIOUS.json` |
| `DIG_HOLE_50hz.npz` | `RL_ACTION_POLICY1` | 挖洞表现 | `actions/DIG_HOLE.json` |
| `DIZZINESS_50hz.npz` | `RL_ACTION_POLICY1` | 眩晕表现，也被委屈预设复用 | `actions/DIZZINESS.json`, `actions/GRIEVANCE.json`, `actions/GRIEVANCE_APP.json` |
| `DOG_50hz.npz` | `RL_ACTION_POLICY1` | 狗狗模仿 | `actions/DOG.json` |
| `DOG_BARK_50hz.npz` | `RL_ACTION_POLICY1` | 吠叫身体动作，声音需另行配合 | `actions/DOG_BARK.json` |
| `DRUM_50hz.npz` | `RL_ACTION_POLICY1` | 打鼓表现 | `actions/DRUM.json` |
| `DRUMER_50hz.npz` | `RL_ACTION_POLICY1` | 鼓手表现变体 | `actions/DRUMER.json` |
| `ELEPHANT_50hz.npz` | `RL_ACTION_POLICY1` | 大象模仿 | `actions/ELEPHANT.json` |
| `EXCITED_50hz.npz` | `RL_ACTION_POLICY1` | 兴奋表现 | `actions/EXCITED.json` |
| `FORTUNE_CAT_50hz.npz` | `RL_ACTION_POLICY1` | 招财猫动作 | `actions/FORTUNE_CAT.json` |
| `FORTUNE_CAT_L_50hz.npz` | `RL_ACTION_POLICY1` | 左侧招财猫动作 | `actions/FORTUNE_CAT_L.json` |
| `GUITAR_50hz.npz` | `RL_ACTION_POLICY1` | 吉他演奏表现 | `actions/GUITAR.json` |
| `HAPPY_BOUNCE_50hz.npz` | `RL_ACTION_POLICY2` | 开心蹦跳，供 HAPPY_JUMP 使用 | `actions/HAPPY_JUMP.json` |
| `HAPPY_BOUNCE_B_50hz.npz` | `RL_ACTION_POLICY2` | 开心蹦跳 B 变体 | `actions/HAPPY_BOUNCE_B.json` |
| `HAPPY_LITTLE_JUMP_50hz.npz` | `RL_ACTION_POLICY1` | 开心小跳 | `actions/HAPPY_LITTLE_JUMP.json` |
| `HAPPYBIRTHDAY_50hz.npz` | `RL_ACTION_POLICY1` | 生日表现 | `actions/HAPPYBIRTHDAY.json` |
| `HEN_50hz.npz` | `RL_ACTION_POLICY1` | 母鸡模仿 | `actions/HEN.json` |
| `HIGH_FIVE_L_50hz.npz` | `RL_ACTION_POLICY1` | 左侧击掌 | `actions/HIGH_FIVE_L.json` |
| `HIGH_FIVE_R_50hz.npz` | `RL_ACTION_POLICY1` | 右侧击掌 | `actions/HIGH_FIVE_R.json` |
| `HOWL_LIKE_WOLF_50hz.npz` | `RL_ACTION_POLICY1` | 狼嚎身体动作，声音需另行配合 | `actions/HOWL_LIKE_WOLF.json` |
| `IDENTIFY_50hz.npz` | `RL_ACTION_POLICY1` | IDENTIFY 主题表现，不提供识别接口 | `actions/IDENTIFY.json` |
| `JUMP_AHEAD_50hz.npz` | `RL_ACTION_POLICY2` | 向前跳跃 JUMP_AHEAD 变体 | `actions/JUMP_AHEAD.json` |
| `JUMP_FORWARD_50hz.npz` | `RL_ACTION_POLICY2` | 向前跳跃 JUMP_FORWARD 变体 | `actions/JUMP_FORWARD.json` |
| `JUMP_IN_PLACE_50hz.npz` | `RL_ACTION_POLICY1` | 原地跳跃 | `actions/JUMP_IN_PLACE.json` |
| `LICK_HAND_50hz.npz` | `RL_ACTION_POLICY1` | 舔手表现 | `actions/LICK_HAND.json` |
| `LOOKLEFT_50hz.npz` | `RL_ACTION_POLICY1` | 向左看身体动作 | `actions/LOOKLEFT.json` |
| `LOOKRIGHT_50hz.npz` | `RL_ACTION_POLICY1` | 向右看身体动作 | `actions/LOOKRIGHT.json` |
| `NEWYEAR_GREETING_50hz.npz` | `RL_ACTION_POLICY1` | 新年问候 | `actions/NEWYEAR_GREETING.json` |
| `PEE_50hz.npz` | `RL_ACTION_POLICY1` | 撒尿模仿 | `actions/PEE.json` |
| `PIANO_50hz.npz` | `RL_ACTION_POLICY1` | 钢琴演奏表现 | `actions/PIANO.json` |
| `PIG_50hz.npz` | `RL_ACTION_POLICY1` | 小猪模仿 | `actions/PIG.json` |
| `PILATES_D_50hz.npz` | `RL_ACTION_POLICY1` | 普拉提 D 变体 | `actions/PILATES_D.json` |
| `PoseC_50hz.npz` | `RL_ACTION_POLICY2` | 造型 C | `actions/POSE_C.json` |
| `PoseD_50hz.npz` | `RL_ACTION_POLICY2` | 造型 D | `actions/POSE_D.json` |
| `PoseE_50hz.npz` | `RL_ACTION_POLICY2` | 造型 E | `actions/POSE_E.json` |
| `PoseF_50hz.npz` | `RL_ACTION_POLICY2` | 造型 F | `actions/POSE_F.json` |
| `PUSHUP_50hz.npz` | `RL_ACTION_POLICY1` | 俯卧撑表现 | `actions/PUSHUP.json` |
| `RELAXED_SWING_50hz.npz` | `RL_ACTION_POLICY1` | 放松摇摆 | `actions/RELAXED_SWING.json` |
| `REPORT_50hz.npz` | `RL_ACTION_POLICY1` | REPORT 主题表现，不是状态上报 | `actions/REPORT.json` |
| `RHYTHM_50hz.npz` | `RL_ACTION_POLICY1` | 律动表现 | `actions/RHYTHM.json` |
| `RHYTHMIC_SWING_50hz.npz` | `RL_ACTION_POLICY1` | 节奏摇摆 | `actions/RHYTHMIC_SWING.json` |
| `ROCKYOU_50hz.npz` | `RL_ACTION_POLICY3` | ROCKYOU 舞蹈 | `actions/ROCKYOU.json` |
| `RUB_LEG_L_50hz.npz` | `RL_ACTION_POLICY1` | 左侧蹭腿表现 | `actions/RUB_LEG_L.json` |
| `RUB_LEG_R_50hz.npz` | `RL_ACTION_POLICY1` | 右侧蹭腿表现 | `actions/RUB_LEG_R.json` |
| `SAXOPHONE_50hz.npz` | `RL_ACTION_POLICY1` | 萨克斯演奏表现 | `actions/SAXOPHONE.json` |
| `SAYNO_50hz.npz` | `RL_ACTION_POLICY1` | 否定动作 | `actions/SAYNO.json` |
| `SAYYES_50hz.npz` | `RL_ACTION_POLICY1` | 肯定动作 | `actions/SAYYES.json` |
| `SCRATCH_HEAD_L_50hz.npz` | `RL_ACTION_POLICY1` | 左侧挠头表现 | `actions/SCRATCH_HEAD_L.json` |
| `SCRATCH_HEAD_R_50hz.npz` | `RL_ACTION_POLICY1` | 右侧挠头表现 | `actions/SCRATCH_HEAD_R.json` |
| `SELF_INTRODUCTION_50hz.npz` | `RL_ACTION_POLICY1` | 自我介绍身体动作，语音需另行配合 | `actions/SELF_INTRODUCTION.json` |
| `SHAKEHAND_50hz.npz` | `RL_ACTION_POLICY1` | 握手 | `actions/SHAKEHAND.json` |
| `SHAKEHAND_L_50hz.npz` | `RL_ACTION_POLICY1` | 左侧握手 | `actions/SHAKEHAND_L.json` |
| `SITUP_50hz.npz` | `RL_ACTION_POLICY1` | 起坐表现 | `actions/SITUP.json` |
| `SMELL_50hz.npz` | `RL_ACTION_POLICY1` | 嗅闻表现，不提供气味感知 | `actions/SMELL.json` |
| `STRETCH_SLEEP_50hz.npz` | `RL_ACTION_POLICY1` | 困倦伸展 | `actions/STRETCH_SLEEP.json` |
| `TICKLING_L_50hz.npz` | `RL_ACTION_POLICY1` | 左侧挠痒反应 | `actions/TICKLING_L.json` |
| `TICKLING_R_50hz.npz` | `RL_ACTION_POLICY1` | 右侧挠痒反应 | `actions/TICKLING_R.json` |
| `TILT_HEAD_LISTEN_50hz.npz` | `RL_ACTION_POLICY1` | 侧头倾听主题身体动作，不提供音频采集 | `actions/TILT_HEAD_LISTEN.json` |
| `TWIST_BUTT_50hz.npz` | `RL_ACTION_POLICY1` | 扭臀 | `actions/TWIST_BUTT.json` |
| `VIOLIN_50hz.npz` | `RL_ACTION_POLICY1` | 小提琴演奏表现 | `actions/VIOLIN.json` |
| `WAKEUP_50hz.npz` | `RL_ACTION_POLICY1` | 醒来表现，不等同站起流程 | `actions/WAKEUP.json` |
| `WAVE_50hz.npz` | `RL_ACTION_POLICY1` | 挥手 | `actions/WAVE.json` |


返回[设备资源](README.zh-CN.md)；通过 RCP 使用时见[节点字段参考](../interfaces/rcp-commands.zh-CN.md)。
