# Interface Definitions

<p align="center">English | <a href="README.zh-CN.md">中文</a></p>

Versioned interface definitions for the [Aorta SDK](../packages/README.md) and the
device-local ROS 2 bridge.

- `aorta/schemas/` contains the public EDU FlatBuffers sources, with the `LICENSE` and
  `NOTICE` they are distributed under.
- `ros2/routes.json` lists the robot's public ROS 2 bridge routes: the Aorta key, schema and
  types, the ROS 2 name and type, the direction, QoS, service timeouts, and command rate
  limits and accepted value ranges.
- `ros2/<package>/` contains the `.msg`, `.srv` and `.action` definitions those routes use,
  the types they reference, and the constant definitions that document their values; nothing
  else. `external_packages` in `routes.json` names the standard ROS 2 packages they also need.
  `ros2/THIRD_PARTY_NOTICES.txt` lists the third-party packages and their licenses.
- `MANIFEST.json` records the schema pack version, the schema pack asset and its SHA-256
  digest in the matching `edu-sdk-*` release, and file counts.

These files are generated for each release; do not edit them by hand. BFBS files and
generated C++ headers are in the schema pack attached to the release. Runtime availability
is documented separately in the [interface reference](../docs/interfaces/README.md) and
[compatibility matrix](../release/compatibility.md).

## Python bindings and example index

Install the matching aorta-sdk, aorta-msgs and vbot-edu-msgs wheels through the [Python SDK guide](../packages/aorta/python/README.md). The .fbs files below define fields; generated Python modules and schema_meta come from the wheels. Do not infer import paths from distribution names. This source snapshot does not include every base SDK include; application development does not require regenerating bindings.

| Capability | Schema | Python type | Recipe |
| --- | --- | --- | --- |
| Camera | [CompressedVideo.fbs](aorta/schemas/topic/foxglove_schema/CompressedVideo.fbs) | `foxglove.CompressedVideo` | [camera](../recipes/camera/README.md) |
| Audio frames | [RawAudio.fbs](aorta/schemas/topic/foxglove_schema/RawAudio.fbs) | `foxglove.RawAudio` | [audio](../recipes/audio/README.md) |
| ASR | [asr_result.fbs](aorta/schemas/topic/speech/asr_result.fbs) | `aorta.topic.speech.AsrResult` | [audio](../recipes/audio/README.md) |
| UWB input end | [audio_done.fbs](aorta/schemas/topic/uwb/audio_done.fbs) | `aorta.uwb.AudioDoneEvent` | [audio](../recipes/audio/README.md) |
| State | [locomotion_status.fbs](aorta/schemas/topic/locomotion/locomotion_status.fbs) | `locomotion.LocomotionStatus` | [subscribe-state](../recipes/subscribe-state/README.md) |
| Body action | [lowlevel_action.fbs](aorta/schemas/service/locomotion/lowlevel_action.fbs) | `aorta.services.locomotion.LowlevelActionRequest` | [locomotion](../recipes/locomotion/README.md) |
| Action report | [action_report.fbs](aorta/schemas/topic/locomotion/action_report.fbs) | `locomotion.ActionReport` | [locomotion](../recipes/locomotion/README.md) |
| RCP goal | [execute_task.fbs](aorta/schemas/action/rcp/execute_task.fbs) | `aorta.action.rcp.ExecuteTaskGoal` | [rcp-task](../recipes/rcp-task/README.md) |
| RCP DAG | [function_input.fbs](aorta/schemas/service/rcp/function_input.fbs) | `aorta.services.rcp.DagSpec` | [rcp-task](../recipes/rcp-task/README.md) |
| Firmware query | [get_firmware_version.fbs](aorta/schemas/service/system/get_firmware_version.fbs) | `aorta.services.system.GetFirmwareVersionRequest` | [device-info](../recipes/device-info/README.md) |
| Light status | [get_light_status.fbs](aorta/schemas/service/peripheral/get_light_status.fbs) | `aorta.services.peripheral.GetLightStatusRequest` | [service-call](../recipes/service-call/README.md) |

For example, import CompressedVideo from foxglove.CompressedVideo and call GetRootAs on received bytes; generated classes with a T suffix build object-API messages. RCP DagSpec, DagNode and NodeCommand come from function_input.fbs, included by execute_task.fbs. Service requests use matching schema_meta and the SDK-provided header. A field's existence does not establish public route availability: consult the interface guide, public directory and selected device.
