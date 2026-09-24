"""Bounded read-only recipe runner; generated schema access stays in each recipe."""

import importlib
import math
import time
from recipes.common import device_node, emit, inbox, parser


def vector(value, quaternion=False):
    if value is None:
        return None
    fields = ("X", "Y", "Z", "W") if quaternion else ("X", "Y", "Z")
    return [getattr(value, field)() for field in fields]


def stamp(value):
    return None if value is None else value.Sec() * 1_000_000_000 + value.Nsec()


def finite(value):
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, dict):
        return {key: finite(item) for key, item in value.items()}
    if isinstance(value, list):
        return [finite(item) for item in value]
    return value


def observe(family, routes, summarize, argv=None):
    cli = parser("Read one selected " + family + " stream without changing device state.", stream=True)
    cli.add_argument("--stream", choices=routes, default=next(iter(routes)))
    args = cli.parse_args(argv)
    route, root = routes[args.stream]
    if not args.execute:
        emit(execute=False, operation="subscribe", route=route, root_type=root, count=args.count)
        return 0
    message_type = getattr(importlib.import_module(root), root.rsplit(".", 1)[1])
    with device_node("vbot_lab_" + family.replace("-", "_")) as (sdk, node):
        with inbox(node, sdk, route) as receive:
            deadline = time.monotonic() + args.timeout
            for _ in range(args.count):
                message = message_type.GetRootAs(receive(deadline), 0)
                emit(route=route, **finite(summarize(args.stream, message)))
    return 0
