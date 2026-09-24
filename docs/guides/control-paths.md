# Choose RCP or a direct service

<p align="center">English | <a href="control-paths.zh-CN.md">中文</a></p>

The same device resources can be reached through different interfaces.
RCP adds orchestration and task lifecycle; a direct service requests one provider operation.
Neither changes the meaning of a trajectory resource or expression asset ID.

## Which should I use?

| Situation | Recommended entry | Reason |
| --- | --- | --- |
| Run a supplied wave, dance, stand/down performance | RCP DagPresetRef | Retains the preset's parameters, transitions and coordinated head/body/peripheral nodes |
| Compose expression, lights, speech and motion in phases | RCP DagSpec | Dependencies, graph resource admission, feedback, cancellation and held-task cleanup |
| One display operation in an application that owns display control | Direct play_emotion service | No graph required; application handles duration, restoration and conflicts |
| A single body operation with a known full control contract | Direct lowlevel_action service | Application owns request correlation, posture checks, parameters, reports and recovery |
| Already have a controller/scheduler managing robot operations | Direct services may fit | Avoid introducing a second scheduler, but provide equivalent ownership and recovery logic |
| Only know a trajectory filename, without its policy/transition parameters | Supplied RCP preset | A filename is not a complete motion request |

RCP does not make an arbitrary motion graph safe. Direct calls still follow device-side
checks, but do **not** automatically inherit RCP graph admission, resource ownership,
precheck orchestration or cancellation. Neither a service response nor an accepted Goal
proves physical completion.

## Body: one resource, different mode enums

| Meaning | Direct /locomotion/lowlevel_action | RCP BodyCommand |
| --- | --- | --- |
| Start the operation | target_state = 1 | Body task constructs the start request |
| Choose wave's body policy | mode = LowlevelActionMode.RL_ACTION_POLICY1 (100) | method = BodyMethod.RL_ACTION_POLICY1 (10) |
| Choose wave's body resource | action_path = WAVE_50hz.npz | action_path = WAVE_50hz.npz |
| Extra runtime parameters | action_params_json: JSON-object string | Not exposed by typed BodyCommand; supplied presets preserve their action_params |
| Correlate progress/completion | Application req_id and matching body reports | Action Goal identity, feedback and terminal result; RCP handles child requests |
| Precheck | pre_check selects provider preparation/check phase | Node pre_check plus graph's automatic batch-precheck flow; not identical to one direct check |

The values 100 and 10 above belong to **different enum domains**. RCP translates by
method name; never send the numeric BodyMethod directly to the service.
The same distinction applies to policy2–4 (direct 101–103 versus RCP 11–13).
Use generated named constants from each interface's own schema.

This table is a field mapping, not a complete wave execution example.
Both paths load the resource on the device; neither action_path uploads a local file
or selects a DAG. For a full wave use `DagPresetRef.relative_path = "actions/WAVE.json"`.
For the companion `WAVE.csv`, use the head interface/HeadCommand, not the body service.
See [body resources](../resources/body-trajectories.md) and [head resources](../resources/head-trajectories.md).

The direct request also carries optional aorta_header metadata. Set target_state explicitly:
its default 0 means OFF, not start. A stop request is not an RCP Goal cancellation;
do not use it against a different control owner's work.
Preserve the original action parameters instead of weakening checks to get a request accepted.

For a direct body operation, subscribe before sending, use a distinct req_id, inspect
status/error_code/error_detail, and match execution-stage reports for that request.
A controller-start result may still require subsequent posture confirmation.
Follow the [motion workflow](../interfaces/locomotion.md); a timeout is an unknown
outcome, not permission to automatically retry.
Core standing uses set_run_mode, not a guessed lowlevel mode based on the word “stand”.

## Expression: resource ID is mode in the direct service

| Meaning | Direct /display_node/play_emotion | RCP EmotionCommand |
| --- | --- | --- |
| Display 048_say_hi | target_state = 1, mode = 48 | emotion_id = 48; method may be BLINK_ONCE because a nonzero ID wins |
| Choose by alias | No EmotionMethod field | method = SAY_HI resolves to asset ID 48 |
| Blink asset 000_blink_once | mode = 0 with target_state = 1 | emotion_id = 0 with BLINK_ONCE or UNSPECIFIED |
| Playback timing | duration_ms is sent to display | duration_ms is forwarded to display, not RCP hold time |
| Layer ownership | No layer field | layer selects RCP's peripheral layer, normally INTERACTION |
| End output | Provider duration behavior or explicit target_state = 0 | Release held task/layer through graph completion, barrier or cancellation |

The direct service's mode is an **asset ID**, not the numeric EmotionMethod enum:
SAY_HI has enum value 32 but resolves to asset 48. Do not send 32 intending SAY_HI.
Use the [expression list](../resources/expressions.md), or query supported emotions
on the device. Direct mode is uint8 (0–255); only installed IDs are valid.

Direct fields are target_state (0 OFF / 1 ON), req_id (request identifier),
pre_check (false for playback), mode (asset ID), duration_ms (int32 playback timing),
and optional aorta_header. A pre_check success does not establish that the requested
expression exists or was displayed. Inspect the response status, message and error_code.
A successful response reports playback startup, not playback completion.

For duration_ms, -1 means play the sequence then restore the display default.
Do not equate this with RCP task completion: an RCP expression task can continue holding
its layer until released. Typed EmotionCommand has no play_for_ms; use a finite
phase with DAEMON/BARRIER, or the supported DSL finite-hold option described in
[NodeCommand](../interfaces/rcp-commands.md).
A direct OFF request stops playback and resumes the display carousel; it is **not**
a selective release of one RCP layer.

## Do not mix control owners

Do not directly replace a display or body operation while an RCP graph owns it.
Direct display writes are outside RCP's layer bookkeeping: a later layer update may
replace them, and a direct stop does not cancel the RCP node. Similarly, direct body
control can invalidate a graph's expected state without completing its Goal.

Choose one control path for each behavior. To switch paths, finish or cancel the
current task, inspect its terminal result and actual device state, then start the
new operation. Graph cancellation itself is not a guarantee of a safe physical posture.

For route discovery and transport names see the [interface table](../interfaces/aorta-ros2.md):
the native body service maps to ROS 2 /sm/action/lowlevel; play_emotion retains its name.
RCP /rcp/execute_task is an **action**; the two direct interfaces are **services**.

Schema: [LowlevelAction](../../schemas/aorta/schemas/service/locomotion/lowlevel_action.fbs),
[PlayEmotion](../../schemas/aorta/schemas/service/peripheral/play_emotion.fbs),
[RCP commands](../../schemas/aorta/schemas/service/rcp/function_input.fbs).
