"""Query device firmware without changing device state."""

from recipes.common import device_node, emit, parser, rpc, run, text

DEVICES = {"motor": 0, "servo": 1, "lidar": 2, "uwb": 3}


def request_fill(schema, device_type):
    def fill(builder, header):
        schema.GetFirmwareVersionRequestStart(builder)
        schema.GetFirmwareVersionRequestAddAortaHeader(builder, header)
        schema.GetFirmwareVersionRequestAddTargetDeviceType(builder, device_type)
        return schema.GetFirmwareVersionRequestEnd(builder)
    return fill


def main(argv=None):
    cli = parser(__doc__)
    cli.add_argument("--device", choices=DEVICES, default="motor")
    args = cli.parse_args(argv)
    route = f"/firmware_version/{args.device}"
    if not args.execute:
        emit(operation="service", route=route, target_device_type=DEVICES[args.device], execute=False)
        return 0
    with device_node("vbot_lab_device_info") as (sdk, node):
        import get_firmware_version_schema_meta as schema
        from aorta.services.system.GetFirmwareVersionResponse import GetFirmwareVersionResponse
        response = rpc(node, sdk, route, schema, GetFirmwareVersionResponse,
                       request_fill(schema, DEVICES[args.device]), args.timeout)
        emit(status=response.Status(), message=text(response.Message()), versions=[
            {"device_id": response.Versions(i).DeviceId(),
             "sw_version": text(response.Versions(i).SwVersion()),
             "hw_version": text(response.Versions(i).HwVersion())}
            for i in range(response.VersionsLength())])
        return 0 if response.Status() == 0 else 1


if __name__ == "__main__":
    raise SystemExit(run(main))
