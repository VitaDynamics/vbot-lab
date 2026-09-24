#include "peripheral_get_light_status_msg.h"
#include "recipes/cpp_common.h"

int main(int argc, char **argv) {
  return recipe::Run([&] {
    auto args = recipe::Parse(argc, argv, "service-call");
    const std::string route = "/light_node/status";
    if (recipe::Preview(args, route))
      return 0;
    auto node = recipe::OpenNode("vbot_lab_cpp_light_status");
    namespace msg = aorta::services::peripheral;
    auto client =
        recipe::Must(node->CreateClientTyped<msg::GetLightStatusRequest,
                                             msg::GetLightStatusResponse>(
            route, recipe::ClientOptions(args.timeout)));
    auto response =
        recipe::Must(client->Call([](msg::GetLightStatusRequestMsg &) {}));
    const auto *result = response.Message();
    recipe::Emit(
        "\"status\":" + std::to_string(result->status()) + ",\"enabled\":" +
        (result->is_enabled() ? std::string("true") : "false") +
        ",\"mode\":" + std::to_string(result->current_mode()) +
        ",\"red\":" + std::to_string(result->current_red()) +
        ",\"green\":" + std::to_string(result->current_green()) +
        ",\"blue\":" + std::to_string(result->current_blue()) +
        ",\"brightness\":" + std::to_string(result->current_brightness()));
    return result->status() == aorta::services::common::ServiceStatus_SUCCESS
               ? 0
               : 1;
  });
}
