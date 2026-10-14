# 音频与语音

<p align="center"><a href="audio.md">English</a> | 中文</p>

本功能域统一包含音频帧、UWB 输入结束、识别文本、语音事件、扬声器 PCM 输入与语音策略控制。

Python SDK 实现见 [audio Recipe](../../recipes/audio/README.zh-CN.md)，包含源码、Bazel 目标、离线预览与显式设备运行。接口语义以下文为准。
此 Recipe 采集输入与事件，不发布 PCM 或修改语音策略。
按应用需要选择数据表示：文本触发类应用使用识别文本，只有自行处理音频时才使用音频帧。

## 前置条件与接口

当前适配 `foot_quadruped` EDU 的机器人应用版本 **V1.6.0-10**，
路由可用性须结合[兼容矩阵](../compatibility.zh-CN.md)确认。
使用 vbot 账户登录并完成[设备 shell 配置](../getting-started/device-environment.zh-CN.md)。
语音链路需要运行；UWB 输入还需要遥控器及其语音输入功能可用。
仅在参与者同意后采集语音或转写内容，默认不保留或上传音频。

下表输出为 **pub/sub，只读订阅**；订阅本身不会启动录音。
PCM 发布和语音策略修改属于独立操作，见下文。

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
timeout 15s aorta schema get /audio/play_pcm --describe
timeout 15s aorta schema get srv/speech_control --describe
timeout 15s ros2 topic list --no-daemon -t
timeout 15s ros2 interface show foxglove_msgs/msg/RawAudio
timeout 15s ros2 interface show aorta_msgs/msg/AudioDoneEvent
timeout 15s ros2 interface show aorta_msgs/msg/AsrResult
timeout 15s ros2 interface show aorta_msgs/msg/PcmPlayback
timeout 15s ros2 interface show speech_msgs/srv/SpeechControl
```

这些检查只读取路由和类型信息，不获取音频载荷。遥控器空闲时两条 UWB 流都可能没有输出；
文本和语音事件取决于语音链路的活动。
能发现接口不表示当前正在进行语音输入。
CLI 的 `srv/` 前缀明确选择 service 元数据，服务名仍为 `/speech_control`。

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
- 输入结束、最终识别与播放结束是不同事件。文本转语音使用[语音 service](aorta-ros2.zh-CN.md)；
  已生成的 PCM 使用下文的播放输入，不是这些只读采集 topic。

## 向扬声器发送 PCM

`/audio/play_pcm` 是 **pub/sub 控制输入**：通过 Aorta 发布 `aorta.topic.audio.PcmPlayback`，
或向同名 ROS 2 topic 发布 `aorta_msgs/msg/PcmPlayback`。
它不是麦克风音频流、ASR 输入，也不是请求／响应 service。
发声前需协调其他音频应用并确认播放音量。

| 字段 | 必需值或含义 |
| --- | --- |
| `frame_sequence` | 无符号帧序号，在同一音频流内递增 |
| `sample_rate` | `16000` Hz |
| `bit_depth` | `16` bit |
| `num_channels` | `1`，单声道 |
| `num_samples` | 当前帧采样数，必须等于 `audio_data` 的长度 |
| `audio_data` | 非空的有符号 16 位采样数组，取值 -32768 至 32767；不是编码文件或字节数组 |

只发送采样，不带 WAV 文件头或数据内的开始／结束标记。第一帧有效非空数据启动播放，并可能中断正在播放的闲聊 TTS；
停止发布后，接收端在静默超时后关闭音频流并排空已排队音频。发布消息不等于播放完成回执，
`/uwb/audio_done` 也不确认扬声器播放完成。

先准备或重采样到所需格式，再按音频节奏发送小帧，不把整段录音装入一条消息。
例如 20 ms 为 320 个采样、640 字节采样数据，不含消息封装开销。
ROS bridge 要求单一发布者，序列化消息不超过 4096 字节，最多每秒 100 条、突发 5 条；
缺少输入的超时为 100 ms，不会注入零采样。这些 bridge 限制不定义直接 Aorta 发布者的所有权。
原生格式错误、采样为空或长度不匹配的帧会丢弃。
退出时停止生产数据并关闭 publisher，不发送自行约定的结束帧。

UWB 输入为 8 kHz ADPCM，不是这里的 16 kHz PCM；应用需要转换播放时先解码和重采样，
不要将 RawAudio 的载荷字节直接填入采样数组。仅需播报文字时，优先使用 `/speech/set_speak`，
无需自行生成 PCM。

## 查询或修改语音策略

`/speech_control` 是 **service**，映射到同名 ROS 2 service，类型为
`speech_msgs/srv/SpeechControl`。原生 Aorta 使用
`aorta.services.speech.SpeechControlRequest` 和 `aorta.services.speech.SpeechControlResponse`。
字段定义见 [Aorta Schema](../../schemas/aorta/schemas/service/speech/speech_control.fbs)
及 [ROS 2 service 定义](../../schemas/ros2/speech_msgs/srv/SpeechControl.srv)。

| 请求类型 | 含义 | 使用字段 |
| --- | --- | --- |
| 1／2／5 | 查询命令识别／闲聊／连续命令识别 | `request_type`，只读查询 |
| 3 | 设置命令识别模式 | `mode`，并按下方规则使用 `enable` 兜底 |
| 4／6 | 开启或关闭闲聊／连续命令识别 | `enable` |
| 7／8 | 通知语音策略进入／退出动作模式 | `request_type` 选择开启／关闭 |
| 9／10 | 通知语音策略进入／退出 avatar 模式 | `request_type` 选择开启／关闭 |
| 11／12 | 通知语音策略进入／退出领航模式 | `request_type` 选择开启／关闭 |
| 13／14 | 通知进入／退出低功耗语音抑制 | `request_type` 选择开启／关闭 |
| 15／16 | 通知 RTC 会话开始／结束 | `request_type` 选择开启／关闭 |
| 17 | 同步主动交互请求状态 | `enable` |

类型 3 的 `mode=0` 为关闭，`mode=1` 为本地语音服务识别，`mode=2` 为云端 ASR。
非零 mode 优先于 `enable`；mode 为 0 时，`enable=false` 选择关闭，
`enable=true` 选择本地模式 1。不要传入 0–2 以外的 mode。
类型 7–17 只改变语音策略状态，不会让机器人运动、选择运动模式或切换硬件功耗状态。

查询的业务字段例如：

```json
{"request_type": 1, "enable": false, "mode": 0}
```

此处是业务载荷，不是序列化后的 Aorta service 封装；构建请求时遵循 SDK 的 service／header 约定。
检查原生 `status.code` 和 `message`，或 ROS 2 `success` 和 `message`，再查看
`cmd_recognition_status`、`cmd_recognition_mode`、`chat_function_status` 和 `continuous_cmd_status`。
修改后再次查询，不把传输成功当作状态确认。
低功耗语音抑制可能拒绝开关修改；动作／avatar／领航模式下不能开启闲聊。
与当前应用协调修改，只恢复自己改变的设置，发现接口时不要发送模式通知。
ROS bridge 最多允许一个在途请求，service 超时 5 秒，每秒 5 次、突发 10 次，请求上限 4096 字节。

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
