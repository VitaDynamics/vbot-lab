"""Explicit release-wheel tests: serialization only, no Node or device session."""

import importlib
from contextlib import contextmanager, redirect_stdout
import io
import json
from pathlib import Path
import struct
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "blueprints/health-monitor"))
from recipes.common import load_sdk


def recipe(slug):
    return importlib.import_module("recipes." + slug + ".main")


class ReleaseSDKTests(unittest.TestCase):
    def monitor_messages(self):
        from aorta.sys.AortaHeader import AortaHeaderT
        from bms.BmsState import BmsStateT
        from bms.Version3 import Version3T
        from bms.TempArray16 import TempArray16T
        from bms.VoltageArray16 import VoltageArray16T
        from locomotion.LocomotionStatus import LocomotionStatusT
        from sm.SmStatus import SmStatusT
        from sm.StatePathEntry import StatePathEntryT
        from sm.KeyValue import KeyValueT
        header = AortaHeaderT(publisherNode="wire-test", sequence=1)
        messages = {
            "state": LocomotionStatusT(aortaHeader=header, heartbeatSeq=1, currentAction="idle", source="test", stampNs=1),
            "battery": BmsStateT(aortaHeader=header, sensorTimestampNs=1, vendor="test", serialNumber="sample",
                                 protocolVersion=Version3T(1, 2, 3), hwVersion=Version3T(), swVersion=Version3T(),
                                 socPercent=80, voltageMv=42000, temperaturesC=TempArray16T([25] * 16),
                                 voltagesSingleMv=VoltageArray16T([3500] * 16)),
            "system": SmStatusT(aortaHeader=header, sensorTimestampNs=1, heartbeatSeq=1, stateName="idle",
                                activeStatePath=[StatePathEntryT(1, "ready"), StatePathEntryT(2, "idle")],
                                message="test", data=[KeyValueT("mode", "observe"), KeyValueT("state", "idle")]),
        }
        return {name: self.sdk.FlatbuffersActionCodec.serialize(value) for name, value in messages.items()}

    def test_monitor_full_schema_and_legal_zero_defaults(self):
        from health_monitor.runtime import decode
        from health_monitor.wire import validator
        for stream, payload in self.monitor_messages().items():
            with self.subTest(stream=stream):
                self.assertEqual(decode(stream, payload)[1], 1)
        for stream, root in (("state", "locomotion.LocomotionStatus"), ("battery", "bms.BmsState"), ("system", "sm.SmStatus")):
            value = getattr(importlib.import_module(root), root.split(".")[-1] + "T")()
            data, stamp = decode(stream, self.sdk.FlatbuffersActionCodec.serialize(value))
            self.assertEqual(stamp, 0)
            self.assertEqual(data["soc_percent"] if stream == "battery" else data["heartbeat_seq"], 0)
            self.assertTrue(validator(stream).objects)

    def test_monitor_rejects_corrupt_root_table_fields_strings_and_header(self):
        from health_monitor.runtime import decode
        from health_monitor.wire import Buffer
        for stream, good in self.monitor_messages().items():
            reader = Buffer(good)
            table = reader.table(reader.target(0))
            root, vtable, _, size = table
            field = reader.field(table, 1, 8, 8)
            text = reader.target(reader.field(table, {"state": 4, "battery": 4, "system": 6}[stream]))
            header = reader.target(reader.field(table, 0))
            changes = ((0, "I", 0), (0, "I", len(good) + 4), (0, "I", 5), (root, "i", 0),
                       (root, "i", 0x7fffffff), (vtable, "H", 3), (vtable + 2, "H", 3),
                       (vtable + 6, "H", 1), (vtable + 6, "H", size - 1),
                       (text, "I", 0xffffffff), (text + 4 + reader.integer(text), "B", 1),
                       (header, "i", 0))
            # Trailing alignment padding may be omitted legally. Truncate a
            # referenced string's terminator instead of arbitrary last bytes.
            bad_inputs = [b"", b"\0" * 8, good[:3], good[:text + 4 + reader.integer(text)]]
            for position, kind, value in changes:
                bad = bytearray(good)
                struct.pack_into("<" + kind, bad, position, value)
                bad_inputs.append(bytes(bad))
            for index, bad in enumerate(bad_inputs):
                with self.subTest(stream=stream, mutation=index), self.assertRaises(ValueError):
                    decode(stream, bad)
            self.assertIsNotNone(field)

    def test_monitor_rejects_broken_vectors_and_nested_tables(self):
        from health_monitor.runtime import decode
        from health_monitor.wire import Buffer
        good = self.monitor_messages()["system"]
        reader = Buffer(good)
        root = reader.table(reader.target(0))
        for field in (7, 9):
            vector = reader.target(reader.field(root, field))
            child = reader.target(vector + 4)
            for position, kind, value in ((vector, "I", 0xffffffff), (vector + 4, "I", 0), (child, "i", 0)):
                bad = bytearray(good)
                struct.pack_into("<" + kind, bad, position, value)
                with self.subTest(field=field, position=position), self.assertRaises(ValueError):
                    decode("system", bad)

    def test_monitor_schema_failure_is_not_treated_as_a_bad_sample(self):
        from health_monitor import runtime, wire
        wire.validator.cache_clear()
        try:
            with patch.object(wire.importlib, "import_module", return_value=SimpleNamespace(ROOT_TYPE_NAME="wrong.Root")), \
                 self.assertRaises(RuntimeError) as caught:
                runtime.load_sdk()
            self.assertEqual(caught.exception.stage, "sdk")
            self.assertEqual(caught.exception.error_code, "sdk_load_failed")
        finally:
            wire.validator.cache_clear()

    def test_monitor_verifier_budgets_are_enforced(self):
        from health_monitor import wire
        schema = wire.validator("state")
        payload = self.monitor_messages()["state"]
        for name, value in (("MAX_BYTES", 8), ("MAX_DEPTH", 0), ("MAX_OBJECTS", 0)):
            with self.subTest(limit=name), patch.object(wire, name, value), self.assertRaises(ValueError):
                schema.verify(payload)

    def test_malformed_monitor_input_cannot_make_the_application_succeed_or_refresh_data(self):
        from health_monitor import main as monitor_app
        good = self.monitor_messages()
        for initial_valid in (False, True):
            clock = [0.0]
            events = iter(([(*item, 0.0) for item in good.items()] if initial_valid else []) +
                          [(stream, b"\0" * 8, 3.5) for stream in good])
            @contextmanager
            def subscription(_):
                def receive(timeout):
                    try:
                        item = next(events)
                    except StopIteration:
                        clock[0] = 4.1
                        return None
                    clock[0] = max(clock[0] + 0.01, item[2])
                    return item
                yield receive
            with self.subTest(initial_valid=initial_valid), patch.object(monitor_app, "subscription", side_effect=subscription), \
                 patch.object(monitor_app.time, "monotonic", side_effect=lambda: clock[0]), redirect_stdout(io.StringIO()) as output:
                self.assertEqual(monitor_app.main(["--execute", "--duration", "4"]), 1)
            final = json.loads(output.getvalue().splitlines()[-1])
            self.assertFalse(final["all_streams_receiving"])
            for value in final["streams"].values():
                self.assertEqual(value["invalid"], 1)
                self.assertEqual(value["samples"], int(initial_valid))
                self.assertEqual(value["status"], "stale" if initial_valid else "waiting_data")

    def test_health_monitor_decoder_matches_published_sdk_types(self):
        from health_monitor.runtime import decode
        from bms.BmsState import BmsStateT
        from sm.SmStatus import SmStatusT
        from locomotion.LocomotionStatus import LocomotionStatusT
        pack = self.sdk.FlatbuffersActionCodec.serialize
        cases = (("battery", BmsStateT(socPercent=75, voltageMv=42000, sensorTimestampNs=123)),
                 ("state", LocomotionStatusT(heartbeatSeq=7, posture=2, stampNs=123)),
                 ("system", SmStatusT(heartbeatSeq=8, stateId=4, sensorTimestampNs=123)))
        for stream, value in cases:
            data, timestamp = decode(stream, pack(value))
            self.assertEqual(timestamp, 123)
            self.assertIsInstance(data, dict)
            if stream == "battery":
                self.assertEqual(data, {"soc_percent": 75, "voltage_v": 42})
            else:
                self.assertEqual(data["heartbeat_seq"], 7 if stream == "state" else 8)

    @classmethod
    def setUpClass(cls):
        cls.sdk = load_sdk()
        cls.guard = patch.object(cls.sdk, "Node", side_effect=AssertionError("offline tests must not open Node"))
        cls.guard.start()

    @classmethod
    def tearDownClass(cls):
        cls.guard.stop()

    def pack_request(self, fill):
        import flatbuffers
        from aorta.header import build_aorta_header
        builder = flatbuffers.Builder(256)
        header = build_aorta_header(builder, sequence=7, publish_stamp_ns=123, publisher_node="offline_test")
        builder.Finish(fill(builder, header))
        return bytes(builder.Output())

    def test_service_requests_keep_sdk_header_and_generated_fields(self):
        import get_firmware_version_schema_meta as firmware
        import get_light_status_schema_meta as light
        import lowlevel_action_schema_meta as motion
        from aorta.services.system.GetFirmwareVersionRequest import GetFirmwareVersionRequest
        from aorta.services.peripheral.GetLightStatusRequest import GetLightStatusRequest
        from aorta.services.locomotion.LowlevelActionRequest import LowlevelActionRequest
        request = GetFirmwareVersionRequest.GetRootAs(self.pack_request(recipe("device-info").request_fill(firmware, 3)), 0)
        self.assertEqual(request.TargetDeviceType(), 3)
        self.assertEqual(request.IdsLength(), 0)
        self.assertEqual(request.AortaHeader().Sequence(), 7)
        request = GetLightStatusRequest.GetRootAs(self.pack_request(recipe("service-call").request_fill(light)), 0)
        self.assertEqual(request.AortaHeader().Sequence(), 7)
        request = LowlevelActionRequest.GetRootAs(self.pack_request(recipe("locomotion").request_fill(motion, 1, "test-request")), 0)
        self.assertEqual(request.TargetState(), 1)
        self.assertEqual(request.Mode(), 1)
        self.assertEqual(request.ReqId(), b"test-request")
        self.assertEqual(request.AortaHeader().Sequence(), 7)

    def test_stand_uses_manual_mode_with_explicit_traction_override(self):
        import set_run_mode_schema_meta as schema
        from aorta.services.locomotion.SetRunModeRequest import SetRunModeRequest
        from aorta.services.locomotion.RunMode import RunMode
        module = recipe("locomotion")
        request = SetRunModeRequest.GetRootAs(self.pack_request(
            module.stand_request_fill(schema, "stand-id")), 0)
        self.assertEqual(request.Mode(), RunMode.MANUAL)
        self.assertEqual(request.TargetState(), 1)
        self.assertEqual(request.ReqId(), b"stand-id")
        self.assertIsNotNone(request.TractionUserParam())
        self.assertFalse(request.TractionUserParam().IsUserParam())
        self.assertEqual(request.AortaHeader().Sequence(), 7)
        self.assertEqual(module.MODES["lie-down"], "SAFE_LAYDOWN_SEQUENCE")

    def test_rcp_dag_union_and_dependencies_round_trip(self):
        from aorta.action.rcp.ExecuteTaskGoal import ExecuteTaskGoalT
        from aorta.action.rcp.ExecuteTaskResult import ExecuteTaskResultT
        from aorta.action.rcp.ExecuteTaskFeedbackData import ExecuteTaskFeedbackDataT
        from aorta.services.rcp.DagInput import DagInput
        from aorta.services.rcp.NodeCommand import NodeCommand
        codec = self.sdk.FlatbuffersActionCodec(goal=ExecuteTaskGoalT, result=ExecuteTaskResultT,
                                               feedback=ExecuteTaskFeedbackDataT)
        goal = ExecuteTaskGoalT.InitFromPackedBuf(codec.serialize(recipe("rcp-task").make_goal(500, "task-test")), 0)
        self.assertEqual(goal.inputType, DagInput.DagSpec)
        self.assertEqual(goal.input.taskId, b"task-test")
        self.assertEqual(len(goal.input.nodes), 2)
        self.assertEqual(goal.input.nodes[1].dependencies, [b"first"])
        for node in goal.input.nodes:
            self.assertEqual(node.commandType, NodeCommand.SleepCommand)
            self.assertEqual(node.command.durationMs, 500)
        wrapped = codec.build_send_goal_request("test-goal", codec.serialize(recipe("rcp-task").make_goal(500, "task-test")))
        self.assertEqual(codec.decode_send_goal_request_goal_id(wrapped), "test-goal")
        self.assertEqual(codec.decode_goal(wrapped).input.taskId, b"task-test")

    @contextmanager
    def fake_device(self, node=None):
        yield self.sdk, node

    def test_family_schema_decoders_use_generated_release_types(self):
        from foxglove.PointCloud import PointCloudT
        for family in ("sensors", "perception", "system-peripherals", "slam"):
            module = recipe(family)
            for stream, (_, root) in module.ROUTES.items():
                with self.subTest(family=family, stream=stream):
                    schema = importlib.import_module(root)
                    name = root.rsplit(".", 1)[1]
                    value = getattr(schema, name + "T")()
                    if isinstance(value, PointCloudT):
                        value.pointStride = 12
                        value.data = bytes(24)
                    payload = self.sdk.FlatbuffersActionCodec.serialize(value)
                    decoded = getattr(schema, name).GetRootAs(payload, 0)
                    fields = module.summarize(stream, decoded)
                    self.assertIsInstance(fields, dict)
                    if stream == "detections":
                        self.assertEqual(fields["person_boxes"], 0)
                        self.assertEqual(fields["detections"], [])
                    if stream == "points":
                        self.assertEqual(fields["point_count"], 2)
                    if stream == "odometry":
                        self.assertIsNone(fields["body_in_map"])

    def test_stand_waits_for_activation_then_observes_posture(self):
        from locomotion.LocomotionStatus import LocomotionStatusT
        from aorta.topic.task.TaskReport import TaskReportT
        from aorta.topic.task.TaskResultPayload import TaskResultPayload
        from aorta.topic.task.LocomotionTaskResult import LocomotionTaskResultT
        from aorta.services.locomotion.SetRunModeResponse import SetRunModeResponseT, SetRunModeResponse
        module = recipe("locomotion")
        pack = self.sdk.FlatbuffersActionCodec.serialize
        for scenario in ("success", "rejected", "missing-report", "wrong-posture"):
            with self.subTest(scenario=scenario):
                states = [pack(LocomotionStatusT(heartbeatSeq=i, posture=2)) for i in (1, 2)]
                states += [pack(LocomotionStatusT(heartbeatSeq=i,
                    posture=2 if scenario == "wrong-posture" else 1,
                    currentAction="RL_TROT")) for i in (3, 4, 5)]
                reports = [pack(TaskReportT(reqId="unrelated")),
                           pack(TaskReportT(reqId="vbot-lab-test-id",
                                resultType=TaskResultPayload.LocomotionTaskResult,
                                result=LocomotionTaskResultT(stage=1)))]
                if scenario != "missing-report":
                    reports.append(pack(TaskReportT(reqId="vbot-lab-test-id",
                        status=1 if scenario == "rejected" else 0,
                        resultType=TaskResultPayload.LocomotionTaskResult,
                        result=LocomotionTaskResultT(stage=2))))
                @contextmanager
                def inbox(_node, _sdk, topic):
                    samples = states if topic == "/locomotion/status" else reports
                    def receive(_deadline):
                        if not samples:
                            raise TimeoutError("no matching sample")
                        return samples.pop(0)
                    yield receive
                response = SetRunModeResponse.GetRootAs(pack(SetRunModeResponseT()), 0)
                with patch.object(module, "device_node", side_effect=lambda _: self.fake_device()), \
                     patch.object(module, "inbox", side_effect=inbox), \
                     patch.object(module, "rpc", return_value=response) as rpc, \
                     patch.object(module.uuid, "uuid4", return_value=SimpleNamespace(hex="test-id")), \
                     redirect_stdout(io.StringIO()) as output:
                    args = ["--mode", "stand", "--confirm-motion", "--execute"]
                    if scenario in ("missing-report", "wrong-posture"):
                        with self.assertRaises(TimeoutError):
                            module.main(args)
                    else:
                        self.assertEqual(module.main(args), 1 if scenario == "rejected" else 0)
                self.assertEqual(rpc.call_count, 1)
                self.assertEqual(rpc.call_args.args[2], module.STAND_ROUTE)
                last = json.loads(output.getvalue().splitlines()[-1])
                if scenario == "success":
                    self.assertTrue(last["observation_only"])
                    self.assertFalse(last["completion"])

    def test_motion_acknowledgement_is_not_completion(self):
        from locomotion.LocomotionStatus import LocomotionStatusT
        from locomotion.ActionReport import ActionReportT
        from aorta.services.locomotion.LowlevelActionResponse import LowlevelActionResponseT, LowlevelActionResponse
        module = recipe("locomotion")
        pack = self.sdk.FlatbuffersActionCodec.serialize
        events = []
        states = [pack(LocomotionStatusT(heartbeatSeq=i, posture=1)) for i in (1, 2)]
        reports = [pack(ActionReportT(reqId="unrelated")), pack(ActionReportT(reqId="vbot-lab-test-id"))]

        @contextmanager
        def inbox(_node, _sdk, topic):
            events.append("subscribe:" + topic)
            samples = states if topic == "/locomotion/status" else reports
            def receive(_deadline):
                if not samples:
                    raise TimeoutError("no report")
                return samples.pop(0)
            yield receive
            events.append("close:" + topic)

        response = LowlevelActionResponse.GetRootAs(pack(LowlevelActionResponseT()), 0)
        def call(*_args):
            events.append("send")
            return response

        with patch.object(module, "device_node", side_effect=lambda _: self.fake_device()), \
             patch.object(module, "inbox", side_effect=inbox), patch.object(module, "rpc", side_effect=call) as rpc, \
             patch.object(module.uuid, "uuid4", return_value=SimpleNamespace(hex="test-id")), \
             redirect_stdout(io.StringIO()) as output:
            self.assertEqual(module.main(["--mode", "lie-down", "--confirm-motion", "--execute"]), 0)
        self.assertEqual(rpc.call_count, 1)
        self.assertEqual(events[:3], ["subscribe:/locomotion/action_report", "subscribe:/locomotion/status", "send"])
        lines = [json.loads(line) for line in output.getvalue().splitlines()]
        self.assertFalse(lines[1]["completion"])
        self.assertEqual(lines[-1]["request_id"], "vbot-lab-test-id")

        states[:] = [pack(LocomotionStatusT(heartbeatSeq=i, posture=1)) for i in (3, 4)]
        with patch.object(module, "device_node", side_effect=lambda _: self.fake_device()), \
             patch.object(module, "inbox", side_effect=inbox), patch.object(module, "rpc", side_effect=call) as rpc, \
             redirect_stdout(io.StringIO()) as output, self.assertRaises(TimeoutError):
            module.main(["--mode", "lie-down", "--confirm-motion", "--execute"])
        self.assertEqual(rpc.call_count, 1)
        self.assertEqual(json.loads(output.getvalue().splitlines()[-1])["outcome"], "unknown")

    def test_rcp_success_cancel_and_timeout_cleanup(self):
        from aorta.action.rcp.ExecuteTaskResult import ExecuteTaskResultT
        from aorta.action.rcp.ExecuteTaskFeedbackData import ExecuteTaskFeedbackDataT
        module = recipe("rcp-task")
        pack = self.sdk.FlatbuffersActionCodec.serialize
        for mode in ("success", "cancel", "cancel-race", "timeout", "admission-timeout"):
            with self.subTest(mode=mode):
                events = []
                state = {"cancelled": False, "goal_id": None}

                def cancel():
                    events.append("cancel")
                    if mode == "cancel-race":
                        raise RuntimeError("ALREADY_TERMINAL")
                    state["cancelled"] = True
                    return SimpleNamespace(accepted=True, status=self.sdk.ActionStatus.CANCELING)

                def wait_result(timeout):
                    events.append("wait")
                    if not state["cancelled"] and mode in ("cancel", "timeout"):
                        raise self.sdk.TimeoutError("not terminal")
                    return SimpleNamespace(status=self.sdk.ActionStatus.CANCELED if state["cancelled"] else self.sdk.ActionStatus.SUCCEEDED,
                                           result=pack(ExecuteTaskResultT(durationMs=1000, errorCategory=0)), message="done")

                @contextmanager
                def subscribe(callback):
                    callback(SimpleNamespace(goal_id=state["goal_id"], data=pack(ExecuteTaskFeedbackDataT(
                        currentNode="first", completedNodes=0, totalNodes=2, progressPct=0))))
                    try:
                        yield
                    finally:
                        events.append("close-feedback")

                def send(goal_id, payload):
                    state["goal_id"] = goal_id
                    events.append("send")
                    self.assertIsInstance(payload, bytes)
                    if mode == "admission-timeout":
                        raise self.sdk.TimeoutError("lost admission")
                    return SimpleNamespace(subscribe_feedback=subscribe, wait_result=wait_result, cancel=cancel)

                @contextmanager
                def client(*_args, **_kwargs):
                    try:
                        yield SimpleNamespace(info=lambda: SimpleNamespace(supports_cancel=True), send_goal_with_id=send)
                    finally:
                        events.append("close-client")

                ticks = iter(i * 0.25 for i in range(100))
                args = ["--execute", "--timeout", "1"]
                if mode in ("cancel", "cancel-race"):
                    args += ["--cancel-after", "0.1"]
                with patch.object(module, "device_node", side_effect=lambda _: self.fake_device(SimpleNamespace(create_action_client=client))), \
                     patch.object(module.time, "monotonic", side_effect=lambda: next(ticks)), redirect_stdout(io.StringIO()) as output:
                    if mode in ("timeout", "admission-timeout"):
                        with self.assertRaises((TimeoutError, self.sdk.TimeoutError)):
                            module.main(args)
                    else:
                        self.assertEqual(module.main(args), 0)
                self.assertEqual(events.count("send"), 1)
                self.assertEqual(events.count("cancel"), 1 if mode in ("cancel", "cancel-race", "timeout") else 0)
                self.assertIn("close-client", events)
                if mode != "admission-timeout":
                    self.assertIn("close-feedback", events)
                self.assertNotIn("goal_secret", output.getvalue())

    def test_audio_asr_and_uwb_frame_decoding(self):
        from aorta.topic.speech.AsrResult import AsrResultT
        from foxglove.RawAudio import RawAudioT
        from foxglove.Time import TimeT
        module = recipe("audio")
        pack = self.sdk.FlatbuffersActionCodec.serialize
        for source, messages, expected in (
                ("asr", [AsrResultT(provider=0, text="unknown"), AsrResultT(provider=2, text="hello")], "TAG"),
                ("uwb", [RawAudioT(format="adpcm", sampleRate=8000, numberOfChannels=1,
                                  data=[1, 2, 3], timestamp=TimeT(sec=1, nsec=2))], "adpcm")):
            samples = iter(pack(message) for message in messages)
            @contextmanager
            def inbox(*_args):
                yield lambda _deadline: next(samples)
            args = ["--source", source, "--execute", "--consent"]
            if source == "asr":
                args += ["--provider", "tag"]
            with patch.object(module, "device_node", side_effect=lambda _: self.fake_device()), \
                 patch.object(module, "inbox", side_effect=inbox), redirect_stdout(io.StringIO()) as output:
                self.assertEqual(module.main(args), 0)
            data = json.loads(output.getvalue())
            self.assertEqual(data["provider" if source == "asr" else "format"], expected)

    def test_camera_metadata_decode_uses_generated_binding(self):
        from foxglove.CompressedVideo import CompressedVideoT
        module = recipe("camera")
        payload = self.sdk.FlatbuffersActionCodec.serialize(CompressedVideoT(format="h265", frameId="left", data=[1, 2, 3]))
        @contextmanager
        def inbox(*_args):
            yield lambda _deadline: payload
        with patch.object(module, "device_node", side_effect=lambda _: self.fake_device()), \
             patch.object(module, "inbox", side_effect=inbox), redirect_stdout(io.StringIO()) as output:
            self.assertEqual(module.main(["--execute"]), 0)
        data = json.loads(output.getvalue())
        self.assertEqual(data["frame_id"], "left")
        self.assertEqual(data["bytes"], 3)

    def test_bulk_video_payload_and_missing_numpy(self):
        from flatbuffers.compat import import_numpy
        from foxglove.CompressedVideo import CompressedVideo, CompressedVideoT
        from recipes.common import byte_vector
        payload = self.sdk.FlatbuffersActionCodec.serialize(
            CompressedVideoT(format="h265", data=[1, 2, 255]))
        message = CompressedVideo.GetRootAs(payload, 0)
        if import_numpy() is None:
            with self.assertRaisesRegex(RuntimeError, "requires NumPy"):
                byte_vector(message)
        else:
            with patch.object(CompressedVideo, "Data", side_effect=AssertionError("no byte-by-byte loop")):
                self.assertEqual(byte_vector(message), b"\x01\x02\xff")

    def test_sample_bindings_used_by_recipes_exist(self):
        classes = {
            "foxglove.CompressedVideo": ("Format", "FrameId", "Timestamp", "DataLength", "Data"),
            "foxglove.RawAudio": ("Format", "SampleRate", "NumberOfChannels", "UserInteractionContext", "Timestamp", "Data"),
            "aorta.topic.speech.AsrResult": ("Text", "Provider"),
            "aorta.uwb.AudioDoneEvent": ("TimestampNs", "UserInteractionContext"),
            "locomotion.LocomotionStatus": ("HeartbeatSeq", "Posture", "Motion", "StampNs", "CurrentAction"),
            "locomotion.ActionReport": ("ReqId", "ActionFamily", "TerminalStatus", "ErrorCode", "Reason"),
            "aorta.services.peripheral.GetLightStatusResponse": ("CurrentRed", "CurrentGreen", "CurrentBlue", "CurrentBrightness", "CurrentMode", "Status", "IsEnabled", "Message"),
        }
        for name, getters in classes.items():
            root = getattr(importlib.import_module(name), name.rsplit(".", 1)[1])
            for getter in ("GetRootAs", *getters):
                self.assertTrue(callable(getattr(root, getter)), name + "." + getter)


if __name__ == "__main__":
    unittest.main()
