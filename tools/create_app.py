"""Create a standalone Bazel application without installing or deploying anything."""

import argparse
import json
from pathlib import Path
import re
import shutil

from container_context import require_dev_container
from package_python import requirements
from sdk_assets import ROOT, configuration


def copy_file(source, destination, replacements=()):
    destination.parent.mkdir(parents=True, exist_ok=True)
    if replacements:
        text = source.read_text()
        for old, new in replacements:
            text = text.replace(old, new)
        destination.write_text(text)
    else:
        shutil.copyfile(source, destination)


def create_python(output, name, config):
    source = ROOT / "blueprints/health-monitor"
    files = ["config.json", "test_model.py", "BUILD.bazel", *[f"health_monitor/{path.name}" for path in sorted((source / "health_monitor").glob("*.py"))]]
    for filename in files:
        template = ROOT / "templates/python-app/BUILD.bazel.template" if filename == "BUILD.bazel" else source / filename
        copy_file(template, output / filename)
    (output / "MODULE.bazel").write_text('module(name = "' + name.replace('-', '_') + '", version = "0.1.0")\n')
    (output / "requirements.txt").write_text(requirements(config))
    return {"format_version": 1, "name": name, "module": "health_monitor.main",
            "sdk_release": config["sdk"]["release_tag"],
            "source_files": ["LICENSE", "NOTICE", "config.json", *[filename for filename in files if filename.startswith("health_monitor/")]]}


def create_cpp(output, name, config):
    replacements = (("blueprints/health-monitor/cpp/", "health_monitor/"),
                    ('"recipes/', '"support/'),
                    ('"blueprints/health-monitor/config.json"', '"config.json"'))
    for filename in ("model.h", "decoder.h", "main.cc", "model_test.cc", "sdk_test.cc"):
        copy_file(ROOT / "blueprints/health-monitor/cpp" / filename,
                  output / "health_monitor" / filename, replacements)
    for filename in ("cpp_common.h", "observe.h"):
        copy_file(ROOT / "recipes" / filename, output / "support" / filename, replacements)
    for filename in ("BUILD.bazel", "aarch64_gcc.bzl"):
        copy_file(ROOT / "toolchains" / filename, output / "toolchains" / filename)
    copy_file(ROOT / "packages/aorta/cpp/repositories.bzl", output / "sdk/repositories.bzl",
              (("packages/aorta/cpp/README.md", "README.md"),))
    (output / "sdk/BUILD.bazel").write_text('exports_files(["repositories.bzl"])\n')
    for filename in ("BUILD.bazel", "MODULE.bazel", ".bazelrc", "test_cli.py"):
        copy_file(ROOT / "templates/cpp-app" / (filename + ".template"), output / filename,
                  (("__APP_MODULE__", name.replace('-', '_')),))
    copy_file(ROOT / "MODULE.bazel.lock", output / "MODULE.bazel.lock")
    copy_file(ROOT / "blueprints/health-monitor/config.json", output / "config.json")
    return {"format_version": 1, "language": "cpp", "name": name,
            "sdk_release": config["sdk"]["release_tag"], "cpp_sdk_version": config["sdk"]["cpp"]["version"],
            "cpp_abi": config["sdk"]["cpp"]["abi"], "schema_pack": config["schema"]["pack_version"],
            "build_target": "//:main", "runtime_files": ["config.json"]}


def create(output, name, language="python"):
    require_dev_container()
    if not re.fullmatch(r"[a-z](?:[a-z0-9-]{0,46}[a-z0-9])?", name):
        raise ValueError("application name must be 1-48 lowercase letters, digits or hyphens, start with a letter and end with a letter or digit")
    if language not in ("python", "cpp"):
        raise ValueError("application language must be python or cpp")
    output = output.absolute()
    if output.exists() or output.is_symlink():
        raise ValueError("application output must be a new directory")
    if output.resolve().is_relative_to(ROOT.resolve()) and not output.resolve().is_relative_to((ROOT / "artifacts").resolve()):
        raise ValueError("create applications outside the reference checkout or under artifacts/")
    config = configuration()
    output.mkdir(parents=True, exist_ok=False)
    manifest = create_python(output, name, config) if language == "python" else create_cpp(output, name, config)
    for filename in ("LICENSE", "NOTICE", ".bazelversion"):
        shutil.copyfile(ROOT / filename, output / filename)
    (output / "APP.json").write_text(json.dumps(manifest, indent=2) + "\n")
    shutil.copyfile(ROOT / "templates/gitignore.template", output / ".gitignore")
    for suffix in (".md", ".zh-CN.md"):
        shutil.copyfile(ROOT / f"templates/{language}-app/README{suffix}", output / f"README{suffix}")
        shutil.copyfile(ROOT / f"templates/{language}-app/AGENTS{suffix}", output / f"AGENTS{suffix}")
    (output / "CLAUDE.md").write_text("@AGENTS.md\n")
    print(json.dumps({"status": "complete", "project": str(output), "language": language,
                      "device_contacted": False, "installed": False}))


def main(argv=None):
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--output", type=Path, required=True)
    cli.add_argument("--name", required=True)
    cli.add_argument("--language", choices=("python", "cpp"), default="python")
    args = cli.parse_args(argv)
    try:
        create(args.output, args.name, args.language)
        return 0
    except (OSError, ValueError, RuntimeError) as error:
        print(str(error))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
