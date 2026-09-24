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

## Interpretation and recovery

Body status mode numbers and body-control service mode numbers are different enum domains;
never copy a number from one into the other. Event silence when no task is active is normal.
Missing state updates, an unmatched request, or a fault require investigation, not automatic
mode switching or restarting the motion service. An `armed` bridge is ready to consider a
command; it does not establish successful motion. A bounded read ending with `124` supplies
no sample and must not enable a control action.
