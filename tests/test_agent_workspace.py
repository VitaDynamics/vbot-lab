"""Offline contract tests, not a model or live-device acceptance test."""

import argparse
import contextlib
from copy import deepcopy
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
RUNFILES = False
sys.path.insert(0, str(ROOT / "tools"))
from check_environment import inspect_environment  # noqa: E402
import check_device_environment as device_env  # noqa: E402
from vbot_catalog import CatalogError, capability_decision, load_catalog, query_catalog, validate_catalog  # noqa: E402


class AgentWorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.catalog, self.robots = load_catalog(ROOT)

    def test_robot_release_and_hardware_scope(self):
        self.assertEqual(self.robots["foot_quadruped"]["release_scope"], "current_target")
        self.assertEqual(self.robots["wheel_quadruped"]["release_scope"], "planned")
        self.assertEqual(self.robots["foot_humanoid"]["release_scope"], "planned")
        for field in ("sensor_reference", "connection_reference"):
            self.assertEqual(self.robots["foot_quadruped"][field], self.robots["wheel_quadruped"][field])
            self.assertIsNone(self.robots["foot_humanoid"][field])

    def test_unknown_versions_are_not_wildcards(self):
        self.assertEqual(self.catalog["sdk"]["integration"], "integrated")
        self.assertEqual(self.catalog["sdk"]["version"], "2026.9.23")
        self.assertEqual(self.catalog["sdk"]["python_import"], "aorta")
        for robot in self.robots.values():
            self.assertEqual(robot["models"], [])
            self.assertIsNone(robot["minimum_firmware"])

    def test_no_robot_is_inferred(self):
        result = query_catalog(ROOT)
        self.assertIsNone(result["robot"])
        for entry in result["capabilities"]:
            expected = "requires_robot_selection" if entry["robot_types"] else "local_only"
            self.assertEqual(entry["decision"], expected)

    def test_planned_devices_do_not_inherit_software_support(self):
        for name in ("wheel_quadruped", "foot_humanoid"):
            result = query_catalog(ROOT, name)
            for entry in result["capabilities"]:
                self.assertEqual(entry["decision"], "blocked_release" if entry["robot_types"] else "local_only")

    def test_documented_is_not_device_verified(self):
        entry = query_catalog(ROOT, "foot_quadruped", "device.agent.content")["capabilities"][0]
        self.assertEqual(entry["decision"], "requires_device_verification")
        self.assertEqual(entry["reference"], "docs/interfaces/agent/content-api.md")
        self.assertEqual(entry["verification"], "documentation_only")
        self.assertIsNone(entry["skill"])

    def test_implemented_recipe_still_needs_device_checks(self):
        entry = query_catalog(ROOT, "foot_quadruped", "robot.state.subscribe")["capabilities"][0]
        self.assertEqual(entry["decision"], "requires_device_verification")
        self.assertEqual(entry["interface_kind"], "pub_sub")
        self.assertEqual(entry["tool"], "recipes/subscribe-state/main.py")
        self.assertTrue((ROOT / "recipes/subscribe-state/BUILD.bazel").exists())

    def test_pending_integrations_remain_blocked(self):
        entry = query_catalog(ROOT, "foot_quadruped", "robot.state.subscribe")["capabilities"][0]
        robot = self.robots["foot_quadruped"]
        self.assertEqual(capability_decision(entry, robot, dict(self.catalog["sdk"], integration="pending")),
                         "blocked_integration")
        self.assertEqual(capability_decision(dict(entry, availability="planned", tool=None), robot, self.catalog["sdk"]),
                         "blocked_integration")

    def test_python_and_cpp_implementations_are_indexed(self):
        self.assertEqual(self.catalog["sdk"]["cpp"]["abi"], 12)
        for entry in self.catalog["capabilities"]:
            if entry.get("recipe"):
                self.assertEqual(set(entry["implementations"]), {"python", "cpp"})
                for language, target in (("python", ":main"), ("cpp", ":main_cpp")):
                    self.assertTrue(entry["implementations"][language]["bazel_target"].endswith(target))

    def test_cpp_catalog_rejects_invalid_sources_targets_and_metadata(self):
        for mutate in (
            lambda data: data["sdk"]["cpp"].update(abi="12"),
            lambda data: data["sdk"]["cpp"].update(reference="missing.md"),
            lambda data: next(e for e in data["capabilities"] if e.get("implementations"))["implementations"]["cpp"].update(source="../outside.cc"),
            lambda data: next(e for e in data["capabilities"] if e.get("implementations"))["implementations"]["cpp"].update(bazel_target="//wrong:main_cpp"),
        ):
            data = deepcopy(self.catalog)
            mutate(data)
            with self.assertRaises(CatalogError):
                validate_catalog(ROOT, data, self.robots)

    def test_family_recipes_are_discoverable_without_splitting_families(self):
        for family, slug in (("robot.cameras", "camera"), ("robot.audio", "audio"),
                             ("robot.locomotion", "locomotion"), ("robot.rcp", "rcp-task")):
            entry = query_catalog(ROOT, "foot_quadruped", family)["capabilities"][0]
            self.assertEqual(entry["recipe"], f"recipes/{slug}/README.md")
            self.assertTrue((ROOT / f"recipes/{slug}/main.py").is_file())
            self.assertFalse(entry["requires_sdk"])  # The family CLI guide stays usable independently.

    def test_device_cli_inventory_does_not_require_sdk(self):
        for capability in ("device.environment.check", "device.interfaces.discover"):
            entry = query_catalog(ROOT, "foot_quadruped", capability)["capabilities"][0]
            self.assertEqual(entry["decision"], "requires_device_verification")
            self.assertEqual(entry["execution_location"], "device_shell")
            self.assertEqual(entry["effect"], "device_read_only")
            self.assertFalse(entry["requires_sdk"])
            self.assertIsNone(entry["minimum_firmware"])

    def test_unknown_queries_fail_closed(self):
        with self.assertRaises(CatalogError):
            query_catalog(ROOT, "unknown_robot")
        with self.assertRaises(CatalogError):
            query_catalog(ROOT, capability="unknown.capability")

    def test_autostart_workflow_is_documented_and_not_read_only(self):
        capability = "device.application.autostart"
        result = query_catalog(ROOT, "foot_quadruped", capability)
        self.assertFalse(result["device_contacted"])
        entry = result["capabilities"][0]
        self.assertEqual(entry["decision"], "requires_device_verification")
        self.assertEqual(entry["availability"], "documented")
        self.assertEqual(entry["verification"], "documentation_only")
        self.assertEqual(entry["execution_location"], "device_shell")
        self.assertEqual(entry["interface_kind"], "local_cli")
        self.assertEqual(entry["effect"], "depends_on_operation")
        self.assertEqual(entry["reference"], "docs/guides/user-autostart.md")
        self.assertFalse(entry["requires_sdk"])
        self.assertIsNone(entry["minimum_firmware"])
        for field in ("tool", "recipe", "skill"):
            self.assertIsNone(entry[field])
        for robot in ("wheel_quadruped", "foot_humanoid"):
            self.assertEqual(query_catalog(ROOT, robot, capability)["capabilities"][0]["decision"],
                             "blocked_release")

    def test_slam_workflow_is_documented_not_automatically_executable(self):
        capability = "robot.slam.mapping-localization"
        result = query_catalog(ROOT, "foot_quadruped", capability)
        self.assertFalse(result["device_contacted"])
        entry = result["capabilities"][0]
        self.assertEqual(entry["decision"], "requires_device_verification")
        self.assertEqual(entry["availability"], "documented")
        self.assertEqual(entry["verification"], "documentation_only")
        self.assertEqual(entry["execution_location"], "device_shell")
        self.assertEqual(entry["interface_kind"], "service")
        self.assertEqual(entry["effect"], "depends_on_operation")
        self.assertEqual(entry["reference"], "docs/guides/mapping-localization.md")
        self.assertFalse(entry["requires_sdk"])
        self.assertIsNone(entry["minimum_firmware"])
        self.assertEqual(entry["recipe"], "recipes/slam/README.md")
        for field in ("tool", "skill"):
            self.assertIsNone(entry[field])
        for robot in ("wheel_quadruped", "foot_humanoid"):
            self.assertEqual(query_catalog(ROOT, robot, capability)["capabilities"][0]["decision"],
                             "blocked_release")

    def test_read_only_families_are_documented_as_single_capabilities(self):
        references = {
            "robot.sensors": "docs/interfaces/sensors.md",
            "robot.cameras": "docs/interfaces/cameras.md",
            "robot.perception": "docs/interfaces/perception.md",
            "robot.audio": "docs/interfaces/audio.md",
        }
        identifiers = [entry["id"] for entry in self.catalog["capabilities"]]
        for family in ("robot.perception", "robot.audio"):
            self.assertEqual(identifiers.count(family), 1)
            self.assertFalse(any(identifier.startswith(family + ".") for identifier in identifiers))
        for capability, reference in references.items():
            with self.subTest(capability=capability):
                result = query_catalog(ROOT, "foot_quadruped", capability)
                self.assertFalse(result["device_contacted"])
                entry = result["capabilities"][0]
                self.assertEqual(entry["reference"], reference)
                self.assertEqual(entry["decision"], "requires_device_verification")
                self.assertEqual(entry["availability"], "documented")
                self.assertEqual(entry["verification"], "documentation_only")
                self.assertEqual(entry["interface_kind"], "pub_sub")
                self.assertEqual(entry["effect"], "device_read_only")
                self.assertEqual(entry["execution_location"], "device_shell")
                self.assertFalse(entry["requires_sdk"])
                self.assertIsNone(entry["minimum_firmware"])
                for field in ("tool", "skill"):
                    self.assertIsNone(entry[field])
                for robot in ("wheel_quadruped", "foot_humanoid"):
                    decision = query_catalog(ROOT, robot, capability)["capabilities"][0]["decision"]
                    self.assertEqual(decision, "blocked_release")

    def test_command_topics_and_rcp_action_are_not_read_only(self):
        for capability, kind in (("robot.locomotion", "pub_sub"),
                                 ("robot.system-peripherals", "pub_sub"),
                                 ("robot.rcp", "action")):
            with self.subTest(capability=capability):
                result = query_catalog(ROOT, "foot_quadruped", capability)
                self.assertFalse(result["device_contacted"])
                entry = result["capabilities"][0]
                self.assertEqual(entry["availability"], "documented")
                self.assertEqual(entry["interface_kind"], kind)
                self.assertEqual(entry["effect"], "depends_on_operation")
                self.assertEqual(entry["decision"], "requires_device_verification")
                self.assertEqual(entry["verification"], "documentation_only")
                self.assertIsNone(entry["tool"])
                self.assertFalse(entry["requires_sdk"])
                for robot in ("wheel_quadruped", "foot_humanoid"):
                    self.assertEqual(query_catalog(ROOT, robot, capability)["capabilities"][0]["decision"],
                                     "blocked_release")

    def test_invalid_catalog_is_rejected(self):
        mutations = (
            lambda data: data.update(format_version=9),
            lambda data: data["capabilities"].append(deepcopy(data["capabilities"][0])),
            lambda data: data["capabilities"][0].update(robot_types=["unknown"]),
            lambda data: data["capabilities"][0].update(reference="../AGENTS.md"),
            lambda data: data["capabilities"][0].update(reference="/etc/passwd"),
            lambda data: data["capabilities"][0].update(reference="missing.md"),
            lambda data: data["capabilities"][0].update(requires_sdk="false"),
            lambda data: data["capabilities"][0].update(effect="device_read_only"),
            lambda data: data["capabilities"][0].update(availability="planned"),
            lambda data: data["capabilities"][0].update(verification="unknown"),
            lambda data: data["capabilities"][0].update(interface_kind="unknown"),
        )
        for mutate in mutations:
            data = deepcopy(self.catalog)
            mutate(data)
            with self.subTest(data=data), self.assertRaises(CatalogError):
                validate_catalog(ROOT, data, self.robots)

    def test_present_tools_do_not_establish_sdk_readiness(self):
        result = inspect_environment(ROOT, "host", which=lambda name: "/tools/" + name)
        self.assertEqual(result["inventory_status"], "complete")
        self.assertEqual(result["sdk_status"], "not_verified")
        self.assertIn("device_connection", result["not_checked"])
        self.assertFalse(result["device_contacted"])
        self.assertFalse(result["changes_made"])

    def test_host_and_container_requirements_are_distinct(self):
        lookup = lambda name: None if name == "docker" else "/tools/" + name
        host = inspect_environment(ROOT, "host", which=lookup)
        container = inspect_environment(ROOT, "container", which=lookup)
        self.assertEqual(host["inventory_status"], "attention_required")
        self.assertEqual(container["inventory_status"], "complete")
        self.assertNotIn("docker", [tool["name"] for tool in container["tools"]])

    def test_old_python_is_reported(self):
        result = inspect_environment(ROOT, "container", which=lambda name: name, python_version=(3, 9, 1))
        self.assertEqual(result["tools"][0]["status"], "incompatible")
        self.assertEqual(result["inventory_status"], "attention_required")

    def test_bazel_is_required_in_container_not_host(self):
        lookup = lambda name: None if name == "bazel" else "/tools/" + name
        host = inspect_environment(ROOT, "host", which=lookup)
        container = inspect_environment(ROOT, "container", which=lookup)
        self.assertEqual(host["inventory_status"], "complete")
        self.assertNotIn("bazel", [tool["name"] for tool in host["tools"]])
        self.assertEqual(container["inventory_status"], "attention_required")
        self.assertIn("docker_daemon", host["not_checked"])

    def test_environment_inventory_never_executes_or_connects(self):
        with patch("subprocess.Popen", side_effect=AssertionError("External command")), \
             patch("socket.create_connection", side_effect=AssertionError("Network connection")):
            result = inspect_environment(ROOT, "host", "wheel_quadruped", which=lambda name: name)
        self.assertEqual(result["robot_status"], "blocked_release")
        self.assertEqual(result["inventory_status"], "attention_required")

    def test_skill_discovery_content_matches(self):
        source = ROOT / "skills/vbot-dev-setup"
        for harness in (".agents", ".claude"):
            discovered = ROOT / harness / "skills/vbot-dev-setup"
            for name in ("SKILL.md", "SKILL.zh-CN.md"):
                self.assertEqual((discovered / name).read_bytes(), (source / name).read_bytes())
        english = (source / "SKILL.md").read_text()
        frontmatter = english.split("---", 2)[1]
        self.assertIn("name: vbot-dev-setup", frontmatter)
        self.assertIn("description:", frontmatter)

    def test_setup_skill_references_runnable_language_paths(self):
        # Validate the workflow's concrete resources, not model behavior.
        for suffix in (".md", ".zh-CN.md"):
            source = ROOT / "skills/vbot-dev-setup" / f"SKILL{suffix}"
            body = source.read_text()
            for relative in (
                f"../../docs/development/python-deployment{suffix}",
                f"../../packages/aorta/cpp/README{suffix}",
                f"../../recipes/subscribe-state/README{suffix}",
                f"../../docs/development/offline-build{suffix}",
            ):
                self.assertIn(relative, body)
                self.assertTrue((source.parent / relative).is_file())
            build = (ROOT / "recipes/subscribe-state/BUILD.bazel").read_text()
            for target in ("main", "main_cpp"):
                self.assertIn(f"//recipes/subscribe-state:{target}", body)
                self.assertIn(f'name = "{target}"', build)

    def test_checkout_aliases_are_relative_symlinks(self):
        if RUNFILES:
            self.skipTest("Bazel materializes runfiles; link metadata is checked on the source checkout")
        for harness in (".agents", ".claude"):
            alias = ROOT / harness / "skills"
            self.assertTrue(alias.is_symlink())
            self.assertEqual(os.readlink(alias), "../skills")
            self.assertEqual(alias.resolve(), (ROOT / "skills").resolve())

    def test_claude_imports_shared_instructions(self):
        for suffix in (".md", ".zh-CN.md"):
            imports = [line for line in (ROOT / f"CLAUDE{suffix}").read_text().splitlines() if line.startswith("@")]
            self.assertEqual(imports, [f"@AGENTS{suffix}"])
            self.assertTrue((ROOT / imports[0][1:]).is_file())

    def test_query_cli_exit_contract(self):
        script = ROOT / "tools/vbot_catalog.py"
        good = subprocess.run([sys.executable, str(script), "--root", str(ROOT), "--robot-type", "wheel_quadruped",
                               "--capability", "device.agent.content"], capture_output=True, text=True, timeout=10)
        self.assertEqual(good.returncode, 0, good.stderr)
        self.assertEqual(json.loads(good.stdout)["capabilities"][0]["decision"], "blocked_release")
        bad = subprocess.run([sys.executable, str(script), "--root", str(ROOT), "--robot-type", "unknown"],
                              capture_output=True, text=True, timeout=10)
        self.assertEqual(bad.returncode, 2)
        self.assertIn("Unknown robot type", json.loads(bad.stdout)["error"])

    def test_environment_cli_errors_and_missing_tools(self):
        script = ROOT / "tools/check_environment.py"
        with tempfile.TemporaryDirectory() as empty_path:
            env = dict(os.environ, PATH=empty_path)
            result = subprocess.run([sys.executable, str(script), "--root", str(ROOT), "--profile", "host"],
                                    env=env, capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual(json.loads(result.stdout)["sdk_status"], "not_verified")
        for args in (("--robot-type", "unknown"), ("--root", "/nonexistent-vbot-lab-checkout")):
            result = subprocess.run([sys.executable, str(script), "--root", str(ROOT), "--profile", "host", *args],
                                    capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertIn("error", json.loads(result.stdout))

    def test_external_application_uses_physical_skill_checkout(self):
        # Materialize only declared resources, never copy the user's .git or build caches.
        resources = {"catalog/capabilities.json", ".bazelversion", "tools/check_environment.py", "tools/vbot_catalog.py",
                     "skills/vbot-dev-setup/SKILL.md", self.catalog["sdk"]["reference"], self.catalog["sdk"]["cpp"]["reference"]}
        resources.update(str(path.relative_to(ROOT)) for path in (ROOT / "catalog/robots").glob("*.json"))
        for entry in self.catalog["capabilities"]:
            resources.update(entry[field] for field in ("reference", "skill", "tool", "recipe") if entry[field])
            for implementation in entry.get("implementations", {}).values():
                resources.add(implementation["source"])
                resources.add(str(Path(implementation["source"]).parent / "BUILD.bazel"))
        for robot in self.robots.values():
            resources.update(robot[field] for field in ("guide", "sensor_reference", "connection_reference") if robot[field])
        with tempfile.TemporaryDirectory() as temporary:
            checkout = Path(temporary) / "vbot lab"
            app = Path(temporary) / "application"
            app.mkdir()
            for resource in resources:
                destination = checkout / resource
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / resource, destination)
            for harness in (".agents", ".claude"):
                link = app / harness / "skills/vbot-dev-setup"
                link.parent.mkdir(parents=True)
                link.symlink_to(checkout / "skills/vbot-dev-setup", target_is_directory=True)
                resolved_root = (link / "SKILL.md").resolve().parents[2]
                self.assertEqual(resolved_root, checkout)
                result = subprocess.run([sys.executable, str(resolved_root / "tools/check_environment.py"),
                                         "--profile", "container"], cwd=app, capture_output=True, text=True, timeout=10)
                self.assertIn(result.returncode, (0, 1), result.stderr)
                self.assertEqual(json.loads(result.stdout)["sdk_status"], "not_verified")
                self.assertFalse((app / "catalog").exists())


class DeviceEnvironmentTests(unittest.TestCase):
    def inspect(self, *, overrides=None, username="vbot", readable=lambda path: True, which=None):
        environ = dict(device_env.EXPECTED_ENV, PATH=device_env.AORTA_BIN + ":/usr/bin")
        environ.update(overrides or {})
        if which is None:
            which = lambda name, path: device_env.AORTA_BIN + "/aorta" if name == "aorta" else "/usr/bin/" + name
        return device_env.inspect_device_environment(environ=environ, username=username,
                                                     readable=readable, which=which)

    def test_good_inventory_is_not_live_acceptance(self):
        result = self.inspect()
        self.assertEqual(result["inventory_status"], "complete")
        self.assertFalse(result["interfaces_contacted"])
        self.assertFalse(result["changes_made"])
        for untested in ("sample_reception", "ros_overlay_type_loading", "bash_startup_persistence",
                         "device_identity_and_firmware", "sdk_and_application_readiness"):
            self.assertIn(untested, result["not_checked"])

    def test_wrong_or_missing_settings_need_attention(self):
        for name in device_env.EXPECTED_ENV:
            for value in (None, "", "incorrect"):
                with self.subTest(name=name, value=value):
                    result = self.inspect(overrides={name: value})
                    self.assertEqual(result["inventory_status"], "attention_required")
                    check = next(check for check in result["checks"] if check["name"] == name)
                    self.assertNotEqual(check["status"], "ok")

    def test_wrong_account_and_missing_public_files(self):
        self.assertEqual(self.inspect(username="developer")["inventory_status"], "attention_required")
        for missing in device_env.PUBLIC_FILES:
            result = self.inspect(readable=lambda path: path != missing)
            self.assertEqual(result["inventory_status"], "attention_required")

    def test_lookup_uses_checked_path_and_rejects_shadowed_aorta(self):
        calls = []

        def which(name, path):
            calls.append((name, path))
            return "/different/bin/" + name

        result = self.inspect(which=which)
        self.assertEqual(result["inventory_status"], "attention_required")
        self.assertEqual(len(calls), 3)
        self.assertTrue(all(path == device_env.AORTA_BIN + ":/usr/bin" for name, path in calls))
        self.assertIn({"name": "aorta", "status": "unexpected_location"}, result["checks"])
        for missing in ("aorta", "ros2", "timeout"):
            result = self.inspect(which=lambda name, path: None if name == missing else device_env.AORTA_BIN + "/" + name)
            self.assertEqual(result["inventory_status"], "attention_required")

    def test_missing_path_is_not_hidden_by_command_lookup(self):
        result = self.inspect(overrides={"PATH": "/usr/bin"})
        self.assertEqual(result["inventory_status"], "attention_required")

    def test_no_external_execution_network_or_config_read(self):
        with patch("subprocess.Popen", side_effect=AssertionError("External command")), \
             patch("socket.socket", side_effect=AssertionError("Network access")), \
             patch("builtins.open", side_effect=AssertionError("File content access")), \
             patch("pathlib.Path.open", side_effect=AssertionError("File content access")):
            result = self.inspect()
        self.assertEqual(result["inventory_status"], "complete")

    def test_report_does_not_disclose_ambient_values(self):
        result = self.inspect(overrides={"ZENOH_SESSION_CONFIG_URI": "private-test-value",
                                         "UNRELATED_TOKEN": "private-test-token"}, username="private-test-user")
        self.assertNotIn("private-test", json.dumps(result))

    def test_cli_exit_codes_and_standalone_execution(self):
        for result, expected_code in ((self.inspect(), 0), (self.inspect(username="developer"), 1)):
            with patch.object(device_env, "inspect_device_environment", return_value=result), \
                 contextlib.redirect_stdout(io.StringIO()) as output:
                self.assertEqual(device_env.main([]), expected_code)
            self.assertEqual(json.loads(output.getvalue()), result)
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
            device_env.main(["--profile", "host"])
        self.assertEqual(error.exception.code, 2)
        with tempfile.TemporaryDirectory() as temporary:
            standalone = Path(temporary) / "check_device_environment.py"
            shutil.copyfile(ROOT / "tools/check_device_environment.py", standalone)
            result = subprocess.run([sys.executable, str(standalone)], cwd=temporary,
                                    env=dict(os.environ, PATH=""), capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertFalse(json.loads(result.stdout)["interfaces_contacted"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--runfiles", action="store_true")
    args = parser.parse_args()
    ROOT = args.root.absolute()
    RUNFILES = args.runfiles
    unittest.main(argv=[__file__], verbosity=2)
