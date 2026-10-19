"""Layered diagnostics; sdk/sample use Python SDK. Device checks require opt-in."""

import argparse
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import queue
import shutil
import subprocess
import sys

SESSION = "/opt/vita/aorta/edu/edu_session.json5"
ROUTES = {"state": "/locomotion/status", "battery": "/bms_state", "system": "/system/sm_status"}


def device_checks():
    if platform.system() != "Linux":
        return [{"check": "device_shell", "status": "mismatch"}]
    import pwd
    return [{"check": "vbot_account", "status": "confirmed" if pwd.getpwuid(os.geteuid()).pw_name == "vbot" else "mismatch"},
            {"check": "session_file", "status": "confirmed" if Path(SESSION).is_file() and os.access(SESSION, os.R_OK) else "missing_or_unreadable"},
            {"check": "session_environment", "status": "confirmed" if os.environ.get("ZENOH_SESSION_CONFIG_URI") == SESSION else "mismatch"}]


def diagnose(level, *, allow_device=False, route="state", timeout=5):
    if route not in ROUTES or not 0 < timeout <= 30:
        raise ValueError("invalid fixed stream or timeout")
    report = {"format_version": 1, "level": level, "checks": [], "interfaces_contacted": False,
              "changes_made": False, "device_version": "not_verified"}
    if level == "sample":
        report["sampling"] = {"attempted": False, "session_opened": False,
                              "subscription_created": False, "sample_received": False}
    if level in ("device", "sample"):
        if not allow_device:
            raise ValueError("device checks require --allow-device-check in the selected device's vbot shell")
        report["checks"] = device_checks()
        if any(item["status"] != "confirmed" for item in report["checks"]) or level == "device":
            return report
        progress = report["sampling"]
        progress["attempted"] = True
        stage = "sdk_import"
        try:
            import aorta
            inbox = queue.Queue(maxsize=1)
            def receive(payload, _context):
                try:
                    inbox.put_nowait(len(payload))
                except queue.Full:
                    pass
            stage = "session_open"
            with aorta.Node("vbot_readonly_diagnostic") as node:
                progress["session_opened"] = True
                stage = "subscribe"
                with node.create_subscriber(ROUTES[route], receive, options=aorta.SubscriberOptions(receive_depth=1)):
                    progress["subscription_created"] = True
                    report["interfaces_contacted"] = True
                    stage = "sample"
                    try:
                        size = inbox.get(timeout=timeout)
                        progress["sample_received"] = True
                        report["checks"].append({"check": "selected_stream", "route": ROUTES[route],
                                                  "status": "sample_received", "payload_bytes": size,
                                                  "decoded": False})
                    except queue.Empty:
                        report["checks"].append({"check": "selected_stream", "route": ROUTES[route],
                                                  "status": "waiting_data_timeout", "support": "not_verified"})
                    stage = "cleanup"
        except ImportError:
            report["checks"].append({"check": stage, "status": "failed", "cause": "import_failed"})
        except Exception:
            report["checks"].append({"check": stage, "status": "failed", "cause": "not_verified"})
        return report
    if level == "inventory":
        report["checks"] = [{"check": name, "status": "confirmed" if shutil.which(name) else "confirmed_missing"}
                            for name in ("python3", "bash", "git")]
        report["python_version"] = platform.python_version()
        report["sdk_runtime"] = "not_verified"
        return report
    from container_context import require_dev_container
    from sdk_assets import configuration
    from sdk_ci import PYTHON_RUNTIME_PROBE
    require_dev_container()
    config = configuration()
    versions = config["sdk"]["python"]["wheels"]
    for name, expected in versions.items():
        try:
            actual = importlib.metadata.version(name.replace("_", "-"))
            report["checks"].append({"check": name, "status": "confirmed" if actual == expected else "mismatch",
                                      "expected": expected, "actual": actual})
        except importlib.metadata.PackageNotFoundError:
            report["checks"].append({"check": name, "status": "confirmed_missing"})
    if all(item["status"] == "confirmed" for item in report["checks"]):
        environment = dict(os.environ, PYTHONNOUSERSITE="1", PYTHONPATH="")
        environment.pop("AORTA_CORE_FFI_LIB", None)
        result = subprocess.run([sys.executable, "-c", PYTHON_RUNTIME_PROBE, str(config["sdk"]["cpp"]["abi"])],
                                capture_output=True, timeout=20, env=environment, check=False)
        report["checks"].append({"check": "native_runtime_abi", "status": "confirmed" if result.returncode == 0 else "failed"})
    return report


def isolated_sample(route, timeout):
    # Native SDK logging writes OS file descriptors, so redirect_stdout is insufficient.
    # A bounded worker keeps its raw SDK output out of the shareable report.
    program = ("import json,runpy,sys; module=runpy.run_path(sys.argv[1]); "
               "print(json.dumps(module['diagnose']('sample', allow_device=True, "
               "route=sys.argv[2], timeout=float(sys.argv[3]))))")
    result = subprocess.run([sys.executable, "-c", program, str(Path(__file__).resolve()), route, str(timeout)],
                            capture_output=True, text=True, timeout=timeout + 20, check=False)
    if result.returncode != 0:
        raise RuntimeError("sampling worker did not complete")
    for line in reversed(result.stdout.splitlines()):
        try:
            report = json.loads(line)
        except ValueError:
            continue
        if isinstance(report, dict) and report.get("format_version") == 1 and report.get("level") == "sample":
            return report
    raise RuntimeError("sampling worker returned no report")


def main(argv=None):
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--level", choices=("inventory", "sdk", "device", "sample"), default="inventory",
                     help="sdk/sample require Python SDK; for C++ see docs/development/diagnostics.md#cpp")
    cli.add_argument("--allow-device-check", action="store_true")
    cli.add_argument("--route", choices=ROUTES)
    cli.add_argument("--timeout", type=float, default=5)
    args = cli.parse_args(argv)
    if not 0 < args.timeout <= 30:
        cli.error("timeout must be finite and in (0, 30]")
    if (args.route is not None and args.level != "sample") or (args.allow_device_check and args.level not in ("device", "sample")):
        cli.error("device opt-in and route selection apply only to their explicit diagnostic levels")
    try:
        if args.level == "sample":
            if not args.allow_device_check:
                raise ValueError("sampling requires explicit opt-in")
            report = isolated_sample(args.route or "state", args.timeout)
        else:
            report = diagnose(args.level, allow_device=args.allow_device_check, route=args.route or "state", timeout=args.timeout)
        print(json.dumps(report, sort_keys=True))
        return 0 if all(item["status"] in ("confirmed", "sample_received") for item in report["checks"]) else 1
    except KeyboardInterrupt:
        return 130
    except (OSError, ValueError, RuntimeError, ImportError, subprocess.TimeoutExpired):
        print(json.dumps({"status": "blocked", "next_step": "check the execution location, explicit opt-in and required inputs"}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
