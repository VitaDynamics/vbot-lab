#include "CompressedVideo_generated.h"
#include "recipes/camera/decoder.h"
extern "C" {
#include <libavutil/opt.h>
}

int main() {
  return recipe::Run([] {
    // Generate a tiny local H.265 frame; no camera, Node, files or device
    // session.
    const auto *encoder = avcodec_find_encoder_by_name("libx265");
    if (!encoder)
      throw std::runtime_error(
          "this optional decoder test requires the libx265 encoder");
    std::unique_ptr<AVCodecContext, recipe::CodecFree> context(
        avcodec_alloc_context3(encoder));
    std::unique_ptr<AVFrame, recipe::FrameFree> frame(av_frame_alloc());
    std::unique_ptr<AVPacket, recipe::PacketFree> packet(av_packet_alloc());
    if (!context || !frame || !packet)
      throw std::runtime_error("test allocation failed");
    context->width = 64;
    context->height = 64;
    context->pix_fmt = AV_PIX_FMT_YUV420P;
    context->time_base = AVRational{1, 30};
    context->gop_size = 1;
    context->max_b_frames = 0;
    context->thread_count = 1;
    if (av_opt_set(context->priv_data, "preset", "ultrafast", 0) < 0 ||
        av_opt_set(context->priv_data, "x265-params",
                   "log-level=error:pools=none:frame-threads=1", 0) < 0 ||
        avcodec_open2(context.get(), encoder, nullptr) < 0)
      throw std::runtime_error("test encoder setup failed");
    frame->width = 64;
    frame->height = 64;
    frame->format = AV_PIX_FMT_YUV420P;
    if (av_frame_get_buffer(frame.get(), 32) < 0)
      throw std::runtime_error("test frame allocation failed");
    for (int plane = 0; plane < 3; ++plane)
      std::memset(frame->data[plane], 128,
                  frame->linesize[plane] * (plane == 0 ? 64 : 32));
    if (avcodec_send_frame(context.get(), frame.get()) < 0 ||
        avcodec_send_frame(context.get(), nullptr) < 0)
      throw std::runtime_error("test encoding failed");
    std::ostringstream output;
    auto *old = std::cout.rdbuf(output.rdbuf());
    try {
      recipe::Decoder decoder;
      int result;
      while ((result = avcodec_receive_packet(context.get(), packet.get())) ==
             0) {
        flatbuffers::FlatBufferBuilder builder;
        auto data = builder.CreateVector(packet->data, packet->size);
        auto format = builder.CreateString("h265");
        auto id = builder.CreateString("synthetic");
        foxglove::CompressedVideoBuilder video(builder);
        video.add_data(data);
        video.add_format(format);
        video.add_frame_id(id);
        builder.Finish(video.Finish());
        recipe::Bytes bytes(builder.GetBufferPointer(),
                            builder.GetBufferPointer() + builder.GetSize());
        const auto *sample = recipe::Decode<foxglove::CompressedVideo>(bytes);
        decoder.Feed(sample->data()->data(), sample->data()->size());
        av_packet_unref(packet.get());
      }
      if (result != AVERROR_EOF)
        throw std::runtime_error("test encoder did not flush");
      decoder.Finish();
    } catch (...) {
      std::cout.rdbuf(old);
      throw;
    }
    std::cout.rdbuf(old);
    if (output.str().find("\"image_width\":64,\"image_height\":64") ==
        std::string::npos)
      throw std::runtime_error(
          "decoded dimensions do not match synthetic frame");
    std::cout << "Synthetic H.265 to RGB decode passed\n";
    return 0;
  });
}
