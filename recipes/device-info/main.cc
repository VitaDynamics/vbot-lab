#include "recipes/cpp_common.h"
#include "system_get_firmware_version_msg.h"

int main(int argc, char **argv) {
  return recipe::Run([&] {
    auto args = recipe::Parse(argc, argv, "device-info");
    const std::string route = "/firmware_version/" + args.device;
    if (recipe::Preview(args, route))
      return 0;
    auto node = recipe::OpenNode("vbot_lab_cpp_device_info");
    namespace msg = aorta::services::system;
    const std::map<std::string, msg::DeviceType> types = {
        {"motor", msg::DeviceType_MOTOR},
        {"servo", msg::DeviceType_SERVO},
        {"lidar", msg::DeviceType_LIDAR},
        {"uwb", msg::DeviceType_UWB}};
    auto client =
        recipe::Must(node->CreateClientTyped<msg::GetFirmwareVersionRequest,
                                             msg::GetFirmwareVersionResponse>(
            route, recipe::ClientOptions(args.timeout)));
    // The typed client supplies the Aorta header and checks service schema
    // hashes.
    auto response = recipe::Must(
        client->Call([&](msg::GetFirmwareVersionRequestMsg &request) {
          request.target_device_type = types.at(args.device);
        }));
    const auto *result =
        response.Message(); // Borrowed until response is destroyed.
    recipe::Emit(
        "\"status\":" + std::to_string(result->status()) +
        ",\"message\":" + recipe::Json(recipe::Text(result->message())));
    if (result->versions())
      for (const auto *version : *result->versions())
        recipe::Emit("\"device_id\":" + std::to_string(version->device_id()) +
                     ",\"sw_version\":" +
                     recipe::Json(recipe::Text(version->sw_version())) +
                     ",\"hw_version\":" +
                     recipe::Json(recipe::Text(version->hw_version())));
    return result->status() == aorta::services::common::ServiceStatus_SUCCESS
               ? 0
               : 1;
  });
}
