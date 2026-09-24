"""Observe system state or display status; no peripheral control is sent."""
from recipes.common import run, text
from recipes.observe import observe

ROUTES = {
    "system": ("/system/sm_status", "sm.SmStatus"),
    "display": ("/display_node/status", "aorta.topic.peripheral.DisplayStatus"),
}


def summarize(stream, m):
    if stream == "display":
        return dict(data=text(m.Data()))
    return dict(timestamp_ns=m.SensorTimestampNs(), heartbeat_seq=m.HeartbeatSeq(),
                category=m.Category(), status=m.Status(), state_id=m.StateId(),
                state_name=text(m.StateName()), severity=m.Severity(), is_active=m.IsActive(),
                active_state_path=[dict(state_id=m.ActiveStatePath(i).StateId(),
                                       state_name=text(m.ActiveStatePath(i).StateName()))
                                   for i in range(m.ActiveStatePathLength())])


def main(argv=None):
    return observe("system-peripherals", ROUTES, summarize, argv)


if __name__ == "__main__":
    raise SystemExit(run(main))
