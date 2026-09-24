"""Read H.265 video frames; optionally save a bounded stream or decode images."""

from contextlib import ExitStack
import time
from recipes.common import byte_vector, device_node, emit, exclusive_output, inbox, parser, run, text

TOPICS = {"left": "/image_left_raw/h265", "right": "/image_right_raw/h265"}


def emit_images(frames):
    count = 0
    for frame in frames:
        rgb = frame.to_rgb()
        # Pixel bytes: bytes(rgb.planes[0]); respect row padding in line_size.
        emit(image_width=rgb.width, image_height=rgb.height,
             pixel_format=rgb.format.name, row_stride=rgb.planes[0].line_size)
        count += 1
    return count


def main(argv=None):
    cli = parser(__doc__, stream=True)
    cli.add_argument("--camera", choices=TOPICS, default="left")
    cli.add_argument("--output", help="new .h265 file; never overwrites a file")
    cli.add_argument("--decode", action="store_true", help="decode RGB frames using optional PyAV")
    cli.add_argument("--consent", action="store_true", help="confirm permission to capture/process images")
    args = cli.parse_args(argv)
    if (args.output or args.decode) and not args.consent:
        cli.error("--output and --decode require --consent")
    if not args.execute:
        emit(operation="subscribe", topic=TOPICS[args.camera], output=args.output,
             decode=args.decode, count=args.count, execute=False)
        return 0
    with ExitStack() as stack:
        sdk, node = stack.enter_context(device_node("vbot_lab_camera"))
        from foxglove.CompressedVideo import CompressedVideo
        output = stack.enter_context(exclusive_output(args.output)) if args.output else None
        decoder = None
        if args.decode:
            import av
            decoder = av.CodecContext.create("hevc", "r")
        receive = stack.enter_context(inbox(node, sdk, TOPICS[args.camera]))
        deadline = time.monotonic() + args.timeout
        total = decoded = 0
        for _ in range(args.count):
            message = CompressedVideo.GetRootAs(receive(deadline), 0)
            encoding = text(message.Format())
            if encoding != "h265":
                raise ValueError(f"expected h265, received {encoding!r}")
            stamp = message.Timestamp()
            emit(format=encoding, frame_id=text(message.FrameId()), bytes=message.DataLength(),
                 timestamp={"sec": stamp.Sec(), "nsec": stamp.Nsec()} if stamp else None)
            if output or decoder:
                data = byte_vector(message)
                total += len(data)
                if total > 16 * 1024 * 1024:
                    raise ValueError("16 MiB capture limit reached; output is partial")
                if output:
                    output.write(data)
                if decoder:
                    try:
                        decoded += emit_images(decoder.decode(av.Packet(data)))
                    except av.error.InvalidDataError:
                        emit(waiting_for_keyframe=True)
        if decoder:
            decoded += emit_images(decoder.decode(None))
        if decoder and not decoded:
            raise RuntimeError("no decoded image; wait for a keyframe with VPS/SPS/PPS and retry deliberately")
    return 0


if __name__ == "__main__":
    raise SystemExit(run(main))
