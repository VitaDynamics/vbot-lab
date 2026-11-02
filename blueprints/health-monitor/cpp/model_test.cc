#include "blueprints/health-monitor/cpp/model.h"
#include <iostream>
#include <limits>

void Check(bool value, const char *description) {
  if (!value)
    throw std::runtime_error(description);
}
template <typename F> void Reject(F operation) {
  try {
    operation();
  } catch (const std::invalid_argument &) {
    return;
  }
  throw std::runtime_error("expected invalid argument rejection");
}
void Populate(health::Monitor &monitor) {
  for (size_t i = 0; i < 3; ++i) {
    health::Sample value;
    value.stamp_ns = 100;
    value.heartbeat_seq = 1;
    value.soc_percent = 80;
    Check(monitor.Update(static_cast<health::Stream>(i), value, 0), "populate");
  }
}
int main() {
  try {
    auto config = health::ParseConfig(
        "{\"low_battery_percent\":2e1,\"stale_after_seconds\":3.0}");
    Check(config.low_battery_percent == 20 && config.stale_after_seconds == 3,
          "config values");
    for (const auto *text :
         {"{}", "[]",
          "{\"stale_after_seconds\":3,\"low_battery_percent\":20} trailing",
          "{\"stale_after_seconds\":true,\"low_battery_percent\":20}",
          "{\"stale_after_seconds\":03,\"low_battery_percent\":20}",
          "{\"stale_after_seconds\":3,\"low_battery_percent\":NaN}",
          "{\"stale_after_seconds\":3,\"stale_after_seconds\":4}",
          "{\"stale_after_seconds\":3,\"unknown\":20}",
          "{\"stale_after_seconds\":3,\"low_battery_percent\":20,\"extra\":1}",
          "{\"stale_after_seconds\":0,\"low_battery_percent\":20}",
          "{\"stale_after_seconds\":3,\"low_battery_percent\":101}"})
      Reject([&] { health::ParseConfig(text); });
    Reject([] { health::ParseConfig(std::string(4097, ' ')); });
    Reject([] {
      health::Validate({std::numeric_limits<double>::infinity(), 20});
    });
    health::Monitor monitor(config);
    Check(!monitor.Get(10).all_streams_receiving, "empty input is not success");
    for (const auto &stream : monitor.Get(10).streams)
      Check(std::string(stream.status) == "waiting_data",
            "missing input status");
    Populate(monitor);
    Check(monitor.Get(2).all_streams_receiving, "all fresh");
    Check(monitor.Get(3).all_streams_receiving, "fresh boundary");
    Check(!monitor.Get(4).all_streams_receiving, "stream expiration");
    health::Sample value;
    value.soc_percent = 80;
    for (const uint64_t stamp : {99, 100}) {
      value.stamp_ns = stamp;
      Check(!monitor.Update(health::Stream::Battery, value, 3),
            "reordered/duplicate frame rejection");
    }
    Check(monitor.Get(4).streams[1].state.out_of_order == 2,
          "ordering counter");
    Check(std::string(monitor.Get(4).streams[1].status) == "stale",
          "old frame cannot refresh");
    value.stamp_ns = 200;
    value.soc_percent = 10;
    Check(monitor.Update(health::Stream::Battery, value, 5),
          "new frame recovery");
    Check(monitor.Get(5).low_battery, "low battery advisory");
    Check(!monitor.Get(5).all_streams_receiving, "other streams still stale");
    value.soc_percent = std::numeric_limits<double>::quiet_NaN();
    Check(!monitor.Update(health::Stream::Battery, value, 6),
          "invalid SOC rejection");
    value.valid = false;
    Check(!monitor.Update(health::Stream::State, value, 6),
          "invalid decode rejection");
    value.valid = true;
    value.stamp_ns = 0;
    Check(monitor.Update(health::Stream::State, value, 6),
          "zero source timestamp");
    Check(std::string(monitor.Get(10).streams[0].status) == "stale",
          "zero timestamp still expires");
    Reject([&] { monitor.Get(std::numeric_limits<double>::quiet_NaN()); });
    std::cout << "health-monitor C++ model checks passed\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << error.what() << '\n';
    return 1;
  }
}
