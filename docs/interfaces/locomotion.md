# Locomotion state, reports, and control inputs

<p align="center">English | <a href="locomotion.zh-CN.md">中文</a></p>

For invocation choices and field mappings, see [direct services versus RCP](../guides/control-paths.md).

Use this family to observe posture/action state, track a requested operation to completion,
or integrate a deliberate control input.

For Python and C++ SDK implementations, see the [locomotion Recipe](../../recipes/locomotion/README.md): source, Bazel targets, offline previews and explicit device execution. The interface semantics below remain authoritative.
Complete [device shell setup](../getting-started/device-environment.md)
on the selected `foot_quadruped` EDU device. Exact types and ROS mappings are in the
[interface table](aorta-ros2.md); output topics and command inputs must not be confused.

## Routes and data meaning

| Aorta topic | Direction | Definition and use |
| --- | --- | --- |
| `/locomotion/status` | Subscribe | `posture`, `motion`, `current_action`, `heartbeat_seq`, and `stamp_ns`; observe current posture and freshness |
| `/locomotion/body_action_status` | Subscribe | Body execution `status`, `mode`, `mode_str`, and `modify_source`; a mode snapshot, not task completion |
| `/locomotion/head_status` | Subscribe | Head `state`, `current_action`, `pending_action`, and `fault_reason`; show head activity and faults |
| `/locomotion/body/task_report` | Subscribe | Body terminal task report correlated by `req_id`; inspect `status`, `reason`, and optional typed result |
| `/locomotion/head/task_report` | Subscribe | Head terminal task report with the same correlation pattern; do not match it to an unrelated body request |
| `/locomotion/action_report` | Subscribe | Body/head action outcome: `action_family`, `action_name`, `terminal_status`, `req_id`, `error_code`, and `reason` |
| `/locomotion/event` | Subscribe | Runtime event with `req_id`, `event_name`, action, success, reason, and parameters; context rather than a periodic pose |
| `/locomotion/joy` | Publish | Joystick axes/buttons; bridged from ROS joystick input, can initiate motion |
| `/locomotion/velocity_command` | Publish | Velocity command; bridged from ROS velocity input, can initiate motion |

All rows are pub/sub. Body/head/run-mode/runtime-control services are separate request/reply
interfaces in the [service table](aorta-ros2.md).

## Minimal read-only flow

```bash
timeout 15s aorta schema get /locomotion/status --describe
timeout 15s aorta schema get /locomotion/body/task_report --describe
timeout 15s aorta topic echo /locomotion/status --count 1
```

1. Subscribe to state first and confirm fresh heartbeat/time fields. Distinguish unknown,
   transitional, recovery, and emergency states from an idle robot ready for a task.
2. If the user requests an operation, establish the matching report subscription before
   issuing it, and preserve the request ID used by the documented service contract.
3. Treat the service's start reply as admission, not completion. Match terminal reports to
   that exact request, then inspect success/failure/cancellation and structured result data.
   A transition to idle alone is not proof that the requested action succeeded.
4. In a task report, inspect `result_type` before reading `result`. If a locomotion result
   contains `stage`, distinguish preparation from execution. Use stable status/reason fields
   for decisions; `diagnostic` is descriptive text, not a machine-readable error code.
5. Action reports with an empty request ID cannot safely complete a specific pending request.
   Keep a timeout for each request and report an unknown outcome when no matching terminal
   report arrives; do not blindly resubmit an operation that might still be running.

## Control input behavior

### Standing and lying down

Use `/locomotion/set_run_mode` with `MANUAL=0` and an explicit
`traction_user_param.is_user_param=false` for the core standing operation.
Use `/locomotion/lowlevel_action` with `target_state=1` and
`SAFE_LAYDOWN_SEQUENCE=4` for lying down. These are the motion operations behind
the device harness `pose` actions; direct service calls do not include the
presets' head, light, or sound behavior. Do not substitute `FIXED_STAND` or
`FIXED_LAYDOWN` solely because their names resemble the requested posture.

For MANUAL mode, a successful execution task report means the controller has
started, not that physical standing is complete. Observe subsequent posture
and confirm stability on site. The [recipe](../../recipes/locomotion/README.md)
explains the distinct completion checks and timeout behavior.

### Joystick and velocity

Read [command-topic safeguards](aorta-ros2.md) before publishing. Confirm a single control
owner, the robot mode, a safe supervised area, and a stopping procedure. Inspect the
delivered axis/button contract, permitted velocity components, limits, and QoS before
constructing commands. A generic Joy or Twist message is not a complete controller specification.

The ROS bridge performs ownership, validation, and timeout handling. A direct Aorta
publisher must not assume it inherits those bridge protections. On exit, stop through the
documented control procedure, check subsequent robot state, and release the publisher.
Closing a terminal alone is not a physical-stop guarantee.

## Control-enable service

`/locomotion/control_enable` pauses/resumes the control loop and motor communication for
power transitions. The [Schema](../../schemas/aorta/schemas/service/locomotion/control_enable.fbs)
defines request `aorta.services.locomotion.ControlEnableRequest` and response
`aorta.services.locomotion.ControlEnableResponse`. Both include `aorta_header`.
The request's `enable=true` resumes control; `enable=false` pauses it. ROS 2 uses
`std_srvs/srv/SetBool` on the same name, with request `data` corresponding to Aorta
`enable`. Aorta returns `status` and `message`; ROS returns `success` and `message`,
with `ServiceStatus.SUCCESS=0` representing success.

The [bridge route](../../schemas/ros2/routes.json) sets a 25000 ms service timeout,
one in-flight request, single-writer ownership, 5 requests/s, burst 10, and a 4096-byte
request limit. QoS is reliable, volatile, keep-last, depth 4. No deadman timeout or
zero-on-deadman command is configured. Inspect the type without calling the service:

```bash
timeout 15s ros2 interface show std_srvs/srv/SetBool
```

## Following and navigation-mode service

`/function/following` controls follow/navigation modes. Its
[Schema](../../schemas/aorta/schemas/service/vln/control_following.fbs) defines request
`aorta.services.vln.ControlFollowingRequest` and response
`aorta.services.vln.ControlFollowingResponse`, both with `aorta_header`.
ROS 2 uses [function_msgs/srv/ControlFollowing](../../schemas/ros2/function_msgs/srv/ControlFollowing.srv)
on the same name. A successful reply acknowledges the request, not arrival.

| Request field | Meaning |
| --- | --- |
| `target_state` | 0=OFF, 1=ON; these are the only bridge-allowed values |
| `mode` | Bridge-allowed domain is 0–9; see constants below |
| `req_id` | Request trace ID |
| `pre_check` | If true, only perform the prepare/check phase |
| `x`, `y`, `yaw` | Target position and destination yaw in radians; NAV_TO_POINT only |
| `goal_frame` | Global/world coordinates when set to `global`; default `local` |
| `stop_distance` | Arrival-threshold override; 0.0 selects the configuration default |
| `max_xvel` | NAV_TO_POINT maximum forward-velocity override; values <=0 select the default (the ROS comment specifies 0.5 m/s) |
| `prompt` | Semantic-navigation instruction; the Aorta comment includes SYNC/ASYNC_SEMANTIC_NAV and CIVIC_NAV; the ROS comment names modes 6/7 |
| `source` | Aorta-only ControlSource: UNKNOWN=0, RCP=1, FSM=2, BASE_ACTION=3, ODOM_QR=4 |
| `waypoints` | Aorta-only CIVIC_NAV path hint: `x1,y1,...,x40,y40` in base_link |

The ROS service declares `STOP=0`, `FOLLOWING=1`, `ROAMING=2`, `NAV_TO_POINT=3`,
`COME_TO_ME=4`, `WALK=5`, `SYNC_SEMANTIC_NAV=6`, `ASYNC_SEMANTIC_NAV=7`, and
`ACCOMPANY=8`. Although its mode comment lists 0–8, the route permits 0–9;
the shared [FollowMode Schema](../../schemas/aorta/schemas/shared/follow_common/follow_common.fbs)
defines `CIVIC_NAV=9`, which has no named constant in the ROS service.

Aorta returns `status`, `message`, `error_code`, and `warning`. ROS returns `success`,
`message`, and `error_code`; success maps to `ServiceStatus.SUCCESS=0` and the numeric
error-code domain is preserved. The Aorta-only `warning` describes a concurrent-owner
conflict while the request is still honored. ROS has no request `source` or `waypoints`.

The [bridge route](../../schemas/ros2/routes.json) sets a 5000 ms timeout, one in-flight
request, single-writer ownership, 5 requests/s, burst 10, and a 65536-byte request limit.
QoS is reliable, volatile, keep-last, depth 4. All of `x`, `y`, `yaw`, `stop_distance`,
and `max_xvel` must be finite. No deadman timeout or zero-on-deadman command is configured.
Inspect the type without submitting a command:

```bash
timeout 15s ros2 interface show function_msgs/srv/ControlFollowing
```

## Interpretation and recovery

Body status mode numbers and body-control service mode numbers are different enum domains;
never copy a number from one into the other. Event silence when no task is active is normal.
Missing state updates, an unmatched request, or a fault require investigation, not automatic
mode switching or restarting the motion service. An `armed` bridge is ready to consider a
command; it does not establish successful motion. A bounded read ending with `124` supplies
no sample and must not enable a control action.
