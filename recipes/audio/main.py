"""Read body/UWB audio, source-labelled ASR, or UWB input-end events."""

from contextlib import ExitStack
import time
from recipes.common import byte_vector, device_node, emit, exclusive_output, inbox, parser, run, text

TOPICS = {"body": "/raw_audio_dump", "uwb": "/audio/uwb_adpcm_segment",
          "asr": "/speech/asr_result", "uwb-end": "/uwb/audio_done"}
PROVIDERS = {0: "UNKNOWN", 1: "BODY", 2: "TAG"}


def provider_matches(provider, selection):
    return selection == "all" or provider == {"body": 1, "tag": 2}[selection]


def main(argv=None):
    cli = parser(__doc__, stream=True)
    cli.add_argument("--source", choices=TOPICS, default="asr")
    cli.add_argument("--provider", choices=("all", "body", "tag"), default="all")
    cli.add_argument("--consent", action="store_true", help="confirm participant permission for voice/transcript access")
    cli.add_argument("--output", help="new binary audio payload file; metadata stays on stdout")
    args = cli.parse_args(argv)
    if args.execute and not args.consent:
        cli.error("live voice access requires --consent")
    if args.output and args.source not in ("body", "uwb"):
        cli.error("--output is only for body or uwb audio frames")
    if args.provider != "all" and args.source != "asr":
        cli.error("--provider only applies to ASR")
    if not args.execute:
        emit(operation="subscribe", topic=TOPICS[args.source], provider=args.provider,
             count=args.count, output=args.output, execute=False)
        return 0
    with ExitStack() as stack:
        sdk, node = stack.enter_context(device_node("vbot_lab_audio"))
        from foxglove.RawAudio import RawAudio
        from aorta.topic.speech.AsrResult import AsrResult
        from aorta.uwb.AudioDoneEvent import AudioDoneEvent
        root = {"asr": AsrResult, "uwb-end": AudioDoneEvent}.get(args.source, RawAudio)
        output = stack.enter_context(exclusive_output(args.output)) if args.output else None
        receive = stack.enter_context(inbox(node, sdk, TOPICS[args.source]))
        deadline = time.monotonic() + args.timeout
        count = total = 0
        recording_format = None
        while count < args.count:
            message = root.GetRootAs(receive(deadline), 0)
            if args.source == "asr":
                if not provider_matches(message.Provider(), args.provider):
                    continue
                emit(provider=PROVIDERS.get(message.Provider(), "UNKNOWN"),
                     provider_value=message.Provider(), text=text(message.Text()))
            elif args.source == "uwb-end":
                context = message.UserInteractionContext()
                emit(timestamp_ns=message.TimestampNs(),
                     interaction_id=text(context.UserInteractionId()) if context else None)
            else:
                audio_format = (text(message.Format()), message.SampleRate(), message.NumberOfChannels())
                stamp = message.Timestamp()
                context = message.UserInteractionContext()
                if output:
                    if recording_format is not None and audio_format != recording_format:
                        raise ValueError("audio format changed; output is partial")
                    recording_format = audio_format
                    data = byte_vector(message)
                    if total + len(data) > 16 * 1024 * 1024:
                        raise ValueError("16 MiB capture limit reached; output is partial")
                    output.write(data)
                emit(source=args.source, format=audio_format[0], sample_rate=audio_format[1],
                     channels=audio_format[2], bytes=message.DataLength(),
                     offset=total if output else None,
                     timestamp={"sec": stamp.Sec(), "nsec": stamp.Nsec()} if stamp else None,
                     interaction_id=text(context.UserInteractionId()) if context else None)
                if output:
                    total += len(data)
            count += 1
    return 0


if __name__ == "__main__":
    raise SystemExit(run(main))
