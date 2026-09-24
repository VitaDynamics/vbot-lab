# Head trajectory resources

<p align="center">English | <a href="head-trajectories.zh-CN.md">中文</a></p>

This list contains 66 head CSV trajectories referenced by the current foot-quadruped EDU presets.
They are separate from [body NPZ trajectories](body-trajectories.md), not older body files replaced by NPZ.

## Select and fill in a resource

- For RCP, use `HeadCommand.method = STREAM` and copy the exact resource name into `action_path` (Python object field `actionPath`).
- Omit or empty `target_angles` when selecting a trajectory: angle input takes precedence. See [HeadCommand fields](../interfaces/rcp-commands.md#headcommand).
- The device service loads the file; clients need not open or upload it. Do not use a workstation path or DAG JSON name.
- Prefer the [complete preset](../guides/rcp-presets.md) for supplied performances, retaining coordinated body, head, light and expression nodes.
- NPZ names below identify body resources referenced by the same preset, not inputs to the head command. “—” means no explicit body trajectory reference, not an absence of other effects.
- Do not derive names by changing extensions: `HAPPY_JUMP.csv` pairs with `HAPPY_BOUNCE_50hz.npz`, and two lucky-cat presets share `FORTUNE_CAT.csv`.
- Descriptions identify the associated performance theme; the CSV alone does not implement the full behavior. Looping trajectories need explicit cancellation and a finite phase.

## Resource list

| Head resource (action_path) | HeadCommand.method | Associated performance theme | Body resource in the same preset | Complete preset |
| --- | --- | --- | --- | --- |
| `BACK_OFF.csv` | `STREAM` | Back-off performance | `BACK_OFF_50hz.npz` | `actions/BACK_OFF.json` |
| `BOW_NEW_YEAR.csv` | `STREAM` | New Year bow | `BOW_NEW_YEAR_50hz.npz` | `actions/BOW_NEW_YEAR.json` |
| `CAT.csv` | `STREAM` | Cat imitation | `CAT_50hz.npz` | `actions/CAT.json` |
| `CHASE_BALL.csv` | `STREAM` | Ball-chasing performance; not ball tracking | `CHASE_BALL_50hz.npz` | `actions/CHASE_BALL.json` |
| `CHEEKY.csv` | `STREAM` | Cheeky performance | `CHEEKY_50hz.npz` | `actions/CHEEKY.json` |
| `CHEER_L.csv` | `STREAM` | Left cheer | `CHEER_L_50hz.npz` | `actions/CHEER_L.json` |
| `CHEER_R.csv` | `STREAM` | Right cheer | `CHEER_R_50hz.npz` | `actions/CHEER_R.json` |
| `CONDUCT.csv` | `STREAM` | Conductor performance | `CONDUCT_50hz.npz` | `actions/CONDUCT.json` |
| `CRAWL.csv` | `STREAM` | Crawling performance | `CRAWL_50hz.npz` | `actions/CRAWL.json` |
| `CURIOUS.csv` | `STREAM` | Curiosity performance | `CURIOUS_50hz.npz` | `actions/CURIOUS.json` |
| `DIG_HOLE.csv` | `STREAM` | Digging performance | `DIG_HOLE_50hz.npz` | `actions/DIG_HOLE.json` |
| `DIZZINESS.csv` | `STREAM` | Dizziness performance; also reused by grievance presets | `DIZZINESS_50hz.npz` | `actions/DIZZINESS.json`, `actions/GRIEVANCE.json`, `actions/GRIEVANCE_APP.json` |
| `DOG_BARK.csv` | `STREAM` | Barking body motion; audio is separate | `DOG_BARK_50hz.npz` | `actions/DOG_BARK.json` |
| `DOG.csv` | `STREAM` | Dog imitation | `DOG_50hz.npz` | `actions/DOG.json` |
| `DRUM.csv` | `STREAM` | Drum performance | `DRUM_50hz.npz` | `actions/DRUM.json` |
| `DRUMER.csv` | `STREAM` | Drummer performance variant | `DRUMER_50hz.npz` | `actions/DRUMER.json` |
| `ELEPHANT.csv` | `STREAM` | Elephant imitation | `ELEPHANT_50hz.npz` | `actions/ELEPHANT.json` |
| `EXCITED.csv` | `STREAM` | Excitement performance | `EXCITED_50hz.npz` | `actions/EXCITED.json` |
| `FORTUNE_CAT.csv` | `STREAM` | Lucky-cat gesture | `FORTUNE_CAT_50hz.npz`, `FORTUNE_CAT_L_50hz.npz` | `actions/FORTUNE_CAT.json`, `actions/FORTUNE_CAT_L.json` |
| `GUITAR.csv` | `STREAM` | Guitar performance | `GUITAR_50hz.npz` | `actions/GUITAR.json` |
| `HAPPY_BOUNCE_B.csv` | `STREAM` | Happy bounce, B variant | `HAPPY_BOUNCE_B_50hz.npz` | `actions/HAPPY_BOUNCE_B.json` |
| `HAPPY_JUMP.csv` | `STREAM` | Happy jump performance | `HAPPY_BOUNCE_50hz.npz` | `actions/HAPPY_JUMP.json` |
| `HAPPY_LITTLE_JUMP.csv` | `STREAM` | Small happy jump | `HAPPY_LITTLE_JUMP_50hz.npz` | `actions/HAPPY_LITTLE_JUMP.json` |
| `HAPPYBIRTHDAY.csv` | `STREAM` | Birthday performance | `HAPPYBIRTHDAY_50hz.npz` | `actions/HAPPYBIRTHDAY.json` |
| `HEN.csv` | `STREAM` | Hen imitation | `HEN_50hz.npz` | `actions/HEN.json` |
| `HIGH_FIVE_L.csv` | `STREAM` | Left high five | `HIGH_FIVE_L_50hz.npz` | `actions/HIGH_FIVE_L.json` |
| `HIGH_FIVE_R.csv` | `STREAM` | Right high five | `HIGH_FIVE_R_50hz.npz` | `actions/HIGH_FIVE_R.json` |
| `HOWL_LIKE_WOLF.csv` | `STREAM` | Wolf-howling body motion; audio is separate | `HOWL_LIKE_WOLF_50hz.npz` | `actions/HOWL_LIKE_WOLF.json` |
| `JUMP_FORWARD.csv` | `STREAM` | Forward jump, JUMP_FORWARD variant | `JUMP_FORWARD_50hz.npz` | `actions/JUMP_FORWARD.json` |
| `JUMP_IN_PLACE.csv` | `STREAM` | Jump in place | `JUMP_IN_PLACE_50hz.npz` | `actions/JUMP_IN_PLACE.json` |
| `LICK_HAND.csv` | `STREAM` | Hand-licking performance | `LICK_HAND_50hz.npz` | `actions/LICK_HAND.json` |
| `LOOKAROUND.csv` | `STREAM` | Look-around performance | — | `actions/LOOKAROUND.json` |
| `LOOKFORWARD.csv` | `STREAM` | Forward-looking / alert performance | — | `actions/LOOKFORWARD.json`, `actions/PARTROLALERT.json` |
| `LOOKLEFT.csv` | `STREAM` | Look-left body motion | `LOOKLEFT_50hz.npz` | `actions/LOOKLEFT.json` |
| `LOOKRIGHT.csv` | `STREAM` | Look-right body motion | `LOOKRIGHT_50hz.npz` | `actions/LOOKRIGHT.json` |
| `NEWYEAR_GREETING.csv` | `STREAM` | New Year greeting | `NEWYEAR_GREETING_50hz.npz` | `actions/NEWYEAR_GREETING.json` |
| `PEE.csv` | `STREAM` | Urination imitation | `PEE_50hz.npz` | `actions/PEE.json` |
| `PIANO.csv` | `STREAM` | Piano performance | `PIANO_50hz.npz` | `actions/PIANO.json` |
| `PIG.csv` | `STREAM` | Pig imitation | `PIG_50hz.npz` | `actions/PIG.json` |
| `PILATES_D.csv` | `STREAM` | Pilates, D variant | `PILATES_D_50hz.npz` | `actions/PILATES_D.json` |
| `PoseC.csv` | `STREAM` | Pose C performance | `PoseC_50hz.npz` | `actions/POSE_C.json` |
| `PoseD.csv` | `STREAM` | Pose D performance | `PoseD_50hz.npz` | `actions/POSE_D.json` |
| `PoseE.csv` | `STREAM` | Pose E performance | `PoseE_50hz.npz` | `actions/POSE_E.json` |
| `PoseF.csv` | `STREAM` | Pose F performance | `PoseF_50hz.npz` | `actions/POSE_F.json` |
| `PUSHUP.csv` | `STREAM` | Push-up performance | `PUSHUP_50hz.npz` | `actions/PUSHUP.json` |
| `RELAXED_SWING.csv` | `STREAM` | Relaxed sway | `RELAXED_SWING_50hz.npz` | `actions/RELAXED_SWING.json` |
| `RHYTHM.csv` | `STREAM` | Rhythm performance | `RHYTHM_50hz.npz` | `actions/RHYTHM.json` |
| `RHYTHMIC_SWING.csv` | `STREAM` | Rhythmic sway | `RHYTHMIC_SWING_50hz.npz` | `actions/RHYTHMIC_SWING.json` |
| `ROCKYOU.csv` | `STREAM` | ROCKYOU dance | `ROCKYOU_50hz.npz` | `actions/ROCKYOU.json` |
| `RUB_LEG_L.csv` | `STREAM` | Left leg-rubbing performance | `RUB_LEG_L_50hz.npz` | `actions/RUB_LEG_L.json` |
| `RUB_LEG_R.csv` | `STREAM` | Right leg-rubbing performance | `RUB_LEG_R_50hz.npz` | `actions/RUB_LEG_R.json` |
| `SAXOPHONE.csv` | `STREAM` | Saxophone performance | `SAXOPHONE_50hz.npz` | `actions/SAXOPHONE.json` |
| `SAYNO.csv` | `STREAM` | No gesture | `SAYNO_50hz.npz` | `actions/SAYNO.json` |
| `SAYYES.csv` | `STREAM` | Yes gesture | `SAYYES_50hz.npz` | `actions/SAYYES.json` |
| `SCRATCH_HEAD_L.csv` | `STREAM` | Left head-scratching performance | `SCRATCH_HEAD_L_50hz.npz` | `actions/SCRATCH_HEAD_L.json` |
| `SCRATCH_HEAD_R.csv` | `STREAM` | Right head-scratching performance | `SCRATCH_HEAD_R_50hz.npz` | `actions/SCRATCH_HEAD_R.json` |
| `SELF_INTRODUCTION.csv` | `STREAM` | Self-introduction body motion; speech is separate | `SELF_INTRODUCTION_50hz.npz` | `actions/SELF_INTRODUCTION.json` |
| `SITUP.csv` | `STREAM` | Sit-up performance | `SITUP_50hz.npz` | `actions/SITUP.json` |
| `SMELL.csv` | `STREAM` | Sniffing performance; not an odor sensor | `SMELL_50hz.npz` | `actions/SMELL.json` |
| `STRETCH_SLEEP.csv` | `STREAM` | Sleepy stretch | `STRETCH_SLEEP_50hz.npz` | `actions/STRETCH_SLEEP.json` |
| `TICKLING_L.csv` | `STREAM` | Left tickling reaction | `TICKLING_L_50hz.npz` | `actions/TICKLING_L.json` |
| `TICKLING_R.csv` | `STREAM` | Right tickling reaction | `TICKLING_R_50hz.npz` | `actions/TICKLING_R.json` |
| `TILT_HEAD_LISTEN.csv` | `STREAM` | Listening-themed body motion; not audio capture | `TILT_HEAD_LISTEN_50hz.npz` | `actions/TILT_HEAD_LISTEN.json` |
| `TWIST_BUTT.csv` | `STREAM` | Hip twist | `TWIST_BUTT_50hz.npz` | `actions/TWIST_BUTT.json` |
| `VIOLIN.csv` | `STREAM` | Violin performance | `VIOLIN_50hz.npz` | `actions/VIOLIN.json` |
| `WAVE.csv` | `STREAM` | Wave | `WAVE_50hz.npz` | `actions/WAVE.json` |

Back to [device resources](README.md).
