# Body trajectory resources

For configurable motion parameters and composition, see [motion parameter reference](../interfaces/motion-parameters.md).

<p align="center">English | <a href="body-trajectories.zh-CN.md">中文</a></p>

For invocation choices and field mappings, see [direct services versus RCP](../guides/control-paths.md).

Copy a resource name exactly into `BodyCommand.action_path` (Python object field
`actionPath`) and pair it with the `method` in the same row. These are device-side
body trajectories, not expression IDs, head CSVs or DAG JSON files.
The table lists 71 distinct body trajectories used by the [RCP presets](../guides/rcp-presets.md), not every
trajectory file installed on a robot. Descriptions identify performance themes,
not guaranteed amplitude, duration or environmental interaction. L/R preserve the
resource's left/right naming. Chasing, sniffing and listening names describe
performances; they do not automatically enable tracking or perception.

**All corresponding presets include additional `action_params` that the current
BodyCommand does not fully expose.** To perform a supplied behavior, use the last
column as `DagPresetRef.relative_path` and retain the full preset's resources,
transitions and companion nodes. This table is not a standalone executable example
using only a method and filename. Use the basic stand/coordinated-down [RCP presets](../guides/rcp-presets.md);
they do not require a similarly named trajectory from this table.
See the [field rules](../guides/rcp-dag.md).

For custom graphs, use DslTaskCommand with supported action_params rather than copying
every preset. Select parameter values using the motion reference and resource constraints;
the preset column is an optional ready-made entry, not a requirement for customization.

For companion CSV files and exact preset pairings, see [head trajectories](head-trajectories.md).
For example, WAVE_50hz.npz goes into BodyCommand, while WAVE.csv goes into HeadCommand.

| Body trajectory resource (action_path) | Matching BodyCommand.method | Description | Complete preset |
| --- | --- | --- | --- |
| `BACK_OFF_50hz.npz` | `RL_ACTION_POLICY2` | Back-off performance | `actions/BACK_OFF.json` |
| `BOW_NEW_YEAR_50hz.npz` | `RL_ACTION_POLICY1` | New Year bow | `actions/BOW_NEW_YEAR.json` |
| `CAT_50hz.npz` | `RL_ACTION_POLICY1` | Cat imitation | `actions/CAT.json` |
| `CHASE_BALL_50hz.npz` | `RL_ACTION_POLICY1` | Ball-chasing performance; not ball tracking | `actions/CHASE_BALL.json` |
| `CHEEKY_50hz.npz` | `RL_ACTION_POLICY1` | Cheeky performance | `actions/CHEEKY.json` |
| `CHEER_L_50hz.npz` | `RL_ACTION_POLICY1` | Left cheer | `actions/CHEER_L.json` |
| `CHEER_R_50hz.npz` | `RL_ACTION_POLICY1` | Right cheer | `actions/CHEER_R.json` |
| `CONDUCT_50hz.npz` | `RL_ACTION_POLICY2` | Conductor performance | `actions/CONDUCT.json` |
| `CRAWL_50hz.npz` | `RL_ACTION_POLICY1` | Crawling performance | `actions/CRAWL.json` |
| `CURIOUS_50hz.npz` | `RL_ACTION_POLICY1` | Curiosity performance | `actions/CURIOUS.json` |
| `DIG_HOLE_50hz.npz` | `RL_ACTION_POLICY1` | Digging performance | `actions/DIG_HOLE.json` |
| `DIZZINESS_50hz.npz` | `RL_ACTION_POLICY1` | Dizziness performance; also reused by grievance presets | `actions/DIZZINESS.json`, `actions/GRIEVANCE.json`, `actions/GRIEVANCE_APP.json` |
| `DOG_50hz.npz` | `RL_ACTION_POLICY1` | Dog imitation | `actions/DOG.json` |
| `DOG_BARK_50hz.npz` | `RL_ACTION_POLICY1` | Barking body motion; audio is separate | `actions/DOG_BARK.json` |
| `DRUM_50hz.npz` | `RL_ACTION_POLICY1` | Drum performance | `actions/DRUM.json` |
| `DRUMER_50hz.npz` | `RL_ACTION_POLICY1` | Drummer performance variant | `actions/DRUMER.json` |
| `ELEPHANT_50hz.npz` | `RL_ACTION_POLICY1` | Elephant imitation | `actions/ELEPHANT.json` |
| `EXCITED_50hz.npz` | `RL_ACTION_POLICY1` | Excitement performance | `actions/EXCITED.json` |
| `FORTUNE_CAT_50hz.npz` | `RL_ACTION_POLICY1` | Lucky-cat gesture | `actions/FORTUNE_CAT.json` |
| `FORTUNE_CAT_L_50hz.npz` | `RL_ACTION_POLICY1` | Left lucky-cat gesture | `actions/FORTUNE_CAT_L.json` |
| `GUITAR_50hz.npz` | `RL_ACTION_POLICY1` | Guitar performance | `actions/GUITAR.json` |
| `HAPPY_BOUNCE_50hz.npz` | `RL_ACTION_POLICY2` | Happy bounce used by HAPPY_JUMP | `actions/HAPPY_JUMP.json` |
| `HAPPY_BOUNCE_B_50hz.npz` | `RL_ACTION_POLICY2` | Happy bounce, B variant | `actions/HAPPY_BOUNCE_B.json` |
| `HAPPY_LITTLE_JUMP_50hz.npz` | `RL_ACTION_POLICY1` | Small happy jump | `actions/HAPPY_LITTLE_JUMP.json` |
| `HAPPYBIRTHDAY_50hz.npz` | `RL_ACTION_POLICY1` | Birthday performance | `actions/HAPPYBIRTHDAY.json` |
| `HEN_50hz.npz` | `RL_ACTION_POLICY1` | Hen imitation | `actions/HEN.json` |
| `HIGH_FIVE_L_50hz.npz` | `RL_ACTION_POLICY1` | Left high five | `actions/HIGH_FIVE_L.json` |
| `HIGH_FIVE_R_50hz.npz` | `RL_ACTION_POLICY1` | Right high five | `actions/HIGH_FIVE_R.json` |
| `HOWL_LIKE_WOLF_50hz.npz` | `RL_ACTION_POLICY1` | Wolf-howling body motion; audio is separate | `actions/HOWL_LIKE_WOLF.json` |
| `IDENTIFY_50hz.npz` | `RL_ACTION_POLICY1` | IDENTIFY themed performance; not a recognition API | `actions/IDENTIFY.json` |
| `JUMP_AHEAD_50hz.npz` | `RL_ACTION_POLICY2` | Forward jump, JUMP_AHEAD variant | `actions/JUMP_AHEAD.json` |
| `JUMP_FORWARD_50hz.npz` | `RL_ACTION_POLICY2` | Forward jump, JUMP_FORWARD variant | `actions/JUMP_FORWARD.json` |
| `JUMP_IN_PLACE_50hz.npz` | `RL_ACTION_POLICY1` | Jump in place | `actions/JUMP_IN_PLACE.json` |
| `LICK_HAND_50hz.npz` | `RL_ACTION_POLICY1` | Hand-licking performance | `actions/LICK_HAND.json` |
| `LOOKLEFT_50hz.npz` | `RL_ACTION_POLICY1` | Look-left body motion | `actions/LOOKLEFT.json` |
| `LOOKRIGHT_50hz.npz` | `RL_ACTION_POLICY1` | Look-right body motion | `actions/LOOKRIGHT.json` |
| `NEWYEAR_GREETING_50hz.npz` | `RL_ACTION_POLICY1` | New Year greeting | `actions/NEWYEAR_GREETING.json` |
| `PEE_50hz.npz` | `RL_ACTION_POLICY1` | Urination imitation | `actions/PEE.json` |
| `PIANO_50hz.npz` | `RL_ACTION_POLICY1` | Piano performance | `actions/PIANO.json` |
| `PIG_50hz.npz` | `RL_ACTION_POLICY1` | Pig imitation | `actions/PIG.json` |
| `PILATES_D_50hz.npz` | `RL_ACTION_POLICY1` | Pilates, D variant | `actions/PILATES_D.json` |
| `PoseC_50hz.npz` | `RL_ACTION_POLICY2` | Pose C performance | `actions/POSE_C.json` |
| `PoseD_50hz.npz` | `RL_ACTION_POLICY2` | Pose D performance | `actions/POSE_D.json` |
| `PoseE_50hz.npz` | `RL_ACTION_POLICY2` | Pose E performance | `actions/POSE_E.json` |
| `PoseF_50hz.npz` | `RL_ACTION_POLICY2` | Pose F performance | `actions/POSE_F.json` |
| `PUSHUP_50hz.npz` | `RL_ACTION_POLICY1` | Push-up performance | `actions/PUSHUP.json` |
| `RELAXED_SWING_50hz.npz` | `RL_ACTION_POLICY1` | Relaxed sway | `actions/RELAXED_SWING.json` |
| `REPORT_50hz.npz` | `RL_ACTION_POLICY1` | REPORT themed performance; not status reporting | `actions/REPORT.json` |
| `RHYTHM_50hz.npz` | `RL_ACTION_POLICY1` | Rhythm performance | `actions/RHYTHM.json` |
| `RHYTHMIC_SWING_50hz.npz` | `RL_ACTION_POLICY1` | Rhythmic sway | `actions/RHYTHMIC_SWING.json` |
| `ROCKYOU_50hz.npz` | `RL_ACTION_POLICY3` | ROCKYOU dance | `actions/ROCKYOU.json` |
| `RUB_LEG_L_50hz.npz` | `RL_ACTION_POLICY1` | Left leg-rubbing performance | `actions/RUB_LEG_L.json` |
| `RUB_LEG_R_50hz.npz` | `RL_ACTION_POLICY1` | Right leg-rubbing performance | `actions/RUB_LEG_R.json` |
| `SAXOPHONE_50hz.npz` | `RL_ACTION_POLICY1` | Saxophone performance | `actions/SAXOPHONE.json` |
| `SAYNO_50hz.npz` | `RL_ACTION_POLICY1` | No gesture | `actions/SAYNO.json` |
| `SAYYES_50hz.npz` | `RL_ACTION_POLICY1` | Yes gesture | `actions/SAYYES.json` |
| `SCRATCH_HEAD_L_50hz.npz` | `RL_ACTION_POLICY1` | Left head-scratching performance | `actions/SCRATCH_HEAD_L.json` |
| `SCRATCH_HEAD_R_50hz.npz` | `RL_ACTION_POLICY1` | Right head-scratching performance | `actions/SCRATCH_HEAD_R.json` |
| `SELF_INTRODUCTION_50hz.npz` | `RL_ACTION_POLICY1` | Self-introduction body motion; speech is separate | `actions/SELF_INTRODUCTION.json` |
| `SHAKEHAND_50hz.npz` | `RL_ACTION_POLICY1` | Handshake | `actions/SHAKEHAND.json` |
| `SHAKEHAND_L_50hz.npz` | `RL_ACTION_POLICY1` | Left handshake | `actions/SHAKEHAND_L.json` |
| `SITUP_50hz.npz` | `RL_ACTION_POLICY1` | Sit-up performance | `actions/SITUP.json` |
| `SMELL_50hz.npz` | `RL_ACTION_POLICY1` | Sniffing performance; not an odor sensor | `actions/SMELL.json` |
| `STRETCH_SLEEP_50hz.npz` | `RL_ACTION_POLICY1` | Sleepy stretch | `actions/STRETCH_SLEEP.json` |
| `TICKLING_L_50hz.npz` | `RL_ACTION_POLICY1` | Left tickling reaction | `actions/TICKLING_L.json` |
| `TICKLING_R_50hz.npz` | `RL_ACTION_POLICY1` | Right tickling reaction | `actions/TICKLING_R.json` |
| `TILT_HEAD_LISTEN_50hz.npz` | `RL_ACTION_POLICY1` | Listening-themed body motion; not audio capture | `actions/TILT_HEAD_LISTEN.json` |
| `TWIST_BUTT_50hz.npz` | `RL_ACTION_POLICY1` | Hip twist | `actions/TWIST_BUTT.json` |
| `VIOLIN_50hz.npz` | `RL_ACTION_POLICY1` | Violin performance | `actions/VIOLIN.json` |
| `WAKEUP_50hz.npz` | `RL_ACTION_POLICY1` | Wake-up performance; not the stand-up sequence | `actions/WAKEUP.json` |
| `WAVE_50hz.npz` | `RL_ACTION_POLICY1` | Wave | `actions/WAVE.json` |


Back to [device resources](README.md); for RCP use, see the [node command reference](../interfaces/rcp-commands.md).
