"""Check pinned SDK installation, builds and package completeness without a robot."""

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import venv
from zipfile import BadZipFile

from container_context import require_dev_container
from create_app import create
from cpp_artifacts import inspect_arm64, require_arm64
from fetch_sdk import fetch
from package_python import package, recipe_names, verify_package
from package_app import package as package_application, verify as verify_application
from sdk_assets import ROOT, configuration, native_platform, verify_release, wheel_names


class BazelPreparationError(RuntimeError):
    """Safe tool-preparation diagnostics, without URLs, command output or credentials."""
    def __init__(self, code, reason, *, timeout=None, exit_code=None):
        super().__init__("Bazel preparation failed; check the selected version and download environment")
        self.report = {"status": "error", "stage": "bazel_prepare", "error_code": code, "reason": reason,
                       "next_step": "Check network, proxy and CA trust for the pinned Bazel download, then retry; no SDK compatibility failure is implied."}
        if code == "bazel_not_found":
            self.report["next_step"] = "Use the selected development container with Bazel or Bazelisk on PATH."
        elif code == "bazel_prepare_timeout":
            self.report["next_step"] = "Check first-use download access and optionally raise --bazel-prepare-timeout up to 600 seconds; this is not an SDK compatibility result."
        if timeout is not None:
            self.report["timeout_seconds"] = timeout
        if exit_code is not None:
            self.report["exit_code"] = exit_code


def prepare_bazel(environment, timeout):
    # The image may provide Bazelisk: --version can download the pinned Bazel on first use.
    try:
        return subprocess.run(["bazel", "--version"], cwd=ROOT, env=environment,
                              check=True, capture_output=True, text=True, timeout=timeout)
    except FileNotFoundError:
        raise BazelPreparationError("bazel_not_found", "tool_missing") from None
    except OSError:
        raise BazelPreparationError("bazel_prepare_failed", "tool_unavailable") from None
    except subprocess.TimeoutExpired:
        raise BazelPreparationError("bazel_prepare_timeout", "timeout", timeout=timeout) from None
    except subprocess.CalledProcessError as error:
        detail = str(error.stderr or "").lower()
        reasons = (("tls", ("certificate", "x509", "tls handshake")),
                   ("dns", ("no such host", "could not resolve", "name or service not known", "temporary failure in name")),
                   ("proxy", ("proxy",)),
                   ("http", ("403", "404", "forbidden", "unauthorized")),
                   ("integrity", ("checksum", "sha256 mismatch")),
                   ("network", ("connection", "network", "timeout", "timed out")))
        reason = next((name for name, markers in reasons if any(marker in detail for marker in markers)), "tool_failed")
        raise BazelPreparationError("bazel_prepare_failed", reason, exit_code=error.returncode) from None


# Runs in each newly installed venv, not in the integration driver's interpreter.
# Importing the SDK is insufficient: its native library is loaded lazily.
PYTHON_RUNTIME_PROBE = """
import json
from pathlib import Path
import sys
import aorta
from locomotion.LocomotionStatus import LocomotionStatus

prefix = Path(sys.prefix).resolve()
package = Path(aorta.__file__).resolve().parent
expected = package / 'libaorta_core.so'
if not package.is_relative_to(prefix):
    raise RuntimeError('Aorta Python package is outside the active venv')
if not expected.is_file() or not expected.resolve().is_relative_to(prefix):
    raise RuntimeError('wheel-bundled Aorta runtime is missing or outside the active venv')
core = aorta.load_library()
loaded = Path(core._name)
if not loaded.is_absolute() or loaded.resolve() != expected.resolve():
    raise RuntimeError('Aorta loaded a runtime other than the wheel-bundled library')
abi = core.aorta_abi_version()
if abi != int(sys.argv[1]):
    raise RuntimeError('Aorta Python native ABI does not match the release configuration')
print(json.dumps({'status': 'complete', 'probe': 'python_native_runtime', 'abi': abi,
                  'library': 'aorta/libaorta_core.so', 'device_contacted': False}))
"""

PYTHON_APPLICATION_WIRE_PROBE = """
import importlib
import json
from unittest.mock import patch
import aorta
from health_monitor.runtime import decode

with patch.object(aorta, 'Node', side_effect=AssertionError('offline probe must not open Node')):
    for stream, root in (('state', 'locomotion.LocomotionStatus'),
                         ('battery', 'bms.BmsState'), ('system', 'sm.SmStatus')):
        value = getattr(importlib.import_module(root), root.split('.')[-1] + 'T')()
        decode(stream, aorta.FlatbuffersActionCodec.serialize(value))
        try:
            decode(stream, bytes(8))
        except ValueError:
            pass
        else:
            raise RuntimeError('malformed input accepted by packaged application')
print(json.dumps({'status': 'complete', 'wire_validation': 'passed', 'device_contacted': False}))
"""


def execute(command, *, env, cwd=ROOT):
    subprocess.run([str(part) for part in command], cwd=cwd, env=env, check=True)


def check_cpp_workspace(work, environment, arm_environment=None):
    """Build the generated project in its own workspace, with no checkout labels."""
    project = work / "cpp-application"
    create(project, "health-monitor-app", "cpp")
    bazel = ["bazel", "--batch", "--ignore_all_rc_files", "--output_user_root=" + str(work / "app-bazel")]
    options = ["--enable_bzlmod", "--noenable_workspace", "--lockfile_mode=error"]
    execute([*bazel, "test", *options, "--test_output=errors", "--test_env=VBOT_DEV_CONTAINER=1",
             "//:model_test", "//:sdk_test", "//:cli_test"], env=environment, cwd=project)
    for arguments in ([], ["--simulate"]):
        result = subprocess.run([*bazel, "run", *options, "//:main", "--", "--config", "config.json", *arguments],
                                cwd=project, env=environment, check=True, capture_output=True, text=True, timeout=120)
        values = [json.loads(line) for line in result.stdout.splitlines()]
        if (not arguments and (len(values) != 1 or values[0].get("execute") is not False)) or (
                arguments and (len(values) != 2 or any(value.get("source") != "synthetic" for value in values))):
            raise ValueError("generated C++ application preview/simulation failed")
    artifacts = []
    if arm_environment is not None:
        arm_options = [*options, "--platforms=//toolchains:linux_arm64", "--incompatible_enable_cc_toolchain_resolution"]
        execute([*bazel, "build", *arm_options, "//:main", "//:model_test", "//:sdk_test"], env=arm_environment, cwd=project)
        output = subprocess.run([*bazel, "info", *arm_options, "bazel-bin"], cwd=project, env=arm_environment,
                                check=True, capture_output=True, text=True).stdout.strip()
        artifacts = inspect_arm64([Path(output) / name for name in ("main", "model_test", "sdk_test")],
                                  Path(arm_environment["AORTA_CPP_SDK_DIR"]))
    return {"native_tests": "passed", "preview_and_simulation": "passed", "arm64_artifacts": artifacts,
            "device_contacted": False}


def check_python_workspace(config, assets, work, environment, target):
    """Exercise the real standalone application package in another clean venv."""
    project = work / "python-application"
    create(project, "health-monitor-app", "python")
    bazel = ["bazel", "--batch", "--ignore_all_rc_files", "--output_user_root=" + str(work / "python-app-bazel")]
    # A new generated Python project has its own module graph and initial lockfile.
    options = ["--enable_bzlmod", "--noenable_workspace", "--lockfile_mode=update"]
    execute([*bazel, "build", *options, "//:main"], env=environment, cwd=project)
    execute([*bazel, "test", *options, "--test_output=errors", "--test_env=VBOT_DEV_CONTAINER=1",
             "//:model_test"], env=environment, cwd=project)
    bundle = work / "python-application-package"
    package_application(project, assets, bundle, target)
    verify_application(bundle, config)
    python = install(config, bundle / "wheelhouse", work / "python-application-runtime", target, environment,
                     requirements_file=bundle / "requirements.txt")
    execute(["sha256sum", "-c", "SHA256SUMS"], env=environment, cwd=bundle)
    with tarfile.open(bundle / "application.tar.gz", "r:gz") as archive:
        archive.extractall(bundle)  # Verified names, hashes and regular-file-only inventory.
    execute(["sha256sum", "-c", "SHA256SUMS"], env=environment, cwd=bundle)
    runtime_environment = dict(environment, PATH=str(python.parent) + os.pathsep + environment["PATH"],
                               ZENOH_SESSION_CONFIG_URI="/nonexistent-sdk-ci-device-config")
    execute([python, "-c", PYTHON_APPLICATION_WIRE_PROBE], env=runtime_environment, cwd=bundle)
    for arguments in ([], ["--simulate"]):
        result = subprocess.run([str(python), "-m", "health_monitor.main", "--config", "config.json", *arguments],
                                cwd=bundle, env=runtime_environment, check=True, capture_output=True, text=True, timeout=20)
        values = [json.loads(line) for line in result.stdout.splitlines()]
        if not arguments:
            if (len(values) != 1 or values[0].get("execute") is not False
                    or set(values[0].get("routes", {})) != {"state", "battery", "system"}):
                raise ValueError("packaged Python application preview failed")
        elif (len(values) != 2 or any(value.get("source") != "synthetic" for value in values)
                or values[0].get("all_streams_receiving") is not True
                or values[1].get("all_streams_receiving") is not False):
            raise ValueError("packaged Python application simulation failed")
    if target != "linux_aarch64":
        robot_bundle = work / "python-application-arm64-package"
        package_application(project, assets, robot_bundle, "linux_aarch64")
        verify_application(robot_bundle, config)
    return {"native_build_and_model_tests": "passed", "real_sdk_package_install": "passed", "wire_validation": "passed",
            "extraction_integrity": "passed", "preview_and_simulation": "passed", "arm64_package": "verified", "device_contacted": False}


def install(config, assets, location, target, environment, *, requirements_file=None):
    environment = dict(environment)
    environment.pop("AORTA_CORE_FFI_LIB", None)
    venv.EnvBuilder(with_pip=True).create(location)
    python = location / "bin/python"
    arguments = (["--find-links", assets, "-r", requirements_file] if requirements_file else
                 ["--no-deps", *[assets / name for name in wheel_names(config, target).values()]])
    execute([python, "-m", "pip", "install", "--no-index", *arguments], env=environment)
    execute([python, "-m", "pip", "check"], env=environment)
    execute([python, "-c", PYTHON_RUNTIME_PROBE, str(config["sdk"]["cpp"]["abi"])],
            env=environment)
    return python


def check_toolchain(config, target, environment, *, bazel_prepare_timeout=180):
    bazel = prepare_bazel(environment, bazel_prepare_timeout)
    if bazel.stdout.strip() != "bazel " + config["development"]["bazel_version"]:
        raise ValueError("Bazel version does not match release configuration")
    compiler = subprocess.run(["g++", "-dumpmachine"], cwd=ROOT, env=environment,
                              check=True, capture_output=True, text=True, timeout=20)
    if not compiler.stdout.strip().startswith(target.removeprefix("linux_") + "-"):
        raise ValueError("C++ compiler target does not match native SDK integration architecture")


def check_arm64_compilation_modes(bazel, options, environment):
    """Inspect actual compile actions; do not execute an ARM64 program."""
    modes = {"fastbuild": {"-O0"}, "opt": {"-O2", "-DNDEBUG"}, "dbg": {"-O0", "-g"}}
    checked = {}
    for mode, expected in modes.items():
        result = subprocess.run([*bazel, "aquery", *options, "-c", mode, "--output=jsonproto",
                                 'mnemonic("CppCompile", //recipes/subscribe-state:main_cpp)'],
                                cwd=ROOT, env=environment, check=True, capture_output=True, text=True)
        actions = json.loads(result.stdout).get("actions", [])
        if not actions:
            raise ValueError(f"ARM64 {mode} has no compile actions to inspect")
        for action in actions:
            arguments = action.get("arguments", [])
            flags = {flag for flag in arguments if flag.startswith(("-O", "-g")) or flag == "-DNDEBUG"}
            if not arguments or not arguments[0].startswith("/usr/bin/aarch64-linux-gnu-") or flags != expected:
                raise ValueError(f"ARM64 {mode} compiler/mode flags mismatch: {sorted(flags)}")
        checked[mode] = sorted(expected)
    return checked


def check(config, assets, work, *, download=False, bazel_prepare_timeout=180):
    if work.exists() or work.is_symlink():
        raise ValueError("SDK check work directory must be new; existing environments are never overwritten")
    target = native_platform()
    arch = target.removeprefix("linux_")
    cpp = config["sdk"]["cpp"]
    sdk_archive = f'aorta-cpp-sdk-{cpp["version"]}-abi{cpp["abi"]}-{cpp["distribution"]}-{arch}.tar.zst'
    if download:
        fetch(config, assets)
    # All download inputs are pinned and checked before extraction or installation.
    verify_release(config, assets, [item["name"] for item in config["sdk"]["assets"]])
    environment = dict(os.environ, PYTHONNOUSERSITE="1", PYTHONPATH="", VBOT_DEV_CONTAINER="1")
    environment.pop("ZENOH_SESSION_CONFIG_URI", None)
    environment.pop("AORTA_CORE_FFI_LIB", None)
    check_toolchain(config, target, environment, bazel_prepare_timeout=bazel_prepare_timeout)
    work.mkdir(parents=True, exist_ok=False)
    python = install(config, assets, work / "sdk-venv", target, environment)
    environment["PATH"] = str(python.parent) + os.pathsep + environment.get("PATH", "")
    for name, archive in (("cpp", sdk_archive), ("schema", config["schema"]["asset"])):
        destination = work / name
        destination.mkdir()
        execute(["tar", "--zstd", "-xf", assets / archive, "-C", destination], env=environment)
    # ABI is also checked by the repository rule's exact shared-library SONAME.
    if not (work / f'cpp/lib/libaorta_core.so.{cpp["abi"]}').is_file():
        raise ValueError("extracted C++ SDK ABI does not match the release")
    environment.update(AORTA_CPP_SDK_DIR=str(work / "cpp"), AORTA_EDU_SCHEMA_DIR=str(work / "schema"))
    bazel = ["bazel", "--batch", "--ignore_all_rc_files", "--output_user_root=" + str(work / "bazel")]
    options = ["--enable_bzlmod", "--noenable_workspace", "--lockfile_mode=error"]
    targets = [f"//recipes/{name}:main_cpp" for name in recipe_names()]
    execute([*bazel, "build", *options, "//recipes/...", *targets,
             "//blueprints/health-monitor:main", "//blueprints/health-monitor:main_cpp"], env=environment)
    execute([*bazel, "test", *options, "--test_output=errors",
             "--test_env=PATH=" + environment["PATH"], "--test_env=PYTHONNOUSERSITE=1", "--test_env=PYTHONPATH=",
             "--test_env=VBOT_DEV_CONTAINER=" + environment["VBOT_DEV_CONTAINER"],
             "//tests:recipe_sdk_test", "//tests:recipe_cpp_test", "//tests:recipe_cpp_sdk_test",
             "//blueprints/health-monitor:model_test", "//blueprints/health-monitor:model_cpp_test",
             "//blueprints/health-monitor:sdk_cpp_test", "//tests:health_monitor_cpp_test"], env=environment)
    arm64_artifacts = []
    arm64_compilation_modes = {}
    arm_environment = None
    if target == "linux_x86_64":
        cross = subprocess.run(["/usr/bin/aarch64-linux-gnu-g++", "-dumpmachine"],
                               check=True, capture_output=True, text=True, timeout=20)
        if cross.stdout.strip() != "aarch64-linux-gnu":
            raise ValueError("ARM64 cross-compiler target mismatch")
        arm_sdk = work / "cpp-arm64"
        arm_sdk.mkdir()
        arm_archive = f'aorta-cpp-sdk-{cpp["version"]}-abi{cpp["abi"]}-{cpp["distribution"]}-aarch64.tar.zst'
        execute(["tar", "--zstd", "-xf", assets / arm_archive, "-C", arm_sdk], env=environment)
        require_arm64(arm_sdk / f'lib/libaorta_core.so.{cpp["abi"]}')
        arm_environment = dict(environment, AORTA_CPP_SDK_DIR=str(arm_sdk))
        # --ignore_all_rc_files is deliberate: select the same checked-in platform explicitly.
        arm_options = [*options, "--platforms=//toolchains:linux_arm64", "--incompatible_enable_cc_toolchain_resolution"]
        execute([*bazel, "build", *arm_options, *targets, "//tests:recipe_cpp_sdk_test",
                 "//blueprints/health-monitor:main_cpp", "//blueprints/health-monitor:model_cpp_test",
                 "//blueprints/health-monitor:sdk_cpp_test"], env=arm_environment)
        output = subprocess.run([*bazel, "info", *arm_options, "bazel-bin"], cwd=ROOT, env=arm_environment,
                                check=True, capture_output=True, text=True).stdout.strip()
        binaries = [Path(output) / "recipes" / name / "main_cpp" for name in recipe_names()]
        binaries.append(Path(output) / "tests/recipe_cpp_sdk_test")
        binaries.extend(Path(output) / "blueprints/health-monitor" / name for name in ("main_cpp", "model_cpp_test", "sdk_cpp_test"))
        arm64_artifacts = inspect_arm64(binaries, arm_sdk)
        arm64_compilation_modes = check_arm64_compilation_modes(bazel, arm_options, arm_environment)
    cpp_workspace = check_cpp_workspace(work, environment, arm_environment)
    python_workspace = check_python_workspace(config, assets, work, environment, target)
    # A package built for the container can be checked in another clean venv without a robot.
    runtime_package = work / "package-smoke"
    package(config, "subscribe-state", assets, runtime_package, target)
    verify_package(config, runtime_package)
    runtime = work / "package-runtime"
    runtime_python = install(config, runtime_package / "wheelhouse", runtime, target, environment,
                             requirements_file=runtime_package / "requirements.txt")
    with tarfile.open(runtime_package / "python-recipe.tar.gz", "r:gz") as archive:
        archive.extractall(runtime_package)  # Inventory and regular-file-only contents verified above.
    result = subprocess.run([str(runtime_python), "-m", "recipes.subscribe-state.main"],
                            cwd=runtime_package, env=environment, capture_output=True, text=True, check=True, timeout=20)
    preview = json.loads(result.stdout)
    if preview.get("execute") is not False or preview.get("topic") != "/locomotion/status":
        raise ValueError("packaged read-only Recipe preview failed")
    robot_package = work / "robot-package"
    package(config, "subscribe-state", assets, robot_package, "linux_aarch64")
    verify_package(config, robot_package)
    execute([python, "tools/run_checks.py", "--scope", "packaging"], env=environment)
    return {"status": "complete", "sdk_release": config["sdk"]["release_tag"], "platform": target,
            "cpp_abi": cpp["abi"], "arm64_cross_artifacts": arm64_artifacts,
            "python_native_runtime": {"abi": cpp["abi"], "origin": "wheel",
                                      "environments": ["sdk-venv", "package-runtime"]},
            "arm64_compilation_modes": arm64_compilation_modes,
            "cpp_application_workspace": cpp_workspace,
            "python_application_workspace": python_workspace,
            "device_contacted": False, "robot_execution_verified": False}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--assets-dir", type=Path, required=True)
    parser.add_argument("--work-dir", type=Path, required=True)
    parser.add_argument("--download", action="store_true", help="explicitly download missing pinned release assets first")
    parser.add_argument("--bazel-prepare-timeout", type=int, default=180,
                        help="seconds allowed for first-use Bazel preparation, including Bazelisk downloads (30-600; default 180)")
    args = parser.parse_args(argv)
    if not 30 <= args.bazel_prepare_timeout <= 600:
        parser.error("--bazel-prepare-timeout must be between 30 and 600 seconds")
    try:
        require_dev_container()
        result = check(configuration(), args.assets_dir.resolve(), args.work_dir.absolute(), download=args.download,
                       bazel_prepare_timeout=args.bazel_prepare_timeout)
        print(json.dumps(result))
        return 0
    except BazelPreparationError as error:
        print(json.dumps(error.report), file=sys.stderr)
        return 1
    except (OSError, ValueError, RuntimeError, KeyError, subprocess.SubprocessError, BadZipFile) as error:
        print(str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
