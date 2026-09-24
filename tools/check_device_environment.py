"""Inspect the current vbot shell without running tools or contacting interfaces."""

import argparse
import json
import os
from pathlib import Path
import shutil
import sys


EXPECTED_ENV = {
    "ZENOH_SESSION_CONFIG_URI": "/opt/vita/aorta/edu/edu_session.json5",
    "RMW_IMPLEMENTATION": "rmw_fastrtps_cpp",
    "ROS_DOMAIN_ID": "178",
    "ROS_LOCALHOST_ONLY": "1",
}
AORTA_BIN = "/opt/vita/aorta/bin"
PUBLIC_FILES = (
    EXPECTED_ENV["ZENOH_SESSION_CONFIG_URI"],
    "/opt/vita/ros/humble/setup.bash",
    "/opt/vita/aorta/ros/local_setup.bash",
)


def effective_username():
    try:
        import pwd
        return pwd.getpwuid(os.geteuid()).pw_name
    except (ImportError, KeyError, OSError):
        return None


def readable_file(path):
    return Path(path).is_file() and os.access(path, os.R_OK)


def inspect_device_environment(*, environ=None, username=None, readable=readable_file,
                               which=shutil.which):
    environ = os.environ if environ is None else environ
    username = effective_username() if username is None else username
    checks = [{"name": "account", "status": "ok" if username == "vbot" else "mismatch",
               "expected": "vbot"}]
    for name, expected in EXPECTED_ENV.items():
        actual = environ.get(name)
        checks.append({"name": name, "expected": expected,
                       "status": "ok" if actual == expected else "missing" if actual is None else "mismatch"})
    path = environ.get("PATH", "")
    checks.append({"name": "aorta_path", "expected": AORTA_BIN,
                   "status": "ok" if AORTA_BIN in path.split(os.pathsep) else "missing"})
    for filename in PUBLIC_FILES:
        checks.append({"name": filename, "status": "ok" if readable(filename) else "missing_or_unreadable"})
    for command in ("aorta", "ros2", "timeout"):
        executable = which(command, path=path)
        status = "ok" if executable else "missing"
        if command == "aorta" and executable and os.path.normpath(executable) != AORTA_BIN + "/aorta":
            status = "unexpected_location"
        checks.append({"name": command, "status": status})
    return {
        "format_version": 1,
        "scope": "current_device_shell",
        "inventory_status": "complete" if all(check["status"] == "ok" for check in checks) else "attention_required",
        "checks": checks,
        "not_checked": ["device_identity_and_firmware", "bash_startup_persistence", "shell_aliases_and_functions",
                        "tool_execution_and_versions", "ros_overlay_type_loading", "aorta_session_connection",
                        "interface_discovery", "sample_reception", "sdk_and_application_readiness"],
        "interfaces_contacted": False,
        "changes_made": False,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args(argv)
    result = inspect_device_environment()
    print(json.dumps(result, indent=2))
    return 0 if result["inventory_status"] == "complete" else 1


if __name__ == "__main__":
    sys.exit(main())
