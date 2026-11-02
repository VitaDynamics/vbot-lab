"""Exercise documented Bash chains with fake tools; never build, install or connect."""

from contextlib import redirect_stdout
import importlib
import io
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))
from container_context import require_dev_container
from recipes import common


# Only these fakes are on PATH. A documentation change cannot fall back to real
# SSH, SDK installation, a compiler or a Recipe. cd is also intercepted below.
RECORDER = r'''
record_step() {
  local step=0 line arguments="${*:2}"
  while IFS= read -r line; do step=$((step + 1)); done < "$COMMAND_TRACE"
  arguments=${arguments//$'\n'/ }
  printf '%s\t%s\n' "$1" "$arguments" >> "$COMMAND_TRACE"
  if [[ "$FAIL_AT" = "$((step + 1))" ]]; then return 37; fi
}
'''
FAKE_TOOL = '#!/bin/bash\n' + RECORDER + r'''
name=${0##*/}
record_step "$name" "$@" || exit "$?"
case "$name" in
  ssh)
    if [[ "$*" = *"mktemp -d"* ]]; then
      printf '%s' "$MOCK_APP_DIR"
    elif [[ "$*" = *"id -un"* ]]; then
      # Execute only the documented read-only precheck against the fake PATH.
      # Directory creation, file transfer and interactive SSH remain simulated.
      /bin/bash --noprofile --norc -c "${!#}"
      exit "$?"
    fi ;;
  id) printf '%s\n' "$MOCK_ACCOUNT" ;;
  uname) printf '%s\n' "$MOCK_ARCHITECTURE" ;;
  python3)
    if [[ "$1" = -c && "$2" = *"sys.version_info"* ]]; then
      # Check the actual Python expression, substituting only the observed version.
      "$TEST_PYTHON" -c 'import sys; sys.version_info=tuple(map(int,sys.argv[1].split("."))); exec(sys.argv[2])' \
        "$MOCK_PYTHON_VERSION" "$2"
      exit "$?"
    elif [[ "$1" = --version ]]; then
      printf 'Python %s\n' "$MOCK_PYTHON_VERSION"
    fi ;;
  mktemp) printf '%s' "$MOCK_PACKAGE_DIR" ;;
  ldd) printf '%s\n' "$MOCK_LDD_OUTPUT" ;;
esac
exit 0
'''


def blocks(page):
    return re.findall(r"```bash\n(.*?)```", (ROOT / page).read_text(), re.S)


class DeploymentCommandTests(unittest.TestCase):
    def run_block(self, script, *, fail_at=0, remote_directory="/userdata/vbot/apps/mock-ABC123",
                  package_directory="/tmp/mock-package", ldd_output="libaorta_core.so.13 => ./lib/libaorta_core.so.13",
                  activation=True, probe="", account="vbot", architecture="aarch64", python_version="3.10.12"):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            binaries = root / "bin"
            binaries.mkdir()
            venv_bin = root / ".venv/bin"
            venv_bin.mkdir(parents=True)
            for name in ("python3", "python", "bazel", "sha256sum", "tar", "mkdir", "mktemp",
                         "cp", "file", "aarch64-linux-gnu-readelf", "ldd", "find", "ssh", "scp",
                         "uname", "pkg-config", "subscribe-state", "health-monitor", "git", "id"):
                path = binaries / name
                path.write_text(FAKE_TOOL)
                path.chmod(0o755)
            (venv_bin / "python").write_text(FAKE_TOOL)
            (venv_bin / "python").chmod(0o755)
            if activation:
                (venv_bin / "activate").write_text(":\n")
            trace = root / "trace"
            trace.touch()
            environment = dict(os.environ, PATH=str(binaries), COMMAND_TRACE=str(trace), FAIL_AT=str(fail_at),
                               MOCK_APP_DIR=remote_directory, MOCK_PACKAGE_DIR=package_directory,
                               MOCK_LDD_OUTPUT=ldd_output, PACKAGE_DIR="/tmp/mock-package",
                               AORTA_CPP_SDK_DIR="/mock-sdk", TEST_PYTHON=sys.executable, MOCK_ACCOUNT=account,
                               MOCK_ARCHITECTURE=architecture, MOCK_PYTHON_VERSION=python_version)
            for name in ("BASH_ENV", "ENV", "SHELLOPTS", "BASHOPTS"):
                environment.pop(name, None)
            for name in list(environment):
                if name.startswith("BASH_FUNC_"):
                    environment.pop(name)
            setup = RECORDER + '\ncd() { record_step cd "$@"; }\n'
            result = subprocess.run(["/bin/bash", "--noprofile", "--norc", "-c", setup + script + "\n" + probe],
                                    cwd=root, env=environment, capture_output=True, text=True, timeout=10)
            return result, trace.read_text().replace(str(root), "<fixture>").splitlines()

    def deployment_blocks(self):
        for suffix in (".md", ".zh-CN.md"):
            for page in ("docs/getting-started/README", "docs/development/python-deployment", "packages/aorta/cpp/README",
                         "packages/aorta/python/README", "docs/development/offline-build", "tools/README",
                         "templates/python-app/README", "templates/cpp-app/README", "blueprints/health-monitor/cpp/README"):
                for index, script in enumerate(blocks(page + suffix)):
                    if any(marker in script for marker in ("tools/fetch_sdk.py", "sha256sum", "scp -r",
                                                          "bazel build", ". .venv/bin/activate", "cd /workspace", "git clone",
                                                          "tools/prepare_bazel_offline.py", "tools/bazel_offline.py",
                                                          "tools/package_python.py --recipe")):
                        yield page + suffix, index, script

    def test_every_failed_step_stops_the_documented_chain(self):
        for page, index, script in self.deployment_blocks():
            success, baseline = self.run_block(script)
            with self.subTest(page=page, block=index, success=True):
                self.assertEqual(success.returncode, 0, success.stderr)
                self.assertTrue(baseline)
            for step in range(1, len(baseline) + 1):
                with self.subTest(page=page, block=index, failed_step=step):
                    result, trace = self.run_block(script, fail_at=step)
                    self.assertNotEqual(result.returncode, 0, result.stderr)
                    self.assertEqual(trace, baseline[:step], "a later command ran after a failure")

    def test_sdk_install_and_offline_bundle_preparation_are_in_the_failure_matrix(self):
        entries = list(self.deployment_blocks())
        for suffix in (".md", ".zh-CN.md"):
            for page, required in (("packages/aorta/python/README", "python3 -m venv"),
                                   ("docs/development/offline-build", "tools/prepare_bazel_offline.py"),
                                   ("tools/README", "tools/package_python.py --recipe")):
                self.assertTrue(any(name == page + suffix and required in script for name, _index, script in entries))

    def test_application_templates_and_cpp_blueprint_are_in_the_failure_matrix(self):
        entries = list(self.deployment_blocks())
        for suffix in (".md", ".zh-CN.md"):
            for page, required in (("templates/python-app/README", "application.tar.gz"),
                                   ("templates/cpp-app/README", "sha256sum"),
                                   ("blueprints/health-monitor/cpp/README", "sha256sum")):
                self.assertTrue(any(name == page + suffix and required in script for name, _index, script in entries))

    def test_python_deployment_passes_selected_arguments_to_real_offline_recipe_cli(self):
        cases = (
            ("subscribe-state", [], {"topic": "/locomotion/status"}),
            ("locomotion", ["--mode", "stand"], {"mode": "MANUAL"}),
            ("perception", ["--stream", "poses", "--count", "2"],
             {"route": "/perception/poses", "count": 2}),
            ("rcp-task", ["--duration-ms", "750"], {"duration_ms": 750}),
        )
        for suffix in (".md", ".zh-CN.md"):
            script = next(block for block in blocks("docs/development/python-deployment" + suffix)
                          if "tools/fetch_sdk.py" in block)
            self.assertIn('"${PREVIEW_ARGS[@]}"', script)
            self.assertIn("PREVIEW_ARGS=()", script)
            self.assertNotIn("--execute", script)
            for recipe, arguments, expected in cases:
                with self.subTest(language=suffix, recipe=recipe):
                    selected = script.replace("RECIPE=subscribe-state", "RECIPE=" + recipe).replace(
                        "PREVIEW_ARGS=()", "PREVIEW_ARGS=(" + shlex.join(arguments) + ")")
                    result, trace = self.run_block(selected)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    run_index = next(i for i, line in enumerate(trace) if line.startswith("bazel\trun "))
                    command = shlex.split(trace[run_index].split("\t", 1)[1])
                    self.assertEqual(command, ["run", f"//recipes/{recipe}:main", "--", *arguments])
                    self.assertTrue(any("tools/package_python.py --recipe " + recipe in line
                                        for line in trace[run_index + 1:]))
                    # Validate the shell-expanded arguments with the actual CLI, not a fake parser.
                    # These are offline previews only; any SDK/device fallback fails the test.
                    module = importlib.import_module("recipes." + recipe + ".main")
                    with patch.object(common, "require_device_environment", side_effect=AssertionError("device access")), \
                         patch.object(common, "load_sdk", side_effect=AssertionError("SDK load")), \
                         redirect_stdout(io.StringIO()) as output:
                        self.assertEqual(module.main(command[3:]), 0)
                    preview = json.loads(output.getvalue())
                    self.assertIs(preview["execute"], False)
                    for key, value in expected.items():
                        self.assertEqual(preview[key], value)

    def test_empty_remote_directory_never_transfers_or_opens_a_session(self):
        for page, index, script in self.deployment_blocks():
            if "APP_DIR=$(ssh" in script:
                with self.subTest(page=page, block=index):
                    result, trace = self.run_block(script, remote_directory="")
                    self.assertNotEqual(result.returncode, 0)
                    commands = [line.split("\t")[0] for line in trace]
                    self.assertEqual(commands.count("ssh"), 2)
                    self.assertEqual(commands[-1], "ssh")
                    self.assertNotIn("scp", commands)

    def test_wrong_account_or_architecture_stops_before_remote_writes(self):
        for page, index, script in self.deployment_blocks():
            if "APP_DIR=$(ssh" in script:
                for mismatch in ({"account": "root"}, {"account": "another-user"},
                                 {"architecture": "x86_64"}, {"architecture": "armv7l"}):
                    with self.subTest(page=page, block=index, mismatch=mismatch):
                        result, trace = self.run_block(script, **mismatch)
                        commands = [line.split("\t")[0] for line in trace]
                        self.assertNotEqual(result.returncode, 0)
                        self.assertEqual(commands.count("ssh"), 1)
                        self.assertNotIn("scp", commands)
                        self.assertFalse(any("mktemp -d" in line for line in trace))

    def test_python_deployments_check_minimum_version_before_remote_writes(self):
        for page, index, script in self.deployment_blocks():
            if "APP_DIR=$(ssh" in script and "sys.version_info" in script:
                for version, allowed in (("2.7.18", False), ("3.9.99", False), ("3.10.0", True),
                                         ("3.10.12", True), ("3.12.7", True)):
                    with self.subTest(page=page, block=index, version=version):
                        result, trace = self.run_block(script, python_version=version)
                        commands = [line.split("\t")[0] for line in trace]
                        self.assertEqual(result.returncode == 0, allowed, result.stderr)
                        self.assertEqual("scp" in commands, allowed)
                        if not allowed:
                            self.assertEqual(commands.count("ssh"), 1)

    def test_cpp_deployment_has_no_python_requirement(self):
        for suffix in (".md", ".zh-CN.md"):
            script = next(block for block in blocks("packages/aorta/cpp/README" + suffix) if "APP_DIR=$(ssh" in block)
            result, trace = self.run_block(script, python_version="2.7.18")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse(any(line.startswith("python") for line in trace))

    def test_empty_cpp_package_directory_never_copies_files(self):
        for suffix in (".md", ".zh-CN.md"):
            script = next(block for block in blocks("packages/aorta/cpp/README" + suffix) if "PACKAGE_DIR=$(mktemp" in block)
            result, trace = self.run_block(script, package_directory="")
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual([line.split("\t")[0] for line in trace], ["bazel", "mktemp"])

    def test_missing_libraries_prevent_cpp_program_execution_even_when_ldd_returns_zero(self):
        for suffix in (".md", ".zh-CN.md"):
            script = next(block for block in blocks("packages/aorta/cpp/README" + suffix) if "ldd ./bin/subscribe-state" in block)
            result, trace = self.run_block(script, ldd_output="libaorta_core.so.13 => not found")
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(trace[-1].split("\t")[0], "ldd")
            self.assertFalse(any(line.startswith("subscribe-state\t") for line in trace))

    def test_missing_venv_activation_does_not_fall_back_to_another_python(self):
        for suffix in (".md", ".zh-CN.md"):
            for page in ("docs/development/python-deployment", "packages/aorta/python/README"):
                with self.subTest(page=page, language=suffix):
                    script = next(block for block in blocks(page + suffix) if ". .venv/bin/activate" in block)
                    result, trace = self.run_block(script, activation=False)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertFalse(any(line.startswith("python\t") for line in trace))

    def test_failure_does_not_exit_the_interactive_shell(self):
        script = next(block for block in blocks("docs/getting-started/README.md") if "tar -xzf python-recipe.tar.gz" in block)
        result, trace = self.run_block(script, fail_at=2, probe='printf "SHELL_STILL_OPEN\\n"')
        self.assertEqual(result.returncode, 0)
        self.assertIn("SHELL_STILL_OPEN", result.stdout)
        self.assertEqual([line.split("\t")[0] for line in trace], ["cd", "sha256sum"])

    def test_cpp_package_variable_remains_available_in_the_same_shell(self):
        script = next(block for block in blocks("packages/aorta/cpp/README.md") if "PACKAGE_DIR=$(mktemp" in block)
        result, _trace = self.run_block(script, probe='printf "PACKAGE=%s\\n" "$PACKAGE_DIR"')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("PACKAGE=/tmp/mock-package", result.stdout)


if __name__ == "__main__":
    require_dev_container()
    unittest.main()
