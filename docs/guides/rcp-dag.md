# Build an RCP task: presets and custom DAGs

<p align="center">English | <a href="rcp-dag.zh-CN.md">中文</a></p>

For invocation choices and field mappings, see [direct services versus RCP](control-paths.md).

An RCP task is submitted as one `ExecuteTaskGoal` to `/rcp/execute_task`.
First choose whether the device should load an existing graph or use nodes you define.

| You want to… | Set input_type to | Put in input |
| --- | --- | --- |
| Run a supplied behavior | `DagPresetRef` | Preset name and template arguments |
| Compose your own sequence or parallel phases | `DagSpec` | Task settings and a list of nodes |

Read this page in order, then use the [complete NodeCommand field reference](../interfaces/rcp-commands.md).
Resource lists are separate: [body trajectories](../resources/body-trajectories.md),
[head trajectories](../resources/head-trajectories.md),
[expressions](../resources/expressions.md), [lights](../resources/lights.md).

The JSON below illustrates **payload construction**, not a device execution command.
Motion payloads require safe starting conditions and supervised use. They do not add
new runnable paths to the existing [Python/C++ recipe](../../recipes/rcp-task/README.md),
whose CLI still builds a Sleep-only graph.

## 1. The outer Goal

| Field | How to fill it |
| --- | --- |
| `source` | String identifying your application, such as `my-app`; not a login account or permission grant |
| `input_type` | Exactly `DagPresetRef` or `DagSpec`; FlatBuffers union discriminator |
| `input` | Object matching input_type, not a JSON string |
| `user_interaction_context` | Optional originating interaction metadata; omit when unavailable. If propagated, preserve the original identity. Its [schema](../../schemas/aorta/schemas/shared/user_interaction/user_interaction_context.fbs) defines a UUIDv7 string, concrete source event type and nanosecond timestamp |

Do not put service-only `request_id` or `aorta_header` fields into this Goal.
The action client's goal identity and a graph's task_id are different identifiers.

## 2. Run a preset with DagPresetRef

For the wave behavior, the complete Goal is:

```json
{
  "source": "my-app",
  "input_type": "DagPresetRef",
  "input": {
    "relative_path": "actions/WAVE.json",
    "template_args": []
  }
}
```

| Field | Type / default | Filling rule |
| --- | --- | --- |
| `relative_path` | String | Exact name from [RCP presets](rcp-presets.md), case-sensitive, including .json; no absolute path or .. |
| `template_args` | Array / empty | Empty for a fixed preset; supply every required argument for a template |
| `template_args[].name` | Required string | Exact parameter name declared by the template; no unknown or duplicate names |
| `template_args[].value_json` | Required string | JSON-encoded value, not a raw number/object; use a JSON serializer |

The device loads the complete graph. You do not copy a protected file onto your
computer and do not substitute a body trajectory filename for relative_path.

A parameterized rotation payload illustrates value encoding:

```json
{
  "source": "my-app",
  "input_type": "DagPresetRef",
  "input": {
    "relative_path": "atom/rotate_param.json",
    "template_args": [
      {
        "name": "task_id",
        "value_json": "\"turn_001\""
      },
      {
        "name": "angle_rad",
        "value_json": "0.2"
      },
      {
        "name": "tts",
        "value_json": "\"confirm\""
      }
    ]
  }
}
```

Here `"0.2"` decodes to a number in radians, while `"\"confirm\""` decodes to
a string. Use `json.dumps(value)` in Python or the equivalent JSON serializer.

| Template | Required arguments |
| --- | --- |
| `atom/rotate_param.json` | task_id: string; angle_rad: signed radians; tts: sound name, use `confirm` |
| `atom/move_param.json` | task_id: string; base_action_task: `base_action.MOVE_FORWARD`, `base_action.MOVE_BACKWARD`, `base_action.MOVE_LEFT` or `base_action.MOVE_RIGHT`; distance_m: positive metres; tts: `confirm` |

A preset is a **whole Goal**, not a node command. To run two presets in order,
submit the first, wait for a successful terminal result, then submit the second.
Do not insert DagPresetRef into a node or run another graph concurrently to
override a preset's light/expression ownership.

## 3. Define a custom DagSpec

Start with two finite pauses: first runs for 500 ms; second starts after first finishes.

```json
{
  "source": "my-app",
  "input_type": "DagSpec",
  "input": {
    "task_id": "wait_sequence_001",
    "priority": 0,
    "skip_batch_pre_check": false,
    "requires_static": false,
    "required_resources": [],
    "optional_resources": [],
    "nodes": [
      {
        "id": "first",
        "dependencies": [],
        "wait_time_ms": 0,
        "execution_timeout_ms": 2000,
        "lifecycle": "NORMAL",
        "command_type": "SleepCommand",
        "command": {
          "duration_ms": 500
        }
      },
      {
        "id": "second",
        "dependencies": [
          "first"
        ],
        "wait_time_ms": 0,
        "execution_timeout_ms": 2000,
        "lifecycle": "NORMAL",
        "command_type": "SleepCommand",
        "command": {
          "duration_ms": 500
        }
      }
    ]
  }
}
```

### Graph fields

| Field | Default / type | Meaning and filling rule |
| --- | --- | --- |
| `task_id` | Empty string | Supply a non-empty application identifier; use a fresh name for a new intended execution |
| `priority` | 0 / int32 | Scheduling priority. Keep 0 unless your application has an agreed policy; schema has no narrower public business range. It is not authorization |
| `skip_batch_pre_check` | false / bool | Keep false; true disables automatic batch prechecks, not a way to fix rejected motion |
| `requires_static` | false / bool | Requests the robot-static precondition with active setup; this can prepare/change the robot's motion state, not just sample a boolean |
| `required_resources` | Empty enum array | Resources the graph must obtain. Motion typically needs LEGS, head HEAD, expression SCREEN, lights LIGHT, speech AUDIO_OUT |
| `optional_resources` | Empty enum array | Only nonessential resources; unavailable optional resources can cause affected nodes to be skipped |
| `preconditions` | Absent / PreconditionExpr | Optional state constraints; see below |
| `nodes` | Required array | Supply at least one node; IDs must be unique and dependencies must form an acyclic graph |

Resource enum values are `NONE, LEGS, HEAD, SCREEN, LIGHT, AUDIO_OUT, AUDIO_IN,
ARMS, SENSORS, NO_EFFECT`. Enum presence does not imply hardware availability;
do not use NONE/NO_EFFECT as substitutes for real resource ownership.

### Node fields

| Field | Default / type | Meaning and filling rule |
| --- | --- | --- |
| `id` | String | Non-empty unique ID within this graph |
| `dependencies` | Empty string array | Existing node IDs to wait for; empty means an entry node. File order does not impose sequence |
| `wait_time_ms` | 0 / int32 | Use nonnegative milliseconds after dependencies become ready, not an absolute timestamp |
| `execution_timeout_ms` | 0 / int32 | Use a positive finite node budget when needed; 0 adds no positive DAG timeout, but task/service timeouts may still apply |
| `lifecycle` | UNSPECIFIED / enum | Explicitly choose NORMAL, DAEMON or BARRIER as below; unspecified ordinary nodes default to NORMAL, BarrierCommand defaults to BARRIER |
| `condition` | Empty string | Leave empty for ordinary graphs. Current executor specially handles literal `false` as skip; do not write script expressions |
| `command_type` | Union discriminator | One of the 13 types in the [command reference](../interfaces/rcp-commands.md) |
| `command` | Matching object | Only fields for that command type; no nested DagPresetRef or DSL `task/args` at node level |

Use 0…2,147,483,647 for nonnegative int32 millisecond values; the numeric storage
range is not a promise that a long operation is supported.

### Lifecycle: sequence, background work and cleanup

- NORMAL: successors wait for the task to return. Use for finite work.
- DAEMON: starts graph-held work and releases successors without waiting for playback
  completion. This is not an acknowledgment that a light/expression is already visible.
- BARRIER: cancels **all currently held daemons in the graph**, not only its dependencies.
  Use for phase cleanup, not a plain join.
- To join branches without stopping daemons, use a NORMAL finite node such as a
  zero-duration SleepCommand with multiple dependencies.
- Graph completion/cancellation also cleans up held work.

### Optional preconditions

Use only context keys with a documented meaning for your application; arbitrary
names are not variables you can define in the Goal. Omit preconditions if not needed.

| Field | Filling rule |
| --- | --- |
| `kind` | LEAF (default), ALL or ANY |
| `key` | Required context-key string for LEAF |
| `op` | EQ (default), NE, GT, LT, GE, LE, CONTAINS, STARTS_WITH, ENDS_WITH, IN, NOT_IN; match the value/key types |
| `value` | Required ConditionValue for LEAF |
| `timeout_ms` | int32, default 0; positive values are forwarded as a condition timeout |
| `all` | Child expressions for ALL; use a non-empty array |
| `any` | Non-empty child expressions for ANY |

ConditionValue explicitly selects `kind` and its corresponding field:
BOOL → bool_value; INT64 → int64_value; FLOAT64 → float64_value;
STRING → string_value; STRING_LIST → string_list_value.
Defaults are false, 0, 0.0 or absent strings/arrays respectively. Do not use
NONE as an implicit numeric type. INT64 is signed 64-bit; FLOAT64 should be finite.
A conjunction cannot repeat the same context key, even with different operators.
Use requires_static for the dedicated robot-static preparation instead of inventing
an equivalent key expression.

## 4. Associate nodes with resources

For configurable motion parameters and composition, see [motion parameter reference](../interfaces/motion-parameters.md).

| Capability | Node type | Resource selector | Example association |
| --- | --- | --- | --- |
| Body trajectory | BodyCommand | method + action_path | RL_ACTION_POLICY1 + WAVE_50hz.npz |
| Head trajectory | HeadCommand | method + action_path; omit target_angles | STREAM + WAVE.csv |
| Screen expression | EmotionCommand | emotion_id or method alias | emotion_id 48 selects 048_say_hi |
| Ear light | LightCommand | method + color/brightness | FIXED_COLOR with RGB values; no trajectory or expression ID |

Body trajectories require their matching policy and preset parameters. Current
BodyCommand lacks the supplied presets' full action_params: do not reconstruct wave
or another performance using only the two fields above. For custom graphs, use
DslTaskCommand to carry the supported action_params and configure them according
to the motion contract. A complete preset is an alternative when no customization is needed.
Stand/down use the supplied posture presets; FIXED_LAYDOWN is not an equivalent
replacement for coordinated down.

For expression/light composition, this payload illustrates parallel background
nodes, a finite hold and explicit cleanup:

```json
{
  "source": "my-app",
  "input_type": "DagSpec",
  "input": {
    "task_id": "greeting_display_001",
    "required_resources": [
      "SCREEN",
      "LIGHT"
    ],
    "nodes": [
      {
        "id": "face",
        "lifecycle": "DAEMON",
        "command_type": "EmotionCommand",
        "command": {
          "method": "BLINK_ONCE",
          "emotion_id": 48,
          "layer": "INTERACTION"
        }
      },
      {
        "id": "light",
        "lifecycle": "DAEMON",
        "command_type": "LightCommand",
        "command": {
          "method": "FIXED_COLOR",
          "red": 0,
          "green": 0,
          "blue": 128,
          "brightness": 128,
          "layer": "INTERACTION"
        }
      },
      {
        "id": "hold",
        "dependencies": [
          "face",
          "light"
        ],
        "lifecycle": "NORMAL",
        "execution_timeout_ms": 3000,
        "command_type": "SleepCommand",
        "command": {
          "duration_ms": 1500
        }
      },
      {
        "id": "release",
        "dependencies": [
          "hold"
        ],
        "lifecycle": "BARRIER",
        "command_type": "BarrierCommand",
        "command": {}
      }
    ]
  }
}
```

The two entry nodes may start concurrently. hold waits for their scheduling completion,
then waits 1.5 s. release cancels both held nodes. This is not a frame-synchronized
1.5-second playback guarantee. No legs are requested and no body node is present.
The expression ID comes from the resource list, not the numeric EmotionMethod enum.
For expressions/lights, duration_ms and sync do **not** define the RCP hold time;
see the command reference before choosing NORMAL.

## 5. Build the SDK object and handle the result

Use the [Python/C++ recipe](../../recipes/rcp-task/README.md) for client setup,
submission, feedback, result and cancellation. Replace only the goal-construction
part in your application. Its CLI does not accept arbitrary JSON files or preset flags.

| JSON/schema | Python generated object field |
| --- | --- |
| input_type, task_id | inputType, taskId |
| relative_path, template_args, value_json | relativePath, templateArgs, valueJson |
| command_type, action_path, emotion_id | commandType, actionPath, emotionId |
| required_resources, execution_timeout_ms | requiredResources, executionTimeoutMs |

Use generated enum constants for union tags and enums, and corresponding generated
payload objects. C++ uses the generated *Msg types and variant payloads shown in
[goal.h](../../recipes/rcp-task/goal.h). JSON is a readable representation here, not
bytes to pass directly to an SDK action publisher.

An accepted Goal is not a completed behavior. Retain its action identity, inspect
feedback and the terminal status/error category. Client timeout does not stop robot
motion. After rejection, failure or cancellation, check actual state before the next
Goal; do not automatically retry movement or remove resource/precheck constraints.
