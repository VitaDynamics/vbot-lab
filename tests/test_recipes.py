"""SDK-free recipe checks. Never connect to a robot."""

import argparse
from contextlib import contextmanager, redirect_stdout, redirect_stderr
import importlib
import io
import json
from pathlib import Path
import sys
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from recipes import common

SLUGS = ("device-info", "subscribe-state", "service-call", "camera", "audio", "locomotion", "rcp-task")


def recipe(slug):
    return importlib.import_module("recipes." + slug + ".main")


class RecipeTests(unittest.TestCase):
    def test_all_previews_do_not_load_sdk_or_open_node(self):
        for slug in SLUGS:
            module = recipe(slug)
            with self.subTest(slug=slug), patch.object(module, "device_node", side_effect=AssertionError("device access")), \
                 patch.object(common, "load_sdk", side_effect=AssertionError("SDK load")), redirect_stdout(io.StringIO()) as output:
                self.assertEqual(module.main(["--mode", "stand"] if slug == "locomotion" else []), 0)
                self.assertFalse(json.loads(output.getvalue())["execute"])

    def test_invalid_or_missing_safety_flags_fail_before_connection(self):
        cases = (("locomotion", ["--mode", "stand", "--execute"]),
                 ("audio", ["--execute"]), ("audio", ["--source", "body", "--provider", "tag"]),
                 ("audio", ["--output", "transcript.bin"]), ("camera", ["--decode"]),
                 ("camera", ["--output", "private.h265"]), ("rcp-task", ["--duration-ms", "0"]),
                 ("rcp-task", ["--cancel-after", "10", "--timeout", "10"]),
                 ("subscribe-state", ["--count", "0"]), ("subscribe-state", ["--timeout", "nan"]))
        for slug, args in cases:
            with self.subTest(slug=slug, args=args), redirect_stderr(io.StringIO()), \
                 patch.object(recipe(slug), "device_node", side_effect=AssertionError("device access")), \
                 self.assertRaises(SystemExit) as error:
                recipe(slug).main(args)
            self.assertEqual(error.exception.code, 2)

    def test_argument_bounds(self):
        for invalid in ("nan", "inf", "-1", "0", "121"):
            with self.assertRaises(argparse.ArgumentTypeError):
                common.positive_seconds(invalid)
        for invalid in ("0", "1001"):
            with self.assertRaises(argparse.ArgumentTypeError):
                common.count_value(invalid)

    def test_device_identity_and_environment_are_required(self):
        with patch("pwd.getpwuid", return_value=SimpleNamespace(pw_name="other")), self.assertRaises(RuntimeError):
            common.require_device_environment()
        with patch("pwd.getpwuid", return_value=SimpleNamespace(pw_name="vbot")), \
             patch.dict("os.environ", {}, clear=True), self.assertRaises(RuntimeError):
            common.require_device_environment()

    def test_release_pairing_is_not_guessed(self):
        with patch("importlib.metadata.version", return_value="0.0.0"), self.assertRaises(RuntimeError):
            common.load_sdk()

    def test_node_closes_on_exception(self):
        events = []

        @contextmanager
        def node(_name):
            events.append("opened")
            try:
                yield object()
            finally:
                events.append("closed")

        with patch.object(common, "require_device_environment"), \
             patch.object(common, "load_sdk", return_value=SimpleNamespace(Node=node)):
            with self.assertRaises(ValueError), common.device_node("test"):
                raise ValueError("consumer failed")
        self.assertEqual(events, ["opened", "closed"])

    def test_bounded_inbox_and_cleanup(self):
        events = []
        sdk = SimpleNamespace(SubscriberOptions=lambda **kwargs: kwargs)

        @contextmanager
        def subscriber(topic, callback, **kwargs):
            self.assertEqual(kwargs["options"]["receive_depth"], 16)
            events.append(topic)
            callback(b"sample", None)
            try:
                yield
            finally:
                events.append("closed")

        node = SimpleNamespace(create_subscriber=subscriber)
        with common.inbox(node, sdk, "/test") as receive:
            self.assertEqual(receive(time.monotonic() + 1), b"sample")
            with self.assertRaises(TimeoutError):
                receive(time.monotonic() + 0.001)
        self.assertEqual(events, ["/test", "closed"])

        @contextmanager
        def overflowing(_topic, callback, **_kwargs):
            for _ in range(17):
                callback(b"sample", None)
            yield

        with common.inbox(SimpleNamespace(create_subscriber=overflowing), sdk, "/test") as receive:
            with self.assertRaises(RuntimeError):
                receive(time.monotonic() + 1)

    def test_output_is_private_and_never_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "capture.bin"
            with common.exclusive_output(path) as output:
                output.write(b"original")
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
            with self.assertRaises(FileExistsError):
                common.exclusive_output(path)
            self.assertEqual(path.read_bytes(), b"original")

    def test_asr_filter_does_not_guess_unknown_provider(self):
        matches = recipe("audio").provider_matches
        self.assertTrue(matches(0, "all"))
        self.assertFalse(matches(0, "body"))
        self.assertFalse(matches(0, "tag"))
        self.assertTrue(matches(1, "body"))
        self.assertTrue(matches(2, "tag"))

    def test_motion_report_requires_identifier_and_body_family(self):
        match = recipe("locomotion").matches_report
        self.assertTrue(match(SimpleNamespace(ReqId=lambda: b"req", ActionFamily=lambda: 0), "req"))
        self.assertFalse(match(SimpleNamespace(ReqId=lambda: b"other", ActionFamily=lambda: 0), "req"))
        self.assertFalse(match(SimpleNamespace(ReqId=lambda: b"req", ActionFamily=lambda: 1), "req"))

    def test_rpc_no_retry_single_provider_and_cleanup(self):
        events = []

        @contextmanager
        def client(route, decoder, **kwargs):
            self.assertEqual(route, "/read")
            self.assertFalse(kwargs["options"]["allow_retry"])
            self.assertTrue(kwargs["options"]["enforce_single_provider"])
            self.assertEqual(kwargs["options"]["timeout_ms"], 1500)
            try:
                yield SimpleNamespace(call=lambda fill: SimpleNamespace(decode=lambda: "decoded"))
            finally:
                events.append("closed")

        result = common.rpc(SimpleNamespace(create_client_typed=client),
                            SimpleNamespace(ClientOptions=lambda **kwargs: kwargs), "/read", object(),
                            SimpleNamespace(GetRootAs=lambda data: data), lambda *args: 0, 1.5)
        self.assertEqual(result, "decoded")
        self.assertEqual(events, ["closed"])


if __name__ == "__main__":
    unittest.main()
