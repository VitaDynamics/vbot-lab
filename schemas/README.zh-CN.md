# Interface Definitions

<p align="center"><a href="README.md">English</a> | 中文</p>

为 [Aorta SDK](../packages/README.zh-CN.md)及设备本地 ROS 2 bridge 提供版本化接口定义。

- `aorta/schemas/` 包含对 EDU 开放的 FlatBuffers 源文件，以及其分发所依据的 `LICENSE` 和
  `NOTICE`。
- `ros2/routes.json` 列出机器人公开的 ROS 2 bridge 路由：Aorta key、schema 与类型，
  ROS 2 名称与类型，方向，QoS，服务超时，以及指令限速和可接受的取值范围。
- `ros2/<package>/` 只包含这些路由使用的 `.msg`、`.srv` 和 `.action` 定义、它们引用的类型，
  以及说明取值的常量定义。`routes.json` 中的 `external_packages` 列出还需要的 ROS 2 标准包。
  `ros2/THIRD_PARTY_NOTICES.txt` 列出第三方包及其许可证。
- `MANIFEST.json` 记录 schema pack 版本、对应 `edu-sdk-*` release 中的 schema pack 资产及其
  SHA-256 摘要，以及文件统计。

这些文件随每个版本生成，请勿手工修改。BFBS 文件和生成的 C++ 头文件位于 release 附带的
schema pack 中。运行时可用性另见[接口参考](../docs/interfaces/README.zh-CN.md)及
[兼容矩阵](../release/compatibility.zh-CN.md)。

## Python 绑定与示例索引

从 [Python SDK 指南](../packages/aorta/python/README.zh-CN.md)安装配套的 aorta-sdk、aorta-msgs 和 vbot-edu-msgs wheel。下面的 .fbs 是字段定义，生成的 Python 模块与 schema_meta 来自 wheel；不要根据发行包名猜测 import 路径。源码快照不包含所有基础 SDK include，应用开发无需自行重新生成绑定。

| 能力 | Schema | Python 类型 | Recipe |
| --- | --- | --- | --- |
| 相机 | [CompressedVideo.fbs](aorta/schemas/topic/foxglove_schema/CompressedVideo.fbs) | `foxglove.CompressedVideo` | [camera](../recipes/camera/README.zh-CN.md) |
| 音频帧 | [RawAudio.fbs](aorta/schemas/topic/foxglove_schema/RawAudio.fbs) | `foxglove.RawAudio` | [audio](../recipes/audio/README.zh-CN.md) |
| ASR | [asr_result.fbs](aorta/schemas/topic/speech/asr_result.fbs) | `aorta.topic.speech.AsrResult` | [audio](../recipes/audio/README.zh-CN.md) |
| UWB 输入结束 | [audio_done.fbs](aorta/schemas/topic/uwb/audio_done.fbs) | `aorta.uwb.AudioDoneEvent` | [audio](../recipes/audio/README.zh-CN.md) |
| 状态 | [locomotion_status.fbs](aorta/schemas/topic/locomotion/locomotion_status.fbs) | `locomotion.LocomotionStatus` | [subscribe-state](../recipes/subscribe-state/README.zh-CN.md) |
| 本体动作 | [lowlevel_action.fbs](aorta/schemas/service/locomotion/lowlevel_action.fbs) | `aorta.services.locomotion.LowlevelActionRequest` | [locomotion](../recipes/locomotion/README.zh-CN.md) |
| 动作报告 | [action_report.fbs](aorta/schemas/topic/locomotion/action_report.fbs) | `locomotion.ActionReport` | [locomotion](../recipes/locomotion/README.zh-CN.md) |
| RCP goal | [execute_task.fbs](aorta/schemas/action/rcp/execute_task.fbs) | `aorta.action.rcp.ExecuteTaskGoal` | [rcp-task](../recipes/rcp-task/README.zh-CN.md) |
| RCP DAG | [function_input.fbs](aorta/schemas/service/rcp/function_input.fbs) | `aorta.services.rcp.DagSpec` | [rcp-task](../recipes/rcp-task/README.zh-CN.md) |
| 固件查询 | [get_firmware_version.fbs](aorta/schemas/service/system/get_firmware_version.fbs) | `aorta.services.system.GetFirmwareVersionRequest` | [device-info](../recipes/device-info/README.zh-CN.md) |
| 灯状态 | [get_light_status.fbs](aorta/schemas/service/peripheral/get_light_status.fbs) | `aorta.services.peripheral.GetLightStatusRequest` | [service-call](../recipes/service-call/README.zh-CN.md) |

命名规则示例：从 foxglove.CompressedVideo 模块导入 CompressedVideo，调用 GetRootAs 解析接收字节；带 T 后缀的生成对象类用于构建消息。RCP 的 DagSpec、DagNode、NodeCommand 来自 function_input.fbs，由 execute_task.fbs 引入。service 请求使用对应 schema_meta 和 SDK 提供的 header。字段存在不代表路由开放；仍需检查接口文档、公开目录及当前设备。
