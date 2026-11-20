"""Read body/UWB audio or UWB input-end events."""

from contextlib import ExitStack
import time
from recipes.common import byte_vector, device_node, emit, exclusive_output, inbox, parser, run, text

TOPICS = {"body": "/raw_audio_dump", "uwb": "/audio/uwb_adpcm_segment",
          "uwb-end": "/uwb/audio_done"}


def main(argv=None):
    cli = parser(__doc__, stream=True)
    cli.add_argument("--source", choices=TOPICS, default="body")
    cli.add_argument("--consent", action="store_true", help="confirm participant permission for audio access")
    cli.add_argument("--output", help="new binary audio payload file; metadata stays on stdout")
    args = cli.parse_args(argv)
    if args.execute and not args.consent:
        cli.error("live voice access requires --consent")
    if args.output and args.source not in ("body", "uwb"):
        cli.error("--output is only for body or uwb audio frames")
    if not args.execute:
        emit(operation="subscribe", topic=TOPICS[args.source],
             count=args.count, output=args.output, execute=False)
        return 0
    with ExitStack() as stack:
        sdk, node = stack.enter_context(device_node("vbot_lab_audio"))
        from foxglove.RawAudio import RawAudio
        from aorta.uwb.AudioDoneEvent import AudioDoneEvent
        root = AudioDoneEvent if args.source == "uwb-end" else RawAudio
        output = stack.enter_context(exclusive_output(args.output)) if args.output else None
        receive = stack.enter_context(inbox(node, sdk, TOPICS[args.source]))
        deadline = time.monotonic() + args.timeout
        count = total = 0
        recording_format = None
        while count < args.count:
            message = root.GetRootAs(receive(deadline), 0)
            if args.source == "uwb-end":
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
