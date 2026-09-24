"""Validate and query VBOT Lab's local capability index. Never contact a device."""

import argparse
import json
from pathlib import Path, PurePosixPath
import re
import sys


DEFAULT_ROOT = Path(__file__).resolve().parents[1]


class CatalogError(ValueError):
    """Invalid catalog or unsupported query input."""


def require(condition, message):
    if not condition:
        raise CatalogError(message)


def read_object(path):
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise CatalogError(f"Cannot read catalog file: {path.name}") from error
    require(isinstance(data, dict), f"Expected an object: {path.name}")
    return data


def check_reference(root, value, *, optional=False):
    if optional and value is None:
        return
    require(isinstance(value, str) and bool(value), "Reference must be a nonempty path")
    path = PurePosixPath(value)
    require(not path.is_absolute() and ".." not in path.parts and "\\" not in value,
            f"Reference must be checkout-relative: {value}")
    require((root / value).is_file(), f"Missing reference: {value}")


def validate_catalog(root, catalog, robots):
    require(catalog.get("format_version") == 1, "Unsupported catalog format")
    require(catalog.get("workspace") == "vbot-lab", "Not a VBOT Lab catalog")
    sdk = catalog.get("sdk")
    require(isinstance(sdk, dict), "Missing SDK metadata")
    require(sdk.get("integration") in ("pending", "integrated"), "Invalid SDK integration state")
    require(sdk.get("name") == "Aorta Python SDK", "Unknown SDK")
    for field in ("version", "python_import"):
        require(sdk.get(field) is None or isinstance(sdk.get(field), str), f"Invalid SDK {field}")
    check_reference(root, sdk.get("reference"))
    cpp = sdk.get("cpp")
    if cpp is not None:
        require(isinstance(cpp, dict), "Invalid C++ SDK metadata")
        require(isinstance(cpp.get("version"), str) and bool(cpp["version"]), "Missing C++ SDK version")
        require(type(cpp.get("abi")) is int and cpp["abi"] > 0, "Invalid C++ ABI")
        require(isinstance(cpp.get("schema_pack"), str) and bool(cpp["schema_pack"]), "Missing C++ Schema pairing")
        check_reference(root, cpp.get("reference"))
    require(bool(robots), "Missing robot profiles")
    for name, robot in robots.items():
        require(re.fullmatch(r"[a-z][a-z0-9_]*", name) is not None, "Invalid robot identifier")
        require(robot.get("format_version") == 1 and robot.get("robot_type") == name,
                f"Invalid robot profile: {name}")
        require(robot.get("release_scope") in ("current_target", "planned"), "Invalid release scope")
        require(isinstance(robot.get("models"), list) and all(
            isinstance(model, str) and model for model in robot["models"]), "Invalid model list")
        require(robot.get("minimum_firmware") is None or isinstance(robot["minimum_firmware"], str),
                "Invalid robot firmware version")
        check_reference(root, robot.get("guide"))
        for field in ("sensor_reference", "connection_reference"):
            check_reference(root, robot.get(field), optional=True)
    entries = catalog.get("capabilities")
    require(isinstance(entries, list) and bool(entries), "Missing capabilities")
    identifiers = set()
    for entry in entries:
        require(isinstance(entry, dict), "Capability must be an object")
        identifier = entry.get("id")
        require(isinstance(identifier, str) and re.fullmatch(r"[a-z][a-z0-9.-]*", identifier),
                "Invalid capability identifier")
        require(identifier not in identifiers, f"Duplicate capability: {identifier}")
        identifiers.add(identifier)
        require(entry.get("availability") in ("implemented", "documented", "planned"),
                f"Invalid availability: {identifier}")
        types = entry.get("robot_types")
        require(isinstance(types, list) and all(isinstance(name, str) and name in robots for name in types),
                f"Unknown robot type in {identifier}")
        require(len(types) == len(set(types)), f"Duplicate robot type in {identifier}")
        require(type(entry.get("requires_sdk")) is bool, "requires_sdk must be boolean")
        require(entry.get("execution_location") in (
            "developer_host_or_container", "device_service", "developer_tool_service", "device_shell"), "Invalid execution location")
        require(entry.get("interface_kind") in (None, "local_cli", "pub_sub", "service", "action", "http", "http_mcp"),
                "Invalid interface kind")
        require(entry.get("effect") in ("local_read_only", "device_read_only", "depends_on_operation"),
                "Invalid effect")
        require(entry.get("verification") in ("local_tests", "documentation_only", "not_verified"),
                "Invalid verification state")
        require(entry.get("minimum_firmware") is None or isinstance(entry["minimum_firmware"], str),
                "Invalid capability firmware version")
        if not types:
            require(entry.get("effect") == "local_read_only" and entry.get("interface_kind") == "local_cli",
                    "Only local inventory capabilities may omit robot types")
        check_reference(root, entry.get("reference"))
        for field in ("skill", "tool", "recipe"):
            check_reference(root, entry.get(field), optional=True)
        implementations = entry.get("implementations", {})
        require(isinstance(implementations, dict), "Invalid implementations")
        for language, implementation in implementations.items():
            require(language in ("python", "cpp") and isinstance(implementation, dict), "Invalid implementation language")
            source = implementation.get("source")
            check_reference(root, source)
            require(source.endswith(".py" if language == "python" else ".cc"), "Invalid implementation source")
            target = implementation.get("bazel_target")
            expected = "//" + str(PurePosixPath(source).parent) + (":main" if language == "python" else ":main_cpp")
            require(target == expected, "Implementation target does not match source directory")
            check_reference(root, str(PurePosixPath(source).parent / "BUILD.bazel"))
        if entry["availability"] == "implemented":
            require(entry.get("tool") is not None, "Implemented capability needs an executable entry")
        if entry["availability"] == "planned":
            require(entry.get("tool") is None, "Planned capability cannot advertise an executable entry")


def load_catalog(root):
    root = Path(root)
    catalog = read_object(root / "catalog/capabilities.json")
    robots = {path.stem: read_object(path) for path in sorted((root / "catalog/robots").glob("*.json"))}
    validate_catalog(root, catalog, robots)
    return catalog, robots


def select_robot(robots, robot_type):
    if robot_type is None:
        return None
    require(robot_type in robots, f"Unknown robot type: {robot_type}")
    return robots[robot_type]


def capability_decision(entry, robot, sdk):
    if not entry["robot_types"]:
        return "local_only" if entry["availability"] == "implemented" else "blocked_integration"
    if robot is None:
        return "requires_robot_selection"
    if robot["release_scope"] != "current_target":
        return "blocked_release"
    if robot["robot_type"] not in entry["robot_types"]:
        return "not_applicable"
    if entry["availability"] == "planned" or (entry["requires_sdk"] and sdk["integration"] != "integrated"):
        return "blocked_integration"
    return "requires_device_verification"


def query_catalog(root, robot_type=None, capability=None):
    catalog, robots = load_catalog(root)
    robot = select_robot(robots, robot_type)
    entries = catalog["capabilities"]
    if capability is not None:
        entries = [entry for entry in entries if entry["id"] == capability]
        require(bool(entries), f"Unknown capability: {capability}")
    return {
        "format_version": 1,
        "robot": robot,
        "sdk": catalog["sdk"],
        "capabilities": [dict(entry, decision=capability_decision(entry, robot, catalog["sdk"])) for entry in entries],
        "device_contacted": False,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--robot-type")
    parser.add_argument("--capability")
    args = parser.parse_args(argv)
    try:
        result = query_catalog(args.root, args.robot_type, args.capability)
    except CatalogError as error:
        print(json.dumps({"error": str(error), "device_contacted": False}))
        return 2
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
