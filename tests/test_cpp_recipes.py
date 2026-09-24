"""Run C++ previews and argument checks only. Requires explicit release-SDK build."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(os.environ.get("TEST_SRCDIR", "")) / os.environ.get("TEST_WORKSPACE", "")
SLUGS = ("device-info", "subscribe-state", "service-call", "camera", "audio", "locomotion", "rcp-task",
         "sensors", "perception", "system-peripherals", "slam")


class CppRecipeTests(unittest.TestCase):
    def execute(self, slug, *args):
        # Even a misconfigured Aorta environment must not affect offline previews.
        environment = dict(os.environ, ZENOH_SESSION_CONFIG_URI="/nonexistent-vbot-lab-test-config")
        return subprocess.run([str(ROOT / "recipes" / slug / "main_cpp"), *args],
                              capture_output=True, text=True, timeout=10, env=environment)

    def test_all_default_previews_and_help(self):
        for slug in SLUGS:
            with self.subTest(slug=slug):
                result = self.execute(slug, *(["--mode", "stand"] if slug == "locomotion" else []))
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertFalse(json.loads(result.stdout)["execute"])
                self.assertEqual(self.execute(slug, "--help").returncode, 0)

    def test_motion_and_voice_need_explicit_confirmation(self):
        for slug, args in (("locomotion", ["--mode", "stand", "--execute"]),
                           ("audio", ["--execute"]), ("camera", ["--output", "private.h265"]),
                           ("audio", ["--source", "asr", "--output", "private.bin"])):
            with self.subTest(slug=slug):
                self.assertEqual(self.execute(slug, *args).returncode, 2)

    def test_family_streams_and_write_rejection(self):
        families = {"sensors": ("battery", "imu", "lidar-imu", "points"),
                    "perception": ("detections", "poses"),
                    "system-peripherals": ("system", "display"),
                    "slam": ("status", "odometry", "transforms")}
        for slug, streams in families.items():
            for stream in streams:
                with self.subTest(slug=slug, stream=stream):
                    result = self.execute(slug, "--stream", stream)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertFalse(json.loads(result.stdout)["execute"])
            self.assertEqual(self.execute(slug, "--stream", "unknown").returncode, 2)
            self.assertEqual(self.execute(slug, "--mode", "mapping").returncode, 2)
        self.assertEqual(self.execute("slam", "--stream", "grid").returncode, 2)

    def test_invalid_arguments_never_execute(self):
        for slug, args in (("subscribe-state", ["--count", "0"]), ("subscribe-state", ["--count", "1.5"]),
                           ("camera", ["--timeout", "nan"]), ("camera", ["--camera", "other"]),
                           ("audio", ["--source", "uwb", "--provider", "tag"]),
                           ("rcp-task", ["--duration-ms", "10001"]),
                           ("rcp-task", ["--cancel-after", "10", "--timeout", "10"]),
                           ("service-call", ["--unknown"]), ("service-call", ["--timeout"])):
            with self.subTest(slug=slug, args=args):
                self.assertEqual(self.execute(slug, *args).returncode, 2)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--bin-root", type=Path)
    args, remaining = parser.parse_known_args()
    if args.bin_root:
        ROOT = args.bin_root.resolve()
    unittest.main(argv=[sys.argv[0], *remaining])
