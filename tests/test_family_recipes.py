"""Offline checks for the eight-family index and new read-only recipe paths."""
from contextlib import contextmanager, redirect_stdout, redirect_stderr
import importlib
import io
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from recipes import observe

FAMILIES = ("sensors", "perception", "system-peripherals", "slam")


class FamilyTests(unittest.TestCase):
    def test_slam_scope_excludes_unreleased_grid_path(self):
        module = importlib.import_module("recipes.slam.main")
        self.assertEqual(set(module.ROUTES), {"status", "odometry", "transforms"})
        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
            module.main(["--stream", "grid"])
        self.assertEqual(error.exception.code, 2)

    def test_all_stream_previews_are_offline(self):
        for family in FAMILIES:
            module = importlib.import_module("recipes." + family + ".main")
            for stream, (route, root) in module.ROUTES.items():
                with self.subTest(family=family, stream=stream), \
                     patch.object(observe, "device_node", side_effect=AssertionError("no device")), \
                     redirect_stdout(io.StringIO()) as output:
                    self.assertEqual(module.main(["--stream", stream]), 0)
                    data = json.loads(output.getvalue())
                    self.assertFalse(data["execute"])
                    self.assertEqual(data["route"], route)
                    self.assertEqual(data["root_type"], root)

    def test_invalid_stream_or_write_option_is_rejected(self):
        for family in FAMILIES:
            module = importlib.import_module("recipes." + family + ".main")
            for args in (["--stream", "unknown"], ["--mode", "mapping"], ["--count", "0"]):
                with self.subTest(family=family, args=args), redirect_stderr(io.StringIO()), \
                     self.assertRaises(SystemExit) as error:
                    module.main(args)
                self.assertEqual(error.exception.code, 2)

    def test_probability_is_stable_and_missing_geometry_stays_missing(self):
        from recipes.perception.main import probability
        from recipes.slam.main import pose
        self.assertEqual(probability(1000), 1)
        self.assertEqual(probability(-1000), 0)
        self.assertEqual(probability(0), 0.5)
        self.assertIsNone(probability(float("nan")))
        self.assertIsNone(pose(None, object()))
        self.assertIsNone(pose(object(), None))
        self.assertEqual(observe.finite({"v": [float("inf"), 0]}), {"v": [None, 0]})


if __name__ == "__main__":
    unittest.main()
