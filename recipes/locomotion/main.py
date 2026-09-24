"""Stand via MANUAL mode or lie down via the safe laydown sequence."""

import time
import uuid
from recipes.common import device_node, emit, inbox, parser, rpc, run, text

ROUTE = "/locomotion/lowlevel_action"
REPORT = "/locomotion/action_report"
MODES = {"stand": "MANUAL", "lie-down": "SAFE_LAYDOWN_SEQUENCE", "safe-stop": "SAFE_STOP_SEQUENCE"}
STAND_ROUTE = "/locomotion/set_run_mode"
STAND_REPORT = "/locomotion/body/task_report"


def stand_request_fill(schema, request_id):
    def fill(builder, header):
        from aorta.services.locomotion.RunMode import RunMode
        from aorta.services.locomotion import TractionUserParam as traction_schema
        identifier = builder.CreateString(request_id)
        traction_schema.TractionUserParamStart(builder)
        traction_schema.TractionUserParamAddIsUserParam(builder, False)
        traction = traction_schema.TractionUserParamEnd(builder)
        schema.SetRunModeRequestStart(builder)
        schema.SetRunModeRequestAddAortaHeader(builder, header)
        schema.SetRunModeRequestAddTargetState(builder, 1)
        schema.SetRunModeRequestAddMode(builder, RunMode.MANUAL)
        schema.SetRunModeRequestAddReqId(builder, identifier)
        schema.SetRunModeRequestAddTractionUserParam(builder, traction)
        return schema.SetRunModeRequestEnd(builder)
    return fill


def request_fill(schema, mode, request_id):
    def fill(builder, header):
        identifier = builder.CreateString(request_id)
        schema.LowlevelActionRequestStart(builder)
        schema.LowlevelActionRequestAddAortaHeader(builder, header)
        schema.LowlevelActionRequestAddTargetState(builder, 1)
        schema.LowlevelActionRequestAddMode(builder, mode)
        schema.LowlevelActionRequestAddReqId(builder, identifier)
        return schema.LowlevelActionRequestEnd(builder)
    return fill


def matches_report(message, request_id):
    return text(message.ReqId()) == request_id and message.ActionFamily() == 0


def main(argv=None):
    cli = parser(__doc__)
    cli.add_argument("--mode", choices=MODES, required=True)
    cli.add_argument("--confirm-motion", action="store_true",
                     help="confirm supervision, clear workspace, sole control owner, and a stopping procedure")
    args = cli.parse_args(argv)
    route = STAND_ROUTE if args.mode == "stand" else ROUTE
    report_route = STAND_REPORT if args.mode == "stand" else REPORT
    if args.execute and not args.confirm_motion:
        cli.error("--execute requires --confirm-motion; a clear supervised workspace and stopping procedure are required")
    if not args.execute:
        emit(operation="service", route=route, mode=MODES[args.mode], terminal_report=report_route, execute=False)
        return 0
    with device_node("vbot_lab_locomotion") as (sdk, node):
        import lowlevel_action_schema_meta as schema
        from aorta.services.locomotion.LowlevelActionMode import LowlevelActionMode
        from aorta.services.locomotion.LowlevelActionResponse import LowlevelActionResponse
        from locomotion.ActionReport import ActionReport
        from locomotion.LocomotionStatus import LocomotionStatus
        with inbox(node, sdk, report_route) as report, inbox(node, sdk, "/locomotion/status") as state:
            deadline = time.monotonic() + args.timeout
            first = LocomotionStatus.GetRootAs(state(deadline), 0)
            while True:
                current = LocomotionStatus.GetRootAs(state(deadline), 0)
                if current.HeartbeatSeq() != first.HeartbeatSeq():
                    break
            if current.Motion() != 0 or current.Posture() not in (1, 2):
                raise RuntimeError("robot is not in an idle, known posture; investigate without changing modes")
            request_id = "vbot-lab-" + uuid.uuid4().hex
            emit(request_id=request_id, route=route, mode=MODES[args.mode], submitting=True)
            try:
                if args.mode == "stand":
                    import set_run_mode_schema_meta as schema
                    from aorta.services.locomotion.SetRunModeResponse import SetRunModeResponse
                    response_type = SetRunModeResponse
                    fill = stand_request_fill(schema, request_id)
                else:
                    response_type = LowlevelActionResponse
                    fill = request_fill(schema, getattr(LowlevelActionMode, MODES[args.mode]), request_id)
                response = rpc(node, sdk, route, schema, response_type, fill,
                               max(0.001, deadline - time.monotonic()))
            except (Exception, KeyboardInterrupt):
                emit(request_id=request_id, outcome="unknown",
                     next_step="Inspect robot state and use the stopping procedure; do not repeat the request automatically.")
                raise
            emit(request_id=request_id, status=response.Status(), error_code=response.ErrorCode(),
                 message=text(response.Message()), completion=False)
            if response.Status() != 0 or response.ErrorCode() != 0:
                return 1
            try:
                if args.mode == "stand":
                    from aorta.topic.task.TaskReport import TaskReport
                    from aorta.topic.task.TaskResultPayload import TaskResultPayload
                    from aorta.topic.task.LocomotionTaskResult import LocomotionTaskResult
                    from aorta.topic.task.LocomotionTaskStage import LocomotionTaskStage
                    while True:
                        terminal = TaskReport.GetRootAs(report(deadline), 0)
                        if text(terminal.ReqId()) != request_id:
                            continue
                        if terminal.ResultType() != TaskResultPayload.LocomotionTaskResult:
                            continue
                        table = terminal.Result()
                        context = LocomotionTaskResult()
                        context.Init(table.Bytes, table.Pos)
                        if context.Stage() != LocomotionTaskStage.EXECUTE:
                            continue
                        emit(request_id=request_id, task_status=terminal.Status(),
                             reason=text(terminal.Reason()), diagnostic=text(terminal.Diagnostic()),
                             completion_point="action_started")
                        if terminal.Status() != 0:
                            return 1
                        break
                    # Mode activation is not proof that the robot is standing.
                    # Status has no req_id: report this separately as observation.
                    last_sequence = current.HeartbeatSeq()
                    matching = 0
                    while matching < 3:
                        observed = LocomotionStatus.GetRootAs(state(deadline), 0)
                        if observed.HeartbeatSeq() <= last_sequence:
                            continue
                        last_sequence = observed.HeartbeatSeq()
                        target = (observed.Posture() == 1 and observed.Motion() == 0
                                  and text(observed.CurrentAction()) == "RL_TROT")
                        matching = matching + 1 if target else 0
                    emit(request_id=request_id, target_state_observed=True,
                         observation_only=True, completion=False, action_continues=True,
                         heartbeat_seq=last_sequence)
                    return 0
                while True:
                    message = ActionReport.GetRootAs(report(deadline), 0)
                    if matches_report(message, request_id):
                        emit(request_id=request_id, terminal_status=message.TerminalStatus(),
                             error_code=message.ErrorCode(), reason=text(message.Reason()))
                        return 0 if message.TerminalStatus() == 0 and message.ErrorCode() == 0 else 1
            except (TimeoutError, KeyboardInterrupt):
                emit(request_id=request_id, outcome="unknown",
                     next_step="Use the documented stopping procedure and inspect robot state; do not blindly resubmit.")
                raise


if __name__ == "__main__":
    raise SystemExit(run(main))
