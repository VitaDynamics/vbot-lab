"""Container-only application/model, workspace, package and diagnostic tests."""

from contextlib import contextmanager, redirect_stdout, redirect_stderr
import ast
import hashlib
import io
import json
import os
from pathlib import Path
import queue
import re
import shlex
import subprocess
import sys
import tarfile
import tempfile
import tokenize
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "tests"))
sys.path.insert(0, str(ROOT / "blueprints/health-monitor"))
from container_context import require_dev_container
import create_app
import diagnose
import package_app
import test_python_packaging as fixtures
from health_monitor import main as app, runtime
from health_monitor.model import Monitor
from health_monitor.errors import ApplicationError
from test_model import MonitorTests


class ApplicationTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.PackagingTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.root = self.fixture.directory
        self.project = self.root / "my-app"
        with redirect_stdout(io.StringIO()):
            create_app.create(self.project, "my-app")

    def test_generated_workspace_is_independent_and_complete(self):
        for name in ("MODULE.bazel", "BUILD.bazel", "test_model.py", "APP.json", "README.md", "README.zh-CN.md",
                     "AGENTS.md", "AGENTS.zh-CN.md", "CLAUDE.md", "LICENSE", "NOTICE", "requirements.txt", "health_monitor/wire.py"):
            self.assertTrue((self.project / name).is_file(), name)
        self.assertNotIn(str(ROOT), (self.project / "MODULE.bazel").read_text())
        self.assertEqual((self.project / "CLAUDE.md").read_text(), "@AGENTS.md\n")
        self.assertNotIn("main_cpp", (self.project / "BUILD.bazel").read_text())
        self.assertNotIn("//recipes:", (self.project / "BUILD.bazel").read_text())
        self.assertIn("health_monitor/wire.py", json.loads((self.project / "APP.json").read_text())["source_files"])

    def test_create_never_overwrites_existing_directory(self):
        before = (self.project / "APP.json").read_bytes()
        with self.assertRaises(ValueError):
            create_app.create(self.project, "my-app")
        self.assertEqual(before, (self.project / "APP.json").read_bytes())

    def test_generation_stops_before_writing_on_host(self):
        output = self.root / "denied"
        with patch.object(create_app, "require_dev_container", side_effect=RuntimeError("host")), self.assertRaises(RuntimeError):
            create_app.create(output, "new-app")
        self.assertFalse(output.exists())

    def test_package_is_explicit_reproducible_and_has_no_build_files(self):
        with patch.object(package_app, "configuration", return_value=self.fixture.config):
            for target in ("linux_x86_64", "linux_aarch64"):
                output = self.root / target
                package_app.package(self.project, self.fixture.assets, output, target)
                manifest = package_app.verify(output, self.fixture.config)
                self.assertEqual(manifest["target_platform"], target)
                self.assertNotIn("MODULE.bazel", manifest["source_files"])
                self.assertEqual(len(list((output / "wheelhouse").glob("*.whl"))), 4)
                again = self.root / (target + "-again")
                package_app.package(self.project, self.fixture.assets, again, target)
                self.assertEqual((output / "SHA256SUMS").read_bytes(), (again / "SHA256SUMS").read_bytes())

    def test_arbitrary_files_are_not_implicitly_packaged(self):
        (self.project / "private.env").write_text("do not copy")
        with patch.object(package_app, "configuration", return_value=self.fixture.config):
            output = self.root / "package"
            package_app.package(self.project, self.fixture.assets, output)
            self.assertNotIn("private.env", package_app.verify(output, self.fixture.config)["source_files"])

    def test_unsafe_manifest_source_is_rejected_before_output(self):
        path = self.project / "APP.json"
        original = json.loads(path.read_text())
        for name in ("../escape.py", "/absolute.py", ".env", "edu_session.json5", "credential.json", "a/../b.py"):
            value = dict(original, source_files=[*original["source_files"], name])
            path.write_text(json.dumps(value))
            with self.subTest(name=name), self.assertRaises(ValueError):
                package_app.read_manifest(self.project, self.fixture.config)

    def test_reserved_deployment_paths_are_rejected_before_reading_assets_or_creating_output(self):
        path = self.project / "APP.json"
        original = json.loads(path.read_text())
        cases = ("APP.json", "EDU_SDK_MANIFEST.json", "wheelhouse/data.json", "licenses/data.json",
                 "wheelhouse/example.whl/data.json", "SHA256SUMS/data.py", "requirements.txt/data.py",
                 "application.tar.gz/data.json")
        with patch.object(package_app, "configuration", return_value=self.fixture.config), \
             patch.object(package_app, "verify_release", side_effect=AssertionError("asset reads")):
            for index, name in enumerate(cases):
                path.write_text(json.dumps(dict(original, source_files=[*original["source_files"], name])))
                output = self.root / f"rejected-package-{index}"
                with self.subTest(name=name), self.assertRaisesRegex(ValueError, "reserved deployment path"):
                    package_app.package(self.project, self.fixture.assets, output)
                self.assertFalse(output.exists())

    def test_verifier_rejects_reserved_archive_members_even_with_rebuilt_checksums(self):
        for index, name in enumerate(("APP.json", "EDU_SDK_MANIFEST.json", "wheelhouse/data.json", "licenses/data.json",
                                      "SHA256SUMS/data.py", "requirements.txt/data.py", "application.tar.gz/data.json")):
            output = self.root / f"resealed-package-{index}"
            with patch.object(package_app, "configuration", return_value=self.fixture.config):
                package_app.package(self.project, self.fixture.assets, output)
            with tarfile.open(output / "application.tar.gz", "r:gz") as archive:
                sources = {member.name: archive.extractfile(member).read() for member in archive.getmembers()}
            sources[name] = b"{}\n"
            with tarfile.open(output / "application.tar.gz", "w:gz") as archive:
                for member_name, data in sorted(sources.items()):
                    member = tarfile.TarInfo(member_name)
                    member.size = len(data)
                    archive.addfile(member, io.BytesIO(data))
            control = output / "APP.json"
            manifest = json.loads(control.read_text())
            manifest["source_files"].append(name)
            manifest["source_hashes"][name] = hashlib.sha256(sources[name]).hexdigest()
            control.write_text(json.dumps(manifest))
            hashes = {str(path.relative_to(output)): package_app.digest(path) for path in output.rglob("*")
                      if path.is_file() and path.name != "SHA256SUMS"}
            (output / "SHA256SUMS").write_text("".join(f"{value}  {path}\n" for path, value in sorted(hashes.items())))
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, "reserved deployment path"):
                package_app.verify(output, self.fixture.config)

    def test_extracting_valid_packages_preserves_every_bundle_file_and_checksum(self):
        original = json.loads((self.project / "APP.json").read_text())
        # Only top-level deployment names are reserved; app-owned metadata is valid.
        for name in ("app-info.json", "health_monitor/APP.json", "health_monitor/licenses/data.json"):
            path = self.project / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("{}\n")
            original["source_files"].append(name)
        (self.project / "APP.json").write_text(json.dumps(original))
        with patch.object(package_app, "configuration", return_value=self.fixture.config):
            for target in ("linux_x86_64", "linux_aarch64"):
                output = self.root / ("extract-" + target)
                package_app.package(self.project, self.fixture.assets, output, target)
                manifest = package_app.verify(output, self.fixture.config)
                before = {path.relative_to(output): path.read_bytes() for path in output.rglob("*") if path.is_file()}
                subprocess.run(["sha256sum", "-c", "SHA256SUMS"], cwd=output, capture_output=True, check=True, timeout=10)
                subprocess.run(["tar", "-xzf", "application.tar.gz"], cwd=output, capture_output=True, check=True, timeout=10)
                subprocess.run(["sha256sum", "-c", "SHA256SUMS"], cwd=output, capture_output=True, check=True, timeout=10)
                for name, data in before.items():
                    self.assertEqual((output / name).read_bytes(), data, str(name))
                self.assertEqual(json.loads((output / "APP.json").read_text()), manifest)
                for name, expected in manifest["source_hashes"].items():
                    self.assertEqual(package_app.digest(output / name), expected, name)

    def test_changed_requirements_and_symlink_source_are_rejected(self):
        (self.project / "requirements.txt").write_text("unprovided==1.0\n")
        with patch.object(package_app, "configuration", return_value=self.fixture.config), self.assertRaises(ValueError):
            package_app.package(self.project, self.fixture.assets, self.root / "package")
        self.assertFalse((self.root / "package").exists())

    def test_package_corruption_or_extra_file_is_rejected(self):
        with patch.object(package_app, "configuration", return_value=self.fixture.config):
            output = self.root / "package"
            package_app.package(self.project, self.fixture.assets, output)
            (output / "extra.json").write_text("{}")
            with self.assertRaises(ValueError):
                package_app.verify(output, self.fixture.config)

    def test_invalid_manifest_fields_and_empty_application_are_rejected(self):
        original = json.loads((self.project / "APP.json").read_text())
        for values in ({"format_version": True}, {"name": None}, {"source_files": []},
                       {"module": "../escape"}, {"sdk_release": "different"}):
            with self.subTest(values=values), self.assertRaises(ValueError):
                package_app.validate_manifest(dict(original, **values), self.fixture.config)

    def test_packaging_is_rejected_on_host_before_output(self):
        output = self.root / "denied"
        with patch.object(package_app, "require_dev_container", side_effect=RuntimeError("host")), self.assertRaises(RuntimeError):
            package_app.package(self.project, self.fixture.assets, output)
        self.assertFalse(output.exists())

    def test_controls_are_not_available_and_preview_does_not_load_sdk(self):
        self.assertEqual(set(runtime.ROUTES), {"state", "battery", "system"})
        with patch.object(app, "subscription", side_effect=AssertionError("device")), redirect_stdout(io.StringIO()) as output:
            self.assertEqual(app.main([]), 0)
        self.assertFalse(json.loads(output.getvalue())["execute"])

    def test_default_configuration_file_is_not_ignored(self):
        path = self.root / "config.json"
        path.write_text(json.dumps({"stale_after_seconds": 9, "low_battery_percent": 10}))
        with patch.object(app, "DEFAULT_CONFIG", path), redirect_stdout(io.StringIO()) as output:
            self.assertEqual(app.main([]), 0)
        self.assertEqual(json.loads(output.getvalue())["config"]["stale_after_seconds"], 9)

    def test_simulation_exercises_receiving_and_stale_without_sdk(self):
        with patch.object(app, "subscription", side_effect=AssertionError("device")), redirect_stdout(io.StringIO()) as output:
            self.assertEqual(app.main(["--simulate"]), 0)
        states = [json.loads(line) for line in output.getvalue().splitlines()]
        self.assertTrue(states[0]["all_streams_receiving"])
        self.assertFalse(states[1]["all_streams_receiving"])

    def test_invalid_duration_and_conflicting_modes_do_not_open_sdk(self):
        for arguments in (["--duration", "nan"], ["--duration", "inf"], ["--duration", "0"], ["--execute", "--simulate"]):
            with patch.object(app, "subscription", side_effect=AssertionError("device")), redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                app.main(arguments)

    def test_generated_cli_process_exit_codes_for_preview_arguments_and_configuration(self):
        # Exercise the copied module's real __main__/entrypoint in a separate process.
        # Even a regression cannot import the SDK or create a device session.
        program = ("import runpy,sys; sys.modules['aorta'] = None; "
                   "sys.argv = ['health_monitor.main', *sys.argv[1:]]; "
                   "runpy.run_module('health_monitor.main', run_name='__main__')")
        bad_config = self.project / "bad-config.json"
        bad_config.write_text("{}")
        cases = (([], 0), (["--simulate"], 0), (["--help"], 0),
                 (["--duration", "nan"], 2), (["--duration", "0"], 2),
                 (["--unknown-option"], 2), (["--execute", "--simulate"], 2),
                 (["--config", str(self.project / "missing.json")], 1),
                 (["--config", str(bad_config)], 1))
        for arguments, expected in cases:
            with self.subTest(arguments=arguments):
                result = subprocess.run([sys.executable, "-c", program, *arguments], cwd=self.project,
                    env=dict(os.environ, PYTHONNOUSERSITE="1", PYTHONPATH="",
                             ZENOH_SESSION_CONFIG_URI="/nonexistent-application-test"),
                    capture_output=True, text=True, timeout=10)
                self.assertEqual(result.returncode, expected, result.stderr)
                if expected == 2:
                    self.assertIn("usage:", result.stderr)
                    self.assertEqual(result.stdout, "")
                elif expected == 1:
                    error = json.loads(result.stderr)
                    self.assertEqual(error["status"], "error")
                    self.assertEqual(error["stage"], "config")
                    self.assertEqual(error["error_code"], "config_not_found" if "missing.json" in arguments[-1] else "invalid_config")
                else:
                    self.assertEqual(result.stderr, "")
                    if not arguments:
                        self.assertFalse(json.loads(result.stdout)["execute"])
                    elif arguments == ["--simulate"]:
                        values = [json.loads(line) for line in result.stdout.splitlines()]
                        self.assertEqual([value["all_streams_receiving"] for value in values], [True, False])

    def test_configuration_failures_are_classified_before_device_access(self):
        cases = ((FileNotFoundError("private-path"), "config_not_found"),
                 (PermissionError("private-path"), "config_not_readable"),
                 (IsADirectoryError("private-path"), "config_not_readable"),
                 (OSError("private-path"), "config_read_failed"),
                 (UnicodeDecodeError("utf-8", b"\xff", 0, 1, "private-data"), "invalid_config"))
        for failure, code in cases:
            with self.subTest(code=code), patch.object(sys, "argv", ["monitor"]), \
                 patch.object(Path, "read_text", side_effect=failure), patch.object(app, "subscription") as subscribe, \
                 redirect_stderr(io.StringIO()) as output:
                self.assertEqual(app.entrypoint(), 1)
            error = json.loads(output.getvalue())
            self.assertEqual((error["stage"], error["error_code"]), ("config", code))
            self.assertNotIn("private-", output.getvalue())
            subscribe.assert_not_called()

    def test_invalid_configuration_does_not_leak_payload_or_open_sdk(self):
        for value in ('private-payload', '{}', '[]', '{"stale_after_seconds":true,"low_battery_percent":20}'):
            with self.subTest(value=value), patch.object(sys, "argv", ["monitor"]), \
                 patch.object(Path, "read_text", return_value=value), patch.object(app, "subscription") as subscribe, \
                 redirect_stderr(io.StringIO()) as output:
                self.assertEqual(app.entrypoint(), 1)
            self.assertEqual(json.loads(output.getvalue())["error_code"], "invalid_config")
            self.assertNotIn("private-payload", output.getvalue())
            subscribe.assert_not_called()

    def test_unknown_exception_still_has_a_redacted_runtime_error(self):
        with patch.object(app, "main", side_effect=RuntimeError("private-token-example")), \
             redirect_stderr(io.StringIO()) as output:
            self.assertEqual(app.entrypoint(), 1)
        self.assertEqual(json.loads(output.getvalue())["error_code"], "unexpected_error")
        self.assertNotIn("private-token-example", output.getvalue())

    def test_generated_cli_process_exit_codes_for_stream_states_and_interrupt(self):
        # Only transport, decoding and the clock are fake; parsing, reporting,
        # cleanup and conversion of the entrypoint result to an OS exit code run.
        program = '''
from contextlib import contextmanager
import signal
import sys
sys.modules["aorta"] = None
from health_monitor import main as app
scenario = sys.argv.pop(1)
clock, closed = [0.0], []
streams = iter(app.ROUTES)
@contextmanager
def subscription(_):
    def receive(timeout):
        clock[0] += 1
        if scenario == "interrupt":
            signal.raise_signal(signal.SIGINT)
        if scenario == "waiting":
            return None
        stream = next(streams, None)
        if stream is None:
            return None
        received_at = 0.0 if scenario == "stale" else clock[0]
        return stream, b"synthetic", received_at
    try:
        yield receive
    finally:
        closed.append(True)
def decode(stream, payload):
    return ({"soc_percent": 80} if stream == "battery" else {"heartbeat_seq": 1}), 1
app.subscription, app.decode = subscription, decode
app.time.monotonic = lambda: clock[0]
result = app.entrypoint()
assert closed == [True], "subscription not closed"
raise SystemExit(result)
'''
        for scenario, expected in (("fresh", 0), ("waiting", 1), ("stale", 1), ("interrupt", 130)):
            with self.subTest(scenario=scenario):
                result = subprocess.run([sys.executable, "-c", program, scenario, "--execute", "--duration", "4"],
                    cwd=self.project, env=dict(os.environ, PYTHONNOUSERSITE="1", PYTHONPATH="",
                                              ZENOH_SESSION_CONFIG_URI="/nonexistent-application-test"),
                    capture_output=True, text=True, timeout=10)
                self.assertEqual(result.returncode, expected, result.stderr)
                self.assertEqual(result.stderr, "")
                if scenario == "interrupt":
                    self.assertEqual(result.stdout, "")
                else:
                    final = json.loads(result.stdout.splitlines()[-1])
                    self.assertTrue(final["final"])
                    self.assertEqual(final["all_streams_receiving"], scenario == "fresh")
                    status = {"fresh": "receiving", "waiting": "waiting_data", "stale": "stale"}[scenario]
                    self.assertEqual({stream["status"] for stream in final["streams"].values()}, {status})

    def test_queued_samples_use_callback_time_not_consumption_time(self):
        clock = [0.0]
        streams = iter(runtime.ROUTES)
        @contextmanager
        def backlog(_):
            def receive(timeout):
                try:
                    stream = next(streams)
                except StopIteration:
                    clock[0] = 6.1
                    return None
                clock[0] = 5.0 if clock[0] == 0 else clock[0] + 0.01
                return stream, b"old-sample", 0.0
            yield receive
        def decode(stream, payload):
            return ({"soc_percent": 80} if stream == "battery" else {"heartbeat_seq": 1}), 1
        with patch.object(app, "subscription", side_effect=backlog), patch.object(app, "decode", side_effect=decode), \
             patch.object(app.time, "monotonic", side_effect=lambda: clock[0]), redirect_stdout(io.StringIO()) as output:
            self.assertEqual(app.main(["--execute", "--duration", "6"]), 1)
        result = json.loads(output.getvalue().splitlines()[-1])
        self.assertFalse(result["all_streams_receiving"])
        for stream in result["streams"].values():
            self.assertEqual(stream["status"], "stale")
            self.assertEqual(stream["age_seconds"], 6.1)


class CppWorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.project = self.root / "cpp-project"
        with redirect_stdout(io.StringIO()):
            create_app.create(self.project, "cpp-project", "cpp")

    def assert_independent_dependencies(self, reference_root):
        """Inspect dependency references, not prose or example SDK locations."""
        for path in self.project.rglob("*"):
            self.assertFalse(path.is_symlink(), path)
            if not path.is_file():
                continue
            text = path.read_text()
            if path.suffix in (".cc", ".h"):
                references = re.findall(r'^\s*#\s*include\s*[<"]([^>"]+)[>"]', text, re.MULTILINE)
            elif path.suffix in (".bazel", ".bzl"):
                references = [ast.literal_eval(token.string) for token in tokenize.generate_tokens(io.StringIO(text).readline)
                              if token.type == tokenize.STRING]
            elif path.name == ".bazelrc":
                references = [part.rsplit("=", 1)[-1] for part in shlex.split(text, comments=True)]
            else:
                continue
            for reference in references:
                self.assertFalse(reference == str(reference_root) or reference.startswith(str(reference_root) + "/"),
                                 f"reference-checkout dependency in {path.relative_to(self.project)}")
                self.assertFalse(reference.startswith(('recipes/', 'blueprints/health-monitor/',
                                                       '//recipes:', '//recipes/', '//blueprints/health-monitor:',
                                                       '//blueprints/health-monitor/')),
                                 f"reference-checkout dependency in {path.relative_to(self.project)}")

    def test_generated_cpp_workspace_is_complete_and_independent(self):
        for name in ("MODULE.bazel", "MODULE.bazel.lock", "BUILD.bazel", ".bazelrc", ".bazelversion",
                     "APP.json", "config.json", "README.md", "README.zh-CN.md", "AGENTS.md", "AGENTS.zh-CN.md",
                     "CLAUDE.md", "LICENSE", "NOTICE", "test_cli.py", "health_monitor/main.cc",
                     "health_monitor/model.h", "health_monitor/decoder.h", "health_monitor/model_test.cc",
                     "health_monitor/sdk_test.cc", "support/cpp_common.h", "support/observe.h",
                     "sdk/BUILD.bazel", "sdk/repositories.bzl", "toolchains/BUILD.bazel", "toolchains/aarch64_gcc.bzl"):
            self.assertTrue((self.project / name).is_file(), name)
        self.assert_independent_dependencies(ROOT)
        self.assertFalse((self.project / "requirements.txt").exists())
        self.assertEqual((self.project / "CLAUDE.md").read_text(), "@AGENTS.md\n")
        compile((self.project / "test_cli.py").read_text(), "test_cli.py", "exec")

    def test_default_workspace_mount_does_not_reject_documentation_examples(self):
        self.assertIn('/workspace/sdk/', (self.project / 'README.md').read_text())
        path = self.project / 'BUILD.bazel'
        path.write_text(path.read_text() + '\n# Example reference path: "/workspace/sdk/example"\n')
        self.assert_independent_dependencies(Path('/workspace'))

    def test_reference_checkout_source_and_build_dependencies_are_rejected(self):
        cases = (("health_monitor/main.cc", '#include "/workspace/recipes/cpp_common.h"\n'),
                 ("health_monitor/main.cc", '#include "recipes/cpp_common.h"\n'),
                 ("BUILD.bazel", 'load("/workspace/toolchains/compiler.bzl", "compiler")\n'),
                 ("BUILD.bazel", 'cc_library(name="bad", deps=["//recipes:cpp_common"])\n'),
                 ("MODULE.bazel", 'local_repository(name="reference", path="/workspace")\n'),
                 (".bazelrc", 'common --override_repository=reference=/workspace\n'))
        for name, dependency in cases:
            path = self.project / name
            original = path.read_text()
            try:
                path.write_text(original + '\n' + dependency)
                with self.subTest(name=name, dependency=dependency), self.assertRaises(AssertionError):
                    self.assert_independent_dependencies(Path('/workspace'))
            finally:
                path.write_text(original)

    def test_cpp_metadata_records_pairing_and_target(self):
        manifest = json.loads((self.project / "APP.json").read_text())
        release = create_app.configuration()
        self.assertEqual(manifest["language"], "cpp")
        self.assertEqual(manifest["sdk_release"], release["sdk"]["release_tag"])
        self.assertEqual(manifest["cpp_abi"], release["sdk"]["cpp"]["abi"])
        self.assertEqual(manifest["schema_pack"], release["schema"]["pack_version"])
        self.assertEqual(manifest["build_target"], "//:main")
        self.assertEqual(manifest["runtime_files"], ["config.json"])
        self.assertIn('name = "cpp_project"', (self.project / "MODULE.bazel").read_text())
        self.assertIn("//toolchains:linux_arm64", (self.project / ".bazelrc").read_text())

    def test_sources_and_toolchain_come_from_current_blueprint(self):
        self.assertEqual((self.project / "health_monitor/model.h").read_bytes(),
                         (ROOT / "blueprints/health-monitor/cpp/model.h").read_bytes())
        self.assertEqual((self.project / "toolchains/aarch64_gcc.bzl").read_bytes(),
                         (ROOT / "toolchains/aarch64_gcc.bzl").read_bytes())
        self.assertIn('#include "support/observe.h"', (self.project / "health_monitor/main.cc").read_text())
        self.assertIn('#include "health_monitor/model.h"', (self.project / "health_monitor/decoder.h").read_text())

    def test_unsupported_language_and_cli_do_not_create_output(self):
        output = self.root / "rejected"
        with self.assertRaisesRegex(ValueError, "language"):
            create_app.create(output, "rejected", "rust")
        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            create_app.main(["--output", str(output), "--name", "rejected", "--language", "rust"])
        self.assertFalse(output.exists())

    def test_cpp_generation_never_overwrites_or_runs_on_host(self):
        before = (self.project / "APP.json").read_bytes()
        with self.assertRaises(ValueError):
            create_app.create(self.project, "cpp-project", "cpp")
        self.assertEqual(before, (self.project / "APP.json").read_bytes())
        output = self.root / "host-rejected"
        with patch.object(create_app, "require_dev_container", side_effect=RuntimeError("host")), self.assertRaises(RuntimeError):
            create_app.create(output, "host-rejected", "cpp")
        self.assertFalse(output.exists())

    def test_python_packager_gives_cpp_specific_guidance(self):
        with self.assertRaisesRegex(ValueError, "Python only"):
            package_app.read_manifest(self.project, create_app.configuration())


class ApplicationNameTests(unittest.TestCase):
    def test_invalid_names_are_rejected_before_either_language_writes(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "rejected"
            for language in ("python", "cpp"):
                for name in ("", "demo-", "a--", "-demo", "1demo", "Demo", "demo_app", "a" * 49):
                    with self.subTest(language=language, name=name), self.assertRaises(ValueError):
                        create_app.create(output, name, language)
                    self.assertFalse(output.exists())

    def test_valid_name_boundaries_generate_valid_module_names(self):
        with tempfile.TemporaryDirectory() as directory:
            for language in ("python", "cpp"):
                for index, name in enumerate(("a", "a0", "my-app", "a" + "-" * 46 + "0")):
                    output = Path(directory) / f"{language}-{index}"
                    with self.subTest(language=language, name=name), redirect_stdout(io.StringIO()):
                        create_app.create(output, name, language)
                    self.assertIn(f'name = "{name.replace("-", "_")}"', (output / "MODULE.bazel").read_text())
                    manifest = json.loads((output / "APP.json").read_text())
                    if language == "python":
                        package_app.validate_manifest(manifest, create_app.configuration())
                        for invalid in ("demo-", "a--", "a" * 49):
                            with self.subTest(name=invalid), self.assertRaises(ValueError):
                                package_app.validate_manifest(dict(manifest, name=invalid), create_app.configuration())


class GeneratedIgnoreTests(unittest.TestCase):
    def test_both_languages_use_shared_safety_patterns_with_real_git(self):
        ignored = (".env", ".env.local", ".env.production", "settings/.env.production",
                   "device_dictionary.txt", "settings/auth_dictionary.txt", "edu_session.json5",
                   "settings/edu_session-robot.json5", "settings.json5.local", "client.key", "client.pem",
                   "id_rsa", "id_ed25519", "id_ecdsa", "artifacts/sdk.whl", "application.tar.gz")
        visible = (".env.example", "settings/.env.example", "APP.json", "config.json",
                   "README.md", "health_monitor/main.py", "health_monitor/main.cc")
        with tempfile.TemporaryDirectory() as temporary:
            for language in ("python", "cpp"):
                project = Path(temporary) / language
                with redirect_stdout(io.StringIO()):
                    create_app.create(project, "ignore-check", language)
                self.assertEqual((project / ".gitignore").read_bytes(), (ROOT / "templates/gitignore.template").read_bytes())
                subprocess.run(["git", "-C", str(project), "init", "--quiet"], check=True, capture_output=True, timeout=10)
                result = subprocess.run(["git", "-C", str(project), "-c", "core.excludesFile=/dev/null",
                                         "check-ignore", "--no-index", "--stdin"],
                                        input="\n".join((*ignored, *visible)) + "\n", capture_output=True,
                                        text=True, check=False, timeout=10)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(set(result.stdout.splitlines()), set(ignored), language)


class SubscriptionTests(unittest.TestCase):
    def test_sdk_missing_and_version_mismatch_are_distinct(self):
        for result, code in ((runtime.importlib.metadata.PackageNotFoundError("private-package"), "sdk_not_installed"),
                             ("0.0.0", "sdk_version_mismatch")):
            with self.subTest(code=code), patch.object(runtime.importlib.metadata, "version",
                     **({"side_effect": result} if isinstance(result, Exception) else {"return_value": result})), \
                 self.assertRaises(ApplicationError) as caught:
                runtime.load_sdk()
            self.assertEqual((caught.exception.stage, caught.exception.error_code), ("sdk", code))
            self.assertNotIn("private-package", json.dumps(caught.exception.summary()))

    def test_sdk_load_failure_is_not_a_configuration_error(self):
        with patch.object(runtime.importlib.metadata, "version", side_effect=lambda name: runtime.VERSIONS[name]), \
             patch.object(runtime, "validator", side_effect=ValueError("private-schema-path")), \
             self.assertRaises(ApplicationError) as caught:
            runtime.load_sdk()
        self.assertEqual((caught.exception.stage, caught.exception.error_code), ("sdk", "sdk_load_failed"))
        self.assertNotIn("private-schema-path", json.dumps(caught.exception.summary()))

    def fake_sdk(self, *, fail=False, flood=False, dropped=0):
        self.closed = []
        self.callbacks = []
        self.handles = []
        @contextmanager
        def subscriber(route, callback, **_):
            if fail and route == "/bms_state":
                raise RuntimeError("subscriber failed")
            self.callbacks.append(callback)
            for _ in range(65 if flood else 1):
                callback(b"sample", None)
            try:
                handle = SimpleNamespace(dropped_count=lambda: dropped)
                self.handles.append(handle)
                yield handle
            finally:
                self.closed.append(route)
        @contextmanager
        def node(_):
            try:
                yield SimpleNamespace(create_subscriber=subscriber)
            finally:
                self.closed.append("node")
        return SimpleNamespace(Node=node, SubscriberOptions=lambda **kw: kw)

    def test_bindings_copy_payload_and_close_all_resources(self):
        with patch.object(runtime, "check_device"), patch.object(runtime, "load_sdk", return_value=self.fake_sdk()):
            with runtime.subscription(runtime.ROUTES) as receive:
                values = [receive(0.01) for _ in range(3)]
        self.assertEqual({value[0] for value in values}, set(runtime.ROUTES))
        self.assertEqual(self.closed[-1], "node")
        self.assertEqual(len(self.closed), 4)

    def test_partial_subscription_failure_closes_existing_resources(self):
        with patch.object(runtime, "check_device"), patch.object(runtime, "load_sdk", return_value=self.fake_sdk(fail=True)), self.assertRaises(ApplicationError) as caught:
            with runtime.subscription(runtime.ROUTES):
                pass
        self.assertEqual(caught.exception.error_code, "subscription_setup_failed")
        self.assertEqual(self.closed, ["/locomotion/status", "node"])

    def test_overflow_is_not_silently_hidden(self):
        with patch.object(runtime, "check_device"), patch.object(runtime, "load_sdk", return_value=self.fake_sdk(flood=True)):
            with runtime.subscription(["state"]) as receive, self.assertRaises(RuntimeError):
                receive(0.01)
        self.assertEqual(self.closed[-1], "node")

    def test_callback_timestamp_and_payload_copy_survive_delayed_consumption(self):
        with patch.object(runtime, "check_device"), patch.object(runtime, "load_sdk", return_value=self.fake_sdk()), \
             patch.object(runtime.time, "monotonic", return_value=1.25):
            with runtime.subscription(["state"]) as receive:
                self.assertEqual(receive(0.01)[2], 1.25)
                payload = bytearray(b"fresh")
                self.callbacks[0](payload, None)
                payload[:] = b"other"
                with patch.object(runtime.time, "monotonic", return_value=9):
                    stream, data, received_at = receive(0.01)
        self.assertEqual((stream, data, received_at), ("state", b"fresh", 1.25))

    def test_sdk_drops_stop_even_when_application_queue_has_space(self):
        with patch.object(runtime, "check_device"), patch.object(runtime, "load_sdk", return_value=self.fake_sdk(dropped=7)):
            with runtime.subscription(["state"]) as receive, self.assertRaisesRegex(RuntimeError, "SDK reported"):
                receive(0.01)
        self.assertEqual(self.closed[-1], "node")

    def test_sdk_drops_during_dequeue_are_checked_before_delivery(self):
        with patch.object(runtime, "check_device"), patch.object(runtime, "load_sdk", return_value=self.fake_sdk()):
            with runtime.subscription(["state"]) as receive:
                reads = iter((0, 1))
                self.handles[0].dropped_count = lambda: next(reads)
                with self.assertRaisesRegex(RuntimeError, "SDK reported"):
                    receive(0.01)

    def test_sdk_drops_during_empty_wait_are_not_reported_as_no_data(self):
        with patch.object(runtime, "check_device"), patch.object(runtime, "load_sdk", return_value=self.fake_sdk()):
            with runtime.subscription(["state"]) as receive:
                receive(0.01)
                reads = iter((0, 1))
                self.handles[0].dropped_count = lambda: next(reads)
                with self.assertRaisesRegex(RuntimeError, "SDK reported"):
                    receive(0.001)


class DiagnosticTests(unittest.TestCase):
    def sample(self, sdk):
        with patch.dict(sys.modules, {"aorta": sdk}), \
             patch.object(diagnose, "device_checks", return_value=[{"check": "account", "status": "confirmed"}]):
            return diagnose.diagnose("sample", allow_device=True, timeout=0.001)

    def assert_progress(self, report, *, attempted=True, session=False, subscription=False, received=False):
        self.assertEqual(report["sampling"], {"attempted": attempted, "session_opened": session,
                                            "subscription_created": subscription, "sample_received": received})
        self.assertEqual(report["interfaces_contacted"], subscription)

    def test_sampling_worker_does_not_leak_native_stdout_or_stderr(self):
        report = {"format_version": 1, "level": "sample", "checks": [{"status": "sample_received"}]}
        raw = SimpleNamespace(returncode=0, stdout="SDK private endpoint\n" + json.dumps(report), stderr="SDK private context")
        with patch.object(diagnose.subprocess, "run", return_value=raw), redirect_stdout(io.StringIO()) as output:
            self.assertEqual(diagnose.main(["--level", "sample", "--allow-device-check"]), 0)
        self.assertEqual(json.loads(output.getvalue()), report)
        self.assertNotIn("private", output.getvalue())

    def test_cli_without_sampling_opt_in_never_launches_worker(self):
        with patch.object(diagnose, "isolated_sample", side_effect=AssertionError("worker")), redirect_stdout(io.StringIO()):
            self.assertEqual(diagnose.main(["--level", "sample"]), 1)

    def test_inventory_does_not_execute_subprocess_or_contact_device(self):
        with patch.object(diagnose.subprocess, "run", side_effect=AssertionError("process")), \
             patch.object(diagnose, "device_checks", side_effect=AssertionError("device")):
            report = diagnose.diagnose("inventory")
        self.assertFalse(report["interfaces_contacted"])
        self.assertEqual(report["sdk_runtime"], "not_verified")

    def test_device_checks_require_explicit_opt_in(self):
        with patch.object(diagnose, "device_checks", side_effect=AssertionError("device")), self.assertRaises(ValueError):
            diagnose.diagnose("device")

    def test_failed_device_preconditions_prevent_sdk_import(self):
        with patch.object(diagnose, "device_checks", return_value=[{"check": "account", "status": "mismatch"}]):
            report = diagnose.diagnose("sample", allow_device=True)
        self.assert_progress(report, attempted=False)

    def test_missing_sdk_never_claims_a_session_or_interface(self):
        report = self.sample(None)
        self.assert_progress(report)
        self.assertEqual(report["checks"][-1], {"check": "sdk_import", "status": "failed", "cause": "import_failed"})

    def test_node_constructor_and_enter_failures_preserve_stage(self):
        def fail(_):
            raise OSError("sensitive session details")
        @contextmanager
        def fail_enter(_):
            raise OSError("sensitive session details")
            yield
        for constructor in (fail, fail_enter):
            with self.subTest(constructor=constructor):
                report = self.sample(SimpleNamespace(Node=constructor))
                self.assert_progress(report)
                self.assertEqual(report["checks"][-1]["check"], "session_open")
                self.assertNotIn("sensitive", json.dumps(report))

    def test_subscription_failure_is_not_interface_contact_and_closes_node(self):
        closed = []
        @contextmanager
        def node(_):
            def subscriber(*args, **kwargs):
                raise RuntimeError("sensitive route details")
            try:
                yield SimpleNamespace(create_subscriber=subscriber)
            finally:
                closed.append("node")
        report = self.sample(SimpleNamespace(Node=node, SubscriberOptions=lambda **kwargs: kwargs))
        self.assert_progress(report, session=True)
        self.assertEqual(report["checks"][-1]["check"], "subscribe")
        self.assertEqual(closed, ["node"])
        self.assertNotIn("sensitive", json.dumps(report))

    def test_received_sample_and_cleanup_failure_remain_distinct(self):
        for fail_cleanup in (False, True):
            closed = []
            @contextmanager
            def node(_):
                @contextmanager
                def subscriber(route, callback, **kwargs):
                    callback(b"sample", None)
                    try:
                        yield
                    finally:
                        closed.append("subscriber")
                        if fail_cleanup:
                            raise RuntimeError("sensitive cleanup details")
                try:
                    yield SimpleNamespace(create_subscriber=subscriber)
                finally:
                    closed.append("node")
            with self.subTest(fail_cleanup=fail_cleanup):
                report = self.sample(SimpleNamespace(Node=node, SubscriberOptions=lambda **kwargs: kwargs))
                self.assert_progress(report, session=True, subscription=True, received=True)
                sample = next(item for item in report["checks"] if item["check"] == "selected_stream")
                self.assertEqual((sample["status"], sample["payload_bytes"], sample["decoded"]), ("sample_received", 6, False))
                self.assertEqual(closed, ["subscriber", "node"])
                self.assertEqual(any(item["status"] == "failed" for item in report["checks"]), fail_cleanup)
                if fail_cleanup:
                    self.assertEqual(report["checks"][-1]["check"], "cleanup")
                self.assertNotIn("sensitive", json.dumps(report))

    def test_timeout_is_not_reported_as_unsupported(self):
        @contextmanager
        def node(_):
            @contextmanager
            def subscriber(*args, **kwargs):
                yield
            yield SimpleNamespace(create_subscriber=subscriber)
        sdk = SimpleNamespace(Node=node, SubscriberOptions=lambda **kwargs: kwargs)
        with patch.dict(sys.modules, {"aorta": sdk}), \
             patch.object(diagnose, "device_checks", return_value=[{"check": "account", "status": "confirmed"}]):
            report = diagnose.diagnose("sample", allow_device=True, timeout=0.001)
        self.assertEqual(report["checks"][-1]["status"], "waiting_data_timeout")
        self.assertEqual(report["checks"][-1]["support"], "not_verified")
        self.assert_progress(report, session=True, subscription=True)

    def test_arbitrary_route_or_bad_timeout_is_rejected(self):
        for route, timeout in (("/locomotion/joy", 1), ("state", float("nan"))):
            with self.assertRaises(ValueError):
                diagnose.diagnose("sample", allow_device=True, route=route, timeout=timeout)


if __name__ == "__main__":
    require_dev_container()
    unittest.main()
