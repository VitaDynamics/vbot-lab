// Test the native SDK boundary without opening a device or loading vendor code.
#include "recipes/camera/h265_start.h"
#include "recipes/camera/s100_decoder.h"
#include <array>

namespace {
struct State {
  int initialize = 0, configure = 0, start = 0, stop = 0, release = 0;
  int input_get = 0, input_queue = 0, output_get = 0, output_queue = 0;
  int input_timeouts = 0, pending = 0, empty_status_reads = 0;
  bool configure_fail = false, input_queue_fail = false, invalid_frame = false;
  bool stop_fail = false, borrowed = false, status_fail = false;
  uint64_t pts = 0;
  std::array<uint8_t, 128> input{}, y{}, uv{};
} state;

void Require(bool condition, const char *message) {
  if (!condition)
    throw std::runtime_error(message);
}
template <class F> void Fails(F function) {
  bool failed = false;
  try {
    function();
  } catch (const std::exception &) {
    failed = true;
  }
  Require(failed, "expected operation to fail");
}
std::vector<uint8_t> Nal(unsigned type, bool short_prefix = false) {
  std::vector<uint8_t> bytes = short_prefix ? std::vector<uint8_t>{0, 0, 1}
                                            : std::vector<uint8_t>{0, 0, 0, 1};
  bytes.insert(bytes.end(), {static_cast<uint8_t>(type << 1), 1, 0x7f});
  return bytes;
}
void Feed(recipe::S100Decoder &decoder) {
  const uint8_t bytes[] = {0, 0, 0, 1, 0x26, 1};
  decoder.Feed(bytes, sizeof(bytes), 1234567, recipe::After(1));
}
} // namespace

extern "C" {
hb_s32 hb_mm_mc_get_default_context(media_codec_id_t id, hb_bool encoder,
                                    media_codec_context_t *context) {
  *context = {};
  context->codec_id = id;
  context->encoder = encoder;
  return 0;
}
hb_s32 hb_mm_mc_initialize(media_codec_context_t *context) {
  ++state.initialize;
  Require(context->codec_id == MEDIA_CODEC_ID_H265 && !context->encoder,
          "expected native H.265 decoder");
  Require(context->video_dec_params.feed_mode == MC_FEEDING_MODE_FRAME_SIZE,
          "expected access-unit feeding");
  return 0;
}
hb_s32 hb_mm_mc_configure(media_codec_context_t *) {
  ++state.configure;
  return state.configure_fail ? HB_MEDIA_ERR_INVALID_PARAMS : 0;
}
hb_s32 hb_mm_mc_start(media_codec_context_t *,
                      const mc_av_codec_startup_params_t *) {
  ++state.start;
  return 0;
}
hb_s32 hb_mm_mc_stop(media_codec_context_t *) {
  ++state.stop;
  return state.stop_fail ? HB_MEDIA_ERR_UNKNOWN : 0;
}
hb_s32 hb_mm_mc_release(media_codec_context_t *) {
  ++state.release;
  return 0;
}
hb_s32 hb_mm_mc_get_status(media_codec_context_t *, mc_inter_status_t *status) {
  *status = {};
  if (state.status_fail)
    return HB_MEDIA_ERR_UNKNOWN;
  if (state.empty_status_reads-- > 0)
    return 0;
  status->cur_output_buf_cnt = state.pending;
  return 0;
}
hb_s32 hb_mm_mc_dequeue_input_buffer(media_codec_context_t *,
                                     media_codec_buffer_t *buffer, hb_s32) {
  ++state.input_get;
  if (state.input_timeouts-- > 0)
    return HB_MEDIA_ERR_WAIT_TIMEOUT;
  buffer->vstream_buf.vir_ptr = state.input.data();
  buffer->vstream_buf.size = state.input.size();
  return 0;
}
hb_s32 hb_mm_mc_queue_input_buffer(media_codec_context_t *,
                                   media_codec_buffer_t *buffer, hb_s32) {
  ++state.input_queue;
  state.pts = buffer->vstream_buf.pts;
  ++state.pending;
  return state.input_queue_fail ? HB_MEDIA_ERR_UNKNOWN : 0;
}
hb_s32 hb_mm_mc_dequeue_output_buffer(media_codec_context_t *,
                                      media_codec_buffer_t *buffer,
                                      media_codec_output_buffer_info_t *info,
                                      hb_s32) {
  ++state.output_get;
  if (!state.pending)
    return HB_MEDIA_ERR_WAIT_TIMEOUT;
  Require(!state.borrowed, "previous output was not returned");
  --state.pending;
  state.borrowed = true;
  info->video_frame_info.decode_result = 1;
  auto &frame = buffer->vframe_buf;
  frame.vir_ptr[0] = state.invalid_frame ? nullptr : state.y.data();
  frame.vir_ptr[1] = state.uv.data();
  frame.width = 8;
  frame.height = 4;
  frame.stride = 16;
  frame.vstride = 16;
  frame.size = 96;
  frame.pix_fmt = MC_PIXEL_FORMAT_NV12;
  frame.pts = state.pts;
  return 0;
}
hb_s32 hb_mm_mc_queue_output_buffer(media_codec_context_t *,
                                    media_codec_buffer_t *, hb_s32) {
  ++state.output_queue;
  Require(state.borrowed, "output was returned twice");
  state.borrowed = false;
  return 0;
}
}

int main() {
  return recipe::Run([] {
    auto parse = [](std::vector<std::string> values) {
      values.insert(values.begin(), "camera-s100");
      std::vector<char *> argv;
      for (auto &value : values)
        argv.push_back(value.data());
      return recipe::Parse(argv.size(), argv.data(), "camera-s100");
    };
    Require(!parse({}).execute, "default unexpectedly executes");
    Fails([&] { parse({"--execute"}); });
    Fails([&] { parse({"--output", "image.h265"}); });
    Fails([&] { parse({"--decode"}); });
    Fails([&] { parse({"--camera", "unknown"}); });
    Fails([&] { parse({"--count", "0"}); });
    const auto live = parse({"--execute", "--consent", "--camera", "right"});
    Require(live.execute && live.consent && live.camera == "right",
            "live hardware decode options were lost");

    recipe::H265Start gate;
    for (unsigned type : {1, 32, 33, 34}) {
      const auto nal = Nal(type, true);
      Require(gate.Prepare(nal.data(), nal.size()).empty(),
              "started without random-access picture");
    }
    const auto idr = Nal(19);
    const auto initial = gate.Prepare(idr.data(), idr.size());
    Require(initial.size() == 3 * Nal(32, true).size() + idr.size(),
            "parameter sets were not prepended");
    Require(gate.Prepare(idr.data(), idr.size()) == idr,
            "startup state was not retained");
    const uint8_t truncated[] = {0, 0, 1, 0x40};
    Fails([&] {
      recipe::H265Start fresh;
      fresh.Prepare(truncated, sizeof(truncated));
    });

    state = {};
    {
      recipe::S100Decoder decoder;
      decoder.Drain(1, recipe::After(1), [](const auto &) {
        throw std::logic_error("no input was submitted");
      });
      Require(state.output_get == 0, "output was read before the first input");
      state.input_timeouts = 1;
      Feed(decoder);
      int consumed = 0;
      state.empty_status_reads = 1;
      decoder.Drain(2, recipe::After(1), [&](const auto &) { ++consumed; });
      Require(consumed == 0 && state.output_get == 0,
              "output was dequeued before asynchronous readiness");
      decoder.Drain(2, recipe::After(1), [&](const auto &frame) {
        Require(frame.pts == 1234567 && frame.stride == 16,
                "frame metadata changed");
        ++consumed;
      });
      Require(consumed == 1 && state.input_get == 2 && state.output_queue == 1,
              "input timeout or output return handling failed");
      decoder.Close();
    }
    Require(state.stop == 1 && state.release == 1,
            "decoder was not closed exactly once");

    state = {};
    Fails([] {
      recipe::S100Decoder decoder;
      Feed(decoder);
      decoder.Drain(1, recipe::After(1), [](const auto &) {
        throw std::runtime_error("consumer failed");
      });
    });
    Require(state.output_queue == 1 && !state.borrowed && state.release == 1,
            "consumer failure leaked its borrowed output");

    state = {};
    state.invalid_frame = true;
    bool consumer_called = false;
    Fails([&] {
      recipe::S100Decoder decoder;
      Feed(decoder);
      decoder.Drain(1, recipe::After(1),
                    [&](const auto &) { consumer_called = true; });
    });
    Require(!consumer_called && state.output_queue == 1 && state.release == 1,
            "invalid frame was not returned");

    state = {};
    state.configure_fail = true;
    Fails([] { recipe::S100Decoder decoder; });
    Require(state.start == 0 && state.release == 1,
            "constructor failure leaked initialized resources");

    state = {};
    state.input_queue_fail = true;
    Fails([] {
      recipe::S100Decoder decoder;
      Feed(decoder);
    });
    Require(state.input_queue == 1 && state.stop == 1 && state.release == 1,
            "failed input was retried or leaked its decoder");

    state = {};
    state.status_fail = true;
    Fails([] {
      recipe::S100Decoder decoder;
      Feed(decoder);
      decoder.Drain(1, recipe::After(1), [](const auto &) {});
    });
    Require(state.output_get == 0 && state.stop == 1 && state.release == 1,
            "status failure was ignored or leaked its decoder");

    state = {};
    state.stop_fail = true;
    Fails([] {
      recipe::S100Decoder decoder;
      decoder.Close();
    });
    Require(state.release == 1, "release was skipped after stop failure");

    state = {};
    Fails([] {
      recipe::S100Decoder decoder;
      const uint8_t packet = 0;
      decoder.Feed(&packet, 1, 0, recipe::Clock::now());
    });
    Require(state.input_get == 0 && state.release == 1,
            "expired deadline accessed a codec buffer");
    std::cout
        << "S100 codec lifecycle and startup tests passed without a device\n";
    return 0;
  });
}
