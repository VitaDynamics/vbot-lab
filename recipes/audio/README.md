# Read audio and ASR

<p align="center">English | <a href="README.zh-CN.md">中文</a></p>

[Recipes index](../README.md) · [Python](main.py) · [C++](main.cc)

Interface: `/raw_audio_dump`, `/audio/uwb_adpcm_segment`, `/speech/asr_result`, `/uwb/audio_done` — pub/sub.

Generated types: `foxglove.RawAudio`, `aorta.topic.speech.AsrResult`, `aorta.uwb.AudioDoneEvent`.

`--source body` reads the robot's microphones; `--source uwb` reads compressed audio carried by UWB signalling (ADPCM, 8 kHz, mono). Read the body stream's format/rate/channels from each message; do not assume it has the UWB encoding. `--source asr` reads recognized text: provider BODY=1 means body microphones, TAG=2 means UWB, UNKNOWN=0 stays unknown. `--provider body|tag` filters ASR, not raw audio. `--source uwb-end` reads input transmission completion with optional interaction ID, not recognition or playback completion.

## Python: build and offline preview

Binary recording with `--output` requires `numpy==2.2.6` for bulk payload extraction.
Prepare its matching wheel through the [offline guide](../../docs/development/offline-build.md).
Metadata and ASR subscriptions do not need NumPy.

```bash
bazel build //recipes/audio:main
bazel run //recipes/audio:main
```

By default, prints only a JSON request plan: no SDK installation, device connection, or request.

## Python: run on the robot

First complete [Python deployment](../../docs/development/python-deployment.md): transfer this recipe and matching wheels, then create the device venv. In the resulting application directory (APP_DIR), with its venv activated and device environment configured, run:

```bash
python -m recipes.audio.main --source asr --provider tag --consent --execute --count 1 --timeout 20
```

All live voice access requires participant permission and `--consent`. Additional entry points:

```bash
python -m recipes.audio.main --source body --consent --execute --count 10
python -m recipes.audio.main --source uwb --consent --execute --count 10 --output uwb.adpcm > uwb.frames.jsonl
python -m recipes.audio.main --source uwb-end --consent --execute --timeout 20
```

Raw output is concatenated payload bytes, not WAV, decoded PCM, or a guaranteed complete utterance. Keep the JSONL metadata (offsets, lengths and timestamps) with it to retain frame boundaries. Recording fails on an encoding/rate/channel change. UWB input-end events are a separate subscription: a complete application should subscribe to both before input begins and use the available interaction context; these short commands do not reconstruct a recording session. Unknown ASR providers are never relabelled as BODY or TAG.

## C++

First follow the [C++ SDK guide](../../packages/aorta/cpp/README.md) for matching SDK/Schema archives, compiler and two artifact paths. On the build machine, build the C++ target explicitly; even previews require SDK linkage, but never create a Node or access a device:

```bash
bazel build //recipes/audio:main_cpp
bazel run //recipes/audio:main_cpp
```

Follow [binary deployment](../../packages/aorta/cpp/README.md#run-on-the-robot) with RECIPE=audio. After vbot SSH login, switch to the deployed application directory and configure the shell and library path as shown there. With the task prerequisites above satisfied, run the executable directly:

```bash
./bin/audio --source asr --provider tag --consent --execute --count 1 --timeout 20
```

The robot does not need Bazel, a compiler, or a repository checkout. C++ uses the same routes, operation permissions and completion conditions as Python; read-only subscriptions never publish commands.

C++ uses the same source rules for frame metadata, ASR providers and input-end events. Keep JSONL alongside binary data for frame boundaries:

```bash
./bin/audio --source body --consent --execute --count 10
./bin/audio --source uwb --consent --execute --count 10 --output uwb.adpcm > uwb.frames.jsonl
./bin/audio --source uwb-end --consent --execute --timeout 20
```

## Completion, failures and exit

Output is JSON Lines. Exit 0 means the example finished (including an offline preview), 1 runtime failure/timeout, 2 invalid arguments, and 130 interruption. Check the execute flag and output semantics; a preview is not live success. Waits are bounded; receive-queue overflow is an error rather than silently claiming complete data. Subscribers, clients and Node are closed on exit.

Files are created exclusively, never overwritten. Limits are 8 MiB per sample and 16 MiB per capture. Failure/interruption may leave a partial file; inspect the error and retain or remove it according to privacy requirements.

For tests, see [Recipes](../README.md); default tests never connect to or operate a robot.
