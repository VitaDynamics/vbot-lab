#include "RawAudio_generated.h"
#include "audio_done_generated.h"
#include "recipes/cpp_common.h"
#include <tuple>

int main(int argc, char **argv) {
  return recipe::Run([&] {
    auto args = recipe::Parse(argc, argv, "audio");
    const std::map<std::string, std::string> routes = {
        {"body", "/raw_audio_dump"},
        {"uwb", "/audio/uwb_adpcm_segment"},
        {"uwb-end", "/uwb/audio_done"}};
    const auto &route = routes.at(args.source);
    if (recipe::Preview(args, route))
      return 0;
    auto node = recipe::OpenNode("vbot_lab_cpp_audio");
    recipe::Output output(args.output);
    recipe::Inbox inbox(node, route);
    std::optional<std::tuple<std::string, uint32_t, uint32_t>> format;
    auto end = recipe::After(args.timeout);
    int count = 0;
    while (count < args.count) {
      auto bytes = inbox.Next(end);
      if (args.source == "uwb-end") {
        const auto *message = recipe::Decode<aorta::uwb::AudioDoneEvent>(bytes);
        const auto *context = message->user_interaction_context();
        recipe::Emit(
            "\"timestamp_ns\":" + std::to_string(message->timestamp_ns()) +
            ",\"interaction_id\":" +
            (context
                 ? recipe::Json(recipe::Text(context->user_interaction_id()))
                 : "null"));
      } else {
        const auto *message = recipe::Decode<foxglove::RawAudio>(bytes);
        const auto *data = message->data();
        if (!data)
          throw std::runtime_error("missing audio payload");
        auto current = std::make_tuple(recipe::Text(message->format()),
                                       uint32_t(message->sample_rate()),
                                       uint32_t(message->number_of_channels()));
        if (output.active() && format && *format != current)
          throw std::runtime_error("audio format changed; output is partial");
        format = current;
        auto offset = output.size();
        output.Write(data->data(), data->size());
        const auto *stamp = message->timestamp();
        const auto *context = message->user_interaction_context();
        recipe::Emit(
            "\"source\":" + recipe::Json(args.source) +
            ",\"format\":" + recipe::Json(std::get<0>(current)) +
            ",\"sample_rate\":" + std::to_string(message->sample_rate()) +
            ",\"channels\":" + std::to_string(message->number_of_channels()) +
            ",\"bytes\":" + std::to_string(data->size()) + ",\"offset\":" +
            (output.active() ? std::to_string(offset) : "null") +
            ",\"timestamp_sec\":" +
            (stamp ? std::to_string(stamp->sec()) : "null") +
            ",\"timestamp_nsec\":" +
            (stamp ? std::to_string(stamp->nsec()) : "null") +
            ",\"interaction_id\":" +
            (context
                 ? recipe::Json(recipe::Text(context->user_interaction_id()))
                 : "null"));
      }
      ++count;
    }
    return 0;
  });
}
