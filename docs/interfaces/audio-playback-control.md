# Custom PCM playback and speech policy

<p align="center">English | <a href="audio-playback-control.zh-CN.md">中文</a></p>

## Availability

These are **unreleased EDU interface additions** ratified on 2026-10-12 for
`foot_quadruped`. They require a matching robot application build, public Schema
pack, EDU ACL and ROS 2 Bridge bundle. The existing V1.6.0 release label alone
does not establish support. No minimum released firmware or SDK version is
assigned yet. The checked-in [Schema snapshot](../../schemas/README.md) remains
the published release snapshot until the matching artifacts are released.

| Function | Aorta route | Primitive / developer direction | Aorta type | Candidate ROS 2 mapping |
| --- | --- | --- | --- | --- |
| Play user-provided PCM | `/audio/play_pcm` | pub/sub — publish only | `aorta.topic.audio.PcmPlayback` | `/audio/play_pcm`, `aorta_msgs/msg/PcmPlayback` |
| Query or set speech policy | `/speech_control` | service — call only | `aorta.services.speech.SpeechControlRequest` / `SpeechControlResponse` | `/speech_control`, `speech_msgs/srv/SpeechControl` |

The former `/speech_phone_to_dog` key and `SpeechPhoneToDog` type are replaced,
not retained as aliases. Update all publishers and rebuild generated bindings.
Mixed old/new application, SDK and Bridge versions are not supported.
EDU clients cannot subscribe to PCM playback input, serve `/speech_control`, or
use these permissions to reach private speech interfaces.

## Prepare and discover

1. Install the coordinated build and matching SDK/Schema artifacts; do not use
   an older wheel that lacks `PcmPlayback`. Complete
   [device shell setup](../getting-started/device-environment.md) as `vbot`.
2. Confirm the speech service and, if needed, the device-local Bridge are running.
   Use a quiet, consented test setting and an appropriately low output volume.
   Do not send audio merely to check connectivity.
3. Inspect types without publishing PCM or modifying policy:

   ```bash
   timeout 15s aorta schema get /audio/play_pcm --describe
   timeout 15s aorta schema get /speech_control --describe
   timeout 15s ros2 interface show aorta_msgs/msg/PcmPlayback
   timeout 15s ros2 interface show speech_msgs/srv/SpeechControl
   timeout 15s ros2 service list -t
   ```

The PCM Schema is registered by a typed publisher; before one exists,
`schema get` may time out. Inspect the installed matching Schema pack as well.
Discovery is not proof that sound played or a policy change took effect.

## Stream PCM samples

`PcmPlayback` uses `topic/audio/pcm_playback.fbs` in the matching public pack.
It contains the following frame fields; the SDK owns `aorta_header`:

| Field | Contract |
| --- | --- |
| `frame_sequence` | Unsigned frame sequence for diagnostics; the receiver does not reorder or deduplicate frames |
| `sample_rate` | `16000` Hz |
| `bit_depth` | `16` |
| `num_channels` | `1` (mono) |
| `num_samples` | Number of samples in this frame; must equal `len(audio_data)` |
| `audio_data` | Nonempty vector of signed 16-bit samples, each in `[-32768, 32767]` |

Decode or resample source audio before sending it. Do not put a WAV header,
MP3/ADPCM bytes, or `0x5555`/`0xaaaa` markers into `audio_data`; marker values
are ordinary PCM samples, not control instructions. Use the typed SDK publisher
on `/audio/play_pcm` and its generated matching metadata, or publish the
candidate ROS type through the Bridge. Do not bypass the robot audio service
with ALSA device access.

Send paced small frames rather than a whole file or a burst: a suitable starting
point is 320 samples per frame (20 ms at 16 kHz). The Bridge enforces one writer,
bounded request size, ownership leases and rate limits. Multiple independent
writers must not share a stream. Format or sample-count mismatches are rejected,
not silently converted.

The first valid frame starts or resumes the playback session. In the current
implementation, more than about 100 ms without new input closes input and allows
already queued samples to drain. Keep inter-frame gaps below that timeout while
streaming. To finish, stop publishing and close your publisher; do not send an
empty frame or a synthetic zero/marker frame. A gap may split playback into
separate sessions. Playback can interact with the robot's existing audio
arbitration and interrupt another channel.

This topic is not a playback Action: it has no per-request acknowledgement, result,
cancel or end-of-speaker acknowledgement. Publisher success is not proof that
all audio was played. `/uwb/audio_done` concerns input transfer and does not
confirm this playback. Do not automatically replay the whole clip after an
uncertain disconnect; application logic must decide how to recover.

## Query, change and restore speech policy

`SpeechControlRequest` uses `service/speech/speech_control.fbs`. Its application
fields are `request_type`, `enable`, and `mode`. The complete operation list is
in that Schema; the following operations support independent voice applications:

| Request | Meaning |
| --- | --- |
| `request_type=1` | Query command-recognition state |
| `request_type=2` | Query ordinary chat state |
| `request_type=3, mode=0, enable=false` | Disable ordinary body keyword recognition / wake-up admission |
| `request_type=3, mode=0, enable=true` | Enable local recognition mode (`1`) |
| `request_type=3, mode=1` or `2` | Select local (`1`) or server (`2`) recognition; nonzero `mode` overrides `enable` |
| `request_type=4, enable=false` | Disable ordinary built-in chat policy |

Read and save `cmd_recognition_mode`, `chat_function_status`, and any other
setting your application changes before setting policy. Call the service with
a bounded timeout; inspect Aorta `status`/`message` or ROS `success`/`message`,
then query again. On exit, restore the saved state and verify it. To restore
recognition mode `0`, use `mode=0, enable=false`; to restore `1` or `2`, use
that nonzero mode. Do not assume defaults or replay an ambiguous timed-out
state-changing request automatically.

These settings govern admission and speech policy, not a global audio hardware
mute or an immediate cancellation of a conversation already in progress.
Disabling ordinary recognition and chat does **not** disable the independent
UWB push-to-talk path; it can still produce ASR and responses. Mode restrictions
remain provider-owned. Do not use this interface as an emergency stop or to
claim exclusive ownership of every voice input path.

## Troubleshooting

- Missing type or permission: check matching application, Schema, Bridge and ACL
  versions. Do not widen ACLs or retain the obsolete topic as a workaround.
- No sound: check frame format/count, publisher pacing, volume, speech-service
  state and competing audio. Check Bridge diagnostics for ownership, size,
  stale-frame and format rejection; do not infer success from topic discovery.
- Policy unchanged: inspect the response and query effective state again.
  Check `mode` precedence and provider restrictions. UWB continuing to respond
  is not proof that ordinary-body recognition remained enabled.
