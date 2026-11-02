"""Dependency-bundle checks; never execute Bazel or contact a device."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import sys
import io
from contextlib import redirect_stderr
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
SPEC = importlib.util.spec_from_file_location("offline", ROOT / "tools/bazel_offline.py")
offline = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(offline)


class OfflineBundleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.bundle = Path(self.temp.name).resolve()
        self.file = self.bundle / "vendor/VENDOR.bazel"
        self.file.parent.mkdir()
        self.file.write_text('ignore("@@platforms~host_platform~host_platform")\n')
        self.manifest = {"bazel": "7.6.1", "module_sha256": offline.digest(ROOT / "MODULE.bazel"),
                         "lock_sha256": offline.digest(ROOT / "MODULE.bazel.lock"),
                         "files": {"vendor/VENDOR.bazel": offline.digest(self.file)}}
        self.write_manifest()

    def write_manifest(self):
        (self.bundle / "manifest.json").write_text(json.dumps(self.manifest))

    def test_valid(self):
        offline.verify(self.bundle)

    def test_changed_file(self):
        self.file.write_text("changed")
        with self.assertRaises(ValueError):
            offline.verify(self.bundle)

    def test_unlisted_file(self):
        (self.file.parent / "unexpected.bzl").write_text("unexpected input")
        with self.assertRaisesRegex(ValueError, "inventory changed"):
            offline.verify(self.bundle)

    def test_wrong_checkout(self):
        self.manifest["lock_sha256"] = "0" * 64
        self.write_manifest()
        with self.assertRaises(ValueError):
            offline.verify(self.bundle)

    def test_escape(self):
        self.manifest["files"] = {"../outside": "0" * 64}
        self.write_manifest()
        with self.assertRaises(ValueError):
            offline.verify(self.bundle)

    def test_symlink(self):
        (self.file.parent / "link").symlink_to(self.file)
        self.manifest["files"]["vendor/link"] = offline.digest(self.file)
        self.write_manifest()
        with self.assertRaises(ValueError):
            offline.verify(self.bundle)

    def test_missing_bundle_never_starts_bazel(self):
        with patch("sys.argv", ["offline", "--bundle", str(self.bundle / "missing"),
                                "--output-user-root", str(self.bundle / "out"), "build", "//recipes/..."]):
            with patch.object(offline.subprocess, "check_output") as execute:
                with self.assertRaises(FileNotFoundError):
                    offline.main()
                execute.assert_not_called()

    def test_arm64_build_preserves_offline_restrictions(self):
        with patch("sys.argv", ["offline", "--bundle", str(self.bundle),
                                "--output-user-root", str(self.bundle / "out"),
                                "--target-platform", "arm64", "build", "//recipes/subscribe-state:main_cpp"]), \
             patch.object(offline, "require_dev_container"), \
             patch.object(offline.subprocess, "check_output", return_value="bazel 7.6.1\n"), \
             patch.object(offline.subprocess, "call", return_value=0) as execute:
            self.assertEqual(offline.main(), 0)
        command = execute.call_args.args[0]
        self.assertIn("--platforms=//toolchains:linux_arm64", command)
        self.assertIn("--incompatible_enable_cc_toolchain_resolution", command)
        rc = (ROOT / ".bazelrc").read_text()
        for option in ("--platforms=//toolchains:linux_arm64", "--incompatible_enable_cc_toolchain_resolution"):
            self.assertIn("build:arm64 " + option, rc)
        self.assertIn("--repository_disable_download", command)
        self.assertIn("--ignore_all_rc_files", command)

    def test_arm64_run_and_test_are_rejected_before_bazel(self):
        for command in ("run", "test"):
            with self.subTest(command=command), \
                 patch("sys.argv", ["offline", "--output-user-root", str(self.bundle / "out"),
                                    "--target-platform", "arm64", command, "//recipes/subscribe-state:main_cpp"]), \
                 patch.object(offline.subprocess, "call") as execute, redirect_stderr(io.StringIO()), \
                 self.assertRaises(SystemExit) as error:
                offline.main()
            self.assertEqual(error.exception.code, 2)
            execute.assert_not_called()

    def test_native_tests_forward_only_the_checked_container_declaration(self):
        with patch("sys.argv", ["offline", "--bundle", str(self.bundle),
                                "--output-user-root", str(self.bundle / "out"), "test",
                                "//tests:deployment_commands_test", "--test_output=errors"]), \
             patch.object(offline, "require_dev_container") as guard, \
             patch.object(offline.subprocess, "check_output", return_value="bazel 7.6.1\n"), \
             patch.object(offline.subprocess, "call", return_value=0) as execute:
            self.assertEqual(offline.main(), 0)
        guard.assert_called_once_with()
        command = execute.call_args.args[0]
        self.assertEqual([value for value in command if value.startswith("--test_env")],
                         ["--test_env=VBOT_DEV_CONTAINER"])
        for required in ("--ignore_all_rc_files", "--repository_disable_download", "--lockfile_mode=error",
                         "//tests:deployment_commands_test", "--test_output=errors"):
            self.assertIn(required, command)

    def test_native_tests_reject_the_host_before_tool_or_output_creation(self):
        output = self.bundle / "out"
        with patch("sys.argv", ["offline", "--bundle", str(self.bundle),
                                "--output-user-root", str(output), "test", "//tests:deployment_commands_test"]), \
             patch.object(offline, "require_dev_container", side_effect=RuntimeError("container required")), \
             patch.object(offline.subprocess, "check_output") as version, \
             patch.object(offline.subprocess, "call") as execute, self.assertRaisesRegex(RuntimeError, "container required"):
            offline.main()
        version.assert_not_called()
        execute.assert_not_called()
        self.assertFalse(output.exists())

    def test_build_and_run_do_not_receive_test_only_options(self):
        for action in ("build", "run"):
            with self.subTest(command=action), \
                 patch("sys.argv", ["offline", "--bundle", str(self.bundle),
                                    "--output-user-root", str(self.bundle / "out"), action,
                                    "//recipes/subscribe-state:main"]), \
                 patch.object(offline, "require_dev_container"), \
                 patch.object(offline.subprocess, "check_output", return_value="bazel 7.6.1\n"), \
                 patch.object(offline.subprocess, "call", return_value=0) as execute:
                self.assertEqual(offline.main(), 0)
                self.assertFalse(any(value.startswith("--test_env") for value in execute.call_args.args[0]))

    def test_arm64_target_cannot_be_overridden_by_extra_options(self):
        with patch("sys.argv", ["offline", "--bundle", str(self.bundle),
                                "--output-user-root", str(self.bundle / "out"), "--target-platform", "arm64",
                                "build", "--platforms=//other:target", "//recipes/subscribe-state:main_cpp"]), \
             patch.object(offline, "require_dev_container"), \
             patch.object(offline.subprocess, "check_output", return_value="bazel 7.6.1\n"), \
             patch.object(offline.subprocess, "call") as execute, redirect_stderr(io.StringIO()), \
             self.assertRaises(SystemExit):
            offline.main()
        execute.assert_not_called()


if __name__ == "__main__":
    unittest.main()
