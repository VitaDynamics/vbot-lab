"""Offline release-configuration checks; no SDK, Docker, GitHub or robot access."""

from contextlib import redirect_stderr, redirect_stdout
import copy
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import socket
import subprocess
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("release_check", ROOT / "tools/check_release.py")
release = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(release)


class ReleaseTests(unittest.TestCase):
    def setUp(self):
        self.baseline = release.read_json(ROOT / "catalog/release.json")
        self.config = copy.deepcopy(self.baseline)
        self.config["workspace"]["tag"] = None
        self.config["development"]["image"]["digest"] = None

    def rejects(self, config, message):
        with self.assertRaisesRegex(release.ReleaseError, message):
            release.validate(config, ROOT)

    def invoke(self, *args):
        output, errors = io.StringIO(), io.StringIO()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "release.json"
            path.write_text(json.dumps(self.config))
            arguments = list(args)
            if "--config" not in arguments:
                arguments += ["--config", str(path)]
            with redirect_stdout(output), redirect_stderr(errors):
                code = release.main(arguments)
        return code, output.getvalue(), errors.getvalue()

    def test_checkout_pairing(self):
        expected = []
        if self.baseline["workspace"]["tag"] is None:
            expected.append("workspace.tag")
        if self.baseline["development"]["image"]["digest"] is None:
            expected.append("development.image.digest")
        self.assertEqual(release.validate(self.baseline, ROOT), expected)

    def test_current_source_snapshot_is_recorded(self):
        self.assertEqual(self.baseline["workspace"],
                         {"branch": "pre_release/V1.6.0.X", "tag": "V1.6.0.12"})
        self.assertEqual(release.validate(self.baseline, ROOT), [])

    def test_consistent_draft_reports_pending(self):
        code, output, errors = self.invoke()
        self.assertEqual(code, 0)
        self.assertFalse(errors)
        self.assertFalse(json.loads(output)["configuration_complete"])
        self.assertEqual(json.loads(output)["status"], "incomplete")

    def test_strict_completion_blocks_draft(self):
        code, output, _ = self.invoke("--require-complete")
        self.assertEqual(code, 1)
        self.assertTrue(json.loads(output)["pending"])

    def test_complete_configuration(self):
        self.config["workspace"]["branch"] = "main"
        self.config["workspace"]["tag"] = "V1.6.1"
        self.config["development"]["image"]["digest"] = self.baseline["development"]["image"]["digest"]
        self.assertEqual(release.validate(self.config, ROOT), [])
        code, output, errors = self.invoke("--require-complete")
        self.assertEqual(code, 0)
        self.assertFalse(errors)
        self.assertTrue(json.loads(output)["configuration_complete"])

    def test_unknown_and_missing_fields(self):
        for change in (lambda config: config.update({"unexpected": True}),
                       lambda config: config["sdk"].pop("assets")):
            config = copy.deepcopy(self.config)
            change(config)
            self.rejects(config, "missing or unknown fields")

    def test_invalid_format(self):
        for value in (True, 2, "1", None):
            self.config["format_version"] = value
            self.rejects(self.config, "format_version")

    def test_unsafe_tag(self):
        for value in ("../tag", "x..y", "tag.lock", "tag.", "", "refs/tags/V1.6.1", 1):
            self.config["workspace"]["tag"] = value
            self.rejects(self.config, "workspace.tag")

    def test_robot_scope_and_application(self):
        self.config["robots"]["wheel_quadruped"] = {"application_version": "V1.6.0-10"}
        self.rejects(self.config, "current_target")
        del self.config["robots"]["wheel_quadruped"]
        self.config["robots"]["foot_quadruped"]["application_version"] = "V1.6.1"
        self.rejects(self.config, "robot profile")

    def test_catalog_release_mismatch(self):
        self.config["sdk"]["release_tag"] = "edu-sdk-2099.1.1"
        self.rejects(self.config, "catalog mismatch")

    def test_recipe_versions_are_parsed_not_imported(self):
        old_version = self.config["sdk"]["python"]["wheels"]["aorta_msgs"]
        self.config["sdk"]["python"]["wheels"]["aorta_msgs"] = "2099.1.1"
        for item in self.config["sdk"]["assets"]:
            item["name"] = item["name"].replace(f"aorta_msgs-{old_version}", "aorta_msgs-2099.1.1")
        self.rejects(self.config, "SDK_VERSIONS")

    def test_bazel_abi_guard(self):
        old_abi = self.config["sdk"]["cpp"]["abi"]
        new_abi = old_abi + 1
        original_read = release.read_json
        with patch.object(release, "read_json", wraps=release.read_json) as read:
            def changed(path):
                data = original_read(path)
                if path.name == "capabilities.json":
                    data["sdk"]["cpp"]["abi"] = new_abi
                return data
            read.side_effect = changed
            self.config["sdk"]["cpp"]["abi"] = new_abi
            for item in self.config["sdk"]["assets"]:
                item["name"] = item["name"].replace(f"-abi{old_abi}-", f"-abi{new_abi}-")
            self.rejects(self.config, "libaorta_core ABI")

    def test_bad_abi_types(self):
        for value in (True, "12", 0, -1):
            self.config["sdk"]["cpp"]["abi"] = value
            self.rejects(self.config, "positive integer")

    def test_missing_asset(self):
        self.config["sdk"]["assets"] = [item for item in self.config["sdk"]["assets"]
                                         if item["name"] != "EDU_SDK_MANIFEST.json"]
        self.rejects(self.config, "missing required")

    def test_duplicate_and_unsafe_assets(self):
        for value in ("duplicate", "../asset.whl", "/asset.whl", "-option", "bad\\name"):
            config = copy.deepcopy(self.config)
            if value == "duplicate":
                config["sdk"]["assets"].append(config["sdk"]["assets"][0])
            else:
                config["sdk"]["assets"][0]["name"] = value
            self.rejects(config, "sdk.assets")

    def test_checksum_validation(self):
        for value in ("a" * 63, "A" * 64, "sha256:" + "a" * 64, None):
            self.config["sdk"]["assets"][0]["sha256"] = value
            self.rejects(self.config, "sha256")

    def test_schema_revision_and_manifest_mismatch(self):
        config = copy.deepcopy(self.config)
        config["schema"]["pack_version"] = "2099.1.1-v4"
        self.rejects(config, "pack revision")
        self.config["schema"]["ros2_bridge_version"] = "2099.1.1"
        self.rejects(self.config, "MANIFEST mismatch")

    def test_image_and_bazel_mismatch(self):
        self.config["development"]["image"]["reference"] = "example.com/edu:other"
        self.rejects(self.config, "Compose")
        self.config = release.read_json(ROOT / "catalog/release.json")
        self.config["development"]["bazel_version"] = "9.0.0"
        self.rejects(self.config, "Bazel version")

    def test_digest_format(self):
        self.config["development"]["image"]["digest"] = "latest"
        self.rejects(self.config, "image.digest")

    def test_compose_digest_must_match_release_configuration(self):
        self.config["development"]["image"]["digest"] = "sha256:" + "a" * 64
        self.rejects(self.config, "Compose")

    def test_platform_selection(self):
        for platforms in ([], ["windows"], ["linux_aarch64", "linux_aarch64"], [None]):
            self.config["sdk"]["python"]["platforms"] = platforms
            self.rejects(self.config, "python.platforms")

    def test_iteration_tag_matches_branch_family(self):
        self.config["workspace"] = {"branch": "pre_release/V1.6.0.X", "tag": "V1.6.0.12"}
        release.validate(self.config, ROOT)
        for value in ("V1.16.0.12", "V1.6.1.12", "V1.6.0-12", "V1.6.0.X", "V1.6.0"):
            self.config["workspace"]["tag"] = value
            self.rejects(self.config, "iteration branch family")

    def test_iteration_branch_must_be_a_long_lived_family(self):
        for value in ("pre_release/V1.6.0.10", "V1.6.0.X", "../main", None):
            self.config["workspace"]["branch"] = value
            self.rejects(self.config, "workspace.branch")

    def test_sdk_manifest_pairing_and_hashes(self):
        sdk, schema = self.config["sdk"], self.config["schema"]
        manifest = {"release_tag": sdk["release_tag"], "pairing": {
            "aorta": sdk["aorta_version"], "schema_pack": schema["version"],
            "ros2_bridge": schema["ros2_bridge_version"], "wheels": sdk["python"]["wheels"]},
            "assets": [copy.deepcopy(item) for item in sdk["assets"]
                       if item["name"] not in {"EDU_SDK_MANIFEST.json", "SHA256SUMS"}]}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "manifest.json"
            path.write_text(json.dumps(manifest))
            release.check_sdk_manifest(self.config, path)
            manifest["assets"][0]["sha256"] = "b" * 64
            path.write_text(json.dumps(manifest))
            with self.assertRaisesRegex(release.ReleaseError, "checksum mismatch"):
                release.check_sdk_manifest(self.config, path)

    def test_hash_local_assets_without_execution(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "asset.whl"
            path.write_bytes(b"synthetic test asset")
            component = {"assets": [{"name": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}]}
            release.check_assets(component, root)
            path.write_bytes(b"modified")
            with self.assertRaisesRegex(release.ReleaseError, "checksum mismatch"):
                release.check_assets(component, root)
            path.unlink()
            with self.assertRaisesRegex(release.ReleaseError, "Missing regular"):
                release.check_assets(component, root)
            path.symlink_to(ROOT / "catalog/release.json")
            with self.assertRaisesRegex(release.ReleaseError, "Missing regular"):
                release.check_assets(component, root)

    def test_json_and_io_errors_use_exit_two(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"
            for content in ('{"format_version":1,"format_version":2}', '{"sdk":', '[]'):
                path.write_text(content)
                code, output, errors = self.invoke("--config", str(path))
                self.assertEqual(code, 2)
                self.assertFalse(output)
                self.assertEqual(json.loads(errors)["status"], "error")
            code, _, _ = self.invoke("--config", str(path.parent / "missing.json"))
            self.assertEqual(code, 2)

    def test_never_contact_network_or_execute_commands(self):
        with patch.object(socket, "create_connection", side_effect=AssertionError("network")) as network, \
                patch.object(subprocess, "run", side_effect=AssertionError("command")) as command:
            self.assertEqual(self.invoke()[0], 0)
            network.assert_not_called()
            command.assert_not_called()


if __name__ == "__main__":
    unittest.main()
