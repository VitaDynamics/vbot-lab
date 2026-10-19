"""Observe three telemetry streams; never publish control messages."""

import argparse
import json
import os
from pathlib import Path
import platform
import struct
import sys
import time

from health_monitor.errors import ApplicationError
from health_monitor.model import Monitor, validate_config
from health_monitor.runtime import ROUTES, decode, subscription

DEFAULT_CONFIG = Path(__file__).resolve().parents[1] / "config.json"


def development_context():
    if (platform.system() != "Linux" or os.environ.get("VBOT_DEV_CONTAINER") != "1"
            or not any(Path(name).is_file() for name in ("/.dockerenv", "/run/.containerenv"))):
        raise ApplicationError("environment", "development_container_required",
                               "Run previews and simulation in the development container.")


def load_config(path):
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise ApplicationError("config", "config_not_found",
                               "Select an existing configuration file with --config.") from None
    except (PermissionError, IsADirectoryError):
        raise ApplicationError("config", "config_not_readable",
                               "Select a readable regular configuration file with --config.") from None
    except UnicodeError:
        raise ApplicationError("config", "invalid_config",
                               "Use UTF-8 JSON with stale_after_seconds in (0, 120] and low_battery_percent in [0, 100].") from None
    except OSError:
        raise ApplicationError("config", "config_read_failed",
                               "Check configuration file access and storage, then retry.") from None
    try:
        return validate_config(json.loads(text))
    except (ValueError, TypeError):
        raise ApplicationError("config", "invalid_config",
                               "Use a JSON object with stale_after_seconds in (0, 120] and low_battery_percent in [0, 100].") from None


def duration(value):
    value = float(value)
    if not 0 < value <= 120:
        raise argparse.ArgumentTypeError("duration must be finite and in (0, 120]")
    return value


def main(argv=None):
    cli = argparse.ArgumentParser(description=__doc__)
    modes = cli.add_mutually_exclusive_group()
    modes.add_argument("--execute", action="store_true")
    modes.add_argument("--simulate", action="store_true")
    cli.add_argument("--duration", type=duration, default=10.0)
    cli.add_argument("--config", type=Path)
    args = cli.parse_args(argv)
    config = load_config(args.config or DEFAULT_CONFIG)
    monitor = Monitor(config)
    if not args.execute:
        development_context()
        if not args.simulate:
            print(json.dumps({"execute": False, "routes": {name: value[0] for name, value in ROUTES.items()},
                              "duration_seconds": args.duration, "config": config}))
            return 0
        for stream, data in (("state", {"heartbeat_seq": 1}), ("battery", {"soc_percent": 80}),
                             ("system", {"heartbeat_seq": 1})):
            monitor.update(stream, data, 1, 0)
        for now in (0, config["stale_after_seconds"] + 1):
            print(json.dumps({"source": "synthetic", **monitor.snapshot(now)}))
        return 0
    with subscription(ROUTES) as receive:
        start = time.monotonic()
        next_report = start
        while time.monotonic() - start < args.duration:
            item = receive(min(0.1, max(0, args.duration - (time.monotonic() - start))))
            now = time.monotonic()
            if item is not None:
                stream, payload, received_at = item
                try:
                    data, stamp_ns = decode(stream, payload)
                    monitor.update(stream, data, stamp_ns, received_at)
                except (ValueError, IndexError, struct.error, TypeError):
                    monitor.update(stream, None, 0, received_at)
            if now >= next_report:
                print(json.dumps({"source": "device", **monitor.snapshot(now)}), flush=True)
                next_report = now + 1
        result = monitor.snapshot(time.monotonic())
        print(json.dumps({"source": "device", "final": True, **result}), flush=True)
        return 0 if result["all_streams_receiving"] else 1


def entrypoint():
    try:
        return main()
    except KeyboardInterrupt:
        return 130
    except ApplicationError as error:
        print(json.dumps(error.summary()), file=sys.stderr)
        return 1
    except Exception:
        print(json.dumps({"status": "error", "stage": "runtime", "error_code": "unexpected_error",
                          "next_step": "Check the last completed stage and application changes; review logs before sharing."}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(entrypoint())
