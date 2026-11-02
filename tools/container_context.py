"""Recognize a declared development-container context without executing tools."""

import argparse
import json
import os
from pathlib import Path
import platform


RUNTIME_MARKERS = ("/.dockerenv", "/run/.containerenv")


def inspect_context(*, environ=None, is_file=None, system=None):
    environ = os.environ if environ is None else environ
    is_file = (lambda name: Path(name).is_file()) if is_file is None else is_file
    system = platform.system() if system is None else system
    checks = {
        "linux": system == "Linux",
        "container_runtime": any(is_file(name) for name in RUNTIME_MARKERS),
        "development_context": environ.get("VBOT_DEV_CONTAINER") == "1",
    }
    return {
        "format_version": 1,
        "context_status": "eligible" if all(checks.values()) else "attention_required",
        "checks": checks,
        "not_checked": ["image_identity", "workspace_mount", "architecture_and_toolchain", "sdk_readiness"],
        "changes_made": False,
    }


def require_dev_container():
    if inspect_context()["context_status"] != "eligible":
        raise RuntimeError(
            "Run this operation inside the matching development container. "
            "Reuse and inspect the container using docker/README.md; "
            "--profile container, CI=true, or an environment flag alone is not sufficient."
        )


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args(argv)
    result = inspect_context()
    print(json.dumps(result, indent=2))
    return 0 if result["context_status"] == "eligible" else 1


if __name__ == "__main__":
    raise SystemExit(main())
