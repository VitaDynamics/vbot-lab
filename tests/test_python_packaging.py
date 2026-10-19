"""Container-only packaging tests with synthetic wheels; no SDK or robot session."""

from contextlib import redirect_stdout, redirect_stderr
from copy import deepcopy
import hashlib
import io
import json
import os
from pathlib import Path
import socket
import sys
import tarfile
import tempfile
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import Mock, patch
from zipfile import ZipFile


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from container_context import require_dev_container
import fetch_sdk
import package_python as packaging
from sdk_assets import configuration, digest, wheel_names
import sdk_ci


class PackagingTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)
        self.assets = self.directory / "assets"
        self.assets.mkdir()
        self.config = deepcopy(configuration())
        self.make_assets()

    def make_assets(self, *, license=True, bad_name=False, dependency=""):
        versions = self.config["sdk"]["python"]["wheels"]
        for item in self.config["sdk"]["assets"]:
            (self.assets / item["name"]).write_bytes(item["name"].encode())
        for target in self.config["sdk"]["python"]["platforms"]:
            for name, filename in wheel_names(self.config, target).items():
                prefix = f"{name}-{versions[name]}.dist-info/"
                with ZipFile(self.assets / filename, "w") as archive:
                    archive.writestr(prefix + "METADATA", f"Name: {'wrong' if bad_name and name == 'aorta_sdk' else name}\n"
                                     f"Version: {versions[name]}\nLicense-Expression: Apache-2.0\n"
                                     + (f"Requires-Dist: {dependency}\n" if dependency and name == "aorta_sdk" else ""))
                    archive.writestr(prefix + "WHEEL", "Wheel-Version: 1.0\nTag: py3-none-"
                                     + (target if name == "aorta_sdk" else "any") + "\n")
                    if license:
                        archive.writestr(prefix + "licenses/LICENSE", "Apache License, Version 2.0\n")
        self.refresh_metadata()

    def refresh_metadata(self):
        for item in self.config["sdk"]["assets"]:
            item["sha256"] = digest(self.assets / item["name"])
        sdk = self.config["sdk"]
        manifest = {"release_tag": sdk["release_tag"],
                    "pairing": {"aorta": sdk["aorta_version"], "schema_pack": self.config["schema"]["version"],
                                "ros2_bridge": self.config["schema"]["ros2_bridge_version"],
                                "wheels": sdk["python"]["wheels"]},
                    "assets": [item for item in sdk["assets"] if item["name"] not in ("EDU_SDK_MANIFEST.json", "SHA256SUMS")]}
        (self.assets / "EDU_SDK_MANIFEST.json").write_text(json.dumps(manifest))
        (self.assets / "SHA256SUMS").write_text("synthetic checksum inventory\n")
        for item in sdk["assets"]:
            item["sha256"] = digest(self.assets / item["name"])

    def create(self, name="package", **kwargs):
        output = self.directory / name
        packaging.package(self.config, "subscribe-state", self.assets, output, **kwargs)
        return output

    def test_package_has_only_selected_sources_and_four_pinned_wheels(self):
        output = self.create()
        manifest = packaging.verify_package(self.config, output)
        self.assertEqual(manifest["intended_use"], "robot")
        self.assertEqual(manifest["robot_type"], "foot_quadruped")
        self.assertEqual(manifest["dependency_profile"], "base")
        self.assertEqual(len(manifest["wheels"]), 4)
        with tarfile.open(output / "python-recipe.tar.gz") as archive:
            self.assertEqual(set(archive.getnames()), set(packaging.source_names("subscribe-state")))
        self.assertTrue((output / "SHA256SUMS").is_file())

    def test_reproducible_outputs_do_not_contain_workstation_paths(self):
        first, second = self.create("one"), self.create("two")
        for name in ("python-recipe.tar.gz", "PACKAGE_MANIFEST.json", "SHA256SUMS"):
            self.assertEqual((first / name).read_bytes(), (second / name).read_bytes())
        self.assertNotIn(str(self.directory), (first / "PACKAGE_MANIFEST.json").read_text())

    def test_native_package_is_explicitly_a_local_preview(self):
        manifest = packaging.verify_package(self.config, self.create(target="linux_x86_64"))
        self.assertEqual(manifest["intended_use"], "local_preview")
        self.assertIsNone(manifest["robot_type"])

    def test_unknown_recipe_is_rejected_before_output(self):
        output = self.directory / "unused"
        with self.assertRaises(ValueError):
            packaging.package(self.config, "unknown", self.assets, output)
        self.assertFalse(output.exists())

    def test_missing_or_corrupt_wheel_is_rejected_before_output(self):
        filename = wheel_names(self.config, "linux_aarch64")["aorta_sdk"]
        path = self.assets / filename
        path.write_bytes(b"corrupt")
        output = self.directory / "unused"
        with self.assertRaisesRegex(ValueError, "checksum"):
            packaging.package(self.config, "subscribe-state", self.assets, output)
        self.assertFalse(output.exists())

    def test_wheel_metadata_is_checked_even_with_matching_hashes(self):
        self.make_assets(bad_name=True)
        with self.assertRaisesRegex(ValueError, "metadata"):
            self.create()

    def test_bundled_licenses_are_required(self):
        self.make_assets(license=False)
        with self.assertRaisesRegex(ValueError, "license"):
            self.create()

    def test_wrong_architecture_metadata_is_rejected(self):
        filename = wheel_names(self.config, "linux_aarch64")["aorta_sdk"]
        with ZipFile(self.assets / filename, "w") as archive:
            prefix = "aorta_sdk.dist-info/"
            archive.writestr(prefix + "METADATA", "Name: aorta_sdk\nVersion: "
                             + self.config["sdk"]["python"]["wheels"]["aorta_sdk"] + "\n")
            archive.writestr(prefix + "WHEEL", "Tag: py3-none-linux_x86_64\n")
            archive.writestr(prefix + "LICENSE", "Apache-2.0")
        self.refresh_metadata()
        with self.assertRaisesRegex(ValueError, "platform mismatch"):
            self.create()

    def test_mismatched_dependency_version_is_rejected(self):
        self.make_assets(dependency="flatbuffers==0.0.0")
        with self.assertRaisesRegex(ValueError, "dependency version mismatch"):
            self.create()

    def test_unresolved_dependencies_are_not_silently_omitted(self):
        self.make_assets(dependency="unprovided-library==1.0.0")
        with self.assertRaisesRegex(ValueError, "unresolved SDK dependency"):
            self.create()

    def test_symlink_asset_is_rejected(self):
        filename = wheel_names(self.config, "linux_aarch64")["aorta_sdk"]
        path = self.assets / filename
        original = self.directory / "original.whl"
        path.rename(original)
        path.symlink_to(original)
        with self.assertRaisesRegex(ValueError, "regular asset"):
            self.create()

    def test_existing_output_is_preserved(self):
        output = self.create()
        before = (output / "SHA256SUMS").read_bytes()
        with self.assertRaisesRegex(ValueError, "never overwritten"):
            self.create()
        self.assertEqual((output / "SHA256SUMS").read_bytes(), before)

    def test_tampered_package_is_rejected(self):
        output = self.create()
        wheel = next((output / "wheelhouse").glob("*.whl"))
        wheel.write_bytes(b"changed")
        with self.assertRaisesRegex(ValueError, "checksum"):
            packaging.verify_package(self.config, output)

    def test_unlisted_files_are_not_treated_as_part_of_a_valid_package(self):
        output = self.create()
        (output / "unexpected.txt").write_text("not a package input")
        with self.assertRaisesRegex(ValueError, "inventory"):
            packaging.verify_package(self.config, output)

    def test_unlisted_special_files_are_not_ignored(self):
        output = self.create()
        os.mkfifo(output / "unexpected.fifo")
        with self.assertRaisesRegex(ValueError, "inventory"):
            packaging.verify_package(self.config, output)

    def test_package_control_symlinks_are_rejected_before_reads(self):
        for name in ("PACKAGE_MANIFEST.json", "SHA256SUMS"):
            for destination in ("inside", "outside", "missing"):
                with self.subTest(control=name, destination=destination):
                    output = self.create(name + "-" + destination)
                    path = output / name
                    if destination == "inside":
                        backup = output / (name + ".original")
                        path.rename(backup)
                        path.symlink_to(backup.name)
                    elif destination == "outside":
                        backup = self.directory / (name + ".original")
                        path.rename(backup)
                        path.symlink_to(backup)
                    else:
                        path.unlink()
                        path.symlink_to(self.directory / "absent-control")
                    with patch.object(Path, "read_text", side_effect=AssertionError("unsafe control read")) as read, \
                         self.assertRaisesRegex(ValueError, "regular file"):
                        packaging.verify_package(self.config, output)
                    read.assert_not_called()

    def test_missing_or_non_regular_package_controls_are_rejected_before_reads(self):
        for name in ("PACKAGE_MANIFEST.json", "SHA256SUMS"):
            for kind in ("missing", "directory", "fifo"):
                with self.subTest(control=name, kind=kind):
                    output = self.create(name + "-" + kind)
                    path = output / name
                    path.unlink()
                    if kind == "directory":
                        path.mkdir()
                    elif kind == "fifo":
                        os.mkfifo(path)
                    # Fail immediately rather than blocking on a FIFO if the guard regresses.
                    with patch.object(Path, "read_text", side_effect=AssertionError("unsafe control read")) as read, \
                         self.assertRaisesRegex(ValueError, "regular file"):
                        packaging.verify_package(self.config, output)
                    read.assert_not_called()

    def test_edited_manifest_cannot_expand_base_package_inventory(self):
        output = self.create()
        manifest = json.loads((output / "PACKAGE_MANIFEST.json").read_text())
        manifest["files"]["extra.txt"] = "a" * 64
        (output / "PACKAGE_MANIFEST.json").write_text(json.dumps(manifest))
        with self.assertRaisesRegex(ValueError, "inventory"):
            packaging.verify_package(self.config, output)

    def test_malformed_manifest_has_a_clear_cli_error(self):
        output = self.create()
        (output / "PACKAGE_MANIFEST.json").write_text("[]")
        with patch.object(packaging, "configuration", return_value=self.config), redirect_stderr(io.StringIO()) as errors:
            self.assertEqual(packaging.main(["--verify", str(output)]), 1)
        self.assertIn("package format", errors.getvalue())

    def test_requirements_match_release_and_are_in_checksum_inventory(self):
        output = self.create()
        self.assertEqual((output / "requirements.txt").read_text(), packaging.requirements(self.config))
        (output / "requirements.txt").write_text("unprovided-library==1.0.0\n")
        with self.assertRaisesRegex(ValueError, "checksum"):
            packaging.verify_package(self.config, output)

    def test_verification_is_read_only_and_does_not_require_container(self):
        for target in ("linux_aarch64", "linux_x86_64"):
            with self.subTest(target=target):
                output = self.create(target, target=target)
                before = {str(path.relative_to(output)): path.read_bytes()
                          for path in output.rglob("*") if path.is_file()}
                with patch.object(packaging, "configuration", return_value=self.config), \
                     patch.object(packaging, "require_dev_container") as guard, redirect_stdout(io.StringIO()):
                    self.assertEqual(packaging.main(["--verify", str(output)]), 0)
                    guard.assert_not_called()
                after = {str(path.relative_to(output)): path.read_bytes()
                         for path in output.rglob("*") if path.is_file()}
                self.assertEqual(before, after)

    def test_verification_rejects_all_explicit_packaging_arguments(self):
        for arguments in (["--platform", "linux_aarch64"], ["--platform", "linux_x86_64"],
                          ["--platform=linux_x86_64"], ["--recipe", "subscribe-state"],
                          ["--assets-dir", str(self.assets)], ["--output", str(self.directory / "unused")]):
            with self.subTest(arguments=arguments), \
                 patch.object(packaging, "configuration", return_value=self.config), \
                 patch.object(packaging, "verify_package") as verify, \
                 patch.object(packaging, "package") as create, \
                 patch.object(packaging, "require_dev_container") as guard, \
                 redirect_stderr(io.StringIO()) as errors, redirect_stdout(io.StringIO()) as output:
                with self.assertRaises(SystemExit) as error:
                    packaging.main(["--verify", str(self.directory / "absent-package"), *arguments])
                self.assertEqual(error.exception.code, 2)
                self.assertIn("--verify cannot be combined", errors.getvalue())
                self.assertFalse(output.getvalue())
                verify.assert_not_called()
                create.assert_not_called()
                guard.assert_not_called()

    def test_packaging_cli_preserves_default_and_explicit_platforms(self):
        for arguments, target in (([], "linux_aarch64"), (["--platform", "linux_aarch64"], "linux_aarch64"),
                                  (["--platform", "linux_x86_64"], "linux_x86_64")):
            with self.subTest(arguments=arguments), \
                 patch.object(packaging, "configuration", return_value=self.config), \
                 patch.object(packaging, "require_dev_container") as guard, \
                 patch.object(packaging, "package") as create, redirect_stdout(io.StringIO()):
                output = self.directory / "unused"
                self.assertEqual(packaging.main(["--recipe", "subscribe-state", "--assets-dir", str(self.assets),
                                                 "--output", str(output), *arguments]), 0)
                guard.assert_called_once_with()
                create.assert_called_once_with(self.config, "subscribe-state", self.assets.resolve(), output, target)

    def test_packaging_cli_refuses_wrong_context_before_output(self):
        output = self.directory / "unused"
        with patch.object(packaging, "configuration", return_value=self.config), \
             patch.object(packaging, "require_dev_container", side_effect=RuntimeError("container required")), \
             redirect_stderr(io.StringIO()):
            self.assertEqual(packaging.main(["--recipe", "subscribe-state", "--assets-dir", str(self.assets),
                                             "--output", str(output)]), 1)
        self.assertFalse(output.exists())

    def test_packaging_never_builds_installs_or_contacts_network(self):
        with patch.object(socket, "socket", side_effect=AssertionError("network access")), \
             patch("subprocess.run", side_effect=AssertionError("external command")):
            self.create()

    def test_fetch_reuses_matching_assets_without_network(self):
        with patch.object(fetch_sdk, "urlopen", side_effect=AssertionError("network access")):
            fetch_sdk.fetch(self.config, self.assets)

    def test_fetch_preserves_invalid_existing_asset_for_inspection(self):
        path = self.assets / self.config["sdk"]["assets"][0]["name"]
        path.write_bytes(b"retain for inspection")
        with patch.object(fetch_sdk, "urlopen", side_effect=AssertionError("network access")), \
             self.assertRaisesRegex(ValueError, "existing asset"):
            fetch_sdk.fetch(self.config, self.assets)
        self.assertEqual(path.read_bytes(), b"retain for inspection")

    def test_new_execution_clis_guard_before_side_effects(self):
        for module, args, operation in (
            (fetch_sdk, ["--output", str(self.directory / "new-assets")], "fetch"),
            (sdk_ci, ["--assets-dir", str(self.assets), "--work-dir", str(self.directory / "new-work")], "check"),
        ):
            with self.subTest(tool=module.__name__), \
                 patch.object(module, "require_dev_container", side_effect=RuntimeError("container required")), \
                 patch.object(module, operation) as execute, redirect_stderr(io.StringIO()):
                self.assertEqual(module.main(args), 1)
                execute.assert_not_called()

    def test_sdk_ci_checks_actual_bazel_version_and_compiler_target(self):
        version = "bazel " + self.config["development"]["bazel_version"] + "\n"
        for outputs, message in ((("bazel 0.0.0\n",), "Bazel version"),
                                 ((version, "aarch64-linux-gnu\n"), "compiler target")):
            with self.subTest(error=message), \
                 patch.object(sdk_ci.subprocess, "run", side_effect=[SimpleNamespace(stdout=value) for value in outputs]), \
                 self.assertRaisesRegex(ValueError, message):
                sdk_ci.check_toolchain(self.config, "linux_x86_64", {})


class PythonNativeRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)
        self.prefix = self.directory / "venv"
        self.package = self.prefix / "lib/python3.10/site-packages/aorta"
        self.package.mkdir(parents=True)
        self.library = self.package / "libaorta_core.so"
        self.library.write_bytes(b"synthetic library; never loaded")
        self.core = SimpleNamespace(_name=str(self.library), aorta_abi_version=Mock(return_value=13))
        self.sdk = ModuleType("aorta")
        self.sdk.__file__ = str(self.package / "__init__.py")
        self.sdk.load_library = Mock(return_value=self.core)
        self.sdk.Node = Mock(side_effect=AssertionError("native checks must not create a Node"))
        locomotion = ModuleType("locomotion")
        locomotion.__path__ = []
        status = ModuleType("locomotion.LocomotionStatus")
        status.LocomotionStatus = object
        self.modules = {"aorta": self.sdk, "locomotion": locomotion, "locomotion.LocomotionStatus": status}

    def probe(self):
        with patch.dict(sys.modules, self.modules), patch.object(sys, "prefix", str(self.prefix)), \
             patch.object(sys, "argv", ["-c", "13"]), redirect_stdout(io.StringIO()) as output:
            exec(sdk_ci.PYTHON_RUNTIME_PROBE, {"__name__": "__main__"})
            return json.loads(output.getvalue())

    def test_loads_the_bundled_runtime_and_checks_abi_without_a_node(self):
        result = self.probe()
        self.assertEqual(result["abi"], 13)
        self.assertEqual(result["library"], "aorta/libaorta_core.so")
        self.assertFalse(result["device_contacted"])
        self.sdk.load_library.assert_called_once_with()
        self.core.aorta_abi_version.assert_called_once_with()
        self.sdk.Node.assert_not_called()

    def test_import_success_does_not_hide_native_load_failure(self):
        self.sdk.load_library.side_effect = RuntimeError("simulated native load failure")
        with self.assertRaisesRegex(RuntimeError, "native load failure"):
            self.probe()
        self.sdk.load_library.assert_called_once_with()
        self.sdk.Node.assert_not_called()

    def test_wrong_native_abi_is_rejected(self):
        self.core.aorta_abi_version.return_value = 12
        with self.assertRaisesRegex(RuntimeError, "ABI"):
            self.probe()

    def test_external_runtime_is_rejected_even_if_its_abi_matches(self):
        self.core._name = str(self.directory / "other/libaorta_core.so")
        with self.assertRaisesRegex(RuntimeError, "other than the wheel-bundled"):
            self.probe()
        self.core.aorta_abi_version.assert_not_called()

    def test_missing_bundled_library_is_rejected_before_loader_fallback(self):
        self.library.unlink()
        with self.assertRaisesRegex(RuntimeError, "missing or outside"):
            self.probe()
        self.sdk.load_library.assert_not_called()

    def test_external_python_package_is_rejected_before_loading(self):
        self.sdk.__file__ = str(self.directory / "other/aorta/__init__.py")
        with self.assertRaisesRegex(RuntimeError, "package is outside"):
            self.probe()
        self.sdk.load_library.assert_not_called()

    def test_library_symlink_cannot_escape_the_venv(self):
        outside = self.directory / "other-core.so"
        outside.write_bytes(b"unrelated runtime")
        self.library.unlink()
        self.library.symlink_to(outside)
        with self.assertRaisesRegex(RuntimeError, "outside the active venv"):
            self.probe()
        self.sdk.load_library.assert_not_called()

    def test_both_installation_modes_run_the_probe_without_inherited_library_override(self):
        config = configuration()
        environment = {"PATH": "/checked-tools", "AORTA_CORE_FFI_LIB": "/unrelated/libaorta_core.so"}
        for requirements_file in (None, self.directory / "requirements.txt"):
            with self.subTest(requirements=requirements_file is not None), \
                 patch.object(sdk_ci.venv, "EnvBuilder"), patch.object(sdk_ci, "execute") as execute:
                python = sdk_ci.install(config, self.directory, self.prefix, "linux_x86_64", environment,
                                        requirements_file=requirements_file)
                self.assertEqual(execute.call_args.args[0],
                                 [python, "-c", sdk_ci.PYTHON_RUNTIME_PROBE, str(config["sdk"]["cpp"]["abi"])])
                self.assertEqual(execute.call_count, 3)
                for call in execute.call_args_list:
                    self.assertNotIn("AORTA_CORE_FFI_LIB", call.kwargs["env"])
                self.assertEqual(environment["AORTA_CORE_FFI_LIB"], "/unrelated/libaorta_core.so")


if __name__ == "__main__":
    require_dev_container()
    unittest.main()
