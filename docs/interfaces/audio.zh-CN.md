# 音频与语音输入

<p align="center"><a href="audio.md">English</a> | 中文</p>

本功能域统一包含音频帧、UWB 输入结束、识别文本与语音事件。

Python SDK 实现见 [audio Recipe](../../recipes/audio/README.zh-CN.md)，包含源码、Bazel 目标、离线预览与显式设备运行。接口语义以下文为准。
按应用需要选择数据表示：文本触发类应用使用识别文本，只有自行处理音频时才使用音频帧。

## 前置条件与接口

当前范围为提供下列路由的 `foot_quadruped` EDU 固件，最低固件版本尚未公布。
使用 vbot 账户登录并完成[设备 shell 配置](../getting-started/device-environment.zh-CN.md)。
语音链路需要运行；UWB 输入还需要遥控器及其语音输入功能可用。
仅在参与者同意后采集语音或转写内容，默认不保留或上传音频。

这些接口均为 **pub/sub，只读订阅**；订阅本身不会启动录音。

| 输出 | Aorta topic | Aorta 根类型 | ROS 2 topic | ROS 2 消息类型 |
| --- | --- | --- | --- | --- |
| 本体麦克风音频帧 | `/raw_audio_dump` | `foxglove.RawAudio` | `/raw_audio_dump` | `foxglove_msgs/msg/RawAudio` |
| UWB 信令音频帧（ADPCM） | `/audio/uwb_adpcm_segment` | `foxglove.RawAudio` | `/audio/uwb_adpcm_segment` | `foxglove_msgs/msg/RawAudio` |
| 输入传输结束 | `/uwb/audio_done` | `aorta.uwb.AudioDoneEvent` | `/uwb/audio_done` | `aorta_msgs/msg/AudioDoneEvent` |
| 最终识别文本 | `/speech/asr_result` | `aorta.topic.speech.AsrResult` | `/speech/asr_result` | `aorta_msgs/msg/AsrResult` |
| 语音交互事件 | `/voice/event` | `aorta.voice.VoiceEvent` | `/voice/event` | `aorta_msgs/msg/VoiceEvent` |

## 区分两路音频来源

- `/raw_audio_dump` 来自**机器人本体麦克风**的采集，用于处理机器人自身拾取的声音。
- `/audio/uwb_adpcm_segment` 来自 **UWB 信令**传入的音频，即遥控器的语音输入，
  不是本体麦克风采集。配套的 `/uwb/audio_done` 事件只针对 UWB 输入，
  不表示本体麦克风音频流结束。

两条路由都使用 RawAudio，但属于不同输入来源，不是别名，也不是同一段录音的两种编码。
先按来源选择 topic，再检查其编码字段。两条音频帧 topic 都不包含识别文本。
需要任一来源的文本时，订阅统一的 `/speech/asr_result`，通过 `provider` 区分来源，
具体方法见下文。

## 不采集音频，先发现接口

在设备 shell 中统一检查本功能域；元数据检查不订阅任何载荷流。
随后只对应用实际需要的路由采样：

```bash
timeout 15s aorta topic list
timeout 15s aorta schema get /raw_audio_dump --describe
timeout 15s aorta schema get /audio/uwb_adpcm_segment --describe
timeout 15s aorta schema get /uwb/audio_done --describe
timeout 15s aorta schema get /speech/asr_result --describe
timeout 15s aorta schema get /voice/event --describe
timeout 15s ros2 topic list --no-daemon -t
timeout 15s ros2 interface show foxglove_msgs/msg/RawAudio
timeout 15s ros2 interface show aorta_msgs/msg/AudioDoneEvent
timeout 15s ros2 interface show aorta_msgs/msg/AsrResult
```

这些检查只读取路由和类型信息，不获取音频载荷。遥控器空闲时两条 UWB 流都可能没有输出；
文本和语音事件取决于语音链路的活动。
能发现接口不表示当前正在进行语音输入。

## 选择并理解输出

- 通用音频：检查各数据流的 `format`、`sample_rate`、`number_of_channels`、`timestamp`、`data`。
  不假定两条 RawAudio 路由编码相同，也不把它们拼接为同一段录音，按实际编码选择解码器。
- 识别文本：`text` 是非空的最终转写。没有消息表示没有新的最终转写，不是空识别结果。
  文本触发应用直接消费此输出，无需先解码音频并运行另一套 ASR。
  应用只接受一路输入时，按下文的来源字段筛选。
- 语音事件：先检查 `payload_type`，再读取带类型的 `payload`，不能把整条流当作纯文本 topic。
  ASR 事件需处理 `is_final` 和 `is_reject`，不对被拒绝或中间文本执行动作。
  用 `session_id`、`generation` 与可选交互上下文关联事件；未知事件类型忽略，不当作命令。
  同时消费最终文本与同轮 ASR 事件时需去重，避免重复触发。
- 输入结束、最终识别与播放结束是不同事件。语音播放使用[语音 service](aorta-ros2.zh-CN.md)，
  不是这些只读 topic。

## 按来源区分 ASR 结果

`/speech/asr_result` 统一发布两路输入的最终识别文本。`provider` 字段标识**输入来源**，
不是 ASR 厂商、说话人身份，也不表示具有执行命令的权限。按每条消息的枚举值区分：

| Provider | 数值 | 输入来源 | 该来源的音频 topic |
| --- | --- | --- | --- |
| `BODY` | `1` | 本体麦克风 | `/raw_audio_dump` |
| `TAG` | `2` | 经 UWB 信令传入的遥控器语音输入 | `/audio/uwb_adpcm_segment` |
| `UNKNOWN` | `0` | 来源未指定 | — |

Aorta 按解码后的枚举值判断；ROS 2 检查 `provider` 字段，数值映射相同。
CLI 或绑定可能显示枚举名或数值，两者含义相同。消费结果时：

1. 读取每条消息的 `provider` 和 `text`。仅处理本体麦克风输入时保留 `BODY`；
   仅处理 UWB 输入时保留 `TAG`。两路都处理时，将来源与转写文本一起保留。
2. `UNKNOWN`、字段缺失或未来新增的未知值均按来源未知处理，不能默认归为任一路。
   应用要求特定来源时，忽略这些结果。
3. 不根据识别出的文字、消息到达顺序或最近哪条音频流活跃猜测来源。
   此字段只区分输入来源，不能据此将转写与某一音频帧或某次 UWB 输入结束事件一一对应。

在参与者同意的文本交互中，先订阅，再让用户讲话：

```bash
timeout 15s aorta topic echo /speech/asr_result --count 1
```

每条新转写只处理一次，校验应用支持的命令词；未知文本不派发设备动作。
限制事件队列长度并丢弃过期会话，重连后不能根据旧事件推断当前语音状态。

## UWB 音频帧

- `format` 为 `adpcm`，`sample_rate` 为 `8000` Hz，`number_of_channels` 为 `1`。
  通用类型名 RawAudio 不表示此路由输出 PCM。
- `data` 是从 UWB 逐帧透传的压缩载荷，不是完整 WAV 文件、未压缩采样或识别文本。
  bridge 不会解码。需要匹配遥控器 ADPCM 帧格式与编码方式的解码器；
  仅凭格式标签无法确定解码器变体。不要把这些字节发送到只接受 PCM 的 ASR 接口。
- `timestamp` 以秒与纳秒携带帧时间戳。Aorta 还可能携带 `user_interaction_context`，
  其中的 `user_interaction_id` 可用于关联音频帧与输入结束事件；此上下文为可选数据。
- ROS RawAudio 映射保留音频字段，但**不携带此交互上下文**。
  应用需要按交互标识关联两条流时，优先使用 Aorta。

## UWB 输入结束事件

- `timestamp_ns` 为纳秒事件时间戳；可选的 `user_interaction_context` 在存在时关联本轮语音输入。
- ROS 类型是有字段的 AudioDoneEvent，不是空通知。使用可选上下文的嵌套字段前，
  先检查 `has_user_interaction_context`。
- 此事件表示 UWB 输入传输结束，**不表示** ASR 已完成、播放已结束，
  也不保证此前所有音频帧都已到达应用。

## 接收一次 UWB 语音输入

1. 在用户开始输入前建立两条订阅。晚加入的订阅者不能期待此前的帧或结束事件被重放。
2. 只缓冲当前输入，明确限制字节数与持续时间。有交互标识时据此关联帧与事件；
   没有时显式管理单轮输入，不能仅凭时间戳认定存在唯一交互 ID。
3. 收到输入结束事件后，为仍在传输中的音频保留有界的收尾等待，再结束对应输入。
   不假设不同 topic 之间有消息顺序保证；识别中断与不完整输入，不能把残缺音频默认为完整录音。
4. 使用只接受 PCM 的播放或识别功能前，先用匹配的 ADPCM 解码器解码。
   语音识别和回复生成是独立的应用步骤。
5. 如果始终没有结束事件，超时结束本轮并清理缓冲；退出时关闭两条订阅，丢弃不再需要的音频。

在主动发起的一轮语音输入期间，仅检查一条结束事件：

```bash
timeout 15s aorta topic echo /uwb/audio_done --count 1
```

在结束输入前启动命令。退出码 `124` 表示超过等待时限，不能证明路由不可用。
此命令不采集配套音频流，不是完整的音频采集实现。
输入期间收不到数据时，检查遥控器连接、语音输入状态和[设备环境](../getting-started/device-environment.zh-CN.md)。
