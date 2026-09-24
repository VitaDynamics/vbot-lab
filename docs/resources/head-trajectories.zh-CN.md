# 头部轨迹资源

<p align="center"><a href="head-trajectories.md">English</a> | 中文</p>

本清单列出当前四足 EDU 预设引用的 66 个头部 CSV 轨迹，与[身体 NPZ 轨迹](body-trajectories.zh-CN.md)分开管理。
CSV 在这里是头部轨迹资源，不是被 NPZ 替代的旧版身体轨迹。

## 如何选择和填写

- 在 RCP 中使用 `HeadCommand.method = STREAM`，将资源名原样填写到 `action_path`（Python 对象字段为 `actionPath`）。
- 使用轨迹时省略或清空 `target_angles`，否则角度输入优先。字段详解见 [HeadCommand](../interfaces/rcp-commands.zh-CN.md#headcommand)。
- 文件由设备服务读取，不需要客户端打开或上传；不要填写电脑路径或 DAG JSON 名。
- 现成表现动作优先使用[完整预设](../guides/rcp-presets.zh-CN.md)，保留身体、头部、灯光与表情的配套编排。
- 表中的 NPZ 是同一预设引用的身体资源，不是头部命令的输入。“—”表示该预设没有显式身体轨迹引用，不代表它没有其他效果。
- 资源名不能靠替换扩展名推导。例如 `HAPPY_JUMP.csv` 配 `HAPPY_BOUNCE_50hz.npz`；
  `FORTUNE_CAT.csv` 被两个招财猫预设复用。
- 说明只描述配套行为主题，不表示 CSV 单独实现完整行为；循环轨迹需明确取消与结束阶段。

## 资源清单

| 头部资源名（action_path） | HeadCommand.method | 配套行为主题 | 同预设身体资源 | 对应完整预设 |
| --- | --- | --- | --- | --- |
| `BACK_OFF.csv` | `STREAM` | 退避表现 | `BACK_OFF_50hz.npz` | `actions/BACK_OFF.json` |
| `BOW_NEW_YEAR.csv` | `STREAM` | 新年作揖 | `BOW_NEW_YEAR_50hz.npz` | `actions/BOW_NEW_YEAR.json` |
| `CAT.csv` | `STREAM` | 猫咪模仿 | `CAT_50hz.npz` | `actions/CAT.json` |
| `CHASE_BALL.csv` | `STREAM` | 追球表现，不提供球体跟踪 | `CHASE_BALL_50hz.npz` | `actions/CHASE_BALL.json` |
| `CHEEKY.csv` | `STREAM` | 俏皮表现 | `CHEEKY_50hz.npz` | `actions/CHEEKY.json` |
| `CHEER_L.csv` | `STREAM` | 左侧欢呼 | `CHEER_L_50hz.npz` | `actions/CHEER_L.json` |
| `CHEER_R.csv` | `STREAM` | 右侧欢呼 | `CHEER_R_50hz.npz` | `actions/CHEER_R.json` |
| `CONDUCT.csv` | `STREAM` | 指挥表现 | `CONDUCT_50hz.npz` | `actions/CONDUCT.json` |
| `CRAWL.csv` | `STREAM` | 爬行表现 | `CRAWL_50hz.npz` | `actions/CRAWL.json` |
| `CURIOUS.csv` | `STREAM` | 好奇表现 | `CURIOUS_50hz.npz` | `actions/CURIOUS.json` |
| `DIG_HOLE.csv` | `STREAM` | 挖洞表现 | `DIG_HOLE_50hz.npz` | `actions/DIG_HOLE.json` |
| `DIZZINESS.csv` | `STREAM` | 眩晕表现，也被委屈预设复用 | `DIZZINESS_50hz.npz` | `actions/DIZZINESS.json`, `actions/GRIEVANCE.json`, `actions/GRIEVANCE_APP.json` |
| `DOG_BARK.csv` | `STREAM` | 吠叫身体动作，声音需另行配合 | `DOG_BARK_50hz.npz` | `actions/DOG_BARK.json` |
| `DOG.csv` | `STREAM` | 狗狗模仿 | `DOG_50hz.npz` | `actions/DOG.json` |
| `DRUM.csv` | `STREAM` | 打鼓表现 | `DRUM_50hz.npz` | `actions/DRUM.json` |
| `DRUMER.csv` | `STREAM` | 鼓手表现变体 | `DRUMER_50hz.npz` | `actions/DRUMER.json` |
| `ELEPHANT.csv` | `STREAM` | 大象模仿 | `ELEPHANT_50hz.npz` | `actions/ELEPHANT.json` |
| `EXCITED.csv` | `STREAM` | 兴奋表现 | `EXCITED_50hz.npz` | `actions/EXCITED.json` |
| `FORTUNE_CAT.csv` | `STREAM` | 招财猫动作 | `FORTUNE_CAT_50hz.npz`, `FORTUNE_CAT_L_50hz.npz` | `actions/FORTUNE_CAT.json`, `actions/FORTUNE_CAT_L.json` |
| `GUITAR.csv` | `STREAM` | 吉他演奏表现 | `GUITAR_50hz.npz` | `actions/GUITAR.json` |
| `HAPPY_BOUNCE_B.csv` | `STREAM` | 开心蹦跳 B 变体 | `HAPPY_BOUNCE_B_50hz.npz` | `actions/HAPPY_BOUNCE_B.json` |
| `HAPPY_JUMP.csv` | `STREAM` | 开心跳跃表现 | `HAPPY_BOUNCE_50hz.npz` | `actions/HAPPY_JUMP.json` |
| `HAPPY_LITTLE_JUMP.csv` | `STREAM` | 开心小跳 | `HAPPY_LITTLE_JUMP_50hz.npz` | `actions/HAPPY_LITTLE_JUMP.json` |
| `HAPPYBIRTHDAY.csv` | `STREAM` | 生日表现 | `HAPPYBIRTHDAY_50hz.npz` | `actions/HAPPYBIRTHDAY.json` |
| `HEN.csv` | `STREAM` | 母鸡模仿 | `HEN_50hz.npz` | `actions/HEN.json` |
| `HIGH_FIVE_L.csv` | `STREAM` | 左侧击掌 | `HIGH_FIVE_L_50hz.npz` | `actions/HIGH_FIVE_L.json` |
| `HIGH_FIVE_R.csv` | `STREAM` | 右侧击掌 | `HIGH_FIVE_R_50hz.npz` | `actions/HIGH_FIVE_R.json` |
| `HOWL_LIKE_WOLF.csv` | `STREAM` | 狼嚎身体动作，声音需另行配合 | `HOWL_LIKE_WOLF_50hz.npz` | `actions/HOWL_LIKE_WOLF.json` |
| `JUMP_FORWARD.csv` | `STREAM` | 向前跳跃 JUMP_FORWARD 变体 | `JUMP_FORWARD_50hz.npz` | `actions/JUMP_FORWARD.json` |
| `JUMP_IN_PLACE.csv` | `STREAM` | 原地跳跃 | `JUMP_IN_PLACE_50hz.npz` | `actions/JUMP_IN_PLACE.json` |
| `LICK_HAND.csv` | `STREAM` | 舔手表现 | `LICK_HAND_50hz.npz` | `actions/LICK_HAND.json` |
| `LOOKAROUND.csv` | `STREAM` | 环顾表现 | — | `actions/LOOKAROUND.json` |
| `LOOKFORWARD.csv` | `STREAM` | 向前看／警觉表现 | — | `actions/LOOKFORWARD.json`, `actions/PARTROLALERT.json` |
| `LOOKLEFT.csv` | `STREAM` | 向左看身体动作 | `LOOKLEFT_50hz.npz` | `actions/LOOKLEFT.json` |
| `LOOKRIGHT.csv` | `STREAM` | 向右看身体动作 | `LOOKRIGHT_50hz.npz` | `actions/LOOKRIGHT.json` |
| `NEWYEAR_GREETING.csv` | `STREAM` | 新年问候 | `NEWYEAR_GREETING_50hz.npz` | `actions/NEWYEAR_GREETING.json` |
| `PEE.csv` | `STREAM` | 撒尿模仿 | `PEE_50hz.npz` | `actions/PEE.json` |
| `PIANO.csv` | `STREAM` | 钢琴演奏表现 | `PIANO_50hz.npz` | `actions/PIANO.json` |
| `PIG.csv` | `STREAM` | 小猪模仿 | `PIG_50hz.npz` | `actions/PIG.json` |
| `PILATES_D.csv` | `STREAM` | 普拉提 D 变体 | `PILATES_D_50hz.npz` | `actions/PILATES_D.json` |
| `PoseC.csv` | `STREAM` | 造型 C | `PoseC_50hz.npz` | `actions/POSE_C.json` |
| `PoseD.csv` | `STREAM` | 造型 D | `PoseD_50hz.npz` | `actions/POSE_D.json` |
| `PoseE.csv` | `STREAM` | 造型 E | `PoseE_50hz.npz` | `actions/POSE_E.json` |
| `PoseF.csv` | `STREAM` | 造型 F | `PoseF_50hz.npz` | `actions/POSE_F.json` |
| `PUSHUP.csv` | `STREAM` | 俯卧撑表现 | `PUSHUP_50hz.npz` | `actions/PUSHUP.json` |
| `RELAXED_SWING.csv` | `STREAM` | 放松摇摆 | `RELAXED_SWING_50hz.npz` | `actions/RELAXED_SWING.json` |
| `RHYTHM.csv` | `STREAM` | 律动表现 | `RHYTHM_50hz.npz` | `actions/RHYTHM.json` |
| `RHYTHMIC_SWING.csv` | `STREAM` | 节奏摇摆 | `RHYTHMIC_SWING_50hz.npz` | `actions/RHYTHMIC_SWING.json` |
| `ROCKYOU.csv` | `STREAM` | ROCKYOU 舞蹈 | `ROCKYOU_50hz.npz` | `actions/ROCKYOU.json` |
| `RUB_LEG_L.csv` | `STREAM` | 左侧蹭腿表现 | `RUB_LEG_L_50hz.npz` | `actions/RUB_LEG_L.json` |
| `RUB_LEG_R.csv` | `STREAM` | 右侧蹭腿表现 | `RUB_LEG_R_50hz.npz` | `actions/RUB_LEG_R.json` |
| `SAXOPHONE.csv` | `STREAM` | 萨克斯演奏表现 | `SAXOPHONE_50hz.npz` | `actions/SAXOPHONE.json` |
| `SAYNO.csv` | `STREAM` | 否定动作 | `SAYNO_50hz.npz` | `actions/SAYNO.json` |
| `SAYYES.csv` | `STREAM` | 肯定动作 | `SAYYES_50hz.npz` | `actions/SAYYES.json` |
| `SCRATCH_HEAD_L.csv` | `STREAM` | 左侧挠头表现 | `SCRATCH_HEAD_L_50hz.npz` | `actions/SCRATCH_HEAD_L.json` |
| `SCRATCH_HEAD_R.csv` | `STREAM` | 右侧挠头表现 | `SCRATCH_HEAD_R_50hz.npz` | `actions/SCRATCH_HEAD_R.json` |
| `SELF_INTRODUCTION.csv` | `STREAM` | 自我介绍身体动作，语音需另行配合 | `SELF_INTRODUCTION_50hz.npz` | `actions/SELF_INTRODUCTION.json` |
| `SITUP.csv` | `STREAM` | 起坐表现 | `SITUP_50hz.npz` | `actions/SITUP.json` |
| `SMELL.csv` | `STREAM` | 嗅闻表现，不提供气味感知 | `SMELL_50hz.npz` | `actions/SMELL.json` |
| `STRETCH_SLEEP.csv` | `STREAM` | 困倦伸展 | `STRETCH_SLEEP_50hz.npz` | `actions/STRETCH_SLEEP.json` |
| `TICKLING_L.csv` | `STREAM` | 左侧挠痒反应 | `TICKLING_L_50hz.npz` | `actions/TICKLING_L.json` |
| `TICKLING_R.csv` | `STREAM` | 右侧挠痒反应 | `TICKLING_R_50hz.npz` | `actions/TICKLING_R.json` |
| `TILT_HEAD_LISTEN.csv` | `STREAM` | 侧头倾听主题身体动作，不提供音频采集 | `TILT_HEAD_LISTEN_50hz.npz` | `actions/TILT_HEAD_LISTEN.json` |
| `TWIST_BUTT.csv` | `STREAM` | 扭臀 | `TWIST_BUTT_50hz.npz` | `actions/TWIST_BUTT.json` |
| `VIOLIN.csv` | `STREAM` | 小提琴演奏表现 | `VIOLIN_50hz.npz` | `actions/VIOLIN.json` |
| `WAVE.csv` | `STREAM` | 挥手 | `WAVE_50hz.npz` | `actions/WAVE.json` |

返回[设备资源](README.zh-CN.md)。
