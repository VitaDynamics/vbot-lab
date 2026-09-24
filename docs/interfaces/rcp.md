# RCP tasks and tracing

<p align="center">English | <a href="rcp.zh-CN.md">中文</a></p>

This family contains the task action and its read-only trace output. Complete
[device shell setup](../getting-started/device-environment.md) on `foot_quadruped` EDU.
Task execution can change device state; observing traces or inspecting the provider does
not submit a task. See the [interface table](aorta-ros2.md) for the mapping overview.

Start with [DAG authoring and composition](../guides/rcp-dag.md) and the
[RCP presets](../guides/rcp-presets.md) for node fields, preset parameters,
dependencies and light/expression lifecycles. Use the [NodeCommand reference](rcp-commands.md)
for every command field and the separate [device resources](../resources/README.md) for identifiers.
The [Python/C++ recipe](../../recipes/rcp-task/README.md)
provides the non-motion submission, feedback and cancellation workflow.

## Task definition and use

`/rcp/execute_task` is an **action**, not a topic or service. It accepts a DAG or preset,
reports progress, produces a terminal result, and supports cancellation.

| Aorta action | Goal / result / feedback data roots | ROS 2 action | ROS 2 action type |
| --- | --- | --- | --- |
| `/rcp/execute_task` | `aorta.action.rcp.ExecuteTaskGoal` / `aorta.action.rcp.ExecuteTaskResult` / `aorta.action.rcp.ExecuteTaskFeedbackData` | `/rcp/execute_task` | `aorta_msgs/action/ExecuteTask` |

Inspect the provider and delivered type without submitting a goal:

```bash
timeout 15s aorta action list
timeout 15s aorta action info /rcp/execute_task
timeout 15s ros2 action list -t
timeout 15s ros2 interface show aorta_msgs/action/ExecuteTask
```

The goal carries `source`, a tagged `input`, and optional `user_interaction_context`.
For native Aorta JSON, select the matching `input_type` and `input`. In ROS, the delivered
type provides `INPUT_TYPE_DAG_SPEC` with `input_dag_spec`, or `INPUT_TYPE_DAG_PRESET_REF`
with `input_dag_preset_ref`. These representations are not interchangeable payloads.

For a requested task, first inspect every DAG node and precondition: a DAG can trigger
motion, speech, lights, or other device changes. Submit deliberately and keep the returned
goal identity. Admission is not completion; observe feedback and then the terminal action
state and result. Feedback contains `current_node`, `completed_nodes`, `total_nodes`, and
`progress_pct`; results include `duration_ms` and `error_category`.

The ROS bridge allows one goal in flight; another is rejected with `GOAL_BUSY`. The native
provider advertises its own concurrency and result-retention settings through action info;
do not apply those numbers to the ROS bridge. Cancellation is a request: wait for the
terminal canceled state, or handle refusal / a goal that already finished. A client timeout
or closed terminal is not task cancellation. Fetch the result within the provider's retention
period and use `/rcp/trace` for task-event context, not as a replacement for the terminal result.

## Trace topic definition and use

`/rcp/trace` is a read-only pub/sub output with Aorta type `aorta.topic.rcp.TraceEvent`,
mapped to the same ROS topic name with type `function_msgs/msg/TraceEvent`.

- Correlate requests with `request_id`; organize nested work with `trace_id`, `parent_id`,
  `task_level`, and `subtask_name`. Do not join two tasks just because events arrived together.
- Interpret `event_type` using the delivered enum. `timestamp` is an ISO 8601 event-time
  string; parse it before comparing times instead of using local receipt order as causality.
- `payload_json` is event-specific JSON, not a single fixed payload shape. Dispatch by
  event type, then check field presence. Unknown events may be retained for display but
  must not default to success.
- Subscribe before a deliberately requested task, update only that request's progress view,
  and finish it from the action terminal state/result. Trace silence between tasks is normal.

Read-only example:

```bash
timeout 15s aorta schema get /rcp/trace --describe
timeout 15s aorta topic echo /rcp/trace --count 1
```

Reading does not create a task; exit `124` is not an executor failure. To stop a task,
request cancellation explicitly and check its terminal state, then clean up subscriptions
and local goal state. Closing the trace subscription does not stop the task. If retention
expiry or disconnection makes the result unavailable, report an unknown outcome instead
of automatically re-executing the entire DAG.
