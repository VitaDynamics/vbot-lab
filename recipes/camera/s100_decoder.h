#pragma once

#include "recipes/cpp_common.h"
#include <cstring>
extern "C" {
#include <hb_media_codec.h>
#include <hb_media_error.h>
}

namespace recipe {
// Own one native decoder per subscribed stream. No software fallback and no
// camera reconfiguration: the SDK owns all codec input/output allocations.
class S100Decoder {
public:
  S100Decoder() {
    try {
      Check(hb_mm_mc_get_default_context(MEDIA_CODEC_ID_H265, false, &context_),
            "get_default_context");
      context_.encoder = false;
      auto &params = context_.video_dec_params;
      params.feed_mode = MC_FEEDING_MODE_FRAME_SIZE;
      params.pix_fmt = MC_PIXEL_FORMAT_NV12;
      params.bitstream_buf_size = kInputCapacity;
      params.bitstream_buf_count = 4;
      params.frame_buf_count = 5;
      params.external_bitstream_buf = false;
      params.h265_dec_config.bandwidth_Opt = true;
      params.h265_dec_config.reorder_enable = true;
      Check(hb_mm_mc_initialize(&context_), "initialize");
      initialized_ = true;
      Check(hb_mm_mc_configure(&context_), "configure");
      mc_av_codec_startup_params_t startup{};
      Check(hb_mm_mc_start(&context_, &startup), "start");
      started_ = true;
    } catch (...) {
      Cleanup();
      throw;
    }
  }
  ~S100Decoder() { Cleanup(); }
  S100Decoder(const S100Decoder &) = delete;
  S100Decoder &operator=(const S100Decoder &) = delete;

  void Feed(const uint8_t *data, size_t size, uint64_t pts_us, Deadline end) {
    if (!data || size == 0 || size > kInputCapacity)
      throw std::runtime_error("H.265 access unit must contain 1..8 MiB");
    media_codec_buffer_t input{};
    int result;
    do {
      const int wait =
          static_cast<int>(std::min<int64_t>(Remaining(end).count(), 10));
      result = hb_mm_mc_dequeue_input_buffer(&context_, &input, wait);
    } while (result == HB_MEDIA_ERR_WAIT_TIMEOUT);
    Check(result, "dequeue_input_buffer");
    if (!input.vstream_buf.vir_ptr || input.vstream_buf.size < size)
      throw std::runtime_error("native input buffer is missing or too small");
    std::memcpy(input.vstream_buf.vir_ptr, data, size);
    input.vstream_buf.size = static_cast<hb_u32>(size);
    input.vstream_buf.pts = pts_us;
    input.vstream_buf.stream_end = false;
    // Queue once: ownership transfers to the codec. On failure the caller exits
    // and stop/release reclaim instance resources; never submit the buffer
    // twice.
    Check(hb_mm_mc_queue_input_buffer(
              &context_, &input,
              static_cast<int>(std::min<int64_t>(Remaining(end).count(), 10))),
          "queue_input_buffer");
    fed_ = true;
  }

  template <class Consume>
  void Drain(int limit, Deadline end, Consume consume) {
    if (!fed_)
      return;
    for (int i = 0; i < limit; ++i) {
      Remaining(end);
      // The native output component is created asynchronously after stream
      // headers arrive. Ask for completed output before borrowing a buffer;
      // dequeuing before it is ready is not reported as a wait timeout.
      mc_inter_status_t status{};
      Check(hb_mm_mc_get_status(&context_, &status), "get_status");
      if (!status.cur_output_buf_cnt)
        return;
      media_codec_buffer_t output{};
      media_codec_output_buffer_info_t info{};
      const int result =
          hb_mm_mc_dequeue_output_buffer(&context_, &output, &info, 0);
      if (result == HB_MEDIA_ERR_WAIT_TIMEOUT)
        return;
      Check(result, "dequeue_output_buffer");
      try {
        const auto &frame = output.vframe_buf;
        if ((info.video_frame_info.decode_result != 1 &&
             info.video_frame_info.decode_result != 16) ||
            !frame.vir_ptr[0] || !frame.vir_ptr[1] || frame.width <= 0 ||
            frame.height <= 0 || frame.stride < frame.width ||
            frame.vstride < frame.width || frame.size == 0 ||
            frame.pix_fmt != MC_PIXEL_FORMAT_NV12)
          throw std::runtime_error(
              "native decoder returned an invalid NV12 frame");
        // Y and UV are borrowed, with independent strides. Consume/copy before
        // this callback returns; queue_output_buffer invalidates these
        // pointers.
        consume(frame);
      } catch (...) {
        const int returned =
            hb_mm_mc_queue_output_buffer(&context_, &output, 10);
        if (returned)
          std::cerr << "native queue_output_buffer during cleanup: " << returned
                    << '\n';
        throw;
      }
      Check(hb_mm_mc_queue_output_buffer(&context_, &output, 10),
            "queue_output_buffer");
    }
  }

  void Close() {
    const int result = Cleanup();
    Check(result, "stop/release");
  }

private:
  static constexpr size_t kInputCapacity = 8 * 1024 * 1024;
  static void Check(int result, const char *operation) {
    if (result)
      throw std::runtime_error(std::string("S100 MediaCodec ") + operation +
                               " failed: " + std::to_string(result));
  }
  int Cleanup() noexcept {
    int stopped = 0, released = 0;
    if (started_) {
      stopped = hb_mm_mc_stop(&context_);
      started_ = false;
    }
    if (initialized_) {
      released = hb_mm_mc_release(&context_);
      initialized_ = false;
    }
    if (stopped || released)
      std::cerr << "native decoder cleanup: stop=" << stopped
                << " release=" << released << '\n';
    return stopped ? stopped : released;
  }
  media_codec_context_t context_{};
  bool initialized_ = false, started_ = false, fed_ = false;
};
} // namespace recipe
