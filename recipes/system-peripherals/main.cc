#include "display_status_generated.h"
#include "recipes/observe.h"
#include "sm_status_generated.h"

using namespace recipe;
int main(int argc, char **argv) {
  return Observe(
      argc, argv, "system",
      {{"system", "/system/sm_status"}, {"display", "/display_node/status"}},
      "system", [](const std::string &stream, const auto &bytes) {
        if (stream == "display") {
          const auto *m =
              Decode<aorta::topic::peripheral::DisplayStatus>(bytes);
          return Object({{"data", Json(Text(m->data()))}});
        }
        const auto *m = Decode<sm::SmStatus>(bytes);
        return Object(
            {{"timestamp_ns", std::to_string(m->sensor_timestamp_ns())},
             {"heartbeat_seq", std::to_string(m->heartbeat_seq())},
             {"category", N(int(m->category()))},
             {"status", N(int(m->status()))},
             {"state_id", N(m->state_id())},
             {"state_name", Json(Text(m->state_name()))},
             {"severity", N(int(m->severity()))},
             {"is_active", B(m->is_active())},
             {"active_state_path",
              Array(m->active_state_path(), [](const auto *state) {
                return Object(
                    {{"state_id", N(state->state_id())},
                     {"state_name", Json(Text(state->state_name()))}});
              })}});
      });
}
