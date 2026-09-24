"""Submit a two-node non-motion Sleep DAG, observe its result, and demonstrate cancellation."""

import time
import uuid
from recipes.common import device_node, emit, parser, positive_seconds, run, text

ROUTE = "/rcp/execute_task"


def request_cancel(handle, goal_id):
    try:
        reply = handle.cancel()
        emit(goal_id=goal_id, cancel_accepted=reply.accepted, status=reply.status.name)
    except Exception as error:
        # Natural completion may race cancellation. Still query the terminal
        # result; a failed cancel alone cannot determine the task's outcome.
        emit(goal_id=goal_id, cancel_error=str(error), next_step="Waiting for terminal status.")


def make_goal(duration_ms, task_id):
    from aorta.action.rcp.ExecuteTaskGoal import ExecuteTaskGoalT
    from aorta.services.rcp.DagInput import DagInput
    from aorta.services.rcp.DagSpec import DagSpecT
    from aorta.services.rcp.DagNode import DagNodeT
    from aorta.services.rcp.NodeCommand import NodeCommand
    from aorta.services.rcp.NodeLifecycle import NodeLifecycle
    from aorta.services.rcp.SleepCommand import SleepCommandT
    nodes = [DagNodeT(id="first", commandType=NodeCommand.SleepCommand,
                      command=SleepCommandT(durationMs=duration_ms), lifecycle=NodeLifecycle.NORMAL),
             DagNodeT(id="second", dependencies=["first"], commandType=NodeCommand.SleepCommand,
                      command=SleepCommandT(durationMs=duration_ms), lifecycle=NodeLifecycle.NORMAL)]
    return ExecuteTaskGoalT(source="vbot-lab", inputType=DagInput.DagSpec,
                            input=DagSpecT(taskId=task_id, nodes=nodes))


def main(argv=None):
    cli = parser(__doc__)
    cli.add_argument("--duration-ms", type=int, default=500, help="each Sleep node, 1..10000 ms")
    cli.add_argument("--cancel-after", type=positive_seconds, help="request cancellation after this many seconds")
    args = cli.parse_args(argv)
    if not 1 <= args.duration_ms <= 10000:
        cli.error("--duration-ms must be 1..10000")
    if args.cancel_after is not None and args.cancel_after >= args.timeout:
        cli.error("--cancel-after must be less than --timeout")
    if not args.execute:
        emit(operation="action", route=ROUTE, nodes=["first: Sleep", "second: Sleep after first"],
             duration_ms=args.duration_ms, cancel_after=args.cancel_after, execute=False)
        return 0
    with device_node("vbot_lab_rcp") as (sdk, node):
        from aorta.action.rcp.ExecuteTaskGoal import ExecuteTaskGoalT
        from aorta.action.rcp.ExecuteTaskResult import ExecuteTaskResultT
        from aorta.action.rcp.ExecuteTaskFeedbackData import ExecuteTaskFeedbackDataT
        codec = sdk.FlatbuffersActionCodec(goal=ExecuteTaskGoalT, result=ExecuteTaskResultT,
                                            feedback=ExecuteTaskFeedbackDataT)
        with node.create_action_client(ROUTE, codec, options=sdk.ActionClientOptions(
                control_timeout_ms=3000, info_timeout_ms=3000)) as client:
            info = client.info()
            if info is None or not info.supports_cancel:
                raise RuntimeError("a cancellable RCP provider is required for this example")
            task_id = "vbot-lab-" + uuid.uuid4().hex
            goal_id = uuid.uuid4().hex
            emit(task_id=task_id, goal_id=goal_id, submitting=True)
            # Log the identity before send; an admission timeout has an unknown
            # outcome and must not trigger a new submission automatically.
            payload = codec.serialize(make_goal(args.duration_ms, task_id))
            try:
                handle = client.send_goal_with_id(goal_id, payload)
            except (Exception, KeyboardInterrupt):
                emit(task_id=task_id, goal_id=goal_id, outcome="unknown",
                     next_step="Inspect RCP state using these identifiers; do not resubmit automatically.")
                raise
            completed = False
            try:
                def feedback(sample):
                    data = ExecuteTaskFeedbackDataT.InitFromPackedBuf(sample.data, 0)
                    emit(goal_id=sample.goal_id, current_node=text(data.currentNode),
                         completed_nodes=data.completedNodes, total_nodes=data.totalNodes,
                         progress_pct=data.progressPct)

                with handle.subscribe_feedback(feedback):
                    start = time.monotonic()
                    cancelled = False
                    while True:
                        elapsed = time.monotonic() - start
                        if args.cancel_after is not None and elapsed >= args.cancel_after and not cancelled:
                            request_cancel(handle, goal_id)
                            cancelled = True
                        remaining = args.timeout - (time.monotonic() - start)
                        if remaining <= 0:
                            raise TimeoutError("RCP result deadline expired")
                        try:
                            result = handle.wait_result(timeout=min(0.2, remaining))
                            break
                        except sdk.TimeoutError:
                            continue
                    completed = True
                    data = ExecuteTaskResultT.InitFromPackedBuf(result.result, 0) if result.result else None
                    emit(goal_id=goal_id, status=result.status.name, message=result.message,
                         duration_ms=data.durationMs if data else None,
                         error_category=data.errorCategory if data else None)
                    if result.status == sdk.ActionStatus.CANCELED:
                        return 0 if cancelled else 1
                    return 0 if result.status == sdk.ActionStatus.SUCCEEDED and data is not None and data.errorCategory == 0 else 1
            finally:
                if not completed:
                    request_cancel(handle, goal_id)
                    try:
                        terminal = handle.wait_result(timeout=3.0)
                        emit(goal_id=goal_id, cleanup_status=terminal.status.name)
                    except Exception as error:
                        emit(goal_id=goal_id, outcome="unknown", cleanup_error=str(error),
                             next_step="Inspect RCP state; do not resubmit automatically.")


if __name__ == "__main__":
    raise SystemExit(run(main))
