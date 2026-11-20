# Audio and speech

<p align="center">English | <a href="audio.zh-CN.md">中文</a></p>

This family groups audio frames, UWB input completion, speaker PCM input and
speech-policy control.

For a Python SDK implementation, see the [audio Recipe](../../recipes/audio/README.md): source, Bazel target, offline preview and explicit device execution. The interface semantics below remain authoritative.
The Recipe captures inputs and events; it does not publish PCM or change speech policy.
Choose the audio source your application needs. Speech recognition and response generation
are application responsibilities, not outputs provided by this interface set.

## Prerequisites and interfaces

The current scope is robot application **V1.7.0-6** on `foot_quadruped` EDU / DEV.
Check route availability against the [compatibility matrix](../compatibility.md).
Log in with the vbot account and complete
[device shell setup](../getting-started/device-environment.md). The speech pipeline must be
running; UWB input additionally needs the remote control and its voice-input function.
Capture audio only with the participants'
permission, and avoid retaining or uploading audio by default.

The outputs below are **pub/sub, read-only subscriptions**. Subscribing does not start recording.
PCM publication and speech-policy changes are separate operations described below.

| Output | Aorta topic | Aorta root type | ROS 2 topic | ROS 2 message type |
| --- | --- | --- | --- | --- |
| Robot-body microphone audio frames | `/raw_audio_dump` | `foxglove.RawAudio` | `/raw_audio_dump` | `foxglove_msgs/msg/RawAudio` |
| UWB signalling audio frames (ADPCM) | `/audio/uwb_adpcm_segment` | `foxglove.RawAudio` | `/audio/uwb_adpcm_segment` | `foxglove_msgs/msg/RawAudio` |
| Input transfer ended | `/uwb/audio_done` | `aorta.uwb.AudioDoneEvent` | `/uwb/audio_done` | `aorta_msgs/msg/AudioDoneEvent` |

## Distinguish the two audio sources

- `/raw_audio_dump` carries audio captured by the **robot-body microphone**. Use this
  route to process sound picked up by the robot itself.
- `/audio/uwb_adpcm_segment` carries audio received through **UWB signalling**, originating
  from the remote control's voice input. Use this route to process that input, not the
  robot-body microphone. Its paired `/uwb/audio_done` event applies only to UWB input;
  it does not mark the end of the robot-body microphone stream.

Both routes use RawAudio, but they are separate input sources, not aliases or two encodings
of the same recording. Select the topic by source first, then inspect its encoding fields.
Neither audio-frame topic contains recognized text; use your own recognition pipeline
when your application needs transcripts.

## Discover without capturing audio

Inspect this family together in the device shell; metadata inspection does not subscribe
to any payload stream. Then sample only the route needed by the application:

```bash
timeout 15s aorta topic list
timeout 15s aorta schema get /raw_audio_dump --describe
timeout 15s aorta schema get /audio/uwb_adpcm_segment --describe
timeout 15s aorta schema get /uwb/audio_done --describe
timeout 15s aorta schema get /audio/play_pcm --describe
timeout 15s aorta schema get srv/speech_control --describe
timeout 15s ros2 topic list --no-daemon -t
timeout 15s ros2 interface show foxglove_msgs/msg/RawAudio
timeout 15s ros2 interface show aorta_msgs/msg/AudioDoneEvent
timeout 15s ros2 interface show aorta_msgs/msg/PcmPlayback
timeout 15s ros2 interface show speech_msgs/srv/SpeechControl
```

These checks inspect route and type information, not audio payloads. An idle remote control
need not emit either UWB stream.
Discovery alone does not mean an input session is in progress.
The `srv/` CLI prefix selects service metadata explicitly; the service name remains `/speech_control`.

## Select and interpret the output

- General audio: inspect the `format`, `sample_rate`, `number_of_channels`, `timestamp`,
  and `data` of each stream. Do not assume the two RawAudio routes use the same codec or
  concatenate them as a single recording. Choose a decoder from the actual encoding.
- Input completion does not confirm processing or playback completion.
  For text-to-speech use the [speech service](aorta-ros2.md); for already-generated PCM
  use the playback input below, not the read-only capture topics.

## Stream PCM to the speaker

`/audio/play_pcm` is a **pub/sub command input**: publish `aorta.topic.audio.PcmPlayback`
through Aorta, or `aorta_msgs/msg/PcmPlayback` on the ROS 2 topic of the same name.
It is not a microphone stream, an ASR input or a request/reply service.
Coordinate with other audio applications and confirm the playback volume before sending sound.

| Field | Required value or meaning |
| --- | --- |
| `frame_sequence` | Unsigned frame sequence; increment within the stream |
| `sample_rate` | `16000` Hz |
| `bit_depth` | `16` bits |
| `num_channels` | `1` (mono) |
| `num_samples` | Number of samples in this frame; must equal the length of `audio_data` |
| `audio_data` | Nonempty signed 16-bit sample vector, values from -32768 to 32767; not an encoded file or byte vector |

Send samples only, without a WAV header or an in-band start/end marker. The first valid
nonempty frame opens playback and can interrupt the current chat TTS; stopping publication lets the receiver close the stream
after its silence timeout and drain queued audio. A published message is not a playback
completion acknowledgement, and `/uwb/audio_done` does not acknowledge speaker playback.

Prepare/resample audio to the required format and send small frames at the audio cadence,
not an entire recording in one message. For example, 20 ms contains 320 samples and 640
bytes of sample data, before message overhead. The ROS bridge requires a single writer,
limits the serialized message to 4096 bytes and accepts at most 100 messages/s with a
burst of 5; its missing-input timeout is 100 ms and does not inject zero samples.
These bridge limits do not define ownership for direct Aorta publishers.
Malformed native frames (wrong format, empty samples or a length mismatch) are dropped.
On exit, stop the producer and close its publisher; do not send an invented end frame.

UWB input is 8 kHz ADPCM, not this 16 kHz PCM representation. Decode and resample it
before playback if your application needs that conversion; do not forward RawAudio
payload bytes directly into this sample vector. For spoken text, prefer `/speech/set_speak`
rather than generating PCM yourself.

## Query or change speech policy

`/speech_control` is a **service**, mapped to the same ROS 2 service name with type
`speech_msgs/srv/SpeechControl`. Native Aorta uses
`aorta.services.speech.SpeechControlRequest` and `aorta.services.speech.SpeechControlResponse`.
The source field definitions are in the [Aorta Schema](../../schemas/aorta/schemas/service/speech/speech_control.fbs)
and [ROS 2 service definition](../../schemas/ros2/speech_msgs/srv/SpeechControl.srv).

| Request type | Meaning | Relevant fields |
| --- | --- | --- |
| 1 / 2 / 5 | Query command recognition / chat / continuous command recognition | `request_type`; read-only queries |
| 3 | Set command recognition mode | `mode`, with the fallback rule below using `enable` |
| 4 / 6 | Enable or disable chat / continuous command recognition | `enable` |
| 7 / 8 | Notify speech policy of action mode on / off | `request_type` selects on / off |
| 9 / 10 | Notify speech policy of avatar mode on / off | `request_type` selects on / off |
| 11 / 12 | Notify speech policy of navigation mode on / off | `request_type` selects on / off |
| 13 / 14 | Notify low-power voice suppression on / off | `request_type` selects on / off |
| 15 / 16 | Notify RTC session active / inactive | `request_type` selects on / off |
| 17 | Synchronize the proactive-interaction requested state | `enable` |
| 18 | Native Aorta: close the current microphone output stream | `close_mic_output=true`; a later accepted wake may open another stream |
| 19 | Native Aorta: set microphone VAD silence timeout | `val`: integer seconds in 1–3600; zero is invalid |

For type 3, `mode=0` is off, `mode=1` is local speech-service recognition and `mode=2`
is cloud ASR. A nonzero mode takes precedence over `enable`; with mode 0,
`enable=false` selects off and `enable=true` selects local mode 1.
Do not pass mode values outside 0–2. Types 7–17 change speech-policy state: they do not
move the robot, select a locomotion mode or switch the hardware power state.

Types 18/19 require the updated native Schema and SDK. The current ROS service has
neither `close_mic_output` nor `val`; its bridge permits request types 1–17 only.
Do not encode these operations as a ROS `enable` or `mode` value. Closing the current
stream is not permanently disabling the microphone; changing its silence timeout is
not an application task timeout. Both modify speech behavior and are not discovery probes.

Query business fields, for example:

```json
{"request_type": 1, "enable": false, "mode": 0}
```

This shows the business payload, not a serialized Aorta service envelope. Use the SDK's
service/header conventions when building a request. Check native `status` and
`message`, or ROS 2 `success` and `message`, then inspect `cmd_recognition_status`,
`cmd_recognition_mode`, `chat_function_status` and `continuous_cmd_status`.
After a change, query the state again rather than treating transport success as confirmation.
Low-power voice suppression can reject switch changes; chat cannot be enabled while
action/avatar/navigation mode is active. Coordinate changes with the current application
and restore only settings your application changed. Discovery must not send mode notifications.
The ROS bridge allows one in-flight request, a 5 s service timeout, 5 requests/s and a
burst of 10, with a 4096-byte request limit.

## UWB audio frames

- `format` is `adpcm`, `sample_rate` is `8000` Hz, and `number_of_channels` is `1`.
  The generic RawAudio type name does not mean this route delivers PCM.
- `data` is a compressed frame payload passed through from UWB. It is not an entire WAV
  file, uncompressed samples, or recognized text. The bridge does not decode it. Use a
  decoder matching the remote-control ADPCM framing and codec; the format label alone does
  not specify a decoder variant. Do not send these bytes to a PCM-only ASR endpoint.
- `timestamp` carries the frame timestamp as seconds and nanoseconds. Aorta may also carry
  `user_interaction_context`, including `user_interaction_id`, for associating frames with
  the corresponding input-end event. Treat that context as optional.
- The ROS RawAudio mapping carries the audio fields but **does not carry this interaction
  context**. Prefer Aorta when application logic depends on correlating the two streams by
  interaction identity.

## UWB input-end event

- `timestamp_ns` is the event timestamp in nanoseconds. Optional `user_interaction_context`
  associates the event with the voice-input interaction when provided.
- The ROS type is a structured AudioDoneEvent, not an empty notification. For the optional
  context, check `has_user_interaction_context` before using the nested fields.
- This event marks the end of UWB input transfer. It does **not** mean ASR has completed,
  playback has finished, or every preceding frame has reached your application.

## Consume a UWB voice-input session

1. Open both subscriptions before the user begins voice input; a subscriber joining late
   must not expect earlier frames or the earlier end event to be replayed.
2. Buffer only the current input with explicit byte and duration bounds. Associate frames
   and events using the optional interaction identity when present. If it is absent,
   handle a single input session explicitly; timestamps alone do not establish a unique ID.
3. On the input-end event, finish the matching session using a bounded drain period for
   in-flight audio. Do not assume ordering between different topics. Detect interruption
   and incomplete input rather than silently treating partial audio as a complete recording.
4. Decode with the matching ADPCM decoder before using PCM-only playback or recognition.
   Recognition and response generation are separate application steps.
5. If the end event never arrives, expire the session and clean up buffers. Close both
   subscriptions and discard unneeded audio on exit.

To inspect only one end event during an intentionally initiated voice-input session:

```bash
timeout 15s aorta topic echo /uwb/audio_done --count 1
```

Start the command before ending the input. Exit `124` means the deadline expired; it does
not prove the route is unavailable. This command does not collect the paired audio stream
and is not a complete audio-capture implementation. If data is missing during input, check
the remote-control connection, voice-input activity, and [device environment](../getting-started/device-environment.md).
