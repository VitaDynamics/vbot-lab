"""Native C++ Blueprint previews and parity checks; never connect to a robot."""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(os.environ.get("TEST_SRCDIR", "")) / os.environ.get("TEST_WORKSPACE", "")
sys.path.insert(0, str(ROOT / "blueprints/health-monitor"))
from health_monitor.model import Monitor


class HealthCppTests(unittest.TestCase):
    def execute(self, *args, config=None, environment=None):
        env = dict(os.environ, ZENOH_SESSION_CONFIG_URI="/nonexistent-health-monitor-test")
        if environment is not None:
            env.update(environment)
        return subprocess.run([str(ROOT / "blueprints/health-monitor/main_cpp"),
            "--config", str(config or ROOT / "blueprints/health-monitor/config.json"), *args],
            capture_output=True, text=True, timeout=10, env=env)

    def test_preview_is_read_only_and_help_needs_no_config(self):
        result = self.execute()
        self.assertEqual(result.returncode, 0, result.stderr)
        value = json.loads(result.stdout)
        self.assertFalse(value["execute"])
        self.assertEqual(value["routes"], {"state": "/locomotion/status", "battery": "/bms_state", "system": "/system/sm_status"})
        self.assertEqual(self.execute("--help", config="/nonexistent-config").returncode, 0)

    def test_simulation_statuses_match_python_model(self):
        result = self.execute("--simulate")
        self.assertEqual(result.returncode, 0, result.stderr)
        actual = [json.loads(line) for line in result.stdout.splitlines()]
        model = Monitor({"stale_after_seconds": 3, "low_battery_percent": 20})
        for stream, data in (("state", {"heartbeat_seq": 1}), ("battery", {"soc_percent": 80}), ("system", {"heartbeat_seq": 1})):
            model.update(stream, data, 1, 0)
        for snapshot, now in zip(actual, (0, 4)):
            expected = model.snapshot(now)
            self.assertEqual(snapshot["source"], "synthetic")
            for key in ("all_streams_receiving", "low_battery"):
                self.assertEqual(snapshot[key], expected[key])
            for stream in expected["streams"]:
                for key in ("status", "age_seconds", "samples", "invalid", "out_of_order"):
                    self.assertEqual(snapshot["streams"][stream][key], expected["streams"][stream][key])

    def test_configuration_values_are_used(self):
        with tempfile.TemporaryDirectory() as location:
            config = Path(location) / "config.json"
            config.write_text('{"stale_after_seconds":9,"low_battery_percent":90}')
            result = self.execute("--simulate", config=config)
            self.assertEqual(result.returncode, 0, result.stderr)
            states = [json.loads(line) for line in result.stdout.splitlines()]
            self.assertTrue(states[0]["low_battery"])
            self.assertFalse(states[1]["low_battery"])
            self.assertEqual(states[1]["streams"]["state"]["age_seconds"], 10)

    def test_missing_or_invalid_configuration_stops_before_node_creation(self):
        self.assertEqual(self.execute(config="/nonexistent-config").returncode, 1)
        with tempfile.TemporaryDirectory() as location:
            path = Path(location) / "config.json"
            for content in ('{}', '{"stale_after_seconds":true,"low_battery_percent":20}', '[]',
                            '{"stale_after_seconds":3,"low_battery_percent":20,"extra":0}'):
                path.write_text(content)
                self.assertEqual(self.execute(config=path).returncode, 1)

    def test_invalid_options_never_create_device_session(self):
        for arguments in (("--execute", "--simulate"), ("--duration", "nan"), ("--duration", "0"),
                          ("--duration", "inf"), ("--duration", "121"), ("--unknown",),
                          ("--duration",), ("--execute", "--execute"), ("--duration", "1x")):
            with self.subTest(arguments=arguments):
                self.assertEqual(self.execute(*arguments).returncode, 2)

    def test_host_preview_is_rejected(self):
        self.assertEqual(self.execute(environment={"VBOT_DEV_CONTAINER": "0"}).returncode, 1)


if __name__ == "__main__":
    unittest.main()
