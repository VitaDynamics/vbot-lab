# Audio and speech input

<p align="center">English | <a href="audio.zh-CN.md">中文</a></p>

This family groups audio frames, UWB input completion, recognized text, and voice events.

For a Python SDK implementation, see the [audio Recipe](../../recipes/audio/README.md): source, Bazel target, offline preview and explicit device execution. The interface semantics below remain authoritative.
Choose the representation your application needs: use recognized text for a text-triggered
application, and audio frames only when implementing your own audio processing.

## Prerequisites and interfaces

The current scope is robot application **V1.6.0** on `foot_quadruped` EDU.
Check route availability against the [compatibility matrix](../compatibility.md).
Log in with the vbot account and complete
[device shell setup](../getting-started/device-environment.md). The speech pipeline must be
running; UWB input additionally needs the remote control and its voice-input function.
Capture voice or transcripts only with the participants'
permission, and avoid retaining or uploading audio by default.

These interfaces are **pub/sub, read-only subscriptions**. Subscribing does not start recording.

| Output | Aorta topic | Aorta root type | ROS 2 topic | ROS 2 message type |
| --- | --- | --- | --- | --- |
| Robot-body microphone audio frames | `/raw_audio_dump` | `foxglove.RawAudio` | `/raw_audio_dump` | `foxglove_msgs/msg/RawAudio` |
| UWB signalling audio frames (ADPCM) | `/audio/uwb_adpcm_segment` | `foxglove.RawAudio` | `/audio/uwb_adpcm_segment` | `foxglove_msgs/msg/RawAudio` |
| Input transfer ended | `/uwb/audio_done` | `aorta.uwb.AudioDoneEvent` | `/uwb/audio_done` | `aorta_msgs/msg/AudioDoneEvent` |
| Final recognized text | `/speech/asr_result` | `aorta.topic.speech.AsrResult` | `/speech/asr_result` | `aorta_msgs/msg/AsrResult` |
| Voice interaction events | `/voice/event` | `aorta.voice.VoiceEvent` | `/voice/event` | `aorta_msgs/msg/VoiceEvent` |

## Distinguish the two audio sources

- `/raw_audio_dump` carries audio captured by the **robot-body microphone**. Use this
  route to process sound picked up by the robot itself.
- `/audio/uwb_adpcm_segment` carries audio received through **UWB signalling**, originating
  from the remote control's voice input. Use this route to process that input, not the
  robot-body microphone. Its paired `/uwb/audio_done` event applies only to UWB input;
  it does not mark the end of the robot-body microphone stream.

Both routes use RawAudio, but they are separate input sources, not aliases or two encodings
of the same recording. Select the topic by source first, then inspect its encoding fields.
Neither audio-frame topic contains recognized text. For text from either source, subscribe
to the shared `/speech/asr_result` topic and distinguish the source using `provider`, as
described below.

## Discover without capturing audio

Inspect this family together in the device shell; metadata inspection does not subscribe
to any payload stream. Then sample only the route needed by the application:

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

These checks inspect route and type information, not audio payloads. An idle remote control
need not emit either UWB stream; text and voice events depend on speech-pipeline activity.
Discovery alone does not mean an input session is in progress.

## Select and interpret the output

- General audio: inspect the `format`, `sample_rate`, `number_of_channels`, `timestamp`,
  and `data` of each stream. Do not assume the two RawAudio routes use the same codec or
  concatenate them as a single recording. Choose a decoder from the actual encoding.
- Recognized text: `text` is a nonempty final transcript. No message means no new final
  transcript, not an empty recognition result. A text trigger should consume this output
  directly instead of decoding audio and running another ASR engine. Filter by the source
  field described below when the application accepts only one input source.
- Voice events: inspect `payload_type` before reading the tagged `payload`; the stream is
  not a flat text topic. For ASR events, handle `is_final` and `is_reject`; do not act on
  rejected or interim text. Use `session_id`, `generation`, and optional interaction
  context to correlate events. Ignore unsupported event variants rather than treating them
  as commands. Do not trigger twice by consuming both the final-text topic and an ASR event
  for the same interaction without deduplication.
- Input completion, final recognition, and playback completion are different events.
  Speech playback uses the [speech service](aorta-ros2.md), not these read-only topics.

## Distinguish ASR results by source

`/speech/asr_result` carries final recognized text from both input paths. Its `provider`
field identifies the **input source**, not the ASR vendor, speaker identity, or permission
to execute a command. Use the enum value in each message:

| Provider | Numeric value | Input source | Audio topic for that source |
| --- | --- | --- | --- |
| `BODY` | `1` | Robot-body microphone | `/raw_audio_dump` |
| `TAG` | `2` | Remote-control voice input through UWB signalling | `/audio/uwb_adpcm_segment` |
| `UNKNOWN` | `0` | Unspecified source | — |

For Aorta, compare the decoded enum value; for ROS 2, inspect the `provider` field using
the same numeric mapping. A CLI or binding may display an enum name or its number; neither
changes its meaning. To consume results:

1. Read `provider` and `text` from each message. A body-microphone-only application accepts
   `BODY`; a UWB-only application accepts `TAG`. An application supporting both should keep
   the source alongside the transcript.
2. Treat `UNKNOWN`, a missing field, or an unrecognized future value as unknown. Do not
   silently classify it as either known source. Ignore it if the application requires a
   specific source.
3. Do not infer the source from the words recognized, message arrival order, or which audio
   topic was most recently active. This field classifies the source; it does not associate
   a transcript with an individual audio frame or a particular UWB input-end event.

For a consented text interaction, start the subscriber before the user speaks:

```bash
timeout 15s aorta topic echo /speech/asr_result --count 1
```

Process each new transcript once, validate the application's command vocabulary, and handle
unknown text without dispatching a device action. Bound event queues and discard obsolete
sessions. Do not infer current voice state from an old event after reconnecting.

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
