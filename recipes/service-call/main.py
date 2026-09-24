"""Read ear-light status using a typed request/reply service."""

from recipes.common import device_node, emit, parser, rpc, run, text

ROUTE = "/light_node/status"


def request_fill(schema):
    def fill(builder, header):
        schema.GetLightStatusRequestStart(builder)
        schema.GetLightStatusRequestAddAortaHeader(builder, header)
        return schema.GetLightStatusRequestEnd(builder)
    return fill


def main(argv=None):
    args = parser(__doc__).parse_args(argv)
    if not args.execute:
        emit(operation="service", route=ROUTE, execute=False)
        return 0
    with device_node("vbot_lab_light_status") as (sdk, node):
        import get_light_status_schema_meta as schema
        from aorta.services.peripheral.GetLightStatusResponse import GetLightStatusResponse
        response = rpc(node, sdk, ROUTE, schema, GetLightStatusResponse,
                       request_fill(schema), args.timeout)
        emit(status=response.Status(), enabled=response.IsEnabled(), mode=response.CurrentMode(),
             rgb=[response.CurrentRed(), response.CurrentGreen(), response.CurrentBlue()],
             brightness=response.CurrentBrightness(), message=text(response.Message()))
        return 0 if response.Status() == 0 else 1


if __name__ == "__main__":
    raise SystemExit(run(main))
