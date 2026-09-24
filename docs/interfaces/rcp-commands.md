# RCP NodeCommand field reference

<p align="center">English | <a href="rcp-commands.zh-CN.md">中文</a></p>

Start with the [Goal and DAG tutorial](../guides/rcp-dag.md). This page covers every
field of command. command_type selects the type; command contains its object,
e.g. SleepCommand pairs with `{"duration_ms":500}`.
Defaults below come from the [schema](../../schemas/aorta/schemas/service/rcp/function_input.fbs),
not necessarily every downstream service. An enum value does not establish support
on every robot: navigation and motion modes require their corresponding providers.

## Types, defaults and limits

bool accepts true/false; int is signed 32-bit (−2,147,483,648…2,147,483,647),
uint is unsigned 32-bit (0…4,294,967,295), and float is 32-bit floating point;
applications should use finite values. Strings/arrays without explicit defaults
are absent. Storage range is not physical range; the tables state business limits
where known and identify fields without universal limits. Use named enums, not
numeric values copied from another interface; BodyMethod differs from low-level motion enums.

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

Control a body mode or play a matching trajectory. Resource: LEGS. For supplied performances, retain the complete preset; this table does not expose its additional action_params.

| Field | Type | Schema default | Meaning / allowed values |
| --- | --- | --- | --- |
| `method` | `BodyMethod` | PASSIVE | Explicitly select a named BodyMethod below; default PASSIVE is not a harmless no-op. FIXED_LAYDOWN is not the coordinated down sequence. RL_WHEEL is a schema value, not foot-quadruped support. |
| `action_path` | `string` | Absent | Exact device trajectory filename from [body resources](../resources/body-trajectories.md), paired with its method. STREAM requires non-empty; RL_ACTION_POLICY1–4 forward it. Other current RCP body methods ignore it. Not a DAG path or local upload. |
| `pre_check` | `bool` | false | Boolean precheck selector; not authorization or a universal read-only dry run. Preserve the preset's checking flow. |

method enum: `PASSIVE`, `FIXED_STAND`, `FIXED_LAYDOWN`, `SAFE_STOP_SEQUENCE`, `SAFE_LAYDOWN_SEQUENCE`, `RL`, `RL_TROT`, `MPC`, `STREAM`, `PILOT`, `RL_ACTION_POLICY1`, `RL_ACTION_POLICY2`, `RL_ACTION_POLICY3`, `RL_ACTION_POLICY4`, `RL_WHEEL`.

## HeadCommand

Select CSV identifiers from [head trajectory resources](../resources/head-trajectories.md).

Control head angles or a head trajectory. Resource: HEAD. Choose one input: target_angles or action_path; angles take precedence. Both empty reset to neutral.

| Field | Type | Schema default | Meaning / allowed values |
| --- | --- | --- | --- |
| `method` | `HeadMethod` | ANGLE_CONTROL | ANGLE_CONTROL or STREAM; actual current dispatch is selected by the populated angle/path fields. Keep method consistent with that selection. |
| `pre_check` | `bool` | false | Boolean. With a trajectory, preparation returns the head to neutral; it can move the head. Without a trajectory the precheck returns early. |
| `duration_ms` | `int` | 0 | Target-angle duration in ms; current RCP implementation clamps values below 5000 to 5000. Not a trajectory playback timeout. |
| `loop_enabled` | `bool` | false | Repeat the head trajectory when true; provide explicit cancellation and a finite phase rather than expecting natural completion. |
| `playback_rate` | `float` | 1.0 | Float in schema; current RCP head task does not consume this field. Keep 1.0; do not rely on it to change speed. |
| `target_angles` | `[float]` | Absent | Exactly two finite radians [pitch, yaw]. Physical bounds depend on robot configuration; no universal safe range is supplied by this schema. Do not guess limits. |
| `action_path` | `string` | Absent | Device head trajectory filename, e.g. WAVE.csv in the wave preset; not WAVE_50hz.npz. Preserve the complete paired behavior. |

method enum: `ANGLE_CONTROL`, `STREAM`.

## LightCommand

Set a light layer. Resource: LIGHT. Modes are listed in [light resources](../resources/lights.md). Use DAEMON plus a finite phase and BARRIER, or a supported finite DSL task.

| Field | Type | Schema default | Meaning / allowed values |
| --- | --- | --- | --- |
| `method` | `LightMethod` | FIXED_COLOR | One of the six LightMethod values below. Typed FIXED_COLOR / CIRCLE_AND_FLASH correspond to DSL light.FIXEDCOLOR / light.CIRCLEANDFLASH. |
| `red` | `uint` | 0 | 0–255 red component; uint32 encoding does not make larger values valid. |
| `green` | `uint` | 0 | 0–255 green component. |
| `blue` | `uint` | 0 | 0–255 blue component. |
| `brightness` | `uint` | 255 | 0–255 brightness. |
| `speed` | `float` | 1.0 | Finite effect parameter, not ms or seconds. Keep 1.0 without a mode-specific contract; no universal effect-speed range is defined here. |
| `duration_ms` | `int` | 0 | Current RCP light task does not use this to finish a node. Keep 0; use lifecycle or DSL play_for_ms. |
| `layer` | `DisplayLayer` | UNSPECIFIED | UNSPECIFIED leaves the task default INTERACTION. For ordinary user output explicitly use INTERACTION. Other schema values: AMBIENT, MISSION, ANIMATION, WARNING, SAFETY; do not override safety indications. |
| `sync` | `bool` | false | Current task does not use this to bound its hold. Keep false. |

method enum: `FIXED_COLOR`, `GRADIENT`, `BREATHING`, `FLASHING`, `CIRCLE_AND_FLASH`, `PULSE`.

## EmotionCommand

Display a screen expression. Resource: SCREEN. Select an ID from [expression resources](../resources/expressions.md). This is not a body animation.

| Field | Type | Schema default | Meaning / allowed values |
| --- | --- | --- | --- |
| `method` | `EmotionMethod` | UNSPECIFIED | Named alias below, not a numeric asset ID. UNSPECIFIED dispatches via BLINK_ONCE. HAPPY resolves to 19; SAY_HI to 48. |
| `emotion_id` | `uint` | 0 | Use an ID actually listed in the resource catalog, not an arbitrary uint32. Nonzero overrides the method alias. For ID 0 use BLINK_ONCE (or UNSPECIFIED), not another alias plus zero. |
| `duration_ms` | `int` | 0 | Int32 playback/loop timing forwarded to display; -1 preserves the display default. Not RCP hold duration. A method name ending in 10S does not guarantee node completion in 10 seconds. |
| `layer` | `DisplayLayer` | UNSPECIFIED | UNSPECIFIED leaves the task default INTERACTION. For ordinary user output explicitly use INTERACTION. Other schema values: AMBIENT, MISSION, ANIMATION, WARNING, SAFETY; do not override safety indications. |
| `sync` | `bool` | false | Current task does not use this to end the hold. Keep false; use lifecycle or DSL play_for_ms. |

method enum: `UNSPECIFIED`, `BLINK_ONCE`, `WINK_10S`, `LISTEN_10S`, `SAD_10S`, `HAPPY_10S`, `HAPPY_30S`, `CONFOUND_3S`, `TIMID_15S`, `COURAGE_15S`, `COURAGE_30S`, `FEAR_10S`, `ANGRY_10S`, `DIZZY_30S`, `SURPRISE_20S`, `ANGRY`, `BLINK_MANY`, `COURAGE`, `DIZZY`, `FEAR_COURAGE`, `HAPPY`, `LISTEN`, `SHY`, `SLEEPING`, `SLEEPY`, `SWEATY`, `TALK`, `WAKEUP`, `WINK`, `WRONGED`, `STREAM`, `DOG_BARKING`, `SAY_HI`, `HAPPY_BIRTHDAY`, `HIGH_FIVE`, `LUNGE_FORWARD`, `NEW_YEAR`, `RHYTHMIC_SWING`, `FEAR_ALT`, `COURAGE_ALT`, `HAPPY_ALT`, `DEFAULT_EMOTION`, `LONG_TALK`.

## SpeakCommand

Play a supplied sound or synthesize speech. Resource: AUDIO_OUT. Does not automatically apply a harness personality or greeting prefix.

| Field | Type | Schema default | Meaning / allowed values |
| --- | --- | --- | --- |
| `method` | `SpeakMethod` | MACHINE_LANGUAGE | MACHINE_LANGUAGE selects a device sound; HUMAN_VOICE selects speech text. |
| `text` | `string` | Absent | Non-empty speech text for HUMAN_VOICE when human_language_text is empty; ignored for MACHINE_LANGUAGE. |
| `machine_language_name` | `string` | Absent | Existing sound name for MACHINE_LANGUAGE, e.g. confirm; not free text, an expression ID or a local audio path. |
| `human_language_text` | `string` | Absent | Non-empty HUMAN_VOICE text; if present, takes precedence over text. Prefer filling only one of the two. |

method enum: `MACHINE_LANGUAGE`, `HUMAN_VOICE`.

## VlnCommand

Primitive visual-navigation operation. Movement and navigation providers must be available; schema presence alone is not a ready-to-use navigation workflow. This command does not own full mode entry/restoration.

| Field | Type | Schema default | Meaning / allowed values |
| --- | --- | --- | --- |
| `method` | `VlnMethod` | FOLLOW | Named VlnMethod below. Coordinate fields are forwarded only for NAV_TO_POINT; other methods ignore them. |
| `x` | `float` | 0.0 | NAV_TO_POINT finite x coordinate in metres, interpreted in frame. |
| `y` | `float` | 0.0 | NAV_TO_POINT finite y coordinate in metres, interpreted in frame. |
| `frame` | `string` | Absent | NAV_TO_POINT coordinate frame string; omission retains task default local. Use a documented provider frame, not an assumed ROS map/odom alias. |
| `stop_distance` | `float` | 0.0 | Finite nonnegative arrival tolerance in metres for navigation. 0 is the wire default; do not interpret it as guaranteed zero-error arrival. |

method enum: `FOLLOW`, `ROAM`, `NAV_TO_POINT`, `COME_TO_ME`, `WALK`, `STOP`, `WALK_WITH_MPC`.

## VlnSessionCommand

Owns a visual-navigation session: enter the needed motion mode, run navigation and restore the previous mode on exit/cancel. Depends on the corresponding device providers; not just a different name for VlnCommand.

| Field | Type | Schema default | Meaning / allowed values |
| --- | --- | --- | --- |
| `method` | `VlnSessionMethod` | FOLLOW | Named VlnSessionMethod below; NAV_TO_POINT uses coordinates, semantic methods use prompt; other fields are ignored for other methods. |
| `x` | `float` | 0.0 | NAV_TO_POINT finite x coordinate in metres, interpreted in frame. |
| `y` | `float` | 0.0 | NAV_TO_POINT finite y coordinate in metres, interpreted in frame. |
| `frame` | `string` | Absent | NAV_TO_POINT coordinate frame string; omission retains task default local. Use a documented provider frame, not an assumed ROS map/odom alias. |
| `stop_distance` | `float` | 0.0 | Finite nonnegative arrival tolerance in metres for navigation. 0 is the wire default; do not interpret it as guaranteed zero-error arrival. |
| `prompt` | `string` | Absent | Non-empty string for SYNC_SEMANTIC_NAV / ASYNC_SEMANTIC_NAV. Other methods do not forward it. |

method enum: `FOLLOW`, `ROAM`, `NAV_TO_POINT`, `COME_TO_ME`, `WALK`, `SYNC_SEMANTIC_NAV`, `ASYNC_SEMANTIC_NAV`.

## LocomotionCommand

Select a high-level motion mode or posture operation; resource LEGS. Prefer supplied stand/down presets, which preserve coordinated behavior.

| Field | Type | Schema default | Meaning / allowed values |
| --- | --- | --- | --- |
| `method` | `LocomotionMethod` | SET_MODE | SET_MODE, STAND_UP, LIE_DOWN or STOP. The preset stand flow can use a DSL operation not represented by this enum; do not assume equivalence. |
| `mode` | `uint` | 0 | Used only by SET_MODE. Wire uint32, current task consumes uint8 (0–255); only provider-defined mode IDs are valid. It is not BodyMethod. Do not invent a mode from an enum number. |

method enum: `SET_MODE`, `STAND_UP`, `LIE_DOWN`, `STOP`.

## BaseActionCommand

Bounded basic movement, navigation or head operation. Motion generally requires LEGS; MOVE_HEAD uses HEAD. Choose one method and fill only its relevant fields.

| Field | Type | Schema default | Meaning / allowed values |
| --- | --- | --- | --- |
| `method` | `BaseActionMethod` | ROTATE | ROTATE uses angle_rad; MOVE_FORWARD/BACKWARD/LEFT/RIGHT use distance_m; NAVIGATE_TO uses x/y/stop_distance; MOVE_HEAD uses angle_rad as pitch and x as yaw. |
| `angle_rad` | `float` | 0.0 | Finite signed radians for rotation; for MOVE_HEAD this means pitch. No universal physical range is specified by this schema. |
| `distance_m` | `float` | 0.0 | Positive finite metres for directional movement; choose direction with method, not a negative distance. Bound movement to the safe available space. |
| `x` | `float` | 0.0 | NAVIGATE_TO x coordinate in metres under its provider's coordinate contract; MOVE_HEAD yaw in radians. No frame field exists in this type. |
| `y` | `float` | 0.0 | NAVIGATE_TO y coordinate in metres; unused for MOVE_HEAD. |
| `stop_distance` | `float` | 0.0 | Finite nonnegative arrival tolerance in metres for navigation. 0 is the wire default; do not interpret it as guaranteed zero-error arrival. |

method enum: `ROTATE`, `MOVE_FORWARD`, `MOVE_BACKWARD`, `MOVE_LEFT`, `MOVE_RIGHT`, `NAVIGATE_TO`, `MOVE_HEAD`.

## NavigateCommand

Rotate in place; resource LEGS. Not a generic map-navigation command.

| Field | Type | Schema default | Meaning / allowed values |
| --- | --- | --- | --- |
| `method` | `NavigateMethod` | ROTATE_IN_PLACE | Only ROTATE_IN_PLACE. |
| `angle_rad` | `float` | 0.0 | Finite signed radians. Positive/negative direction follows the navigation provider; do not infer a safe amplitude from the float storage range. |

method enum: `ROTATE_IN_PLACE`.

## SleepCommand

Finite delay with no actuator resource; use NORMAL. Useful for sequencing or joining branches.

| Field | Type | Schema default | Meaning / allowed values |
| --- | --- | --- | --- |
| `duration_ms` | `int` | 0 | Nonnegative int32 milliseconds, 0…2,147,483,647. Use small intentional waits; a positive node timeout must allow the wait to finish. |

## BarrierCommand

Empty payload {}. Use lifecycle BARRIER and dependencies on the finite work ending the phase. Cancels all graph-held daemons; it is not a selective resource release or ordinary join.

## DslTaskCommand

For configurable motion parameters and composition, see [motion parameter reference](motion-parameters.md).

Escape hatch for a registered DSL task whose parameters are absent from typed commands. Not shell execution, arbitrary code, or a nested-preset loader.

| Field | Type | Schema default | Meaning / allowed values |
| --- | --- | --- | --- |
| `task` | `string` | Absent | Exact supported canonical key, e.g. emotion.HAPPY or light.FIXEDCOLOR. Do not infer supported tasks from arbitrary strings. |
| `args_json` | `string` | Absent | A string encoding a JSON object. Empty means {}; arrays/scalars are rejected. For finite expression/light hold, encode play_for_ms > 0, e.g. {"layer":"INTERACTION","play_for_ms":1500}, then use NORMAL. No other typed field name automatically becomes a supported DSL parameter. |

## Hold duration and resource association

Typed LightCommand/EmotionCommand do not have play_for_ms. Light duration_ms does
not end the hold; expression duration_ms is display playback timing, and sync does
not fill this gap. Use DAEMON with finite work and BARRIER for typed output phases.
For a self-finishing NORMAL node, use a supported DslTaskCommand with explicit play_for_ms > 0.

Body filenames go into action_path, expression IDs into emotion_id, and lights use
method and color. They are not interchangeable. See [device resources](../resources/README.md)
and the [composition walkthrough](../guides/rcp-dag.md).
