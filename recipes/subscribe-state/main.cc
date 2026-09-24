#include "locomotion_status_generated.h"
#include "recipes/cpp_common.h"

int main(int argc, char **argv) {
  return recipe::Run([&] {
    auto args = recipe::Parse(argc, argv, "subscribe-state");
    const std::string route = "/locomotion/status";
    if (recipe::Preview(args, route,
                        ",\"count\":" + std::to_string(args.count)))
      return 0;
    auto node = recipe::OpenNode("vbot_lab_cpp_state");
    recipe::Inbox inbox(node, route);
    auto end = recipe::After(args.timeout);
    for (int i = 0; i < args.count; ++i) {
      auto bytes =
          inbox.Next(end); // Own the bytes for the entire accessor lifetime.
      const auto *message = recipe::Decode<locomotion::LocomotionStatus>(bytes);
      recipe::Emit(
          "\"heartbeat_seq\":" + std::to_string(message->heartbeat_seq()) +
          ",\"posture\":" + std::to_string(message->posture()) +
          ",\"motion\":" + std::to_string(message->motion()) +
          ",\"current_action\":" +
          recipe::Json(recipe::Text(message->current_action())) +
          ",\"stamp_ns\":" + std::to_string(message->stamp_ns()));
    }
    return 0;
  });
}
