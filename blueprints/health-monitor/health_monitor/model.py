"""Deterministic business logic, independent of SDK and wall-clock time."""

import math

STREAMS = ("state", "battery", "system")


def finite(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def validate_config(value):
    if not isinstance(value, dict) or set(value) != {"stale_after_seconds", "low_battery_percent"}:
        raise ValueError("expected stale_after_seconds and low_battery_percent")
    age, battery = value["stale_after_seconds"], value["low_battery_percent"]
    if not finite(age) or not 0 < age <= 120 or not finite(battery) or not 0 <= battery <= 100:
        raise ValueError("invalid freshness or battery threshold")
    return value


class Monitor:
    def __init__(self, config):
        self.config = validate_config(config)
        self.streams = {name: {"received_at": None, "stamp_ns": None, "data": None,
                               "invalid": 0, "out_of_order": 0, "samples": 0} for name in STREAMS}

    def update(self, stream, data, stamp_ns, now):
        if stream not in self.streams or not finite(now):
            raise ValueError("unknown stream or invalid local clock")
        state = self.streams[stream]
        valid = isinstance(data, dict) and isinstance(stamp_ns, int) and not isinstance(stamp_ns, bool) and stamp_ns >= 0
        if stream == "battery":
            valid = valid and finite(data.get("soc_percent")) and 0 <= data["soc_percent"] <= 100
        else:
            valid = valid and isinstance(data.get("heartbeat_seq"), int) and not isinstance(data["heartbeat_seq"], bool)
        if not valid:
            state["invalid"] += 1
            return False
        if stamp_ns and state["stamp_ns"] and stamp_ns <= state["stamp_ns"]:
            state["out_of_order"] += 1
            return False
        state.update(received_at=now, stamp_ns=stamp_ns or None, data=dict(data), samples=state["samples"] + 1)
        return True

    def snapshot(self, now):
        if not finite(now):
            raise ValueError("invalid local clock")
        streams = {}
        for name, value in self.streams.items():
            age = None if value["received_at"] is None else max(0, now - value["received_at"])
            status = "waiting_data" if age is None else "stale" if age > self.config["stale_after_seconds"] else "receiving"
            streams[name] = dict(status=status, age_seconds=age, samples=value["samples"],
                                 invalid=value["invalid"], out_of_order=value["out_of_order"], data=value["data"])
        battery = streams["battery"]
        warning = battery["status"] == "receiving" and battery["data"]["soc_percent"] < self.config["low_battery_percent"]
        return {"all_streams_receiving": all(value["status"] == "receiving" for value in streams.values()),
                "low_battery": warning, "streams": streams}
