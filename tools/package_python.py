"""Package one Recipe and pinned wheels locally; never build, install or contact a robot."""

import argparse
import gzip
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import sys
import tarfile
from zipfile import BadZipFile

from container_context import require_dev_container
from sdk_assets import ROOT, configuration, digest, verify_release, wheel_info, wheel_names


def requirements(config):
    return "".join(f"{name.replace('_', '-')}=={version}\n"
                   for name, version in sorted(config["sdk"]["python"]["wheels"].items()))


def recipe_names(root=ROOT):
    catalog = json.loads((root / "catalog/capabilities.json").read_text())
    sources = {entry["implementations"]["python"]["source"] for entry in catalog["capabilities"]
               if "python" in entry.get("implementations", {})}
    return sorted(path.parent.name for source in sources if
                  (path := PurePosixPath(source)).parts[:1] == ("recipes",)
                  and len(path.parts) == 3 and path.name == "main.py")


def source_names(recipe):
    return ["LICENSE", "NOTICE", "recipes/__init__.py", "recipes/common.py", "recipes/observe.py",
            f"recipes/{recipe}/main.py"]


def plan(config, recipe, assets, target, root=ROOT):
    if recipe not in recipe_names(root):
        raise ValueError("select a Recipe from the capability catalog")
    sources = source_names(recipe)
    for name in sources:
        path = root / name
        if path.is_symlink() or not path.is_file() or not path.resolve().is_relative_to(root.resolve()):
            raise ValueError(f"missing or unsafe source file: {name}")
    names = wheel_names(config, target)
    license_name = f'flatbuffers-{config["sdk"]["python"]["wheels"]["flatbuffers"]}.LICENSE'
    verify_release(config, assets, [*names.values(), license_name])
    versions = config["sdk"]["python"]["wheels"]
    wheels = [dict(file="wheelhouse/" + file,
                   **wheel_info(assets / file, name, versions[name], target, versions))
              for name, file in names.items()]
    return {
        "format_version": 1, "recipe": recipe, "module": f"recipes.{recipe}.main",
        "target_platform": target, "intended_use": "robot" if target == "linux_aarch64" else "local_preview",
        "robot_type": "foot_quadruped" if target == "linux_aarch64" else None,
        "application_version": config["robots"]["foot_quadruped"]["application_version"],
        "sdk_release": config["sdk"]["release_tag"],
        "minimum_python": config["sdk"]["python"]["minimum_version"],
        "dependency_profile": "base", "wheels": wheels,
        "source_files": {name: digest(root / name) for name in sources},
        "optional_features_not_packaged": ["audio/video payload extraction (NumPy)", "image decoding (PyAV)"],
    }


def package(config, recipe, assets, output, target="linux_aarch64", root=ROOT):
    manifest = plan(config, recipe, assets, target, root)
    output = output.absolute()
    if output.is_symlink() or output.exists():
        raise ValueError("package output must be a new directory; existing output is never overwritten")
    if output.resolve().is_relative_to(root.resolve()) and not output.resolve().is_relative_to((root / "artifacts").resolve()):
        raise ValueError("keep generated packages under artifacts/ or outside the checkout")
    output.mkdir(parents=True, exist_ok=False)
    # No user directories are removed on failure. SHA256SUMS is written last.
    with (output / "python-recipe.tar.gz").open("xb") as stream:
        with gzip.GzipFile(filename="", fileobj=stream, mode="wb", mtime=0) as compressed:
            with tarfile.open(fileobj=compressed, mode="w") as archive:
                for name in source_names(recipe):
                    payload = (root / name).read_bytes()
                    info = tarfile.TarInfo(name)
                    info.size, info.mode, info.mtime = len(payload), 0o644, 0
                    archive.addfile(info, io.BytesIO(payload))
    (output / "wheelhouse").mkdir()
    for item in manifest["wheels"]:
        shutil.copyfile(assets / Path(item["file"]).name, output / item["file"])
    (output / "licenses").mkdir()
    license_name = f'flatbuffers-{config["sdk"]["python"]["wheels"]["flatbuffers"]}.LICENSE'
    shutil.copyfile(assets / license_name, output / "licenses" / license_name)
    shutil.copyfile(assets / "EDU_SDK_MANIFEST.json", output / "EDU_SDK_MANIFEST.json")
    (output / "requirements.txt").write_text(requirements(config))
    files = {str(path.relative_to(output)): digest(path) for path in sorted(output.rglob("*")) if path.is_file()}
    manifest["files"] = files
    (output / "PACKAGE_MANIFEST.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    checksums = dict(files, **{"PACKAGE_MANIFEST.json": digest(output / "PACKAGE_MANIFEST.json")})
    (output / "SHA256SUMS").write_text("".join(f"{value}  {name}\n" for name, value in sorted(checksums.items())))
    verify_package(config, output)
    return manifest


def verify_package(config, directory):
    if directory.is_symlink():
        raise ValueError("package directory must not be a symlink")
    # Validate both controls before reading either, including when one is a FIFO.
    for name in ("PACKAGE_MANIFEST.json", "SHA256SUMS"):
        path = directory / name
        if path.is_symlink() or not path.is_file() or not path.resolve().is_relative_to(directory.resolve()):
            raise ValueError(f"package control must be a regular file inside the package: {name}")
    manifest = json.loads((directory / "PACKAGE_MANIFEST.json").read_text())
    if not isinstance(manifest, dict) or manifest.get("format_version") != 1 or manifest.get("sdk_release") != config["sdk"]["release_tag"]:
        raise ValueError("package format or SDK pairing mismatch")
    recipe = manifest.get("recipe")
    if recipe not in recipe_names() or manifest.get("module") != f"recipes.{recipe}.main":
        raise ValueError("invalid packaged Recipe")
    if manifest.get("target_platform") not in ("linux_aarch64", "linux_x86_64"):
        raise ValueError("unsupported package platform")
    robot = manifest["target_platform"] == "linux_aarch64"
    expected = {"intended_use": "robot" if robot else "local_preview",
                "robot_type": "foot_quadruped" if robot else None,
                "application_version": config["robots"]["foot_quadruped"]["application_version"],
                "minimum_python": config["sdk"]["python"]["minimum_version"], "dependency_profile": "base"}
    if any(manifest.get(key) != value for key, value in expected.items()):
        raise ValueError("package target or dependency profile mismatch")
    files = manifest.get("files")
    if not isinstance(files, dict) or not files or any(
            not isinstance(name, str) or not isinstance(value, str) or not re.fullmatch(r"[a-f0-9]{64}", value)
            for name, value in files.items()):
        raise ValueError("package file inventory is missing")
    names = wheel_names(config, manifest["target_platform"])
    license_name = f'flatbuffers-{config["sdk"]["python"]["wheels"]["flatbuffers"]}.LICENSE'
    expected_files = {"python-recipe.tar.gz", "requirements.txt", "EDU_SDK_MANIFEST.json",
                      "licenses/" + license_name, *["wheelhouse/" + name for name in names.values()]}
    if set(files) != expected_files:
        raise ValueError("unexpected package file inventory")
    sources = manifest.get("source_files")
    if not isinstance(sources, dict) or set(sources) != set(source_names(recipe)):
        raise ValueError("invalid source file inventory")
    actual = {str(path.relative_to(directory)) for path in directory.rglob("*")
              if not path.is_dir() or path.is_symlink()}
    if actual != set(files) | {"PACKAGE_MANIFEST.json", "SHA256SUMS"}:
        raise ValueError("package file inventory changed")
    expected_sums = dict(files, **{"PACKAGE_MANIFEST.json": digest(directory / "PACKAGE_MANIFEST.json")})
    expected_text = "".join(f"{value}  {name}\n" for name, value in sorted(expected_sums.items()))
    if (directory / "SHA256SUMS").read_text() != expected_text:
        raise ValueError("package checksum inventory mismatch")
    for name, expected in files.items():
        path = directory / name
        if PurePosixPath(name).is_absolute() or ".." in PurePosixPath(name).parts or "\\" in name:
            raise ValueError("unsafe package path")
        if path.is_symlink() or not path.is_file() or not path.resolve().is_relative_to(directory.resolve()) or digest(path) != expected:
            raise ValueError(f"package checksum mismatch: {name}")
    inventory = {item["name"]: item["sha256"] for item in config["sdk"]["assets"]}
    expected_wheels = [dict(file="wheelhouse/" + filename,
                           **wheel_info(directory / "wheelhouse" / filename, name,
                                        config["sdk"]["python"]["wheels"][name], manifest["target_platform"],
                                        config["sdk"]["python"]["wheels"])) for name, filename in names.items()]
    if manifest.get("wheels") != expected_wheels:
        raise ValueError("package wheel inventory mismatch")
    for name in names.values():
        if files.get("wheelhouse/" + name) != inventory[name]:
            raise ValueError("package wheel does not match the pinned release")
    if files.get("EDU_SDK_MANIFEST.json") != inventory["EDU_SDK_MANIFEST.json"]:
        raise ValueError("package SDK manifest mismatch")
    if files.get("licenses/" + license_name) != inventory[license_name]:
        raise ValueError("package license mismatch")
    if (directory / "requirements.txt").read_text() != requirements(config):
        raise ValueError("package requirements do not match the release")
    with tarfile.open(directory / "python-recipe.tar.gz", "r:gz") as archive:
        members = archive.getmembers()
        if len(members) != len(source_names(recipe)) or {item.name for item in members} != set(source_names(recipe)):
            raise ValueError("source archive inventory mismatch")
        for item in members:
            if not item.isfile() or item.size > 1024 * 1024:
                raise ValueError("unsafe source archive entry")
            if hashlib.sha256(archive.extractfile(item).read()).hexdigest() != manifest["source_files"].get(item.name):
                raise ValueError("source archive checksum mismatch")
    return manifest


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--recipe", choices=recipe_names())
    parser.add_argument("--assets-dir", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--platform", choices=("linux_aarch64", "linux_x86_64"),
                        help="packaging only; default: linux_aarch64")
    parser.add_argument("--verify", type=Path, help="read-only verification of an existing package; allowed outside the container")
    args = parser.parse_args(argv)
    try:
        config = configuration()
        if args.verify:
            if any(value is not None for value in (args.recipe, args.assets_dir, args.output, args.platform)):
                parser.error("--verify cannot be combined with packaging arguments")
            verify_package(config, args.verify.absolute())
        else:
            if not all((args.recipe, args.assets_dir, args.output)):
                parser.error("packaging requires --recipe, --assets-dir and --output")
            require_dev_container()
            package(config, args.recipe, args.assets_dir.resolve(), args.output, args.platform or "linux_aarch64")
        print(json.dumps({"status": "complete", "device_contacted": False, "deployed": False}))
        return 0
    except (OSError, ValueError, RuntimeError, KeyError, tarfile.TarError, BadZipFile) as error:
        print(str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
