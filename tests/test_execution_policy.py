"""Read-only policy checks and mocked guards; never run a Recipe, Bazel or Docker."""

from contextlib import redirect_stdout, redirect_stderr
from copy import deepcopy
import ast
import io
import json
from pathlib import Path
import re
import struct
import subprocess
from types import SimpleNamespace
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import bazel_offline
import check_environment
import container_context
import in_container
import prepare_bazel_offline
import run_checks
import vbot_catalog
import cpp_artifacts
import sdk_ci


class BazelPreparationTests(unittest.TestCase):
    config = {"development": {"bazel_version": "7.6.1"}}

    def test_first_download_has_a_separate_budget_from_the_compiler_probe(self):
        def run(command, **options):
            if command[0] == "bazel":
                # Model the reported 24.7-second first download, without sleeping or networking.
                if options["timeout"] < 24.7:
                    raise subprocess.TimeoutExpired(command, options["timeout"])
                return SimpleNamespace(stdout="bazel 7.6.1\n")
            self.assertEqual(options["timeout"], 20)
            return SimpleNamespace(stdout="x86_64-linux-gnu\n")
        with patch.object(sdk_ci.subprocess, "run", side_effect=run) as execute:
            sdk_ci.check_toolchain(self.config, "linux_x86_64", {})
        self.assertEqual(execute.call_args_list[0].kwargs["timeout"], 180)
        self.assertEqual(execute.call_count, 2)

    def test_custom_bazel_budget_does_not_change_compiler_timeout(self):
        with patch.object(sdk_ci.subprocess, "run", side_effect=[SimpleNamespace(stdout="bazel 7.6.1"),
                         SimpleNamespace(stdout="x86_64-linux-gnu")]) as execute:
            sdk_ci.check_toolchain(self.config, "linux_x86_64", {}, bazel_prepare_timeout=300)
        self.assertEqual([call.kwargs["timeout"] for call in execute.call_args_list], [300, 20])

    def test_download_failures_retain_a_safe_reason_not_raw_output(self):
        for detail, reason in (("x509 certificate error", "tls"), ("no such host", "dns"),
                               ("proxy authentication failed", "proxy"), ("403 Forbidden", "http"),
                               ("checksum mismatch", "integrity"), ("connection refused", "network"),
                               ("unexpected failure", "tool_failed")):
            failure = subprocess.CalledProcessError(1, ["bazel", "--version"], stderr=detail + " private-token-example")
            with self.subTest(reason=reason), patch.object(sdk_ci.subprocess, "run", side_effect=failure), \
                 self.assertRaises(sdk_ci.BazelPreparationError) as caught:
                sdk_ci.prepare_bazel({}, 180)
            self.assertEqual(caught.exception.report["reason"], reason)
            self.assertEqual(caught.exception.report["exit_code"], 1)
            self.assertNotIn("private-token-example", json.dumps(caught.exception.report))

    def test_timeout_and_missing_tool_are_distinct(self):
        for failure, code in ((subprocess.TimeoutExpired(["bazel"], 180, stderr="private-example"), "bazel_prepare_timeout"),
                              (FileNotFoundError("private-example"), "bazel_not_found")):
            with self.subTest(code=code), patch.object(sdk_ci.subprocess, "run", side_effect=failure), \
                 self.assertRaises(sdk_ci.BazelPreparationError) as caught:
                sdk_ci.prepare_bazel({}, 180)
            self.assertEqual(caught.exception.report["error_code"], code)
            self.assertEqual(caught.exception.report["stage"], "bazel_prepare")
            self.assertNotIn("private-example", json.dumps(caught.exception.report))

    def test_cli_reports_tool_preparation_stage_without_traceback(self):
        error = sdk_ci.BazelPreparationError("bazel_prepare_timeout", "timeout", timeout=180)
        with patch.object(sdk_ci, "require_dev_container"), patch.object(sdk_ci, "configuration", return_value={}), \
             patch.object(sdk_ci, "check", side_effect=error), redirect_stderr(io.StringIO()) as output:
            self.assertEqual(sdk_ci.main(["--assets-dir", "unused", "--work-dir", "unused"]), 1)
        self.assertEqual(json.loads(output.getvalue()), error.report)

    def test_cli_rejects_unbounded_preparation_time_before_execution(self):
        for timeout in ("0", "29", "601", "invalid"):
            with self.subTest(timeout=timeout), patch.object(sdk_ci, "check") as check, \
                 redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as caught:
                sdk_ci.main(["--assets-dir", "unused", "--work-dir", "unused", "--bazel-prepare-timeout", timeout])
            self.assertEqual(caught.exception.code, 2)
            check.assert_not_called()


class Arm64CompilationModeTests(unittest.TestCase):
    @staticmethod
    def actions(flags, compiler="/usr/bin/aarch64-linux-gnu-gcc"):
        return SimpleNamespace(stdout=json.dumps({"actions": [
            {"arguments": [compiler, "-fPIC", *flags, "-c", "example.cc"]},
        ]}))

    def test_checks_actual_actions_for_all_modes_without_executing_them(self):
        outputs = [self.actions(["-O0"]), self.actions(["-O2", "-DNDEBUG"]), self.actions(["-O0", "-g"])]
        with patch.object(sdk_ci.subprocess, "run", side_effect=outputs) as run:
            result = sdk_ci.check_arm64_compilation_modes(["bazel", "--batch"], ["--platforms=//toolchains:linux_arm64"], {})
        self.assertEqual(result, {"fastbuild": ["-O0"], "opt": ["-DNDEBUG", "-O2"], "dbg": ["-O0", "-g"]})
        for call, mode in zip(run.call_args_list, ("fastbuild", "opt", "dbg")):
            command = call.args[0]
            self.assertEqual(command[:3], ["bazel", "--batch", "aquery"])
            self.assertIn("--platforms=//toolchains:linux_arm64", command)
            self.assertEqual(command[command.index("-c") + 1], mode)

    def test_missing_conflicting_flags_or_host_compiler_are_rejected(self):
        for output in (self.actions([]), self.actions(["-O0", "-O2"]), self.actions(["-O0"], "/usr/bin/gcc"),
                       SimpleNamespace(stdout='{"actions": []}')):
            with self.subTest(output=output.stdout), patch.object(sdk_ci.subprocess, "run", return_value=output), \
                 self.assertRaisesRegex(ValueError, "ARM64 fastbuild"):
                sdk_ci.check_arm64_compilation_modes(["bazel"], [], {})

    def test_opt_and_dbg_do_not_accept_fastbuild_flags(self):
        for outputs, mode in (([self.actions(["-O0"]), self.actions(["-O0"])], "opt"),
                              ([self.actions(["-O0"]), self.actions(["-O2", "-DNDEBUG"]), self.actions(["-O0"])], "dbg")):
            with self.subTest(mode=mode), patch.object(sdk_ci.subprocess, "run", side_effect=outputs), \
                 self.assertRaisesRegex(ValueError, "ARM64 " + mode):
                sdk_ci.check_arm64_compilation_modes(["bazel"], [], {})


class Arm64ArtifactTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)
        self.binary = self.directory / "example"
        header = bytearray(64)
        header[:6] = b"\x7fELF\x02\x01"
        struct.pack_into("<H", header, 18, 183)
        self.binary.write_bytes(header)

    def inspect(self, dynamic="", interpreter="/lib/ld-linux-aarch64.so.1", versions=""):
        outputs = [dynamic, "[Requesting program interpreter: " + interpreter + "]", versions]
        with patch.object(cpp_artifacts, "_read", side_effect=outputs):
            return cpp_artifacts.inspect_arm64([self.binary], self.directory)

    def test_arm64_elf_is_read_without_executing_it(self):
        result = self.inspect()
        self.assertEqual(result[0]["machine"], "aarch64")
        self.assertTrue(result[0]["executable"])

    def test_host_elf_and_truncated_input_are_rejected_before_tool_calls(self):
        header = bytearray(self.binary.read_bytes())
        struct.pack_into("<H", header, 18, 62)
        for data in (b"partial", header):
            self.binary.write_bytes(data)
            with patch.object(cpp_artifacts, "_read") as read, self.assertRaisesRegex(ValueError, "ARM64 ELF"):
                cpp_artifacts.inspect_arm64([self.binary], self.directory)
            read.assert_not_called()

    def test_wrong_interpreter_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "interpreter"):
            self.inspect(interpreter="/lib64/ld-linux-x86-64.so.2")

    def test_newer_glibc_requirement_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "GLIBC requirement"):
            self.inspect(versions="Version needs section: Name: GLIBC_2.36")

    def test_unresolved_dependency_is_not_silently_accepted(self):
        with patch.object(cpp_artifacts, "_read", side_effect=["(NEEDED) [libmissing.so]",
                         "[Requesting program interpreter: /lib/ld-linux-aarch64.so.1]", "", "libmissing.so\n"]), \
             self.assertRaisesRegex(ValueError, "unresolved ARM64"):
            cpp_artifacts.inspect_arm64([self.binary], self.directory)


class ContainerContextTests(unittest.TestCase):
    def inspect(self, env=None, marker=False, system="Linux"):
        return container_context.inspect_context(environ={} if env is None else env,
                                                 is_file=lambda _name: marker, system=system)

    def test_host_is_not_eligible(self):
        self.assertEqual(self.inspect()["context_status"], "attention_required")

    def test_ci_flag_or_declared_profile_alone_is_not_a_container(self):
        for env in ({"CI": "true"}, {"VBOT_DEV_CONTAINER": "1"}, {"PROFILE": "container"}):
            with self.subTest(env=env):
                self.assertEqual(self.inspect(env)["context_status"], "attention_required")

    def test_arbitrary_container_alone_is_not_a_development_context(self):
        self.assertEqual(self.inspect(marker=True)["context_status"], "attention_required")

    def test_both_context_signals_are_required(self):
        result = self.inspect({"VBOT_DEV_CONTAINER": "1"}, marker=True)
        self.assertEqual(result["context_status"], "eligible")
        self.assertIn("image_identity", result["not_checked"])
        self.assertIn("workspace_mount", result["not_checked"])
        self.assertFalse(result["changes_made"])

    def test_non_linux_is_not_the_development_environment(self):
        self.assertEqual(self.inspect({"VBOT_DEV_CONTAINER": "1"}, True, "Darwin")["context_status"],
                         "attention_required")

    def test_context_output_does_not_dump_environment(self):
        result = self.inspect({"VBOT_DEV_CONTAINER": "1", "PRIVATE_VALUE": "never-report-this"}, True)
        self.assertNotIn("never-report-this", json.dumps(result))

    def test_guard_rejects_ineligible_context(self):
        with patch.object(container_context, "inspect_context", return_value=self.inspect()):
            with self.assertRaisesRegex(RuntimeError, "development container"):
                container_context.require_dev_container()

    def test_guard_accepts_declared_container_without_launching_tools(self):
        with patch.object(container_context, "inspect_context",
                          return_value=self.inspect({"VBOT_DEV_CONTAINER": "1"}, True)):
            container_context.require_dev_container()


class CommandGuardTests(unittest.TestCase):
    def test_wrapper_denies_before_subprocess(self):
        with patch.object(in_container, "require_dev_container", side_effect=RuntimeError("container required")), \
             patch.object(in_container.subprocess, "run") as execute, redirect_stderr(io.StringIO()):
            self.assertEqual(in_container.main(["--", "bazel", "build", "//recipes/..."]), 1)
            execute.assert_not_called()

    def test_wrapper_keeps_arguments_and_exit_status(self):
        command = ["python3", "-m", "recipes.subscribe-state.main", "--output", "path with spaces"]
        with patch.object(in_container, "require_dev_container"), \
             patch.object(in_container.subprocess, "run", return_value=SimpleNamespace(returncode=7)) as execute:
            self.assertEqual(in_container.main(["--", *command]), 7)
            execute.assert_called_once_with(command, check=False)

    def test_wrapper_requires_an_explicit_command(self):
        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
            in_container.main([])
        self.assertEqual(error.exception.code, 2)

    def test_prepare_bundle_denies_before_tool_or_output_creation(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "unused"
            with patch.object(sys, "argv", ["prepare", "--output", str(output)]), \
                 patch.object(prepare_bazel_offline, "require_dev_container", side_effect=RuntimeError("container required")), \
                 patch.object(prepare_bazel_offline.subprocess, "check_output") as execute:
                with self.assertRaises(RuntimeError):
                    prepare_bazel_offline.main()
                execute.assert_not_called()
                self.assertFalse(output.exists())

    def test_offline_bazel_denies_before_tool_or_cache_creation(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "unused"
            with patch.object(sys, "argv", ["offline", "--output-user-root", str(output), "build", "//recipes/..."]), \
                 patch.object(bazel_offline, "verify"), \
                 patch.object(bazel_offline, "require_dev_container", side_effect=RuntimeError("container required")), \
                 patch.object(bazel_offline.subprocess, "check_output") as execute:
                with self.assertRaises(RuntimeError):
                    bazel_offline.main()
                execute.assert_not_called()
                self.assertFalse(output.exists())


class CheckGroupTests(unittest.TestCase):
    def test_recipe_suites_are_not_host_checks(self):
        groups = run_checks.load_groups(ROOT)
        for file in ("tests/test_recipes.py", "tests/test_family_recipes.py"):
            self.assertIn(file, groups["recipes"]["checks"])
            self.assertNotIn(file, groups["repository"]["checks"])

    def test_sdk_execution_suites_are_not_host_checks(self):
        checks = run_checks.load_groups(ROOT)["repository"]["checks"]
        for file in ("tests/test_recipe_sdk.py", "tests/test_cpp_recipes.py"):
            self.assertNotIn(file, checks)

    def test_deployment_command_execution_is_in_the_container_packaging_group(self):
        groups = run_checks.load_groups(ROOT)
        self.assertIn("tests/test_deployment_commands.py", groups["packaging"]["checks"])
        self.assertNotIn("tests/test_deployment_commands.py", groups["repository"]["checks"])

    def test_list_is_read_only_even_for_container_checks(self):
        with patch.object(run_checks, "require_dev_container") as guard, \
             patch.object(run_checks.subprocess, "run") as execute, redirect_stdout(io.StringIO()) as output:
            self.assertEqual(run_checks.main(["--scope", "recipes", "--list"]), 0)
            self.assertEqual(json.loads(output.getvalue())["execution_location"], "development_container")
            guard.assert_not_called()
            execute.assert_not_called()

    def test_recipe_group_denies_host_before_any_test(self):
        with patch.object(run_checks, "require_dev_container", side_effect=RuntimeError("container required")), \
             patch.object(run_checks.subprocess, "run") as execute, redirect_stderr(io.StringIO()):
            self.assertEqual(run_checks.main(["--scope", "recipes"]), 1)
            execute.assert_not_called()

    def test_repository_group_needs_no_container_or_bazel(self):
        with patch.object(run_checks, "require_dev_container") as guard, \
             patch.object(run_checks.subprocess, "run", return_value=SimpleNamespace(returncode=0)) as execute, \
             redirect_stdout(io.StringIO()):
            self.assertEqual(run_checks.main(["--scope", "repository"]), 0)
            guard.assert_not_called()
            expected = run_checks.load_groups(ROOT)["repository"]["checks"]
            self.assertEqual(len(expected), execute.call_count)
            for call, file in zip(execute.call_args_list, expected):
                self.assertEqual(call.args[0], [sys.executable, str(ROOT / file)])

    def test_failure_is_not_reported_as_success(self):
        with patch.object(run_checks.subprocess, "run", return_value=SimpleNamespace(returncode=1)), \
             redirect_stdout(io.StringIO()):
            self.assertEqual(run_checks.main(["--scope", "repository"]), 1)

    def test_group_metadata_rejects_unsafe_paths_and_locations(self):
        original = json.loads((ROOT / "catalog/checks.json").read_text())
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "catalog").mkdir()
            (root / "tests").mkdir()
            for group in original["groups"].values():
                for file in group["checks"]:
                    (root / file).touch()
            for value in ("../outside.py", "/absolute.py", "recipes/subscribe-state/main.py"):
                candidate = deepcopy(original)
                candidate["groups"]["repository"]["checks"][0] = value
                (root / "catalog/checks.json").write_text(json.dumps(candidate))
                with self.subTest(path=value), self.assertRaises(ValueError):
                    run_checks.load_groups(root)
            candidate = deepcopy(original)
            candidate["groups"]["recipes"]["execution_location"] = "host_or_ci"
            (root / "catalog/checks.json").write_text(json.dumps(candidate))
            with self.assertRaises(ValueError):
                run_checks.load_groups(root)

    def test_ci_container_checks_feed_existing_required_gate(self):
        workflow = (ROOT / ".github/workflows/scaffold.yml").read_text()
        jobs = dict(re.findall(r"^  ([\w-]+):\n(.*?)(?=^  [\w-]+:\n|\Z)", workflow, re.M | re.S))
        self.assertIn("python3 tools/run_checks.py --scope repository", jobs["repository-checks"])
        self.assertNotIn("--scope recipes", jobs["repository-checks"])
        self.assertIn("docker compose -f docker/compose.yaml run --rm --no-deps -T dev", jobs["recipe-checks"])
        self.assertIn("python3 tools/run_checks.py --scope recipes", jobs["recipe-checks"])
        gate = jobs["repository-layout"]
        self.assertIn("needs: [repository-checks, recipe-checks, sdk-integration]", gate)
        self.assertIn("always()", gate)
        for job in ("repository-checks", "recipe-checks", "sdk-integration"):
            self.assertIn("needs." + job + ".result", gate)
        self.assertIn('test "$REPOSITORY_RESULT" = success', gate)
        self.assertIn('test "$RECIPE_RESULT" = success', gate)
        self.assertIn('test "$SDK_RESULT" = success', gate)
        self.assertIn("docker compose -f docker/compose.yaml run", jobs["sdk-integration"])
        self.assertIn("python3 tools/sdk_ci.py", jobs["sdk-integration"])


class StatusSemanticsTests(unittest.TestCase):
    def test_blueprint_runtime_versions_match_release_metadata(self):
        source = ROOT / "blueprints/health-monitor/health_monitor/runtime.py"
        assignments = [node.value for node in ast.parse(source.read_text()).body
                       if isinstance(node, ast.Assign) and any(isinstance(name, ast.Name) and name.id == "VERSIONS" for name in node.targets)]
        self.assertEqual(len(assignments), 1)
        release = json.loads((ROOT / "catalog/release.json").read_text())
        expected = {name.replace("_", "-"): value for name, value in release["sdk"]["python"]["wheels"].items() if name != "flatbuffers"}
        self.assertEqual(ast.literal_eval(assignments[0]), expected)

    def test_integration_is_not_local_sdk_readiness(self):
        catalog, robots = vbot_catalog.load_catalog(ROOT)
        for integration, expected in (("pending", "blocked_integration"), ("integrated", "not_verified")):
            candidate = deepcopy(catalog)
            candidate["sdk"]["integration"] = integration
            with patch.object(check_environment, "load_catalog", return_value=(candidate, robots)):
                result = check_environment.inspect_environment(ROOT, "host", which=lambda name: name)
                self.assertEqual(result["sdk_status"], expected)
                self.assertFalse(result["device_contacted"])

    def test_summary_comes_from_catalog_and_matches_source_inventory(self):
        summary = vbot_catalog.summarize_catalog(ROOT)
        catalog, _robots = vbot_catalog.load_catalog(ROOT)
        self.assertEqual(summary["sdk"], catalog["sdk"])
        for language, filename in (("python", "main.py"), ("cpp", "main.cc")):
            sources = sorted(str(path.relative_to(ROOT)) for path in (ROOT / "recipes").glob("*/" + filename))
            self.assertEqual(summary["recipe_sources"][language], sources)
            self.assertEqual(summary["recipe_counts"][language], len(sources))
            blueprints = sorted(str(path.relative_to(ROOT)) for path in (ROOT / "blueprints").rglob(filename))
            self.assertEqual(summary["blueprint_sources"][language], blueprints)
            self.assertEqual(summary["blueprint_counts"][language], len(blueprints))
            self.assertFalse(set(sources) & set(blueprints))
        self.assertEqual(summary["runtime_status"], "not_verified")
        self.assertFalse(summary["device_contacted"])

    def test_retired_status_claims_do_not_return(self):
        for suffix in (".md", ".zh-CN.md"):
            tools = (ROOT / ("tools/README" + suffix)).read_text()
            index = (ROOT / ("catalog/README" + suffix)).read_text()
            homepage = (ROOT / ("README" + suffix)).read_text()
            for retired in ("it remains `blocked_integration`", "始终为 `blocked_integration`"):
                self.assertNotIn(retired, tools)
            for retired in ("planned single-task implementations", "规划中的单项任务实现"):
                self.assertNotIn(retired, index)
            self.assertNotRegex(homepage, r"Seven tasks|七个任务|7 个任务")


class DocumentationPolicyTests(unittest.TestCase):
    def test_python_setup_checks_native_loading_not_only_imports(self):
        for suffix in (".md", ".zh-CN.md"):
            for page in ("packages/aorta/python/README", "docs/getting-started/README",
                         "docs/development/python-deployment", "docs/troubleshooting/README"):
                with self.subTest(page=page, language=suffix):
                    document = (ROOT / (page + suffix)).read_text()
                    blocks = re.findall(r"```bash\n(.*?)```", document, re.S)
                    check = next(block for block in blocks if "aorta.load_library()" in block)
                    self.assertIn("unset AORTA_CORE_FFI_LIB", check)
                    self.assertIn("core.aorta_abi_version()", check)
                    self.assertLess(check.index("unset AORTA_CORE_FFI_LIB"), check.index("aorta.load_library()"))

    def test_flatbuffers_license_description_matches_wheel_and_release(self):
        for suffix in (".md", ".zh-CN.md"):
            document = (ROOT / ("packages/aorta/python/README" + suffix)).read_text()
            self.assertIn(".dist-info/LICENSE", document)
            self.assertIn("flatbuffers-<ver>.LICENSE", document)
            self.assertNotIn("wheel has no license", document)
            self.assertNotIn("wheel 不含许可证", document)

    def test_first_success_path_builds_packages_then_runs_read_only(self):
        for suffix in (".md", ".zh-CN.md"):
            with self.subTest(language=suffix):
                document = (ROOT / ("docs/getting-started/README" + suffix)).read_text()
                commands = re.findall(r"```bash\n(.*?)```", document, re.S)
                preparation = next(block for block in commands if "tools/fetch_sdk.py" in block)
                self.assertIn("bazel build //recipes/subscribe-state:main", preparation)
                self.assertIn("bazel run //recipes/subscribe-state:main", preparation)
                self.assertIn("tools/package_python.py --recipe subscribe-state", preparation)
                self.assertIn("tools/package_python.py --verify", preparation)
                self.assertNotIn("pip install", preparation)
                device = next(block for block in commands if "-m venv" in block)
                self.assertIn("--no-index --find-links wheelhouse -r requirements.txt", device)
                self.assertIn(".venv/bin/python -m recipes.subscribe-state.main --execute --count 3 --timeout 10", device)
                self.assertIn("unset PYTHONPATH", device)
                self.assertLess(document.index('ssh "$ROBOT"'), document.index("export ZENOH_SESSION_CONFIG_URI="))
                self.assertNotRegex("\n".join(commands), r"--confirm-motion|--consent|init\.sh")

    def test_symptom_index_and_tool_commands_stay_discoverable(self):
        for suffix in (".md", ".zh-CN.md"):
            with self.subTest(language=suffix):
                document = (ROOT / ("docs/troubleshooting/README" + suffix)).read_text()
                for anchor in ("container", "sdk-import", "build", "package", "ssh", "no-data", "runtime"):
                    self.assertIn(f'<a id="{anchor}"></a>', document)
                for command in ("pip check", "tools/package_python.py --verify", "--count 1", "timeout 12s"):
                    self.assertIn(command, document)
                tools = (ROOT / ("tools/README" + suffix)).read_text()
                for tool in ("fetch_sdk.py", "package_python.py", "sdk_ci.py"):
                    self.assertIn(tool, tools)
                workflow = (ROOT / (".github/WORKFLOWS" + suffix)).read_text()
                self.assertIn("sdk-integration", workflow)
                self.assertNotIn("not yet included", workflow)
                self.assertNotIn("尚不包含依赖构建", workflow)

    def test_image_is_pinned_and_platform_limit_is_explicit(self):
        config = json.loads((ROOT / "catalog/release.json").read_text())
        image = config["development"]["image"]
        self.assertRegex(image["digest"], r"^sha256:[a-f0-9]{64}$")
        compose = (ROOT / "docker/compose.yaml").read_text()
        self.assertIn(image["reference"] + "@" + image["digest"], compose)
        self.assertIn("platform: linux/amd64", compose)
        for suffix in (".md", ".zh-CN.md"):
            guide = (ROOT / ("docker/README" + suffix)).read_text()
            self.assertIn(image["digest"], guide)
            self.assertIn("linux/amd64", guide)
            self.assertIn("ARM64", guide)

    def test_compiler_checks_distinguish_runtime_and_target_architectures(self):
        for suffix in (".md", ".zh-CN.md"):
            with self.subTest(language=suffix):
                guide = (ROOT / ("docker/README" + suffix)).read_text()
                scripts = re.findall(r"```bash\n(.*?)```", guide, re.S)
                check = next(block for block in scripts if "aarch64-linux-gnu-gcc -dumpmachine" in block)
                for command in ("uname -m", "g++ -dumpmachine", "aarch64-linux-gnu-gcc -dumpmachine",
                                "aarch64-linux-gnu-g++ -dumpmachine"):
                    self.assertIn(command, check.splitlines())
                self.assertNotRegex(check, r"docker (?:run|pull|build)|apt(?:-get)? install")
                for file in ("docker/README", "docs/compatibility", "docs/getting-started/README",
                             "packages/aorta/cpp/README", "skills/vbot-dev-setup/SKILL"):
                    document = (ROOT / (file + suffix)).read_text()
                    for retired in ("supplies no ARM64 cross-compilation toolchain",
                                    "no ARM64 C++ cross-toolchain is supplied",
                                    "does not provide an ARM64 C++ compiler",
                                    "native container architecture must be `aarch64`",
                                    "不含 ARM64 交叉工具链", "不提供 ARM64 C++ 交叉工具链",
                                    "未提供 ARM64 C++ 交叉工具链", "不提供 ARM64 交叉工具链",
                                    "不提供 ARM64 C++ 编译器", "原生容器架构必须为 `aarch64`"):
                        self.assertNotIn(retired, document)

    def test_arm64_build_entry_and_deployment_checks_match(self):
        module = (ROOT / "MODULE.bazel").read_text()
        self.assertIn('register_toolchains("//toolchains:linux_aarch64_gcc")', module)
        self.assertIn("//toolchains:repository_files", (ROOT / "BUILD.bazel").read_text())
        for suffix in (".md", ".zh-CN.md"):
            for page in ("docker/README", "docs/compatibility", "docs/getting-started/README",
                         "packages/aorta/cpp/README", "skills/vbot-dev-setup/SKILL"):
                document = (ROOT / (page + suffix)).read_text()
                self.assertIn("--config=arm64", document)
                self.assertNotIn("not yet provided and verified", document)
                self.assertNotIn("尚未提供并验证", document)
            guide = (ROOT / ("packages/aorta/cpp/README" + suffix)).read_text()
            build = next(block for block in re.findall(r"```bash\n(.*?)```", guide, re.S) if "PACKAGE_DIR=$(mktemp" in block)
            self.assertIn('bazel build --config=arm64 "//recipes/$RECIPE:main_cpp"', build)
            self.assertIn("aarch64-linux-gnu-readelf -d", build)
            self.assertNotRegex(build, r"\bldd\b|bazel run")

    def test_entry_points_link_to_the_same_execution_rule(self):
        references = {
            "AGENTS": "docs/development/README",
            "CONTRIBUTING": "docs/development/README",
            "README": "docs/development/README",
            "tools/README": "../docs/development/README",
            "tests/README": "../docs/development/README",
            "recipes/README": "../docs/development/README",
            "skills/README": "../docs/development/README",
            "skills/vbot-dev-setup/SKILL": "../../docs/development/README",
            "docs/agents/README": "../development/README",
            "docs/getting-started/README": "../development/README",
            "packages/aorta/python/README": "../../../docs/development/README",
            "packages/aorta/cpp/README": "../../../docs/development/README",
        }
        for suffix in (".md", ".zh-CN.md"):
            for file, reference in references.items():
                with self.subTest(file=file, language=suffix):
                    document = (ROOT / (file + suffix)).read_text()
                    self.assertIn(reference + suffix, re.findall(r"\]\(([^)]+)\)", document))

    def test_device_deployment_no_longer_runs_development_previews(self):
        for suffix in (".md", ".zh-CN.md"):
            document = (ROOT / ("packages/aorta/cpp/README" + suffix)).read_text()
            device_block = next(block for block in re.findall(r"```bash\n(.*?)```", document, re.S)
                                if "ldd ./bin/subscribe-state" in block)
            self.assertNotIn("./bin/subscribe-state", device_block.splitlines())
            self.assertIn("./bin/subscribe-state --execute --count 3 --timeout 10", device_block)
            python = (ROOT / ("docs/development/python-deployment" + suffix)).read_text()
            device_block = next(block for block in re.findall(r"```bash\n(.*?)```", python, re.S)
                                if "export ZENOH_SESSION_CONFIG_URI=" in block)
            self.assertNotIn("python -m recipes.subscribe-state.main", device_block.splitlines())
            self.assertIn("python -m recipes.subscribe-state.main --execute --count 3 --timeout 10", device_block)

    def test_container_entry_configuration_declares_context(self):
        compose = (ROOT / "docker/compose.yaml").read_text()
        editor = json.loads((ROOT / ".devcontainer/devcontainer.json").read_text())
        self.assertIn('VBOT_DEV_CONTAINER: "1"', compose)
        self.assertEqual(editor["remoteEnv"]["VBOT_DEV_CONTAINER"], "1")
        self.assertNotIn("privileged:", compose)
        self.assertNotIn("docker.sock", compose)


if __name__ == "__main__":
    unittest.main()
