"""Device-local subscription adapter with bounded queues and explicit cleanup."""

from contextlib import ExitStack, contextmanager
import importlib
import importlib.metadata
import os
import queue
import time

from health_monitor.wire import validator
from health_monitor.errors import ApplicationError

ROUTES = {"state": ("/locomotion/status", "locomotion.LocomotionStatus"),
          "battery": ("/bms_state", "bms.BmsState"),
          "system": ("/system/sm_status", "sm.SmStatus")}
VERSIONS = {"aorta-sdk": "2026.10.12", "aorta-msgs": "2026.10.12", "vbot-edu-msgs": "2026.10.13"}


def check_device():
    import pwd
    if pwd.getpwuid(os.geteuid()).pw_name != "vbot":
        raise ApplicationError("environment", "device_user_required", "Run live execution in the device vbot shell.")
    expected = "/opt/vita/aorta/edu/edu_session.json5"
    if os.environ.get("ZENOH_SESSION_CONFIG_URI") != expected:
        raise ApplicationError("environment", "session_config_not_set", "Load the documented device Aorta environment.")
    if not os.access(expected, os.R_OK):
        raise ApplicationError("environment", "session_config_not_readable", "Check that the documented Aorta session configuration is readable.")


def load_sdk():
    for name, expected in VERSIONS.items():
        try:
            actual = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            raise ApplicationError("sdk", "sdk_not_installed", "Use the application venv and install its pinned requirements.") from None
        if actual != expected:
            raise ApplicationError("sdk", "sdk_version_mismatch", "Use the application's pinned SDK requirements in its venv.")
    try:
        for stream in ROUTES:
            validator(stream)
        return importlib.import_module("aorta")
    except (ImportError, OSError, ValueError, RuntimeError):
        raise ApplicationError("sdk", "sdk_load_failed", "Check the pinned SDK, generated message bindings and BFBS files in the application venv.") from None


def decode(stream, payload):
    validator(stream).verify(payload)
    module = importlib.import_module(ROUTES[stream][1])
    value = getattr(module, ROUTES[stream][1].rsplit(".", 1)[1]).GetRootAs(payload, 0)
    if stream == "battery":
        return {"soc_percent": value.SocPercent(), "voltage_v": value.VoltageMv() / 1000}, value.SensorTimestampNs()
    if stream == "state":
        return {"heartbeat_seq": value.HeartbeatSeq(), "posture": value.Posture(), "motion": value.Motion()}, value.StampNs()
    return {"heartbeat_seq": value.HeartbeatSeq(), "state_id": value.StateId(),
            "severity": value.Severity()}, value.SensorTimestampNs()


@contextmanager
def subscription(streams):
    check_device()
    sdk = load_sdk()
    inbox = queue.Queue(maxsize=64)
    overflow = queue.Queue(maxsize=1)

    def callback(stream):
        def receive(payload, _context):
            received_at = time.monotonic()
            try:
                if len(payload) > 1024 * 1024:
                    raise ValueError("telemetry sample too large")
                inbox.put_nowait((stream, bytes(payload), received_at))
            except (ValueError, queue.Full):
                try:
                    overflow.put_nowait(True)
                except queue.Full:
                    pass
        return receive

    with ExitStack() as stack:
        try:
            node = stack.enter_context(sdk.Node("vbot_health_monitor"))
            subscribers = []
            for stream in streams:
                subscribers.append(stack.enter_context(node.create_subscriber(ROUTES[stream][0], callback(stream),
                    options=sdk.SubscriberOptions(receive_depth=16))))
        except Exception:
            raise ApplicationError("subscription", "subscription_setup_failed",
                                   "Check the device Aorta environment and selected routes; use bounded read-only diagnostics.") from None

        def check_loss():
            if not overflow.empty():
                raise ApplicationError("subscription", "telemetry_queue_overflow",
                                       "A telemetry queue overflow stopped the monitor; inspect processing load before restarting.")
            if any(subscriber.dropped_count() for subscriber in subscribers):
                raise ApplicationError("subscription", "sdk_samples_dropped",
                                       "SDK reported dropped telemetry; inspect processing load and subscription settings.")

        def receive(timeout):
            check_loss()
            try:
                item = inbox.get(timeout=timeout)
            except queue.Empty:
                check_loss()
                return None
            check_loss()
            return item
        yield receive
