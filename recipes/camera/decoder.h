#pragma once
#include "recipes/cpp_common.h"
extern "C" {
#include <libavcodec/avcodec.h>
#include <libswscale/swscale.h>
}

namespace recipe {
struct CodecFree {
  void operator()(AVCodecContext *p) const { avcodec_free_context(&p); }
};
struct FrameFree {
  void operator()(AVFrame *p) const { av_frame_free(&p); }
};
struct PacketFree {
  void operator()(AVPacket *p) const { av_packet_free(&p); }
};
struct ScaleFree {
  void operator()(SwsContext *p) const { sws_freeContext(p); }
};

// Optional software decoder. One instance per stream; decoded RGB is
// application memory, not a pointer into a received Aorta sample or an FFmpeg
// frame.
class Decoder {
public:
  Decoder() {
    const auto *codec = avcodec_find_decoder(AV_CODEC_ID_HEVC);
    if (!codec)
      throw std::runtime_error("FFmpeg HEVC decoder is unavailable");
    codec_.reset(avcodec_alloc_context3(codec));
    frame_.reset(av_frame_alloc());
    if (!codec_ || !frame_)
      throw std::runtime_error("decoder allocation failed");
    codec_->thread_count = 1;
    codec_->max_pixels = 32 * 1024 * 1024 / 3;
    if (avcodec_open2(codec_.get(), codec, nullptr) < 0)
      throw std::runtime_error("HEVC decoder open failed");
  }
  void Feed(const uint8_t *bytes, size_t size) {
    if (size > kMaxSample)
      throw std::runtime_error("video sample too large");
    std::unique_ptr<AVPacket, PacketFree> packet(av_packet_alloc());
    if (!packet || av_new_packet(packet.get(), static_cast<int>(size)) < 0)
      throw std::runtime_error("packet allocation failed");
    std::memcpy(packet->data, bytes, size);
    Send(packet.get());
  }
  void Finish() {
    Send(nullptr);
    if (images_ == 0)
      throw std::runtime_error(
          "no decoded image; wait for a keyframe with VPS/SPS/PPS");
  }

private:
  void Send(const AVPacket *packet) {
    int result = avcodec_send_packet(codec_.get(), packet);
    if (result == AVERROR(EAGAIN)) {
      Drain();
      result = avcodec_send_packet(codec_.get(), packet);
    }
    if (result == AVERROR_INVALIDDATA) {
      Emit("\"waiting_for_keyframe\":true");
      return;
    }
    if (result < 0 && result != AVERROR_EOF)
      throw std::runtime_error("video decode failed");
    Drain();
  }
  void Drain() {
    while (true) {
      CheckInterrupt();
      int result = avcodec_receive_frame(codec_.get(), frame_.get());
      if (result == AVERROR(EAGAIN) || result == AVERROR_EOF)
        return;
      if (result == AVERROR_INVALIDDATA) {
        Emit("\"waiting_for_keyframe\":true");
        return;
      }
      if (result < 0)
        throw std::runtime_error("video frame decode failed");
      int width = frame_->width, height = frame_->height;
      if (width <= 0 || height <= 0 ||
          int64_t(width) * height * 3 > 32 * 1024 * 1024)
        throw std::runtime_error("decoded image exceeds 32 MiB RGB limit");
      std::unique_ptr<SwsContext, ScaleFree> scale(sws_getContext(
          width, height, static_cast<AVPixelFormat>(frame_->format), width,
          height, AV_PIX_FMT_RGB24, SWS_BILINEAR, nullptr, nullptr, nullptr));
      if (!scale)
        throw std::runtime_error("RGB conversion setup failed");
      std::vector<uint8_t> rgb(size_t(width) * height * 3);
      uint8_t *planes[] = {rgb.data(), nullptr, nullptr, nullptr};
      int strides[] = {width * 3, 0, 0, 0};
      if (sws_scale(scale.get(), frame_->data, frame_->linesize, 0, height,
                    planes, strides) != height)
        throw std::runtime_error("incomplete RGB conversion");
      // Consume rgb here, or move it to application-owned storage; no image
      // or transcript content is persisted by this decoder.
      Emit("\"image_width\":" + std::to_string(width) +
           ",\"image_height\":" + std::to_string(height) +
           ",\"pixel_format\":\"rgb24\",\"row_stride\":" +
           std::to_string(strides[0]));
      ++images_;
      av_frame_unref(frame_.get());
    }
  }
  std::unique_ptr<AVCodecContext, CodecFree> codec_;
  std::unique_ptr<AVFrame, FrameFree> frame_;
  size_t images_ = 0;
};
} // namespace recipe
