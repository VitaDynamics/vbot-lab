# Motion parameters and reusable composition

<p align="center">English | <a href="motion-parameters.zh-CN.md">中文</a></p>

Configure an interface according to the intended operation; you do not need a separate
tutorial or copied preset for every action. This reference complements
[NodeCommand fields](rcp-commands.md), [resource names](../resources/README.md), and
[direct services versus RCP](../guides/control-paths.md). It describes request construction,
not a new runnable motion example.

## Choose an operation before choosing parameters

| Intent | Interface | Parameters to configure |
| --- | --- | --- |
| Bounded turn in place | BaseActionCommand.ROTATE or NavigateCommand.ROTATE_IN_PLACE | angle_rad, finite signed radians; follow the selected provider's direction contract |
| Bounded translation | BaseActionCommand.MOVE_FORWARD / MOVE_BACKWARD / MOVE_LEFT / MOVE_RIGHT | distance_m, positive metres; method selects direction |
| Supplied jump, dance or body performance | BodyCommand, or DslTaskCommand when overrides are needed | Matching policy method and action_path from the body resource list; applicable action_params |
| Head pose or head trajectory | HeadCommand | target_angles [pitch, yaw] in radians, or a head CSV action_path; do not fill both |
| Expression, speech and lights | EmotionCommand, SpeakCommand, LightCommand | Expression ID, human text, light mode/color; see their field reference |

A jump trajectory does not imply a configurable jump height, speed or repetition count.
Do not invent height/speed/loop fields, or change a policy number to select intensity.
A mathematical full turn is 2π radians, but encoding that number does not establish
the provider's accepted range or the available safe space. Resource/mode availability
and starting-posture requirements remain specific to the device.

## Where action_params belongs

| Entry | Representation |
| --- | --- |
| RCP typed BodyCommand | No action_params field |
| RCP DslTaskCommand | task = body.RL_ACTION_POLICY1, body.RL_ACTION_POLICY2, body.RL_ACTION_POLICY3 or body.RL_ACTION_POLICY4; args_json encodes the args object |
| Body task args object | action_path: device resource string; pre_check: bool; action_params: object; completion_timeout_ms: optional body completion budget |
| Direct /locomotion/lowlevel_action | action_params_json encodes only the action_params object; mode and action_path are separate request fields |

In RCP, construct the args object as
`{"action_path": selected_resource, "action_params": selected_parameters}`
and JSON-serialize that whole object once into args_json. The parameter map remains
an object inside args, not another encoded string. These are application variables,
not literal resource names. Python generated fields use argsJson/actionPath;
use generated payload objects and union tags as explained in the DAG guide.

The current RCP body task forwards action_params for RL_ACTION_POLICY1–4 only.
Do not assume STREAM, RL_TROT or the posture methods consume these overrides.
pre_check is a preparation/check phase, not a universal read-only dry run.
completion_timeout_ms > 0 overrides the body's completion wait; omitted/nonpositive
uses the task default. It does not replace the DAG node execution_timeout_ms.

Each action_params value must be a scalar boolean, number or string. Arrays, nested
objects and null are not forwarded by the low-level scalar parameter merger.
Use actual booleans, finite numbers and exact strings, not numbers encoded as strings.
Unknown keys are not a capability-discovery mechanism: forwarding a key does not prove
the selected action consumes it.

Request values override the action's configured values. Omission means inheritance,
not “use the last preset's value” or a universal safe default. Path-embedded parameter
syntax is not needed for this workflow. Keep action_path as a resource name.

## Transition parameters

These keys apply to the stepping-transition path when selected by the body action.
An override cannot add an unsupported transition to a controller.
Defaults below distinguish request omission from implementation fallback; they are
not a recommended motion profile.

| Parameter | Type | Default / omission | Meaning and constraints |
| --- | --- | --- | --- |
| `transition_stepping_enabled` | bool | false fallback; device action configuration may override | Enable the stepping transition strategy; not a request to sit or a generic posture converter. |
| `transition_validation_mode` | string | Device configuration; absent request means no override | required or skip. required requests transition post-checks; skip disables them. Do not use skip to bypass a rejection. |
| `transition_validation_require_ramp` | bool | true in the post-check specification | Whether ramp estimation/checking is required when post-checks are enabled. |
| `transition_validation_require_payload` | bool | true in the post-check specification | Whether payload estimation/checking is required when post-checks are enabled. |
| `transition_validation_ramp_angle_deg` | number | Device transition configuration | Ramp threshold in degrees. Use a finite physically justified threshold; no universal user-safe maximum is defined. |
| `transition_validation_payload_min_kg` | number | Device transition configuration | Lower bound on estimated payload, kg; signed estimates are possible. This is not the robot rated load. |
| `transition_validation_payload_max_kg` | number | Device transition configuration | Upper bound on estimated payload, kg; must be >= min when both are supplied. Do not widen bounds to force execution. |
| `transition_validation_estimator_timeout_s` | number | Device transition configuration | Estimator wait budget in seconds; use a finite positive value, distinct from node execution_timeout_ms. |

An explicit validation override without mode can enable post-checks; explicitly selecting
skip disables them. Numeric thresholds omitted from a request are resolved against
device transition configuration. Do not copy values from another action or weaken checks
to make a rejected request run.

## Action obstacle-check parameters

These are directional obstacle-check boxes, not automatic path planning or a computed
trajectory swept volume. Their dimensions must describe the actual action's clearance needs.

| Key | Type | Constraint / omission |
| --- | --- | --- |
| `obstacle_avoidance_enabled` | bool | Missing does not explicitly request these action-level checks; false skips them |
| `obstacle_avoidance_<direction>_enabled` | bool | Required for each of front, rear, left, right, top when the master switch is true |
| `obstacle_avoidance_<direction>_length_m` | number | Box X dimension in base_link, metres |
| `obstacle_avoidance_<direction>_width_m` | number | Box Y dimension in base_link, metres |
| `obstacle_avoidance_<direction>_height_m` | number | Box Z dimension, metres, from the configured action-check Z origin |

When enabled, provide all five groups (21 scalar keys including the master switch);
at least one direction must be enabled. Dimensions for enabled directions must be
finite and positive. Disabled directions still require their dimension fields and may
use zero. Do not use a nested directions object. The configured Z origin is not
necessarily ground level; no single set of dimensions fits every motion.
RCP's action-obstacle feature switch can disable the effective check even if the request
sets true. A request field alone is not proof that an obstacle check actually ran.

## Reusable orchestration pattern

1. Choose the operation and verify its supported initial state; use a separate preparation
   task only where the transition contract requires it. A name such as “sit” is not a state check.
2. Build a DagSpec with required resources for indispensable outputs (including AUDIO_OUT
   when speech must occur). Keep skip_batch_pre_check false; preserve needed preconditions.
3. Start expression/light DAEMON nodes; run finite motion and speech as NORMAL nodes with
   the appropriate shared dependencies. Do not make speech depend on motion completion
   when it should accompany motion.
4. Make cleanup BARRIER depend on both finite motion and speech. It releases all held
   daemons in the graph; it is not a selective stop. Observe the Goal terminal result.
5. Keep triggering, debounce, cooldown and departure detection in the application.
   On failure/timeout, resolve the active Goal and actual robot state before allowing another trigger.

This is a composition pattern, not a promise of frame-synchronized outputs. Speech may
outlast motion; if it must fit entirely inside the motion interval, establish timing from
the selected operation and output events, not just parallel dependencies.
Neither graph completion nor a controller-start report proves a specific physical posture.

Users choose supported values within the motion/resource contract. If a resource's starting
posture, policy compatibility or required parameters are undocumented, the missing contract
must be supplied before constructing that motion; do not obtain it by trial-and-error
parameter guessing. Ready-made presets remain optional conveniences, not the only
way to express a custom graph.
