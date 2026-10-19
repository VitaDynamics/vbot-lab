"""Validate pinned SDK inputs without importing or installing their code."""

from email.parser import Parser
import hashlib
from pathlib import Path, PurePosixPath
import platform
import re
from zipfile import ZipFile

import check_release as release


ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    result = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(block)
    return result.hexdigest()


def configuration(root=ROOT):
    config = release.read_json(root / "catalog/release.json")
    release.validate(config, root)
    return config


def native_platform():
    machine = {"AMD64": "x86_64", "arm64": "aarch64"}.get(platform.machine(), platform.machine())
    if platform.system() != "Linux" or machine not in ("x86_64", "aarch64"):
        raise ValueError("SDK integration requires a Linux x86_64 or aarch64 development container")
    return "linux_" + machine


def wheel_names(config, target):
    if target not in config["sdk"]["python"]["platforms"]:
        raise ValueError("unsupported wheel platform")
    versions = config["sdk"]["python"]["wheels"]
    return {
        "aorta_sdk": f'aorta_sdk-{versions["aorta_sdk"]}-py3-none-{target}.whl',
        "aorta_msgs": f'aorta_msgs-{versions["aorta_msgs"]}-py3-none-any.whl',
        "vbot_edu_msgs": f'vbot_edu_msgs-{versions["vbot_edu_msgs"]}-py3-none-any.whl',
        "flatbuffers": f'flatbuffers-{versions["flatbuffers"]}-py2.py3-none-any.whl',
    }


def verify_assets(config, directory, names):
    inventory = {item["name"]: item["sha256"] for item in config["sdk"]["assets"]}
    for name in names:
        if name not in inventory:
            raise ValueError(f"asset is not in the pinned release: {name}")
        path = directory / name
        if path.is_symlink() or not path.is_file() or digest(path) != inventory[name]:
            raise ValueError(f"missing regular asset or checksum mismatch: {name}")


def verify_release(config, directory, names):
    metadata = ["EDU_SDK_MANIFEST.json", "SHA256SUMS"]
    verify_assets(config, directory, [*metadata, *names])
    release.check_sdk_manifest(config, directory / metadata[0])


def normalized(name):
    return re.sub(r"[-_.]+", "-", name).lower()


def wheel_info(path, name, version, target, versions):
    with ZipFile(path) as archive:
        entries = archive.infolist()
        if len(entries) > 10000 or sum(item.file_size for item in entries) > 512 * 1024 * 1024:
            raise ValueError("wheel exceeds inspection limits")
        for item in entries:
            relative = PurePosixPath(item.filename)
            if relative.is_absolute() or ".." in relative.parts or "\\" in item.filename:
                raise ValueError("unsafe wheel entry")
        metadata = [item.filename for item in entries if item.filename.endswith(".dist-info/METADATA")]
        if len(metadata) != 1:
            raise ValueError("wheel must contain one distribution metadata record")
        prefix = metadata[0].removesuffix("METADATA")
        info = Parser().parsestr(archive.read(metadata[0]).decode())
        if normalized(info.get("Name", "")) != normalized(name) or info.get("Version") != version:
            raise ValueError(f"wheel metadata does not match release: {path.name}")
        wheel = Parser().parsestr(archive.read(prefix + "WHEEL").decode())
        tags = wheel.get_all("Tag", [])
        if not any(tag.endswith("-" + target) or tag.endswith("-any") for tag in tags):
            raise ValueError(f"wheel platform mismatch: {path.name}")
        if name == "aorta_sdk" and not any(tag.endswith("-" + target) for tag in tags):
            raise ValueError("Aorta SDK must match the selected native platform")
        dependencies = []
        for dependency in info.get_all("Requires-Dist", []):
            match = re.fullmatch(r"([A-Za-z0-9_.-]+)\s*(?:\(?\s*==\s*([0-9.]+)\s*\)?)?", dependency)
            allowed = {normalized(key): value for key, value in versions.items()}
            if not match or normalized(match[1]) not in allowed:
                raise ValueError(f"unresolved SDK dependency: {dependency}")
            if match[2] is not None and match[2] != allowed[normalized(match[1])]:
                raise ValueError(f"SDK dependency version mismatch: {dependency}")
            dependencies.append(dependency)
        licenses = sorted(item.filename for item in entries if item.filename.startswith(prefix)
                          and not item.is_dir() and any(word in item.filename.lower()
                                                      for word in ("license", "notice", "copying")))
        if not licenses:
            raise ValueError(f"wheel has no bundled license material: {path.name}")
        return {"name": normalized(name), "version": version, "tags": tags,
                "requires_dist": dependencies, "license_files_in_wheel": licenses}
