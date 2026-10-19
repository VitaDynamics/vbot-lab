#include "blueprints/health-monitor/cpp/decoder.h"
#include "recipes/observe.h"
#include <filesystem>
#include <memory>

namespace health {
struct Args {
  bool execute = false, simulate = false, help = false;
  double duration = 10;
  std::string config;
};
Args Parse(int argc, char **argv) {
  Args result;
  std::set<std::string> seen;
  for (int i = 1; i < argc; ++i) {
    const std::string key = argv[i];
    if (!seen.insert(key).second)
      throw std::invalid_argument("repeated option");
    if (key == "--execute")
      result.execute = true;
    else if (key == "--simulate")
      result.simulate = true;
    else if (key == "--help")
      result.help = true;
    else if (key == "--duration" || key == "--config") {
      if (++i == argc)
        throw std::invalid_argument("missing option value");
      if (key == "--duration") {
        result.duration = recipe::Number(argv[i], 0, 120);
        if (result.duration <= 0)
          throw std::invalid_argument("duration must be positive");
      } else {
        result.config = argv[i];
        if (result.config.empty())
          throw std::invalid_argument("empty config path");
      }
    } else
      throw std::invalid_argument("unknown option");
  }
  if (result.execute && result.simulate)
    throw std::invalid_argument(
        "--execute and --simulate are mutually exclusive");
  if (result.config.empty())
    result.config = std::filesystem::is_regular_file("config.json")
                        ? "config.json"
                        : "blueprints/health-monitor/config.json";
  return result;
}
void RequireContainer() {
  const char *declared = std::getenv("VBOT_DEV_CONTAINER");
  if (!declared || std::string(declared) != "1" ||
      (!std::filesystem::is_regular_file("/.dockerenv") &&
       !std::filesystem::is_regular_file("/run/.containerenv")))
    throw std::runtime_error(
        "preview and simulation run in the development container");
}
std::string SnapshotJson(const Snapshot &snapshot) {
  std::string streams = "{";
  for (size_t i = 0; i < kNames.size(); ++i) {
    const auto &value = snapshot.streams[i];
    const auto &data = value.state.data;
    std::string fields = "null";
    if (value.state.received_at) {
      if (i == Index(Stream::Battery))
        fields = recipe::Object({{"soc_percent", recipe::N(data.soc_percent)},
                                 {"voltage_v", recipe::N(data.voltage_v)}});
      else if (i == Index(Stream::State))
        fields = recipe::Object(
            {{"heartbeat_seq", std::to_string(data.heartbeat_seq)},
             {"posture", std::to_string(data.posture)},
             {"motion", std::to_string(data.motion)}});
      else
        fields = recipe::Object(
            {{"heartbeat_seq", std::to_string(data.heartbeat_seq)},
             {"state_id", std::to_string(data.state_id)},
             {"severity", std::to_string(data.severity)}});
    }
    if (i)
      streams += ',';
    streams +=
        recipe::Json(kNames[i]) + ':' +
        recipe::Object(
            {{"status", recipe::Json(value.status)},
             {"age_seconds",
              value.age_seconds ? recipe::N(*value.age_seconds) : "null"},
             {"samples", std::to_string(value.state.samples)},
             {"invalid", std::to_string(value.state.invalid)},
             {"out_of_order", std::to_string(value.state.out_of_order)},
             {"data", fields}});
  }
  return "\"all_streams_receiving\":" +
         recipe::B(snapshot.all_streams_receiving) +
         ",\"low_battery\":" + recipe::B(snapshot.low_battery) +
         ",\"streams\":" + streams + '}';
}

double Now() {
  return std::chrono::duration<double>(recipe::Clock::now().time_since_epoch())
      .count();
}

// One bounded aggregate queue. Callbacks retain shared state, never borrowed
// MessageView storage or a pointer to a potentially destroyed owning object.
class Inbox {
public:
  using Event = ReceivedSample;
  explicit Inbox(const std::shared_ptr<aorta::Node> &node) {
    for (size_t i = 0; i < kNames.size(); ++i) {
      aorta::SubscriberOptions options;
      options.receive_depth = 16;
      auto state = state_;
      subscribers_.push_back(recipe::Must(node->CreateSubscriber(
          kRoutes[i],
          [state, i](const aorta::MessageView &view,
                     const aorta::MessageContextView &) {
            const double received_at = Now();
            std::lock_guard<std::mutex> lock(state->mutex);
            if (view.size > 1024 * 1024 || state->queue.size() >= 64)
              state->overflow = true;
            else
              state->queue.push_back(
                  {static_cast<Stream>(i), view.ToVector(), received_at});
            state->ready.notify_one();
          },
          options)));
    }
  }
  std::optional<Event> Poll(recipe::Deadline end) {
    std::unique_lock<std::mutex> lock(state_->mutex);
    while (true) {
      recipe::CheckInterrupt();
      if (state_->overflow)
        throw std::runtime_error(
            "telemetry queue overflow; stopping rather than hiding data loss");
      for (const auto &subscriber : subscribers_)
        if (subscriber->DroppedCount())
          throw std::runtime_error("SDK reported dropped telemetry; stopping");
      if (!state_->queue.empty()) {
        auto result = std::move(state_->queue.front());
        state_->queue.pop_front();
        return result;
      }
      if (recipe::Clock::now() >= end)
        return std::nullopt;
      state_->ready.wait_until(
          lock,
          std::min(end, recipe::Clock::now() + std::chrono::milliseconds(100)));
    }
  }

private:
  struct State {
    std::mutex mutex;
    std::condition_variable ready;
    std::deque<Event> queue;
    bool overflow = false;
  };
  std::shared_ptr<State> state_ = std::make_shared<State>();
  std::vector<std::shared_ptr<aorta::Subscriber>> subscribers_;
};
} // namespace health

int main(int argc, char **argv) {
  return recipe::Run([&] {
    const auto args = health::Parse(argc, argv);
    if (args.help) {
      std::cout << "Read-only health monitor: [--config FILE] [--duration "
                   "SECONDS] [--simulate | --execute]\n";
      return 0;
    }
    const auto config = health::LoadConfig(args.config);
    health::Monitor monitor(config);
    if (!args.execute) {
      health::RequireContainer();
      if (!args.simulate) {
        recipe::Emit("\"execute\":false,\"routes\":{\"state\":\"/locomotion/"
                     "status\",\"battery\":\"/bms_state\",\"system\":\"/system/"
                     "sm_status\"},\"duration_seconds\":" +
                     recipe::N(args.duration) + ",\"config\":" +
                     recipe::Object({{"stale_after_seconds",
                                      recipe::N(config.stale_after_seconds)},
                                     {"low_battery_percent",
                                      recipe::N(config.low_battery_percent)}}));
        return 0;
      }
      for (size_t i = 0; i < health::kNames.size(); ++i) {
        health::Sample sample;
        sample.stamp_ns = sample.heartbeat_seq = 1;
        sample.soc_percent = 80;
        monitor.Update(static_cast<health::Stream>(i), sample, 0);
      }
      for (double now : {0.0, config.stale_after_seconds + 1})
        recipe::Emit("\"source\":\"synthetic\"," +
                     health::SnapshotJson(monitor.Get(now)));
      return 0;
    }
    auto node = recipe::OpenNode("vbot_health_monitor_cpp");
    health::Inbox inbox(node);
    const auto end = recipe::After(args.duration);
    double next_report = health::Now();
    while (recipe::Clock::now() < end) {
      const auto item = inbox.Poll(std::min(end, recipe::After(0.1)));
      const double now = health::Now();
      if (item)
        health::Consume(monitor, *item);
      if (now >= next_report) {
        recipe::Emit("\"source\":\"device\"," +
                     health::SnapshotJson(monitor.Get(now)));
        next_report = now + 1;
      }
    }
    recipe::CheckInterrupt();
    const auto result = monitor.Get(health::Now());
    recipe::Emit("\"source\":\"device\",\"final\":true," +
                 health::SnapshotJson(result));
    return result.all_streams_receiving ? 0 : 1;
  });
}
