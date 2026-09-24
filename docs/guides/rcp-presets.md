# RCP preset catalog

<p align="center">English | <a href="rcp-presets.zh-CN.md">中文</a></p>

Use this foot-quadruped EDU reference with the [DAG authoring guide](rcp-dag.md).
The device service loads presets; users need no access to their installation directory.
Pass exact relative names through `DagPresetRef.relative_path`.
Resource presence does not make a behavior suitable for every posture; admission depends
on current state and resources. Software versions can provide different sets.

Common entries: stand `action_stand_from_phone.json`; coordinated down
`action_down_from_phone.json`; sit `actions/SITUP.json`; wave `actions/WAVE.json`;
handshake `actions/SHAKEHAND.json` / `actions/SHAKEHAND_L.json`;
high five `actions/HIGH_FIVE_R.json` / `actions/HIGH_FIVE_L.json`;
birthday performance `actions/HAPPYBIRTHDAY.json`; head forward `atom/look_forward.json`.

Presets often combine body, head, expression, lights and sound; they are not individual
joint motions or `BodyCommand.method` values. They cannot be nested as preset nodes.
Sequence complete presets on the client, waiting for each successful terminal result.
Tables preserve resource declarations; `—` means none explicitly declared. Optional
resources may be skipped, not necessarily unused by nodes. See the authoring guide for
required template arguments.

## Basic posture and parameterized movement

Do not use action_sit_from_phone.json for sitting: its body node selects FIXED_LAYDOWN.
For configurable motion and composition, see [motion parameter reference](../interfaces/motion-parameters.md).

| Relative preset name | required_resources | optional_resources | Node families |
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

## Performance presets

Performances, jumps and spins need sufficient space, a suitable posture and an onsite
stopping procedure. Names do not establish amplitude, duration or payload capacity;
preserve the complete preset's transition settings and checks.

| Relative preset name | required_resources | optional_resources | Node families |
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


For body trajectories, expression IDs and light modes, see [device resources](../resources/README.md).
