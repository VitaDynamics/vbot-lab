"""Run checked-in repository, container-only Recipe or packaging check groups."""

import argparse
import json
from pathlib import Path, PurePosixPath
import subprocess
import sys

from container_context import require_dev_container


ROOT = Path(__file__).resolve().parents[1]
LOCATIONS = {"repository": "host_or_ci", "recipes": "development_container", "packaging": "development_container"}


def load_groups(root=ROOT):
    data = json.loads((root / "catalog/checks.json").read_text())
    if (not isinstance(data, dict) or data.get("format_version") != 1
            or not isinstance(data.get("groups"), dict) or set(data["groups"]) != set(LOCATIONS)):
        raise ValueError("invalid check-group format")
    seen = set()
    for name, location in LOCATIONS.items():
        group = data["groups"][name]
        if (not isinstance(group, dict) or group.get("execution_location") != location
                or not isinstance(group.get("checks"), list) or not group["checks"]):
            raise ValueError(f"invalid check group: {name}")
        for entry in group["checks"]:
            if not isinstance(entry, str):
                raise ValueError("check path must be a string")
            path = PurePosixPath(entry)
            if len(path.parts) != 2 or path.parts[0] != "tests" or path.suffix != ".py" or "\\" in entry:
                raise ValueError(f"invalid check path: {entry}")
            target = root / entry
            if entry in seen or not target.is_file() or not target.resolve().is_relative_to(root.resolve()):
                raise ValueError(f"missing, duplicate or escaped check: {entry}")
            seen.add(entry)
    return data["groups"]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scope", choices=tuple(LOCATIONS), required=True)
    parser.add_argument("--list", action="store_true", help="print the group without executing any checks")
    args = parser.parse_args(argv)
    try:
        group = load_groups(ROOT)[args.scope]
        if args.list:
            print(json.dumps(group, indent=2))
            return 0
        if group["execution_location"] == "development_container":
            require_dev_container()
        results = []
        for check in group["checks"]:
            result = subprocess.run([sys.executable, str(ROOT / check)], cwd=ROOT, check=False, timeout=120)
            results.append({"check": check, "exit_code": result.returncode})
        print(json.dumps({"scope": args.scope, "results": results}))
        return 0 if all(item["exit_code"] == 0 for item in results) else 1
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as error:
        print(str(error), file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
