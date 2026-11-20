# Interface Definitions

<p align="center">English | <a href="README.zh-CN.md">中文</a></p>

Versioned interface definitions for the [Aorta SDK](../packages/README.md) and the
device-local ROS 2 bridge.

- `aorta/schemas/` contains the public FlatBuffers sources shared by EDU and DEV, with the `LICENSE` and
  `NOTICE` they are distributed under.
- `ros2/routes.json` lists the robot's public ROS 2 bridge routes: the Aorta key, schema and
  types, the ROS 2 name and type, the direction, QoS, service timeouts, and command rate
  limits and accepted value ranges.
- `ros2/<package>/` contains the `.msg`, `.srv` and `.action` definitions those routes use,
  the types they reference, and the constant definitions that document their values; nothing
  else. `external_packages` in `routes.json` names the standard ROS 2 packages they also need.
  `ros2/THIRD_PARTY_NOTICES.txt` lists the third-party packages and their licenses.
- `MANIFEST.json` records the current ROS 2 definition version in `ros2_bridge_version`,
  the schema pack archive/version/SHA-256, and file counts.

These files are generated for each release; do not edit them by hand. BFBS files and
generated C++ headers are in the schema pack attached to the release. Runtime availability
is documented separately in the [interface reference](../docs/interfaces/README.md) and
[compatibility matrix](../docs/compatibility.md).

## Display interface definitions

The [display guide](../docs/interfaces/system-peripherals.md#registered-image-sequences)
documents registration, status queries, playback and deletion. These files are included:

| Capability | Aorta Schema | ROS 2 interface source |
| --- | --- | --- |
| Register a sequence | [custom_images_ctrl.fbs](aorta/schemas/service/peripheral/custom_images_ctrl.fbs): `AddImagesRequest` / `AddImagesResponse` | [AddImages.srv](ros2/aorta_msgs/srv/AddImages.srv) |
| Query sequences | [custom_images_ctrl.fbs](aorta/schemas/service/peripheral/custom_images_ctrl.fbs): `GetImagesStatusRequest` / `GetImagesStatusResponse` | [GetImagesStatus.srv](ros2/aorta_msgs/srv/GetImagesStatus.srv) |
| Delete a sequence | [custom_images_ctrl.fbs](aorta/schemas/service/peripheral/custom_images_ctrl.fbs): `DelImagesRequest` / `DelImagesResponse` | [DelImages.srv](ros2/aorta_msgs/srv/DelImages.srv) |
| Full-field sequence playback | [play_emotion.fbs](aorta/schemas/service/peripheral/play_emotion.fbs): `PlayEmotionRequest` / `PlayEmotionResponse` | [PlayEmotion.srv](ros2/aorta_msgs/srv/PlayEmotion.srv) (`/display_node/play_emotion_native` on ROS) |

Direct ROS dependencies include [ShowImg.msg](ros2/aorta_msgs/msg/ShowImg.msg),
[CustomImageSequenceStatus.msg](ros2/aorta_msgs/msg/CustomImageSequenceStatus.msg),
[AortaHeader.msg](ros2/aorta_msgs/msg/AortaHeader.msg) and
[ServiceStatus.msg](ros2/aorta_msgs/msg/ServiceStatus.msg). These are ROS 2 `.srv` / `.msg`
sources, not generated `.idl` files; the standard `rosidl` toolchain generates IDL and
language bindings. The checked-in references do not replace the device's installed packages.

## Python bindings and example index

Install the matching aorta-sdk, aorta-msgs and vbot-edu-msgs wheels through the [Python SDK guide](../packages/aorta/python/README.md). The .fbs files below define fields; generated Python modules and schema_meta come from the wheels. Do not infer import paths from distribution names. This source snapshot does not include every base SDK include; application development does not require regenerating bindings.

| Capability | Schema | Python type | Recipe |
| --- | --- | --- | --- |
| Camera | [CompressedVideo.fbs](aorta/schemas/topic/foxglove_schema/CompressedVideo.fbs) | `foxglove.CompressedVideo` | [camera](../recipes/camera/README.md) |
| Audio frames | [RawAudio.fbs](aorta/schemas/topic/foxglove_schema/RawAudio.fbs) | `foxglove.RawAudio` | [audio](../recipes/audio/README.md) |
| UWB input end | [audio_done.fbs](aorta/schemas/topic/uwb/audio_done.fbs) | `aorta.uwb.AudioDoneEvent` | [audio](../recipes/audio/README.md) |
| State | [locomotion_status.fbs](aorta/schemas/topic/locomotion/locomotion_status.fbs) | `locomotion.LocomotionStatus` | [subscribe-state](../recipes/subscribe-state/README.md) |
| Body action | [lowlevel_action.fbs](aorta/schemas/service/locomotion/lowlevel_action.fbs) | `aorta.services.locomotion.LowlevelActionRequest` | [locomotion](../recipes/locomotion/README.md) |
| Action report | [action_report.fbs](aorta/schemas/topic/locomotion/action_report.fbs) | `locomotion.ActionReport` | [locomotion](../recipes/locomotion/README.md) |
| RCP goal | [execute_task.fbs](aorta/schemas/action/rcp/execute_task.fbs) | `aorta.action.rcp.ExecuteTaskGoal` | [rcp-task](../recipes/rcp-task/README.md) |
| RCP DAG | [function_input.fbs](aorta/schemas/service/rcp/function_input.fbs) | `aorta.services.rcp.DagSpec` | [rcp-task](../recipes/rcp-task/README.md) |
| Firmware query | [get_firmware_version.fbs](aorta/schemas/service/system/get_firmware_version.fbs) | `aorta.services.system.GetFirmwareVersionRequest` | [device-info](../recipes/device-info/README.md) |
| Light status | [get_light_status.fbs](aorta/schemas/service/peripheral/get_light_status.fbs) | `aorta.services.peripheral.GetLightStatusRequest` | [service-call](../recipes/service-call/README.md) |

For example, import CompressedVideo from foxglove.CompressedVideo and call GetRootAs on received bytes; generated classes with a T suffix build object-API messages. RCP DagSpec, DagNode and NodeCommand come from function_input.fbs, included by execute_task.fbs. Service requests use matching schema_meta and the SDK-provided header. A field's existence does not establish public route availability: consult the interface guide, public directory and selected device.
