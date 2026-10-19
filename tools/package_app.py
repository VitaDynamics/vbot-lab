"""Package an explicitly listed standalone application and verified SDK wheels."""

import argparse
import gzip
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import tarfile
from zipfile import BadZipFile

from container_context import require_dev_container
from package_python import requirements
from sdk_assets import ROOT, configuration, digest, verify_release, wheel_info, wheel_names

RESERVED_ROOTS = frozenset({"APP.json", "EDU_SDK_MANIFEST.json", "SHA256SUMS",
                            "requirements.txt", "application.tar.gz", "wheelhouse", "licenses"})


def validate_manifest(value, config, *, packaged=False):
    if isinstance(value, dict) and value.get("language") == "cpp":
        raise ValueError("package_app.py packages Python only; follow the C++ project's README for binary packaging")
    fields = {"format_version", "name", "module", "sdk_release", "source_files"}
    if packaged:
        fields |= {"target_platform", "source_hashes"}
    if (not isinstance(value, dict) or set(value) != fields
            or type(value["format_version"]) is not int or value["format_version"] != 1
            or not isinstance(value["name"], str) or not re.fullmatch(r"[a-z](?:[a-z0-9-]{0,46}[a-z0-9])?", value["name"])
            or not isinstance(value["module"], str) or not re.fullmatch(r"[a-zA-Z_]\w*(?:\.[a-zA-Z_]\w*)+", value["module"])
            or value["sdk_release"] != config["sdk"]["release_tag"]):
        raise ValueError("application manifest or SDK release mismatch")
    files = value["source_files"]
    if (not isinstance(files, list) or not files or any(not isinstance(name, str) for name in files)
            or len(set(files)) != len(files) or not {"LICENSE", "NOTICE", value["module"].replace(".", "/") + ".py"} <= set(files)):
        raise ValueError("explicit source, license and entrypoint inventory required")
    for name in files:
        path = PurePosixPath(name)
        if (not path.parts or path.is_absolute() or ".." in path.parts or str(path) != name or "\\" in name
                or any(part.startswith(".") for part in path.parts)):
            raise ValueError("unsafe or unsupported application source path")
        # Application files are extracted beside, not over, the bundle controls.
        # This shared manifest check protects both package() and verify().
        if path.parts[0] in RESERVED_ROOTS:
            raise ValueError(f"application source uses reserved deployment path: {path.parts[0]}")
        if ((name not in ("LICENSE", "NOTICE") and path.suffix not in (".py", ".json"))
                or "session" in name.lower() or "credential" in name.lower()):
            raise ValueError("unsafe or unsupported application source path")
    return value


def read_manifest(project, config):
    control = project / "APP.json"
    if control.is_symlink() or not control.is_file():
        raise ValueError("APP.json must be a regular file")
    return validate_manifest(json.loads(control.read_text()), config)


def package(project, assets, output, target="linux_aarch64"):
    require_dev_container()
    config = configuration()
    manifest = read_manifest(project, config)
    sources = {}
    for name in manifest["source_files"]:
        path = project / name
        if path.is_symlink() or not path.is_file() or not path.resolve().is_relative_to(project.resolve()) or path.stat().st_size > 1024 * 1024:
            raise ValueError("missing, unsafe or oversized application source")
        sources[name] = path.read_bytes()
    dependency_file = project / "requirements.txt"
    if dependency_file.is_symlink() or not dependency_file.is_file() or dependency_file.read_text() != requirements(config):
        raise ValueError("application requirements must match the selected release")
    names = wheel_names(config, target)
    license_name = f'flatbuffers-{config["sdk"]["python"]["wheels"]["flatbuffers"]}.LICENSE'
    verify_release(config, assets, [*names.values(), license_name])
    for name, filename in names.items():
        wheel_info(assets / filename, name, config["sdk"]["python"]["wheels"][name], target, config["sdk"]["python"]["wheels"])
    if output.exists() or output.is_symlink():
        raise ValueError("package output must be a new directory")
    if output.resolve().is_relative_to(project.resolve()):
        raise ValueError("keep deployment packages outside the application source tree")
    if output.resolve().is_relative_to(ROOT.resolve()) and not output.resolve().is_relative_to((ROOT / "artifacts").resolve()):
        raise ValueError("keep generated packages under artifacts/ or outside the reference checkout")
    output.mkdir(parents=True, exist_ok=False)
    with (output / "application.tar.gz").open("xb") as raw:
        with gzip.GzipFile(filename="", fileobj=raw, mode="wb", mtime=0) as compressed:
            with tarfile.open(fileobj=compressed, mode="w") as archive:
                for name, data in sorted(sources.items()):
                    member = tarfile.TarInfo(name)
                    member.size, member.mode, member.mtime = len(data), 0o644, 0
                    archive.addfile(member, io.BytesIO(data))
    (output / "wheelhouse").mkdir()
    for filename in names.values():
        shutil.copyfile(assets / filename, output / "wheelhouse" / filename)
    (output / "licenses").mkdir()
    shutil.copyfile(assets / license_name, output / "licenses" / license_name)
    shutil.copyfile(assets / "EDU_SDK_MANIFEST.json", output / "EDU_SDK_MANIFEST.json")
    (output / "requirements.txt").write_text(requirements(config))
    manifest.update(target_platform=target, source_hashes={name: hashlib.sha256(data).hexdigest() for name, data in sources.items()})
    (output / "APP.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    files = {str(path.relative_to(output)): digest(path) for path in sorted(output.rglob("*")) if path.is_file()}
    (output / "SHA256SUMS").write_text("".join(f"{value}  {name}\n" for name, value in sorted(files.items())))
    verify(output, config)


def verify(directory, config=None):
    config = configuration() if config is None else config
    if directory.is_symlink() or not directory.is_dir():
        raise ValueError("expected a regular package directory")
    for name in ("APP.json", "SHA256SUMS"):
        if (directory / name).is_symlink() or not (directory / name).is_file():
            raise ValueError("package controls must be regular files")
    manifest = validate_manifest(json.loads((directory / "APP.json").read_text()), config, packaged=True)
    target = manifest.get("target_platform")
    if target not in ("linux_x86_64", "linux_aarch64"):
        raise ValueError("unsupported package architecture")
    names = wheel_names(config, target)
    license_name = f'flatbuffers-{config["sdk"]["python"]["wheels"]["flatbuffers"]}.LICENSE'
    expected = {"APP.json", "application.tar.gz", "requirements.txt", "EDU_SDK_MANIFEST.json", "licenses/" + license_name,
                *["wheelhouse/" + filename for filename in names.values()]}
    actual = {str(path.relative_to(directory)) for path in directory.rglob("*") if not path.is_dir() or path.is_symlink()}
    if actual != expected | {"SHA256SUMS"}:
        raise ValueError("package inventory changed")
    hashes = {}
    for name in sorted(expected):
        path = directory / name
        if path.is_symlink() or not path.is_file():
            raise ValueError("all package contents must be regular files")
        hashes[name] = digest(path)
    if (directory / "SHA256SUMS").read_text() != "".join(f"{value}  {name}\n" for name, value in sorted(hashes.items())):
        raise ValueError("package checksum mismatch")
    inventory = {entry["name"]: entry["sha256"] for entry in config["sdk"]["assets"]}
    for name in (*names.values(), "EDU_SDK_MANIFEST.json", license_name):
        package_name = "wheelhouse/" + name if name in names.values() else "licenses/" + name if name == license_name else name
        if hashes[package_name] != inventory[name]:
            raise ValueError("package does not contain pinned release files")
    if (directory / "requirements.txt").read_text() != requirements(config):
        raise ValueError("package requirements mismatch")
    sources = manifest.get("source_hashes")
    if (not isinstance(sources, dict) or set(sources) != set(manifest["source_files"])
            or any(not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value) for value in sources.values())):
        raise ValueError("missing source inventory")
    with tarfile.open(directory / "application.tar.gz", "r:gz") as archive:
        members = archive.getmembers()
        if len(members) != len(sources) or {item.name for item in members} != set(sources):
            raise ValueError("source archive inventory mismatch")
        for item in members:
            path = PurePosixPath(item.name)
            if not item.isfile() or item.size > 1024 * 1024 or path.is_absolute() or ".." in path.parts or "\\" in item.name:
                raise ValueError("unsafe application archive entry")
            if hashlib.sha256(archive.extractfile(item).read()).hexdigest() != sources[item.name]:
                raise ValueError("application source checksum mismatch")
    return manifest


def main(argv=None):
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--project", type=Path)
    cli.add_argument("--assets-dir", type=Path)
    cli.add_argument("--output", type=Path)
    cli.add_argument("--platform", choices=("linux_aarch64", "linux_x86_64"))
    cli.add_argument("--verify", type=Path)
    args = cli.parse_args(argv)
    try:
        if args.verify is not None:
            if any(value is not None for value in (args.project, args.assets_dir, args.output, args.platform)):
                cli.error("verification cannot be combined with packaging arguments")
            verify(args.verify.absolute())
        else:
            if any(value is None for value in (args.project, args.assets_dir, args.output)):
                cli.error("packaging requires project, assets-dir and output")
            package(args.project.resolve(), args.assets_dir.resolve(), args.output.absolute(), args.platform or "linux_aarch64")
        print(json.dumps({"status": "complete", "device_contacted": False, "deployed": False}))
        return 0
    except (OSError, ValueError, RuntimeError, KeyError, TypeError, tarfile.TarError, BadZipFile) as error:
        print(str(error))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
