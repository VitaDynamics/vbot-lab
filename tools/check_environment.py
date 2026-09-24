"""Inventory local VBOT development requirements without running external commands."""

import argparse
import json
from pathlib import Path
import platform
import shutil
import sys

from vbot_catalog import CatalogError, DEFAULT_ROOT, load_catalog, require, select_robot


REQUIRED_TOOLS = {
    "host": ("bash", "git", "docker"),
    "container": ("bash", "git", "bazel"),
}


def inspect_environment(root, profile, robot_type=None, *, which=shutil.which, python_version=None):
    require(profile in REQUIRED_TOOLS, "Unknown environment profile")
    catalog, robots = load_catalog(root)
    robot = select_robot(robots, robot_type)
    python_version = sys.version_info[:3] if python_version is None else python_version
    checks = [{
        "name": "python", "status": "present" if tuple(python_version) >= (3, 10) else "incompatible",
        "version": ".".join(map(str, python_version)), "minimum_version": "3.10",
    }]
    for name in REQUIRED_TOOLS[profile]:
        checks.append({"name": name, "status": "present" if which(name) else "missing", "version": "not_checked"})
    blocked_robot = robot is not None and robot["release_scope"] != "current_target"
    missing_tools = any(check["status"] != "present" for check in checks)
    try:
        bazel_baseline = (Path(root) / ".bazelversion").read_text(encoding="utf-8").strip()
    except OSError as error:
        raise CatalogError("Missing Bazel baseline") from error
    require(bool(bazel_baseline), "Empty Bazel baseline")
    return {
        "format_version": 1,
        "profile": profile,
        "system": platform.system(),
        "architecture": platform.machine(),
        "inventory_status": "attention_required" if missing_tools or blocked_robot else "complete",
        "tools": checks,
        "expected_bazel_version": bazel_baseline,
        "robot": robot,
        "robot_status": "not_selected" if robot is None else "blocked_release" if blocked_robot else "current_target_unverified",
        "sdk": catalog["sdk"],
        "sdk_status": "blocked_integration" if catalog["sdk"]["integration"] == "pending" else "not_verified",
        "not_checked": [
            "external_tool_versions", "docker_daemon", "development_image_pull", "sdk_import_and_abi",
            "device_connection", "device_firmware", "harness_skill_discovery",
        ],
        "device_contacted": False,
        "changes_made": False,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--profile", choices=tuple(REQUIRED_TOOLS), required=True)
    parser.add_argument("--robot-type")
    args = parser.parse_args(argv)
    try:
        result = inspect_environment(args.root, args.profile, args.robot_type)
    except CatalogError as error:
        print(json.dumps({"error": str(error), "device_contacted": False, "changes_made": False}))
        return 2
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["inventory_status"] == "complete" else 1


if __name__ == "__main__":
    sys.exit(main())
