"""Synthetic telemetry only; never import or connect the SDK."""

import math
import unittest
from health_monitor.model import Monitor


class MonitorTests(unittest.TestCase):
    def setUp(self):
        self.monitor = Monitor({"stale_after_seconds": 3, "low_battery_percent": 20})

    def populate(self, now=0):
        for stream, data in (("state", {"heartbeat_seq": 1}), ("battery", {"soc_percent": 80}),
                             ("system", {"heartbeat_seq": 1})):
            self.monitor.update(stream, data, 100, now)

    def test_empty_input_never_means_healthy(self):
        result = self.monitor.snapshot(100)
        self.assertFalse(result["all_streams_receiving"])
        self.assertEqual({value["status"] for value in result["streams"].values()}, {"waiting_data"})

    def test_all_streams_then_disconnect(self):
        self.populate()
        self.assertTrue(self.monitor.snapshot(2)["all_streams_receiving"])
        result = self.monitor.snapshot(4)
        self.assertFalse(result["all_streams_receiving"])
        self.assertEqual({value["status"] for value in result["streams"].values()}, {"stale"})

    def test_delayed_and_duplicate_frames_do_not_refresh_freshness(self):
        self.populate()
        self.assertFalse(self.monitor.update("battery", {"soc_percent": 80}, 99, 3))
        self.assertFalse(self.monitor.update("battery", {"soc_percent": 80}, 100, 3))
        self.assertEqual(self.monitor.snapshot(4)["streams"]["battery"]["status"], "stale")

    def test_recovery_requires_new_data(self):
        self.populate()
        self.assertTrue(self.monitor.update("battery", {"soc_percent": 10}, 200, 5))
        result = self.monitor.snapshot(5)
        self.assertTrue(result["low_battery"])
        self.assertFalse(result["all_streams_receiving"])

    def test_invalid_values_do_not_refresh(self):
        for value in (None, {}, {"soc_percent": math.nan}, {"soc_percent": -1}, {"soc_percent": 101}):
            self.assertFalse(self.monitor.update("battery", value, 1, 0))
        self.assertEqual(self.monitor.snapshot(0)["streams"]["battery"]["invalid"], 5)

    def test_zero_source_timestamp_uses_local_freshness(self):
        self.assertTrue(self.monitor.update("state", {"heartbeat_seq": 1}, 0, 0))
        self.assertEqual(self.monitor.snapshot(4)["streams"]["state"]["status"], "stale")

    def test_bad_configuration(self):
        for age in (0, -1, math.inf, math.nan, True):
            with self.assertRaises(ValueError):
                Monitor({"stale_after_seconds": age, "low_battery_percent": 20})


if __name__ == "__main__":
    unittest.main()
