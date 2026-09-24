"""Small CLI/lifetime helpers shared by the recipes, not a replacement SDK."""

import argparse
from contextlib import contextmanager
import importlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import queue
import sys
import time


SDK_VERSIONS = {"aorta-sdk": "2026.9.23", "aorta-msgs": "2026.9.23", "vbot-edu-msgs": "2026.9.24"}
MAX_SAMPLE_BYTES = 8 * 1024 * 1024


def positive_seconds(value):
    value = float(value)
    if not math.isfinite(value) or not 0 < value <= 120:
        raise argparse.ArgumentTypeError("expected finite seconds in (0, 120]")
    return value


def count_value(value):
    value = int(value)
    if not 1 <= value <= 1000:
        raise argparse.ArgumentTypeError("count must be between 1 and 1000")
    return value


def parser(description, *, stream=False):
    result = argparse.ArgumentParser(description=description)
    result.add_argument("--execute", action="store_true", help="connect to the robot; otherwise print an offline plan")
    result.add_argument("--timeout", type=positive_seconds, default=10.0, help="bounded wait in seconds (default: 10)")
    if stream:
        result.add_argument("--count", type=count_value, default=1, help="number of matching samples")
    return result


def emit(**fields):
    print(json.dumps(fields, ensure_ascii=False), flush=True)


def text(value):
    return value.decode("utf-8", "replace") if isinstance(value, bytes) else (value or "")


def load_sdk():
    for name, version in SDK_VERSIONS.items():
        actual = importlib.metadata.version(name)
        if actual != version:
            raise RuntimeError(
                f"{name}: expected {version}, found {actual}; use the documented release pairing "
                "in a dedicated venv shell with PYTHONPATH unset and PYTHONNOUSERSITE=1"
            )
    return importlib.import_module("aorta")


def require_device_environment():
    # These first recipes deliberately target device-local execution, not guessed
    # workstation router endpoints or copied session credentials.
    import pwd
    if pwd.getpwuid(os.geteuid()).pw_name != "vbot":
        raise RuntimeError("live recipes run in the robot's vbot shell; omit --execute for an offline preview")
    expected = "/opt/vita/aorta/edu/edu_session.json5"
    if os.environ.get("ZENOH_SESSION_CONFIG_URI") != expected or not os.access(expected, os.R_OK):
        raise RuntimeError("load the documented device Aorta environment before --execute")


@contextmanager
def device_node(name):
    require_device_environment()
    sdk = load_sdk()
    with sdk.Node(name) as node:
        yield sdk, node


@contextmanager
def inbox(node, sdk, topic):
    messages = queue.Queue(maxsize=16)
    overflow = queue.Queue(maxsize=1)

    def receive(payload, _context):
        try:
            if len(payload) > MAX_SAMPLE_BYTES:
                raise ValueError("sample exceeds the 8 MiB limit")
            messages.put_nowait(bytes(payload))
        except (ValueError, queue.Full):
            try:
                overflow.put_nowait(True)
            except queue.Full:
                pass

    with node.create_subscriber(topic, receive, options=sdk.SubscriberOptions(receive_depth=16)):
        def next_message(deadline):
            if not overflow.empty():
                raise RuntimeError("receive queue or sample limit exceeded; data may be incomplete")
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError("no matching sample before the deadline")
            try:
                return messages.get(timeout=remaining)
            except queue.Empty as error:
                raise TimeoutError("no matching sample before the deadline") from error
        yield next_message


def rpc(node, sdk, route, schema, response_type, fill, timeout):
    options = sdk.ClientOptions(timeout_ms=max(1, int(timeout * 1000)),
                                enforce_single_provider=True, allow_retry=False)
    with node.create_client_typed(route, response_type.GetRootAs,
                                  request_schema_meta=schema, options=options) as client:
        return client.call(fill).decode()


def byte_vector(message):
    size = message.DataLength()
    if size > MAX_SAMPLE_BYTES:
        raise ValueError("audio/video payload exceeds the 8 MiB limit")
    if size == 0:
        return b""
    # Bulk extraction avoids a Python accessor call per byte at video rates.
    from flatbuffers.compat import NumpyRequiredForThisFeature
    try:
        return message.DataAsNumpy().tobytes()
    except NumpyRequiredForThisFeature as error:
        raise RuntimeError("audio/video payload extraction requires NumPy; install the documented wheel") from error


def exclusive_output(path):
    return os.fdopen(os.open(Path(path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), "wb")


def run(main):
    try:
        return main()
    except KeyboardInterrupt:
        print("Interrupted; device operations may require their documented stopping procedure.", file=sys.stderr)
        return 130
    except Exception as error:
        print(f"{type(error).__name__}: {error}", file=sys.stderr)
        return 1
