#include "CompressedVideo_generated.h"
#include "recipes/cpp_common.h"
#ifdef VBOT_CAMERA_DECODE
#include "recipes/camera/decoder.h"
#endif

int main(int argc, char **argv) {
  return recipe::Run([&] {
    auto args = recipe::Parse(argc, argv, "camera");
    const std::string route = "/image_" + args.camera + "_raw/h265";
    if (recipe::Preview(args, route,
                        ",\"output\":" + recipe::Json(args.output)))
      return 0;
    auto node = recipe::OpenNode("vbot_lab_cpp_camera");
    recipe::Output output(args.output);
#ifdef VBOT_CAMERA_DECODE
    std::unique_ptr<recipe::Decoder> decoder;
    if (args.decode)
      decoder = std::make_unique<recipe::Decoder>();
    size_t decoded_bytes = 0;
#endif
    recipe::Inbox inbox(node, route);
    auto end = recipe::After(args.timeout);
    for (int i = 0; i < args.count; ++i) {
      auto bytes = inbox.Next(end);
      const auto *message = recipe::Decode<foxglove::CompressedVideo>(bytes);
      if (recipe::Text(message->format()) != "h265")
        throw std::runtime_error("expected H.265");
      const auto *data = message->data();
      const auto *stamp = message->timestamp();
      if (!data)
        throw std::runtime_error("missing compressed payload");
      recipe::Emit("\"format\":\"h265\",\"frame_id\":" +
                   recipe::Json(recipe::Text(message->frame_id())) +
                   ",\"bytes\":" + std::to_string(data->size()) +
                   ",\"timestamp_sec\":" +
                   (stamp ? std::to_string(stamp->sec()) : "null") +
                   ",\"timestamp_nsec\":" +
                   (stamp ? std::to_string(stamp->nsec()) : "null"));
      // Annex B compressed bytes, NOT RGB/JPEG. Keep one decoder per stream.
      // This buffer is borrowed from bytes; consume/copy it before the next
      // loop.
      output.Write(data->data(), data->size());
#ifdef VBOT_CAMERA_DECODE
      if (decoder) {
        decoded_bytes += data->size();
        if (decoded_bytes > 16 * 1024 * 1024)
          throw std::runtime_error("16 MiB capture limit reached");
        decoder->Feed(data->data(), data->size());
      }
#endif
    }
#ifdef VBOT_CAMERA_DECODE
    if (decoder)
      decoder->Finish();
#endif
    return 0;
  });
}
