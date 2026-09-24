"""Receive bounded locomotion-state samples; never publish motion commands."""

import time
from recipes.common import device_node, emit, inbox, parser, run, text

ROUTE = "/locomotion/status"


def main(argv=None):
    args = parser(__doc__, stream=True).parse_args(argv)
    if not args.execute:
        emit(operation="subscribe", topic=ROUTE, count=args.count, timeout=args.timeout, execute=False)
        return 0
    with device_node("vbot_lab_state") as (sdk, node):
        from locomotion.LocomotionStatus import LocomotionStatus
        with inbox(node, sdk, ROUTE) as receive:
            deadline = time.monotonic() + args.timeout
            for _ in range(args.count):
                message = LocomotionStatus.GetRootAs(receive(deadline), 0)
                emit(heartbeat_seq=message.HeartbeatSeq(), posture=message.Posture(),
                     motion=message.Motion(), current_action=text(message.CurrentAction()),
                     stamp_ns=message.StampNs())
    return 0


if __name__ == "__main__":
    raise SystemExit(run(main))
