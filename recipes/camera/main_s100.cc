#include "CompressedVideo_generated.h"
#include "recipes/camera/h265_start.h"
#include "recipes/camera/s100_decoder.h"

int main(int argc, char **argv) {
  return recipe::Run([&] {
    auto args = recipe::Parse(argc, argv, "camera-s100");
    const std::string route = "/image_" + args.camera + "_raw/h265";
    if (recipe::Preview(args, route, ",\"backend\":\"s100-mediacodec\""))
      return 0;
    if (access("/dev/vpu", R_OK | W_OK) != 0)
      throw std::runtime_error("vbot requires read/write access to /dev/vpu");
    auto node = recipe::OpenNode("vbot_lab_cpp_camera_s100");
    recipe::S100Decoder decoder;
    recipe::Inbox inbox(node, route);
    recipe::H265Start start;
    const auto end = recipe::After(args.timeout);
    int decoded = 0;
    uint64_t submitted = 0;
    bool waiting_reported = false;
    auto consume = [&](const mc_video_frame_buffer_info_t &frame) {
      // Process frame.vir_ptr[0] (Y) and frame.vir_ptr[1] (UV) here, respecting
      // frame.stride / frame.vstride. No pixels are stored or printed.
      ++decoded;
      recipe::Emit("\"backend\":\"s100-mediacodec\",\"decoded_frames\":" +
                   std::to_string(decoded) +
                   ",\"width\":" + std::to_string(frame.width) +
                   ",\"height\":" + std::to_string(frame.height) +
                   ",\"pixel_format\":\"nv12\",\"y_stride\":" +
                   std::to_string(frame.stride) +
                   ",\"uv_stride\":" + std::to_string(frame.vstride) +
                   ",\"pts_us\":" + std::to_string(frame.pts));
    };
    while (decoded < args.count) {
      decoder.Drain(args.count - decoded, end, consume);
      if (decoded == args.count)
        break;
      auto bytes = inbox.Next(end);
      const auto *message = recipe::Decode<foxglove::CompressedVideo>(bytes);
      const auto *stamp = message->timestamp();
      if (recipe::Text(message->format()) != "h265" || !message->data() ||
          !stamp || stamp->nsec() >= 1000000000)
        throw std::runtime_error("invalid H.265 sample or capture timestamp");
      auto packet =
          start.Prepare(message->data()->data(), message->data()->size());
      if (packet.empty()) {
        if (!waiting_reported)
          recipe::Emit("\"waiting_for_vps_sps_pps_keyframe\":true");
        waiting_reported = true;
        continue;
      }
      const uint64_t pts =
          static_cast<uint64_t>(stamp->sec()) * 1000000 + stamp->nsec() / 1000;
      decoder.Feed(packet.data(), packet.size(), pts, end);
      ++submitted;
    }
    decoder.Close();
    recipe::Emit(
        "\"complete\":true,\"decoded_frames\":" + std::to_string(decoded) +
        ",\"submitted_access_units\":" + std::to_string(submitted) +
        ",\"decoder_released\":true");
    return 0;
  });
}
