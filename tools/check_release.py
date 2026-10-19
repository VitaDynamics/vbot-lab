"""Check release pairing locally. Never download, execute artifacts, or publish."""

import argparse
import ast
import hashlib
import json
from pathlib import Path
import re
import sys


DEFAULT_ROOT = Path(__file__).resolve().parents[1]


class ReleaseError(ValueError):
    """Invalid release configuration or inconsistent checkout."""


def require(condition, message):
    if not condition:
        raise ReleaseError(message)


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, f"Duplicate JSON field: {key}")
        result[key] = value
    return result


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique_object)


def fields(value, name, keys):
    require(isinstance(value, dict), f"{name}: expected object")
    require(set(value) == set(keys), f"{name}: missing or unknown fields")
    return value


def text(value, name, pattern):
    require(isinstance(value, str) and re.fullmatch(pattern, value) is not None,
            f"{name}: invalid value")


def version(value, name):
    text(value, name, r"\d+\.\d+\.\d+(?:-[A-Za-z0-9.-]+)?")


def tag(value, name, *, nullable=False):
    if nullable and value is None:
        return
    text(value, name, r"[A-Za-z0-9][A-Za-z0-9._-]*")
    require(".." not in value and not value.endswith((".", ".lock")), f"{name}: invalid tag")


def selections(value, name, allowed, *, optional=False):
    require(isinstance(value, list) and all(isinstance(item, str) for item in value),
            f"{name}: expected string list")
    require((optional or bool(value)) and len(set(value)) == len(value) and set(value) <= allowed,
            f"{name}: empty, duplicate or unsupported selection")


def assets(value, name, *, optional=False):
    require(isinstance(value, list) and (optional or bool(value)), f"{name}: expected asset list")
    result = {}
    for item in value:
        fields(item, name, ("name", "sha256"))
        text(item["name"], f"{name}.name", r"[A-Za-z0-9][A-Za-z0-9._+-]*")
        text(item["sha256"], f"{name}.sha256", r"[0-9a-f]{64}")
        require(item["name"] not in result, f"{name}: duplicate asset")
        result[item["name"]] = item["sha256"]
    return result


def recipe_versions(root):
    tree = ast.parse((root / "recipes/common.py").read_text(encoding="utf-8"))
    declarations = [node.value for node in tree.body if isinstance(node, ast.Assign)
                    and any(isinstance(target, ast.Name) and target.id == "SDK_VERSIONS"
                            for target in node.targets)]
    require(len(declarations) == 1, "recipes/common.py: missing or ambiguous SDK_VERSIONS")
    return ast.literal_eval(declarations[0])


def validate(config, root):
    fields(config, "release", ("format_version", "workspace", "robots", "sdk", "schema",
                               "development"))
    require(type(config["format_version"]) is int and config["format_version"] == 1,
            "Unsupported release format_version")
    workspace = fields(config["workspace"], "workspace", ("branch", "tag"))
    branch = workspace["branch"]
    require(isinstance(branch, str) and (branch == "main" or
            re.fullmatch(r"pre_release/V\d+\.\d+\.\d+\.X", branch) is not None),
            "workspace.branch: expected main or pre_release/V<major>.<minor>.<patch>.X")
    tag(workspace["tag"], "workspace.tag", nullable=True)
    if branch != "main" and workspace["tag"] is not None:
        family = branch.removeprefix("pre_release/").removesuffix(".X")
        require(re.fullmatch(re.escape(family) + r"\.\d+", workspace["tag"]) is not None,
                "workspace.tag: must match the iteration branch family and numeric iteration")
    robots = config["robots"]
    require(isinstance(robots, dict) and bool(robots), "robots: expected nonempty object")
    profiles = {path.stem: read_json(path) for path in (root / "catalog/robots").glob("*.json")}
    targets = {name for name, profile in profiles.items() if profile["release_scope"] == "current_target"}
    require(set(robots) == targets, "robots: must match current_target profiles")
    for name, robot in robots.items():
        fields(robot, f"robots.{name}", ("application_version",))
        text(robot["application_version"], f"robots.{name}.application_version", r"V\d+\.\d+\.\d+(?:-\d+)?")
        require(robot["application_version"] == profiles[name]["application_version"],
                f"robots.{name}: application version differs from robot profile")

    sdk = fields(config["sdk"], "sdk", ("repository", "release_tag", "aorta_version", "python", "cpp", "assets"))
    text(sdk["repository"], "sdk.repository", r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+")
    tag(sdk["release_tag"], "sdk.release_tag")
    version(sdk["aorta_version"], "sdk.aorta_version")
    python = fields(sdk["python"], "sdk.python", ("minimum_version", "wheels", "platforms"))
    text(python["minimum_version"], "sdk.python.minimum_version", r"\d+\.\d+")
    wheels = fields(python["wheels"], "sdk.python.wheels", ("aorta_sdk", "aorta_msgs", "vbot_edu_msgs", "flatbuffers"))
    for name, value in wheels.items():
        version(value, f"sdk.python.wheels.{name}")
    require(wheels["aorta_sdk"] == sdk["aorta_version"], "sdk: Python/Aorta version mismatch")
    selections(python["platforms"], "sdk.python.platforms",
               {"linux_x86_64", "linux_aarch64", "macosx_11_0_arm64"})
    cpp = fields(sdk["cpp"], "sdk.cpp", ("version", "abi", "distribution", "architectures"))
    version(cpp["version"], "sdk.cpp.version")
    require(cpp["version"] == sdk["aorta_version"], "sdk: C++/Aorta version mismatch")
    require(type(cpp["abi"]) is int and cpp["abi"] > 0, "sdk.cpp.abi: expected positive integer")
    text(cpp["distribution"], "sdk.cpp.distribution", r"[a-z][a-z0-9.]*")
    selections(cpp["architectures"], "sdk.cpp.architectures", {"x86_64", "aarch64"})
    inventory = assets(sdk["assets"], "sdk.assets")
    schema = fields(config["schema"], "schema", ("version", "pack_version", "asset", "sha256", "ros2_bridge_version"))
    version(schema["version"], "schema.version")
    version(schema["pack_version"], "schema.pack_version")
    require(schema["pack_version"] == schema["version"] or schema["pack_version"].startswith(schema["version"] + "-"),
            "schema: pack revision must belong to schema version")
    version(schema["ros2_bridge_version"], "schema.ros2_bridge_version")
    require(schema["asset"] == f'aorta-edu-schema-pack-{schema["pack_version"]}.tar.zst',
            "schema: archive name differs from pack_version")
    text(schema["sha256"], "schema.sha256", r"[0-9a-f]{64}")
    require(inventory.get(schema["asset"]) == schema["sha256"], "schema: SDK asset checksum mismatch")
    required = {"EDU_SDK_MANIFEST.json", "SHA256SUMS", schema["asset"],
                f'flatbuffers-{wheels["flatbuffers"]}.LICENSE',
                f'flatbuffers-{wheels["flatbuffers"]}-py2.py3-none-any.whl'}
    required.update(f'{name}-{wheels[name]}-py3-none-any.whl' for name in ("aorta_msgs", "vbot_edu_msgs"))
    required.update(f'aorta_sdk-{wheels["aorta_sdk"]}-py3-none-{platform}.whl' for platform in python["platforms"])
    required.update(f'aorta-cpp-sdk-{cpp["version"]}-abi{cpp["abi"]}-{cpp["distribution"]}-{arch}.tar.zst'
                    for arch in cpp["architectures"])
    require(required <= inventory.keys(), "sdk.assets: missing required wheel, archive, checksum or license metadata")

    catalog = read_json(root / "catalog/capabilities.json")["sdk"]
    require(catalog["version"] == sdk["aorta_version"] and catalog["release"] == sdk["release_tag"]
            and catalog["edu_messages_version"] == wheels["vbot_edu_msgs"], "sdk: capability catalog mismatch")
    require(all(catalog["cpp"][name] == cpp[name] for name in ("version", "abi"))
            and catalog["cpp"]["schema_pack"] == schema["pack_version"], "sdk.cpp: capability catalog mismatch")
    expected = {name.replace("_", "-"): wheels[name] for name in ("aorta_sdk", "aorta_msgs", "vbot_edu_msgs")}
    require(recipe_versions(root) == expected, "sdk.python: recipe SDK_VERSIONS mismatch")
    repository_rule = (root / "packages/aorta/cpp/repositories.bzl").read_text(encoding="utf-8")
    require(set(re.findall(r"lib/libaorta_core\.so\.(\d+)", repository_rule)) == {str(cpp["abi"])},
            "sdk.cpp: Bazel libaorta_core ABI mismatch")
    manifest = read_json(root / "schemas/MANIFEST.json")
    require(manifest["schema_pack"] == {"version": schema["version"], "asset": schema["asset"], "sha256": schema["sha256"]}
            and manifest["ros2_bridge_version"] == schema["ros2_bridge_version"], "schema: checked-in MANIFEST mismatch")
    for suffix in (".md", ".zh-CN.md"):
        py_guide = (root / f"packages/aorta/python/README{suffix}").read_text(encoding="utf-8")
        cpp_guide = (root / f"packages/aorta/cpp/README{suffix}").read_text(encoding="utf-8")
        release_url = f'https://github.com/{sdk["repository"]}/releases/tag/{sdk["release_tag"]}'
        require(release_url in py_guide and release_url in cpp_guide, "sdk: installation-guide Release link mismatch")
        require(all(value in py_guide for value in wheels.values())
                and python["minimum_version"] in py_guide, "sdk.python: installation-guide version mismatch")
        require(schema["pack_version"] in cpp_guide and cpp["version"] in cpp_guide,
                "sdk.cpp: installation-guide version mismatch")

    development = fields(config["development"], "development", ("bazel_version", "image"))
    version(development["bazel_version"], "development.bazel_version")
    require((root / ".bazelversion").read_text().strip() == development["bazel_version"], "development: Bazel version mismatch")
    image = fields(development["image"], "development.image", ("reference", "digest"))
    text(image["reference"], "development.image.reference", r"[A-Za-z0-9][A-Za-z0-9._:/-]*:[A-Za-z0-9._-]+")
    if image["digest"] is not None:
        text(image["digest"], "development.image.digest", r"sha256:[0-9a-f]{64}")
    compose = (root / "docker/compose.yaml").read_text(encoding="utf-8")
    selected = re.findall(r"\$\{VBOT_LAB_DEV_IMAGE:-(.*?)\}", compose)
    require(len(selected) == 1 and selected[0].split("@", 1)[0] == image["reference"],
            "development: Compose default image mismatch")
    if image["digest"] is not None:
        require(selected[0] == image["reference"] + "@" + image["digest"],
                "development: Compose default image digest mismatch")

    return [name for name, value in (("workspace.tag", workspace["tag"]),
                                    ("development.image.digest", image["digest"])) if value is None]


def check_sdk_manifest(config, path):
    manifest = read_json(path)
    require(isinstance(manifest, dict), "SDK manifest: expected object")
    schema, sdk = config["schema"], config["sdk"]
    require(manifest.get("release_tag") == sdk["release_tag"], "SDK manifest: Release tag mismatch")
    require(manifest.get("pairing") == {"aorta": sdk["aorta_version"], "schema_pack": schema["version"],
                                        "ros2_bridge": schema["ros2_bridge_version"], "wheels": sdk["python"]["wheels"]},
            "SDK manifest: component pairing mismatch")
    # The upstream inventory excludes its own manifest and SHA256SUMS to avoid self-hashing.
    declared = manifest.get("assets")
    require(isinstance(declared, list) and all(isinstance(item, dict) for item in declared),
            "SDK manifest: expected asset list")
    actual = assets([{"name": item.get("name"), "sha256": item.get("sha256")} for item in declared], "SDK manifest.assets")
    expected = {item["name"]: item["sha256"] for item in sdk["assets"]
                if item["name"] not in {"EDU_SDK_MANIFEST.json", "SHA256SUMS"}}
    require(actual == expected, "SDK manifest: asset inventory or checksum mismatch")


def check_assets(component, directory):
    directory = directory.resolve()
    for item in component["assets"]:
        path = directory / item["name"]
        require(not path.is_symlink() and path.is_file(), f'Missing regular asset: {item["name"]}')
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(block)
        require(digest.hexdigest() == item["sha256"], f'Asset checksum mismatch: {item["name"]}')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT, help="complete VBOT Lab checkout")
    parser.add_argument("--config", type=Path, help="configuration JSON; default: <root>/catalog/release.json")
    parser.add_argument("--require-complete", action="store_true", help="also reject unfilled source tag or image digest")
    parser.add_argument("--sdk-manifest", type=Path, help="compare an already-downloaded EDU_SDK_MANIFEST.json")
    parser.add_argument("--sdk-assets-dir", type=Path, help="hash all declared SDK assets in an existing directory")
    args = parser.parse_args(argv)
    try:
        root = args.root.resolve()
        config = read_json(args.config or root / "catalog/release.json")
        pending = validate(config, root)
        checked = []
        if args.sdk_manifest is not None:
            check_sdk_manifest(config, args.sdk_manifest)
            checked.append("sdk_manifest")
        if args.sdk_assets_dir is not None:
            check_assets(config["sdk"], args.sdk_assets_dir)
            checked.append("sdk_asset_hashes")
        print(json.dumps({"status": "incomplete" if pending else "consistent", "pending": pending,
                          "optional_checks": checked, "configuration_complete": not pending}))
        return 1 if args.require_complete and pending else 0
    except (OSError, ValueError, KeyError, TypeError, SyntaxError) as error:
        print(json.dumps({"status": "error", "error": str(error)}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
