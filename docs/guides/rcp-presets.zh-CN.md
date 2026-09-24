# RCP 预设目录

<p align="center"><a href="rcp-presets.md">English</a> | 中文</p>

本目录提供四足 EDU 的预设标识与资源声明，配合 [DAG 编写指南](rcp-dag.zh-CN.md)使用。
设备服务加载预设，用户无需读取安装目录；调用时使用 `DagPresetRef.relative_path`。
资源存在不代表所有姿态下都能执行；实际准入取决于当前状态与资源。不同软件版本的集合可能不同。

常用入口：站起 `action_stand_from_phone.json`；协调趴下 `action_down_from_phone.json`；
坐下 `actions/SITUP.json`；挥手 `actions/WAVE.json`；
握手 `actions/SHAKEHAND.json`／`actions/SHAKEHAND_L.json`；
击掌 `actions/HIGH_FIVE_R.json`／`actions/HIGH_FIVE_L.json`；
生日表现 `actions/HAPPYBIRTHDAY.json`；头部回正 `atom/look_forward.json`。

预设通常已组合身体、头部、表情、灯光和音效，不是单个关节动作或 `BodyCommand.method`。
也不能直接作为嵌套预设节点；顺序播放多个预设时，客户端逐个提交并等待成功终态。
表中保留原有资源声明，`—` 表示没有显式声明。可选资源可能被跳过，不表示节点不使用该资源。
参数化预设的必需参数见编写指南。

## 基础姿态与参数化移动

不要使用 action_sit_from_phone.json 坐下：其身体节点选择 FIXED_LAYDOWN。
通用运动参数与组合规则见[运动参数参考](../interfaces/motion-parameters.zh-CN.md)。

| 相对预设名 | required_resources | optional_resources | 节点类别 |
| --- | --- | --- | --- |
| `action_down_from_phone.json` | `LEGS`, `HEAD` | `AUDIO_OUT`, `LIGHT`, `SCREEN` | `body`, `emotion`, `light`, `barrier`, `speak`, `head` |
| `action_sit_from_phone.json` | `LEGS`, `LIGHT`, `SCREEN`, `HEAD` | `AUDIO_OUT` | `body`, `emotion`, `light`, `speak`, `head` |
| `action_stand_from_phone.json` | `LEGS`, `LIGHT`, `SCREEN`, `HEAD` | `AUDIO_OUT` | `locomotion`, `emotion`, `light`, `speak`, `head` |
| `atom/look_down.json` | — | `HEAD`, `LIGHT`, `AUDIO_OUT` | `head`, `emotion`, `light`, `speak` |
| `atom/look_forward.json` | — | `HEAD`, `LIGHT`, `AUDIO_OUT` | `head`, `emotion`, `light`, `speak` |
| `atom/look_left.json` | — | `HEAD`, `LIGHT`, `AUDIO_OUT` | `head`, `emotion`, `light`, `speak` |
| `atom/look_right.json` | — | `HEAD`, `LIGHT`, `AUDIO_OUT` | `head`, `emotion`, `light`, `speak` |
| `atom/look_up.json` | — | `HEAD`, `LIGHT`, `AUDIO_OUT` | `head`, `emotion`, `light`, `speak` |
| `atom/move_param.json` | `LEGS` | `HEAD`, `LIGHT`, `AUDIO_OUT` | `head`, `base_action`, `emotion`, `light`, `speak` |
| `atom/rotate_180_l.json` | `LEGS` | `LIGHT`, `AUDIO_OUT` | `base_action`, `emotion`, `light`, `speak` |
| `atom/rotate_180_r.json` | `LEGS` | `LIGHT`, `AUDIO_OUT` | `base_action`, `emotion`, `light`, `speak` |
| `atom/rotate_360.json` | `LEGS` | `LIGHT`, `AUDIO_OUT` | `base_action`, `emotion`, `light`, `speak` |
| `atom/rotate_90_l.json` | `LEGS` | `LIGHT`, `AUDIO_OUT` | `base_action`, `emotion`, `light`, `speak` |
| `atom/rotate_90_r.json` | `LEGS` | `LIGHT`, `AUDIO_OUT` | `base_action`, `emotion`, `light`, `speak` |
| `atom/rotate_param.json` | `LEGS` | `LIGHT`, `AUDIO_OUT` | `base_action`, `emotion`, `light`, `speak` |

## 表现动作预设

身体表演、跳跃、转圈需足够空间、合适姿态和现场停止手段。不要从名称推断幅度、时长或负载能力，
应保留完整预设的过渡和检查逻辑。

| 相对预设名 | required_resources | optional_resources | 节点类别 |
| --- | --- | --- | --- |
| `actions/BACK_OFF.json` | `LIGHT`, `SCREEN`, `LEGS`, `HEAD` | `AUDIO_OUT` | `body`, `head`, `emotion`, `light`, `speak` |
| `actions/BOW_NEW_YEAR.json` | `LIGHT`, `SCREEN`, `LEGS`, `HEAD` | `AUDIO_OUT` | `body`, `head`, `emotion`, `light`, `speak` |
| `actions/CAT.json` | `LIGHT`, `SCREEN`, `LEGS`, `HEAD` | `AUDIO_OUT` | `body`, `head`, `emotion`, `light`, `speak` |
| `actions/CHASE_BALL.json` | `LIGHT`, `SCREEN`, `LEGS`, `HEAD` | `AUDIO_OUT` | `body`, `head`, `emotion`, `light`, `speak` |
| `actions/CHEEKY.json` | `LIGHT`, `SCREEN`, `LEGS`, `HEAD` | `AUDIO_OUT` | `body`, `head`, `emotion`, `light`, `speak` |
| `actions/CHEER_L.json` | `LIGHT`, `SCREEN`, `LEGS`, `HEAD` | `AUDIO_OUT` | `body`, `head`, `emotion`, `light`, `speak` |
| `actions/CHEER_R.json` | `LIGHT`, `SCREEN`, `LEGS`, `HEAD` | `AUDIO_OUT` | `body`, `head`, `emotion`, `light`, `speak` |
| `actions/CONDUCT.json` | `LIGHT`, `SCREEN`, `LEGS`, `HEAD` | `AUDIO_OUT` | `body`, `head`, `emotion`, `light`, `speak` |
| `actions/CRAWL.json` | `LIGHT`, `SCREEN`, `LEGS`, `HEAD` | `AUDIO_OUT` | `body`, `head`, `emotion`, `light`, `speak` |
| `actions/CURIOUS.json` | `LIGHT`, `SCREEN`, `LEGS`, `HEAD` | `AUDIO_OUT` | `body`, `head`, `emotion`, `light`, `speak` |
| `actions/DIG_HOLE.json` | `LIGHT`, `SCREEN`, `LEGS`, `HEAD` | `AUDIO_OUT` | `body`, `head`, `emotion`, `light`, `speak` |
| `actions/DIZZINESS.json` | `LIGHT`, `SCREEN`, `LEGS`, `HEAD` | `AUDIO_OUT` | `body`, `head`, `emotion`, `light`, `speak` |
| `actions/DOG.json` | `LIGHT`, `SCREEN`, `LEGS`, `HEAD` | `AUDIO_OUT` | `body`, `head`, `emotion`, `light`, `speak` |
| `actions/DOG_BARK.json` | `LIGHT`, `SCREEN`, `LEGS`, `HEAD` | `AUDIO_OUT` | `body`, `head`, `emotion`, `light`, `speak` |
| `actions/DRUM.json` | `LIGHT`, `SCREEN`, `LEGS`, `HEAD` | `AUDIO_OUT` | `body`, `head`, `emotion`, `light`, `speak` |
| `actions/DRUMER.json` | `LIGHT`, `SCREEN`, `LEGS`, `HEAD` | `AUDIO_OUT` | `body`, `head`, `emotion`, `light`, `speak` |
| `actions/ELEPHANT.json` | `LIGHT`, `SCREEN`, `LEGS`, `HEAD` | `AUDIO_OUT` | `body`, `head`, `emotion`, `light`, `speak` |
| `actions/ENJOY.json` | `SCREEN`, `LEGS`, `LIGHT` | `AUDIO_OUT` | `emotion` |
| `actions/EXCITED.json` | `LIGHT`, `SCREEN`, `LEGS`, `HEAD` | `AUDIO_OUT` | `body`, `head`, `emotion`, `light`, `speak` |
| `actions/FORTUNE_CAT.json` | `LIGHT`, `SCREEN`, `LEGS`, `HEAD` | `AUDIO_OUT` | `body`, `head`, `emotion`, `light`, `speak` |
| `actions/FORTUNE_CAT_L.json` | `LIGHT`, `SCREEN`, `LEGS`, `HEAD` | `AUDIO_OUT` | `body`, `head`, `emotion`, `light`, `speak` |
| `actions/GRIEVANCE.json` | `LIGHT`, `SCREEN`, `LEGS`, `HEAD` | `AUDIO_OUT` | `body`, `head`, `emotion`, `light`, `speak` |
| `actions/GRIEVANCE_APP.json` | `LIGHT`, `SCREEN`, `LEGS`, `HEAD` | `AUDIO_OUT` | `body`, `head`, `emotion`, `light`, `speak` |
| `actions/GRIEVANCE_NOBODY.json` | `LIGHT`, `SCREEN`, `LEGS`, `HEAD` | `AUDIO_OUT` | `emotion`, `light`, `speak` |
| `actions/GUITAR.json` | `LIGHT`, `SCREEN`, `LEGS`, `HEAD` | `AUDIO_OUT` | `body`, `head`, `emotion`, `light`, `speak` |
| `actions/HAPPYBIRTHDAY.json` | `LIGHT`, `SCREEN`, `LEGS`, `HEAD` | `AUDIO_OUT` | `body`, `head`, `emotion`, `light`, `speak` |
| `actions/HAPPY_BOUNCE_B.json` | `LIGHT`, `SCREEN`, `LEGS`, `HEAD` | `AUDIO_OUT` | `body`, `head`, `emotion`, `light`, `speak` |
| `actions/HAPPY_JUMP.json` | `LIGHT`, `SCREEN`, `LEGS`, `HEAD` | `AUDIO_OUT` | `body`, `head`, `emotion`, `light`, `speak` |
| `actions/HAPPY_LITTLE_JUMP.json` | `LIGHT`, `SCREEN`, `LEGS`, `HEAD` | `AUDIO_OUT` | `body`, `head`, `emotion`, `light`, `speak` |
| `actions/HEN.json` | `LIGHT`, `SCREEN`, `LEGS`, `HEAD` | `AUDIO_OUT` | `body`, `head`, `emotion`, `light`, `speak` |
| `actions/HIGH_FIVE_L.json` | `LIGHT`, `SCREEN`, `LEGS`, `HEAD` | `AUDIO_OUT` | `body`, `head`, `emotion`, `light`, `speak` |
| `actions/HIGH_FIVE_R.json` | `LIGHT`, `SCREEN`, `LEGS`, `HEAD` | `AUDIO_OUT` | `body`, `head`, `emotion`, `light`, `speak` |
| `actions/HOWL_LIKE_WOLF.json` | `LIGHT`, `SCREEN`, `LEGS`, `HEAD` | `AUDIO_OUT` | `body`, `head`, `emotion`, `light`, `speak` |
| `actions/IDENTIFY.json` | `SCREEN`, `LEGS`, `LIGHT` | `AUDIO_OUT` | `body`, `emotion`, `light`, `speak` |
| `actions/JUMP_AHEAD.json` | `LIGHT`, `SCREEN`, `LEGS`, `HEAD` | `AUDIO_OUT` | `body`, `emotion`, `light`, `speak` |
| `actions/JUMP_FORWARD.json` | `LIGHT`, `SCREEN`, `LEGS`, `HEAD` | `AUDIO_OUT` | `body`, `head`, `emotion`, `light`, `speak` |
| `actions/JUMP_IN_PLACE.json` | `LIGHT`, `SCREEN`, `LEGS`, `HEAD` | `AUDIO_OUT` | `body`, `head`, `emotion`, `light`, `speak` |
| `actions/LICK_HAND.json` | `LIGHT`, `SCREEN`, `LEGS`, `HEAD` | `AUDIO_OUT` | `body`, `head`, `emotion`, `light`, `speak` |
| `actions/LOOKAROUND.json` | `LIGHT`, `SCREEN`, `LEGS`, `HEAD` | `AUDIO_OUT` | `head`, `emotion`, `light`, `speak` |
| `actions/LOOKFORWARD.json` | `LIGHT`, `SCREEN`, `LEGS`, `HEAD` | `AUDIO_OUT` | `head`, `emotion`, `light`, `speak` |
| `actions/LOOKLEFT.json` | `LIGHT`, `SCREEN`, `LEGS`, `HEAD` | `AUDIO_OUT` | `body`, `head`, `emotion`, `light`, `speak` |
| `actions/LOOKRIGHT.json` | `LIGHT`, `SCREEN`, `LEGS`, `HEAD` | `AUDIO_OUT` | `body`, `head`, `emotion`, `light`, `speak` |
| `actions/NEWYEAR_GREETING.json` | `LIGHT`, `SCREEN`, `LEGS`, `HEAD` | `AUDIO_OUT` | `body`, `head`, `emotion`, `light`, `speak` |
| `actions/PARTROLALERT.json` | `LIGHT`, `SCREEN`, `LEGS`, `HEAD` | `AUDIO_OUT` | `head`, `emotion`, `light`, `speak` |
| `actions/PEE.json` | `LIGHT`, `SCREEN`, `LEGS`, `HEAD` | `AUDIO_OUT` | `body`, `head`, `emotion`, `light`, `speak` |
| `actions/PIANO.json` | `LIGHT`, `SCREEN`, `LEGS`, `HEAD` | `AUDIO_OUT` | `body`, `head`, `emotion`, `light`, `speak` |
| `actions/PIG.json` | `LIGHT`, `SCREEN`, `LEGS`, `HEAD` | `AUDIO_OUT` | `body`, `head`, `emotion`, `light`, `speak` |
| `actions/PILATES_D.json` | `LIGHT`, `SCREEN`, `LEGS`, `HEAD` | `AUDIO_OUT` | `body`, `head`, `emotion`, `light`, `speak` |
| `actions/POSE_C.json` | `LIGHT`, `SCREEN`, `LEGS`, `HEAD` | `AUDIO_OUT` | `body`, `head`, `emotion`, `light`, `speak` |
| `actions/POSE_D.json` | `LIGHT`, `SCREEN`, `LEGS`, `HEAD` | `AUDIO_OUT` | `body`, `head`, `emotion`, `light`, `speak` |
| `actions/POSE_E.json` | `LIGHT`, `SCREEN`, `LEGS`, `HEAD` | `AUDIO_OUT` | `body`, `head`, `emotion`, `light`, `speak` |
| `actions/POSE_F.json` | `LIGHT`, `SCREEN`, `LEGS`, `HEAD` | `AUDIO_OUT` | `body`, `head`, `emotion`, `light`, `speak` |
| `actions/PUSHUP.json` | `LIGHT`, `SCREEN`, `LEGS`, `HEAD` | `AUDIO_OUT` | `body`, `head`, `emotion`, `light`, `speak` |
| `actions/RELAXED_SWING.json` | `LIGHT`, `SCREEN`, `LEGS`, `HEAD` | `AUDIO_OUT` | `body`, `head`, `emotion`, `light`, `speak` |
| `actions/REPORT.json` | `SCREEN`, `LEGS`, `LIGHT` | `AUDIO_OUT` | `body`, `emotion`, `light`, `speak` |
| `actions/RHYTHM.json` | `LIGHT`, `SCREEN`, `LEGS`, `HEAD` | `AUDIO_OUT` | `body`, `head`, `emotion`, `light`, `speak` |
| `actions/RHYTHMIC_SWING.json` | `LIGHT`, `SCREEN`, `LEGS`, `HEAD` | `AUDIO_OUT` | `body`, `head`, `emotion`, `light`, `speak` |
| `actions/ROCKYOU.json` | `LIGHT`, `SCREEN`, `LEGS`, `HEAD` | `AUDIO_OUT` | `body`, `head`, `emotion`, `light`, `speak` |
| `actions/RUB_LEG_L.json` | `LIGHT`, `SCREEN`, `LEGS`, `HEAD` | `AUDIO_OUT` | `body`, `head`, `emotion`, `light`, `speak` |
| `actions/RUB_LEG_R.json` | `LIGHT`, `SCREEN`, `LEGS`, `HEAD` | `AUDIO_OUT` | `body`, `head`, `emotion`, `light`, `speak` |
| `actions/SAXOPHONE.json` | `LIGHT`, `SCREEN`, `LEGS`, `HEAD` | `AUDIO_OUT` | `body`, `head`, `emotion`, `light`, `speak` |
| `actions/SAYNO.json` | `LIGHT`, `SCREEN`, `LEGS`, `HEAD` | `AUDIO_OUT` | `body`, `head`, `emotion`, `light`, `speak` |
| `actions/SAYYES.json` | `LIGHT`, `SCREEN`, `LEGS`, `HEAD` | `AUDIO_OUT` | `body`, `head`, `emotion`, `light`, `speak` |
| `actions/SCRATCH_HEAD_L.json` | `LIGHT`, `SCREEN`, `LEGS`, `HEAD` | `AUDIO_OUT` | `body`, `head`, `emotion`, `light`, `speak` |
| `actions/SCRATCH_HEAD_R.json` | `LIGHT`, `SCREEN`, `LEGS`, `HEAD` | `AUDIO_OUT` | `body`, `head`, `emotion`, `light`, `speak` |
| `actions/SELF_INTRODUCTION.json` | `LIGHT`, `SCREEN`, `LEGS`, `HEAD` | `AUDIO_OUT` | `body`, `head`, `emotion`, `light`, `speak` |
| `actions/SHAKEHAND.json` | `SCREEN`, `LEGS`, `LIGHT` | `AUDIO_OUT` | `body`, `emotion`, `light`, `speak` |
| `actions/SHAKEHAND_L.json` | `SCREEN`, `LEGS`, `LIGHT` | `AUDIO_OUT` | `body`, `emotion`, `light`, `speak` |
| `actions/SITUP.json` | `LIGHT`, `SCREEN`, `LEGS`, `HEAD` | `AUDIO_OUT` | `body`, `head`, `emotion`, `light`, `speak` |
| `actions/SMELL.json` | `LIGHT`, `SCREEN`, `LEGS`, `HEAD` | `AUDIO_OUT` | `body`, `head`, `emotion`, `light`, `speak` |
| `actions/STRETCH_SLEEP.json` | `LIGHT`, `SCREEN`, `LEGS`, `HEAD` | `AUDIO_OUT` | `body`, `head`, `emotion`, `light`, `speak` |
| `actions/TICKLING_L.json` | `LIGHT`, `SCREEN`, `LEGS`, `HEAD` | `AUDIO_OUT` | `body`, `head`, `emotion`, `light`, `speak` |
| `actions/TICKLING_R.json` | `LIGHT`, `SCREEN`, `LEGS`, `HEAD` | `AUDIO_OUT` | `body`, `head`, `emotion`, `light`, `speak` |
| `actions/TILT_HEAD_LISTEN.json` | `LIGHT`, `SCREEN`, `LEGS`, `HEAD` | `AUDIO_OUT` | `body`, `head`, `emotion`, `light`, `speak` |
| `actions/TWIST_BUTT.json` | `LIGHT`, `SCREEN`, `LEGS`, `HEAD` | `AUDIO_OUT` | `body`, `head`, `emotion`, `light`, `speak` |
| `actions/VIOLIN.json` | `LIGHT`, `SCREEN`, `LEGS`, `HEAD` | `AUDIO_OUT` | `body`, `head`, `emotion`, `light`, `speak` |
| `actions/WAKEUP.json` | `SCREEN`, `LEGS`, `LIGHT` | `AUDIO_OUT` | `body`, `emotion`, `light`, `speak` |
| `actions/WAVE.json` | `LIGHT`, `SCREEN`, `LEGS`, `HEAD` | `AUDIO_OUT` | `body`, `head`, `emotion`, `light`, `speak` |
| `actions/rotate_360.json` | `LEGS` | `LIGHT`, `AUDIO_OUT` | `base_action`, `emotion`, `light`, `speak` |


身体轨迹、表情 ID 与灯光模式见[设备资源](../resources/README.zh-CN.md)。
