# 自定义 PCM 播放与语音策略控制

<p align="center"><a href="audio-playback-control.md">English</a> | 中文</p>

## 可用范围

这两项是 2026-10-12 确认开放、**尚未发布的 EDU 接口扩展**，适用形态为
`foot_quadruped`。需要配套的机器人应用构建、公开 Schema 包、EDU ACL 和 ROS 2
Bridge 包。仅凭 V1.6.0 版本号不能判断已支持；目前尚未指定最低已发布固件或 SDK
版本。[已入库的 Schema](../../schemas/README.zh-CN.md) 仍保持已发布快照，待配套产物发布后同步。

| 功能 | Aorta 路由 | 原语／开发者方向 | Aorta 类型 | 候选 ROS 2 映射 |
| --- | --- | --- | --- | --- |
| 播放用户提供的 PCM | `/audio/play_pcm` | pub/sub — 仅发布 | `aorta.topic.audio.PcmPlayback` | `/audio/play_pcm`，`aorta_msgs/msg/PcmPlayback` |
| 查询或设置语音策略 | `/speech_control` | service — 仅调用 | `aorta.services.speech.SpeechControlRequest` / `SpeechControlResponse` | `/speech_control`，`speech_msgs/srv/SpeechControl` |

原 `/speech_phone_to_dog` 与 `SpeechPhoneToDog` 已被新名称替代，不保留兼容别名。
调用方需更换发布名称并重新生成／安装绑定；不支持混用新旧应用、SDK 和 Bridge。
EDU 用户不能订阅 PCM 播放输入、提供 `/speech_control` 服务，也不会因此获得其他私有语音接口权限。

## 准备与发现

1. 使用配套构建和 SDK／Schema 产物，不能继续使用缺少 `PcmPlayback` 的旧 wheel。
   以 `vbot` 登录，完成[设备 shell 配置](../getting-started/device-environment.zh-CN.md)。
2. 确认语音服务，以及按需使用的设备本地 Bridge 正常运行。使用安静、获同意的测试场景，
   输出音量设置适当；不要通过播放音频来做普通连通性检查。
3. 只检查类型，不发布 PCM 或修改策略：

   ```bash
   timeout 15s aorta schema get /audio/play_pcm --describe
   timeout 15s aorta schema get /speech_control --describe
   timeout 15s ros2 interface show aorta_msgs/msg/PcmPlayback
   timeout 15s ros2 interface show speech_msgs/srv/SpeechControl
   timeout 15s ros2 service list -t
   ```

PCM Schema 由 typed publisher 注册；没有发布者时，`schema get` 可能超时，需同时检查
已安装的配套 Schema 包。发现接口不等于声音已播放或策略设置已生效。

## 流式发送 PCM 样本

`PcmPlayback` 定义在配套公开包的 `topic/audio/pcm_playback.fbs`。
业务帧字段如下，`aorta_header` 交由 SDK 维护：

| 字段 | 约束 |
| --- | --- |
| `frame_sequence` | 无符号帧序号，用于诊断；接收端不会据此重排或去重 |
| `sample_rate` | `16000` Hz |
| `bit_depth` | `16` |
| `num_channels` | `1`，单声道 |
| `num_samples` | 本帧样本数，必须等于 `len(audio_data)` |
| `audio_data` | 非空有符号 16 位样本数组，单个值范围为 `[-32768, 32767]` |

源音频应先解码／重采样。不能发送 WAV 文件头、MP3／ADPCM 字节或 `0x5555`／`0xaaaa`
控制标记；这些标记数值只会被当作普通 PCM 样本。使用新接口对应的 typed SDK publisher
及配套生成元数据，或通过 Bridge 发布候选 ROS 类型；不要绕过语音服务直接操作 ALSA。

按实际音频节奏发送小帧，不整文件发送或突发灌入。可以从每帧 320 样本开始，
对应 16 kHz 下的 20 ms。Bridge 有单写入者、请求大小、租约和限流约束，不能让多个
独立写入者混用同一条流。格式和样本数量不匹配会被拒绝，不会静默转换。

第一帧有效数据启动／恢复播放会话。当前实现超过约 100 ms 未收到新输入后结束输入，
随后播放完已排队样本；连续播放期间应让帧间隔小于该超时。
正常结束时停止发送并关闭 publisher，不发送空帧、合成零帧或标记帧。
间隔过长可能把播放拆成多轮；播放还受机器人现有音频仲裁影响，可能中断其他声道。

此 topic 不是播放 Action，没有逐请求的接收确认、结果、取消或扬声器播放结束确认。
发布成功不等于全部声音已经播完；`/uwb/audio_done` 是输入传输结束，不是本接口播放完成。
断连后结果不确定时，不自动重播整段音频，由业务决定恢复策略。

## 查询、修改与恢复语音策略

`SpeechControlRequest` 定义在 `service/speech/speech_control.fbs`，业务字段是
`request_type`、`enable`、`mode`。完整操作列表以 Schema 为准，独立语音应用常用如下操作：

| 请求 | 含义 |
| --- | --- |
| `request_type=1` | 查询命令词识别状态 |
| `request_type=2` | 查询普通闲聊状态 |
| `request_type=3, mode=0, enable=false` | 关闭普通本体命令词识别／唤醒准入 |
| `request_type=3, mode=0, enable=true` | 打开本地识别模式 `1` |
| `request_type=3, mode=1` 或 `2` | 选择本地 `1` 或服务端 `2`；非零 `mode` 优先于 `enable` |
| `request_type=4, enable=false` | 关闭普通内置闲聊策略 |

修改前查询并保存 `cmd_recognition_mode`、`chat_function_status` 及应用会改变的其他设置。
设置请求采用有界超时，检查 Aorta `status`／`message` 或 ROS `success`／`message`，
随后再查询实际状态。退出时恢复原值并核对：恢复模式 `0` 使用 `mode=0, enable=false`；
恢复 `1`／`2` 使用对应的非零 `mode`。不要假定默认状态，也不自动重试结果不确定的修改请求。

这些设置控制语音准入与策略，不是全局硬件静音，也不保证立即取消已进行的对话。
关闭普通识别与闲聊**不会关闭独立的 UWB 按键对话链路**，该链路仍可能产生 ASR 和回复。
模式限制仍由服务提供端决定；不能用它代替急停或声称独占了全部语音输入。

## 异常处理

- 找不到类型／被拒绝：核对应用、Schema、Bridge 与 ACL 是否配套，不扩大 ACL 或退回旧名称。
- 无声音：检查格式、样本数、发送节奏、音量、语音服务及其他声道；查看 Bridge 的写入者冲突、
  超限、过期帧和格式拒绝诊断，不能仅凭发现 topic 判定成功。
- 策略未改变：检查响应并重新查询，特别检查 `mode` 优先级与服务端模式限制。
  UWB 仍响应不表示普通本体识别仍然开启。
